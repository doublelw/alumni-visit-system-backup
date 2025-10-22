"""
Web页面路由
处理HTML页面渲染
"""

from flask import Blueprint, render_template, send_from_directory, current_app
import os

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """主页 - 移动端界面"""
    return render_template('index.html')

@web_bp.route('/admin')
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

@web_bp.route('/favicon.ico')
def favicon():
    """favicon服务"""
    try:
        # 使用Flask的static_folder来服务favicon
        return current_app.send_static_file('favicon.ico')
    except Exception as e:
        print(f"Favicon error: {e}")
        return '', 404