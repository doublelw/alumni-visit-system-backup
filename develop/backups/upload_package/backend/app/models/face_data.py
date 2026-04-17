"""
人脸数据模型
"""

from datetime import datetime
from app import db

class FaceData(db.Model):
    """人脸信息表"""
    __tablename__ = 'face_data'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    face_encoding = db.Column(db.Text, nullable=False)  # 人脸特征编码(JSON字符串)
    face_image_path = db.Column(db.String(500), nullable=False)  # 人脸图片路径
    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    quality_score = db.Column(db.Float)  # 人脸图片质量分数
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'registration_time': self.registration_time.isoformat() if self.registration_time else None,
            'is_active': self.is_active,
            'quality_score': self.quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<FaceData {self.user_id}>'