"""
验证日志模型
"""

from datetime import datetime
from app import db


class VerificationLog(db.Model):
    """验证日志表"""

    __tablename__ = 'verification_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 访问码信息
    code_type = db.Column(db.String(20), nullable=False,
                          comment='类型: application/visitor')
    code = db.Column(db.String(6), nullable=False, comment='访问码')

    # 人员信息
    personnel_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True,
                          comment='校内人员ID')
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitor_applications.id'),
                       nullable=True, comment='访客ID')

    # 验证结果
    verification_result = db.Column(db.Boolean, nullable=False, comment='验证结果')
    verified_by = db.Column(db.String(50), nullable=False, comment='门卫用户名')
    verified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                         comment='验证时间')

    # 显示信息
    user_name = db.Column(db.String(100), nullable=True, comment='用户姓名（显示用）')
    visitor_name = db.Column(db.String(100), nullable=True, comment='访客姓名（显示用）')
    host_name = db.Column(db.String(100), nullable=True, comment='接待人姓名（显示用）')

    # 备注
    notes = db.Column(db.Text, nullable=True)

    # 关系
    personnel = db.relationship('User', foreign_keys=[personnel_id])
    visitor = db.relationship('VisitorApplication', foreign_keys=[visitor_id])

    def __repr__(self):
        return f'<VerificationLog {self.id}: {self.code_type} - {self.code}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'code_type': self.code_type,
            'code': self.code,
            'personnel_id': self.personnel_id,
            'visitor_id': self.visitor_id,
            'verification_result': self.verification_result,
            'verified_by': self.verified_by,
            'verified_at': self.verified_at.strftime('%Y-%m-%d %H:%M:%S') if self.verified_at else None,
            'user_name': self.user_name,
            'visitor_name': self.visitor_name,
            'host_name': self.host_name,
            'notes': self.notes
        }
