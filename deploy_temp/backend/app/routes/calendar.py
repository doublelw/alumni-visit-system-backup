"""
校历管理API
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from calendar import monthrange

from app import db
from app.models.school_calendar import SchoolCalendar, EventBooking
from app.models.user import User

# 公开的校历API Blueprint（不需要认证）
public_calendar_bp = Blueprint('public_calendar', __name__)

# 管理员专用的校历API Blueprint（需要认证）
calendar_bp = Blueprint('calendar', __name__)

# 尝试导入pandas，如果失败则设为None
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

# 需要导入extract函数
from sqlalchemy import extract

# 导入其他必要的模块
import os
from werkzeug.utils import secure_filename

# 公开的校历事件端点（不需要认证）
@public_calendar_bp.route('/events', methods=['GET'])
def get_public_events():
    """获取公开的校历事件列表（不需要认证）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        event_type = request.args.get('event_type', '')
        status = request.args.get('status', 'published')  # 默认只显示已发布的
        search = request.args.get('search', '')

        query = SchoolCalendar.query

        # 年份筛选
        if year:
            if month:
                # 筛选特定月份
                start_date = date(year, month, 1)
                _, last_day = monthrange(year, month)
                end_date = date(year, month, last_day)
                query = query.filter(
                    SchoolCalendar.start_date <= end_date,
                    or_(
                        SchoolCalendar.end_date >= start_date,
                        SchoolCalendar.end_date.is_(None)
                    )
                )
            else:
                # 筛选整年
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
                query = query.filter(
                    SchoolCalendar.start_date <= end_date,
                    or_(
                        SchoolCalendar.start_date >= start_date,
                        SchoolCalendar.end_date >= start_date
                    )
                )

        # 事件类型筛选
        if event_type:
            query = query.filter_by(event_type=event_type)

        # 状态筛选
        if status:
            query = query.filter_by(status=status)

        # 搜索筛选
        if search:
            query = query.filter(
                or_(
                    SchoolCalendar.title.contains(search),
                    SchoolCalendar.description.contains(search),
                    SchoolCalendar.location.contains(search),
                    SchoolCalendar.contact_person.contains(search)
                )
            )

        # 排序：即将到来的事件优先，然后按开始时间排序
        query = query.order_by(
            SchoolCalendar.start_date.asc(),
            SchoolCalendar.created_at.desc()
        )

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        events_list = [event.to_dict() for event in pagination.items]

        return jsonify({
            'events': events_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取公开校历事件列表失败: {str(e)}")
        return jsonify({'error': '获取校历事件列表失败'}), 500

# 管理员专用API（需要认证）
@calendar_bp.before_request
@jwt_required()
def admin_required():
    """管理员权限检查"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or current_user.user_type != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403

@calendar_bp.route('/events', methods=['GET'])
def get_events():
    """获取校历事件列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        event_type = request.args.get('event_type', '')
        status = request.args.get('status', '')
        search = request.args.get('search', '')

        query = SchoolCalendar.query

        # 年份筛选
        if year:
            if month:
                # 筛选特定月份
                start_date = date(year, month, 1)
                _, last_day = monthrange(year, month)
                end_date = date(year, month, last_day)
                query = query.filter(
                    SchoolCalendar.start_date <= end_date,
                    or_(
                        SchoolCalendar.end_date >= start_date,
                        SchoolCalendar.end_date.is_(None)
                    )
                )
            else:
                # 筛选整年
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
                query = query.filter(
                    SchoolCalendar.start_date <= end_date,
                    or_(
                        SchoolCalendar.end_date >= start_date,
                        SchoolCalendar.end_date.is_(None)
                    )
                )

        # 事件类型筛选
        if event_type:
            query = query.filter_by(event_type=event_type)

        # 状态筛选
        if status:
            query = query.filter_by(status=status)

        # 搜索筛选
        if search:
            query = query.filter(
                or_(
                    SchoolCalendar.title.contains(search),
                    SchoolCalendar.description.contains(search),
                    SchoolCalendar.location.contains(search),
                    SchoolCalendar.contact_person.contains(search)
                )
            )

        # 排序：即将到来的事件优先，然后按开始时间排序
        query = query.order_by(
            SchoolCalendar.start_date.asc(),
            SchoolCalendar.created_at.desc()
        )

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        events_list = [event.to_dict() for event in pagination.items]

        return jsonify({
            'events': events_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取校历事件列表失败: {str(e)}")
        return jsonify({'error': '获取校历事件列表失败'}), 500

@calendar_bp.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """获取单个校历事件详情"""
    try:
        event = SchoolCalendar.query.get(event_id)
        if not event:
            return jsonify({'error': '事件不存在'}), 404

        return jsonify({
            'event': event.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取校历事件详情失败: {str(e)}")
        return jsonify({'error': '获取校历事件详情失败'}), 500

@calendar_bp.route('/events', methods=['POST'])
def create_event():
    """创建校历事件"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['title', 'event_type', 'start_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field}不能为空'}), 400

        # 解析日期
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '开始日期格式错误'}), 400

        end_date = None
        if data.get('end_date'):
            try:
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                if end_date < start_date:
                    return jsonify({'error': '结束日期不能早于开始日期'}), 400
            except ValueError:
                return jsonify({'error': '结束日期格式错误'}), 400

        # 解析时间
        start_time = None
        end_time = None
        if data.get('start_time'):
            try:
                start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'error': '开始时间格式错误'}), 400

        if data.get('end_time'):
            try:
                end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'error': '结束时间格式错误'}), 400

        # 验证时间逻辑
        if start_time and end_time and end_time < start_time:
            return jsonify({'error': '结束时间不能早于开始时间'}), 400

        # 验证预约截止时间
        booking_deadline = None
        if data.get('booking_deadline'):
            try:
                booking_deadline = datetime.strptime(data['booking_deadline'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return jsonify({'error': '预约截止时间格式错误'}), 400

        current_user_id = int(get_jwt_identity())

        # 创建事件
        event = SchoolCalendar(
            title=data['title'],
            description=data.get('description', ''),
            event_type=data['event_type'],
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            all_day=data.get('all_day', False),
            target_audience=data.get('target_audience', 'all'),
            target_graduation_years=','.join(data.get('target_graduation_years', [])),
            target_divisions=','.join(data.get('target_divisions', [])),
            location=data.get('location', ''),
            online_url=data.get('online_url', ''),
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'draft'),
            contact_person=data.get('contact_person', ''),
            contact_phone=data.get('contact_phone', ''),
            contact_email=data.get('contact_email', ''),
            requires_booking=data.get('requires_booking', False),
            max_participants=data.get('max_participants') if data.get('max_participants') else None,
            booking_deadline=booking_deadline,
            created_by=current_user_id,
            club_name=data.get('club_name', ''),
            club_type=data.get('club_type'),
            anniversary_year=data.get('anniversary_year') if data.get('anniversary_year') else None,
            graduation_year=data.get('graduation_year') if data.get('graduation_year') else None
        )

        # 如果状态是发布，设置发布时间
        if event.status == 'published':
            event.published_at = datetime.utcnow()

        db.session.add(event)
        db.session.commit()

        return jsonify({
            'message': '校历事件创建成功',
            'event': event.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建校历事件失败: {str(e)}")
        return jsonify({'error': '创建校历事件失败'}), 500

@calendar_bp.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """更新校历事件"""
    try:
        event = SchoolCalendar.query.get(event_id)
        if not event:
            return jsonify({'error': '事件不存在'}), 404

        data = request.get_json()

        # 更新基本信息
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'event_type' in data:
            event.event_type = data['event_type']

        # 更新日期时间
        if 'start_date' in data:
            try:
                event.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '开始日期格式错误'}), 400

        if 'end_date' in data:
            if data['end_date']:
                try:
                    event.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': '结束日期格式错误'}), 400
            else:
                event.end_date = None

        if 'start_time' in data:
            if data['start_time']:
                try:
                    event.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
                except ValueError:
                    return jsonify({'error': '开始时间格式错误'}), 400
            else:
                event.start_time = None

        if 'end_time' in data:
            if data['end_time']:
                try:
                    event.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
                except ValueError:
                    return jsonify({'error': '结束时间格式错误'}), 400
            else:
                event.end_time = None

        # 更新其他字段
        if 'all_day' in data:
            event.all_day = data['all_day']
        if 'target_audience' in data:
            event.target_audience = data['target_audience']
        if 'target_graduation_years' in data:
            event.target_graduation_years = ','.join(data['target_graduation_years']) if data['target_graduation_years'] else ''
        if 'target_divisions' in data:
            event.target_divisions = ','.join(data['target_divisions']) if data['target_divisions'] else ''
        if 'location' in data:
            event.location = data['location']
        if 'online_url' in data:
            event.online_url = data['online_url']
        if 'priority' in data:
            event.priority = data['priority']
        if 'status' in data:
            old_status = event.status
            event.status = data['status']
            # 如果状态从非发布改为发布，设置发布时间
            if old_status != 'published' and data['status'] == 'published':
                event.published_at = datetime.utcnow()

        if 'contact_person' in data:
            event.contact_person = data['contact_person']
        if 'contact_phone' in data:
            event.contact_phone = data['contact_phone']
        if 'contact_email' in data:
            event.contact_email = data['contact_email']
        if 'requires_booking' in data:
            event.requires_booking = data['requires_booking']
        if 'max_participants' in data:
            event.max_participants = data['max_participants'] if data['max_participants'] else None
        if 'booking_deadline' in data:
            if data['booking_deadline']:
                try:
                    event.booking_deadline = datetime.strptime(data['booking_deadline'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return jsonify({'error': '预约截止时间格式错误'}), 400
            else:
                event.booking_deadline = None
        if 'club_name' in data:
            event.club_name = data['club_name']
        if 'club_type' in data:
            event.club_type = data['club_type']
        if 'anniversary_year' in data:
            event.anniversary_year = data['anniversary_year'] if data['anniversary_year'] else None
        if 'graduation_year' in data:
            event.graduation_year = data['graduation_year'] if data['graduation_year'] else None

        # 验证日期时间逻辑
        if event.end_date and event.end_date < event.start_date:
            return jsonify({'error': '结束日期不能早于开始日期'}), 400

        if event.start_time and event.end_time and event.end_time < event.start_time:
            return jsonify({'error': '结束时间不能早于开始时间'}), 400

        event.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': '校历事件更新成功',
            'event': event.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新校历事件失败: {str(e)}")
        return jsonify({'error': '更新校历事件失败'}), 500

@calendar_bp.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """删除校历事件"""
    try:
        event = SchoolCalendar.query.get(event_id)
        if not event:
            return jsonify({'error': '事件不存在'}), 404

        # 检查是否有预约记录
        if event.bookings.count() > 0:
            return jsonify({'error': '该事件已有预约记录，无法删除'}), 400

        db.session.delete(event)
        db.session.commit()

        return jsonify({
            'message': '校历事件删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除校历事件失败: {str(e)}")
        return jsonify({'error': '删除校历事件失败'}), 500

@calendar_bp.route('/events/<int:event_id>/publish', methods=['POST'])
def publish_event(event_id):
    """发布校历事件"""
    try:
        event = SchoolCalendar.query.get(event_id)
        if not event:
            return jsonify({'error': '事件不存在'}), 404

        if event.status == 'published':
            return jsonify({'error': '事件已经发布'}), 400

        event.status = 'published'
        event.published_at = datetime.utcnow()
        event.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '校历事件发布成功',
            'event': event.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发布校历事件失败: {str(e)}")
        return jsonify({'error': '发布校历事件失败'}), 500

@calendar_bp.route('/events/<int:event_id>/cancel', methods=['POST'])
def cancel_event(event_id):
    """取消校历事件"""
    try:
        event = SchoolCalendar.query.get(event_id)
        if not event:
            return jsonify({'error': '事件不存在'}), 404

        if event.status == 'cancelled':
            return jsonify({'error': '事件已经取消'}), 400

        if event.status == 'completed':
            return jsonify({'error': '已完成的 events cannot be cancelled'}), 400

        data = request.get_json()
        reason = data.get('reason', '')

        event.status = 'cancelled'
        event.updated_at = datetime.utcnow()
        if reason:
            event.description = f"{event.description}\n\n取消原因：{reason}"

        db.session.commit()

        return jsonify({
            'message': '校历事件已取消',
            'event': event.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"取消校历事件失败: {str(e)}")
        return jsonify({'error': '取消校历事件失败'}), 500

@calendar_bp.route('/events/<int:event_id>/bookings', methods=['GET'])
def get_event_bookings(event_id):
    """获取事件预约列表"""
    try:
        event = SchoolCalendar.query.get(event_id)
        if not event:
            return jsonify({'error': '事件不存在'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')

        query = event.bookings

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(EventBooking.booking_time.desc())

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        bookings_list = [booking.to_dict() for booking in pagination.items]

        return jsonify({
            'bookings': bookings_list,
            'event': event.to_dict(),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取事件预约列表失败: {str(e)}")
        return jsonify({'error': '获取事件预约列表失败'}), 500

@calendar_bp.route('/statistics', methods=['GET'])
def get_calendar_statistics():
    """获取校历统计信息"""
    try:
        year = request.args.get('year', date.today().year, type=int)

        # 基础统计
        total_events = SchoolCalendar.query.filter(
            extract('year', SchoolCalendar.start_date) == year
        ).count()

        published_events = SchoolCalendar.query.filter(
            extract('year', SchoolCalendar.start_date) == year,
            SchoolCalendar.status == 'published'
        ).count()

        # 按事件类型统计
        event_type_stats = db.session.query(
            SchoolCalendar.event_type,
            func.count(SchoolCalendar.id).label('count')
        ).filter(
            extract('year', SchoolCalendar.start_date) == year,
            SchoolCalendar.status == 'published'
        ).group_by(SchoolCalendar.event_type).all()

        # 按月份统计
        monthly_stats = db.session.query(
            extract('month', SchoolCalendar.start_date).label('month'),
            func.count(SchoolCalendar.id).label('count')
        ).filter(
            extract('year', SchoolCalendar.start_date) == year,
            SchoolCalendar.status == 'published'
        ).group_by(
            extract('month', SchoolCalendar.start_date)
        ).order_by('month').all()

        # 即将到来的活动
        today = date.today()
        upcoming_events = SchoolCalendar.query.filter(
            SchoolCalendar.start_date >= today,
            SchoolCalendar.status == 'published'
        ).order_by(SchoolCalendar.start_date.asc()).limit(5).all()

        # 本月活动
        current_month = today.month
        current_year = today.year
        month_start = date(current_year, current_month, 1)
        _, last_day = monthrange(current_year, current_month)
        month_end = date(current_year, current_month, last_day)

        this_month_events = SchoolCalendar.query.filter(
            SchoolCalendar.start_date >= month_start,
            SchoolCalendar.start_date <= month_end,
            SchoolCalendar.status == 'published'
        ).order_by(SchoolCalendar.start_date.asc()).all()

        return jsonify({
            'year': year,
            'total_events': total_events,
            'published_events': published_events,
            'event_type_stats': [{'type': stat.event_type, 'count': stat.count} for stat in event_type_stats],
            'monthly_stats': [{'month': int(stat.month), 'count': stat.count} for stat in monthly_stats],
            'upcoming_events': [event.to_dict() for event in upcoming_events],
            'this_month_events': [event.to_dict() for event in this_month_events]
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取校历统计信息失败: {str(e)}")
        return jsonify({'error': '获取校历统计信息失败'}), 500

@calendar_bp.route('/upcoming', methods=['GET'])
def get_upcoming_events():
    """获取即将到来的活动（用于仪表板）"""
    try:
        limit = request.args.get('limit', 10, type=int)
        days_ahead = request.args.get('days_ahead', 30, type=int)

        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        events = SchoolCalendar.query.filter(
            SchoolCalendar.start_date >= today,
            SchoolCalendar.start_date <= end_date,
            SchoolCalendar.status == 'published'
        ).order_by(SchoolCalendar.start_date.asc()).limit(limit).all()

        return jsonify({
            'events': [event.to_dict() for event in events]
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取即将到来的活动失败: {str(e)}")
        return jsonify({'error': '获取即将到来的活动失败'}), 500

# 允许的文件类型
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@calendar_bp.route('/import/template', methods=['GET'])
def get_import_template():
    """获取校历导入模板"""
    try:
        if not PANDAS_AVAILABLE:
            return jsonify({'error': 'pandas模块未安装，无法生成Excel模板'}), 500

        import io
        from flask import send_file

        # 创建模板数据
        template_data = [
            {
                '标题': '示例：2024年春季学期开学典礼',
                '描述': '活动详细描述',
                '事件类型': 'activity',
                '开始日期': '2024-02-26',
                '结束日期': '2024-02-26',
                '开始时间': '09:00',
                '结束时间': '11:00',
                '全天事件': 'FALSE',
                '面向对象': 'all',
                '目标毕业年份': '2020,2021,2022',
                '目标学部': '高中部,初中部',
                '地点': '学校大礼堂',
                '在线链接': '',
                '优先级': 'high',
                '状态': 'published',
                '联系人': '张老师',
                '联系电话': '13800138000',
                '联系邮箱': 'teacher@school.edu.cn',
                '需要预约': 'FALSE',
                '最大参与人数': '500',
                '预约截止时间': '2024-02-25 17:00:00',
                '社团名称': '',
                '社团类型': '',
                '周年年份': '',
                '毕业年份': ''
            }
        ]

        # 创建DataFrame
        df = pd.DataFrame(template_data)

        # 创建内存中的Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='校历导入模板')
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='校历导入模板.xlsx'
        )

    except Exception as e:
        current_app.logger.error(f"生成导入模板失败: {str(e)}")
        return jsonify({'error': '生成导入模板失败'}), 500

@calendar_bp.route('/import/upload', methods=['POST'])
def upload_import_file():
    """上传并解析导入文件"""
    try:
        if not PANDAS_AVAILABLE:
            return jsonify({'error': 'pandas模块未安装，无法处理文件导入'}), 500

        # 检查文件是否存在
        if 'file' not in request.files:
            return jsonify({'error': '请选择要导入的文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '请选择要导入的文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式，请上传Excel文件(.xlsx, .xls)或CSV文件(.csv)'}), 400

        # 保存上传的文件
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        try:
            # 读取文件
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path, engine='openpyxl')

            # 数据验证和清洗
            validation_result = validate_import_data(df)
            if not validation_result['valid']:
                return jsonify({
                    'error': '数据验证失败',
                    'validation_errors': validation_result['errors']
                }), 400

            # 转换数据格式
            events_data = convert_import_data(df)

            return jsonify({
                'message': '文件解析成功',
                'events_count': len(events_data),
                'events': events_data,
                'preview': True
            }), 200

        except Exception as e:
            current_app.logger.error(f"解析文件失败: {str(e)}")
            return jsonify({'error': f'解析文件失败: {str(e)}'}), 400

        finally:
            # 清理上传的文件
            try:
                os.unlink(file_path)
            except:
                pass

    except Exception as e:
        current_app.logger.error(f"上传文件失败: {str(e)}")
        return jsonify({'error': '上传文件失败'}), 500

@calendar_bp.route('/import/confirm', methods=['POST'])
def confirm_import():
    """确认导入校历事件"""
    try:
        data = request.get_json()
        events_data = data.get('events', [])

        if not events_data:
            return jsonify({'error': '没有要导入的事件数据'}), 400

        current_user_id = int(get_jwt_identity())
        imported_events = []
        errors = []

        # 批量导入事件
        for i, event_data in enumerate(events_data):
            try:
                # 创建事件
                event = SchoolCalendar(
                    title=event_data['title'],
                    description=event_data.get('description', ''),
                    event_type=event_data['event_type'],
                    start_date=datetime.strptime(event_data['start_date'], '%Y-%m-%d').date(),
                    end_date=datetime.strptime(event_data['end_date'], '%Y-%m-%d').date() if event_data.get('end_date') else None,
                    start_time=datetime.strptime(event_data['start_time'], '%H:%M').time() if event_data.get('start_time') else None,
                    end_time=datetime.strptime(event_data['end_time'], '%H:%M').time() if event_data.get('end_time') else None,
                    all_day=event_data.get('all_day', False),
                    target_audience=event_data.get('target_audience', 'all'),
                    target_graduation_years=event_data.get('target_graduation_years', ''),
                    target_divisions=event_data.get('target_divisions', ''),
                    location=event_data.get('location', ''),
                    online_url=event_data.get('online_url', ''),
                    priority=event_data.get('priority', 'medium'),
                    status=event_data.get('status', 'draft'),
                    contact_person=event_data.get('contact_person', ''),
                    contact_phone=event_data.get('contact_phone', ''),
                    contact_email=event_data.get('contact_email', ''),
                    requires_booking=event_data.get('requires_booking', False),
                    max_participants=event_data.get('max_participants') if event_data.get('max_participants') else None,
                    booking_deadline=datetime.strptime(event_data['booking_deadline'], '%Y-%m-%d %H:%M:%S') if event_data.get('booking_deadline') else None,
                    created_by=current_user_id,
                    club_name=event_data.get('club_name', ''),
                    club_type=event_data.get('club_type'),
                    anniversary_year=event_data.get('anniversary_year') if event_data.get('anniversary_year') else None,
                    graduation_year=event_data.get('graduation_year') if event_data.get('graduation_year') else None
                )

                # 如果状态是发布，设置发布时间
                if event.status == 'published':
                    event.published_at = datetime.utcnow()

                db.session.add(event)
                imported_events.append(event.to_dict())

            except Exception as e:
                error_msg = f"第{i+1}行导入失败: {str(e)}"
                errors.append(error_msg)
                current_app.logger.error(error_msg)

        # 提交数据库事务
        if imported_events:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"批量导入提交失败: {str(e)}")
                return jsonify({'error': '批量导入提交失败，请检查数据格式'}), 500

        return jsonify({
            'message': f'成功导入{len(imported_events)}个事件',
            'imported_count': len(imported_events),
            'error_count': len(errors),
            'errors': errors,
            'imported_events': imported_events
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"确认导入失败: {str(e)}")
        return jsonify({'error': '确认导入失败'}), 500

def validate_import_data(df):
    """验证导入数据"""
    errors = []
    valid = True

    # 检查必需列
    required_columns = ['标题', '事件类型', '开始日期']
    for col in required_columns:
        if col not in df.columns:
            errors.append(f'缺少必需列: {col}')
            valid = False

    if not valid:
        return {'valid': False, 'errors': errors}

    # 验证每行数据
    for index, row in df.iterrows():
        row_num = index + 2  # Excel行号从2开始

        # 检查标题
        if pd.isna(row['标题']) or str(row['标题']).strip() == '':
            errors.append(f'第{row_num}行: 标题不能为空')

        # 检查事件类型
        valid_types = ['anniversary', 'festival', 'activity', 'club', 'meeting', 'holiday', 'exam']
        event_type = str(row['事件类型']).strip().lower()
        if event_type not in valid_types:
            errors.append(f'第{row_num}行: 事件类型无效，有效值: {", ".join(valid_types)}')

        # 检查日期格式
        try:
            if not pd.isna(row['开始日期']):
                pd.to_datetime(row['开始日期'], format='%Y-%m-%d')
        except:
            errors.append(f'第{row_num}行: 开始日期格式错误，请使用YYYY-MM-DD格式')

        # 检查结束日期
        if not pd.isna(row['结束日期']):
            try:
                end_date = pd.to_datetime(row['结束日期'], format='%Y-%m-%d')
                start_date = pd.to_datetime(row['开始日期'], format='%Y-%m-%d')
                if end_date < start_date:
                    errors.append(f'第{row_num}行: 结束日期不能早于开始日期')
            except:
                errors.append(f'第{row_num}行: 结束日期格式错误，请使用YYYY-MM-DD格式')

        # 检查时间格式
        if not pd.isna(row['开始时间']):
            try:
                pd.to_datetime(row['开始时间'], format='%H:%M')
            except:
                errors.append(f'第{row_num}行: 开始时间格式错误，请使用HH:MM格式')

        if not pd.isna(row['结束时间']):
            try:
                pd.to_datetime(row['结束时间'], format='%H:%M')
            except:
                errors.append(f'第{row_num}行: 结束时间格式错误，请使用HH:MM格式')

        # 检查优先级
        if not pd.isna(row['优先级']):
            valid_priorities = ['high', 'medium', 'low']
            priority = str(row['优先级']).strip().lower()
            if priority not in valid_priorities:
                errors.append(f'第{row_num}行: 优先级无效，有效值: {", ".join(valid_priorities)}')

        # 检查状态
        if not pd.isna(row['状态']):
            valid_statuses = ['draft', 'published', 'cancelled', 'completed']
            status = str(row['状态']).strip().lower()
            if status not in valid_statuses:
                errors.append(f'第{row_num}行: 状态无效，有效值: {", ".join(valid_statuses)}')

    return {'valid': len(errors) == 0, 'errors': errors}

def convert_import_data(df):
    """转换导入数据为标准格式"""
    events = []

    for index, row in df.iterrows():
        # 跳过空行
        if pd.isna(row['标题']) or str(row['标题']).strip() == '':
            continue

        event = {
            'title': str(row['标题']).strip(),
            'description': str(row['描述']).strip() if not pd.isna(row['描述']) else '',
            'event_type': str(row['事件类型']).strip().lower(),
            'start_date': pd.to_datetime(row['开始日期']).strftime('%Y-%m-%d'),
            'end_date': pd.to_datetime(row['结束日期']).strftime('%Y-%m-%d') if not pd.isna(row['结束日期']) else None,
            'start_time': pd.to_datetime(row['开始时间']).strftime('%H:%M') if not pd.isna(row['开始时间']) else None,
            'end_time': pd.to_datetime(row['结束时间']).strftime('%H:%M') if not pd.isna(row['结束时间']) else None,
            'all_day': str(row['全天事件']).upper() == 'TRUE' if not pd.isna(row['全天事件']) else False,
            'target_audience': str(row['面向对象']).strip().lower() if not pd.isna(row['面向对象']) else 'all',
            'target_graduation_years': str(row['目标毕业年份']).strip() if not pd.isna(row['目标毕业年份']) else '',
            'target_divisions': str(row['目标学部']).strip() if not pd.isna(row['目标学部']) else '',
            'location': str(row['地点']).strip() if not pd.isna(row['地点']) else '',
            'online_url': str(row['在线链接']).strip() if not pd.isna(row['在线链接']) else '',
            'priority': str(row['优先级']).strip().lower() if not pd.isna(row['优先级']) else 'medium',
            'status': str(row['状态']).strip().lower() if not pd.isna(row['状态']) else 'draft',
            'contact_person': str(row['联系人']).strip() if not pd.isna(row['联系人']) else '',
            'contact_phone': str(row['联系电话']).strip() if not pd.isna(row['联系电话']) else '',
            'contact_email': str(row['联系邮箱']).strip() if not pd.isna(row['联系邮箱']) else '',
            'requires_booking': str(row['需要预约']).upper() == 'TRUE' if not pd.isna(row['需要预约']) else False,
            'max_participants': int(row['最大参与人数']) if not pd.isna(row['最大参与人数']) and str(row['最大参与人数']).isdigit() else None,
            'booking_deadline': pd.to_datetime(row['预约截止时间']).strftime('%Y-%m-%d %H:%M:%S') if not pd.isna(row['预约截止时间']) else None,
            'club_name': str(row['社团名称']).strip() if not pd.isna(row['社团名称']) else '',
            'club_type': str(row['社团类型']).strip().lower() if not pd.isna(row['社团类型']) and str(row['社团类型']).strip() != '' else None,
            'anniversary_year': int(row['周年年份']) if not pd.isna(row['周年年份']) and str(row['周年年份']).isdigit() else None,
            'graduation_year': int(row['毕业年份']) if not pd.isna(row['毕业年份']) and str(row['毕业年份']).isdigit() else None
        }

        events.append(event)

    return events

