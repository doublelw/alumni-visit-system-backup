#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
学生请假统计路由
提供多维度的请假数据统计和查询
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.student_leave import StudentLeaveApplication
from app.models.alumni_profile import AlumniProfile
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

# 创建蓝图
student_leave_statistics_bp = Blueprint('student_leave_statistics', __name__)


@student_leave_statistics_bp.route('/teacher/leave-statistics', methods=['GET'])
@jwt_required()
def get_leave_statistics():
    """
    获取学生请假统计数据
    参数：
    - time_range: today/week/month（默认today）
    - grade: 年级筛选（可选）
    - class_name: 班级筛选（可选）
    """
    try:
        current_user_id = get_jwt_identity()
        teacher = User.query.get(current_user_id)

        if not teacher or teacher.user_type != 'teacher':
            return jsonify({'success': False, 'error': '无权访问'}), 403

        # 获取筛选参数
        time_range = request.args.get('time_range', 'today')
        grade = request.args.get('grade', '')
        class_name = request.args.get('class_name', '')

        # 计算时间范围
        now = datetime.now()
        if time_range == 'today':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'week':
            start_time = now - timedelta(days=now.weekday())
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'month':
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 构建查询条件
        conditions = [StudentLeave.created_at >= start_time]

        if grade:
            conditions.append(StudentLeave.grade == grade)
        if class_name:
            conditions.append(StudentLeave.class_name == class_name)

        # 核心指标统计
        total_leaves = StudentLeaveApplication.query.filter(*conditions).count()

        pending_leaves = StudentLeaveApplication.query.filter(
            *conditions,
            StudentLeaveApplication.status == 'pending'
        ).count()

        approved_leaves = StudentLeaveApplication.query.filter(
            *conditions,
            StudentLeaveApplication.status == 'approved'
        ).count()

        used_leaves = StudentLeaveApplication.query.filter(
            *conditions,
            StudentLeaveApplication.status == 'used'
        ).count()

        expired_leaves = StudentLeaveApplication.query.filter(
            *conditions,
            StudentLeaveApplication.status == 'expired'
        ).count()

        # 按年级统计
        grade_stats = db.session.query(
            StudentLeaveApplication.grade,
            func.count(StudentLeaveApplication.id).label('count')
        ).filter(
            *conditions,
            StudentLeaveApplication.grade.isnot(None)
        ).group_by(StudentLeaveApplication.grade).all()

        grade_list = []
        for grade_name, count in grade_stats:
            grade_list.append({
                'grade': grade_name,
                'count': count
            })

        # 按年级排序
        grade_list.sort(key=lambda x: x['count'], reverse=True)

        # 按班级统计
        class_stats = db.session.query(
            StudentLeaveApplication.grade,
            StudentLeaveApplication.class_name,
            func.count(StudentLeaveApplication.id).label('count')
        ).filter(
            *conditions,
            StudentLeaveApplication.class_name.isnot(None)
        ).group_by(
            StudentLeaveApplication.grade,
            StudentLeaveApplication.class_name
        ).all()

        class_list = []
        for grade_name, class_name_value, count in class_stats:
            class_list.append({
                'grade': grade_name,
                'class_name': class_name_value,
                'count': count,
                'full_name': f"{grade_name} {class_name_value}"
            })

        # 按班级排序
        class_list.sort(key=lambda x: x['count'], reverse=True)

        # 按原因统计
        reason_stats = db.session.query(
            StudentLeaveApplication.leave_type,
            func.count(StudentLeaveApplication.id).label('count')
        ).filter(*conditions).group_by(
            StudentLeaveApplication.leave_type
        ).all()

        reason_list = []
        for reason, count in reason_stats:
            reason_list.append({
                'reason': reason or '未填写',
                'count': count
            })

        # 近7天趋势
        trend_data = []
        for i in range(6, -1, -1):
            date = now - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

            day_count = StudentLeaveApplication.query.filter(
                StudentLeaveApplication.created_at >= day_start,
                StudentLeaveApplication.created_at <= day_end
            ).count()

            trend_data.append({
                'date': date.strftime('%m-%d'),
                'count': day_count
            })

        # 异常预警（频繁请假的学生）
        abnormal_leaves = db.session.query(
            StudentLeaveApplication.student_name,
            StudentLeaveApplication.grade,
            StudentLeaveApplication.class_name,
            func.count(StudentLeaveApplication.id).label('count')
        ).filter(
            StudentLeaveApplication.created_at >= start_time - timedelta(days=30)
        ).group_by(
            StudentLeaveApplication.student_name,
            StudentLeaveApplication.grade,
            StudentLeaveApplication.class_name
        ).having(
            func.count(StudentLeaveApplication.id) >= 3
        ).all()

        abnormal_list = []
        for student_name, grade_name, class_name_value, count in abnormal_leaves:
            abnormal_list.append({
                'student_name': student_name,
                'grade': grade_name,
                'class_name': class_name_value,
                'count': count
            })

        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total': total_leaves,
                    'pending': pending_leaves,
                    'approved': approved_leaves,
                    'used': used_leaves,
                    'expired': expired_leaves
                },
                'grade_ranking': grade_list,
                'class_ranking': class_list[:20],  # 前20名
                'reason_distribution': reason_list,
                'trend': trend_data,
                'abnormal_warnings': abnormal_list
            }
        })

    except Exception as e:
        print(f"统计数据错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取统计数据失败'}), 500


@student_leave_statistics_bp.route('/teacher/statistics/grades', methods=['GET'])
@jwt_required()
def get_grades():
    """获取所有年级列表"""
    try:
        current_user_id = get_jwt_identity()
        teacher = User.query.get(current_user_id)

        if not teacher or teacher.user_type != 'teacher':
            return jsonify({'success': False, 'error': '无权访问'}), 403

        # 从学生请假记录中获取所有年级
        grades = db.session.query(StudentLeave.grade).filter(
            StudentLeave.grade.isnot(None)
        ).distinct().order_by(StudentLeave.grade).all()

        grade_list = [g[0] for g in grades if g[0]]

        return jsonify({
            'success': True,
            'data': grade_list
        })

    except Exception as e:
        print(f"获取年级列表错误: {str(e)}")
        return jsonify({'success': False, 'error': '获取年级列表失败'}), 500


@student_leave_statistics_bp.route('/teacher/statistics/classes', methods=['GET'])
@jwt_required()
def get_classes():
    """获取班级列表（可按年级筛选）"""
    try:
        current_user_id = get_jwt_identity()
        teacher = User.query.get(current_user_id)

        if not teacher or teacher.user_type != 'teacher':
            return jsonify({'success': False, 'error': '无权访问'}), 403

        grade = request.args.get('grade', '')

        # 构建查询
        query = db.session.query(
            StudentLeave.class_name
        ).filter(
            StudentLeave.class_name.isnot(None)
        )

        if grade:
            query = query.filter(StudentLeave.grade == grade)

        classes = query.distinct().order_by(StudentLeave.class_name).all()
        class_list = [c[0] for c in classes if c[0]]

        return jsonify({
            'success': True,
            'data': class_list
        })

    except Exception as e:
        print(f"获取班级列表错误: {str(e)}")
        return jsonify({'success': False, 'error': '获取班级列表失败'}), 500
