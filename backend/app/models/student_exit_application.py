"""
学生出校申请模型
"""

from datetime import datetime, date, time
from app import db
from app.models.user import User
import json

class StudentExitApplication(db.Model):
    """学生出校申请表"""
    __tablename__ = 'student_exit_applications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='学生ID')
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='申请人ID（学生或家长）')

    # 出校信息
    exit_date = db.Column(db.Date, nullable=False, comment='出校日期')
    exit_time_start = db.Column(db.Time, nullable=False, comment='出校开始时间')
    exit_time_end = db.Column(db.Time, nullable=False, comment='预计返校时间')
    exit_reason = db.Column(db.Text, nullable=False, comment='出校原因')
    destination = db.Column(db.String(200), nullable=True, comment='目的地')
    transport_method = db.Column(db.String(100), nullable=True, comment='交通方式')
    companion_info = db.Column(db.Text, nullable=True, comment='同行人信息JSON')

    # 审批状态
    application_status = db.Column(db.Enum('pending', 'parent_approved', 'teacher_approved', 'parent_rejected', 'teacher_rejected', 'approved', 'rejected', 'completed', 'cancelled'),
                                   nullable=False, default='pending', comment='申请状态')

    # 家长审批
    parent_approval_status = db.Column(db.Enum('pending', 'approved', 'rejected'),
                                       nullable=False, default='pending', comment='家长审批状态')
    parent_approval_time = db.Column(db.DateTime, nullable=True, comment='家长审批时间')
    parent_approval_note = db.Column(db.Text, nullable=True, comment='家长审批备注')
    parent_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='家长审批人ID')

    # 班主任审批
    teacher_approval_status = db.Column(db.Enum('pending', 'approved', 'rejected'),
                                        nullable=False, default='pending', comment='班主任审批状态')
    teacher_approval_time = db.Column(db.DateTime, nullable=True, comment='班主任审批时间')
    teacher_approval_note = db.Column(db.Text, nullable=True, comment='班主任审批备注')
    teacher_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='班主任审批人ID')

    # 出校状态
    exit_status = db.Column(db.Enum('pending', 'exited', 'returned'),
                           nullable=False, default='pending', comment='出校状态')
    exit_time = db.Column(db.DateTime, nullable=True, comment='实际出校时间')
    return_time = db.Column(db.DateTime, nullable=True, comment='实际返校时间')

    # 二维码凭证
    qr_code = db.Column(db.String(500), nullable=True, comment='出校二维码数据')
    qr_code_expires_at = db.Column(db.DateTime, nullable=True, comment='二维码过期时间')
    verification_code = db.Column(db.String(6), nullable=True, comment='6位验证码')

    # 其他信息
    emergency_contact = db.Column(db.String(100), nullable=True, comment='紧急联系人')
    emergency_phone = db.Column(db.String(20), nullable=True, comment='紧急联系电话')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_qr=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'applicant_id': self.applicant_id,
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,
            'exit_time_start': self.exit_time_start.isoformat() if self.exit_time_start else None,
            'exit_time_end': self.exit_time_end.isoformat() if self.exit_time_end else None,
            'exit_reason': self.exit_reason,
            'destination': self.destination,
            'transport_method': self.transport_method,
            'application_status': self.application_status,
            'parent_approval_status': self.parent_approval_status,
            'parent_approval_time': self.parent_approval_time.isoformat() if self.parent_approval_time else None,
            'parent_approval_note': self.parent_approval_note,
            'parent_approved_by': self.parent_approved_by,
            'teacher_approval_status': self.teacher_approval_status,
            'teacher_approval_time': self.teacher_approval_time.isoformat() if self.teacher_approval_time else None,
            'teacher_approval_note': self.teacher_approval_note,
            'teacher_approved_by': self.teacher_approved_by,
            'exit_status': self.exit_status,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'return_time': self.return_time.isoformat() if self.return_time else None,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        # 解析同行人信息
        if self.companion_info:
            try:
                data['companion_info'] = json.loads(self.companion_info)
            except (json.JSONDecodeError, TypeError):
                data['companion_info'] = []
        else:
            data['companion_info'] = []

        if include_qr and self.qr_code:
            data['qr_code'] = self.qr_code
            data['qr_code_expires_at'] = self.qr_code_expires_at.isoformat() if self.qr_code_expires_at else None
            data['verification_code'] = self.verification_code

        return data

    def update_approval_status(self):
        """更新审批状态"""
        if self.parent_approval_status == 'approved' and self.teacher_approval_status == 'approved':
            self.application_status = 'approved'
            # 生成二维码
            self.generate_qr_code()
        elif self.parent_approval_status == 'rejected' or self.teacher_approval_status == 'rejected':
            self.application_status = 'rejected'
        elif self.parent_approval_status == 'approved' and self.teacher_approval_status == 'pending':
            self.application_status = 'parent_approved'
        elif self.parent_approval_status == 'pending' and self.teacher_approval_status == 'approved':
            self.application_status = 'teacher_approved'

        db.session.commit()

    def generate_qr_code(self):
        """生成出校二维码"""
        if self.application_status == 'approved':
            import random
            import string

            # 生成6位数字验证码
            self.verification_code = ''.join(random.choices(string.digits, k=6))

            qr_data = {
                'type': 'student_exit',
                'id': self.id,
                'student_id': self.student_id,
                'exit_date': self.exit_date.isoformat() if self.exit_date else None,
                'exit_time_start': self.exit_time_start.isoformat() if self.exit_time_start else None,
                'exit_time_end': self.exit_time_end.isoformat() if self.exit_time_end else None,
                'student_name': self.student.real_name if self.student else None,
                'class_id': self.student.class_id if self.student else None,
                'grade': self.student.grade if self.student else None,
                'verification_code': self.verification_code,
                'generated_at': datetime.utcnow().isoformat()
            }
            self.qr_code = json.dumps(qr_data, ensure_ascii=False)
            # 设置二维码过期时间为当天晚上11点59分
            if self.exit_date:
                from datetime import time as dt_time
                self.qr_code_expires_at = datetime.combine(self.exit_date, dt_time(23, 59))
            db.session.commit()

    def is_qr_code_valid(self):
        """检查二维码是否有效"""
        if not self.qr_code or not self.qr_code_expires_at:
            return False
        return datetime.utcnow() <= self.qr_code_expires_at and self.application_status == 'approved'

    def can_approve(self, user_id, user_type):
        """检查用户是否可以审批"""
        if user_type == 'parent':
            # 检查是否是学生的家长
            student = User.query.get(self.student_id)
            return student and student.student_parent_id == user_id and self.parent_approval_status == 'pending'
        elif user_type == 'teacher':
            # 检查是否是班主任
            teacher = User.query.get(user_id)
            return teacher and teacher.is_class_teacher and self.teacher_approval_status == 'pending'
        return False

    @property
    def student(self):
        """获取学生信息"""
        return User.query.get(self.student_id)

    @property
    def applicant(self):
        """获取申请人信息"""
        return User.query.get(self.applicant_id)

    @property
    def parent_approver(self):
        """获取家长审批人信息"""
        return User.query.get(self.parent_approved_by) if self.parent_approved_by else None

    @property
    def teacher_approver(self):
        """获取班主任审批人信息"""
        return User.query.get(self.teacher_approved_by) if self.teacher_approved_by else None

    def __repr__(self):
        return f'<StudentExitApplication {self.id}>'