"""
Flask应用初始化
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

# 全局扩展对象
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name=None):
    """
    创建Flask应用实例
    """
    # 获取项目根目录
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(backend_dir)
    template_folder = os.path.join(project_root, 'frontend', 'templates')
    static_folder = os.path.join(project_root, 'frontend', 'static')

    # 添加backend目录到Python路径（修复Docker环境导入问题）
    import sys
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # 加载.env文件
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # 根据环境变量选择配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # 加载配置（使用相对导入避免路径冲突）
    from .config import config
    Config = config.get(config_name, config['default'])

    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # 初始化电子校友卡服务
    from .services.electronic_card_service import ElectronicCardService
    ElectronicCardService.init_app(app.config.get('ELECTRONIC_CARD_SECRET_KEY'))

    # 初始化Redis缓存管理器（如果启用）
    cache_manager = None
    if app.config.get('CACHE_ENABLED', False):
        try:
            from ..utils.cache_manager import CacheManager
            cache_manager = CacheManager(
                redis_host=app.config.get('REDIS_HOST', 'localhost'),
                redis_port=app.config.get('REDIS_PORT', 6379),
                redis_db=app.config.get('REDIS_DB', 0),
                password=app.config.get('REDIS_PASSWORD')
            )
            app.cache_manager = cache_manager

            if cache_manager.is_available():
                app.logger.info('Redis缓存已启用')
            else:
                app.logger.warning('Redis连接失败，将使用降级模式（无缓存）')
        except ImportError:
            app.logger.warning('cache_manager模块未找到，缓存功能不可用')
        except Exception as e:
            app.logger.warning(f'Redis缓存初始化失败: {e}')
    else:
        app.cache_manager = None


    # 注册蓝图
    from .routes.auth import auth_bp
    from .routes.users import users_bp
    from .routes.visits import visits_bp
    from .routes.faces import faces_bp
    from .routes.admin import admin_bp
    from .routes.web import web_bp
    from .routes.target_persons import target_persons_bp
    from .routes.user_compat import user_compat_bp
    from .routes.qr_codes import qr_codes_bp
    from .routes.security_portal import security_portal_bp
    from .routes.health import health_bp
    from .routes.calendar import calendar_bp, public_calendar_bp
    from .api.organization import organization_bp
    from .routes.roles import roles_bp
    from .routes.alumni import alumni_bp
    from .routes.student_exit import student_exit_bp
    from .routes.survey import survey_bp
    from .routes.event import event_bp
    from .routes.backup import backup_bp
    from .routes.electronic_card import electronic_card_bp
    from .routes.student_leave import student_leave_bp
    from .routes.parent import parent_bp
    from .routes.wechat import wechat_bp
    from .routes.key_management import key_management_bp
    from .routes.external_visitor import external_visitor_bp
    from .routes.guard_verify import guard_verify_bp
    from .routes.external import external_bp
    from .routes.statistics import statistics_bp
    from .routes.student_leave_statistics import student_leave_statistics_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(visits_bp, url_prefix='/api/visits')
    app.register_blueprint(faces_bp, url_prefix='/api/faces')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(qr_codes_bp, url_prefix='/api/qr-codes')
    app.register_blueprint(target_persons_bp, url_prefix='/api/target-persons')
    app.register_blueprint(user_compat_bp, url_prefix='/api/user', name='user_compat')  # 兼容性路径
    app.register_blueprint(security_portal_bp, url_prefix='/api/security-portal')
    app.register_blueprint(calendar_bp, url_prefix='/api/calendar')
    app.register_blueprint(public_calendar_bp, url_prefix='/api/public/calendar')
    app.register_blueprint(organization_bp)
    app.register_blueprint(roles_bp, url_prefix='/api/roles')
    app.register_blueprint(alumni_bp, url_prefix='/api/alumni')
    app.register_blueprint(student_exit_bp)
    app.register_blueprint(survey_bp, url_prefix='/api/survey')
    app.register_blueprint(event_bp, url_prefix='/api/event')
    app.register_blueprint(backup_bp, url_prefix='/api/admin/backup')
    app.register_blueprint(electronic_card_bp, url_prefix='/api/electronic-card')
    app.register_blueprint(student_leave_bp, url_prefix='/api/student-leave')
    app.register_blueprint(parent_bp, url_prefix='/api/parent')
    app.register_blueprint(wechat_bp, url_prefix='/api/wechat')
    app.register_blueprint(key_management_bp, url_prefix='/api/admin/keys')
    app.register_blueprint(external_visitor_bp, url_prefix='/api/external-visitor')
    app.register_blueprint(guard_verify_bp, url_prefix='/api/guard')
    app.register_blueprint(external_bp)
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    app.register_blueprint(student_leave_statistics_bp, url_prefix='/teacher')
    app.register_blueprint(health_bp)
    app.register_blueprint(web_bp)

    # 配置uploads静态文件路由
    uploads_folder = os.path.join(project_root, 'backend', 'uploads')
    if os.path.exists(uploads_folder):
        @app.route('/uploads/<filename>')
        def serve_uploaded_file(filename):
            from flask import send_from_directory
            return send_from_directory(uploads_folder, filename)


    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request'}, 400

    # JWT错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired'}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token'}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Authorization token is required'}, 401

    return app