"""
学生请假申请模型
"""

from datetime import datetime
from app import db


class StudentLeaveApplication(db.Model):
    """学生请假申请表"""

    __tablename__ = 'student_leave_applications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_name = db.Column(db.String(50), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20))

    # 家长信息
    parent_name = db.Column(db.String(50), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)
    parent_id_card = db.Column(db.String(18))

    # 请假信息
    leave_reason = db.Column(db.Text, nullable=False)
    leave_type = db.Column(db.String(20), nullable=False)  # sick/personal/other
    expected_return_time = db.Column(db.DateTime, nullable=False)

    # 请假码
    leave_code = db.Column(db.String(6), unique=True, nullable=False)

    # 审批信息
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending/approved/rejected
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    teacher_name = db.Column(db.String(50))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)

    # 使用次数（0=未用, 1=已出校, 2=已往返完成）
    used_count = db.Column(db.Integer, default=0, nullable=False)

    # 特批标记
    is_emergency = db.Column(db.Boolean, default=False, nullable=False)
    emergency_approver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    emergency_approver_name = db.Column(db.String(50))
    emergency_reason = db.Column(db.Text)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    # 关系
    student = db.relationship('User', foreign_keys=[student_id], backref='leave_applications')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='approved_leaves')
    emergency_approver = db.relationship('User', foreign_keys=[emergency_approver_id], backref='emergency_approvals')

    def __repr__(self):
        return f'<StudentLeaveApplication {self.id}: {self.student_name} - {self.status}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'class_name': self.class_name,
            'grade': self.grade,
            'parent_name': self.parent_name,
            'parent_phone': self.parent_phone,
            'leave_reason': self.leave_reason,
            'leave_type': self.leave_type,
            'leave_type_label': self.get_leave_type_label(),
            'expected_return_time': self.expected_return_time.strftime('%Y-%m-%d %H:%M') if self.expected_return_time else None,
            'leave_code': self.leave_code,
            'status': self.status,
            'status_label': self.get_status_label(),
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher_name,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M') if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'used_count': self.used_count,
            'is_emergency': self.is_emergency,
            'emergency_approver_name': self.emergency_approver_name,
            'emergency_reason': self.emergency_reason,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M') if self.expires_at else None
        }

    def get_leave_type_label(self):
        """获取请假类型标签"""
        labels = {
            'sick': '病假',
            'personal': '事假',
            'other': '其他'
        }
        return labels.get(self.leave_type, self.leave_type)

    def get_status_label(self):
        """获取状态标签"""
        labels = {
            'pending': '待审批',
            'approved': '已批准',
            'rejected': '已拒绝'
        }
        return labels.get(self.status, self.status)

    def is_valid(self):
        """检查请假码是否有效"""
        if self.status != 'approved':
            return False, '请假申请未批准'
        if datetime.utcnow() > self.expires_at:
            return False, '请假码已过期'
        if self.used_count >= 2:
            return False, '请假码已使用完毕'
        return True, '有效'

    def can_use(self):
        """检查是否可以使用（未用完）"""
        return self.used_count < 2

    def get_remaining_uses(self):
        """获取剩余使用次数"""
        return 2 - self.used_count
