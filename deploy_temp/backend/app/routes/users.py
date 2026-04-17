"""
用户管理API
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app import db
from app.models.user import User
from app.models.alumni_profile import AlumniProfile

users_bp = Blueprint('users', __name__)

@users_bp.route('/alumni', methods=['GET'])
@jwt_required()
def get_alumni_list():
    """获取校友列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')

        query = User.query.filter_by(user_type='alumni', status='active')

        if search:
            query = query.filter(
                User.real_name.contains(search) |
                User.phone.contains(search) |
                User.email.contains(search)
            )

        # 关联校友档案进行搜索
        if search:
            query = query.outerjoin(AlumniProfile).filter(
                AlumniProfile.student_id.contains(search) |
                AlumniProfile.class_name.contains(search) |
                AlumniProfile.division.contains(search) |
                AlumniProfile.major.contains(search)
            )

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        alumni_list = []
        for user in pagination.items:
            alumni_data = user.to_dict(include_sensitive=True)
            alumni_list.append(alumni_data)

        return jsonify({
            'alumni': alumni_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取校友列表失败: {str(e)}")
        return jsonify({'error': '获取校友列表失败'}), 500

@users_bp.route('/alumni/<int:user_id>', methods=['GET'])
@jwt_required()
def get_alumni_detail(user_id):
    """获取校友详细信息"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        alumni = User.query.filter_by(id=user_id, user_type='alumni').first()
        if not alumni:
            return jsonify({'error': '校友不存在'}), 404

        alumni_data = alumni.to_dict(include_sensitive=True)

        # 脱敏处理敏感信息（只有管理员和本人可以看到完整信息）
        if current_user.user_type != 'admin' and current_user_id != user_id:
            if alumni_data.get('alumni_profile'):
                alumni_data['alumni_profile']['id_card'] = alumni_data['alumni_profile']['id_card'][-4:] + '*' * (len(alumni_data['alumni_profile']['id_card']) - 4) if alumni_data['alumni_profile'].get('id_card') else None

        return jsonify({'alumni': alumni_data}), 200

    except Exception as e:
        current_app.logger.error(f"获取校友详细信息失败: {str(e)}")
        return jsonify({'error': '获取校友详细信息失败'}), 500

@users_bp.route('/alumni/<int:user_id>/profile', methods=['PUT'])
@jwt_required()
def update_alumni_profile(user_id):
    """更新校友档案"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        alumni = User.query.filter_by(id=user_id, user_type='alumni').first()
        if not alumni:
            return jsonify({'error': '校友不存在'}), 404

        # 权限检查：只有本人、管理员、教师可以修改
        if (current_user_id != user_id and
            current_user.user_type not in ['admin', 'teacher']):
            return jsonify({'error': '没有权限修改此信息'}), 403

        data = request.get_json()

        # 获取或创建校友档案
        alumni_profile = AlumniProfile.query.filter_by(user_id=user_id).first()
        if not alumni_profile:
            alumni_profile = AlumniProfile(user_id=user_id)
            db.session.add(alumni_profile)

        # 更新字段
        updatable_fields = [
            'graduation_year', 'class_name', 'division', 'major',
            'contact_teacher', 'contact_teacher_phone',
            'emergency_contact', 'emergency_phone'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(alumni_profile, field, data[field])

        # 只有管理员可以修改学号和身份证号
        if current_user.user_type == 'admin':
            if 'student_id' in data:
                # 检查学号是否重复
                existing = AlumniProfile.query.filter(
                    AlumniProfile.student_id == data['student_id'],
                    AlumniProfile.user_id != user_id
                ).first()
                if existing:
                    return jsonify({'error': '学号已存在'}), 400
                alumni_profile.student_id = data['student_id']

            if 'id_card' in data:
                # 检查身份证号是否重复
                existing = AlumniProfile.query.filter(
                    AlumniProfile.id_card == data['id_card'],
                    AlumniProfile.user_id != user_id
                ).first()
                if existing:
                    return jsonify({'error': '身份证号已存在'}), 400
                alumni_profile.id_card = data['id_card']

        alumni_profile.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': '校友档案更新成功',
            'alumni': alumni.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新校友档案失败: {str(e)}")
        return jsonify({'error': '更新校友档案失败'}), 500

@users_bp.route('/teachers', methods=['GET'])
@jwt_required()
def get_teachers_list():
    """获取教师列表（用于选择接待人）"""
    try:
        search = request.args.get('search', '')

        query = User.query.filter_by(user_type='teacher', status='active')

        if search:
            query = query.filter(
                User.real_name.contains(search) |
                User.phone.contains(search) |
                User.email.contains(search)
            )

        teachers = query.all()
        teachers_list = []

        for teacher in teachers:
            teachers_list.append({
                'id': teacher.id,
                'real_name': teacher.real_name,
                'phone': teacher.phone,
                'email': teacher.email
            })

        return jsonify({'teachers': teachers_list}), 200

    except Exception as e:
        current_app.logger.error(f"获取教师列表失败: {str(e)}")
        return jsonify({'error': '获取教师列表失败'}), 500

@users_bp.route('/alumni/profile', methods=['GET'])
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

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """获取当前用户资料"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        user_data = user.to_dict(include_sensitive=True)

        return jsonify({'user': user_data}), 200

    except Exception as e:
        current_app.logger.error(f"获取用户资料失败: {str(e)}")
        return jsonify({'error': '获取用户资料失败'}), 500

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """更新当前用户资料"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        data = request.get_json()

        # 更新用户基本信息
        updatable_fields = ['real_name', 'email', 'phone']
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])

        # 更新用户的扩展信息字段（如果存在）
        if hasattr(user, 'alumni_info') and 'alumni_info' in data:
            user.alumni_info = data['alumni_info']
        if hasattr(user, 'work_info') and 'work_info' in data:
            user.work_info = data['work_info']

        # 如果是校友，更新校友档案
        if user.user_type == 'alumni':
            alumni_profile = AlumniProfile.query.filter_by(user_id=current_user_id).first()
            if not alumni_profile:
                alumni_profile = AlumniProfile(user_id=current_user_id)
                db.session.add(alumni_profile)

            # 更新校友档案字段
            alumni_fields = [
                'graduation_year', 'class_name', 'division', 'major',
                'student_id', 'id_card', 'contact_teacher', 'contact_teacher_phone',
                'emergency_contact', 'emergency_phone', 'class_teacher',
                'current_city', 'work_unit', 'position'
            ]

            for field in alumni_fields:
                if field in data:
                    setattr(alumni_profile, field, data[field])

            alumni_profile.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '个人资料更新成功',
            'user': user.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新用户资料失败: {str(e)}")
        return jsonify({'error': '更新用户资料失败'}), 500

# 车辆管理功能已移除
# @users_bp.route('/vehicles', methods=['GET'])
# @jwt_required()
# def get_user_vehicles():
#     """获取当前用户的车辆列表"""
#     try:
#         current_user_id = get_jwt_identity()
#         user = User.query.get(current_user_id)
#
#         if not user:
#             return jsonify({'error': '用户不存在'}), 404
#
#         # 只返回当前用户的车辆
#         vehicles = Vehicle.query.filter_by(user_id=current_user_id).all()
#
#         vehicles_list = []
#         for vehicle in vehicles:
#             vehicle_data = vehicle.to_dict()
#             vehicles_list.append(vehicle_data)
#
#         return jsonify({'vehicles': vehicles_list}), 200
#
#     except Exception as e:
#         current_app.logger.error(f"获取用户车辆列表失败: {str(e)}")
#         return jsonify({'error': '获取用户车辆列表失败'}), 500

@users_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    """搜索用户"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.user_type not in ['admin', 'teacher', 'security']:
            return jsonify({'error': '没有权限搜索用户'}), 403

        search = request.args.get('search', '')
        user_type = request.args.get('user_type', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = User.query.filter_by(status='active')

        if search:
            query = query.filter(
                User.real_name.contains(search) |
                User.username.contains(search) |
                User.phone.contains(search) |
                User.email.contains(search)
            )

        if user_type:
            query = query.filter_by(user_type=user_type)

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        users_list = []
        for user in pagination.items:
            user_data = user.to_dict()
            if user.alumni_profile:
                user_data['alumni_profile'] = user.alumni_profile.to_dict()
            users_list.append(user_data)

        return jsonify({
            'users': users_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"搜索用户失败: {str(e)}")
        return jsonify({'error': '搜索用户失败'}), 500