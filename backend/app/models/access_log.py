"""
访问日志模型
"""

from datetime import datetime
from backend.app import db


class AccessLog(db.Model):
    """访问日志表（外网）"""

    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='用户ID（访客可为NULL）')
    access_type = db.Column(db.String(20), nullable=False, comment='访问类型: dynamic_code/visit/leave')
    access_code = db.Column(db.String(6), nullable=False, comment='访问码')
    verification_result = db.Column(db.Boolean, nullable=False, comment='验证结果')
    verified_by = db.Column(db.String(50), nullable=True, comment='门卫用户名')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')

    # 关系
    user = db.relationship('User', backref='access_logs')

    def __repr__(self):
        return f'<AccessLog {self.id}: {self.access_type} - {self.access_code}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else None,
            'access_type': self.access_type,
            'access_code': self.access_code,
            'verification_result': self.verification_result,
            'verified_by': self.verified_by,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
