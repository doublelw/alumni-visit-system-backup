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
        print(f"收到注册请求数据: {data}")  # 调试信息

        # 验证基本信息必填字段
        basic_fields = ['username', 'password', 'realName', 'email', 'phone', 'idCard']
        for field in basic_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return jsonify({'success': False, 'message': f'{field}不能为空'}), 400

        # 验证校友信息必填字段
        alumni_fields = ['graduationYear', 'classNumber', 'department', 'major', 'classTeacher']
        for field in alumni_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return jsonify({'success': False, 'message': f'{field}不能为空'}), 400

        # 验证工作信息必填字段
        work_fields = ['currentCity', 'workUnit', 'position', 'emergencyContact', 'emergencyPhone']
        for field in work_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return jsonify({'success': False, 'message': f'{field}不能为空'}), 400

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

        # 验证紧急联系人电话
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
            status='pending'  # 注册后需要管理员审核
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
            department=data['department'],
            major=data['major'],
            id_card=data['idCard'],
            class_teacher=data['classTeacher'],
            contact_teacher=data.get('contactTeacher', '未指定'),
            contact_teacher_phone=data.get('contactTeacherPhone', ''),
            emergency_contact=data['emergencyContact'],
            emergency_phone=data['emergencyPhone'],
            # 工作信息
            current_city=data['currentCity'],
            work_unit=data['workUnit'],
            position=data['position'],
            notes=data.get('notes', ''),
            approval_status='pending'
        )

        db.session.add(alumni_profile)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '注册成功！您的账号正在审核中，请等待管理员批准。审核通过后您将收到通知。',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"注册失败: {str(e)}")
        return jsonify({'success': False, 'message': '注册失败，请稍后重试'}), 500

        # 验证校友信息必填字段
        alumni_fields = ['graduationYear', 'classNumber', 'department', 'major', 'classTeacher']
        for field in alumni_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return jsonify({'success': False, 'message': f'{field}不能为空'}), 400

        # 验证工作信息必填字段
        work_fields = ['currentCity', 'workUnit', 'position', 'emergencyContact', 'emergencyPhone']
        for field in work_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return jsonify({'success': False, 'message': f'{field}不能为空'}), 400

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

        # 验证紧急联系人电话
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
            status='pending'  # 注册后需要管理员审核
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.flush()  # 获取用户ID

        # 创建校友档案
        alumni_profile = AlumniProfile(
            user_id=user.id,
            student_id=data.get('studentId', ''),
            graduation_year=graduation_year,
            class_name=data['classNumber'],
            department=data['department'],
            major=data['major'],
            id_card=data['idCard'],
            class_teacher=data['classTeacher'],
            contact_teacher=data.get('contactTeacher', ''),
            contact_teacher_phone=data.get('contactTeacherPhone', ''),
            emergency_contact=data['emergencyContact'],
            emergency_phone=data['emergencyPhone'],
            # 工作信息
            current_city=data['currentCity'],
            work_unit=data['workUnit'],
            position=data['position'],
            notes=data.get('notes', ''),
            approval_status='pending'
        )

        db.session.add(alumni_profile)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '注册成功！您的账号正在审核中，请等待管理员批准。审核通过后您将收到通知。',
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
        if not user or not user.check_password(data['password']):
            return jsonify({'error': '用户名或密码错误'}), 401

        if user.status != 'active':
            return jsonify({'error': '账户已被禁用，请联系管理员'}), 401

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