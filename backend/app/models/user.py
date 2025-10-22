"""
用户模型
"""

import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True, comment='用户UUID')
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    user_type = db.Column(db.Enum('alumni', 'teacher', 'security', 'admin'),
                          nullable=False, default='alumni')
    status = db.Column(db.Enum('active', 'inactive', 'pending'),
                       nullable=False, default='pending')

    # 新增字段
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True, comment='所属组织ID')
    student_id = db.Column(db.String(50), nullable=True, comment='学号/工号')
    employee_id = db.Column(db.String(50), nullable=True, comment='员工编号')
    is_visitable = db.Column(db.Boolean, default=False, nullable=False, comment='是否可作为拜访对象')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    alumni_profile = db.relationship('AlumniProfile', foreign_keys='AlumniProfile.user_id', backref='user', uselist=False)
    face_data = db.relationship('FaceData', backref='user', uselist=False)
    visit_applications = db.relationship('VisitApplication', foreign_keys='VisitApplication.applicant_id', backref='applicant')
    approved_applications = db.relationship('VisitApplication', foreign_keys='VisitApplication.approved_by', backref='approver')
    visit_records = db.relationship('VisitRecord', foreign_keys='VisitRecord.user_id')
    organization = db.relationship('Organization', backref='users', foreign_keys='User.organization_id')
    # roles关系通过UserRoleAssignment的user关系和UserRole的assignments关系间接访问

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        # 确保UUID存在
        if not hasattr(self, 'uuid') or not self.uuid:
            self.uuid = str(uuid.uuid4())
            db.session.commit()

        data = {
            'id': self.id,
            'uuid': self.uuid,
            'username': self.username,
            'real_name': self.real_name,
            'email': self.email,
            'phone': self.phone,
            'user_type': self.user_type,
            'status': self.status,
            'organization_id': self.organization_id,
            'student_id': self.student_id,
            'employee_id': self.employee_id,
            'is_visitable': self.is_visitable,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_sensitive:
            data['alumni_profile'] = self.alumni_profile.to_dict() if self.alumni_profile else None
            data['has_face_data'] = bool(self.face_data)

        # 包含组织信息
        if self.organization:
            data['organization'] = self.organization.to_dict()

        return data

    @classmethod
    def get_visitable_teachers(cls):
        """获取所有可拜访的教师"""
        return cls.query.filter_by(
            user_type='teacher',
            status='active',
            is_visitable=True
        ).all()

    @classmethod
    def get_visitable_teacher_by_employee_id(cls, employee_id):
        """根据员工编号获取可拜访的教师"""
        return cls.query.filter_by(
            employee_id=employee_id,
            user_type='teacher',
            status='active',
            is_visitable=True
        ).first()

    def to_visit_target_dict(self):
        """转换为拜访对象格式"""
        return {
            'work_id': self.employee_id,
            'name': self.real_name,
            'department': self.organization.name if self.organization else '未知部门',
            'position': '教师',
            'email': self.email,
            'phone': self.phone
        }

    def __repr__(self):
        return f'<User {self.username}>'