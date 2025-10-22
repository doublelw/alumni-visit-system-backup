"""
拜访对象API
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models import TargetPerson

target_persons_bp = Blueprint('target_persons', __name__)

@target_persons_bp.route('/search', methods=['GET'])
def search_target_person():
    """根据工作ID搜索拜访对象"""
    work_id = request.args.get('work_id')

    if not work_id:
        return jsonify({'error': '工作ID不能为空'}), 400

    person = TargetPerson.query.filter_by(work_id=work_id, is_active=True).first()

    if not person:
        return jsonify({'error': '未找到该工作ID对应的拜访对象'}), 404

    return jsonify({
        'work_id': person.work_id,
        'name': person.name,
        'department': person.department,
        'position': person.position,
        'email': person.email,
        'phone': person.phone
    })

@target_persons_bp.route('/list', methods=['GET'])
def list_target_persons():
    """获取所有活跃的拜访对象列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    persons = TargetPerson.query.filter_by(is_active=True).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'persons': [person.to_dict() for person in persons.items],
        'total': persons.total,
        'pages': persons.pages,
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