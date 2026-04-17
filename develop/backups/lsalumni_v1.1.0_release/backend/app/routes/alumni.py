"""
校友相关API
"""

from flask import Blueprint, jsonify, current_app, request, render_template_string
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app import db
from app.models.user import User
from app.models.alumni_profile import AlumniProfile

alumni_bp = Blueprint('alumni', __name__)

@alumni_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_alumni_profile():
    """获取校友档案"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        if user.user_type != 'alumni':
            return jsonify({'error': '非校友用户无权访问此接口'}), 403

        user_data = user.to_dict(include_sensitive=True)

        # 添加校友档案信息
        if hasattr(user, 'alumni_profile') and user.alumni_profile:
            alumni_profile = user.alumni_profile.to_dict()
            # 隐藏敏感信息
            if alumni_profile.get('id_card'):
                alumni_profile['id_card'] = alumni_profile['id_card'][-4:] + '*' * (len(alumni_profile['id_card']) - 4)
            user_data['alumni_profile'] = alumni_profile

        return jsonify({'user': user_data}), 200

    except Exception as e:
        current_app.logger.error(f"获取校友档案失败: {str(e)}")
        return jsonify({'error': '获取校友档案失败'}), 500

@alumni_bp.route('/profile/verify/<int:user_id>', methods=['GET'])
def verify_alumni_profile(user_id):
    """验证校友档案 - 用于QR码扫描"""
    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': '校友不存在'}), 404

        if user.user_type != 'alumni':
            return jsonify({'error': '非校友用户'}), 403

        user_data = user.to_dict()

        # 添加校友档案信息
        alumni_data = None
        if hasattr(user, 'alumni_profile') and user.alumni_profile:
            alumni_data = user.alumni_profile.to_dict()
            # 隐藏敏感信息用于显示
            if alumni_data.get('id_card'):
                alumni_data['id_card'] = alumni_data['id_card'][-4:] + '*' * (len(alumni_data['id_card']) - 4)

        # 根据请求类型返回不同格式
        if request.args.get('format') == 'json':
            return jsonify({
                'success': True,
                'user': user_data,
                'alumni_profile': alumni_data,
                'verify_time': datetime.now().isoformat()
            }), 200
        else:
            # 返回简单的验证页面
            html_template = """
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>校友身份验证</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .header { text-align: center; margin-bottom: 30px; }
                    .success { color: #28a745; font-size: 48px; text-align: center; margin-bottom: 20px; }
                    .info-item { margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px; }
                    .label { font-weight: bold; color: #333; display: inline-block; width: 100px; }
                    .value { color: #666; }
                    .footer { text-align: center; margin-top: 30px; color: #999; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>校友身份验证</h1>
                    </div>
                    <div class="success">✓</div>
                    <div class="info-item">
                        <span class="label">姓名：</span>
                        <span class="value">{{ real_name }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">学号：</span>
                        <span class="value">{{ student_id }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">毕业年份：</span>
                        <span class="value">{{ graduation_year }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">班级：</span>
                        <span class="value">{{ class_name }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">验证时间：</span>
                        <span class="value">{{ verify_time }}</span>
                    </div>
                    <div class="footer">
                        此验证信息由辽宁省实验中学校友入校登记系统提供
                    </div>
                </div>
            </body>
            </html>
            """

            return render_template_string(html_template,
                real_name=user_data.get('real_name', '未知'),
                student_id=alumni_data.get('student_id', 'N/A') if alumni_data else 'N/A',
                graduation_year=alumni_data.get('graduation_year', 'N/A') if alumni_data else 'N/A',
                class_name=alumni_data.get('class_name', 'N/A') if alumni_data else 'N/A',
                verify_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ), 200

    except Exception as e:
        current_app.logger.error(f"验证校友档案失败: {str(e)}")
        return jsonify({'error': '验证失败'}), 500