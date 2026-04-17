"""
密钥导出API（外网服务器）

提供公钥数据导出功能，供内网导入使用
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from functools import wraps
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

from backend.app.models.user import User
from backend.app import db

key_export_bp = Blueprint('key_export', __name__)


def admin_required(f):
    """管理员权限验证"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 这里应该验证管理员权限
        # 暂时跳过
        return f(*args, **kwargs)
    return decorated_function


@key_export_bp.route('/export/keys', methods=['GET'])
@admin_required
def export_public_keys():
    """
    导出公钥数据（Excel格式）

    参数:
        start_date: 开始日期（可选，格式：YYYY-MM-DD）
        end_date: 结束日期（可选，格式：YYYY-MM-DD）
        has_key: 是否已设置密钥（true/false，可选）
        user_type: 用户类型过滤（可选）

    返回:
        Excel文件下载
    """
    try:
        # 获取查询参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        has_key = request.args.get('has_key')
        user_type = request.args.get('user_type')

        # 构建查询
        query = User.query

        # 日期范围过滤
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                query = query.filter(User.created_at >= start_date)
            except ValueError:
                return jsonify({'error': '开始日期格式错误，应为YYYY-MM-DD'}), 400

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # 包含当天的最后一秒
                end_date = end_date + timedelta(days=1, seconds=-1)
                query = query.filter(User.created_at <= end_date)
            except ValueError:
                return jsonify({'error': '结束日期格式错误，应为YYYY-MM-DD'}), 400

        # 是否有密钥过滤
        if has_key is not None:
            if has_key.lower() == 'true':
                query = query.filter(User.private_key.isnot(None))
            elif has_key.lower() == 'false':
                query = query.filter(User.private_key.is_(None))

        # 用户类型过滤
        if user_type:
            query = query.filter(User.user_type == user_type)

        # 执行查询
        users = query.all()

        if not users:
            return jsonify({'error': '没有找到符合条件的用户'}), 404

        # 构建导出数据
        export_data = []
        for user in users:
            # 只导出有密钥的用户
            if not user.public_key or not user.pin_hash:
                continue

            export_data.append({
                'user_id': user.id,
                'real_name': user.real_name,
                'phone': user.phone,
                'user_type': user.user_type,
                'student_no': user.student_no or '',
                'employee_no': user.employee_no or '',
                'public_key': user.public_key,
                'pin_hash': user.pin_hash,
                'key_version': user.key_version or 1,
                'key_expires_at': user.key_expires_at.strftime('%Y-%m-%d %H:%M:%S') if user.key_expires_at else '',
                'key_created_at': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else ''
            })

        if not export_data:
            return jsonify({'error': '没有用户已设置密钥'}), 404

        # 创建Excel文件
        df = pd.DataFrame(export_data)

        # 重命名列为中文（方便查看）
        df_renamed = df.rename(columns={
            'user_id': '用户ID',
            'real_name': '姓名',
            'phone': '手机号',
            'user_type': '用户类型',
            'student_no': '学号',
            'employee_no': '工号',
            'public_key': '公钥（Base64）',
            'pin_hash': 'PIN哈希（SHA256）',
            'key_version': '密钥版本',
            'key_expires_at': '密钥过期时间',
            'key_created_at': '密钥创建时间'
        })

        # 调整列顺序
        columns_order = [
            '用户ID', '姓名', '手机号', '用户类型',
            '学号', '工号',
            '公钥（Base64）', 'PIN哈希（SHA256）',
            '密钥版本', '密钥创建时间', '密钥过期时间'
        ]
        df_renamed = df_renamed[columns_order]

        # 生成Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_renamed.to_excel(writer, sheet_name='公钥数据', index=False)

            # 调整列宽
            worksheet = writer.sheets['公钥数据']
            worksheet.column_dimensions['A'].width = 10  # 用户ID
            worksheet.column_dimensions['B'].width = 15  # 姓名
            worksheet.column_dimensions['C'].width = 15  # 手机号
            worksheet.column_dimensions['D'].width = 12  # 用户类型
            worksheet.column_dimensions['E'].width = 15  # 学号
            worksheet.column_dimensions['F'].width = 15  # 工号
            worksheet.column_dimensions['G'].width = 50  # 公钥
            worksheet.column_dimensions['H'].width = 70  # PIN哈希
            worksheet.column_dimensions['I'].width = 12  # 密钥版本
            worksheet.column_dimensions['J'].width = 20  # 创建时间
            worksheet.column_dimensions['K'].width = 20  # 过期时间

        output.seek(0)

        # 生成文件名
        filename = f"公钥数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"导出公钥失败: {str(e)}")
        return jsonify({'error': '导出公钥失败', 'details': str(e)}), 500


@key_export_bp.route('/export/keys/preview', methods=['GET'])
@admin_required
def preview_export():
    """
    预览导出数据（不下载，只返回数量）

    返回:
    {
        "success": true,
        "data": {
            "total_users": 1000,
            "users_with_keys": 800,
            "filtered_users": 50,
            "date_range": {
                "start": "2026-03-01",
                "end": "2026-03-27"
            }
        }
    }
    """
    try:
        # 获取查询参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        has_key = request.args.get('has_key')
        user_type = request.args.get('user_type')

        # 构建查询
        query = User.query
        total_users = query.count()

        # 应用过滤
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(User.created_at >= start_date)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date + timedelta(days=1, seconds=-1)
            query = query.filter(User.created_at <= end_date)

        if has_key is not None:
            if has_key.lower() == 'true':
                query = query.filter(User.private_key.isnot(None))
            elif has_key.lower() == 'false':
                query = query.filter(User.private_key.is_(None))

        if user_type:
            query = query.filter(User.user_type == user_type)

        filtered_users = query.count()
        users_with_keys = query.filter(User.private_key.isnot(None)).count()

        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'users_with_keys': users_with_keys,
                'filtered_users': filtered_users,
                'filters': {
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'has_key': has_key,
                    'user_type': user_type
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"预览导出数据失败: {str(e)}")
        return jsonify({'error': '预览导出数据失败', 'details': str(e)}), 500


@key_export_bp.route('/export/stats', methods=['GET'])
@admin_required
def export_statistics():
    """
    导出统计信息

    返回:
    {
        "success": true,
        "data": {
            "total_users": 1000,
            "users_with_keys": 800,
            "users_without_keys": 200,
            "by_type": {
                "student": 600,
                "teacher": 150,
                "alumni": 200,
                "parent": 50
            },
            "keys_expiring_soon": 50,  # 7天内过期
            "keys_expired": 10
        }
    }
    """
    try:
        total_users = User.query.count()
        users_with_keys = User.query.filter(User.private_key.isnot(None)).count()
        users_without_keys = total_users - users_with_keys

        # 按类型统计
        by_type = {}
        for user_type in ['student', 'teacher', 'alumni', 'parent']:
            count = User.query.filter_by(
                user_type=user_type
            ).filter(User.private_key.isnot(None)).count()
            by_type[user_type] = count

        # 密钥过期统计
        seven_days_later = datetime.utcnow() + timedelta(days=7)
        keys_expiring_soon = User.query.filter(
            User.key_expires_at.isnot(None),
            User.key_expires_at <= seven_days_later,
            User.key_expires_at > datetime.utcnow()
        ).count()

        keys_expired = User.query.filter(
            User.key_expires_at.isnot(None),
            User.key_expires_at < datetime.utcnow()
        ).count()

        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'users_with_keys': users_with_keys,
                'users_without_keys': users_without_keys,
                'by_type': by_type,
                'keys_expiring_soon': keys_expiring_soon,
                'keys_expired': keys_expired
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取导出统计失败: {str(e)}")
        return jsonify({'error': '获取导出统计失败', 'details': str(e)}), 500
