"""
访客档案模型
"""

from datetime import datetime
from app import db


class VisitorProfile(db.Model):
    """访客档案表"""

    __tablename__ = 'visitor_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 基本信息
    real_name = db.Column(db.String(50), nullable=False)
    id_card = db.Column(db.String(18), nullable=False)  # 身份证号
    phone = db.Column(db.String(20), nullable=False)  # 手机号
    email = db.Column(db.String(100))  # 邮箱

    # 访客类型
    visitor_type = db.Column(db.String(20), nullable=False,
                            comment='访客类型：individual/group/vendor/delivery/other',
                            default='individual')
    visitor_type_label = db.Column(db.String(50),
                                  comment='访客类型标签（中文）')

    # 来访单位信息
    organization = db.Column(db.String(200), comment='所属单位/公司')
    organization_address = db.Column(db.String(300), comment='单位地址')

    # 车辆信息
    has_vehicle = db.Column(db.Boolean, default=False,
                           comment='是否有车辆')
    vehicle_plate = db.Column(db.String(20), comment='车牌号')
    vehicle_type = db.Column(db.String(20), comment='车辆类型：car/truck/motorcycle/other')
    vehicle_color = db.Column(db.String(20), comment='车辆颜色')

    # 拜访信息
    visit_purpose = db.Column(db.Text, comment='来访目的')
    target_department = db.Column(db.String(100), comment='拜访部门')
    target_person = db.Column(db.String(50), comment='拜访对象')
    target_person_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                                comment='拜访对象ID')

    # 预计来访信息
    estimated_visit_date = db.Column(db.Date, comment='预计来访日期')
    estimated_visit_duration = db.Column(db.Integer,
                                        comment='预计停留时长（分钟）')

    # 陪同人员（团队访客）
    companion_count = db.Column(db.Integer, default=0,
                               comment='陪同人数（不含本人）')
    companion_names = db.Column(db.Text,
                               comment='陪同人员姓名（JSON数组）')

    # 物品携带
    has_items = db.Column(db.Boolean, default=False,
                         comment='是否携带物品')
    items_description = db.Column(db.Text, comment='物品描述')

    # 健康与安全
    health_declaration = db.Column(db.Boolean, default=True,
                                  comment='健康声明（是否有发热等症状）')
    safety_agreement = db.Column(db.Boolean, default=False,
                                comment='是否签署安全协议')

    # 审批状态
    application_status = db.Column(db.String(20),
                                   comment='申请状态：pending/approved/rejected/completed/cancelled',
                                   default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'),
                           comment='审批人ID')
    approved_at = db.Column(db.DateTime, comment='审批时间')
    rejection_reason = db.Column(db.Text, comment='拒绝原因')

    # 访问凭证
    access_code = db.Column(db.String(20), unique=True,
                           comment='访问码/验证码（6位数字）')
    access_password = db.Column(db.String(10),
                               comment='访问密码（2位数字，明文存储用于验证）')
    qr_code = db.Column(db.String(500), comment='二维码数据')

    # 访问记录
    actual_visit_time = db.Column(db.DateTime, comment='实际进入时间')
    actual_leave_time = db.Column(db.DateTime, comment='实际离开时间')
    visit_completed = db.Column(db.Boolean, default=False,
                               comment='是否已完成访问')

    # 黑名单
    is_blacklisted = db.Column(db.Boolean, default=False,
                              comment='是否在黑名单')
    blacklist_reason = db.Column(db.Text, comment='拉黑原因')
    blacklisted_at = db.Column(db.DateTime, comment='拉黑时间')
    blacklisted_by = db.Column(db.Integer, db.ForeignKey('users.id'),
                              comment='拉黑操作人ID')

    # 备注
    notes = db.Column(db.Text, comment='备注信息')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='visitor_profile')
    target_person_obj = db.relationship('User', foreign_keys=[target_person_id])
    approver = db.relationship('User', foreign_keys=[approved_by])
    blacklist_operator = db.relationship('User', foreign_keys=[blacklisted_by])

    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'real_name': self.real_name,
            'id_card': self.id_card[-4:] + '*' * (len(self.id_card) - 4) if self.id_card else None,
            'phone': self.phone,
            'email': self.email,
            'visitor_type': self.visitor_type,
            'visitor_type_label': self.get_visitor_type_label(),
            'organization': self.organization,
            'organization_address': self.organization_address,
            'has_vehicle': self.has_vehicle,
            'vehicle_plate': self.vehicle_plate,
            'vehicle_type': self.vehicle_type,
            'vehicle_color': self.vehicle_color,
            'visit_purpose': self.visit_purpose,
            'target_department': self.target_department,
            'target_person': self.target_person,
            'estimated_visit_date': self.estimated_visit_date.strftime('%Y-%m-%d') if self.estimated_visit_date else None,
            'estimated_visit_duration': self.estimated_visit_duration,
            'companion_count': self.companion_count,
            'has_items': self.has_items,
            'items_description': self.items_description,
            'health_declaration': self.health_declaration,
            'safety_agreement': self.safety_agreement,
            'application_status': self.application_status,
            'application_status_label': self.get_status_label(),
            'access_code': self.access_code,
            'actual_visit_time': self.actual_visit_time.strftime('%Y-%m-%d %H:%M') if self.actual_visit_time else None,
            'actual_leave_time': self.actual_leave_time.strftime('%Y-%m-%d %H:%M') if self.actual_leave_time else None,
            'visit_completed': self.visit_completed,
            'is_blacklisted': self.is_blacklisted,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }

        if include_sensitive:
            data['id_card'] = self.id_card
            data['companion_names'] = self.companion_names

        return data

    def get_visitor_type_label(self):
        """获取访客类型标签"""
        labels = {
            'individual': '个人访客',
            'group': '团队访客',
            'vendor': '供应商',
            'delivery': '快递/送货',
            'other': '其他'
        }
        return labels.get(self.visitor_type, self.visitor_type)

    def get_status_label(self):
        """获取状态标签"""
        labels = {
            'pending': '待审批',
            'approved': '已批准',
            'rejected': '已拒绝',
            'completed': '已完成',
            'cancelled': '已取消'
        }
        return labels.get(self.application_status, self.application_status)

    def is_valid_visit(self):
        """检查访问是否有效（未完成、未取消、未过期）"""
        if self.visit_completed:
            return False, '访问已完成'
        if self.application_status != 'approved':
            return False, f'访问状态为：{self.get_status_label()}'
        if self.is_blacklisted:
            return False, '访客在黑名单中'
        return True, '有效'

    def __repr__(self):
        return f'<VisitorProfile {self.real_name} - {self.get_visitor_type_label()}>'
