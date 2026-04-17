"""
门卫验证系统API路由（内网）

提供访客码、离校码、动态码的验证功能
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta, date
from functools import wraps
import secrets
import time

from app import db
from app.models.user import User
from app.models.visit_application import VisitApplication
from app.models.visit_record import VisitRecord
from app.models.verification_log import VerificationLog
from app.utils.hmac_utils import verify_hmac_code

guard_verify_bp = Blueprint('guard_verify', __name__)


# === 缓存辅助函数 ===

def get_cached_alumni_by_phone(phone: str):
    """从缓存获取校友信息"""
    try:
        if hasattr(current_app, 'cache_manager') and current_app.cache_manager:
            cache_key = f"alumni:phone:{phone}"
            return current_app.cache_manager.get_cached_visitor(cache_key)
    except Exception as e:
        current_app.logger.warning(f"获取缓存失败: {e}")
    return None


def cache_alumni_info(phone: str, alumni_data: dict, ttl=3600):
    """缓存校友信息（默认1小时）"""
    try:
        if hasattr(current_app, 'cache_manager') and current_app.cache_manager:
            cache_key = f"alumni:phone:{phone}"
            current_app.cache_manager.cache_visitor(cache_key, alumni_data, ttl)
            current_app.logger.debug(f"已缓存校友信息: {phone}")
    except Exception as e:
        current_app.logger.warning(f"缓存校友信息失败: {e}")


def cache_verification_result(phone: str, result: dict, ttl=86400):
    """缓存验证结果（24小时）"""
    try:
        if hasattr(current_app, 'cache_manager') and current_app.cache_manager:
            current_app.cache_manager.cache_verification_result(phone, result, ttl)
    except Exception as e:
        current_app.logger.warning(f"缓存验证结果失败: {e}")


def get_cached_verification(phone: str):
    """获取缓存的验证结果"""
    try:
        if hasattr(current_app, 'cache_manager') and current_app.cache_manager:
            return current_app.cache_manager.get_cached_verification(phone)
    except Exception as e:
        current_app.logger.warning(f"获取验证缓存失败: {e}")
    return None


def guard_auth_required(f):
    """门卫认证装饰器（简化版）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 这里应该验证门卫的身份
        # 暂时跳过，实际使用时需要添加
        return f(*args, **kwargs)
    return decorated_function


@guard_verify_bp.route('/verify', methods=['POST'])
def verify_access_code():
    """
    统一验证接口 - 验证五种类型的访问码

    请求体:
    {
        "code": "123456",  # 6位码
        "guard_name": "门卫01",  # 门卫用户名（可选）
        "verify_type": "alumni"  # 可选：指定验证类型优化查询
    }

    verify_type可选值：
    - student-parent: 学生/家长（查询VisitApplication）
    - alumni: 校友（直接查询User表）
    - visitor: 访客（查询VisitApplication）

    返回:
    {
        "success": true,
        "data": {
            "code_type": "dynamic",  # alumni/visit_application/dynamic/visit/leave
            "valid": true,
            "message": "验证成功",
            "user_info": {
                "name": "张三",
                "type": "学生",
                "photo_url": "/static/photos/...",
                "details": {...}
            }
        }
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        guard_name = data.get('guard_name', 'unknown')
        verify_type = data.get('verify_type', None)  # 可选的验证类型

        if not code or len(code) != 6:
            return jsonify({'error': '访问码必须是6位数字'}), 400

        # 根据指定的验证类型优化查询
        if verify_type == 'alumni':
            # 直接验证校友，跳过其他查询
            result = verify_alumni_code_internal(code)
            if result['valid']:
                log_verification('alumni', code, True, guard_name, result.get('user_info', {}).get('name'))
                current_app.logger.info(f"✅ 门卫验证成功（校友）: {result.get('user_info', {}).get('name')}")
                return jsonify({
                    'success': True,
                    'data': {
                        'code_type': 'alumni',
                        'valid': True,
                        'message': "验证成功 - 校友",
                        'user_info': result['user_info']
                    }
                })

            # 校友验证失败
            log_verification('alumni', code, False, guard_name, None)
            return jsonify({
                'success': False,
                'data': {
                    'valid': False,
                    'message': '校友码无效或已过期'
                }
            })

        elif verify_type == 'student-leave':
            # 学生出校验证（24小时有效期）
            result = verify_student_leave_code_internal(code)
            if result['valid']:
                log_verification('student_leave', code, True, guard_name, result.get('parent_info', {}).get('name'))
                current_app.logger.info(f"✅ 门卫验证成功（学生出校）: {result.get('parent_info', {}).get('name')}")
                return jsonify({
                    'success': True,
                    'data': {
                        'code_type': 'student_leave',
                        'valid': True,
                        'message': "验证成功 - 学生出校",
                        'user_info': result['parent_info']
                    }
                })

            # 学生出校验证失败
            log_verification('student_leave', code, False, guard_name, None)
            return jsonify({
                'success': False,
                'data': {
                    'valid': False,
                    'message': '学生出校码无效或已过期（24小时有效期）'
                }
            })

        elif verify_type in ['student-parent', 'visitor']:
            # 验证学生/家长/访客（查询VisitApplication）
            result = verify_visit_application_internal(code)
            if result['valid']:
                log_verification('visit_application', code, True, guard_name, result.get('applicant_info', {}).get('name'))
                current_app.logger.info(f"✅ 门卫验证成功: {result.get('applicant_info', {}).get('name')}, 审批后{result.get('time_diff_seconds')}秒")
                return jsonify({
                    'success': True,
                    'data': {
                        'code_type': 'visit_application',
                        'valid': True,
                        'message': f"验证成功 - {result.get('applicant_info', {}).get('type', '访客')}",
                        'user_info': result['applicant_info'],
                        'application_id': result.get('application_id'),
                        'time_diff_seconds': result.get('time_diff_seconds')
                    }
                })

            # 访问申请验证失败
            log_verification('visit_application', code, False, guard_name, None)
            return jsonify({
                'success': False,
                'data': {
                    'valid': False,
                    'message': '访问码无效或已过期（3分钟有效期）'
                }
            })

        # 未指定类型或类型不匹配，依次尝试所有类型（向后兼容）

        # 1. 首先检查校友动态码（直接查询User表，无需老师审批）- 3分钟窗口
        result = verify_alumni_code_internal(code)
        if result['valid']:
            log_verification('alumni', code, True, guard_name, result.get('user_info', {}).get('name'))
            current_app.logger.info(f"✅ 门卫验证成功（校友）: {result.get('user_info', {}).get('name')}")
            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'alumni',
                    'valid': True,
                    'message': "验证成功 - 校友",
                    'user_info': result['user_info']
                }
            })

        # 2. 检查老师审批的访问申请（VisitApplication表）- 3分钟窗口
        result = verify_visit_application_internal(code)
        if result['valid']:
            log_verification('visit_application', code, True, guard_name, result.get('applicant_info', {}).get('name'))
            current_app.logger.info(f"✅ 门卫验证成功: {result.get('applicant_info', {}).get('name')}, 审批后{result.get('time_diff_seconds')}秒")
            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'visit_application',
                    'valid': True,
                    'message': f"验证成功 - {result.get('applicant_info', {}).get('type', '访客')}",
                    'user_info': result['applicant_info'],
                    'application_id': result.get('application_id'),  # 添加application_id用于确认放行
                    'time_diff_seconds': result.get('time_diff_seconds')
                }
            })

        # 2. 尝试验证动态码
        result = verify_dynamic_code_internal(code)
        if result['valid']:
            log_verification('dynamic', code, True, guard_name, result.get('user_name'))
            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'dynamic',
                    'valid': True,
                    'message': '验证成功 - 校内人员',
                    'user_info': result['user_info']
                }
            })

        # 3. 尝试验证访客码
        result = verify_visit_code_internal(code)
        if result['valid']:
            log_verification('visit', code, True, guard_name, result.get('visitor_name'))

            # 更新使用次数
            update_visit_code_usage(code)

            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'visit',
                    'valid': True,
                    'message': '验证成功 - 访客',
                    'user_info': result['visitor_info']
                }
            })

        # 4. 尝试验证离校码
        result = verify_leave_pass_internal(code)
        if result['valid']:
            log_verification('leave', code, True, guard_name, result.get('student_name'))

            # 更新使用次数
            update_leave_pass_usage(code)

            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'leave',
                    'valid': True,
                    'message': '验证成功 - 学生离校',
                    'user_info': result['student_info']
                }
            })

        # 都不匹配
        log_verification('unknown', code, False, guard_name, None)
        return jsonify({
            'success': False,
            'data': {
                'valid': False,
                'message': '访问码无效或已过期'
            }
        })

    except Exception as e:
        current_app.logger.error(f"验证访问码失败: {str(e)}")
        return jsonify({'error': '验证访问码失败', 'details': str(e)}), 500


def verify_dynamic_code_internal(code: str) -> dict:
    """
    验证动态码（内部函数）

    从dynamic_codes_cache表查询
    """
    try:
        # 延迟导入，避免模块不存在时启动失败
        try:
            from app.models.dynamic_code_cache import DynamicCodeCache
        except ImportError:
            return {'valid': False, 'message': '动态码功能未启用'}

        cache_entry = DynamicCodeCache.query.filter_by(code=code).first()

        if not cache_entry:
            return {'valid': False, 'message': '动态码不存在'}

        # 检查是否过期
        if cache_entry.expires_at < datetime.utcnow():
            return {'valid': False, 'message': '动态码已过期'}

        # 检查是否被撤销
        if cache_entry.blacklisted:
            return {'valid': False, 'message': '动态码已被撤销'}

        # 获取用户信息
        try:
            from app.models.user_verification import UserVerification
        except ImportError:
            return {'valid': False, 'message': '用户验证功能未启用'}

        user = UserVerification.query.get(cache_entry.user_id)
        if not user or not user.is_active:
            return {'valid': False, 'message': '用户不存在或已停用'}

        return {
            'valid': True,
            'user_name': user.real_name,
            'user_info': {
                'name': user.real_name,
                'type': user.user_type,
                'student_no': user.student_no,
                'employee_no': user.employee_no,
                'photo_url': user.photo_url,
                'valid_until': cache_entry.expires_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }

    except Exception as e:
        current_app.logger.error(f"验证动态码失败: {str(e)}")
        return {'valid': False, 'message': f'验证失败: {str(e)}'}


def verify_visit_application_internal(code: str) -> dict:
    """
    门卫验证逻辑（优化版 + 防重复放行）

    优化思路：
    1. 查询今天所有已审批的记录（包括已使用的）
    2. 先验证所有用户的HMAC
    3. 如果验证通过但记录已使用，返回明确错误
    4. 如果验证通过且记录未使用，返回用户信息

    性能提升：O(已审批记录数) 而不是 O(总用户数)
    """
    try:
        # 步骤1: 查询今天所有已审批的记录（包括已使用的，为了检测重复）
        today = date.today()
        all_applications = VisitApplication.query.filter(
            VisitApplication.visit_date == today,
            VisitApplication.application_status == 'approved'
        ).all()

        if not all_applications:
            current_app.logger.warning(f"❌ 今天没有审批记录")
            return {'valid': False, 'message': '今天没有审批记录，无法验证'}

        current_app.logger.info(f"📋 今天的审批记录数: {len(all_applications)}")

        # 步骤2: 收集需要验证的用户ID
        applicant_ids = set()
        for app in all_applications:
            applicant_ids.add(app.applicant_id)

        current_app.logger.info(f"👥 需要验证的用户数: {len(applicant_ids)}")

        # 步骤3: 查询这些用户
        users = User.query.filter(
            User.id.in_(applicant_ids),
            User.status == 'active'
        ).all()

        # 创建用户ID到用户的映射
        user_map = {user.id: user for user in users}

        # 步骤4: 尝试HMAC验证（收集所有匹配的记录）
        matched_applications = []  # 存储所有HMAC验证通过的记录

        for application in all_applications:
            applicant = user_map.get(application.applicant_id)
            if not applicant:
                continue

            # 尝试家长/校友的验证（纯手机号）
            # 对于访客类型，使用24小时时间窗口（与外网缓存一致）
            # 其他类型使用3分钟时间窗口
            time_window = 1440 if applicant.user_type == 'visitor' else 3  # 1440分钟 = 24小时

            verification = verify_hmac_code(code, applicant.phone, applicant.wechat_password, time_window)
            if verification['valid']:
                matched_applications.append({
                    'application': application,
                    'applicant': applicant,
                    'user_type': applicant.user_type,
                    'phone': applicant.phone
                })
                current_app.logger.info(f"✅ 门卫HMAC验证通过: phone={applicant.phone}, type={applicant.user_type}, app_id={application.id}, used={application.visit_started}, time_window={time_window}分钟")
                continue  # 不要break，继续收集所有匹配的记录

            # 尝试学生请假的验证（手机号+STU）- 如果是家长
            if applicant.user_type == 'parent':
                phone_stu = applicant.phone + 'STU'
                verification_stu = verify_hmac_code(code, phone_stu, applicant.wechat_password, 3)
                if verification_stu['valid']:
                    matched_applications.append({
                        'application': application,
                        'applicant': applicant,
                        'user_type': 'student-leave',
                        'phone': applicant.phone
                    })
                    current_app.logger.info(f"✅ 门卫HMAC验证通过: phone={applicant.phone}, type=student-leave, app_id={application.id}, used={application.visit_started}")

        if not matched_applications:
            current_app.logger.warning(f"❌ 门卫HMAC验证失败: 未找到匹配用户")
            return {'valid': False, 'message': '验证失败：码无效或已过期（3分钟有效期）'}

        # 步骤5: 从匹配的记录中，选择今天最新审批且未使用的记录
        # 先筛选未使用的记录
        unused_matches = [m for m in matched_applications if not m['application'].visit_started]

        if unused_matches:
            # 按审批时间降序排序，取最新的
            unused_matches.sort(key=lambda x: x['application'].approval_time or datetime.min, reverse=True)
            selected = unused_matches[0]
            current_app.logger.info(f"📄 找到未使用记录: id={selected['application'].id}, applicant={selected['applicant'].real_name}, approval_time={selected['application'].approval_time}")
        else:
            # 所有匹配的记录都已使用，选择最新使用的那条用于显示错误信息
            matched_applications.sort(key=lambda x: x['application'].visit_start_time or datetime.min, reverse=True)
            selected = matched_applications[0]
            applicant = selected['applicant']
            application = selected['application']
            current_app.logger.warning(f"🚫 该验证码已使用: applicant={applicant.real_name}, app_id={application.id}, used_at={application.visit_start_time}")
            return {
                'valid': False,
                'message': f'该验证码已使用！{applicant.real_name}已于{application.visit_start_time.strftime("%H:%M")}确认放行，不能重复使用'
            }

        # 步骤6: 返回找到的审批记录信息（未使用的记录）
        application = selected['application']
        applicant = selected['applicant']
        user_type = selected['user_type']
        phone = selected['phone']

        current_app.logger.info(f"📄 最终选择记录: id={application.id}, applicant={applicant.real_name}")

        # 检查审批时间（日志记录）
        if application.approval_time:
            time_diff_seconds = int((datetime.utcnow() - application.approval_time).total_seconds())
            current_app.logger.info(f"⏰ 审批时间: {application.approval_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                                   f"门卫验证: 审批后{time_diff_seconds}秒")

        # 获取毕业年份和公司信息（如果是校友）
        graduation_year = None
        company = None
        if applicant.alumni_profile:
            graduation_year = applicant.alumni_profile.graduation_year
            company = applicant.alumni_profile.company

        # 获取审批人信息（班主任）
        approver_name = None
        if application.approved_by:
            approver = User.query.get(application.approved_by)
            if approver:
                approver_name = approver.real_name

        # 获取关联学生信息（如果是家长）
        child_info = None
        if applicant.user_type == 'parent' and applicant.student_children:
            # 获取第一个关联的学生
            child = applicant.student_children[0]
            child_info = {
                'name': child.real_name,
                'student_no': getattr(child, 'student_no', None),
                'class_name': None  # 需要从其他地方获取
            }

        # 获取照片URL（如果存在）
        photo_url = applicant.photo_url if hasattr(applicant, 'photo_url') else None

        # 返回用户信息
        return {
            'valid': True,
            'applicant_id': applicant.id,
            'application_id': application.id,
            'approval_time': application.approval_time,
            'applicant_info': {
                'name': applicant.real_name,
                'type': user_type,
                'phone': applicant.phone,
                'photo_url': photo_url,
                'student_no': applicant.student_no if hasattr(applicant, 'student_no') else None,
                'employee_no': applicant.employee_no if hasattr(applicant, 'employee_no') else None,
                'graduation_year': graduation_year,
                'company': company,
                'child_info': child_info,  # 家长的孩子信息
                'visit_date': application.visit_date.strftime('%Y-%m-%d') if application.visit_date else None,
                'visit_purpose': application.visit_purpose,
                'approved_by': application.approved_by,
                'approver_name': approver_name,  # 班主任姓名
                'approval_note': application.approval_note,
                'approval_time_str': application.approval_time.strftime('%Y-%m-%d %H:%M:%S') if application.approval_time else None
            }
        }

    except Exception as e:
        current_app.logger.error(f"验证访问申请失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return {'valid': False, 'message': f'验证失败: {str(e)}'}


def verify_alumni_code_internal(code: str) -> dict:
    """
    验证校友动态码（内部函数）- 优化版本，支持Redis缓存

    校友无需老师审批，直接使用User表验证
    性能优化：使用缓存 + 数据库索引
    """
    try:
        start_time = time.time()

        current_app.logger.info(f"\n{'='*70}")
        current_app.logger.info(f"[校友验证开始] 验证码: {code}")
        current_app.logger.info(f"[验证时间] {time.strftime('%Y-%m-%d %H:%M:%S')}")
        current_app.logger.info(f"{'='*70}")

        # 查询所有校友类型的用户（使用索引优化）
        query_start = time.time()
        alumni_users = User.query.filter(
            User.user_type == 'alumni',
            User.status == 'active'
        ).all()
        query_time = (time.time() - query_start) * 1000

        if not alumni_users:
            current_app.logger.info(f"📋 系统中没有校友用户")
            return {'valid': False, 'message': '没有校友用户'}

        current_app.logger.info(f"📋 校友用户数: {len(alumni_users)}")
        current_app.logger.info(f"📋 查询时间: {query_time:.2f}ms")
        current_app.logger.info(f"📋 开始逐个验证...")

        matched_alumni = []

        for idx, alumni in enumerate(alumni_users, 1):
            current_app.logger.info(f"\n[{idx}/{len(alumni_users)}] 尝试验证校友: {alumni.real_name}")
            current_app.logger.info(f"  - 手机号: {alumni.phone}")

            verification = verify_hmac_code(code, alumni.phone, alumni.wechat_password, 3)

            if verification['valid']:
                # 计算时间差（秒）
                time_diff_seconds = int(time.time()) - verification['timestamp']

                matched_alumni.append({
                    'alumni': alumni,
                    'time_diff_seconds': time_diff_seconds
                })
                current_app.logger.info(f"  ✅ HMAC验证通过！")
                current_app.logger.info(f"  - 时间戳: {verification['timestamp']}")
                current_app.logger.info(f"  - 时间差: {time_diff_seconds}秒")
                current_app.logger.info(f"  - 消息: {verification['message']}")
            else:
                current_app.logger.info(f"  ❌ HMAC验证失败: {verification['message']}")

        current_app.logger.info(f"\n{'='*70}")
        current_app.logger.info(f"[验证结果] 匹配数: {len(matched_alumni)}")

        if not matched_alumni:
            current_app.logger.info(f"[验证失败] 未找到匹配的校友")
            current_app.logger.info(f"{'='*70}\n")
            return {'valid': False, 'message': '校友码无效或已过期（3分钟有效期）'}

        # 如果有多个匹配（理论上不应该发生），选择第一个
        selected = matched_alumni[0]
        alumni = selected['alumni']

        # 获取校友详细信息
        graduation_year = None
        company = None
        if alumni.alumni_profile:
            graduation_year = alumni.alumni_profile.graduation_year
            company = alumni.alumni_profile.work_unit  # 注意：是work_unit不是company

        # 构建用户信息
        user_info = {
            'id': alumni.id,
            'name': alumni.real_name,
            'phone': alumni.phone,
            'type': '校友',
            'graduation_year': graduation_year,
            'company': company,
            'photo_url': alumni.photo_url or '/static/images/default-avatar.png',
            'verification_time': datetime.now().isoformat(),
            'code_age_seconds': selected['time_diff_seconds']
        }

        # 缓存校友信息（1小时）
        cache_alumni_info(alumni.phone, user_info, ttl=3600)

        # 缓存验证结果（24小时）
        cache_verification_result(alumni.phone, {
            'valid': True,
            'user_info': user_info,
            'timestamp': int(time.time())
        }, ttl=86400)

        current_app.logger.info(f"[验证成功] 校友信息:")
        current_app.logger.info(f"  - 姓名: {alumni.real_name}")
        current_app.logger.info(f"  - 手机号: {alumni.phone}")
        current_app.logger.info(f"  - 毕业年份: {graduation_year}")
        current_app.logger.info(f"  - 工作单位: {company}")
        current_app.logger.info(f"  - 验证码年龄: {selected['time_diff_seconds']}秒")
        current_app.logger.info(f"  - 总耗时: {(time.time() - start_time)*1000:.2f}ms")
        current_app.logger.info(f"{'='*70}\n")

        return {
            'valid': True,
            'user_info': {
                'name': alumni.real_name,
                'type': 'alumni',
                'phone': alumni.phone,
                'photo_url': alumni.photo_url if hasattr(alumni, 'photo_url') else None,
                'graduation_year': graduation_year,
                'company': company,
                'employee_no': alumni.employee_id if hasattr(alumni, 'employee_id') else None
            }
        }

    except Exception as e:
        current_app.logger.error(f"验证校友码失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return {'valid': False, 'message': f'验证失败: {str(e)}'}


def verify_student_leave_code_internal(code: str) -> dict:
    """
    验证学生请假出校码（内部函数）

    学生请假：基于学号的HMAC验证码，当天有效
    家长申请 → 老师审批 → 生成HMAC码(学号+日期) → 学生凭码出校

    Args:
        code: 6位HMAC验证码

    Returns:
        {
            'valid': bool,
            'parent_info': dict or None
        }
    """
    try:
        import time
        from datetime import datetime, date as dt_date
        from app.utils.hmac_utils import generate_hmac_code

        current_app.logger.info(f"\n{'='*70}")
        current_app.logger.info(f"[学生出校验证开始] 验证码: {code}")
        current_app.logger.info(f"[验证时间] {time.strftime('%Y-%m-%d %H:%M:%S')}")
        current_app.logger.info(f"[有效期限] 当天23:59前")
        current_app.logger.info(f"{'='*70}")

        # 验证码格式：6位纯数字
        if not code or len(code) != 6 or not code.isdigit():
            current_app.logger.info(f"❌ 验证码格式错误：必须是6位纯数字")
            return {'valid': False, 'message': '验证码格式错误'}

        # 查询所有有学号的学生用户
        from app.models.user import User
        students = User.query.filter(
            User.student_id.isnot(None),
            User.student_id != '',
            User.status == 'active'
        ).all()

        if not students:
            current_app.logger.info(f"📋 系统中没有学生用户")
            return {'valid': False, 'message': '没有学生用户'}

        current_app.logger.info(f"📋 学生用户数: {len(students)}")
        current_app.logger.info(f"📋 开始逐个验证（学号+今天日期）...")

        # 使用今天的日期戳（和生成时保持一致）
        today = dt_date.today()
        today_datetime = datetime.combine(today, datetime.min.time())
        date_timestamp = int(today_datetime.timestamp())

        matched_students = []

        for idx, student in enumerate(students, 1):
            current_app.logger.info(f"\n[{idx}/{len(students)}] 尝试验证学生: {student.real_name}")
            current_app.logger.info(f"  - 学号: {student.student_id}")

            # 直接生成HMAC码并比较（使用今天0点时间戳）
            # 密钥必须和生成时一致：'STUDENT_EXIT'
            generated_code = generate_hmac_code(student.student_id, 'STUDENT_EXIT', date_timestamp)

            if generated_code == code:
                matched_students.append({
                    'student': student,
                    'time_diff_seconds': int(time.time()) - date_timestamp
                })
                current_app.logger.info(f"  ✅ HMAC验证通过！")
                current_app.logger.info(f"  - 生成时间戳: {date_timestamp} (今天0点)")
                current_app.logger.info(f"  - 时间差: {int(time.time()) - date_timestamp}秒")
            else:
                current_app.logger.info(f"  ❌ HMAC验证失败")

        current_app.logger.info(f"\n{'='*70}")
        current_app.logger.info(f"[验证结果] 匹配数: {len(matched_students)}")

        if not matched_students:
            current_app.logger.info(f"[验证失败] 未找到匹配的学生")
            current_app.logger.info(f"{'='*70}\n")
            return {'valid': False, 'message': '学生出校码无效或已过期（当天有效）'}

        # 如果有多个匹配（理论上不应该发生），选择第一个
        selected = matched_students[0]
        student = selected['student']

        current_app.logger.info(f"[验证成功] 学生信息:")
        current_app.logger.info(f"  - 姓名: {student.real_name}")
        current_app.logger.info(f"  - 学号: {student.student_id}")
        current_app.logger.info(f"  - 班级: {student.grade}{student.class_id if student.grade and student.class_id else ''}")
        current_app.logger.info(f"{'='*70}\n")

        return {
            'valid': True,
            'parent_info': {
                'name': student.real_name,
                'type': 'student',
                'phone': student.phone,
                'student_id': student.student_id,
                'grade': student.grade,
                'class_name': student.class_id,
                'photo_url': student.photo_url if hasattr(student, 'photo_url') else None
            }
        }

    except Exception as e:
        current_app.logger.error(f"验证学生出校码失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return {'valid': False, 'message': f'验证失败: {str(e)}'}


def verify_visit_code_internal(code: str) -> dict:
    """
    验证访客通行码（内部函数）

    从visit_codes表查询
    """
    try:
        try:
            from app.models.visit_code import VisitCode
        except ImportError:
            return {'valid': False, 'message': '访客码功能未启用'}

        visit = VisitCode.query.filter_by(code=code).first()

        if not visit:
            return {'valid': False, 'message': '访客码不存在'}

        # 检查是否已审批
        if not visit.approved:
            return {'valid': False, 'message': '访客申请未审批'}

        # 检查是否过期
        if visit.expires_at < datetime.utcnow():
            return {'valid': False, 'message': '访客码已过期'}

        # 检查使用次数
        if visit.used_count >= visit.max_uses:
            return {'valid': False, 'message': '访客码已使用完毕'}

        return {
            'valid': True,
            'visitor_name': visit.visitor_name,
            'visitor_info': {
                'name': visit.visitor_name,
                'id_card_last4': visit.id_card_last4,
                'host_name': visit.host_name,
                'visit_reason': visit.visit_reason,
                'visit_date': visit.visit_date.strftime('%Y-%m-%d'),
                'approved': visit.approved,
                'uses_remaining': visit.max_uses - visit.used_count
            }
        }

    except Exception as e:
        current_app.logger.error(f"验证访客码失败: {str(e)}")
        return {'valid': False, 'message': f'验证失败: {str(e)}'}


def verify_leave_pass_internal(code: str) -> dict:
    """
    验证离校通行码（内部函数）

    从leave_passes表查询
    """
    try:
        try:
            from app.models.leave_pass import LeavePass
        except ImportError:
            return {'valid': False, 'message': '离校码功能未启用'}

        leave_pass = LeavePass.query.filter_by(code=code).first()

        if not leave_pass:
            return {'valid': False, 'message': '离校码不存在'}

        # 检查审批状态
        if not leave_pass.teacher_approved:
            return {'valid': False, 'message': '老师未审批'}

        if not leave_pass.parent_verified:
            return {'valid': False, 'message': '家长未验证'}

        # 检查是否过期
        if leave_pass.expires_at < datetime.utcnow():
            return {'valid': False, 'message': '离校码已过期'}

        # 检查状态
        if leave_pass.pass_status == 'expired':
            return {'valid': False, 'message': '离校码已失效'}

        if leave_pass.used_count >= 2:
            return {'valid': False, 'message': '离校码已使用完毕'}

        return {
            'valid': True,
            'student_name': leave_pass.student_name,
            'student_info': {
                'name': leave_pass.student_name,
                'leave_type': leave_pass.leave_type,
                'leave_start_time': leave_pass.leave_start_time.strftime('%Y-%m-%d %H:%M'),
                'leave_end_time': leave_pass.leave_end_time.strftime('%Y-%m-%d %H:%M'),
                'teacher_approved': leave_pass.teacher_approved,
                'parent_verified': leave_pass.parent_verified,
                'pass_status': leave_pass.pass_status,
                'used_count': leave_pass.used_count
            }
        }

    except Exception as e:
        current_app.logger.error(f"验证离校码失败: {str(e)}")
        return {'valid': False, 'message': f'验证失败: {str(e)}'}


def log_verification(code_type: str, code: str, result: bool, guard_name: str, user_name: str = None):
    """记录验证日志（静默失败，不影响验证流程）"""
    try:
        log = VerificationLog(
            code_type=code_type,
            code=code,
            verification_result=result,
            verified_by=guard_name,
            user_name=user_name
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # 静默失败，不影响验证流程
        pass


def update_visit_code_usage(code: str):
    """更新访客码使用次数"""
    try:
        try:
            from app.models.visit_code import VisitCode
            visit = VisitCode.query.filter_by(code=code).first()
            if visit:
                visit.used_count += 1
                db.session.commit()
        except ImportError:
            pass  # 访客码功能未启用
    except Exception as e:
        current_app.logger.error(f"更新访客码使用次数失败: {str(e)}")
        db.session.rollback()


def update_leave_pass_usage(code: str):
    """更新离校码使用次数"""
    try:
        try:
            from app.models.leave_pass import LeavePass
            leave_pass = LeavePass.query.filter_by(code=code).first()
            if leave_pass:
                leave_pass.used_count += 1

                # 更新状态
                if leave_pass.used_count == 1:
                    leave_pass.pass_status = 'used_left'
                elif leave_pass.used_count == 2:
                    leave_pass.pass_status = 'used_back'

                db.session.commit()
        except ImportError:
            pass  # 离校码功能未启用
    except Exception as e:
        current_app.logger.error(f"更新离校码使用次数失败: {str(e)}")
        db.session.rollback()


@guard_verify_bp.route('/confirm', methods=['POST'])
def confirm_visit_entry():
    """
    确认放行，标记记录为已使用（一人一码一次）

    请求体:
    {
        "application_id": 123,  # 审批记录ID
        "guard_name": "门卫01"  # 门卫姓名（可选）
    }

    返回:
    {
        "success": true,
        "message": "已确认放行"
    }
    """
    try:
        data = request.get_json()
        application_id = data.get('application_id')
        guard_name = data.get('guard_name', 'unknown')

        if not application_id:
            return jsonify({'error': '缺少application_id'}), 400

        application = VisitApplication.query.get(application_id)

        if not application:
            current_app.logger.error(f"❌ 确认放行失败: 记录不存在, application_id={application_id}")
            return jsonify({'error': '记录不存在'}), 404

        # 检查是否已经使用过
        if application.visit_started:
            # 获取申请人信息用于日志
            applicant = User.query.get(application.applicant_id)
            applicant_name = applicant.real_name if applicant else 'Unknown'
            current_app.logger.warning(f"🚫 重复确认放行: applicant={applicant_name}, application_id={application_id}, guard={guard_name}, first_used_at={application.visit_start_time}")
            return jsonify({
                'error': '该记录已确认过，不能重复使用',
                'applicant_name': applicant_name,
                'first_used_at': application.visit_start_time.strftime('%Y-%m-%d %H:%M:%S') if application.visit_start_time else None
            }), 400

        # 获取申请人信息用于日志
        applicant = User.query.get(application.applicant_id)
        applicant_name = applicant.real_name if applicant else 'Unknown'
        applicant_phone = applicant.phone if applicant else 'Unknown'

        # 标记为已使用
        application.visit_started = True
        application.visit_start_time = datetime.utcnow()

        # 检查用户信息完整度
        info_complete = bool(
            applicant and
            applicant.phone and
            applicant.email and
            applicant.id_card
        ) if applicant else False

        # 创建访问记录（填充所有新字段）
        visit_record = VisitRecord(
            user_id=application.applicant_id,
            visit_application_id=application.id,
            entry_time=datetime.utcnow(),
            verification_method='manual',  # 门卫手动确认放行
            gate_name='Main Gate',  # 可以根据实际情况配置
            security_guard_id=None,  # 如果有门卫用户系统，可以关联门卫ID
            guard_name=guard_name,  # 门卫姓名
            visitor_type=applicant.user_type if applicant else None,  # 访问者类型
            destination=application.target_department,  # 访问目的地
            host_person=application.target_person,  # 接待人姓名
            host_person_id=None,  # 接待人ID（后续可以从target_work_id查询）
            info_complete=info_complete,  # 信息完整度
            visit_purpose=application.visit_purpose,  # 访问目的
            notes=f'门卫确认放行: {guard_name}'  # 保留原有笔记
        )
        db.session.add(visit_record)
        db.session.commit()

        current_app.logger.info(f"✅ Created visit_record ID={visit_record.id} for application {application_id}")

        # 记录完整的放行信息到日志
        current_app.logger.info(
            f"✅ 门卫确认放行完成 | "
            f"申请ID: {application_id} | "
            f"申请人: {applicant_name} | "
            f"手机号: {applicant_phone} | "
            f"访问日期: {application.visit_date} | "
            f"访问目的: {application.visit_purpose} | "
            f"审批时间: {application.approval_time} | "
            f"放行时间: {application.visit_start_time} | "
            f"门卫: {guard_name}"
        )

        # 记录到verification_log表（如果可用）
        log_verification(
            code_type='guard_confirm',
            code=str(application_id),
            result=True,
            guard_name=guard_name,
            user_name=applicant_name
        )

        return jsonify({
            'success': True,
            'message': f'已确认放行：{applicant_name}，访问记录已创建，该码已失效',
            'applicant_name': applicant_name,
            'visit_record_id': visit_record.id,
            'confirm_time': application.visit_start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ 确认放行失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': '确认放行失败'}), 500


@guard_verify_bp.route('/sync', methods=['GET'])
def sync_from_external():
    """
    从外网服务器同步数据（内网定时任务调用）

    参数:
        last_sync: 上次同步时间（可选，Unix时间戳）

    返回:
    {
        "success": true,
        "data": {
            "synced_at": "2026-03-27 12:00:00",
            "user_verification_count": 100,
            "visit_codes_count": 5,
            "leave_passes_count": 3
        }
    }
    """
    try:
        from backend.app.services.sync_service import SyncService

        last_sync = request.args.get('last_sync', type=int)

        sync_service = SyncService()
        result = sync_service.sync_all(last_sync)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        current_app.logger.error(f"同步数据失败: {str(e)}")
        return jsonify({'error': '同步数据失败', 'details': str(e)}), 500


@guard_verify_bp.route('/code/<code>', methods=['GET'])
def get_code_details(code: str):
    """
    查询码的详细信息（调试用）

    返回:
    {
        "success": true,
        "data": {
            "code_type": "dynamic",
            "exists": true,
            "details": {...}
        }
    }
    """
    try:
        code = code.strip()

        if len(code) != 6:
            return jsonify({'error': '访问码必须是6位数字'}), 400

        # 查询五种类型
        info = {
            'code': code,
            'alumni': None,
            'visit_application': None,
            'dynamic': None,
            'visit': None,
            'leave': None
        }

        # 1. 校友动态码（无需审批）
        try:
            from backend.app.models.user import User

            alumni_users = User.query.filter(
                User.user_type == 'alumni',
                User.status == 'active'
            ).all()

            for alumni in alumni_users:
                from app.utils.hmac_utils import verify_hmac_code
                verification = verify_hmac_code(code, alumni.phone, alumni.wechat_password, 3)
                if verification['valid']:
                    info['alumni'] = {
                        'exists': True,
                        'name': alumni.real_name,
                        'phone': alumni.phone,
                        'graduation_year': alumni.alumni_profile.graduation_year if alumni.alumni_profile else None,
                        'company': alumni.alumni_profile.company if alumni.alumni_profile else None,
                        'time_diff_seconds': verification['time_diff_seconds'],
                        'is_within_3min': verification['time_diff_seconds'] <= 180
                    }
                    break
        except Exception as e:
            info['alumni'] = {'error': str(e)}

        # 1. 访问申请（老师审批的）
        try:
            from backend.app.models.visit_application import VisitApplication
            from backend.app.models.user import User
            from datetime import datetime

            app = VisitApplication.query.filter_by(qr_code=code, application_status='approved').first()
            if app:
                time_diff = None
                if app.approval_time:
                    time_diff = int((datetime.utcnow() - app.approval_time).total_seconds())

                applicant = User.query.get(app.applicant_id)
                info['visit_application'] = {
                    'exists': True,
                    'applicant_id': app.applicant_id,
                    'applicant_name': applicant.real_name if applicant else 'Unknown',
                    'applicant_type': applicant.user_type if applicant else 'Unknown',
                    'visit_date': app.visit_date.strftime('%Y-%m-%d') if app.visit_date else None,
                    'visit_purpose': app.visit_purpose,
                    'approval_time': app.approval_time.strftime('%Y-%m-%d %H:%M:%S') if app.approval_time else None,
                    'time_diff_seconds': time_diff,
                    'is_within_3min': time_diff is not None and time_diff <= 180
                }
        except Exception as e:
            info['visit_application'] = {'error': str(e)}

        # 2. 动态码
        try:
            from backend.app.models.dynamic_code_cache import DynamicCodeCache
            cache = DynamicCodeCache.query.filter_by(code=code).first()
            if cache:
                info['dynamic'] = {
                    'exists': True,
                    'expires_at': cache.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'blacklisted': cache.blacklisted
                }
        except:
            pass

        # 3. 访客码
        try:
            from backend.app.models.visit_code import VisitCode
            visit = VisitCode.query.filter_by(code=code).first()
            if visit:
                info['visit'] = {
                    'exists': True,
                    'visitor_name': visit.visitor_name,
                    'approved': visit.approved,
                    'used_count': visit.used_count,
                    'max_uses': visit.max_uses,
                    'expires_at': visit.expires_at.strftime('%Y-%m-%d %H:%M:%S')
                }
        except:
            pass

        # 4. 离校码
        try:
            from backend.app.models.leave_pass import LeavePass
            leave = LeavePass.query.filter_by(code=code).first()
            if leave:
                info['leave'] = {
                    'exists': True,
                    'student_name': leave.student_name,
                    'teacher_approved': leave.teacher_approved,
                    'parent_verified': leave.parent_verified,
                    'pass_status': leave.pass_status,
                    'used_count': leave.used_count,
                    'expires_at': leave.expires_at.strftime('%Y-%m-%d %H:%M:%S')
                }
        except:
            pass

        return jsonify({
            'success': True,
            'data': info
        })

    except Exception as e:
        current_app.logger.error(f"查询码详情失败: {str(e)}")
        return jsonify({'error': '查询码详情失败', 'details': str(e)}), 500
