"""
返校日活动报名API
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json

from app import db
from app.models import User, EventRegistration

event_bp = Blueprint('event', __name__)

@event_bp.route('/register', methods=['POST'])
def register():
    """返校日活动报名"""
    try:
        data = request.get_json()
        current_app.logger.info(f"收到活动报名请求数据: {data}")

        # 验证必填字段
        required_fields = ['username', 'contactPhone']
        for field in required_fields:
            if not data.get(field) or data.get(field).strip() == '':
                return jsonify({'success': False, 'message': f'{field}不能为空'}), 400

        # 验证手机号格式
        phone = data['contactPhone'].strip()
        if not phone or not phone.startswith('1') or len(phone) != 11 or not phone.isdigit():
            return jsonify({'success': False, 'message': '手机号格式不正确'}), 400

        # 查找用户
        user = User.query.filter_by(username=data['username'].strip()).first()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在，请先完成注册'}), 400

        # 检查是否已经报名
        existing_registration = EventRegistration.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()

        if existing_registration:
            return jsonify({'success': False, 'message': '您已经完成报名，请勿重复提交'}), 400

        # 验证就餐选择的菜品
        will_dine = data.get('willDine', False)
        favorite_dishes = None

        if will_dine:
            if not data.get('favoriteDishes'):
                return jsonify({'success': False, 'message': '选择就餐时必须填写菜品信息'}), 400

            try:
                dishes = json.loads(data['favoriteDishes'])
                if not isinstance(dishes, list) or len(dishes) != 4:
                    return jsonify({'success': False, 'message': '必须选择恰好4个菜品'}), 400

                # 检查菜品是否在推荐列表中
                available_dishes = EventRegistration.get_dish_list()
                for dish in dishes:
                    if not dish.strip():
                        return jsonify({'success': False, 'message': '菜品名称不能为空'}), 400
                    if dish not in available_dishes:
                        current_app.logger.warning(f"用户选择了不在推荐列表的菜品: {dish}")
                        # 这里允许用户填写自定义菜品，但记录警告

                # 检查重复菜品
                unique_dishes = [dish.strip() for dish in dishes]
                if len(unique_dishes) != len(set(unique_dishes)):
                    return jsonify({'success': False, 'message': '不能选择重复的菜品'}), 400

                favorite_dishes = json.dumps(unique_dishes, ensure_ascii=False)

            except (json.JSONDecodeError, TypeError):
                return jsonify({'success': False, 'message': '菜品数据格式错误'}), 400

        # 创建报名记录
        registration = EventRegistration(
            user_id=user.id,
            username=user.username,
            real_name=user.real_name,
            will_dine=will_dine,
            favorite_dishes=favorite_dishes,
            contact_phone=phone,
            notes=data.get('notes', '').strip(),
            status='active'
        )

        db.session.add(registration)
        db.session.commit()

        current_app.logger.info(f"用户 {user.username} 活动报名成功")

        return jsonify({
            'success': True,
            'message': '报名成功！感谢您的参与！',
            'registration': registration.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"活动报名失败: {str(e)}")
        return jsonify({'success': False, 'message': '报名失败，请稍后重试'}), 500

@event_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取活动报名统计信息"""
    try:
        # 总报名人数
        total_registrations = EventRegistration.query.filter_by(status='active').count()

        # 就餐人数
        dining_registrations = EventRegistration.query.filter_by(
            status='active',
            will_dine=True
        ).count()

        # 菜品统计
        dish_statistics = EventRegistration.get_dish_statistics()

        # 最新报名列表（前20条）
        recent_registrations = EventRegistration.query.filter_by(
            status='active'
        ).order_by(EventRegistration.registration_time.desc()).limit(20).all()

        registration_list = [reg.to_dict() for reg in recent_registrations]

        return jsonify({
            'success': True,
            'statistics': {
                'total_registrations': total_registrations,
                'dining_registrations': dining_registrations,
                'non_dining_registrations': total_registrations - dining_registrations,
                'dish_statistics': dish_statistics
            },
            'recent_registrations': registration_list
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取活动统计信息失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取统计信息失败'}), 500

@event_bp.route('/registrations', methods=['GET'])
def get_registrations():
    """获取报名列表（分页）"""
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        will_dine = request.args.get('will_dine', type=str)

        # 构建查询
        query = EventRegistration.query.filter_by(status='active')

        # 筛选条件
        if will_dine is not None:
            if will_dine.lower() == 'true':
                query = query.filter_by(will_dine=True)
            elif will_dine.lower() == 'false':
                query = query.filter_by(will_dine=False)

        # 排序和分页
        registrations = query.order_by(EventRegistration.registration_time.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        registration_list = [reg.to_dict() for reg in registrations.items]

        return jsonify({
            'success': True,
            'registrations': registration_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': registrations.total,
                'pages': registrations.pages,
                'has_prev': registrations.has_prev,
                'has_next': registrations.has_next
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取报名列表失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取报名列表失败'}), 500

@event_bp.route('/menu', methods=['GET'])
def get_menu():
    """获取可用菜品列表"""
    try:
        dishes = EventRegistration.get_dish_list()
        return jsonify({
            'success': True,
            'dishes': dishes
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取菜品列表失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取菜品列表失败'}), 500

@event_bp.route('/cancel/<int:registration_id>', methods=['POST'])
def cancel_registration(registration_id):
    """取消报名"""
    try:
        registration = EventRegistration.query.get_or_404(registration_id)

        if registration.status != 'active':
            return jsonify({'success': False, 'message': '该报名已经无效'}), 400

        registration.status = 'cancelled'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '报名已取消'
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"取消报名失败: {str(e)}")
        return jsonify({'success': False, 'message': '取消报名失败'}), 500