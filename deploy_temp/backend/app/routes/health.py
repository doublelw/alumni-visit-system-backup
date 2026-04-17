"""
健康检查API
"""

from flask import Blueprint

health_bp = Blueprint('health', __name__)

@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """系统健康检查"""
    return {
        'status': 'healthy',
        'message': '系统运行正常',
        'version': '1.1.0'
    }, 200