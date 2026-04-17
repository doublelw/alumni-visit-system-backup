"""
学生请假模型
"""

from datetime import datetime
from backend.app import db


class LeaveRequest(db.Model):
    """学生请假申请表"""

    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='学生ID')
    leave_type = db.Column(db.String(20), nullable=False, comment='请假类型: sick/personal/other')
    leave_reason = db.Column(db.Text, nullable=False, comment='请假事由')
    leave_start_time = db.Column(db.DateTime, nullable=False, comment='请假开始时间')
    leave_end_time = db.Column(db.DateTime, nullable=False, comment='请假结束时间')
    parent_phone = db.Column(db.String(20), nullable=False, comment='家长手机号')

    # 老师审批
    teacher_status = db.Column(db.String(20), nullable=False, default='pending', comment='老师审批状态')
    teacher_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='审批老师ID')
    teacher_approved_at = db.Column(db.DateTime, nullable=True, comment='审批时间')
    teacher_rejection_reason = db.Column(db.Text, nullable=True, comment='拒绝原因')

    # 家长验证
    parent_verify_code = db.Column(db.String(6), nullable=True, comment='家长验证码')
    parent_verified = db.Column(db.Boolean, nullable=False, default=False, comment='家长是否已验证')
    parent_verified_at = db.Column(db.DateTime, nullable=True, comment='家长验证时间')

    # 离校通行
    leave_pass_code = db.Column(db.String(6), nullable=True, comment='离校通行码')
    pass_status = db.Column(db.String(20), nullable=False, default='pending', comment='通行状态')
    used_count = db.Column(db.Integer, nullable=False, default=0, comment='使用次数: 0=未使用, 1=已离校, 2=已返校')
    expires_at = db.Column(db.DateTime, nullable=True, comment='过期时间')

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')

    # 关系
    student = db.relationship('User', foreign_keys=[student_id], backref='leave_requests')
    teacher_approver = db.relationship('User', foreign_keys=[teacher_approved_by])

    def __repr__(self):
        return f'<LeaveRequest {self.id}: {self.student.real_name if self.student else "Unknown"} - {self.leave_type}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.real_name if self.student else None,
            'leave_type': self.leave_type,
            'leave_reason': self.leave_reason,
            'leave_start_time': self.leave_start_time.strftime('%Y-%m-%d %H:%M:%S') if self.leave_start_time else None,
            'leave_end_time': self.leave_end_time.strftime('%Y-%m-%d %H:%M:%S') if self.leave_end_time else None,
            'parent_phone': self.parent_phone,
            'teacher_status': self.teacher_status,
            'teacher_approved_by': self.teacher_approved_by,
            'teacher_approved_at': self.teacher_approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.teacher_approved_at else None,
            'teacher_rejection_reason': self.teacher_rejection_reason,
            'parent_verified': self.parent_verified,
            'parent_verified_at': self.parent_verified_at.strftime('%Y-%m-%d %H:%M:%S') if self.parent_verified_at else None,
            'leave_pass_code': self.leave_pass_code,
            'pass_status': self.pass_status,
            'used_count': self.used_count,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M:%S') if self.expires_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
