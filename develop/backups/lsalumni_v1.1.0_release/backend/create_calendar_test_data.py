#!/usr/bin/env python3
"""
创建校历管理测试数据
"""

from datetime import datetime, date, timedelta
from app import create_app, db
from app.models.school_calendar import SchoolCalendar
from app.models.user import User
import random

def create_calendar_test_data():
    """创建校历测试数据"""
    app = create_app('development')

    with app.app_context():
        print("创建校历测试数据...")

        # 获取管理员用户
        admin_user = User.query.filter_by(user_type='admin').first()
        if not admin_user:
            print("未找到管理员用户，请先创建管理员账户")
            return

        # 清除现有的校历数据
        SchoolCalendar.query.delete()
        db.session.commit()
        print("已清除现有校历数据")

        # 当前日期
        today = date.today()

        # 测试数据
        events_data = [
            # 校庆和周年活动
            {
                'title': '建校65周年校庆',
                'description': '学校65周年校庆庆典活动，邀请历届校友返校参加',
                'event_type': 'anniversary',
                'start_date': date(today.year, 10, 1),
                'end_date': date(today.year, 10, 3),
                'all_day': True,
                'location': '学校大礼堂',
                'priority': 'urgent',
                'status': 'published',
                'target_audience': 'all',
                'anniversary_year': 65,
                'contact_person': '校庆办公室',
                'contact_phone': '010-12345678',
                'contact_email': 'anniversary@school.edu.cn'
            },

            # 毕业10周年返校
            {
                'title': '2014届校友毕业10周年返校日',
                'description': '2014届校友毕业十周年返校活动，重温校园时光',
                'event_type': 'anniversary',
                'start_date': date(today.year, 7, 15),
                'all_day': True,
                'location': '学校各校区',
                'priority': 'high',
                'status': 'published',
                'target_audience': 'alumni',
                'target_graduation_years': ['2014'],
                'anniversary_year': 10,
                'graduation_year': 2014,
                'contact_person': '校友会',
                'contact_phone': '010-87654321',
                'contact_email': 'alumni@school.edu.cn',
                'requires_booking': True,
                'max_participants': 500,
                'booking_deadline': datetime(today.year, 7, 10, 23, 59, 59)
            },

            # 毕业20周年返校
            {
                'title': '2004届校友毕业20周年返校日',
                'description': '2004届校友毕业二十周年返校活动',
                'event_type': 'anniversary',
                'start_date': date(today.year, 8, 20),
                'all_day': True,
                'location': '学校主校区',
                'priority': 'high',
                'status': 'published',
                'target_audience': 'alumni',
                'target_graduation_years': ['2004'],
                'anniversary_year': 20,
                'graduation_year': 2004,
                'contact_person': '校友会',
                'contact_phone': '010-87654321',
                'contact_email': 'alumni@school.edu.cn'
            },

            # 毕业30周年返校
            {
                'title': '1994届校友毕业30周年返校日',
                'description': '1994届校友毕业三十周年返校活动',
                'event_type': 'anniversary',
                'start_date': date(today.year, 9, 10),
                'all_day': True,
                'location': '学校各校区',
                'priority': 'medium',
                'status': 'published',
                'target_audience': 'alumni',
                'target_graduation_years': ['1994'],
                'anniversary_year': 30,
                'graduation_year': 1994,
                'contact_person': '校友会',
                'contact_phone': '010-87654321',
                'contact_email': 'alumni@school.edu.cn'
            },

            # 传统节日活动
            {
                'title': '2025年春节校友联谊会',
                'description': '春节期间校友联谊活动，共度新春佳节',
                'event_type': 'festival',
                'start_date': date(today.year, 2, 10),
                'start_time': datetime.strptime('18:00', '%H:%M').time(),
                'end_time': datetime.strptime('21:00', '%H:%M').time(),
                'location': '学校校友之家',
                'priority': 'medium',
                'status': 'published',
                'target_audience': 'all',
                'contact_person': '校友会',
                'contact_phone': '010-87654321',
                'contact_email': 'alumni@school.edu.cn',
                'requires_booking': True,
                'max_participants': 200,
                'booking_deadline': datetime(today.year, 2, 5, 18, 0, 0)
            },

            {
                'title': '中秋节月光晚会',
                'description': '传统中秋节月光晚会，赏月品茗',
                'event_type': 'festival',
                'start_date': date(today.year, 9, 21),
                'start_time': datetime.strptime('19:00', '%H:%M').time(),
                'end_time': datetime.strptime('22:00', '%H:%M').time(),
                'location': '学校湖畔',
                'priority': 'medium',
                'status': 'published',
                'target_audience': 'all',
                'contact_person': '学生处',
                'contact_phone': '010-11111111',
                'contact_email': 'student@school.edu.cn'
            },

            # 学术活动
            {
                'title': '校友学术讲座系列 - 人工智能前沿',
                'description': '邀请在人工智能领域有突出贡献的校友回校分享最新研究成果',
                'event_type': 'activity',
                'start_date': today + timedelta(days=15),
                'start_time': datetime.strptime('14:00', '%H:%M').time(),
                'end_time': datetime.strptime('16:30', '%H:%M').time(),
                'location': '学术报告厅',
                'priority': 'medium',
                'status': 'published',
                'target_audience': 'all',
                'contact_person': '教务处',
                'contact_phone': '010-22222222',
                'contact_email': 'academic@school.edu.cn',
                'online_url': 'https://live.school.edu.cn/ai-lecture'
            },

            {
                'title': '创新创业校友分享会',
                'description': '邀请创业成功的校友分享创业经验和心得',
                'event_type': 'activity',
                'start_date': today + timedelta(days=22),
                'start_time': datetime.strptime('15:00', '%H:%M').time(),
                'end_time': datetime.strptime('17:30', '%H:%M').time(),
                'location': '创新创业中心',
                'priority': 'medium',
                'status': 'published',
                'target_audience': 'students',
                'target_graduation_years': ['2015', '2016', '2017', '2018', '2019', '2020'],
                'contact_person': '创新创业中心',
                'contact_phone': '010-33333333',
                'contact_email': 'innovation@school.edu.cn'
            },

            # 社团活动
            {
                'title': '校友篮球友谊赛',
                'description': '校友与在校师生篮球友谊赛',
                'event_type': 'club',
                'start_date': today + timedelta(days=8),
                'start_time': datetime.strptime('16:00', '%H:%M').time(),
                'end_time': datetime.strptime('18:00', '%H:%M').time(),
                'location': '体育馆',
                'priority': 'low',
                'status': 'published',
                'target_audience': 'all',
                'club_name': '篮球俱乐部',
                'club_type': 'sports',
                'contact_person': '体育部',
                'contact_phone': '010-44444444',
                'contact_email': 'sports@school.edu.cn',
                'requires_booking': True,
                'max_participants': 40
            },

            {
                'title': '校友摄影展',
                'description': '展示校友摄影作品的展览活动',
                'event_type': 'club',
                'start_date': today + timedelta(days=30),
                'end_date': today + timedelta(days=45),
                'all_day': True,
                'location': '艺术馆',
                'priority': 'low',
                'status': 'published',
                'target_audience': 'all',
                'club_name': '摄影协会',
                'club_type': 'arts',
                'contact_person': '艺术部',
                'contact_phone': '010-55555555',
                'contact_email': 'arts@school.edu.cn'
            },

            # 重要会议
            {
                'title': '校友代表大会',
                'description': '校友代表大会，选举新一届校友会理事会',
                'event_type': 'meeting',
                'start_date': today + timedelta(days=60),
                'start_time': datetime.strptime('09:00', '%H:%M').time(),
                'end_time': datetime.strptime('12:00', '%H:%M').time(),
                'location': '大会议室',
                'priority': 'high',
                'status': 'draft',  # 草稿状态
                'target_audience': 'alumni',
                'contact_person': '校友会',
                'contact_phone': '010-87654321',
                'contact_email': 'alumni@school.edu.cn'
            },

            # 即将到来的活动（用于测试仪表板）
            {
                'title': '春季校园开放日',
                'description': '春季校园开放日，欢迎校友带家人回校参观',
                'event_type': 'activity',
                'start_date': today + timedelta(days=3),
                'all_day': True,
                'location': '全校',
                'priority': 'medium',
                'status': 'published',
                'target_audience': 'all',
                'contact_person': '招生办',
                'contact_phone': '010-66666666',
                'contact_email': 'admission@school.edu.cn'
            },

            {
                'title': '高中部家长开放日',
                'description': '高中部家长开放日活动',
                'event_type': 'activity',
                'start_date': today + timedelta(days=7),
                'start_time': datetime.strptime('08:30', '%H:%M').time(),
                'end_time': datetime.strptime('17:00', '%H:%M').time(),
                'location': '高中部',
                'priority': 'medium',
                'status': 'published',
                'target_audience': 'specific',
                'target_divisions': ['高中部'],
                'contact_person': '高中部',
                'contact_phone': '010-77777777',
                'contact_email': 'highschool@school.edu.cn'
            },

            {
                'title': '国际部文化体验日',
                'description': '国际部多元文化体验活动',
                'event_type': 'activity',
                'start_date': today + timedelta(days=12),
                'start_time': datetime.strptime('13:00', '%H:%M').time(),
                'end_time': datetime.strptime('18:00', '%H:%M').time(),
                'location': '国际部',
                'priority': 'medium',
                'status': 'published',
                'target_audience': 'all',
                'target_divisions': ['国际部'],
                'contact_person': '国际部',
                'contact_phone': '010-88888888',
                'contact_email': 'international@school.edu.cn'
            },

            # 已取消的活动（用于测试状态管理）
            {
                'title': '原定夏季运动会',
                'description': '因天气原因，原定夏季运动会取消',
                'event_type': 'activity',
                'start_date': today - timedelta(days=10),
                'all_day': True,
                'location': '运动场',
                'priority': 'medium',
                'status': 'cancelled',
                'target_audience': 'all',
                'contact_person': '体育部',
                'contact_phone': '010-44444444',
                'contact_email': 'sports@school.edu.cn'
            },

            # 已完成的活动
            {
                'title': '新年音乐会',
                'description': '2025年新年音乐会',
                'event_type': 'activity',
                'start_date': today - timedelta(days=20),
                'start_time': datetime.strptime('19:30', '%H:%M').time(),
                'end_time': datetime.strptime('21:30', '%H:%M').time(),
                'location': '音乐厅',
                'priority': 'medium',
                'status': 'completed',
                'target_audience': 'all',
                'contact_person': '艺术部',
                'contact_phone': '010-55555555',
                'contact_email': 'arts@school.edu.cn'
            }
        ]

        # 创建事件
        created_events = []
        for event_data in events_data:
            # 处理列表字段，转换为字符串
            data_copy = event_data.copy()
            if 'target_graduation_years' in data_copy and isinstance(data_copy['target_graduation_years'], list):
                data_copy['target_graduation_years'] = ','.join(data_copy['target_graduation_years'])
            if 'target_divisions' in data_copy and isinstance(data_copy['target_divisions'], list):
                data_copy['target_divisions'] = ','.join(data_copy['target_divisions'])

            event = SchoolCalendar(
                created_by=admin_user.id,
                **data_copy
            )

            # 如果状态是发布，设置发布时间
            if event.status == 'published':
                event.published_at = datetime.now()

            db.session.add(event)
            created_events.append(event)

        db.session.commit()

        print(f"成功创建 {len(created_events)} 个校历事件")

        # 统计信息
        total_events = len(created_events)
        published_events = len([e for e in created_events if e.status == 'published'])
        anniversary_events = len([e for e in created_events if e.event_type == 'anniversary'])
        upcoming_events = len([e for e in created_events if e.start_date > today and e.status == 'published'])

        print(f"\n校历事件统计:")
        print(f"  总事件数: {total_events}")
        print(f"  已发布: {published_events}")
        print(f"  周年活动: {anniversary_events}")
        print(f"  即将到来: {upcoming_events}")
        print(f"\n创建完成！")

if __name__ == '__main__':
    create_calendar_test_data()