"""
家长档案模型
"""

from datetime import datetime
from app import db


class ParentProfile(db.Model):
    """家长档案表"""

    __tablename__ = 'parent_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 基本信息
    real_name = db.Column(db.String(50), nullable=False)
    id_card = db.Column(db.String(18), unique=True, nullable=False)  # 身份证号
    phone = db.Column(db.String(20), nullable=False)  # 手机号
    email = db.Column(db.String(100))  # 邮箱
    wechat = db.Column(db.String(100))  # 微信号

    # 职业/工作信息
    occupation = db.Column(db.String(100))  # 职业
    workplace = db.Column(db.String(200))  # 工作单位
    work_address = db.Column(db.String(200))  # 工作地址

    # 与学生关系
    relationship_type = db.Column(db.String(20), nullable=False,
                                  comment='与学生关系：father/mother/grandfather/grandmother/other')

    # 紧急联系人备选
    emergency_contact_name = db.Column(db.String(50))  # 备选紧急联系人
    emergency_contact_phone = db.Column(db.String(20))  # 备选紧急电话
    emergency_contact_relationship = db.Column(db.String(20))  # 备选联系人关系

    # 住址信息
    home_address = db.Column(db.String(300))  # 家庭住址

    # 状态
    is_primary = db.Column(db.Boolean, default=False,
                          comment='是否为主要联系人（第一监护人）')
    can_pick_up = db.Column(db.Boolean, default=True,
                           comment='是否可以接学生离校')

    # 微信H5登录相关
    wechat_password = db.Column(db.String(4), nullable=True,
                               comment='微信H5登录密码（2-4位数字）')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = db.relationship('User', backref='parent_profile')

    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'real_name': self.real_name,
            'id_card': self.id_card[-4:] + '*' * (len(self.id_card) - 4) if self.id_card else None,
            'phone': self.phone,
            'email': self.email,
            'wechat': self.wechat,
            'occupation': self.occupation,
            'workplace': self.workplace,
            'work_address': self.work_address,
            'relationship_type': self.relationship_type,
            'relationship_type_label': self.get_relationship_label(),
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relationship': self.emergency_contact_relationship,
            'home_address': self.home_address,
            'is_primary': self.is_primary,
            'can_pick_up': self.can_pick_up,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }

        if include_sensitive:
            data['id_card'] = self.id_card

        return data

    def get_relationship_label(self):
        """获取关系类型标签"""
        labels = {
            'father': '父亲',
            'mother': '母亲',
            'grandfather': '祖父/外祖父',
            'grandmother': '祖母/外祖母',
            'other': '其他监护人'
        }
        return labels.get(self.relationship_type, self.relationship_type)

    def __repr__(self):
        return f'<ParentProfile {self.real_name}>'


class ParentStudentRelation(db.Model):
    """家长-学生关联表（中间表）"""

    __tablename__ = 'parent_student_relations'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 关系属性
    relationship_type = db.Column(db.String(20), nullable=False,
                                  comment='与学生关系：father/mother/grandfather/grandmother/other')
    is_primary = db.Column(db.Boolean, default=False,
                          comment='是否为主要监护人')
    is_emergency_contact = db.Column(db.Boolean, default=True,
                                    comment='是否为紧急联系人')
    can_pick_up = db.Column(db.Boolean, default=True,
                           comment='是否可以接学生离校')
    priority = db.Column(db.Integer, default=0,
                        comment='优先级（数字越小优先级越高）')

    # 审批状态（可选）
    is_verified = db.Column(db.Boolean, default=False,
                           comment='亲子关系是否已验证')
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'),
                           comment='验证人（班主任/管理员）')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    parent = db.relationship('User', foreign_keys=[parent_id],
                           backref='student_relations')
    student = db.relationship('User', foreign_keys=[student_id],
                            backref='parent_relations')
    verifier = db.relationship('User', foreign_keys=[verified_by])

    # 唯一约束（一个家长对一个学生只能有一条记录）
    __table_args__ = (
        db.UniqueConstraint('parent_id', 'student_id', name='unique_parent_student'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'parent_id': self.parent_id,
            'student_id': self.student_id,
            'parent_name': self.parent.real_name if self.parent else None,
            'student_name': self.student.real_name if self.student else None,
            'relationship_type': self.relationship_type,
            'relationship_type_label': self.get_relationship_label(),
            'is_primary': self.is_primary,
            'is_emergency_contact': self.is_emergency_contact,
            'can_pick_up': self.can_pick_up,
            'priority': self.priority,
            'is_verified': self.is_verified,
            'verified_at': self.verified_at.strftime('%Y-%m-%d %H:%M') if self.verified_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

    def get_relationship_label(self):
        """获取关系类型标签"""
        labels = {
            'father': '父亲',
            'mother': '母亲',
            'grandfather': '祖父/外祖父',
            'grandmother': '祖母/外祖母',
            'other': '其他监护人'
        }
        return labels.get(self.relationship_type, self.relationship_type)

    def __repr__(self):
        return f'<ParentStudentRelation {self.parent_id}-{self.student_id}>'
