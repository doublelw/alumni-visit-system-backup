"""
拜访对象API
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import TargetPerson, User

target_persons_bp = Blueprint('target_persons', __name__)

def check_admin_permission():
    """检查管理员权限"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.user_type != 'admin':
        return False
    return True

@target_persons_bp.route('/search', methods=['GET'])
def search_target_person():
    """根据工作ID搜索拜访对象"""
    work_id = request.args.get('work_id')

    if not work_id:
        return jsonify({'error': '工作ID不能为空'}), 400

    person = User.get_visitable_teacher_by_employee_id(work_id)

    if not person:
        return jsonify({'error': '未找到该工作ID对应的拜访对象'}), 404

    return jsonify(person.to_visit_target_dict())

@target_persons_bp.route('/list', methods=['GET'])
def list_target_persons():
    """获取所有活跃的拜访对象列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = User.query.filter_by(
        user_type='teacher',
        status='active',
        is_visitable=True
    )

    # 搜索过滤
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            (User.employee_id.like(f'%{search}%')) |
            (User.real_name.like(f'%{search}%')) |
            (User.email.like(f'%{search}%'))
        )

    # 排序
    query = query.order_by(User.real_name)

    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'persons': [person.to_visit_target_dict() for person in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@target_persons_bp.route('/init-data', methods=['POST'])
def init_test_data():
    """初始化测试数据"""
    test_data = [
        {
            'work_id': 'EMP001',
            'name': '张伟',
            'department': '计算机科学与技术学院',
            'position': '教授',
            'email': 'zhangwei@university.edu.cn',
            'phone': '13800138001'
        },
        {
            'work_id': 'EMP002',
            'name': '李娜',
            'department': '软件学院',
            'position': '副教授',
            'email': 'lina@university.edu.cn',
            'phone': '13800138002'
        },
        {
            'work_id': 'EMP003',
            'name': '王强',
            'department': '信息工程学院',
            'position': '讲师',
            'email': 'wangqiang@university.edu.cn',
            'phone': '13800138003'
        },
        {
            'work_id': 'EMP004',
            'name': '刘芳',
            'department': '数学学院',
            'position': '教授',
            'email': 'liufang@university.edu.cn',
            'phone': '13800138004'
        },
        {
            'work_id': 'EMP005',
            'name': '陈明',
            'department': '物理学院',
            'position': '副教授',
            'email': 'chenming@university.edu.cn',
            'phone': '13800138005'
        },
        {
            'work_id': 'EMP006',
            'name': '赵静',
            'department': '化学学院',
            'position': '讲师',
            'email': 'zhaojing@university.edu.cn',
            'phone': '13800138006'
        },
        {
            'work_id': 'EMP007',
            'name': '孙超',
            'department': '生物学院',
            'position': '教授',
            'email': 'sunchao@university.edu.cn',
            'phone': '13800138007'
        },
        {
            'work_id': 'EMP008',
            'name': '周婷',
            'department': '外国语学院',
            'position': '副教授',
            'email': 'zhouting@university.edu.cn',
            'phone': '13800138008'
        },
        {
            'work_id': 'EMP009',
            'name': '吴涛',
            'department': '经济管理学院',
            'position': '讲师',
            'email': 'wutao@university.edu.cn',
            'phone': '13800138009'
        },
        {
            'work_id': 'EMP010',
            'name': '郑敏',
            'department': '法学院',
            'position': '教授',
            'email': 'zhengmin@university.edu.cn',
            'phone': '13800138010'
        }
    ]

    try:
        # 检查是否已存在测试数据
        existing_count = TargetPerson.query.count()
        if existing_count >= 10:
            return jsonify({'message': '测试数据已存在'}), 200

        # 插入测试数据
        for data in test_data:
            person = TargetPerson(**data)
            db.session.add(person)

        db.session.commit()

        return jsonify({
            'message': f'成功创建 {len(test_data)} 条测试数据',
            'count': len(test_data)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建测试数据失败: {str(e)}'}), 500

# ===== CRUD API 管理功能 =====

@target_persons_bp.route('', methods=['GET'])
@jwt_required()
def get_target_persons():
    """获取拜访对象列表（支持分页和搜索）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', 'active')  # active, inactive, all

        query = TargetPerson.query

        # 状态过滤
        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)

        # 搜索过滤
        if search:
            query = query.filter(
                (TargetPerson.work_id.like(f'%{search}%')) |
                (TargetPerson.name.like(f'%{search}%')) |
                (TargetPerson.department.like(f'%{search}%')) |
                (TargetPerson.position.like(f'%{search}%'))
            )

        # 排序
        query = query.order_by(TargetPerson.created_at.desc())

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'data': {
                'persons': [person.to_dict() for person in pagination.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取拜访对象列表失败: {str(e)}'
        }), 500

@target_persons_bp.route('', methods=['POST'])
@jwt_required()
def create_target_person():
    """创建新的拜访对象"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以创建拜访对象'
            }), 403

        data = request.get_json()

        # 验证必填字段
        required_fields = ['work_id', 'name', 'department']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400

        # 检查工作ID是否已存在
        existing_person = TargetPerson.query.filter_by(work_id=data['work_id']).first()
        if existing_person:
            return jsonify({
                'success': False,
                'message': f'工作ID {data["work_id"]} 已存在'
            }), 400

        # 创建新的拜访对象
        person = TargetPerson(
            work_id=data['work_id'],
            name=data['name'],
            department=data['department'],
            position=data.get('position', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            is_active=data.get('is_active', True)
        )

        db.session.add(person)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '拜访对象创建成功',
            'data': person.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建拜访对象失败: {str(e)}'
        }), 500

@target_persons_bp.route('/<int:person_id>', methods=['GET'])
@jwt_required()
def get_target_person(person_id):
    """获取单个拜访对象详情"""
    try:
        person = TargetPerson.query.get_or_404(person_id)

        return jsonify({
            'success': True,
            'data': person.to_dict()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取拜访对象详情失败: {str(e)}'
        }), 500

@target_persons_bp.route('/<int:person_id>', methods=['PUT'])
@jwt_required()
def update_target_person(person_id):
    """更新拜访对象信息"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以更新拜访对象'
            }), 403

        person = TargetPerson.query.get_or_404(person_id)
        data = request.get_json()

        # 更新字段
        if 'work_id' in data:
            # 检查新的工作ID是否已被其他记录使用
            existing_person = TargetPerson.query.filter(
                TargetPerson.work_id == data['work_id'],
                TargetPerson.id != person_id
            ).first()
            if existing_person:
                return jsonify({
                    'success': False,
                    'message': f'工作ID {data["work_id"]} 已被其他记录使用'
                }), 400
            person.work_id = data['work_id']

        if 'name' in data:
            person.name = data['name']
        if 'department' in data:
            person.department = data['department']
        if 'position' in data:
            person.position = data['position']
        if 'email' in data:
            person.email = data['email']
        if 'phone' in data:
            person.phone = data['phone']
        if 'is_active' in data:
            person.is_active = data['is_active']

        person.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '拜访对象更新成功',
            'data': person.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新拜访对象失败: {str(e)}'
        }), 500

@target_persons_bp.route('/<int:person_id>', methods=['DELETE'])
@jwt_required()
def delete_target_person(person_id):
    """删除拜访对象（软删除）"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以删除拜访对象'
            }), 403

        person = TargetPerson.query.get_or_404(person_id)

        # 软删除：标记为非活跃
        person.is_active = False
        person.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '拜访对象删除成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除拜访对象失败: {str(e)}'
        }), 500

@target_persons_bp.route('/<int:person_id>/restore', methods=['POST'])
@jwt_required()
def restore_target_person(person_id):
    """恢复已删除的拜访对象"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以恢复拜访对象'
            }), 403

        person = TargetPerson.query.get_or_404(person_id)

        # 恢复：标记为活跃
        person.is_active = True
        person.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '拜访对象恢复成功',
            'data': person.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'恢复拜访对象失败: {str(e)}'
        }), 500

@target_persons_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_target_persons_stats():
    """获取拜访对象统计信息"""
    try:
        # 统计教师用户
        total_teachers = User.query.filter_by(user_type='teacher').count()
        active_teachers = User.query.filter_by(user_type='teacher', status='active').count()
        visitable_teachers = User.query.filter_by(
            user_type='teacher',
            status='active',
            is_visitable=True
        ).count()

        return jsonify({
            'success': True,
            'data': {
                'total_count': total_teachers,
                'active_count': active_teachers,
                'visitable_count': visitable_teachers,
                'visitable_percentage': round(visitable_teachers / total_teachers * 100, 1) if total_teachers > 0 else 0
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500

@target_persons_bp.route('/sync-teachers', methods=['POST'])
@jwt_required()
def sync_with_teachers():
    """与教师用户同步拜访对象数据"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以同步数据'
            }), 403

        # 导入同步脚本
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from sync_target_persons import sync_target_persons_with_users, show_current_status

        # 执行同步
        sync_target_persons_with_users()

        return jsonify({
            'success': True,
            'message': '教师数据同步成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'同步失败: {str(e)}'
        }), 500