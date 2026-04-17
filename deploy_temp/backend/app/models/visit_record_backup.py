"""
访问记录模型
"""

from datetime import datetime
from app import db
# Fixed syntax error

class VisitRecord(db.Model):
    """访问记录表"""
    __tablename__ = 'visit_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_application_id = db.Column(db.Integer, db.ForeignKey('visit_applications.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    entry_time = db.Column(db.DateTime, nullable=False)
    exit_time = db.Column(db.DateTime)
    verification_method = db.Column(db.Enum('face', 'qr_code', 'manual'),
                                   nullable=False, default='manual')
    gate_name = db.Column(db.String(100))  # 闸机名称
    security_guard_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 当值保安
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='visit_records')
    security_guard = db.relationship('User', foreign_keys=[security_guard_id], backref='guarded_records')
    visit_application = db.relationship('VisitApplication', backref='visit_records')
    vehicle = db.relationship('Vehicle', backref='visit_records')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'visit_application_id': self.visit_application_id,
            'vehicle_id': self.vehicle_id,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'verification_method': self.verification_method,
            'gate_name': self.gate_name,
            'security_guard_id': self.security_guard_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<VisitRecord {self.id}>'