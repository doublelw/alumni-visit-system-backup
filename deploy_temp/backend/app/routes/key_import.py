"""
公钥导入API（内网服务器）

提供公钥数据导入功能，从外网导出的Excel文件导入
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from datetime import datetime
import pandas as pd
from io import BytesIO

from backend.app.models.user import User
from backend.app import db

key_import_bp = Blueprint('key_import', __name__)


def admin_required(f):
    """管理员权限验证"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 这里应该验证管理员权限
        # 暂时跳过
        return f(*args, **kwargs)
    return decorated_function


@key_import_bp.route('/import/keys', methods=['POST'])
@admin_required
def import_public_keys():
    """
    导入公钥数据（Excel文件）

    请求:
        file: Excel文件（multipart/form-data）
        update_existing: 是否更新已存在的密钥（true/false，默认false）
        create_missing: 是否为缺失的用户创建记录（true/false，默认false）

    返回:
    {
        "success": true,
        "data": {
            "total_rows": 100,
            "imported": 95,
            "updated": 3,
            "skipped": 2,
            "failed": 0,
            "details": [
                {
                    "row": 2,
                    "phone": "13800138000",
                    "real_name": "张三",
                    "status": "imported",
                    "message": "导入成功"
                },
                ...
            ]
        }
    }
    """
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': '只支持Excel文件（.xlsx, .xls）'}), 400

        # 获取选项
        update_existing = request.form.get('update_existing', 'false').lower() == 'true'
        create_missing = request.form.get('create_missing', 'false').lower() == 'true'

        # 读取Excel文件
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'读取Excel文件失败: {str(e)}'}), 400

        # 验证必需的列
        required_columns = ['手机号', '公钥（Base64）', 'PIN哈希（SHA256）']
        missing_columns = [col for col in required_columns if col not in df.columns]

        # 尝试使用英文字段名
        if missing_columns:
            english_mapping = {
                '手机号': 'phone',
                '公钥（Base64）': 'public_key',
                'PIN哈希（SHA256）': 'pin_hash',
                '姓名': 'real_name',
                '用户ID': 'user_id',
                '用户类型': 'user_type',
                '学号': 'student_no',
                '工号': 'employee_no',
                '密钥版本': 'key_version',
                '密钥创建时间': 'key_created_at',
                '密钥过期时间': 'key_expires_at'
            }

            # 重命名列为英文字段名
            df_renamed = df.rename(columns=english_mapping)
            missing_columns = [col for col in ['phone', 'public_key', 'pin_hash']
                             if col not in df_renamed.columns]

            if missing_columns:
                return jsonify({
                    'error': f'Excel文件缺少必需的列: {", ".join(missing_columns)}',
                    'required_columns': ['手机号', '公钥（Base64）', 'PIN哈希（SHA256）']
                }), 400

            df = df_renamed

        # 处理NaN值
        df = df.fillna('')

        total_rows = len(df)
        imported = 0
        updated = 0
        skipped = 0
        failed = 0
        details = []

        # 逐行处理
        for index, row in df.iterrows():
            row_num = index + 2  # Excel行号（从1开始，加上标题行）

            try:
                phone = str(row['phone']).strip()
                public_key = str(row['public_key']).strip()
                pin_hash = str(row['pin_hash']).strip()

                # 验证必需字段
                if not phone or not public_key or not pin_hash:
                    details.append({
                        'row': row_num,
                        'phone': phone,
                        'status': 'failed',
                        'message': '缺少必需字段（手机号/公钥/PIN哈希）'
                    })
                    failed += 1
                    continue

                # 查找用户
                user = User.query.filter_by(phone=phone).first()

                if user:
                    # 用户存在
                    if user.public_key and not update_existing:
                        # 已有公钥且不更新
                        details.append({
                            'row': row_num,
                            'phone': phone,
                            'real_name': user.real_name,
                            'status': 'skipped',
                            'message': '用户已有公钥，跳过'
                        })
                        skipped += 1
                        continue

                    # 更新公钥
                    user.public_key = public_key
                    user.pin_hash = pin_hash
                    user.key_version = int(row.get('key_version', 1))
                    user.key_imported_at = datetime.utcnow()

                    # 解析过期时间
                    expires_at_str = row.get('key_expires_at', '')
                    if expires_at_str:
                        try:
                            if isinstance(expires_at_str, str):
                                user.key_expires_at = datetime.strptime(
                                    expires_at_str,
                                    '%Y-%m-%d %H:%M:%S'
                                )
                        except:
                            pass

                    db.session.commit()

                    details.append({
                        'row': row_num,
                        'phone': phone,
                        'real_name': user.real_name,
                        'status': 'updated',
                        'message': '更新公钥成功'
                    })
                    updated += 1

                else:
                    # 用户不存在
                    if create_missing:
                        # 创建新用户
                        user = User(
                            real_name=str(row.get('real_name', '未知')).strip(),
                            phone=phone,
                            user_type=str(row.get('user_type', 'alumni')).strip(),
                            student_no=str(row.get('student_no', '')).strip() or None,
                            employee_no=str(row.get('employee_no', '')).strip() or None,
                            public_key=public_key,
                            pin_hash=pin_hash,
                            key_version=int(row.get('key_version', 1)),
                            key_imported_at=datetime.utcnow()
                        )

                        # 解析过期时间
                        expires_at_str = row.get('key_expires_at', '')
                        if expires_at_str:
                            try:
                                if isinstance(expires_at_str, str):
                                    user.key_expires_at = datetime.strptime(
                                        expires_at_str,
                                        '%Y-%m-%d %H:%M:%S'
                                    )
                            except:
                                pass

                        db.session.add(user)
                        db.session.commit()

                        details.append({
                            'row': row_num,
                            'phone': phone,
                            'real_name': user.real_name,
                            'status': 'imported',
                            'message': '创建新用户并导入公钥'
                        })
                        imported += 1

                    else:
                        # 不创建，跳过
                        details.append({
                            'row': row_num,
                            'phone': phone,
                            'status': 'skipped',
                            'message': '用户不存在，跳过（未启用创建缺失用户）'
                        })
                        skipped += 1

            except Exception as e:
                db.session.rollback()
                details.append({
                    'row': row_num,
                    'phone': row.get('phone', ''),
                    'status': 'failed',
                    'message': f'处理失败: {str(e)}'
                })
                failed += 1

        return jsonify({
            'success': True,
            'data': {
                'total_rows': total_rows,
                'imported': imported,
                'updated': updated,
                'skipped': skipped,
                'failed': failed,
                'details': details
            }
        })

    except Exception as e:
        current_app.logger.error(f"导入公钥失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '导入公钥失败', 'details': str(e)}), 500


@key_import_bp.route('/import/keys/validate', methods=['POST'])
@admin_required
def validate_import_file():
    """
    验证导入文件（不实际导入，只检查格式）

    请求:
        file: Excel文件（multipart/form-data）

    返回:
    {
        "success": true,
        "data": {
            "valid": true,
            "total_rows": 100,
            "valid_rows": 95,
            "invalid_rows": 5,
            "columns": ["手机号", "公钥（Base64）", ...],
            "sample_data": [...],
            "warnings": [...]
        }
    }
    """
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        # 读取Excel文件
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({
                'success': False,
                'data': {
                    'valid': False,
                    'error': f'读取Excel文件失败: {str(e)}'
                }
            })

        total_rows = len(df)

        # 检查列
        columns = df.columns.tolist()
        warnings = []

        # 检查必需列
        required_columns_cn = ['手机号', '公钥（Base64）', 'PIN哈希（SHA256）']
        required_columns_en = ['phone', 'public_key', 'pin_hash']

        has_cn_columns = all(col in columns for col in required_columns_cn)
        has_en_columns = all(col in columns for col in required_columns_en)

        if not has_cn_columns and not has_en_columns:
            return jsonify({
                'success': True,
                'data': {
                    'valid': False,
                    'total_rows': total_rows,
                    'columns': columns,
                    'error': 'Excel文件缺少必需的列',
                    'required_columns_cn': required_columns_cn,
                    'required_columns_en': required_columns_en
                }
            })

        # 选择使用的列
        if has_cn_columns:
            key_columns = required_columns_cn
        else:
            key_columns = required_columns_en

        # 验证数据
        valid_rows = 0
        invalid_rows = 0
        sample_data = []

        for index, row in df.head(10).iterrows():  # 只检查前10行
            try:
                if has_cn_columns:
                    phone = str(row['手机号']).strip()
                    public_key = str(row['公钥（Base64）']).strip()
                    pin_hash = str(row['PIN哈希（SHA256）']).strip()
                else:
                    phone = str(row['phone']).strip()
                    public_key = str(row['public_key']).strip()
                    pin_hash = str(row['pin_hash']).strip()

                if phone and public_key and pin_hash:
                    valid_rows += 1
                    sample_data.append({
                        'phone': phone,
                        'has_public_key': len(public_key) > 0,
                        'has_pin_hash': len(pin_hash) > 0
                    })
                else:
                    invalid_rows += 1
            except:
                invalid_rows += 1

        # 生成警告
        if invalid_rows > 0:
            warnings.append(f'前10行中有{invalid_rows}行数据不完整')

        return jsonify({
            'success': True,
            'data': {
                'valid': True,
                'total_rows': total_rows,
                'valid_rows': valid_rows,
                'invalid_rows': invalid_rows,
                'columns': columns,
                'key_columns': key_columns,
                'sample_data': sample_data,
                'warnings': warnings
            }
        })

    except Exception as e:
        current_app.logger.error(f"验证导入文件失败: {str(e)}")
        return jsonify({'error': '验证导入文件失败', 'details': str(e)}), 500


@key_import_bp.route('/import/stats', methods=['GET'])
@admin_required
def import_statistics():
    """
    导入统计信息

    返回:
    {
        "success": true,
        "data": {
            "total_personnel": 1000,
            "personnel_with_keys": 800,
            "personnel_without_keys": 200,
            "last_import": "2026-03-27 12:00:00",
            "keys_expiring_soon": 50,
            "keys_expired": 10
        }
    }
    """
    try:
        total_personnel = User.query.count()
        personnel_with_keys = User.query.filter(User.public_key.isnot(None)).count()
        personnel_without_keys = total_personnel - personnel_with_keys

        # 最后导入时间
        last_import_user = User.query.filter(
            User.key_imported_at.isnot(None)
        ).order_by(User.key_imported_at.desc()).first()

        last_import = last_import_user.key_imported_at if last_import_user else None

        # 密钥过期统计
        from datetime import timedelta
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
                'total_personnel': total_personnel,
                'personnel_with_keys': personnel_with_keys,
                'personnel_without_keys': personnel_without_keys,
                'last_import': last_import.strftime('%Y-%m-%d %H:%M:%S') if last_import else None,
                'keys_expiring_soon': keys_expiring_soon,
                'keys_expired': keys_expired
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取导入统计失败: {str(e)}")
        return jsonify({'error': '获取导入统计失败', 'details': str(e)}), 500
