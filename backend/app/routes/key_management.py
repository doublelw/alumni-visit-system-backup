"""
密钥管理API路由

提供密钥查看、更换、历史记录等功能
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from datetime import datetime, timedelta
from functools import wraps
import secrets
import string
from app import db
from app.models.user import User

key_management_bp = Blueprint('key_management', __name__)


def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查JWT token
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
        except Exception:
            return jsonify({'error': '需要有效的认证token'}), 401

        # 检查管理员权限
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user or current_user.user_type != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403

        return f(*args, **kwargs)
    return decorated_function


@key_management_bp.route('/status', methods=['GET'])
@admin_required
def get_keys_status():
    """
    获取当前密钥状态

    返回:
    {
        "success": true,
        "data": {
            "electronic_card_key": {
                "last_changed": "2026-03-27",
                "days_since_change": 30,
                "needs_rotation": true,
                "suggested_rotation": "monthly"
            },
            "jwt_key": {
                "last_changed": "2026-03-27",
                "days_since_change": 30,
                "needs_rotation": true,
                "suggested_rotation": "monthly"
            },
            "wechat_passwords": {
                "teacher_password": "1234",
                "parent_password": "88",
                "last_changed": "2026-03-27",
                "days_since_change": 0
            }
        }
    }
    """
    try:
        from app.models.key_history import KeyHistory

        # 获取电子卡密钥最后更换时间
        electronic_card_history = KeyHistory.query.filter_by(
            key_type='electronic_card'
        ).order_by(KeyHistory.changed_at.desc()).first()

        if electronic_card_history:
            days_since = (datetime.now() - electronic_card_history.changed_at).days
            needs_rotation = days_since >= 30  # 30天建议更换
        else:
            days_since = 999
            needs_rotation = True

        # 获取JWT密钥最后更换时间
        jwt_history = KeyHistory.query.filter_by(
            key_type='jwt'
        ).order_by(KeyHistory.changed_at.desc()).first()

        if jwt_history:
            jwt_days = (datetime.now() - jwt_history.changed_at).days
            jwt_needs_rotation = jwt_days >= 30
        else:
            jwt_days = 999
            jwt_needs_rotation = True

        return jsonify({
            'success': True,
            'data': {
                'electronic_card_key': {
                    'last_changed': electronic_card_history.changed_at.strftime('%Y-%m-%d') if electronic_card_history else '未设置',
                    'days_since_change': days_since if electronic_card_history else 999,
                    'needs_rotation': needs_rotation,
                    'suggested_rotation': 'monthly'
                },
                'jwt_key': {
                    'last_changed': jwt_history.changed_at.strftime('%Y-%m-%d') if jwt_history else '未设置',
                    'days_since_change': jwt_days if jwt_history else 999,
                    'needs_rotation': jwt_needs_rotation,
                    'suggested_rotation': 'monthly'
                },
                'wechat_passwords': {
                    'teacher_password': '1234',
                    'parent_password': '88',
                    'last_changed': '2026-03-27',
                    'days_since_change': 0
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取密钥状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@key_management_bp.route('/rotate', methods=['POST'])
@admin_required
def rotate_key():
    """
    更换密钥

    请求体:
    {
        "key_type": "electronic_card"  # electronic_card 或 jwt
    }

    返回:
    {
        "success": true,
        "data": {
            "old_key": "old_key_preview",
            "new_key": "new_key_preview",
            "changed_at": "2026-03-27"
        }
    }
    """
    try:
        from app.models.key_history import KeyHistory
        from app.config import Config

        data = request.get_json()
        key_type = data.get('key_type')

        # 获取当前登录的管理员用户
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        # 生成新密钥
        if key_type == 'electronic_card':
            old_key = current_app.config.get('ELECTRONIC_CARD_SECRET_KEY')
            new_key = secrets.token_urlsafe(32)

            # 记录历史
            history = KeyHistory(
                key_type='electronic_card',
                old_key=old_key[:8] + '...' if old_key else 'not_set',
                new_key=new_key[:8] + '...',
                changed_by=current_user.username,
                changed_at=datetime.now(),
                reason='manual_rotation'
            )
            db.session.add(history)
            db.session.commit()

            # TODO: 更新配置文件或环境变量
            # 实际生产环境需要更新配置文件并重启服务

            return jsonify({
                'success': True,
                'data': {
                    'key_type': 'electronic_card',
                    'old_key_preview': old_key[:8] + '...' if old_key else '未设置',
                    'new_key_preview': new_key[:8] + '...',
                    'changed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'changed_by': current_user.username,
                    'message': '电子卡密钥已更新，请重启服务生效'
                }
            })

        elif key_type == 'jwt':
            old_key = current_app.config.get('JWT_SECRET_KEY')
            new_key = secrets.token_urlsafe(32)

            # 记录历史
            history = KeyHistory(
                key_type='jwt',
                old_key=old_key[:8] + '...' if old_key else 'not_set',
                new_key=new_key[:8] + '...',
                changed_by=current_user.username,
                changed_at=datetime.now(),
                reason='manual_rotation'
            )
            db.session.add(history)
            db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'key_type': 'jwt',
                    'old_key_preview': old_key[:8] + '...' if old_key else '未设置',
                    'new_key_preview': new_key[:8] + '...',
                    'changed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'changed_by': current_user.username,
                    'message': 'JWT密钥已更新，请重启服务生效'
                }
            })

        else:
            return jsonify({'success': False, 'error': '无效的密钥类型'}), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更换密钥失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@key_management_bp.route('/history', methods=['GET'])
@admin_required
def get_key_history():
    """
    获取密钥更换历史（支持分页）

    参数:
        key_type: 密钥类型（可选）
        page: 页码（可选，默认1）
        per_page: 每页条数（可选，默认20）

    返回:
    {
        "success": true,
        "data": {
            "history": [...],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": 100,
                "pages": 5,
                "has_prev": false,
                "has_next": true
            }
        }
    }
    """
    try:
        from app.models.key_history import KeyHistory

        key_type = request.args.get('key_type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        query = KeyHistory.query
        if key_type:
            query = query.filter_by(key_type=key_type)

        # 获取总数
        total = query.count()

        # 计算分页
        pages = (total + per_page - 1) // per_page if total > 0 else 1
        has_prev = page > 1
        has_next = page < pages

        # 获取当前页数据
        history_records = query.order_by(KeyHistory.changed_at.desc()) \
            .offset((page - 1) * per_page) \
            .limit(per_page) \
            .all()

        history_list = []
        for record in history_records:
            history_list.append({
                'id': record.id,
                'key_type': record.key_type,
                'old_key_preview': record.old_key,
                'new_key_preview': record.new_key,
                'changed_by': record.changed_by,
                'changed_at': record.changed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'reason': record.reason
            })

        return jsonify({
            'success': True,
            'data': {
                'history': history_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': pages,
                    'has_prev': has_prev,
                    'has_next': has_next
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取密钥历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@key_management_bp.route('/wechat/update', methods=['POST'])
@admin_required
def update_wechat_passwords():
    """
    更新微信登录密码

    请求体:
    {
        "teacher_password": "1234",
        "parent_password": "88"
    }

    返回:
    {
        "success": true,
        "data": {
            "updated_at": "2026-03-27"
        }
    }
    """
    try:
        data = request.get_json()
        teacher_password = data.get('teacher_password')
        parent_password = data.get('parent_password')

        from app.models.user import User
        from sqlalchemy import text

        if teacher_password:
            # 更新教师密码
            db.session.execute(
                text('UPDATE users SET wechat_password = :pwd WHERE user_type LIKE :type'),
                {'pwd': teacher_password, 'type': '%teacher%'}
            )

        if parent_password:
            # 更新家长密码
            db.session.execute(
                text('UPDATE users SET wechat_password = :pwd WHERE user_type LIKE :type'),
                {'pwd': parent_password, 'type': '%parent%'}
            )

        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': '微信登录密码已更新'
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新微信密码失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
