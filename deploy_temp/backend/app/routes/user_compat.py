"""
用户兼容性API - 匹配前端请求的路径
"""

from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.routes.users import get_user_profile, update_user_profile

user_compat_bp = Blueprint('user_compat', __name__)

@user_compat_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户资料 - /api/user/profile"""
    return get_user_profile()

@user_compat_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新当前用户资料 - /api/user/profile"""
    return update_user_profile()

