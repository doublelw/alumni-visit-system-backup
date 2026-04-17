"""
高级统计分析API - Excel导出扩展
"""

import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from flask import send_file
from sqlalchemy import func
from app import db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from app.models.visit_record import VisitRecord


def export_statistics_excel(stat_type, start_date, end_date, group_by, time_range):
    """导出统计数据为Excel文件"""

    # 根据统计类型生成Excel
    if stat_type == 'leaves':
        excel_data, filename = _generate_leave_excel(start_date, end_date, group_by, time_range)
    elif stat_type == 'alumni':
        excel_data, filename = _generate_alumni_excel(start_date, end_date, group_by, time_range)
    elif stat_type == 'visits':
        excel_data, filename = _generate_visit_excel(start_date, end_date, group_by, time_range)
    else:
        raise ValueError('Invalid statistics type')

    return excel_data, filename


def _generate_leave_excel(start_date, end_date, group_by, time_range):
    """生成学生请假统计Excel"""
    # 查询数据
    query = StudentExitApplication.query.filter(
        StudentExitApplication.application_status == 'approved',
        func.date(StudentExitApplication.exit_date) >= start_date,
        func.date(StudentExitApplication.exit_date) <= end_date
    )

    leaves = query.all()

    # 准备数据
    data_rows = []
    for leave in leaves:
        student = User.query.get(leave.student_id)
        if student:
            data_rows.append({
                '学生姓名': student.real_name,
                '学号': student.student_id or '',
                '年级': student.grade or '',
                '班级': student.class_id or '',
                '离校日期': str(leave.exit_date),
                '离校时间': str(leave.exit_time_start) if leave.exit_time_start else '',
                '返校时间': str(leave.exit_time_end) if leave.exit_time_end else '',
                '离校原因': leave.exit_reason or '',
                '目的地': leave.destination or '',
                '交通方式': leave.transport_method or '',
                '申请时间': str(leave.created_at),
                '审批时间': str(leave.teacher_approval_time) if leave.teacher_approval_time else '',
                '状态': leave.application_status
            })

    # 创建分组统计
    stats_data = []
    if group_by == 'class':
        stats = {}
        for leave in leaves:
            student = User.query.get(leave.student_id)
            if student and student.class_id:
                class_name = f"{student.grade or ''}{student.class_id or ''}"
                if class_name not in stats:
                    stats[class_name] = {'count': 0, 'students': set()}
                stats[class_name]['count'] += 1
                stats[class_name]['students'].add(leave.student_id)

        stats_data = [{
            '班级': k,
            '请假次数': v['count'],
            '请假人数': len(v['students'])
        } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

    elif group_by == 'grade':
        stats = {}
        for leave in leaves:
            student = User.query.get(leave.student_id)
            if student and student.grade:
                grade = student.grade
                if grade not in stats:
                    stats[grade] = {'count': 0, 'students': set()}
                stats[grade]['count'] += 1
                stats[grade]['students'].add(leave.student_id)

        stats_data = [{
            '年级': k,
            '请假次数': v['count'],
            '请假人数': len(v['students'])
        } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

    elif group_by == 'student':
        stats = {}
        for leave in leaves:
            student = User.query.get(leave.student_id)
            if student:
                key = leave.student_id
                if key not in stats:
                    stats[key] = {
                        '学生姓名': student.real_name,
                        '班级': f"{student.grade or ''}{student.class_id or ''}",
                        '请假次数': 0
                    }
                stats[key]['请假次数'] += 1

        stats_data = sorted(stats.values(), key=lambda x: x['请假次数'], reverse=True)

    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 详细数据Sheet
        df_details = pd.DataFrame(data_rows)
        df_details.to_excel(writer, sheet_name='请假明细', index=False)

        # 统计汇总Sheet
        if stats_data:
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='统计汇总', index=False)

        # 概览Sheet
        overview_data = {
            '统计项': ['统计时间范围', '开始日期', '结束日期', '总请假次数', '涉及学生数'],
            '数值': [
                f'{time_range}',
                str(start_date),
                str(end_date),
                len(leaves),
                len(set(leave.student_id for leave in leaves))
            ]
        }
        df_overview = pd.DataFrame(overview_data)
        df_overview.to_excel(writer, sheet_name='概览', index=False)

    output.seek(0)
    filename = f'学生请假统计_{start_date}_to_{end_date}.xlsx'
    return output, filename


def _generate_alumni_excel(start_date, end_date, group_by, time_range):
    """生成校友返校统计Excel"""
    # 查询数据
    query = VisitRecord.query.filter(
        VisitRecord.visitor_type == 'alumni',
        func.date(VisitRecord.entry_time) >= start_date,
        func.date(VisitRecord.entry_time) <= end_date
    )

    visits = query.all()

    # 准备详细数据
    data_rows = []
    for visit in visits:
        user = User.query.get(visit.user_id)
        if user and hasattr(user, 'alumni_profile') and user.alumni_profile:
            grad_year = user.alumni_profile.graduation_year if user.alumni_profile else ''
            class_name = user.alumni_profile.class_name if user.alumni_profile else ''
            data_rows.append({
                '校友姓名': user.real_name,
                '毕业年份': grad_year or '',
                '班级': class_name or '',
                '访问时间': str(visit.entry_time),
                '受访老师': visit.host_person or '',
                '访问目的': visit.visit_purpose or '',
                '访问目的地': visit.destination or '',
                '门卫': visit.guard_name or '',
                '验证方式': visit.verification_method or ''
            })

    # 创建分组统计
    stats_data = []
    if group_by == 'grade':
        stats = {}
        for visit in visits:
            user = User.query.get(visit.user_id)
            if user and hasattr(user, 'alumni_profile') and user.alumni_profile:
                grad_year = user.alumni_profile.graduation_year
                if grad_year:
                    if grad_year not in stats:
                        stats[grad_year] = {'count': 0, 'visitors': set()}
                    stats[grad_year]['count'] += 1
                    stats[grad_year]['visitors'].add(visit.user_id)

        stats_data = [{
            '毕业年份': k,
            '返校次数': v['count'],
            '返校人数': len(v['visitors'])
        } for k, v in sorted(stats.items(), key=lambda x: x[0], reverse=True)]

    elif group_by == 'student':
        stats = {}
        for visit in visits:
            user = User.query.get(visit.user_id)
            if user and hasattr(user, 'alumni_profile') and user.alumni_profile:
                key = visit.user_id
                grad_year = user.alumni_profile.graduation_year or ''
                class_name = user.alumni_profile.class_name or ''
                if key not in stats:
                    stats[key] = {
                        '校友姓名': user.real_name,
                        '毕业年份': grad_year,
                        '班级': class_name,
                        '返校次数': 0
                    }
                stats[key]['返校次数'] += 1

        stats_data = sorted(stats.values(), key=lambda x: x['返校次数'], reverse=True)

    elif group_by == 'year_segment':
        def get_year_segment(year):
            if not year:
                return '未知'
            try:
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
            except:
                return '未知'

        stats = {}
        for visit in visits:
            user = User.query.get(visit.user_id)
            if user and hasattr(user, 'alumni_profile') and user.alumni_profile:
                grad_year = user.alumni_profile.graduation_year
                if grad_year:
                    segment = get_year_segment(grad_year)
                    if segment not in stats:
                        stats[segment] = {'count': 0, 'visitors': set()}
                    stats[segment]['count'] += 1
                    stats[segment]['visitors'].add(visit.user_id)

        stats_data = [{
            '年代段': k,
            '返校次数': v['count'],
            '返校人数': len(v['visitors'])
        } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 详细数据Sheet
        df_details = pd.DataFrame(data_rows)
        df_details.to_excel(writer, sheet_name='返校明细', index=False)

        # 统计汇总Sheet
        if stats_data:
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='统计汇总', index=False)

        # 概览Sheet
        overview_data = {
            '统计项': ['统计时间范围', '开始日期', '结束日期', '总返校次数', '返校人数'],
            '数值': [
                f'{time_range}',
                str(start_date),
                str(end_date),
                len(visits),
                len(set(visit.user_id for visit in visits))
            ]
        }
        df_overview = pd.DataFrame(overview_data)
        df_overview.to_excel(writer, sheet_name='概览', index=False)

    output.seek(0)
    filename = f'校友返校统计_{start_date}_to_{end_date}.xlsx'
    return output, filename


def _generate_visit_excel(start_date, end_date, group_by, time_range):
    """生成访问记录统计Excel"""
    # 查询数据
    query = VisitRecord.query.filter(
        func.date(VisitRecord.entry_time) >= start_date,
        func.date(VisitRecord.entry_time) <= end_date
    )

    visits = query.all()

    # 准备详细数据
    data_rows = []
    for visit in visits:
        user = User.query.get(visit.user_id)
        if user:
            data_rows.append({
                '访问者': user.real_name,
                '访客类型': visit.visitor_type or '',
                '访问时间': str(visit.entry_time),
                '受访老师': visit.host_person or '',
                '访问目的': visit.visit_purpose or '',
                '访问目的地': visit.destination or '',
                '门卫': visit.guard_name or '',
                '验证方式': visit.verification_method or ''
            })

    # 创建分组统计
    stats_data = []
    if group_by == 'host':
        stats = {}
        for visit in visits:
            if visit.host_person_id and visit.host_person:
                key = visit.host_person_id
                if key not in stats:
                    stats[key] = {
                        '受访老师': visit.host_person,
                        '受访次数': 0,
                        '访客人数': 0,
                        '访客列表': set()
                    }
                stats[key]['受访次数'] += 1
                if visit.user_id:
                    stats[key]['访客列表'].add(visit.user_id)

        stats_data = [{
            '受访老师': v['受访老师'],
            '受访次数': v['受访次数'],
            '访客人数': len(v['访客列表'])
        } for k, v in sorted(stats.items(), key=lambda x: x[1]['受访次数'], reverse=True)]

    elif group_by == 'visitor_type':
        type_map = {
            'alumni': '校友',
            'parent': '家长',
            'visitor': '访客',
            'teacher': '教师',
            'student': '学生'
        }

        stats = {}
        for visit in visits:
            vtype = visit.visitor_type or '未知'
            if vtype not in stats:
                stats[vtype] = {'count': 0, 'visitors': set()}
            stats[vtype]['count'] += 1
            if visit.user_id:
                stats[vtype]['visitors'].add(visit.user_id)

        stats_data = [{
            '访客类型': type_map.get(k, k),
            '访问次数': v['count'],
            '访客人数': len(v['visitors'])
        } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

    elif group_by == 'purpose':
        stats = {}
        for visit in visits:
            purpose = visit.visit_purpose or '其他'
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

        stats_data = [{
            '访问目的': k,
            '访问次数': v['count'],
            '访客人数': len(v['visitors'])
        } for k, v in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)]

    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 详细数据Sheet
        df_details = pd.DataFrame(data_rows)
        df_details.to_excel(writer, sheet_name='访问明细', index=False)

        # 统计汇总Sheet
        if stats_data:
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='统计汇总', index=False)

        # 概览Sheet
        overview_data = {
            '统计项': ['统计时间范围', '开始日期', '结束日期', '总访问次数', '访客人数'],
            '数值': [
                f'{time_range}',
                str(start_date),
                str(end_date),
                len(visits),
                len(set(visit.user_id for visit in visits if visit.user_id))
            ]
        }
        df_overview = pd.DataFrame(overview_data)
        df_overview.to_excel(writer, sheet_name='概览', index=False)

    output.seek(0)
    filename = f'访问记录统计_{start_date}_to_{end_date}.xlsx'
    return output, filename
