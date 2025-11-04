"""
二维码生成和验证API
"""

import qrcode
import io
import base64
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from PIL import Image, ImageDraw, ImageFont

from app import db
from app.models.user import User
from app.models.visit_application import VisitApplication

qr_codes_bp = Blueprint('qr_codes', __name__)

def generate_visit_qr_code(visit_application):
    """为访问申请生成二维码"""
    try:
        # 准备二维码数据
        # 安全获取访客信息
        visitor_name = ''
        if visit_application.visitor_info:
            if isinstance(visit_application.visitor_info, dict):
                visitor_name = visit_application.visitor_info.get('name', '')
            else:
                visitor_name = str(visit_application.visitor_info)

        qr_data = {
            'type': 'visit_application',
            'id': visit_application.id,
            'visitor_name': visitor_name,
            'visit_date': visit_application.visit_date.strftime('%Y-%m-%d'),
            'visit_time_start': visit_application.visit_time_start,
            'visit_time_end': visit_application.visit_time_end,
            'visit_purpose': visit_application.visit_purpose,
            'target_person': visit_application.target_person,
            'application_status': visit_application.application_status,
            'approval_note': visit_application.approval_note or '',
            'generated_at': datetime.utcnow().isoformat(),
            'verification_url': f"{current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')}/api/qr-codes/verify/{visit_application.id}"
        }

        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data, ensure_ascii=False))
        qr.make(fit=True)

        # 创建二维码图像
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # 添加标题和说明文字
        img_width, img_height = qr_img.size
        new_height = img_height + 100  # 额外空间用于文字
        new_img = Image.new('RGB', (img_width, new_height), 'white')
        new_img.paste(qr_img, (0, 0))

        draw = ImageDraw.Draw(new_img)

        try:
            # 尝试使用字体，如果没有则使用默认字体
            font_title = ImageFont.truetype("arial.ttf", 16)
            font_text = ImageFont.truetype("arial.ttf", 12)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

        # 添加标题
        title = "校友入校访问码"
        title_width = draw.textlength(title, font=font_title)
        title_x = (img_width - title_width) / 2
        draw.text((title_x, img_height + 10), title, fill="black", font=font_title)

        # 添加访问信息
        info_lines = [
            f"访客: {qr_data['visitor_name']}",
            f"日期: {qr_data['visit_date']}",
            f"时间: {qr_data['visit_time_start']}-{qr_data['visit_time_end']}",
            f"目的: {qr_data['visit_purpose']}"
        ]

        y_offset = img_height + 35
        for line in info_lines:
            if line:
                draw.text((10, y_offset), line, fill="black", font=font_text)
                y_offset += 15

        # 转换为字节流
        img_byte_arr = io.BytesIO()
        new_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return img_byte_arr

    except Exception as e:
        current_app.logger.error(f"生成二维码失败: {str(e)}")
        return None

@qr_codes_bp.route('/generate/<int:application_id>', methods=['GET'])
@jwt_required()
def generate_visit_qr(application_id):
    """生成访问申请的二维码"""
    try:
        current_user_id = get_jwt_identity()

        # 获取访问申请
        visit_application = VisitApplication.query.filter_by(
            id=application_id,
            applicant_id=current_user_id
        ).first()

        if not visit_application:
            return jsonify({'error': '访问申请不存在'}), 404

        # 只有已通过的申请才能生成二维码
        if visit_application.application_status != 'approved':
            return jsonify({'error': '只有已通过的访问申请才能生成二维码'}), 400

        # 生成二维码
        qr_img = generate_visit_qr_code(visit_application)
        if not qr_img:
            return jsonify({'error': '生成二维码失败'}), 500

        return send_file(
            qr_img,
            mimetype='image/png',
            as_attachment=False,
            download_name=f'visit_qr_{application_id}.png'
        )

    except Exception as e:
        current_app.logger.error(f"生成二维码失败: {str(e)}")
        return jsonify({'error': '生成二维码失败'}), 500

@qr_codes_bp.route('/generate/<int:application_id>/base64', methods=['GET'])
@jwt_required()
def generate_visit_qr_base64(application_id):
    """生成访问申请的二维码并返回base64编码"""
    try:
        current_user_id = get_jwt_identity()

        # 获取访问申请
        visit_application = VisitApplication.query.filter_by(
            id=application_id,
            applicant_id=current_user_id
        ).first()

        if not visit_application:
            return jsonify({'error': '访问申请不存在'}), 404

        # 只有已通过的申请才能生成二维码
        if visit_application.application_status != 'approved':
            return jsonify({'error': '只有已通过的访问申请才能生成二维码'}), 400

        # 生成二维码
        qr_img = generate_visit_qr_code(visit_application)
        if not qr_img:
            return jsonify({'error': '生成二维码失败'}), 500

        # 转换为base64
        qr_img.seek(0)
        img_base64 = base64.b64encode(qr_img.getvalue()).decode('utf-8')

        # 安全获取访客姓名
        visitor_name = ''
        if visit_application.visitor_info:
            if isinstance(visit_application.visitor_info, dict):
                visitor_name = visit_application.visitor_info.get('name', '')
            else:
                visitor_name = str(visit_application.visitor_info)

        return jsonify({
            'qr_code': f"data:image/png;base64,{img_base64}",
            'application_id': application_id,
            'visit_date': visit_application.visit_date.strftime('%Y-%m-%d'),
            'visit_time': f"{visit_application.visit_time_start}-{visit_application.visit_time_end}",
            'visitor_name': visitor_name
        })

    except Exception as e:
        current_app.logger.error(f"生成二维码失败: {str(e)}")
        return jsonify({'error': '生成二维码失败'}), 500

@qr_codes_bp.route('/verify/<int:application_id>', methods=['GET'])
def verify_visit_qr(application_id):
    """验证访问二维码（供门卫使用）"""
    try:
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
            visit_application.visit_time_start
        )

        # 如果访问时间已过，检查是否在当天有效期内
        if now > visit_datetime:
            visit_end_datetime = datetime.combine(
                visit_application.visit_date,
                visit_application.visit_time_end
            )
            if now > visit_end_datetime:
                return jsonify({'error': '访问时间已过期'}), 400

        # 安全获取访客信息
        visitor_name = ''
        visitor_phone = ''
        if visit_application.visitor_info:
            if isinstance(visit_application.visitor_info, dict):
                visitor_name = visit_application.visitor_info.get('name', '')
                visitor_phone = visit_application.visitor_info.get('phone', '')
            else:
                visitor_name = str(visit_application.visitor_info)

        # 返回验证结果
        return jsonify({
            'valid': True,
            'message': '访问申请有效',
            'application': {
                'id': visit_application.id,
                'visitor_name': visitor_name,
                'visitor_phone': visitor_phone,
                'visit_date': visit_application.visit_date.strftime('%Y-%m-%d'),
                'visit_time_start': visit_application.visit_time_start,
                'visit_time_end': visit_application.visit_time_end,
                'visit_purpose': visit_application.visit_purpose,
                'target_person': visit_application.target_person,
                'target_department': visit_application.target_department,
                'application_status': visit_application.application_status,
                'approval_note': visit_application.approval_note,
                'created_at': visit_application.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'applicant': {
                    'name': visit_application.applicant.real_name,
                    'email': visit_application.applicant.email
                } if visit_application.applicant else None
            }
        })

    except Exception as e:
        current_app.logger.error(f"验证二维码失败: {str(e)}")
        return jsonify({'error': '验证二维码失败'}), 500

@qr_codes_bp.route('/my-qr-codes', methods=['GET'])
@jwt_required()
def get_my_qr_codes():
    """获取用户当前有效的二维码列表"""
    try:
        current_user_id = get_jwt_identity()

        # 获取用户已通过的访问申请
        approved_visits = VisitApplication.query.filter_by(
            applicant_id=current_user_id,
            application_status='approved'
        ).filter(
            # 只显示今天及未来的访问
            VisitApplication.visit_date >= datetime.utcnow().date()
        ).order_by(VisitApplication.visit_date.asc()).all()

        qr_codes = []
        for visit in approved_visits:
            # 检查访问时间是否还有效
            visit_datetime = datetime.combine(visit.visit_date, visit.visit_time_end)

            if datetime.utcnow() <= visit_datetime:
                # 安全获取访客姓名
                visitor_name = ''
                if visit.visitor_info:
                    if isinstance(visit.visitor_info, dict):
                        visitor_name = visit.visitor_info.get('name', '')
                    else:
                        visitor_name = str(visit.visitor_info)

                qr_codes.append({
                    'id': visit.id,
                    'visit_date': visit.visit_date.strftime('%Y-%m-%d'),
                    'visit_time': f"{visit.visit_time_start}-{visit.visit_time_end}",
                    'visit_purpose': visit.visit_purpose,
                    'target_person': visit.target_person,
                    'visitor_name': visitor_name,
                    'is_today': visit.visit_date == datetime.utcnow().date()
                })

        return jsonify({'qr_codes': qr_codes})

    except Exception as e:
        current_app.logger.error(f"获取二维码列表失败: {str(e)}")
        return jsonify({'error': '获取二维码列表失败'}), 500