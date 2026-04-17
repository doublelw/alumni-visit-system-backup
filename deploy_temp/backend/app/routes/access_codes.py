"""
访问码管理API路由

提供动态码生成、验证等功能
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from datetime import datetime, timedelta
import base64
import secrets

from backend.app.models.user import User
from backend.app.services.access_code_service import AccessCodeService

access_codes_bp = Blueprint('access_codes', __name__)


def token_required(f):
    """JWT token验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': '缺少认证令牌'}), 401

        if token.startswith('Bearer '):
            token = token[7:]

        try:
            from backend.app.routes.auth import verify_token
            payload = verify_token(token)
            if payload is None:
                return jsonify({'error': '无效的令牌'}), 401
            request.current_user_id = payload['user_id']
        except Exception as e:
            current_app.logger.error(f"Token验证失败: {str(e)}")
            return jsonify({'error': '令牌验证失败'}), 401

        return f(*args, **kwargs)
    return decorated_function


@access_codes_bp.route('/generate', methods=['POST'])
@token_required
def generate_dynamic_code():
    """
    生成6位动态访问码

    请求体:
    {
        "phone": "13800138000",
        "pin": "88"  # 2位私人密码
    }

    返回:
    {
        "success": true,
        "data": {
            "code": "123456",
            "timestamp": 1234567890,
            "expires_at": "2026-03-27 12:05:00",
            "valid_minutes": 5
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        pin = data.get('pin', '').strip()

        # 验证参数
        if not phone:
            return jsonify({'error': '手机号不能为空'}), 400
        if not pin or len(pin) != 2:
            return jsonify({'error': 'PIN必须是2位数字'}), 400
        if not pin.isdigit():
            return jsonify({'error': 'PIN必须只包含数字'}), 400

        # 查找用户
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 检查密钥是否存在
        if not user.private_key:
            return jsonify({'error': '用户未设置密钥，请先完成注册绑定'}), 400

        # 检查密钥是否过期
        if user.key_expires_at:
            if user.key_expires_at < datetime.utcnow():
                return jsonify({
                    'error': '密钥已过期',
                    'message': '请更新密钥后继续使用'
                }), 403

        # 验证PIN
        expected_pin_hash = AccessCodeService.hash_pin(pin)
        if user.pin_hash != expected_pin_hash:
            return jsonify({'error': 'PIN错误'}), 401

        # 生成动态码
        result = AccessCodeService.generate_dynamic_code(
            user.private_key,
            phone,
            pin
        )

        return jsonify({
            'success': True,
            'data': result
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"生成动态码失败: {str(e)}")
        return jsonify({'error': '生成动态码失败', 'details': str(e)}), 500


@access_codes_bp.route('/verify', methods=['POST'])
def verify_dynamic_code():
    """
    验证6位动态访问码（门卫系统使用）

    请求体:
    {
        "phone": "13800138000",
        "code": "123456",
        "timestamp": 1234567890
    }

    返回:
    {
        "success": true,
        "data": {
            "valid": true,
            "message": "验证成功",
            "user": {
                "real_name": "张三",
                "user_type": "student",
                "student_no": "2021001",
                "photo_url": "/static/photos/..."
            }
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()
        timestamp = data.get('timestamp')

        # 验证参数
        if not phone:
            return jsonify({'error': '手机号不能为空'}), 400
        if not code or len(code) != 6:
            return jsonify({'error': '访问码必须是6位数字'}), 400
        if timestamp is None:
            return jsonify({'error': '时间戳不能为空'}), 400

        # 查找用户
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 验证动态码
        if not user.public_key or not user.pin_hash:
            return jsonify({'error': '用户信息不完整'}), 400

        is_valid, message = AccessCodeService.verify_dynamic_code(
            user.public_key,
            phone,
            user.pin_hash,
            code,
            int(timestamp)
        )

        # 记录验证日志
        from backend.app.models.access_log import AccessLog
        log = AccessLog(
            user_id=user.id,
            access_type='dynamic_code',
            access_code=code,
            verification_result=is_valid,
            verified_by=data.get('guard_name', 'unknown'),
            notes=message
        )
        db.session.add(log)
        db.session.commit()

        if is_valid:
            return jsonify({
                'success': True,
                'data': {
                    'valid': True,
                    'message': message,
                    'user': {
                        'real_name': user.real_name,
                        'user_type': user.user_type,
                        'student_no': user.student_no,
                        'employee_no': user.employee_no,
                        'photo_url': user.photo_url
                    }
                }
            })
        else:
            return jsonify({
                'success': False,
                'data': {
                    'valid': False,
                    'message': message
                }
            })

    except Exception as e:
        current_app.logger.error(f"验证动态码失败: {str(e)}")
        return jsonify({'error': '验证动态码失败', 'details': str(e)}), 500


@access_codes_bp.route('/user/setup-key', methods=['POST'])
@token_required
def setup_user_key():
    """
    用户设置密钥（注册/绑定时调用）

    请求体:
    {
        "phone": "13800138000",
        "pin": "88"  # 2位私人密码
    }

    返回:
    {
        "success": true,
        "data": {
            "private_key": "base64_encoded_key",
            "key_version": 1,
            "expires_at": "2026-09-27 00:00:00"
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        pin = data.get('pin', '').strip()

        # 验证参数
        if not phone:
            return jsonify({'error': '手机号不能为空'}), 400
        if not pin or len(pin) != 2:
            return jsonify({'error': 'PIN必须是2位数字'}), 400
        if not pin.isdigit():
            return jsonify({'error': 'PIN必须只包含数字'}), 400

        # 查找用户
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 检查是否已设置密钥
        if user.private_key:
            return jsonify({'error': '用户已设置密钥，如需更新请使用更新接口'}), 400

        # 生成密钥对
        private_key, public_key = AccessCodeService.generate_user_key_pair()

        # 计算PIN哈希
        pin_hash = AccessCodeService.hash_pin(pin)

        # 计算过期时间（6个月后）
        expires_at = AccessCodeService.calculate_next_expiry()

        # 更新用户信息
        user.private_key = private_key
        user.public_key = public_key
        user.pin_hash = pin_hash
        user.key_version = 1
        user.key_expires_at = expires_at

        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'private_key': private_key,
                'key_version': user.key_version,
                'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"设置用户密钥失败: {str(e)}")
        return jsonify({'error': '设置用户密钥失败', 'details': str(e)}), 500


@access_codes_bp.route('/user/update-key', methods=['POST'])
@token_required
def update_user_key():
    """
    更新用户密钥

    请求体:
    {
        "phone": "13800138000"
    }

    返回:
    {
        "success": true,
        "data": {
            "private_key": "new_base64_key",
            "key_version": 2,
            "expires_at": "2026-12-27 00:00:00"
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()

        if not phone:
            return jsonify({'error': '手机号不能为空'}), 400

        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 生成新密钥对
        private_key, public_key = AccessCodeService.generate_user_key_pair()

        # 更新版本号
        new_version = (user.key_version or 0) + 1

        # 计算新过期时间
        expires_at = AccessCodeService.calculate_next_expiry()

        # 更新用户信息（保留PIN哈希）
        user.private_key = private_key
        user.public_key = public_key
        user.key_version = new_version
        user.key_expires_at = expires_at

        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'private_key': private_key,
                'key_version': new_version,
                'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新用户密钥失败: {str(e)}")
        return jsonify({'error': '更新用户密钥失败', 'details': str(e)}), 500


@access_codes_bp.route('/user/status', methods=['GET'])
@token_required
def get_user_key_status():
    """
    获取用户密钥状态

    参数:
        phone: 手机号

    返回:
    {
        "success": true,
        "data": {
            "has_key": true,
            "key_version": 1,
            "expires_at": "2026-09-27 00:00:00",
            "days_until_expiry": 180,
            "needs_update": false
        }
    }
    """
    try:
        phone = request.args.get('phone', '').strip()

        if not phone:
            return jsonify({'error': '手机号不能为空'}), 400

        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        has_key = user.private_key is not None
        key_version = user.key_version or 0
        expires_at = user.key_expires_at

        # 检查是否需要更新
        is_expired, days_until_expiry = AccessCodeService.check_key_expiry(expires_at)
        needs_update = is_expired or days_until_expiry <= 7  # 7天内过期需要更新

        return jsonify({
            'success': True,
            'data': {
                'has_key': has_key,
                'key_version': key_version,
                'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S') if expires_at else None,
                'days_until_expiry': days_until_expiry,
                'needs_update': needs_update
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取用户密钥状态失败: {str(e)}")
        return jsonify({'error': '获取用户密钥状态失败', 'details': str(e)}), 500
