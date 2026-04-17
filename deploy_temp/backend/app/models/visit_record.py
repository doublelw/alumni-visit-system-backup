"""
访问记录模型
"""

from datetime import datetime
from app import db

class VisitRecord(db.Model):
    """访问记录表"""
    __tablename__ = 'visit_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_application_id = db.Column(db.Integer, db.ForeignKey('visit_applications.id'))
    # vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))  # 车辆管理功能已移除
    entry_time = db.Column(db.DateTime, nullable=False)
    exit_time = db.Column(db.DateTime)
    verification_method = db.Column(db.Enum('face', 'qr_code', 'manual'),
                                   nullable=False, default='manual')
    gate_name = db.Column(db.String(100))  # 闸机名称
    security_guard_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 当值保安

    # 新增字段
    visitor_type = db.Column(db.String(20))  # 访问者类型: 'parent', 'alumni', 'visitor', 'teacher', 'student'
    destination = db.Column(db.String(200))  # 访问目的地
    host_person = db.Column(db.String(100))  # 接待人姓名
    host_person_id = db.Column(db.Integer)  # 接待人ID
    guard_name = db.Column(db.String(100))  # 门卫姓名
    info_complete = db.Column(db.Boolean, default=False)  # 信息完整度
    visit_purpose = db.Column(db.Text)  # 访问目的

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], overlaps="visit_records")
    security_guard = db.relationship('User', foreign_keys=[security_guard_id])
    visit_application = db.relationship('VisitApplication')
    # vehicle = db.relationship('Vehicle', overlaps="visit_records")  # 车辆管理功能已移除

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'visit_application_id': self.visit_application_id,
            # 'vehicle_id': self.vehicle_id,  # 车辆管理功能已移除
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'verification_method': self.verification_method,
            'gate_name': self.gate_name,
            'security_guard_id': self.security_guard_id,
            'visitor_type': self.visitor_type,
            'destination': self.destination,
            'host_person': self.host_person,
            'host_person_id': self.host_person_id,
            'guard_name': self.guard_name,
            'info_complete': self.info_complete,
            'visit_purpose': self.visit_purpose,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<VisitRecord {self.id}>'