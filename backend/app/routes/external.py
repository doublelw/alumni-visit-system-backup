"""
外网API路由（模拟flag服务器）
只处理验证码生成和基本查询，不存储详细个人信息
"""

from flask import Blueprint, request, jsonify
from external_network import external_storage

external_bp = Blueprint('external', __name__, url_prefix='/external')

@external_bp.route('/generate-code', methods=['POST'])
def generate_code():
    """
    外网：生成访问码
    只存储码本身和类型，不存储个人信息

    请求体:
    {
        "code_type": "visitor" | "parent-visit" | "student-leave" | "alumni",
        "phone": "手机号"  # 仅访客需要
    }

    返回:
    {
        "success": true,
        "code": "生成的6位码",
        "expires_at": "过期时间"
    }
    """
    try:
        data = request.get_json()
        code_type = data.get('code_type')
        phone = data.get('phone', '')

        # 生成HMAC验证码（与门卫验证逻辑保持一致）
        from app.utils.hmac_utils import generate_hmac_code

        # 生成默认密码（手机号后6位）
        password = phone[-6:] if len(phone) >= 6 else phone

        # 生成HMAC码
        code = generate_hmac_code(phone, password)

        # 存储到外网
        if code_type == 'visitor' and phone:
            # 访客：存储码+手机号
            external_storage.store_access_code(code, code_type)
            external_storage.store_visitor_info(code, phone)
        else:
            # 其他类型：只存储码
            external_storage.store_access_code(code, code_type)

        return jsonify({
            'success': True,
            'code': code,
            'expires_at': '24小时后'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@external_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """
    外网：验证访问码是否有效
    只返回是否有效，不返回个人信息

    请求体:
    {
        "code": "访问码",
        "code_type": "码类型（可选）"
    }

    返回:
    {
        "success": true,
        "valid": true/false,
        "code_type": "码类型"
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        code_type = data.get('code_type')

        # 验证码
        is_valid = external_storage.verify_access_code(code, code_type)

        return jsonify({
            'success': True,
            'valid': is_valid,
            'code_type': code_type
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@external_bp.route('/visitor/info/<code>', methods=['GET'])
def get_visitor_info(code):
    """
    外网：获取访客基本信息
    只返回手机号，不返回姓名、身份证等敏感信息

    路径参数:
        code: 访问码

    返回:
    {
        "success": true,
        "exists": true/false,
        "visitor_info": {
            "phone": "手机号",
            "created_at": "创建时间",
            "expires_at": "过期时间"
        }
    }
    """
    try:
        # 从外网获取基本信息
        visitor_info = external_storage.get_visitor_info(code)

        if visitor_info:
            return jsonify({
                'success': True,
                'exists': True,
                'visitor_info': visitor_info
            })
        else:
            return jsonify({
                'success': True,
                'exists': False,
                'visitor_info': None
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@external_bp.route('/visitor/mark-used', methods=['POST'])
def mark_visitor_used():
    """
    外网：标记访客码已使用
    教师验证后调用，防止重复使用

    请求体:
    {
        "code": "访问码"
    }

    返回:
    {
        "success": true
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '').strip()

        # 标记为已使用
        external_storage.mark_visitor_used(code)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@external_bp.route('/cleanup', methods=['POST'])
def cleanup():
    """
    外网：清理过期数据
    定时任务调用

    返回:
    {
        "success": true,
        "deleted_count": 清理数量
    }
    """
    try:
        deleted_count = external_storage.cleanup_expired()

        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
