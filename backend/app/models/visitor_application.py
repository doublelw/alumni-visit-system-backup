"""
访客申请模型
"""

from datetime import datetime
from app import db


class VisitorApplication(db.Model):
    """访客申请表"""

    __tablename__ = 'visitor_applications'

    id = db.Column(db.Integer, primary_key=True)

    # 访客信息
    visitor_name = db.Column(db.String(100), nullable=False, comment='访客姓名')
    id_card = db.Column(db.String(18), nullable=True, comment='身份证号')  # 改为nullable，家长用户可能没有
    phone = db.Column(db.String(20), nullable=False, comment='手机号')

    # 访问信息
    visit_reason = db.Column(db.Text, nullable=True, comment='访问事由')
    host_name = db.Column(db.String(100), nullable=True, comment='接待人姓名')
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='接待人ID')
    visit_date = db.Column(db.Date, nullable=True, comment='访问日期')

    # 照片
    photo_data = db.Column(db.Text, nullable=True, comment='Base64照片数据')
    photo_path = db.Column(db.String(255), nullable=True, comment='照片文件路径')

    # 审批信息
    status = db.Column(db.String(20), nullable=False, default='pending',
                       comment='状态: pending/approved/rejected')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='审批人ID')
    approved_at = db.Column(db.DateTime, nullable=True, comment='审批时间')
    rejection_reason = db.Column(db.Text, nullable=True, comment='拒绝原因')

    # 访客码
    access_code = db.Column(db.String(6), nullable=True, comment='6位访客码')
    code_generated_at = db.Column(db.DateTime, nullable=True, comment='码生成时间')
    code_expires_at = db.Column(db.DateTime, nullable=True, comment='码过期时间')

    # 使用记录
    used_count = db.Column(db.Integer, nullable=False, default=0, comment='使用次数')

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')

    # 关系
    host = db.relationship('User', foreign_keys=[host_id], backref='hosted_visitors')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_visitors')

    def __repr__(self):
        return f'<VisitorApplication {self.id}: {self.visitor_name}>'

    def get_photo_url(self):
        """获取照片URL"""
        if self.photo_path:
            return self.photo_path
        elif self.photo_data:
            # 如果有Base64数据，返回data URI
            return f"data:image/jpeg;base64,{self.photo_data}"
        else:
            return None

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'visitor_name': self.visitor_name,
            'id_card': self.id_card,
            'id_card_last4': self.id_card[-4:] if self.id_card else None,
            'phone': self.phone,
            'visit_reason': self.visit_reason,
            'host_name': self.host_name,
            'host_id': self.host_id,
            'visit_date': self.visit_date.strftime('%Y-%m-%d') if self.visit_date else None,
            'photo_url': self.get_photo_url(),
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'access_code': self.access_code,
            'code_expires_at': self.code_expires_at.strftime('%Y-%m-%d %H:%M:%S') if self.code_expires_at else None,
            'used_count': self.used_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
