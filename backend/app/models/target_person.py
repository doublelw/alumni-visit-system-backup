"""
拜访对象模型
"""

from datetime import datetime
from app import db

class TargetPerson(db.Model):
    """拜访对象表"""
    __tablename__ = 'target_persons'

    id = db.Column(db.Integer, primary_key=True)
    work_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # 工作ID
    name = db.Column(db.String(100), nullable=False)  # 姓名
    department = db.Column(db.String(100), nullable=False)  # 部门
    position = db.Column(db.String(100))  # 职位
    email = db.Column(db.String(100))  # 邮箱
    phone = db.Column(db.String(20))  # 电话
    is_active = db.Column(db.Boolean, default=True)  # 是否在职
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'work_id': self.work_id,
            'name': self.name,
            'department': self.department,
            'position': self.position,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<TargetPerson {self.work_id} - {self.name}>'