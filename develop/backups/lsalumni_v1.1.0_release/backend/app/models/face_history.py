"""
人脸历史记录模型
"""

from datetime import datetime
from app import db
from app.models.user import User


class FaceHistory(db.Model):
    """人脸历史记录表"""
    __tablename__ = 'face_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')

    # 人脸信息
    face_encoding = db.Column(db.Text, nullable=False, comment='人脸特征数据')
    face_image_path = db.Column(db.String(500), nullable=True, comment='人脸图像路径')

    # 操作信息
    operation_type = db.Column(db.Enum('register', 'update', 'delete'), nullable=False, comment='操作类型：注册、更新、删除')
    previous_face_id = db.Column(db.Integer, nullable=True, comment='前一个人脸记录ID')

    # 验证信息
    is_verified = db.Column(db.Boolean, default=False, comment='是否已验证通过')
    verification_method = db.Column(db.Enum('auto', 'manual', 'comparison'), default='auto', comment='验证方式：自动、人工、对比')
    verification_score = db.Column(db.Float, nullable=True, comment='验证得分')
    verification_admin_id = db.Column(db.Integer, nullable=True, comment='验证管理员ID')
    verification_note = db.Column(db.Text, nullable=True, comment='验证备注')
    verification_time = db.Column(db.DateTime, nullable=True, comment='验证时间')

    # 设备和位置信息
    device_info = db.Column(db.String(500), nullable=True, comment='设备信息')
    ip_address = db.Column(db.String(45), nullable=True, comment='IP地址')
    user_agent = db.Column(db.Text, nullable=True, comment='用户代理')

    # 状态
    status = db.Column(db.Enum('active', 'inactive', 'suspicious', 'rejected'), default='active', comment='状态')
    is_current = db.Column(db.Boolean, default=False, comment='是否为当前使用的人脸')

    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'face_image_path': self.face_image_path,
            'operation_type': self.operation_type,
            'previous_face_id': self.previous_face_id,
            'is_verified': self.is_verified,
            'verification_method': self.verification_method,
            'verification_score': self.verification_score,
            'verification_admin_id': self.verification_admin_id,
            'verification_note': self.verification_note,
            'verification_time': self.verification_time.isoformat() if self.verification_time else None,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'status': self.status,
            'is_current': self.is_current,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create_new_face_record(cls, user_id, face_encoding, face_image_path=None, operation_type='update',
                              device_info=None, ip_address=None, user_agent=None, previous_face_id=None):
        """创建新的人脸记录"""
        # 如果是更新操作，将之前的记录标记为非当前
        if operation_type == 'update':
            current_records = cls.query.filter_by(user_id=user_id, is_current=True).all()
            for record in current_records:
                record.is_current = False

        # 创建新记录
        new_record = cls(
            user_id=user_id,
            face_encoding=face_encoding,
            face_image_path=face_image_path,
            operation_type=operation_type,
            previous_face_id=previous_face_id,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            is_current=True
        )

        db.session.add(new_record)
        db.session.commit()
        return new_record

    @classmethod
    def get_user_face_history(cls, user_id, limit=10):
        """获取用户的人脸历史记录"""
        return cls.query.filter_by(user_id=user_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit)\
                       .all()

    @classmethod
    def get_current_face(cls, user_id):
        """获取用户当前使用的人脸记录"""
        return cls.query.filter_by(user_id=user_id, is_current=True).first()

    @classmethod
    def compare_with_previous_faces(cls, user_id, new_face_encoding, threshold=0.6):
        """与历史人脸记录进行对比"""
        previous_faces = cls.query.filter_by(user_id=user_id)\
                                 .filter(cls.face_encoding.isnot(None))\
                                 .order_by(cls.created_at.desc())\
                                 .limit(5)\
                                 .all()

        comparison_results = []
        for face_record in previous_faces:
            try:
                # 这里需要实现人脸特征对比算法
                similarity = cls._calculate_face_similarity(new_face_encoding, face_record.face_encoding)
                comparison_results.append({
                    'face_id': face_record.id,
                    'similarity': similarity,
                    'created_at': face_record.created_at,
                    'is_match': similarity >= threshold
                })
            except Exception as e:
                comparison_results.append({
                    'face_id': face_record.id,
                    'similarity': 0.0,
                    'created_at': face_record.created_at,
                    'is_match': False,
                    'error': str(e)
                })

        return comparison_results

    @staticmethod
    def _calculate_face_similarity(encoding1, encoding2):
        """计算两个人脸特征的相似度"""
        try:
            import numpy as np
            import json

            # 解码JSON格式的人脸特征
            if isinstance(encoding1, str):
                encoding1 = json.loads(encoding1)
            if isinstance(encoding2, str):
                encoding2 = json.loads(encoding2)

            # 转换为numpy数组
            face1 = np.array(encoding1)
            face2 = np.array(encoding2)

            # 计算欧氏距离
            distance = np.linalg.norm(face1 - face2)

            # 转换为相似度（距离越小，相似度越高）
            similarity = 1 / (1 + distance)

            return similarity

        except Exception as e:
            print(f"计算人脸相似度失败: {e}")
            return 0.0

    @property
    def user(self):
        """获取用户信息"""
        return User.query.get(self.user_id)

    @property
    def previous_face(self):
        """获取前一个人脸记录"""
        return FaceHistory.query.get(self.previous_face_id) if self.previous_face_id else None

    def __repr__(self):
        return f'<FaceHistory {self.id} User:{self.user_id} Type:{self.operation_type}>'