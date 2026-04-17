"""
外部访客路由
老师为外部访客（送货、拜访等）创建访问申请
"""

from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.user import User
from app.models.visit_application import VisitApplication
from datetime import datetime, timedelta
import random
import string

external_visitor_bp = Blueprint('external_visitor', __name__)


def generate_visitor_code():
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))


@external_visitor_bp.route('/api/external-visitor/create', methods=['POST'])
def create_external_visitor():
    """
    创建外部访客申请

    请求体:
    {
        "visitor_name": "张三",
        "visitor_phone": "13800000001",
        "visitor_company": "XX快递",
        "visit_purpose": "送货",
        "contact_person": "李老师",
        "visit_date": "2026-03-28",
        "notes": "备注信息"
    }

    返回:
    {
        "success": true,
        "data": {
            "visitor_code": "123456",
            "message": "访客申请已创建"
        }
    }
    """

    try:
        data = request.get_json()

        visitor_name = data.get('visitor_name', '').strip()
        visitor_phone = data.get('visitor_phone', '').strip()
        visitor_company = data.get('visitor_company', '').strip()
        visit_purpose = data.get('visit_purpose', '拜访').strip()
        contact_person = data.get('contact_person', '').strip()
        visit_date_str = data.get('visit_date', '').strip()
        notes = data.get('notes', '').strip()

        # 验证必填字段
        if not visitor_name:
            return jsonify({'error': '访客姓名不能为空'}), 400
        if not visitor_phone:
            return jsonify({'error': '联系电话不能为空'}), 400
        if not contact_person:
            return jsonify({'error': '联系人不能为空'}), 400

        # 检查手机号是否已存在
        existing_query = db.text("""
            SELECT va.id, va.application_status, va.visit_date
            FROM visit_applications va
            WHERE va.qr_code = :visitor_phone
            ORDER BY va.created_at DESC
            LIMIT 1
        """)
        existing = db.session.execute(existing_query, {'visitor_phone': visitor_phone}).fetchone()

        if existing:
            existing_id, status, existing_date = existing
            # 如果是已批准的申请且在有效期内（7天）
            if status == 'approved' and existing_date:
                existing_date = datetime.strptime(existing_date, '%Y-%m-%d').date()
                if (datetime.now().date() - existing_date).days < 7:
                    # 查找验证码
                    code_query = db.text("""
                        SELECT qr_code FROM visit_applications WHERE id = :id
                    """)
                    code_result = db.session.execute(code_query, {'id': existing_id}).fetchone()
                    if code_result and code_result[0] and len(code_result[0]) == 6:
                        return jsonify({
                            'success': True,
                            'data': {
                                'visitor_code': code_result[0],
                                'message': '该访客已有有效验证码（7天有效期内）',
                                'is_existing': True
                            }
                        })

        # 生成验证码
        visitor_code = generate_visitor_code()

        # 处理访问日期
        if visit_date_str:
            try:
                visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '日期格式错误，应为YYYY-MM-DD'}), 400
        else:
            visit_date = datetime.now().date()

        # 创建访客信息
        visitor_info = {
            'visitor_name': visitor_name,
            'visitor_phone': visitor_phone,
            'visitor_company': visitor_company,
            'visitor_type': 'external_visitor',
            'contact_person': contact_person,
            'notes': notes
        }

        # 创建访客申请记录（不需要applicant_id，使用0或-1）
        now = datetime.now()

        insert_query = db.text("""
            INSERT INTO visit_applications (
                applicant_id, visit_date, visit_time_start, visit_time_end,
                visit_purpose, target_person, qr_code, application_status,
                approved_by, approval_time, visit_started, created_at, updated_at
            ) VALUES (0, :visit_date, '08:00', '20:00', :visit_purpose,
                    :contact_person, :qr_code, 'approved', 0, :approval_time,
                    0, :created_at, :updated_at)
        """)

        db.session.execute(insert_query, {
            'visit_date': visit_date.strftime('%Y-%m-%d'),
            'visit_purpose': f"{visit_purpose} - {visitor_company}" if visitor_company else visit_purpose,
            'contact_person': contact_person,
            'qr_code': visitor_code,
            'approval_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': now.strftime('%Y-%m-%d %H:%M:%S')
        })

        visitor_app_id = db.session.execute(db.text("SELECT last_insert_rowid()")).scalar()

        # 更新qr_code字段，包含完整访客信息
        qr_data = {
            'type': 'visit_application',
            'id': visitor_app_id,
            'timestamp': now.isoformat(),
            'uuid': str(random.randint(100000, 999999)),
            'visitor_info': visitor_info
        }

        import json
        update_query = db.text("""
            UPDATE visit_applications
            SET qr_code = :visitor_code,
                application_status = 'approved'
            WHERE id = :id
        """)
        db.session.execute(update_query, {
            'id': visitor_app_id,
            'visitor_code': visitor_code
        })

        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'visitor_code': visitor_code,
                'visitor_name': visitor_name,
                'contact_person': contact_person,
                'visit_purpose': visit_purpose,
                'visit_date': visit_date.strftime('%Y-%m-%d'),
                'message': f'访客申请已创建，验证码: {visitor_code}'
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建外部访客申请失败: {str(e)}")
        return jsonify({'error': f'创建访客申请失败: {str(e)}'}), 500


@external_visitor_bp.route('/api/external-visitor/validate', methods=['POST'])
def validate_external_visitor():
    """
    验证外部访客（门卫使用）

    请求体:
    {
        "code": "123456"
    }

    返回:
    {
        "success": true,
        "data": {
            "visitor_name": "张三",
            "visitor_phone": "13800000001",
            "visitor_company": "XX快递",
            "contact_person": "李老师",
            "visit_purpose": "送货",
            "approved_at": "2026-03-27 14:00"
        }
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '').strip()

        if not code or len(code) != 6:
            return jsonify({'error': '验证码必须是6位数字'}), 400

        # 查询访客信息
        query = db.text("""
            SELECT va.id, va.visit_date, va.visit_purpose, va.target_person,
                   va.approval_time, va.application_status
            FROM visit_applications va
            WHERE va.qr_code = :code
            AND va.application_status = 'approved'
            ORDER BY va.created_at DESC
            LIMIT 1
        """)

        result = db.session.execute(query, {'code': code}).fetchone()

        if not result:
            return jsonify({'error': '验证码无效或已过期'}), 404

        visitor_id, visit_date, visit_purpose, contact_person, approval_time, status = result

        # 格式化审批时间
        try:
            if approval_time and hasattr(approval_time, 'strftime'):
                approval_time_str = approval_time.strftime('%Y-%m-%d %H:%M')
            else:
                approval_time_str = str(approval_time) if approval_time else None
        except:
            approval_time_str = None

        return jsonify({
            'success': True,
            'data': {
                'code_type': 'external_visitor',
                'valid': True,
                'message': '验证成功 - 外部访客',
                'person_info': {
                    'visitor_name': '外部访客',
                    'visitor_type': 'external_visitor',
                    'user_type_label': '外部访客',
                    'visit_purpose': visit_purpose,
                    'host_name': contact_person,
                    'approved_at': approval_time_str
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"验证外部访客失败: {str(e)}")
        return jsonify({'error': f'验证失败: {str(e)}'}), 500
