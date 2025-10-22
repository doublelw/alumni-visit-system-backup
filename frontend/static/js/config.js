/**
 * 系统配置文件
 * 用于管理API地址和其他系统配置
 */

// 自动检测当前环境
const getEnvironmentConfig = () => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;

    // 根据当前域名自动确定API地址
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        // 开发环境
        return {
            API_BASE_URL: `${protocol}//${hostname}:5000/api`,
            FRONTEND_BASE_URL: `${protocol}//${hostname}:8080`,
            WS_BASE_URL: `ws://${hostname}:5000`,
            environment: 'development'
        };
    } else {
        // 生产环境 - 使用当前域名
        return {
            API_BASE_URL: `${protocol}//${hostname}/api`,
            FRONTEND_BASE_URL: `${protocol}//${hostname}`,
            WS_BASE_URL: `wss://${hostname}/ws`,
            environment: 'production'
        };
    }
};

const config = getEnvironmentConfig();

// 导出配置
window.Config = {
    API_BASE_URL: config.API_BASE_URL,
    FRONTEND_BASE_URL: config.FRONTEND_BASE_URL,
    WS_BASE_URL: config.WS_BASE_URL,
    ENVIRONMENT: config.environment,

    // 应用信息
    APP_NAME: '校友入校登记系统',
    VERSION: '1.0.0',

    // API超时设置
    API_TIMEOUT: 30000,

    // 分页设置
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,

    // 文件上传限制
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_FILE_TYPES: ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx'],

    // 本地存储键名
    STORAGE_KEYS: {
        AUTH_TOKEN: 'auth_token',
        USER_INFO: 'user_info',
        THEME: 'theme',
        LANGUAGE: 'language'
    },

    // 状态映射
    USER_TYPES: {
        'admin': '管理员',
        'teacher': '教师',
        'alumni': '校友',
        'security': '保安'
    },

    VISIT_STATUSES: {
        'pending': '待审核',
        'approved': '已通过',
        'rejected': '已拒绝',
        'cancelled': '已取消'
    },

    // 获取完整的API URL
    getApiUrl: function(endpoint) {
        return `${this.API_BASE_URL}${endpoint}`;
    },

    // 获取前端URL
    getFrontendUrl: function(path) {
        return `${this.FRONTEND_BASE_URL}${path}`;
    }
};

// 在控制台输出配置信息（仅在开发环境）
if (config.environment === 'development') {
    console.log('=== 系统配置 ===');
    console.log('环境:', config.environment);
    console.log('API地址:', window.Config.API_BASE_URL);
    console.log('前端地址:', window.Config.FRONTEND_BASE_URL);
    console.log('================');
}