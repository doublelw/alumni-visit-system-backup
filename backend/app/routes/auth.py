"""
认证相关API
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import re
import time

from app import db
from app.models import User, AlumniProfile

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/test')
def test():
    return jsonify({'message': 'Auth blueprint is working!'})

@auth_bp.route('/test-users')
def get_test_users():
    """获取测试用户列表（用于登录页自动填充）"""
    try:
        # 获取所有活跃的测试用户
        test_users = User.query.filter_by(status='active').all()

        # 按用户类型分类并添加显示信息
        user_categories = {
            'alumni': [],
            'teacher': [],
            'student': [],
            'parent': [],
            'security': [],
            'admin': []
        }

        # 定义已知用户的正确密码
        known_passwords = {
            'admin': 'admin123',
            'zhang_xiaoming': 'student123',
            'li_laoshi': 'teacher123',
            'zhang_fumu': 'parent123',
            'student01': '123456',
            'security01': '123456',
            'security02': '123456',
            'teacher01': '123456',
            'parent01': '123456',
            'alumni001': 'test123456',
            'security001': 'security123',
            'security002': 'security123',
            'test_security_api': 'test123456',
            'test_student004': 'test123456'
        }

        for user in test_users:
            # 只包含常见的测试用户类型
            if user.user_type in user_categories:
                user_info = {
                    'username': user.username,
                    'real_name': user.real_name,
                    'user_type': user.user_type,
                    'password': known_passwords.get(user.username, '123456'),
                    'display_name': user.real_name or user.username
                }

                # 限制每种类型最多显示2个用户，避免界面过于拥挤
                if len(user_categories[user.user_type]) < 2:
                    user_categories[user.user_type].append(user_info)

        # 格式化返回数据，与前端现有的按钮布局匹配
        response_data = {
            'success': True,
            'users': {
                'alumni001': user_categories['alumni'][0] if user_categories['alumni'] else None,
                'li_laoshi': user_categories['teacher'][0] if user_categories['teacher'] else None,
                'zhang_xiaoming': user_categories['student'][0] if user_categories['student'] else None,
                'zhang_fumu': user_categories['parent'][0] if user_categories['parent'] else None,
                'admin': user_categories['admin'][0] if user_categories['admin'] else None,
                'security001': user_categories['security'][0] if user_categories['security'] else None
            }
        }

        # 过滤掉None值
        response_data['users'] = {k: v for k, v in response_data['users'].items() if v is not None}

        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"获取测试用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取测试用户列表失败'
        }), 500

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """验证密码强度"""
    if len(password) < 8:
        return False, "密码长度至少8位"
    if not re.search(r'[A-Za-z]', password):
        return False, "密码必须包含字母"
    if not re.search(r'\d', password):
        return False, "密码必须包含数字"
    return True, "密码格式正确"

def validate_username(username):
    """验证用户名格式"""
    if len(username) < 4 or len(username) > 20:
        return False, "用户名长度应在4-20个字符之间"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    return True, "用户名格式正确"

def validate_id_card(id_card):
    """验证身份证号格式"""
    if not re.match(r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$', id_card):
        return False, "身份证号格式不正确"

    # 验证校验码
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    checksums = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    sum_val = 0
    for i in range(17):
        sum_val += int(id_card[i]) * weights[i]

    checksum = checksums[sum_val % 11]
    if id_card[17].upper() != checksum:
        return False, "身份证号校验码不正确"

    return True, "身份证号格式正确"

@auth_bp.route('/register', methods=['POST'])
def register():
    """校友注册"""
    try:
        data = request.get_json()
        current_app.logger.info(f"收到注册请求数据: {data}")  # 调试日志

        # 验证基本信息必填字段
        basic_fields = ['username', 'password', 'realName', 'email', 'phone', 'idCard']
        for field in basic_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return jsonify({'success': False, 'message': f'{field}不能为空'}), 400

        # 验证校友信息必填字段
        alumni_fields = ['graduationYear', 'classNumber', 'division', 'major', 'classTeacher']
        for field in alumni_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return jsonify({'success': False, 'message': f'{field}不能为空'}), 400

        # 验证工作信息必填字段
        work_fields = ['currentCity', 'workUnit', 'position']
        for field in work_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return jsonify({'success': False, 'message': f'{field}不能为空'}), 400

        # 紧急联系人信息改为选填
        emergency_fields = ['emergencyContact', 'emergencyPhone']
        for field in emergency_fields:
            if data.get(field) and data.get(field).strip() != '':
                # 验证格式
                if field == 'emergencyPhone' and not validate_phone(data[field]):
                    return jsonify({'success': False, 'message': '紧急联系人电话格式不正确'}), 400

        # 验证服务条款
        if not data.get('agreeTerms'):
            return jsonify({'success': False, 'message': '请同意服务条款和隐私政策'}), 400

        # 验证数据格式
        is_valid, msg = validate_username(data['username'])
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400

        if not validate_email(data['email']):
            return jsonify({'success': False, 'message': '邮箱格式不正确'}), 400

        if not validate_phone(data['phone']):
            return jsonify({'success': False, 'message': '手机号格式不正确'}), 400

        is_valid, msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400

        is_valid, msg = validate_id_card(data['idCard'])
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400

        # 验证紧急联系人电话（如果提供了的话）
        if data.get('emergencyPhone') and data.get('emergencyPhone').strip() != '':
            if not validate_phone(data['emergencyPhone']):
                return jsonify({'success': False, 'message': '紧急联系人电话格式不正确'}), 400

        # 验证毕业年份
        try:
            graduation_year = int(data['graduationYear'])
            current_year = datetime.now().year
            if graduation_year < 1950 or graduation_year > current_year:
                return jsonify({'success': False, 'message': f'毕业年份应在1950年至{current_year}年之间'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': '毕业年份格式不正确'}), 400

        # 验证密码确认
        if data.get('confirmPassword') != data['password']:
            return jsonify({'success': False, 'message': '两次输入的密码不一致'}), 400

        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': '邮箱已存在'}), 400

        if User.query.filter_by(phone=data['phone']).first():
            return jsonify({'success': False, 'message': '手机号已存在'}), 400

        # 检查身份证号是否已存在
        if AlumniProfile.query.filter_by(id_card=data['idCard']).first():
            return jsonify({'success': False, 'message': '该身份证号已被注册'}), 400

        # 创建用户
        user = User(
            username=data['username'],
            real_name=data['realName'],
            email=data['email'],
            phone=data['phone'],
            user_type='alumni',
            status='active'  # 自动审核通过
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.flush()  # 获取用户ID

        # 创建校友档案
        alumni_profile = AlumniProfile(
            user_id=user.id,
            student_id=data.get('studentId', f"AUTO{int(time.time())}"),  # 生成默认学号
            graduation_year=graduation_year,
            class_name=data['classNumber'],
            division=data['division'],  # 修复字段名
            major=data['major'],
            id_card=data['idCard'],
            class_teacher=data['classTeacher'],
            contact_teacher=data.get('contactTeacher', '未指定'),
            contact_teacher_phone=data.get('contactTeacherPhone', ''),
            emergency_contact=data.get('emergencyContact', ''),  # 修复：提供默认值
            emergency_phone=data.get('emergencyPhone', ''),  # 修复：提供默认值
            # 工作信息
            current_city=data['currentCity'],
            work_unit=data['workUnit'],
            position=data['position'],
            notes=data.get('notes', ''),
            approval_status='approved'  # 自动审核通过
        )

        db.session.add(alumni_profile)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '注册成功！欢迎加入实验中学校友大家庭，您现在可以直接登录系统。',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"注册失败: {str(e)}")
        return jsonify({'success': False, 'message': '注册失败，请稍后重试'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()

        if not data.get('username') or not data.get('password'):
            return jsonify({'error': '用户名和密码不能为空'}), 400

        # 查找用户
        user = User.query.filter_by(username=data['username']).first()

        # 详细错误信息
        if not user:
            return jsonify({'error': '用户不存在，请检查用户名'}), 401

        if not user.check_password(data['password']):
            return jsonify({'error': '密码错误，请重新输入'}), 401

        if user.status != 'active':
            return jsonify({'error': f'账户已被{user.status}，请联系管理员'}), 401

        # 生成访问令牌
        access_token = create_access_token(
            identity=str(user.id),  # 转换为字符串
            expires_delta=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        )

        return jsonify({
            'message': '登录成功',
            'access_token': access_token,
            'user': user.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        current_app.logger.error(f"登录失败: {str(e)}")
        return jsonify({'error': '登录失败，请稍后重试'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """刷新令牌"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user or user.status != 'active':
            return jsonify({'error': '用户不存在或已被禁用'}), 401

        access_token = create_access_token(
            identity=str(current_user_id),  # 转换为字符串
            expires_delta=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        )

        return jsonify({
            'access_token': access_token
        }), 200

    except Exception as e:
        current_app.logger.error(f"刷新令牌失败: {str(e)}")
        return jsonify({'error': '刷新令牌失败'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        return jsonify({
            'user': user.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({'error': '获取用户信息失败'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not old_password or not new_password:
            return jsonify({'error': '旧密码和新密码不能为空'}), 400

        if not user.check_password(old_password):
            return jsonify({'error': '旧密码不正确'}), 400

        is_valid, password_msg = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': password_msg}), 400

        user.set_password(new_password)
        db.session.commit()

        return jsonify({'message': '密码修改成功'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"修改密码失败: {str(e)}")
        return jsonify({'error': '修改密码失败'}), 500

@auth_bp.route('/admin/approve-user/<int:user_id>', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    """管理员审核用户通过"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        # 检查当前用户是否为管理员
        if not current_user or current_user.user_type != 'admin':
            return jsonify({'error': '权限不足，仅管理员可执行此操作'}), 403

        # 查找要审核的用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 更新用户状态
        user.status = 'active'

        # 更新校友档案状态
        if user.alumni_profile:
            user.alumni_profile.approval_status = 'approved'
            user.alumni_profile.approved_by = current_user_id
            user.alumni_profile.approval_time = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': f'用户 {user.username} 已审核通过',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"审核用户失败: {str(e)}")
        return jsonify({'error': '审核失败，请稍后重试'}), 500

@auth_bp.route('/admin/pending-users', methods=['GET'])
@jwt_required()
def get_pending_users():
    """获取待审核用户列表"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        # 检查当前用户是否为管理员
        if not current_user or current_user.user_type != 'admin':
            return jsonify({'error': '权限不足，仅管理员可执行此操作'}), 403

        # 查找待审核用户
        pending_users = User.query.filter_by(status='pending').all()

        users_data = []
        for user in pending_users:
            user_data = user.to_dict()
            if user.alumni_profile:
                user_data['alumni_profile'] = user.alumni_profile.to_dict()
            users_data.append(user_data)

        return jsonify({
            'users': users_data,
            'count': len(users_data)
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取待审核用户失败: {str(e)}")
        return jsonify({'error': '获取用户列表失败'}), 500

@auth_bp.route('/face-login', methods=['POST'])
def face_login():
    """人脸识别登录 - 仅支持家长用户"""
    try:
        data = request.get_json()

        if not data.get('face_image'):
            return jsonify({'error': '请提供人脸图像数据'}), 400

        face_image = data.get('face_image')

        # 这里应该调用人脸识别服务来识别用户
        # 目前使用模拟的方式，通过用户姓名或ID查找
        user_info = None

        # 如果提供了用户ID，直接查找
        if 'user_id' in data:
            user = User.query.filter_by(
                user_type='parent',
                id=data['user_id']
            ).first()
            if user:
                user_info = user
        # 如果提供了姓名，查找匹配的家长用户
        elif 'real_name' in data:
            parents = User.query.filter_by(
                user_type='parent',
                real_name=data['real_name']
            ).all()
            if parents:
                user_info = parents[0]

        if not user_info:
            return jsonify({'error': '未找到匹配的家长用户信息'}), 404

        # 检查用户状态
        if user_info.status != 'active':
            return jsonify({'error': f'账户已被{user_info.status}，请联系管理员'}), 401

        # 生成访问令牌
        access_token = create_access_token(
            identity=str(user_info.id),
            expires_delta=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        )

        return jsonify({
            'message': '人脸识别登录成功',
            'access_token': access_token,
            'user': user_info.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        current_app.logger.error(f"人脸识别登录失败: {str(e)}")
        return jsonify({'error': '人脸识别登录失败，请重试'}), 500

@auth_bp.route('/face-register', methods=['POST'])
def face_register():
    """家长人脸信息注册"""
    try:
        current_user_id = request.headers.get('X-User-ID')
        if not current_user_id:
            return jsonify({'error': '用户未登录'}), 401

        user = User.query.get(int(current_user_id))
        if not user or user.user_type != 'parent':
            return jsonify({'error': '仅家长用户可以注册人脸信息'}), 403

        data = request.get_json()
        if not data.get('face_image'):
            return jsonify({'error': '请提供人脸图像数据'}), 400

        face_image = data.get('face_image')

        # 这里应该调用人脸识别服务来注册人脸特征
        # 目前只是模拟保存成功

        return jsonify({
            'message': '人脸信息注册成功',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error(f"人脸信息注册失败: {str(e)}")
        return jsonify({'error': '人脸信息注册失败，请重试'}), 500