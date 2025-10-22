"""
保安相关模型
"""

from datetime import datetime
from app import db

class SecurityShift(db.Model):
    """保安班次表"""
    __tablename__ = 'security_shifts'

    id = db.Column(db.Integer, primary_key=True)
    security_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    shift_start = db.Column(db.Time, nullable=False)
    shift_end = db.Column(db.Time, nullable=False)
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    status = db.Column(db.Enum('scheduled', 'checked_in', 'checked_out', 'absent'),
                       nullable=False, default='scheduled')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    security = db.relationship('User', backref='security_shifts')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'security_id': self.security_id,
            'security_name': self.security.real_name if self.security else None,
            'shift_date': self.shift_date.strftime('%Y-%m-%d') if self.shift_date else None,
            'shift_start': self.shift_start.strftime('%H:%M') if self.shift_start else None,
            'shift_end': self.shift_end.strftime('%H:%M') if self.shift_end else None,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SecurityAccessLog(db.Model):
    """保安操作记录表"""
    __tablename__ = 'security_access_logs'

    id = db.Column(db.Integer, primary_key=True)
    security_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_application_id = db.Column(db.Integer, db.ForeignKey('visit_applications.id'), nullable=False, default=0)
    action_type = db.Column(db.Enum('scan_qr', 'face_verify', 'manual_entry', 'grant_access', 'deny_access'),
                           nullable=False)
    verification_method = db.Column(db.Enum('qr_code', 'face_recognition', 'manual', 'id_card'),
                                   nullable=False)
    action_result = db.Column(db.Enum('success', 'failed', 'cancelled'), nullable=False)
    access_granted = db.Column(db.Boolean, default=False)
    visitor_name = db.Column(db.String(100))  # 手动登记的访客姓名
    visitor_phone = db.Column(db.String(20))  # 手动登记的访客电话
    visit_purpose = db.Column(db.String(200))  # 访问目的
    target_person = db.Column(db.String(100))  # 被访人
    companions = db.Column(db.JSON)  # 同行人信息，存储为JSON
    notes = db.Column(db.Text)
    face_match_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    security = db.relationship('User', backref='security_logs')
    visit_application = db.relationship('VisitApplication', backref='access_logs', foreign_keys=[visit_application_id])

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'security_id': self.security_id,
            'security_name': self.security.real_name if self.security else None,
            'visit_application_id': self.visit_application_id,
            'visitor_name': self.visitor_name or (self.visit_application.visitor_info.get('name', '') if self.visit_application and self.visit_application.visitor_info else ''),
            'visitor_phone': self.visitor_phone,
            'visit_purpose': self.visit_purpose,
            'target_person': self.target_person,
            'companions': self.companions,
            'action_type': self.action_type,
            'verification_method': self.verification_method,
            'action_result': self.action_result,
            'access_granted': self.access_granted,
            'notes': self.notes,
            'face_match_score': self.face_match_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }