"""
校友相关API
"""

from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

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