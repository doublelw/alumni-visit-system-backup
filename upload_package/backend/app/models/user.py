"""
用户模型
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    user_type = db.Column(db.Enum('alumni', 'teacher', 'security', 'admin'),
                          nullable=False, default='alumni')
    status = db.Column(db.Enum('active', 'inactive', 'pending'),
                       nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    alumni_profile = db.relationship('AlumniProfile', foreign_keys='AlumniProfile.user_id', backref='user', uselist=False)
    face_data = db.relationship('FaceData', backref='user', uselist=False)
    visit_applications = db.relationship('VisitApplication', foreign_keys='VisitApplication.applicant_id', backref='applicant')
    approved_applications = db.relationship('VisitApplication', foreign_keys='VisitApplication.approved_by', backref='approver')
    visit_records = db.relationship('VisitRecord', foreign_keys='VisitRecord.user_id')

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'email': self.email,
            'phone': self.phone,
            'user_type': self.user_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_sensitive:
            data['alumni_profile'] = self.alumni_profile.to_dict() if self.alumni_profile else None
            data['has_face_data'] = bool(self.face_data)

        return data

    def __repr__(self):
        return f'<User {self.username}>'