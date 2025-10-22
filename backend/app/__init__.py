"""
Flask应用初始化
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
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

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # 根据环境变量选择配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # 加载配置
    from app.config import config
    Config = config.get(config_name, config['default'])

    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    
    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.visits import visits_bp
    from app.routes.faces import faces_bp
    from app.routes.admin import admin_bp
    from app.routes.web import web_bp
    from app.routes.target_persons import target_persons_bp
    from app.routes.user_compat import user_compat_bp
    from app.routes.qr_codes import qr_codes_bp
    from app.routes.security_portal import security_portal_bp
    from app.routes.health import health_bp
    from app.routes.calendar import calendar_bp, public_calendar_bp
    from app.api.organization import organization_bp
    from app.routes.roles import roles_bp

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
    app.register_blueprint(health_bp)
    app.register_blueprint(web_bp)

    
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