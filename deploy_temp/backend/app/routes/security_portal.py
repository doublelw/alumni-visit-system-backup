"""
保安专用端API
处理保安签到、访客验证、放行等功能
"""

from datetime import datetime, date, time, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from sqlalchemy import and_, or_

from app import db
from app.models.user import User
from app.models.visit_application import VisitApplication
from app.models.face_data import FaceData
from app.models.security import SecurityShift, SecurityAccessLog

security_portal_bp = Blueprint('security_portal', __name__)

@security_portal_bp.route('/login', methods=['POST'])
def security_login():
    """保安登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400

        # 验证保安身份
        security = User.query.filter_by(
            username=username,
            user_type='security',
            status='active'
        ).first()

        if not security or not security.check_password(password):
            return jsonify({'error': '用户名或密码错误'}), 401

        # 创建访问令牌
        access_token = create_access_token(identity=security.id)

        return jsonify({
            'access_token': access_token,
            'security': security.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error(f"保安登录失败: {str(e)}")
        return jsonify({'error': '登录失败'}), 500

@security_portal_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_security_profile():
    """获取保安个人信息"""
    try:
        current_user_id = get_jwt_identity()
        security = User.query.get(current_user_id)

        if not security or security.user_type != 'security':
            return jsonify({'error': '无权限访问'}), 403

        # 获取当前班次信息
        today = date.today()
        current_shift = SecurityShift.query.filter_by(
            security_id=security.id,
            shift_date=today
        ).first()

        profile_data = security.to_dict()
        if current_shift:
            profile_data['current_shift'] = current_shift.to_dict()

        return jsonify(profile_data), 200

    except Exception as e:
        current_app.logger.error(f"获取保安信息失败: {str(e)}")
        return jsonify({'error': '获取信息失败'}), 500

@security_portal_bp.route('/shift/check-in', methods=['POST'])
@jwt_required()
def check_in_shift():
    """保安签到"""
    try:
        current_user_id = get_jwt_identity()
        security = User.query.get(current_user_id)

        if not security or security.user_type != 'security':
            return jsonify({'error': '无权限访问'}), 403

        today = date.today()
        now = datetime.utcnow()

        # 查找今日班次
        shift = SecurityShift.query.filter_by(
            security_id=security.id,
            shift_date=today
        ).first()

        if not shift:
            # 如果没有预设班次，创建一个
            shift = SecurityShift(
                security_id=security.id,
                shift_date=today,
                shift_start=time(8, 0),  # 默认8点开始
                shift_end=time(17, 0),   # 默认17点结束
                status='checked_in'
            )
        else:
            shift.status = 'checked_in'

        shift.check_in_time = now
        shift.updated_at = now

        db.session.add(shift)
        db.session.commit()

        return jsonify({
            'message': '签到成功',
            'shift': shift.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error(f"保安签到失败: {str(e)}")
        return jsonify({'error': '签到失败'}), 500

@security_portal_bp.route('/shift/check-out', methods=['POST'])
@jwt_required()
def check_out_shift():
    """保安签退"""
    try:
        current_user_id = get_jwt_identity()
        security = User.query.get(current_user_id)

        if not security or security.user_type != 'security':
            return jsonify({'error': '无权限访问'}), 403

        today = date.today()
        now = datetime.utcnow()

        # 查找今日班次
        shift = SecurityShift.query.filter_by(
            security_id=security.id,
            shift_date=today
        ).first()

        if not shift:
            return jsonify({'error': '未找到今日班次记录'}), 404

        shift.status = 'checked_out'
        shift.check_out_time = now
        shift.updated_at = now

        db.session.add(shift)
        db.session.commit()

        return jsonify({
            'message': '签退成功',
            'shift': shift.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error(f"保安签退失败: {str(e)}")
        return jsonify({'error': '签退失败'}), 500

@security_portal_bp.route('/visit/verify-qr', methods=['POST'])
@jwt_required()
def verify_visit_qr():
    """通过二维码验证访客信息"""
    try:
        current_user_id = get_jwt_identity()
        security = User.query.get(current_user_id)

        if not security or security.user_type != 'security':
            return jsonify({'error': '无权限访问'}), 403

        data = request.get_json()
        application_id = data.get('application_id')

        if not application_id:
            return jsonify({'error': '访问申请编号不能为空'}), 400

        # 获取访问申请
        visit_application = VisitApplication.query.get(application_id)

        if not visit_application:
            return jsonify({'error': '访问申请不存在'}), 404

        # 检查申请状态
        if visit_application.application_status != 'approved':
            return jsonify({
                'error': '访问申请未通过审批',
                'status': visit_application.application_status
            }), 400

        # 检查访问时间是否有效
        now = datetime.utcnow()
        visit_datetime = datetime.combine(
            visit_application.visit_date,
            datetime.strptime(visit_application.visit_time_start, '%H:%M').time()
        )

        # 如果访问时间已过，检查是否在当天有效期内
        if now > visit_datetime:
            visit_end_datetime = datetime.combine(
                visit_application.visit_date,
                datetime.strptime(visit_application.visit_time_end, '%H:%M').time()
            )
            if now > visit_end_datetime:
                return jsonify({'error': '访问时间已过期'}), 400

        # 记录验证操作
        access_log = SecurityAccessLog(
            security_id=current_user_id,
            visit_application_id=application_id,
            action_type='scan_qr',
            verification_method='qr_code',
            action_result='success',
            access_granted=False  # 暂未放行
        )
        db.session.add(access_log)
        db.session.commit()

        return jsonify({
            'valid': True,
            'message': '访问申请有效',
            'application': visit_application.to_dict(),
            'log_id': access_log.id
        }), 200

    except Exception as e:
        current_app.logger.error(f"二维码验证失败: {str(e)}")
        return jsonify({'error': '验证失败'}), 500

@security_portal_bp.route('/visit/verify-face', methods=['POST'])
@jwt_required()
def verify_visit_face():
    """通过人脸识别验证访客"""
    try:
        current_user_id = get_jwt_identity()
        security = User.query.get(current_user_id)

        if not security or security.user_type != 'security':
            return jsonify({'error': '无权限访问'}), 403

        data = request.get_json()
        image_data = data.get('image_data')

        if not image_data:
            return jsonify({'error': '人脸图像数据不能为空'}), 400

        # 这里需要集成实际的人脸识别算法
        # 目前先模拟验证过程
        # TODO: 集成真正的人脸识别服务

        # 模拟人脸匹配分数
        face_match_score = 0.85  # 模拟85%匹配度

        if face_match_score < 0.7:  # 设定阈值为70%
            # 记录失败验证
            access_log = SecurityAccessLog(
                security_id=current_user_id,
                visit_application_id=0,  # 人脸识别时可能没有申请ID
                action_type='face_verify',
                verification_method='face_recognition',
                action_result='failed',
                access_granted=False,
                face_match_score=face_match_score,
                notes='人脸匹配度不足'
            )
            db.session.add(access_log)
            db.session.commit()

            return jsonify({
                'error': '人脸识别失败，请重试或使用其他验证方式',
                'match_score': face_match_score
            }), 400

        # 记录成功验证
        access_log = SecurityAccessLog(
            security_id=current_user_id,
            visit_application_id=0,
            action_type='face_verify',
            verification_method='face_recognition',
            action_result='success',
            access_granted=False,
            face_match_score=face_match_score
        )
        db.session.add(access_log)
        db.session.commit()

        return jsonify({
            'valid': True,
            'message': '人脸识别成功',
            'match_score': face_match_score,
            'log_id': access_log.id
        }), 200

    except Exception as e:
        current_app.logger.error(f"人脸识别验证失败: {str(e)}")
        return jsonify({'error': '人脸识别失败'}), 500

@security_portal_bp.route('/visit/verify-face-match', methods=['POST'])
@jwt_required()
def verify_face_match():
    """通过人脸识别比对当日访问申请"""
    try:
        current_user_id = get_jwt_identity()
        security = User.query.get(current_user_id)

        if not security or security.user_type != 'security':
            return jsonify({'error': '无权限访问'}), 403

        data = request.get_json()
        image_data = data.get('image_data')
        match_today_applications = data.get('match_today_applications', False)

        if not image_data:
            return jsonify({'error': '人脸图像数据不能为空'}), 400

        # 获取今日的访问申请
        today = date.today()
        query = VisitApplication.query.filter_by(
            application_status='approved',
            visit_date=today
        )

        approved_applications = query.all()

        if not approved_applications:
            return jsonify({
                'matches': [],
                'message': '今日没有已批准的访问申请'
            }), 200

        # 模拟人脸匹配过程
        # 在实际应用中，这里会调用真正的人脸识别服务
        matches = []
        for app in approved_applications:
            # 检查该申请是否有注册的人脸数据
            if app.applicant and app.applicant.face_data:
                # 模拟人脸匹配度（实际应用中应该调用人脸识别API）
                import random
                match_score = random.uniform(60, 95)  # 模拟60-95%的匹配度

                if match_score > 75:  # 只显示匹配度大于75%的结果
                    matches.append({
                        'id': app.id,
                        'visitor_info': app.visitor_info,
                        'visit_date': app.visit_date.strftime('%Y-%m-%d'),
                        'visit_time_start': app.visit_time_start,
                        'visit_time_end': app.visit_time_end,
                        'visit_purpose': app.visit_purpose,
                        'target_person': app.target_person,
                        'target_department': app.target_department,
                        'application_status': app.application_status,
                        'match_score': round(match_score, 1),
                        'applicant_name': app.applicant.real_name if app.applicant else None
                    })

        # 按匹配度排序
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        # 记录人脸识别操作
        access_log = SecurityAccessLog(
            security_id=current_user_id,
            visit_application_id=matches[0]['id'] if matches else 0,
            action_type='face_verify',
            verification_method='face_recognition',
            action_result='success' if matches else 'failed',
            access_granted=False,
            face_match_score=matches[0]['match_score'] if matches else 0,
            notes=f'识别到{len(matches)}个匹配申请' if matches else '未找到匹配申请'
        )
        db.session.add(access_log)
        db.session.commit()

        return jsonify({
            'matches': matches,
            'message': f'找到{len(matches)}个匹配的访问申请' if matches else '未找到匹配的访问申请'
        }), 200

    except Exception as e:
        current_app.logger.error(f"人脸比对失败: {str(e)}")
        return jsonify({'error': '人脸比对失败'}), 500

@security_portal_bp.route('/visit/grant-access', methods=['POST'])
@jwt_required()
def grant_visit_access():
    """允许访客进入"""
    try:
        current_user_id = get_jwt_identity()
        security = User.query.get(current_user_id)

        if not security or security.user_type != 'security':
            return jsonify({'error': '无权限访问'}), 403

        data = request.get_json()
        application_id = data.get('application_id')
        log_id = data.get('log_id')
        notes = data.get('notes', '')

        if not application_id:
            return jsonify({'error': '访问申请编号不能为空'}), 400

        # 获取访问申请
        visit_application = VisitApplication.query.get(application_id)
        if not visit_application:
            return jsonify({'error': '访问申请不存在'}), 404

        # 更新操作记录
        if log_id:
            access_log = SecurityAccessLog.query.get(log_id)
            if access_log:
                access_log.action_type = 'grant_access'
                access_log.access_granted = True
                access_log.notes = notes
                access_log.updated_at = datetime.utcnow()
        else:
            # 创建新的放行记录
            access_log = SecurityAccessLog(
                security_id=current_user_id,
                visit_application_id=application_id,
                action_type='grant_access',
                verification_method='manual',
                action_result='success',
                access_granted=True,
                notes=notes
            )
            db.session.add(access_log)

        db.session.commit()

        return jsonify({
            'message': '访客已成功放行',
            'access_time': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        current_app.logger.error(f"放行操作失败: {str(e)}")
        return jsonify({'error': '放行失败'}), 500

@security_portal_bp.route('/logs', methods=['GET', 'POST'])
@jwt_required()
def handle_access_logs():
    """处理操作记录 - 获取或创建"""
    try:
        current_user_id = get_jwt_identity()
        security = User.query.get(current_user_id)

        if not security or security.user_type != 'security':
            return jsonify({'error': '无权限访问'}), 403

        if request.method == 'POST':
            """创建操作记录"""
            data = request.get_json()

            # 创建访问日志
            access_log = SecurityAccessLog(
                security_id=current_user_id,
                visit_application_id=data.get('visit_application_id', 0),
                action_type=data.get('action_type', 'manual_entry'),
                verification_method=data.get('verification_method', 'manual'),
                action_result=data.get('action_result', 'success'),
                access_granted=data.get('access_granted', True),
                visitor_name=data.get('visitor_name'),
                visitor_phone=data.get('visitor_phone'),
                visit_purpose=data.get('visit_purpose'),
                target_person=data.get('target_person'),
                companions=data.get('companions', []),
                notes=data.get('notes', ''),
                face_match_score=data.get('face_match_score')
            )

            db.session.add(access_log)
            db.session.commit()

            return jsonify({
                'message': '操作记录已创建',
                'log_id': access_log.id
            }), 201

        else:  # GET method
            """获取操作记录"""
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            action_type = request.args.get('action_type')

            # 构建查询
            query = SecurityAccessLog.query.filter_by(security_id=current_user_id)

            if start_date:
                query = query.filter(SecurityAccessLog.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
            if end_date:
                query = query.filter(SecurityAccessLog.created_at <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
            if action_type:
                query = query.filter_by(action_type=action_type)

            # 排序和分页
            query = query.order_by(SecurityAccessLog.created_at.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            logs = [log.to_dict() for log in pagination.items]

            return jsonify({
                'logs': logs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }), 200

    except Exception as e:
        current_app.logger.error(f"处理操作记录失败: {str(e)}")
        return jsonify({'error': '处理记录失败'}), 500