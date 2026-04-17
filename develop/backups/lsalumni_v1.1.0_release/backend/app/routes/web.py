"""
Web页面路由
处理HTML页面渲染
"""

from flask import Blueprint, render_template, send_from_directory, current_app, jsonify
import os
from datetime import datetime, timedelta
from app import db

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """主页 - 移动端界面"""
    return render_template('index.html')

@web_bp.route('/alumni-management-2025')
def admin():
    """管理后台"""
    return render_template('admin.html')


@web_bp.route('/security-portal')
def security_portal():
    """保安专用端"""
    return render_template('security-portal.html')

@web_bp.route('/register')
def register():
    """校友注册页面"""
    return render_template('register.html')

@web_bp.route('/registerOnce')
def registerOnce():
    """校友一次性注册页面"""
    return render_template('registerOnce.html')

@web_bp.route('/event-registration')
def event_registration():
    """返校日活动报名页面"""
    return render_template('event-registration.html')

@web_bp.route('/event')
def event_redirect():
    """活动报名页面重定向（兼容性）"""
    return render_template('event-registration.html')

@web_bp.route('/verification-code')
def verification_code():
    """验证码显示页面"""
    return render_template('verification-code.html')

@web_bp.route('/login')
def login():
    """登录页面"""
    return render_template('index.html')

@web_bp.route('/admin-login')
def admin_login():
    """管理后台登录页面"""
    return render_template('admin-login.html')

@web_bp.route('/ssl-setup')
def ssl_setup():
    """SSL证书设置指南页面"""
    return render_template('ssl-setup.html')

@web_bp.route('/ssl-error')
def ssl_error():
    """SSL错误页面"""
    return render_template('ssl-error.html')

@web_bp.route('/admin/dashboard')
def admin_dashboard():
    """管理后台仪表板数据API"""
    try:
        from app.models import User, EventRegistration, AlumniProfile

        # 统计数据
        total_users = User.query.count()
        total_alumni = User.query.filter(User.user_type.like('%alumni%')).count()
        total_admins = User.query.filter(User.user_type.like('%admin%')).count()

        # 今日访问统计（简化版本）
        today_visits = 50  # 这里可以根据实际需求实现访问统计

        # 活动报名统计
        total_registrations = EventRegistration.query.filter_by(status='active').count()
        event_dining_registrations = EventRegistration.query.filter_by(status='active', will_dine=True).count()

        # 校友就餐统计（包含同行人）
        alumni_dining_total = db.session.query(db.func.sum(AlumniProfile.dining_companions)).filter(
            AlumniProfile.user_id.in_(
                db.session.query(User.id).filter(User.user_type == 'alumni')
            )
        ).scalar() or 0

        # 总就餐人数 = 活动就餐人数 + 校友就餐人数（包含同行人）
        total_dining_count = event_dining_registrations + alumni_dining_total

        # 待处理事项
        pending_alumni = 0  # 待审核校友数
        pending_visits = 0   # 待审核访问数
        pending_vehicles = 0 # 待审核车辆数

        # 返校总人数 = 校友总数 + 活动报名人数（包含同行人）
        total_return_count = total_alumni + total_registrations

        statistics = {
            'total_users': total_users,
            'total_alumni': total_alumni,
            'total_admins': total_admins,
            'today_visits': today_visits,
            'total_registrations': total_registrations,
            # 就餐相关统计
            'event_dining_registrations': event_dining_registrations,  # 活动就餐人数
            'alumni_dining_total': alumni_dining_total,  # 校友就餐总人数（含同行人）
            'total_dining_count': total_dining_count,  # 总就餐人数
            # 返校人数统计
            'total_return_count': total_return_count,  # 总返校人数
            # 待处理事项
            'pending_alumni': pending_alumni,
            'pending_visits': pending_visits,
            'pending_vehicles': pending_vehicles
        }

        # 访问趋势（简化数据）
        visit_trend = [
            {'date': (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d'), 'visits': 30},
            {'date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'), 'visits': 45},
            {'date': (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d'), 'visits': 38},
            {'date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'), 'visits': 52},
            {'date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'), 'visits': 41},
            {'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), 'visits': 48},
            {'date': datetime.now().strftime('%Y-%m-%d'), 'visits': today_visits}
        ]

        # 访问目的统计（简化数据）
        purpose_stats = [
            {'purpose': '返校参观', 'count': 120},
            {'purpose': '拜访老师', 'count': 85},
            {'purpose': '参加活动', 'count': 65},
            {'purpose': '办事', 'count': 45}
        ]

        return jsonify({
            'success': True,
            'statistics': statistics,
            'visit_trend': visit_trend,
            'purpose_stats': purpose_stats
        })

    except Exception as e:
        current_app.logger.error(f"获取仪表板数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取仪表板数据失败'
        }), 500


@web_bp.route('/templates/<path:filename>')
def template_files(filename):
    """模板文件服务"""
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    template_dir = os.path.join(root_dir, 'frontend', 'templates')

    return send_from_directory(template_dir, filename)

@web_bp.route('/test')
def test_api():
    """API测试页面"""
    return send_from_directory(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'backend/templates/test_api.html'
    )

@web_bp.route('/uploads/<path:filename>')
def uploaded_files(filename):
    """上传文件服务"""
    try:
        # 获取项目根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        upload_dir = os.path.join(root_dir, 'uploads')

        return send_from_directory(upload_dir, filename)
    except Exception as e:
        current_app.logger.error(f"Upload file error: {e}")
        return '', 404

@web_bp.route('/favicon.ico')
def favicon():
    """favicon服务"""
    try:
        # 使用Flask的static_folder来服务favicon
        return current_app.send_static_file('favicon.ico')
    except Exception as e:
        print(f"Favicon error: {e}")
        return '', 404

# 添加对 /lsalumni/ 前缀的支持
@web_bp.route('/lsalumni/')
def lsalumni_index():
    """主页 - 移动端界面 (带/lsalumni/前缀)"""
    return render_template('index.html')

@web_bp.route('/lsalumni/admin')
def lsalumni_admin():
    """管理后台 (带/lsalumni/前缀)"""
    return render_template('admin.html')

@web_bp.route('/lsalumni/security-portal')
def lsalumni_security_portal():
    """保安专用端 (带/lsalumni/前缀)"""
    return render_template('security-portal.html')

@web_bp.route('/lsalumni/register')
def lsalumni_register():
    """校友注册页面 (带/lsalumni/前缀)"""
    return render_template('register.html')

@web_bp.route('/lsalumni/registerOnce')
def lsalumni_registerOnce():
    """校友一次性注册页面 (带/lsalumni/前缀)"""
    return render_template('registerOnce.html')

@web_bp.route('/lsalumni/event-registration')
def lsalumni_event_registration():
    """返校日活动报名页面 (带/lsalumni/前缀)"""
    return render_template('event-registration.html')

@web_bp.route('/lsalumni/event')
def lsalumni_event_redirect():
    """活动报名页面重定向（兼容性，带/lsalumni/前缀）"""
    return render_template('event-registration.html')

@web_bp.route('/lsalumni/login')
def lsalumni_login():
    """登录页面 (带/lsalumni/前缀)"""
    return render_template('index.html')

@web_bp.route('/lsalumni/admin-login')
def lsalumni_admin_login():
    """管理后台登录页面 (带/lsalumni/前缀)"""
    return render_template('admin-login.html')

@web_bp.route('/lsalumni/ssl-setup')
def lsalumni_ssl_setup():
    """SSL证书设置指南页面 (带/lsalumni/前缀)"""
    return render_template('ssl-setup.html')

@web_bp.route('/lsalumni/ssl-error')
def lsalumni_ssl_error():
    """SSL错误页面 (带/lsalumni/前缀)"""
    return render_template('ssl-error.html')

# 添加对 /static/ 静态文件的支持
@web_bp.route('/static/<path:filename>')
def static_files(filename):
    """静态文件服务"""
    try:
        return current_app.send_static_file(filename)
    except Exception as e:
        current_app.logger.error(f"Static file error: {e}")
        return '', 404

# 添加对 /lsalumni/static/ 静态文件的支持
@web_bp.route('/lsalumni/static/<path:filename>')
def lsalumni_static_files(filename):
    """静态文件服务 (带/lsalumni/前缀)"""
    try:
        return current_app.send_static_file(filename)
    except Exception as e:
        current_app.logger.error(f"Static file error: {e}")
        return '', 404