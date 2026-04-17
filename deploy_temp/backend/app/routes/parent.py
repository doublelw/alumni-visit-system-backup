"""
家长服务 - API路由

支持两阶段码机制：
1. 审批码（长期有效，用于老师审批）
2. 入校码（3分钟有效，用于门卫验证）
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.visitor_application import VisitorApplication
import random

parent_bp = Blueprint('parent', __name__)


# ==================== 家长登录 ====================

@parent_bp.route('/login', methods=['POST'])
def parent_login():
    """
    家长登录（微信H5页面使用）

    请求体:
    {
        "phone": "13800138000",
        "password": "88"  # 2-6位数字密码
    }

    返回:
    {
        "success": true,
        "data": {
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "parent": {
                "id": 1,
                "name": "张父",
                "phone": "13800138000",
                "real_name": "张父"
            }
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()

        # 验证输入
        if not phone or len(phone) != 11:
            return jsonify({'error': '请输入正确的11位手机号'}), 400

        if not password or len(password) < 2 or len(password) > 6:
            return jsonify({'error': '请输入2-6位数字密码'}), 400

        # 查找家长用户
        parent = User.query.filter(
            User.phone == phone,
            User.user_type.like('%parent%')
        ).first()

        if not parent:
            return jsonify({'error': '未找到该家长账号，请联系学校'}), 404

        # TODO: 验证密码（暂时跳过，需要添加字段到User表）
        # if parent.wechat_password != password:
        #     return jsonify({'error': '密码错误'}), 401

        # 生成简单的token（实际应该使用JWT）
        import hashlib
        import time
        token_data = f"{parent.id}:{phone}:{int(time.time())}"
        token = hashlib.md5(token_data.encode()).hexdigest()

        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'parent': {
                    'id': parent.id,
                    'name': parent.real_name,
                    'phone': parent.phone,
                    'real_name': parent.real_name
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"家长登录失败: {str(e)}")
        return jsonify({'error': '登录失败', 'details': str(e)}), 500


def generate_6_digit_code():
    """生成6位数字码"""
    return f"{random.randint(0, 999999):06d}"


def validate_parent(phone, pin):
    """
    验证家长身份

    返回: (success, user_or_error_message)
    """
    if not phone or len(phone) != 11:
        return False, "请输入正确的11位手机号"

    if not pin or len(pin) != 2 or not pin.isdigit():
        return False, "请输入2位数字密码"

    # 查找家长用户
    parent = User.query.filter(
        User.phone == phone,
        User.user_type.like('%parent%')
    ).first()

    if not parent:
        return False, "未找到该家长账号，请联系学校"

    # TODO: 验证2位密码（暂时跳过，需要添加字段到User表）
    # if parent.pin_code != pin:
    #     return False, "密码错误"

    return True, parent


# ==================== 家长进校：两阶段码 ====================

@parent_bp.route('/generate-visit-code', methods=['POST'])
def generate_visit_code():
    """
    家长生成进校审批码（第一阶段）

    请求体:
    {
        "phone": "13800138000",
        "pin": "88"
    }

    返回:
    {
        "success": true,
        "data": {
            "approval_code": "123456",  # 审批码，长期有效
            "parent_name": "张父",
            "expires_at": "2026-03-27 23:59:59"
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        pin = data.get('pin', '').strip()

        success, result = validate_parent(phone, pin)
        if not success:
            return jsonify({'error': result}), 400

        parent = result

        # 生成审批码（长期有效，当天23:59:59过期）
        today_end = datetime.now().replace(hour=23, minute=59, second=59)
        approval_code = generate_6_digit_code()

        # 创建访客申请（状态为pending，等待老师审批）
        application = VisitorApplication(
            visitor_name=parent.real_name,
            id_card=parent.id_card if hasattr(parent, 'id_card') else None,
            phone=parent.phone,
            visit_reason="家长进校",
            host_name="",  # 待老师审批时填写
            access_code=approval_code,  # 先存入审批码
            status='pending',
            created_at=datetime.now()
        )

        db.session.add(application)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'approval_code': approval_code,
                'parent_name': parent.real_name,
                'application_id': application.id,
                'expires_at': today_end.strftime('%Y-%m-%d %H:%M:%S'),
                'message': '审批码已生成，请发给老师审批'
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"生成审批码失败: {str(e)}")
        return jsonify({'error': '生成审批码失败', 'details': str(e)}), 500


@parent_bp.route('/generate-entry-code', methods=['POST'])
def generate_entry_code():
    """
    家长到校后生成入校码（第二阶段）

    请求体:
    {
        "phone": "13800138000",
        "pin": "88"
    }

    返回:
    {
        "success": true,
        "data": {
            "entry_code": "789012",  # 入校码，3分钟有效
            "expires_at": "2026-03-27 14:05:00"
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        pin = data.get('pin', '').strip()

        success, result = validate_parent(phone, pin)
        if not success:
            return jsonify({'error': result}), 400

        parent = result

        # 检查是否有已批准的申请
        application = VisitorApplication.query.filter(
            VisitorApplication.phone == phone,
            VisitorApplication.status == 'approved'
        ).order_by(VisitorApplication.created_at.desc()).first()

        if not application:
            return jsonify({'error': '未找到已批准的申请，请先联系老师审批'}), 404

        # 检查审批日期是否有效
        if application.approved_at:
            approved_date = application.approved_at.date()
            today = datetime.now().date()
            if approved_date < today:
                return jsonify({'error': '审批日期已过期，请重新申请'}), 400

        # 生成入校码（3分钟有效）
        expires_at = datetime.now() + timedelta(minutes=3)
        entry_code = generate_6_digit_code()

        # 更新访客申请的入校码
        application.access_code = entry_code
        application.code_expires_at = expires_at
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'entry_code': entry_code,
                'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                'message': '入校码已生成，3分钟内有效'
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"生成入校码失败: {str(e)}")
        return jsonify({'error': '生成入校码失败', 'details': str(e)}), 500


# ==================== 学生请假：基于家长账号 ====================

@parent_bp.route('/get-children', methods=['POST'])
def get_children():
    """
    获取家长关联的学生列表

    请求体:
    {
        "phone": "13800138000",
        "pin": "88"
    }

    返回:
    {
        "success": true,
        "data": {
            "phone": "13800138000",
            "parent_name": "张父",
            "children": [
                {"id": 123, "name": "张三", "class_name": "高三(1)班"},
                {"id": 124, "name": "张四", "class_name": "高一(2)班"}
            ]
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        pin = data.get('pin', '').strip()

        success, result = validate_parent(phone, pin)
        if not success:
            return jsonify({'error': result}), 400

        parent = result

        # 查找该家长关联的学生
        # TODO: 需要在数据库中建立家长-学生关联关系
        # 临时方案：通过手机号查找（假设家长手机号存储在学生表中）
        children = User.query.filter(
            User.user_type.like('%student%')
        ).all()

        # 临时返回所有学生（实际应该只返回该家长的孩子）
        children_list = []
        for child in children:
            children_list.append({
                'id': child.id,
                'name': child.real_name,
                'class_name': child.class_name
            })

        return jsonify({
            'success': True,
            'data': {
                'phone': phone,
                'parent_name': parent.real_name,
                'children': children_list
            }
        })

    except Exception as e:
        current_app.logger.error(f"查询学生列表失败: {str(e)}")
        return jsonify({'error': '查询学生列表失败', 'details': str(e)}), 500


@parent_bp.route('/generate-leave-code', methods=['POST'])
def generate_leave_code():
    """
    家长为学生生成请假码

    请求体:
    {
        "phone": "13800138000",
        "pin": "88",
        "student_id": 123
    }

    返回:
    {
        "success": true,
        "data": {
            "leave_code": "654321",
            "student_name": "张三",
            "class_name": "高三(1)班"
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        pin = data.get('pin', '').strip()
        student_id = data.get('student_id')

        success, result = validate_parent(phone, pin)
        if not success:
            return jsonify({'error': result}), 400

        if not student_id:
            return jsonify({'error': '请选择学生'}), 400

        parent = result

        # 查找学生
        student = User.query.get(student_id)
        if not student or 'student' not in student.user_type:
            return jsonify({'error': '学生不存在'}), 404

        # 生成请假码（长期有效，待老师审批）
        today_end = datetime.now().replace(hour=23, minute=59, second=59)
        leave_code = generate_6_digit_code()

        # 创建请假申请（复用VisitorApplication表）
        application = VisitorApplication(
            visitor_name=f"{parent.real_name}（家长）",
            id_card=parent.id_card if hasattr(parent, 'id_card') else None,
            phone=parent.phone,
            visit_reason=f"学生请假：{student.real_name}",
            host_name="",
            access_code=leave_code,
            status='pending',
            created_at=datetime.now()
        )

        db.session.add(application)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'leave_code': leave_code,
                'application_id': application.id,
                'student_name': student.real_name,
                'class_name': student.class_name,
                'parent_name': parent.real_name,
                'expires_at': today_end.strftime('%Y-%m-%d %H:%M:%S'),
                'message': '请假码已生成，请发给老师审批'
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"生成请假码失败: {str(e)}")
        return jsonify({'error': '生成请假码失败', 'details': str(e)}), 500


# ==================== 访客登记 ====================

@parent_bp.route('/register-visitor', methods=['POST'])
def register_visitor():
    """
    家长代访客登记（微信H5页面使用）

    请求体:
    {
        "visitor_name": "张三",
        "visitor_phone": "13800138000",
        "id_card": "110101199001011234",
        "visit_purpose": "meeting",
        "host_name": "李老师",
        "visit_date": "2026-03-28"
    }

    返回:
    {
        "success": true,
        "message": "访客登记成功",
        "application_id": 123
    }
    """
    try:
        data = request.get_json()

        # 获取参数
        visitor_name = data.get('visitor_name', '').strip()
        visitor_phone = data.get('visitor_phone', '').strip()
        id_card = data.get('id_card', '').strip()
        visit_purpose = data.get('visit_purpose', 'other')
        host_name = data.get('host_name', '').strip()
        visit_date_str = data.get('visit_date', '').strip()

        # 验证必填字段
        if not visitor_name:
            return jsonify({'error': '请输入访客姓名'}), 400

        if not visitor_phone or len(visitor_phone) != 11:
            return jsonify({'error': '请输入正确的11位手机号'}), 400

        if not id_card or len(id_card) != 18:
            return jsonify({'error': '请输入正确的18位身份证号'}), 400

        if not host_name:
            return jsonify({'error': '请输入被访人姓名'}), 400

        if not visit_date_str:
            return jsonify({'error': '请选择访问日期'}), 400

        # 解析访问日期
        try:
            from datetime import datetime
            visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '日期格式不正确'}), 400

        # 查找或创建访客用户
        visitor_user = User.query.filter_by(phone=visitor_phone).first()

        if not visitor_user:
            # 创建新的访客用户
            visitor_user = User(
                phone=visitor_phone,
                real_name=visitor_name,
                id_card=id_card,
                user_type='visitor',
                wechat_password='88',  # 访客默认密码
                status='active'
            )
            db.session.add(visitor_user)
            db.session.flush()
            current_app.logger.info(f"✅ 创建新访客用户: {visitor_name} ({visitor_phone})")
        else:
            # 更新现有访户信息
            visitor_user.real_name = visitor_name
            visitor_user.id_card = id_card
            current_app.logger.info(f"📝 更新访客信息: {visitor_name} ({visitor_phone})")

        # 创建访问申请记录（状态为pending，需要老师审批）
        application = VisitorApplication(
            applicant_id=visitor_user.id,
            visit_date=visit_date,
            visit_time_start=datetime.now().time(),
            visit_time_end=datetime.now().time(),
            visit_purpose=visit_purpose,
            target_person=host_name,
            application_status='pending'  # 待审批
        )

        db.session.add(application)
        db.session.commit()

        current_app.logger.info(
            f"✅ 访客登记成功 | "
            f"访客: {visitor_name} | "
            f"手机: {visitor_phone} | "
            f"被访人: {host_name} | "
            f"访问日期: {visit_date_str} | "
            f"申请ID: {application.id}"
        )

        return jsonify({
            'success': True,
            'message': '访客登记成功，请提醒访客到校时联系被访人获取验证码',
            'application_id': application.id,
            'visitor_name': visitor_name,
            'visit_date': visit_date_str
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"访客登记失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': '访客登记失败', 'details': str(e)}), 500
