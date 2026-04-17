"""
校友档案模型
"""

from datetime import datetime
from app import db

class AlumniProfile(db.Model):
    """校友档案表"""
    __tablename__ = 'alumni_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    graduation_year = db.Column(db.Integer, nullable=False)
    class_name = db.Column(db.String(100), nullable=False)
    division = db.Column(db.String(100), nullable=False)  # 学部（高中部、初中部、国际部、新疆部、北校区等）
    major = db.Column(db.String(100))  # 专业（中学可以改为学习方向或留空）
    id_card = db.Column(db.String(20), unique=True, nullable=False)
    contact_teacher = db.Column(db.String(100), nullable=False)
    contact_teacher_phone = db.Column(db.String(20), nullable=False)
    emergency_contact = db.Column(db.String(100))  # 改为可选
    emergency_phone = db.Column(db.String(20))  # 改为可选

    # 新增校友档案详细字段
    class_teacher = db.Column(db.String(100))  # 班主任
    chinese_teacher = db.Column(db.String(100))  # 语文老师
    math_teacher = db.Column(db.String(100))  # 数学老师
    english_teacher = db.Column(db.String(100))  # 英语老师
    physics_teacher = db.Column(db.String(100))  # 物理老师
    chemistry_teacher = db.Column(db.String(100))  # 化学老师
    biology_teacher = db.Column(db.String(100))  # 生物老师
    history_teacher = db.Column(db.String(100))  # 历史老师
    geography_teacher = db.Column(db.String(100))  # 地理老师
    politics_teacher = db.Column(db.String(100))  # 政治老师
    principal = db.Column(db.String(100))  # 时任校长
    division_director = db.Column(db.String(100))  # 时任学部主任
    class_advisor = db.Column(db.String(100))  # 班导师或班主任

    # 工作信息字段
    current_city = db.Column(db.String(100))  # 现在居住城市
    work_unit = db.Column(db.String(200))  # 工作单位
    position = db.Column(db.String(100))  # 职务

    # 就餐安排字段
    dining_companions = db.Column(db.Integer, default=1)  # 就餐人数（包含自己）

    notes = db.Column(db.Text)  # 备注说明
    approval_status = db.Column(db.Enum('pending', 'approved', 'rejected'),
                                nullable=False, default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approval_time = db.Column(db.DateTime)
    approval_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'student_id': self.student_id,
            'graduation_year': self.graduation_year,
            'class_name': self.class_name,
            'division': self.division,
            'major': self.major,
            'id_card': self.id_card[-4:] + '*' * (len(self.id_card) - 4) if self.id_card else None,  # 脱敏显示
            'contact_teacher': self.contact_teacher,
            'contact_teacher_phone': self.contact_teacher_phone,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            # 新增字段
            'class_teacher': self.class_teacher,
            'chinese_teacher': self.chinese_teacher,
            'math_teacher': self.math_teacher,
            'english_teacher': self.english_teacher,
            'physics_teacher': self.physics_teacher,
            'chemistry_teacher': self.chemistry_teacher,
            'biology_teacher': self.biology_teacher,
            'history_teacher': self.history_teacher,
            'geography_teacher': self.geography_teacher,
            'politics_teacher': self.politics_teacher,
            'principal': self.principal,
            'division_director': self.division_director,
            'class_advisor': self.class_advisor,
            # 工作信息
            'current_city': self.current_city,
            'work_unit': self.work_unit,
            'position': self.position,
            'notes': self.notes,
            'approval_status': self.approval_status,
            'approved_by': self.approved_by,
            'approval_time': self.approval_time.isoformat() if self.approval_time else None,
            'approval_note': self.approval_note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        # 如果需要包含敏感信息，返回完整的身份证号
        if include_sensitive:
            data['id_card'] = self.id_card

        return data

    def __repr__(self):
        return f'<AlumniProfile {self.student_id}>'