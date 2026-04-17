"""
访问申请模型
"""

from datetime import datetime, date, time
from app import db

class VisitApplication(db.Model):
    """访问申请表"""
    __tablename__ = 'visit_applications'

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    visit_time_start = db.Column(db.Time, nullable=False)
    visit_time_end = db.Column(db.Time, nullable=False)
    visit_purpose = db.Column(db.Text, nullable=False)
    target_work_id = db.Column(db.String(20))  # 拜访对象工作ID
    target_person = db.Column(db.String(100))
    target_department = db.Column(db.String(100))
    vehicle_info = db.Column(db.Text)  # 车辆信息JSON
    application_status = db.Column(db.Enum('pending', 'approved', 'rejected', 'completed', 'cancelled'),
                                   nullable=False, default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approval_time = db.Column(db.DateTime)
    approval_note = db.Column(db.Text)
    needs_profile_approval = db.Column(db.Boolean, default=False)  # 是否需要校友档案审核
    qr_code = db.Column(db.String(500))  # 二维码数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_qr=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'applicant_id': self.applicant_id,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'visit_time_start': self.visit_time_start.isoformat() if self.visit_time_start else None,
            'visit_time_end': self.visit_time_end.isoformat() if self.visit_time_end else None,
            'visit_purpose': self.visit_purpose,
            'target_work_id': self.target_work_id,
            'target_person': self.target_person,
            'target_department': self.target_department,
            'application_status': self.application_status,
            'approved_by': self.approved_by,
            'approval_time': self.approval_time.isoformat() if self.approval_time else None,
            'approval_note': self.approval_note,
            'needs_profile_approval': self.needs_profile_approval,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_qr and self.qr_code:
            data['qr_code'] = self.qr_code

        return data

    def __repr__(self):
        return f'<VisitApplication {self.id}>'