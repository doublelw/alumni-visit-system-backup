"""
问卷调查模型
"""

from datetime import datetime
from app import db
import json

class Survey(db.Model):
    """问卷表"""
    __tablename__ = 'surveys'

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    title = db.Column(db.String(200), nullable=False, comment='问卷标题')
    description = db.Column(db.Text, comment='问卷描述')

    # 关联事件
    event_id = db.Column(db.Integer, db.ForeignKey('school_calendar.id'), comment='关联的校历事件ID')

    # 问卷设置
    is_anonymous = db.Column(db.Boolean, default=False, comment='是否匿名问卷')
    is_public = db.Column(db.Boolean, default=True, comment='是否公开')
    require_login = db.Column(db.Boolean, default=True, comment='是否需要登录')

    # 时间设置
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='结束时间')

    # 状态
    status = db.Column(db.Enum('draft', 'published', 'closed', 'archived'),
                      default='draft', comment='状态')

    # 系统字段
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_surveys')
    event = db.relationship('SchoolCalendar', backref='surveys')
    questions = db.relationship('SurveyQuestion', backref='survey', lazy='dynamic', cascade='all, delete-orphan')
    responses = db.relationship('SurveyResponse', backref='survey', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'event_id': self.event_id,
            'event_title': self.event.title if self.event else None,
            'is_anonymous': self.is_anonymous,
            'is_public': self.is_public,
            'require_login': self.require_login,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'created_by': self.created_by,
            'creator_name': self.creator.real_name if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'questions_count': self.questions.count(),
            'responses_count': self.responses.count(),
            'is_active': self.is_active()
        }

    def is_active(self):
        """是否正在进行中"""
        if self.status != 'published':
            return False

        now = datetime.utcnow()
        if self.start_time and now < self.start_time:
            return False

        if self.end_time and now > self.end_time:
            return False

        return True

    def __repr__(self):
        return f'<Survey {self.title}>'

class SurveyQuestion(db.Model):
    """问卷问题表"""
    __tablename__ = 'survey_questions'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'), nullable=False)

    # 问题信息
    question_text = db.Column(db.Text, nullable=False, comment='问题内容')
    question_type = db.Column(db.Enum('single_choice', 'multiple_choice', 'text', 'textarea', 'rating', 'number'),
                             nullable=False, comment='问题类型')

    # 选项信息（选择题）
    options = db.Column(db.Text, comment='选项JSON，用于选择题')

    # 验证规则
    is_required = db.Column(db.Boolean, default=True, comment='是否必答')

    # 排序
    order_index = db.Column(db.Integer, default=0, comment='排序索引')

    # 系统字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_options(self):
        """获取选项列表"""
        if self.options:
            try:
                return json.loads(self.options)
            except:
                return []
        return []

    def set_options(self, options_list):
        """设置选项列表"""
        if options_list:
            self.options = json.dumps(options_list, ensure_ascii=False)
        else:
            self.options = None

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'survey_id': self.survey_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'options': self.get_options(),
            'is_required': self.is_required,
            'order_index': self.order_index,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SurveyQuestion {self.question_text[:50]}>'

class SurveyResponse(db.Model):
    """问卷回答表"""
    __tablename__ = 'survey_responses'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='回答用户ID')

    # 回答信息
    answers = db.Column(db.Text, nullable=False, comment='回答内容JSON')

    # 状态
    status = db.Column(db.Enum('draft', 'completed'), default='draft', comment='状态')

    # 系统字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, comment='完成时间')

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='survey_responses')

    def get_answers(self):
        """获取回答内容"""
        if self.answers:
            try:
                return json.loads(self.answers)
            except:
                return {}
        return {}

    def set_answers(self, answers_dict):
        """设置回答内容"""
        self.answers = json.dumps(answers_dict, ensure_ascii=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'survey_id': self.survey_id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else '匿名用户',
            'answers': self.get_answers(),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def __repr__(self):
        return f'<SurveyResponse {self.id}>'