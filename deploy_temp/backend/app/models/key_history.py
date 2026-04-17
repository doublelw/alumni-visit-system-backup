"""
密钥历史记录模型

记录所有密钥的更换历史，用于审计和安全追踪
"""

from datetime import datetime
from app import db


class KeyHistory(db.Model):
    """密钥更换历史记录"""

    __tablename__ = 'key_history'

    id = db.Column(db.Integer, primary_key=True)
    key_type = db.Column(db.String(50), nullable=False, index=True)  # 密钥类型: electronic_card, jwt
    old_key = db.Column(db.String(100))  # 旧密钥预览（只保存前8位）
    new_key = db.Column(db.String(100))  # 新密钥预览（只保存前8位）
    changed_by = db.Column(db.String(100), nullable=False)  # 更换人
    changed_at = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 更换时间
    reason = db.Column(db.String(200))  # 更换原因: scheduled_rotation, security_incident, etc.

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'key_type': self.key_type,
            'old_key_preview': self.old_key,
            'new_key_preview': self.new_key,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.strftime('%Y-%m-%d %H:%M:%S') if self.changed_at else None,
            'reason': self.reason
        }

    def __repr__(self):
        return f'<KeyHistory {self.key_type} at {self.changed_at}>'
