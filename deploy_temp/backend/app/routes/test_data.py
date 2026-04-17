"""
测试数据生成和验证端点
"""

from flask import Blueprint, jsonify, request
from app import db
from app.models.user import User
from app.models.visit_application import VisitApplication
# QRCode model doesn't exist - using VisitApplication directly instead
from datetime import datetime, timedelta, time

# 创建测试蓝图
test_data_bp = Blueprint('test_data', __name__)

@test_data_bp.route('/create-test-visit', methods=['POST'])
def create_test_visit():
    """创建测试访问申请数据"""
    try:
        data = request.get_json()

        # 创建测试用户
        user = User.query.filter_by(username='test_security').first()
        if not user:
            user = User(
                username='test_security',
                email='test@example.com',
                password='test123456',
                user_type='teacher'
            )
            db.session.add(user)
            db.session.commit()

        # 创建测试访问申请
        start_date = datetime.now()
        end_date = start_date + timedelta(hours=2)

        visit_application = VisitApplication(
            visit_purpose=data.get('visit_purpose', '学术交流'),
            target_person=data.get('target_person', '张老师'),
            target_department=data.get('target_department', '教务处'),
            visit_date=start_date.date(),
            visit_time_start=start_date.time(),
            visit_time_end=end_date.time(),
            application_status='approved',
            approval_note='测试通过',
            created_at=start_date,
            applicant_id=user.id
        )

        # 设置访客信息
        visit_application.visitor_info = {
            'name': data.get('visitor_name', '测试访客'),
            'phone': data.get('visitor_phone', '13800138000'),
            'email': data.get('visitor_email', 'test@example.com')
        }

        db.session.add(visit_application)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '测试数据创建成功',
            'visit_id': visit_application.id,
            'qr_code_url': f"/api/qr-codes/generate/{visit_application.id}"
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@test_data_bp.route('/verify-test-visit/<int:application_id>', methods=['GET'])
def verify_test_visit(application_id):
    """验证测试访问申请"""
    try:
        visit_application = VisitApplication.query.get(application_id)
        if not visit_application:
            return jsonify({'error': '访问申请不存在'}), 404

        # 检查申请状态
        if visit_application.application_status != 'approved':
            return jsonify({
                'valid': False,
                'error': '访问申请未通过审批',
                'status': visit_application.application_status
            }), 400

        visitor_info = {
            'name': visit_application.visitor_info.get('name', '') if visit_application.visitor_info else '',
            'phone': visit_application.visitor_info.get('phone', '') if visit_application.visitor_info else '',
            'email': visit_application.visitor_info.get('email', '') if visit_application.visitor_info else '',
            'purpose': visit_application.visit_purpose,
            'target': visit_application.target_person,
            'date': visit_application.visit_date.strftime('%Y-%m-%d'),
            'time': f"{visit_application.visit_time_start}-{visit_application.visit_time_end}"
        }

        return jsonify({
            'valid': True,
            'message': '验证成功',
            'visitor_info': visitor_info,
            'application_id': visit_application.id
        })

    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500

@test_data_bp.route('/test-visits', methods=['GET'])
def list_test_visits():
    """获取所有测试访问申请"""
    try:
        # 使用qr_code字段中存储的访客姓名来查找测试数据
        visits = VisitApplication.query.join(VisitApplication.applicant).filter(
            User.username.like('test%')
        ).all()
        visits_list = []

        for visit in visits:
            visits_list.append({
                'id': visit.id,
                'visitor_name': visit.visitor_info.get('name', '') if visit.visitor_info else '',
                'visit_date': visit.visit_date.strftime('%Y-%m-%d'),
                'visit_time': f"{visit.visit_time_start}-{visit.visit_time_end}",
                'visit_purpose': visit.visit_purpose,
                'target_person': visit.target_person,
                'target_department': visit.target_department,
                'application_status': visit.application_status,
                'created_at': visit.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'qr_code_url': f"/api/qr-codes/generate/{visit.id}" if visit.application_status == 'approved' else None
            })

        return jsonify({
            'success': True,
            'visits': visits_list
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@test_data_bp.route('/reset-test-data', methods=['POST'])
def reset_test_data():
    """重置测试数据"""
    try:
        # 删除所有测试数据
        test_users = User.query.filter(User.username.like('test%')).all()
        for user in test_users:
            VisitApplication.query.filter_by(applicant_id=user.id).delete()
        User.query.filter(User.username.like('test%')).delete()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '测试数据已重置'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500