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
    """主页 - 统一入口"""
    return render_template('portal.html')

@web_bp.route('/index.html')
def index_redirect():
    """兼容旧链接 - 重定向到主页"""
    return render_template('portal.html')

@web_bp.route('/electronic-card')
def electronic_card():
    """电子校友卡 - 家长/校友/学生统一入口"""
    return render_template('electronic-card.html')

@web_bp.route('/alumni-management-2025')
def admin():
    """管理后台"""
    return render_template('admin.html')

@web_bp.route('/admin/key-management')
def key_management():
    """密钥管理页面"""
    return render_template('admin/key-management.html')

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

@web_bp.route('/generate-code')
def generate_code():
    """生成入校码页面（学生/校友）"""
    return render_template('generate-code.html')

@web_bp.route('/apply-visit')
def apply_visit():
    """访客申请页面（家长/访客）"""
    return render_template('apply-visit.html')

@web_bp.route('/teacher-approve')
def teacher_approve():
    """教师审批页面"""
    return render_template('teacher-approve.html')

@web_bp.route('/guard-verify')
def guard_verify():
    """门卫验证页面"""
    return render_template('guard-verify.html')

@web_bp.route('/external-visitor')
def external_visitor():
    """外部访客申请页面（老师端）"""
    return render_template('external-visitor.html')

@web_bp.route('/student-leave-apply')
def student_leave_apply():
    """学生请假申请页面（家长端）"""
    return render_template('student-leave-apply.html')

@web_bp.route('/parent-portal')
def parent_portal():
    """家长服务中心"""
    return render_template('parent-portal.html')

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
        from app.models import User, EventRegistration, AlumniProfile, StudentLeaveApplication, VisitApplication

        # ========== 基础统计数据 ==========
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
        pending_alumni = AlumniProfile.query.filter_by(approval_status='pending').count()
        pending_visits = VisitApplication.query.filter_by(application_status='pending').count()
        pending_leaves = StudentLeaveApplication.query.filter_by(status='pending').count()

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
            'pending_leaves': pending_leaves
        }

        # ========== 学生请假统计（按年级、班级）==========
        leave_by_grade = db.session.query(
            StudentLeaveApplication.grade,
            db.func.count(StudentLeaveApplication.id).label('count')
        ).filter(
            StudentLeaveApplication.status.in_(['approved', 'completed'])
        ).group_by(StudentLeaveApplication.grade).all()

        leave_by_class = db.session.query(
            StudentLeaveApplication.grade,
            StudentLeaveApplication.class_name,
            db.func.count(StudentLeaveApplication.id).label('count')
        ).filter(
            StudentLeaveApplication.status.in_(['approved', 'completed'])
        ).group_by(
            StudentLeaveApplication.grade,
            StudentLeaveApplication.class_name
        ).order_by(
            StudentLeaveApplication.grade,
            StudentLeaveApplication.class_name
        ).all()

        # 格式化请假统计
        leave_statistics = {
            'by_grade': [{'grade': grade or '未分类', 'count': count} for grade, count in leave_by_grade],
            'by_class': [{'grade': grade, 'class_name': class_name, 'count': count}
                        for grade, class_name, count in leave_by_class],
            'total_approved': StudentLeaveApplication.query.filter(
                StudentLeaveApplication.status.in_(['approved', 'completed'])
            ).count()
        }

        # ========== 校友入校统计（按毕业年份/年级）==========
        alumni_by_year = db.session.query(
            AlumniProfile.graduation_year,
            db.func.count(AlumniProfile.id).label('count')
        ).filter(
            AlumniProfile.approval_status == 'approved'
        ).group_by(AlumniProfile.graduation_year).order_by(
            AlumniProfile.graduation_year.desc()
        ).all()

        alumni_by_division = db.session.query(
            AlumniProfile.division,
            db.func.count(AlumniProfile.id).label('count')
        ).filter(
            AlumniProfile.approval_status == 'approved'
        ).group_by(AlumniProfile.division).all()

        # 格式化校友统计
        alumni_statistics = {
            'by_graduation_year': [{'year': year, 'count': count} for year, count in alumni_by_year],
            'by_division': [{'division': division or '未分类', 'count': count} for division, count in alumni_by_division],
            'total_approved': AlumniProfile.query.filter_by(approval_status='approved').count()
        }

        # ========== 校外访客统计（按受访者/部门）==========
        visitor_by_person = db.session.query(
            VisitApplication.target_person,
            db.func.count(VisitApplication.id).label('count')
        ).filter(
            VisitApplication.application_status.in_(['approved', 'completed'])
        ).group_by(VisitApplication.target_person).order_by(
            db.func.count(VisitApplication.id).desc()
        ).limit(20).all()

        visitor_by_department = db.session.query(
            VisitApplication.target_department,
            db.func.count(VisitApplication.id).label('count')
        ).filter(
            VisitApplication.application_status.in_(['approved', 'completed'])
        ).group_by(VisitApplication.target_department).order_by(
            db.func.count(VisitApplication.id).desc()
        ).all()

        # 访客状态统计
        visitor_by_status = db.session.query(
            VisitApplication.application_status,
            db.func.count(VisitApplication.id).label('count')
        ).group_by(VisitApplication.application_status).all()

        # 格式化访客统计
        visitor_statistics = {
            'by_target_person': [{'person': person or '未指定', 'count': count} for person, count in visitor_by_person],
            'by_department': [{'department': dept or '未指定', 'count': count} for dept, count in visitor_by_department],
            'by_status': [{'status': status, 'count': count} for status, count in visitor_by_status],
            'total_approved': VisitApplication.query.filter(
                VisitApplication.application_status.in_(['approved', 'completed'])
            ).count()
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
            'purpose_stats': purpose_stats,
            # 新增详细统计
            'leave_statistics': leave_statistics,
            'alumni_statistics': alumni_statistics,
            'visitor_statistics': visitor_statistics
        })

    except Exception as e:
        current_app.logger.error(f"获取仪表板数据失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
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

@web_bp.route('/lsalumni/guard-verify')
def lsalumni_guard_verify():
    """门卫验证页面 (带/lsalumni/前缀)"""
    return render_template('guard-verify.html')

@web_bp.route('/lsalumni/student-leave-apply')
def lsalumni_student_leave_apply():
    """学生请假申请页面（家长端，带/lsalumni/前缀）"""
    return render_template('student-leave-apply.html')

@web_bp.route('/lsalumni/parent-portal')
def lsalumni_parent_portal():
    """家长服务中心（带/lsalumni/前缀）"""
    return render_template('parent-portal.html')

@web_bp.route('/teacher-wechat')
def teacher_wechat():
    """老师微信H5页面"""
    return render_template('teacher-wechat.html')

@web_bp.route('/parent-wechat')
def parent_wechat():
    """家长微信H5页面"""
    return render_template('parent-wechat.html')

@web_bp.route('/lsalumni/teacher-wechat')
def lsalumni_teacher_wechat():
    """老师微信H5页面（带/lsalumni/前缀）"""
    return render_template('teacher-wechat.html')

@web_bp.route('/lsalumni/parent-wechat')
def lsalumni_parent_wechat():
    """家长微信H5页面（带/lsalumni/前缀）"""
    return render_template('parent-wechat.html')

@web_bp.route('/parent-simple')
def parent_simple():
    """家长简化版H5页面（无需登录）"""
    return render_template('parent-simple.html')

@web_bp.route('/visitor-verify')
def visitor_verify():
    """访客验证页面"""
    return render_template('visitor-verify.html')

@web_bp.route('/teacher-statistics')
def teacher_statistics():
    """教师统计页面"""
    return render_template('teacher-statistics.html')

@web_bp.route('/lsalumni/parent-simple')
def lsalumni_parent_simple():
    """家长简化版H5页面（无需登录，带/lsalumni/前缀）"""
    return render_template('parent-simple.html')

@web_bp.route('/visitor-register')
def visitor_register():
    """访客登记页面（无需登录）"""
    return render_template('visitor-register.html')

@web_bp.route('/lsalumni/visitor-register')
def lsalumni_visitor_register():
    """访客登记页面（带/lsalumni/前缀）"""
    return render_template('visitor-register.html')

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

@web_bp.route('/responsive-test')
def responsive_test():
    """响应式布局测试页面"""
    return render_template('responsive-test.html')

@web_bp.route('/lsalumni/responsive-test')
def lsalumni_responsive_test():
    """响应式布局测试页面 (带/lsalumni/前缀)"""
    return render_template('responsive-test.html')