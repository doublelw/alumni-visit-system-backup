"""
创建基于5月4日建校日的模拟校历数据
"""

from datetime import datetime, date, timedelta
from app import create_app, db
from app.models.school_calendar import SchoolCalendar
from app.models.user import User
import random

def create_school_calendar_data():
    """创建模拟校历数据"""
    app = create_app()

    with app.app_context():
        # 获取管理员用户
        admin_user = User.query.filter_by(user_type='admin').first()
        if not admin_user:
            print("错误：未找到管理员用户")
            return

        # 清除现有数据
        SchoolCalendar.query.delete()
        db.session.commit()

        # 当前年份
        current_year = datetime.now().year

        events = []

        # 1. 建校纪念日（5月4日）- 每年最重要的活动
        for year in range(current_year - 2, current_year + 3):
            # 计算校庆周年数（假设1924年建校）
            anniversary_year = year - 1924
            if anniversary_year > 0:
                events.append({
                    'title': f'{anniversary_year}周年校庆纪念日',
                    'description': f'庆祝学校建校{anniversary_year}周年，弘扬五四精神，传承校园文化。',
                    'event_type': 'anniversary',
                    'start_date': date(year, 5, 4),
                    'end_date': date(year, 5, 4),
                    'start_time': '09:00',
                    'end_time': '17:00',
                    'all_day': True,
                    'location': '学校体育场',
                    'priority': 'high',
                    'status': 'published',
                    'contact_person': '校庆筹备委员会',
                    'contact_phone': '400-888-8888',
                    'contact_email': 'anniversary@school.edu.cn',
                    'anniversary_year': anniversary_year,
                    'created_by': admin_user.id
                })

        # 2. 学年重要活动
        for year in range(current_year, current_year + 2):
            # 春季学期开学
            events.append({
                'title': f'{year}年春季学期开学典礼',
                'description': '新学期开始，全体师生参加开学典礼，迎接新的学习生活。',
                'event_type': 'activity',
                'start_date': date(year, 2, 26),
                'end_date': date(year, 2, 26),
                'start_time': '08:30',
                'end_time': '11:00',
                'location': '学校大礼堂',
                'priority': 'high',
                'status': 'published',
                'contact_person': '教务处',
                'contact_phone': '010-12345678',
                'created_by': admin_user.id
            })

            # 清明节纪念活动
            qingming_date = date(year, 4, 5)  # 简化处理，实际清明节日期会变动
            events.append({
                'title': f'{year}年清明节纪念活动',
                'description': '缅怀革命先烈，传承红色基因，进行爱国主义教育。',
                'event_type': 'festival',
                'start_date': qingming_date,
                'end_date': qingming_date,
                'start_time': '09:00',
                'end_time': '11:30',
                'location': '学校纪念广场',
                'priority': 'medium',
                'status': 'published',
                'contact_person': '学生处',
                'created_by': admin_user.id
            })

            # 五四青年节（与建校日结合）
            events.append({
                'title': f'{year}年五四青年节暨建校纪念日系列活动',
                'description': '弘扬五四精神，展现青春风采，开展主题教育活动。',
                'event_type': 'festival',
                'start_date': date(year, 5, 4),
                'end_date': date(year, 5, 6),
                'start_time': '08:00',
                'end_time': '18:00',
                'all_day': True,
                'location': '全校范围',
                'priority': 'high',
                'status': 'published',
                'contact_person': '团委',
                'contact_phone': '010-12345679',
                'created_by': admin_user.id
            })

            # 毕业典礼
            events.append({
                'title': f'{year}届学生毕业典礼',
                'description': '祝贺毕业生顺利完成学业，踏上人生新征程。',
                'event_type': 'activity',
                'start_date': date(year, 6, 20),
                'end_date': date(year, 6, 20),
                'start_time': '14:00',
                'end_time': '17:00',
                'location': '学校体育场',
                'priority': 'high',
                'status': 'published',
                'contact_person': '教务处',
                'contact_phone': '010-12345680',
                'graduation_year': year,
                'created_by': admin_user.id
            })

            # 秋季学期开学
            events.append({
                'title': f'{year}年秋季学期开学典礼',
                'description': '新学年伊始，欢迎新生入学，开启新的学习征程。',
                'event_type': 'activity',
                'start_date': date(year, 9, 1),
                'end_date': date(year, 9, 1),
                'start_time': '08:30',
                'end_time': '11:00',
                'location': '学校大礼堂',
                'priority': 'high',
                'status': 'published',
                'contact_person': '教务处',
                'contact_phone': '010-12345678',
                'created_by': admin_user.id
            })

            # 教师节庆祝活动
            events.append({
                'title': f'{year}年教师节庆祝大会',
                'description': '尊师重教，感恩师长，表彰优秀教师和教育工作者。',
                'event_type': 'festival',
                'start_date': date(year, 9, 10),
                'end_date': date(year, 9, 10),
                'start_time': '15:00',
                'end_time': '17:30',
                'location': '学校大礼堂',
                'priority': 'medium',
                'status': 'published',
                'contact_person': '工会',
                'contact_phone': '010-12345681',
                'created_by': admin_user.id
            })

            # 校运动会
            events.append({
                'title': f'{year}年秋季田径运动会',
                'description': '增强学生体质，培养团队精神，展现体育风采。',
                'event_type': 'activity',
                'start_date': date(year, 10, 15),
                'end_date': date(year, 10, 17),
                'start_time': '08:00',
                'end_time': '17:00',
                'all_day': True,
                'location': '学校体育场',
                'priority': 'high',
                'status': 'published',
                'contact_person': '体育组',
                'contact_phone': '010-12345682',
                'created_by': admin_user.id
            })

            # 元旦联欢
            events.append({
                'title': f'{year}年元旦联欢晚会',
                'description': '欢庆新年，师生联欢，展现才艺，共度佳节。',
                'event_type': 'festival',
                'start_date': date(year, 12, 31),
                'end_date': date(year + 1, 1, 1),
                'start_time': '19:00',
                'end_time': '22:00',
                'location': '学校大礼堂',
                'priority': 'medium',
                'status': 'published',
                'contact_person': '学生会',
                'contact_phone': '010-12345683',
                'created_by': admin_user.id
            })

        # 3. 周年返校活动（针对不同毕业年份）
        graduation_years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
        for year in graduation_years:
            anniversary = current_year - year
            if anniversary in [5, 10, 15, 20, 25, 30, 40]:  # 重要的周年纪念
                events.append({
                    'title': f'{year}届校友毕业{anniversary}周年返校日活动',
                    'description': f'欢迎{year}届校友返校，畅叙师生情谊，共话校园发展。',
                    'event_type': 'anniversary',
                    'start_date': date(current_year, 5, 3),  # 校庆前一天
                    'end_date': date(current_year, 5, 5),
                    'start_time': '09:00',
                    'end_time': '18:00',
                    'all_day': True,
                    'location': '学校校园',
                    'priority': 'high',
                    'status': 'published',
                    'contact_person': '校友会',
                    'contact_phone': '010-12345684',
                    'contact_email': 'alumni@school.edu.cn',
                    'target_graduation_years': str(year),
                    'graduation_year': year,
                    'anniversary_year': anniversary,
                    'created_by': admin_user.id
                })

        # 4. 社团活动（定期举行）
        club_types = ['学术', '文艺', '体育', '公益', '科技']
        for year in range(current_year, current_year + 2):
            for month in [3, 4, 9, 10, 11]:  # 学期中的月份
                for club_type in club_types:
                    # 每月每个类型的社团活动
                    day = random.randint(1, 28)
                    events.append({
                        'title': f'{year}年{month}月{club_type}社团展示活动',
                        'description': f'展示{club_type}社团风采，丰富校园文化生活。',
                        'event_type': 'club',
                        'start_date': date(year, month, day),
                        'end_date': date(year, month, day),
                        'start_time': '14:00',
                        'end_time': '17:00',
                        'location': '学生活动中心',
                        'priority': 'medium',
                        'status': 'published',
                        'contact_person': '社团联合会',
                        'contact_phone': '010-12345685',
                        'club_name': f'{club_type}类社团联合',
                        'club_type': club_type.lower(),
                        'created_by': admin_user.id
                    })

        # 5. 考试安排
        for year in range(current_year, current_year + 2):
            # 期中考试
            events.append({
                'title': f'{year}年春季学期期中考试',
                'description': '期中教学质量检测，检验学生学习成果。',
                'event_type': 'exam',
                'start_date': date(year, 4, 15),
                'end_date': date(year, 4, 19),
                'start_time': '08:00',
                'end_time': '17:00',
                'all_day': True,
                'location': '各教学楼考场',
                'priority': 'high',
                'status': 'published',
                'contact_person': '教务处',
                'contact_phone': '010-12345678',
                'created_by': admin_user.id
            })

            # 期末考试
            events.append({
                'title': f'{year}年春季学期期末考试',
                'description': '学期末综合性考核，全面评价学生学习情况。',
                'event_type': 'exam',
                'start_date': date(year, 6, 25),
                'end_date': date(year, 7, 5),
                'start_time': '08:00',
                'end_time': '17:00',
                'all_day': True,
                'location': '各教学楼考场',
                'priority': 'high',
                'status': 'published',
                'contact_person': '教务处',
                'contact_phone': '010-12345678',
                'created_by': admin_user.id
            })

            # 秋季期中考试
            events.append({
                'title': f'{year}年秋季学期期中考试',
                'description': '期中教学质量检测，检验学习效果。',
                'event_type': 'exam',
                'start_date': date(year, 11, 10),
                'end_date': date(year, 11, 15),
                'start_time': '08:00',
                'end_time': '17:00',
                'all_day': True,
                'location': '各教学楼考场',
                'priority': 'high',
                'status': 'published',
                'contact_person': '教务处',
                'contact_phone': '010-12345678',
                'created_by': admin_user.id
            })

        # 6. 会议和讲座
        for year in range(current_year, current_year + 2):
            # 家长会
            events.append({
                'title': f'{year}年春季学期家长会',
                'description': '家校合作，共育英才，汇报学校教育成果。',
                'event_type': 'meeting',
                'start_date': date(year, 3, 20),
                'end_date': date(year, 3, 20),
                'start_time': '14:00',
                'end_time': '17:00',
                'location': '学校大礼堂',
                'priority': 'medium',
                'status': 'published',
                'contact_person': '德育处',
                'contact_phone': '010-12345686',
                'created_by': admin_user.id
            })

            # 学术讲座
            for month in [4, 5, 10, 11]:
                day = random.randint(1, 28)
                events.append({
                    'title': f'{year}年{month}月专家学术讲座',
                    'description': '邀请专家学者进行学术交流，拓宽师生视野。',
                    'event_type': 'meeting',
                    'start_date': date(year, month, day),
                    'end_date': date(year, month, day),
                    'start_time': '15:00',
                    'end_time': '17:00',
                    'location': '学术报告厅',
                    'priority': 'medium',
                    'status': 'published',
                    'contact_person': '教科室',
                    'contact_phone': '010-12345687',
                    'created_by': admin_user.id
                })

        # 7. 假期安排
        for year in range(current_year, current_year + 2):
            # 寒假
            events.append({
                'title': f'{year}年寒假放假安排',
                'description': '寒假期间学生放假，注意安全，合理安排学习和生活。',
                'event_type': 'holiday',
                'start_date': date(year, 1, 15),
                'end_date': date(year, 2, 25),
                'all_day': True,
                'priority': 'medium',
                'status': 'published',
                'contact_person': '教务处',
                'contact_phone': '010-12345678',
                'created_by': admin_user.id
            })

            # 暑假
            events.append({
                'title': f'{year}年暑假放假安排',
                'description': '暑假期间学生放假，注意安全，参与社会实践和志愿服务。',
                'event_type': 'holiday',
                'start_date': date(year, 7, 10),
                'end_date': date(year, 8, 31),
                'all_day': True,
                'priority': 'medium',
                'status': 'published',
                'contact_person': '教务处',
                'contact_phone': '010-12345678',
                'created_by': admin_user.id
            })

        # 创建事件记录
        created_events = []
        for event_data in events:
            try:
                # 转换时间字符串为时间对象
                if 'start_time' in event_data and event_data['start_time']:
                    from datetime import time
                    hour, minute = map(int, event_data['start_time'].split(':'))
                    event_data['start_time'] = time(hour, minute)

                if 'end_time' in event_data and event_data['end_time']:
                    from datetime import time
                    hour, minute = map(int, event_data['end_time'].split(':'))
                    event_data['end_time'] = time(hour, minute)

                event = SchoolCalendar(**event_data)

                # 如果状态是发布，设置发布时间
                if event.status == 'published':
                    event.published_at = datetime.now()

                db.session.add(event)
                created_events.append(event)

            except Exception as e:
                print(f"创建事件失败: {event_data.get('title', 'Unknown')} - {str(e)}")

        # 提交到数据库
        try:
            db.session.commit()
            print(f"成功创建 {len(created_events)} 个校历事件")

            # 统计信息
            stats = {
                '总事件数': len(created_events),
                '校庆活动': len([e for e in created_events if e.event_type == 'anniversary']),
                '节庆活动': len([e for e in created_events if e.event_type == 'festival']),
                '校园活动': len([e for e in created_events if e.event_type == 'activity']),
                '社团活动': len([e for e in created_events if e.event_type == 'club']),
                '会议讲座': len([e for e in created_events if e.event_type == 'meeting']),
                '假期安排': len([e for e in created_events if e.event_type == 'holiday']),
                '考试安排': len([e for e in created_events if e.event_type == 'exam']),
            }

            print("\n校历事件统计:")
            for key, value in stats.items():
                print(f"  {key}: {value} 个")

            print("\n重要活动日期:")
            important_events = [e for e in created_events if e.priority == 'high']
            for event in sorted(important_events, key=lambda x: x.start_date)[:10]:
                print(f"  {event.start_date}: {event.title}")

        except Exception as e:
            db.session.rollback()
            print(f"数据库提交失败: {str(e)}")

if __name__ == '__main__':
    create_school_calendar_data()