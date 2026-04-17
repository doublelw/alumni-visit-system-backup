"""
高级统计分析API
提供多维度的数据统计功能
"""

from flask import Blueprint, request, jsonify, send_file, send_file
from sqlalchemy import func, and_, or_, case
from app import db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from app.models.visit_record import VisitRecord
from app.models.visit_application import VisitApplication
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

statistics_bp = Blueprint('statistics', __name__)


@statistics_bp.route('/overview', methods=['GET'])
def get_overview_statistics():
    """获取概览统计数据"""
    try:
        # 基础统计
        total_students = User.query.filter_by(user_type='student').count()
        total_alumni = User.query.filter_by(user_type='alumni').count()
        total_teachers = User.query.filter_by(user_type='teacher').count()

        # 今日统计
        today = datetime.now().date()
        today_visits = VisitRecord.query.filter(
            func.date(VisitRecord.entry_time) == today
        ).count()

        today_leaves = StudentExitApplication.query.filter(
            func.date(StudentExitApplication.created_at) == today,
            StudentExitApplication.application_status == 'approved'
        ).count()

        return jsonify({
            'total_students': total_students,
            'total_alumni': total_alumni,
            'total_teachers': total_teachers,
            'today_visits': today_visits,
            'today_leaves': today_leaves
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@statistics_bp.route('/student-leaves', methods=['GET'])
def get_student_leave_statistics():
    """学生请假统计

    参数:
    - time_range: today, week, month, custom
    - start_date: 自定义开始日期
    - end_date: 自定义结束日期
    - group_by: class, grade, student (分组维度)
    """
    try:
        time_range = request.args.get('time_range', 'week')
        group_by = request.args.get('group_by', 'class')

        # 确定日期范围
        end_date = datetime.now().date()
        if time_range == 'today':
            start_date = end_date
        elif time_range == 'week':
            start_date = end_date - timedelta(days=7)
        elif time_range == 'month':
            start_date = end_date - timedelta(days=30)
        else:  # custom
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()

        # 查询已批准的请假申请
        query = StudentExitApplication.query.filter(
            StudentExitApplication.application_status == 'approved',
            func.date(StudentExitApplication.exit_date) >= start_date,
            func.date(StudentExitApplication.exit_date) <= end_date
        )

        leaves = query.all()

        # 按不同维度统计
        if group_by == 'class':
            # 按班级统计
            stats = {}
            for leave in leaves:
                student = User.query.get(leave.student_id)
                if student and student.class_id:
                    class_name = f"{student.grade or ''}{student.class_id or ''}"
                    if class_name not in stats:
                        stats[class_name] = {'count': 0, 'students': set()}
                    stats[class_name]['count'] += 1
                    stats[class_name]['students'].add(leave.student_id)

            # 转换为列表并排序
            result = [{
                'class_name': k,
                'leave_count': v['count'],
                'student_count': len(v['students'])
            } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

        elif group_by == 'grade':
            # 按年级统计
            stats = {}
            for leave in leaves:
                student = User.query.get(leave.student_id)
                if student and student.grade:
                    grade = student.grade
                    if grade not in stats:
                        stats[grade] = {'count': 0, 'students': set()}
                    stats[grade]['count'] += 1
                    stats[grade]['students'].add(leave.student_id)

            result = [{
                'grade_name': k,
                'leave_count': v['count'],
                'student_count': len(v['students'])
            } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

        elif group_by == 'student':
            # 按学生统计（请假王）
            stats = {}
            for leave in leaves:
                student = User.query.get(leave.student_id)
                if student:
                    key = leave.student_id
                    if key not in stats:
                        stats[key] = {
                            'student_id': leave.student_id,
                            'student_name': student.real_name,
                            'class_name': f"{student.grade or ''}{student.class_id or ''}",
                            'count': 0
                        }
                    stats[key]['count'] += 1

            result = sorted(stats.values(), key=lambda x: x['count'], reverse=True)[:20]  # 取前20名

        return jsonify({
            'time_range': time_range,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'group_by': group_by,
            'data': result
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@statistics_bp.route('/alumni-visits', methods=['GET'])
def get_alumni_visit_statistics():
    """校友返校统计

    参数:
    - time_range: today, week, month, custom
    - start_date: 自定义开始日期
    - end_date: 自定义结束日期
    - group_by: grade, student, year_segment (分组维度)
    """
    try:
        time_range = request.args.get('time_range', 'month')
        group_by = request.args.get('group_by', 'grade')

        # 确定日期范围
        end_date = datetime.now().date()
        if time_range == 'today':
            start_date = end_date
        elif time_range == 'week':
            start_date = end_date - timedelta(days=7)
        elif time_range == 'month':
            start_date = end_date - timedelta(days=30)
        else:  # custom
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()

        # 查询校友访问记录
        query = VisitRecord.query.filter(
            VisitRecord.visitor_type == 'alumni',
            func.date(VisitRecord.entry_time) >= start_date,
            func.date(VisitRecord.entry_time) <= end_date
        )

        visits = query.all()

        # 按不同维度统计
        if group_by == 'grade':
            # 按毕业年级统计
            stats = {}
            for visit in visits:
                user = User.query.get(visit.user_id)
                if user and user.alumni_profile and user.alumni_profile.graduation_year:
                    year = user.alumni_profile.graduation_year
                    if year not in stats:
                        stats[year] = {'count': 0, 'visitors': set()}
                    stats[year]['count'] += 1
                    stats[year]['visitors'].add(visit.user_id)

            result = [{
                'graduation_year': k,
                'visit_count': v['count'],
                'visitor_count': len(v['visitors'])
            } for k, v in sorted(stats.items(), key=lambda x: x[0], reverse=True)]

        elif group_by == 'student':
            # 按校友个人统计（返校次数排名）
            stats = {}
            for visit in visits:
                user = User.query.get(visit.user_id)
                if user and user.alumni_profile:
                    key = visit.user_id
                    if key not in stats:
                        grad_year = user.alumni_profile.graduation_year or ''
                        class_name = user.alumni_profile.class_name or ''
                        stats[key] = {
                            'user_id': visit.user_id,
                            'alumni_name': user.real_name,
                            'graduation_year': grad_year,
                            'class_name': class_name,
                            'visit_count': 0
                        }
                    stats[key]['visit_count'] += 1

            result = sorted(stats.values(), key=lambda x: x['visit_count'], reverse=True)[:30]  # 取前30名

        elif group_by == 'year_segment':
            # 按年代段统计（90年代、00年代、10年代、20年代）
            def get_year_segment(year):
                if not year:
                    return '未知'
                year_int = int(year)
                if 1990 <= year_int <= 1999:
                    return '90年代'
                elif 2000 <= year_int <= 2009:
                    return '00年代'
                elif 2010 <= year_int <= 2019:
                    return '10年代'
                elif 2020 <= year_int <= 2029:
                    return '20年代'
                else:
                    return f'{year_int}年代'

            stats = {}
            for visit in visits:
                user = User.query.get(visit.user_id)
                if user and user.alumni_profile and user.alumni_profile.graduation_year:
                    segment = get_year_segment(user.alumni_profile.graduation_year)
                    if segment not in stats:
                        stats[segment] = {'count': 0, 'visitors': set()}
                    stats[segment]['count'] += 1
                    stats[segment]['visitors'].add(visit.user_id)

            result = [{
                'year_segment': k,
                'visit_count': v['count'],
                'visitor_count': len(v['visitors'])
            } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

        return jsonify({
            'time_range': time_range,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'group_by': group_by,
            'total_visits': len(visits),
            'data': result
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@statistics_bp.route('/visit-records', methods=['GET'])
def get_visit_record_statistics():
    """访问记录统计

    参数:
    - time_range: today, week, month, custom
    - start_date: 自定义开始日期
    - end_date: 自定义结束日期
    - group_by: host, visitor_type, purpose (分组维度)
    """
    try:
        time_range = request.args.get('time_range', 'week')
        group_by = request.args.get('group_by', 'host')

        # 确定日期范围
        end_date = datetime.now().date()
        if time_range == 'today':
            start_date = end_date
        elif time_range == 'week':
            start_date = end_date - timedelta(days=7)
        elif time_range == 'month':
            start_date = end_date - timedelta(days=30)
        else:  # custom
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()

        # 查询访问记录
        query = VisitRecord.query.filter(
            func.date(VisitRecord.entry_time) >= start_date,
            func.date(VisitRecord.entry_time) <= end_date
        )

        visits = query.all()

        # 按不同维度统计
        if group_by == 'host':
            # 按受访老师统计
            stats = {}
            for visit in visits:
                if visit.host_person_id and visit.host_person:
                    key = visit.host_person_id
                    if key not in stats:
                        stats[key] = {
                            'host_id': visit.host_person_id,
                            'host_name': visit.host_person,
                            'visit_count': 0,
                            'visitors': set()
                        }
                    stats[key]['visit_count'] += 1
                    if visit.user_id:
                        stats[key]['visitors'].add(visit.user_id)

            result = [{
                'host_id': v['host_id'],
                'host_name': v['host_name'],
                'visit_count': v['visit_count'],
                'visitor_count': len(v['visitors'])
            } for k, v in sorted(stats.items(), key=lambda x: x[1]['visit_count'], reverse=True)[:20]]

        elif group_by == 'visitor_type':
            # 按访客类型统计
            stats = {}
            for visit in visits:
                vtype = visit.visitor_type or '未知'
                if vtype not in stats:
                    stats[vtype] = {'count': 0, 'visitors': set()}
                stats[vtype]['count'] += 1
                if visit.user_id:
                    stats[vtype]['visitors'].add(visit.user_id)

            type_map = {
                'alumni': '校友',
                'parent': '家长',
                'visitor': '访客',
                'teacher': '教师',
                'student': '学生'
            }

            result = [{
                'visitor_type': k,
                'visitor_type_name': type_map.get(k, k),
                'visit_count': v['count'],
                'visitor_count': len(v['visitors'])
            } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

        elif group_by == 'purpose':
            # 按访问目的统计
            stats = {}
            for visit in visits:
                purpose = visit.visit_purpose or '其他'
                # 简化目的归类
                if '办公' in purpose or '手续' in purpose:
                    purpose_category = '办公办事'
                elif '参观' in purpose or '访问' in purpose:
                    purpose_category = '参观访问'
                elif '访友' in purpose or '老师' in purpose:
                    purpose_category = '拜访师生'
                elif '活动' in purpose or '会议' in purpose:
                    purpose_category = '参加会议'
                else:
                    purpose_category = '其他'

                if purpose_category not in stats:
                    stats[purpose_category] = {'count': 0, 'visitors': set()}
                stats[purpose_category]['count'] += 1
                if visit.user_id:
                    stats[purpose_category]['visitors'].add(visit.user_id)

            result = [{
                'purpose_category': k,
                'visit_count': v['count'],
                'visitor_count': len(v['visitors'])
            } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

        return jsonify({
            'time_range': time_range,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'group_by': group_by,
            'total_visits': len(visits),
            'data': result
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@statistics_bp.route('/trend', methods=['GET'])
def get_statistics_trend():
    """获取统计数据趋势

    参数:
    - type: leaves, visits (统计类型)
    - time_range: week, month, quarter (时间范围)
    """
    try:
        stat_type = request.args.get('type', 'visits')
        time_range = request.args.get('time_range', 'week')

        # 确定日期范围
        end_date = datetime.now().date()
        if time_range == 'week':
            days = 7
            start_date = end_date - timedelta(days=days)
        elif time_range == 'month':
            days = 30
            start_date = end_date - timedelta(days=days)
        else:  # quarter
            days = 90
            start_date = end_date - timedelta(days=days)

        # 生成日期序列
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)

        # 查询数据
        trend_data = []
        if stat_type == 'leaves':
            for date in date_list:
                count = StudentExitApplication.query.filter(
                    func.date(StudentExitApplication.exit_date) == date,
                    StudentExitApplication.application_status == 'approved'
                ).count()
                trend_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
        else:  # visits
            for date in date_list:
                count = VisitRecord.query.filter(
                    func.date(VisitRecord.entry_time) == date
                ).count()
                trend_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })

        return jsonify({
            'type': stat_type,
            'time_range': time_range,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'data': trend_data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Excel导出功能导入
from app.routes.statistics_excel import export_statistics_excel

@statistics_bp.route('/export/<stat_type>', methods=['GET'])
def export_statistics(stat_type):
    """导出统计数据为Excel文件"""
    try:
        time_range = request.args.get('time_range', 'week')
        group_by = request.args.get('group_by', 'class')
        
        # 确定日期范围
        from datetime import timedelta
        end_date = datetime.now().date()
        if time_range == 'today':
            start_date = end_date
        elif time_range == 'week':
            start_date = end_date - timedelta(days=7)
        elif time_range == 'month':
            start_date = end_date - timedelta(days=30)
        else:  # custom
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        excel_data, filename = export_statistics_excel(stat_type, start_date, end_date, group_by, time_range)
        
        return send_file(
            excel_data,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
