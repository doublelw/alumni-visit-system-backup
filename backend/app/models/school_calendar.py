"""
校历管理模型
"""

from datetime import datetime, date
from app import db

class SchoolCalendar(db.Model):
    """校历事件表"""
    __tablename__ = 'school_calendar'

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    title = db.Column(db.String(200), nullable=False, comment='事件标题')
    description = db.Column(db.Text, comment='事件描述')
    event_type = db.Column(db.Enum('anniversary', 'festival', 'activity', 'club', 'holiday', 'exam', 'meeting'),
                           nullable=False, default='activity', comment='事件类型')

    # 时间信息
    start_date = db.Column(db.Date, nullable=False, comment='开始日期')
    end_date = db.Column(db.Date, comment='结束日期')
    start_time = db.Column(db.Time, comment='开始时间')
    end_time = db.Column(db.Time, comment='结束时间')
    all_day = db.Column(db.Boolean, default=False, comment='是否全天事件')

    # 校友相关
    target_audience = db.Column(db.Enum('all', 'alumni', 'students', 'teachers', 'specific'),
                               default='all', comment='目标受众')
    target_graduation_years = db.Column(db.String(500), comment='目标毕业年份（逗号分隔）')
    target_divisions = db.Column(db.String(500), comment='目标学部（逗号分隔）')

    # 位置信息
    location = db.Column(db.String(200), comment='活动地点')
    online_url = db.Column(db.String(500), comment='在线链接')

    # 重要程度和状态
    priority = db.Column(db.Enum('low', 'medium', 'high', 'urgent'),
                        default='medium', comment='重要程度')
    status = db.Column(db.Enum('draft', 'published', 'cancelled', 'completed'),
                      default='draft', comment='状态')

    # 联系信息
    contact_person = db.Column(db.String(100), comment='联系人')
    contact_phone = db.Column(db.String(20), comment='联系电话')
    contact_email = db.Column(db.String(100), comment='联系邮箱')

    # 预约信息
    requires_booking = db.Column(db.Boolean, default=False, comment='是否需要预约')
    max_participants = db.Column(db.Integer, comment='最大参与人数')
    booking_deadline = db.Column(db.DateTime, comment='预约截止时间')

    # 系统字段
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, comment='发布时间')

    # 社团活动特有字段
    club_name = db.Column(db.String(100), comment='社团名称')
    club_type = db.Column(db.Enum('academic', 'sports', 'arts', 'volunteer', 'technology', 'other'),
                         comment='社团类型')

    # 返校日特有字段
    anniversary_year = db.Column(db.Integer, comment='周年纪念年数（如10、20、30）')
    graduation_year = db.Column(db.Integer, comment='对应毕业年份')

    # 关系
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_events')
    bookings = db.relationship('EventBooking', backref='event', lazy='dynamic')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'event_type': self.event_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'all_day': self.all_day,
            'target_audience': self.target_audience,
            'target_graduation_years': self.target_graduation_years.split(',') if self.target_graduation_years else [],
            'target_divisions': self.target_divisions.split(',') if self.target_divisions else [],
            'location': self.location,
            'online_url': self.online_url,
            'priority': self.priority,
            'status': self.status,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'requires_booking': self.requires_booking,
            'max_participants': self.max_participants,
            'booking_deadline': self.booking_deadline.isoformat() if self.booking_deadline else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'club_name': self.club_name,
            'club_type': self.club_type,
            'anniversary_year': self.anniversary_year,
            'graduation_year': self.graduation_year,
            'creator_name': self.creator.real_name if self.creator else None,
            'booking_count': self.bookings.count(),
            'is_upcoming': self.is_upcoming(),
            'is_ongoing': self.is_ongoing(),
            'days_until': self.days_until()
        }

    def is_upcoming(self):
        """是否为即将到来的事件"""
        if not self.start_date:
            return False
        today = date.today()
        return self.start_date > today and self.status == 'published'

    def is_ongoing(self):
        """是否正在进行中"""
        if not self.start_date:
            return False
        today = date.today()
        end_date = self.end_date or self.start_date

        if self.start_date <= today <= end_date and self.status == 'published':
            return True

        # 检查时间（如果是今天的事件）
        if self.start_date == today and self.start_time and self.end_time:
            now = datetime.now().time()
            return self.start_time <= now <= self.end_time

        return False

    def days_until(self):
        """距离活动还有多少天"""
        if not self.start_date:
            return None
        today = date.today()
        if self.start_date <= today:
            return 0
        return (self.start_date - today).days

    def __repr__(self):
        return f'<SchoolCalendar {self.title}>'

class EventBooking(db.Model):
    """活动预约表"""
    __tablename__ = 'event_bookings'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('school_calendar.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 预约信息
    booking_time = db.Column(db.DateTime, default=datetime.utcnow, comment='预约时间')
    status = db.Column(db.Enum('confirmed', 'cancelled', 'attended', 'no_show'),
                      default='confirmed', comment='预约状态')
    notes = db.Column(db.Text, comment='备注')

    # 联系信息
    contact_phone = db.Column(db.String(20), comment='联系电话')
    contact_email = db.Column(db.String(100), comment='联系邮箱')

    # 系统字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='event_bookings')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'user_id': self.user_id,
            'booking_time': self.booking_time.isoformat() if self.booking_time else None,
            'status': self.status,
            'notes': self.notes,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_name': self.user.real_name if self.user else None,
            'event_title': self.event.title if self.event else None
        }

    def __repr__(self):
        return f'<EventBooking {self.user_id}->{self.event_id}>'