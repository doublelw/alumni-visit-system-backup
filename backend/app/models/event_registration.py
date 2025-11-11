"""
返校日活动报名模型
"""

from datetime import datetime
from app import db

class EventRegistration(db.Model):
    """返校日活动报名"""
    __tablename__ = 'event_registrations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    real_name = db.Column(db.String(100), nullable=False)

    # 就餐信息
    will_dine = db.Column(db.Boolean, default=False, comment='是否在食堂就餐')
    favorite_dishes = db.Column(db.Text, comment='最想吃的四个菜，JSON格式')

    # 报名信息
    registration_time = db.Column(db.DateTime, default=datetime.utcnow, comment='报名时间')
    contact_phone = db.Column(db.String(20), comment='联系电话')
    notes = db.Column(db.Text, comment='备注信息')

    # 状态
    status = db.Column(db.String(20), default='active', comment='报名状态：active/cancelled')

    # 关联关系
    user = db.relationship('User', backref=db.backref('event_registrations', lazy=True))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'real_name': self.real_name,
            'will_dine': self.will_dine,
            'favorite_dishes': self.favorite_dishes,
            'registration_time': self.registration_time.isoformat() if self.registration_time else None,
            'contact_phone': self.contact_phone,
            'notes': self.notes,
            'status': self.status,
            'user': self.user.to_dict() if self.user else None
        }

    @staticmethod
    def get_dish_list():
        """获取菜品列表"""
        return [
            # 红烧肉类
            '红烧肉', '糖醋里脊', '红烧排骨', '红烧鸡翅', '红烧猪蹄',
            '红烧带鱼', '红烧茄子', '红烧豆腐',

            # 川菜类
            '水煮肉片', '毛血旺', '水煮鱼', '酸菜鱼',
            '川香肉丝', '鱼香肉丝', '京酱肉丝', '宫保鸡丁',
            '回锅肉', '麻婆豆腐', '蚂蚁上树',

            # 炒菜类
            '干煸四季豆', '干煸豆角', '干煸土豆丝', '干煸牛肉丝',
            '辣子鸡丁', '宫爆鸡丁', '青椒肉丝', '芹菜肉丝',
            '蒜苔肉丝', '洋葱肉丝', '韭菜肉丝',

            # 特色菜类
            '鱼香茄子', '地三鲜', '麻婆豆腐',
            '家常豆腐', '肉末茄子', '肉末豆腐',

            # 汤羹类
            '酸菜粉丝汤', '紫菜蛋花汤', '西红柿鸡蛋汤',
            '冬瓜排骨汤', '玉米排骨汤', '萝卜排骨汤',
            '海带豆腐汤',

            # 小炒类
            '青椒土豆丝', '酸辣土豆丝', '蒜蓉菠菜', '清炒时蔬',
            '蚝油生菜', '炒合菜', '炒豆芽',

            # 鸡蛋类
            '西红柿炒鸡蛋', '韭菜炒鸡蛋', '黄瓜炒鸡蛋',
            '苦瓜炒鸡蛋', '青椒炒鸡蛋',

            # 主食类
            '蛋炒饭', '扬州炒饭', '酱油炒饭',
            '盖浇饭', '咖喱炒饭', '海鲜炒饭'
        ]

    @staticmethod
    def get_dish_statistics():
        """获取菜品统计"""
        from sqlalchemy import func

        # 查询所有有效报名中选择的菜品
        registrations = EventRegistration.query.filter_by(status='active', will_dine=True).all()

        dish_count = {}
        for reg in registrations:
            if reg.favorite_dishes:
                try:
                    import json
                    dishes = json.loads(reg.favorite_dishes)
                    for dish in dishes:
                        if dish in dish_count:
                            dish_count[dish] += 1
                        else:
                            dish_count[dish] = 1
                except:
                    continue

        # 排序并返回前10
        sorted_dishes = sorted(dish_count.items(), key=lambda x: x[1], reverse=True)[:10]
        return [{'dish': dish, 'count': count} for dish, count in sorted_dishes]

    def __repr__(self):
        return f'<EventRegistration {self.real_name}>'