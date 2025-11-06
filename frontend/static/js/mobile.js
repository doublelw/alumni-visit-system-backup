/**
 * 移动端应用JavaScript - 版本 5.3 (电子校友卡风格访问二维码)
 * 校友入校登记系统
 * 更新时间: 2025-01-29 06:40
 */

console.log('=== MOBILE.JS 版本 5.3 已加载 ===');

// 模态框操作状态跟踪
let isModalOperationInProgress = false;

// 应用配置
const APP_CONFIG = {
    API_BASE_URL: window.Config?.API_BASE_URL || '/api',
    STORAGE_KEYS: {
        TOKEN: 'auth_token',
        USER: 'user_info',
        REMEMBER_USERNAME: 'remember_username',
        REMEMBER_PASSWORD: 'remember_password'
    },
    PAGES: {
        HOME: 'home',
        VISIT: 'visit',
        FACE: 'face',
        PROFILE: 'profile'
    },
    // 事件绑定标志
    EVENTS_BOUND: {
        QUICK_ACTIONS: false
    }
};

// 应用状态
const AppState = {
    currentPage: APP_CONFIG.PAGES.HOME,
    user: null,
    token: null,
    isAuthenticated: false
};

// 工具函数
const Utils = {
    // API请求封装
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {}
        };

        // 只有当body不是FormData时才设置Content-Type
        if (!(options.body instanceof FormData)) {
            defaultOptions.headers['Content-Type'] = 'application/json';
        }

        if (AppState.token) {
            defaultOptions.headers['Authorization'] = `Bearer ${AppState.token}`;
        }

        // 在开发环境中绕过SSL验证
        const fetchOptions = {
            ...defaultOptions,
            ...options
        };

        // 只对HTTPS请求添加代理设置（用于开发环境）
        if (APP_CONFIG.API_BASE_URL.startsWith('https://localhost')) {
            // 在浏览器环境中，我们需要特殊的处理来绕过SSL
            // 对于localhost，大多数浏览器会自签名证书的问题
            fetchOptions.credentials = 'omit'; // 不发送cookies以避免证书问题
        }

        const fullUrl = APP_CONFIG.API_BASE_URL + url;
        console.log('=== 请求调试信息 ===');
        console.log('完整URL:', fullUrl);
        console.log('请求方法:', fetchOptions.method || 'GET');
        console.log('请求头:', fetchOptions.headers);
        console.log('请求体:', fetchOptions.body);

        let response;
        try {
            response = await fetch(fullUrl, fetchOptions);
            console.log('响应状态:', response.status, response.statusText);
        } catch (fetchError) {
            // 简化错误处理 - 开发环境使用HTTP模式
            console.warn('API请求失败:', fetchError.message);
            throw new Error(`网络连接失败：请确保开发服务器正在运行 (${APP_CONFIG.API_BASE_URL})`);
        }

        let data;
        try {
            data = await response.json();
            console.log('响应数据:', data);
        } catch (jsonError) {
            // 如果响应不是JSON格式，使用默认错误消息
            console.warn('JSON解析失败:', jsonError.message);
            if (!response.ok) {
                throw new Error(`请求失败 (${response.status})`);
            }
            data = {};
        }

        if (!response.ok) {
            // 尝试从多个字段获取错误信息
            let errorMessage = data.error || data.message || `请求失败 (${response.status})`;

            // 如果是401错误且没有详细错误信息，提供默认提示
            if (response.status === 401 && !data.error && !data.message) {
                errorMessage = '登录失败：用户名或密码错误，请检查后重试';
            }

            console.log('最终错误消息:', errorMessage);
            console.log('响应数据详情:', data);
            throw new Error(errorMessage);
        }

        return data;
    },

    // 显示Toast提示
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastMessage = toast.querySelector('.toast-message');
        const toastIcon = toast.querySelector('.toast-icon');

        // 设置消息和样式 - 支持多行文本和HTML
        if (message.includes('\n')) {
            // 如果包含换行符，使用innerHTML并转换换行为<br>
            toastMessage.innerHTML = message.replace(/\n/g, '<br>').replace(/📅|🕐|👤|✅|❌/g, match => `<span style="font-size: 16px; margin-right: 4px;">${match}</span>`);
        } else {
            // 简单消息使用textContent（更安全）
            toastMessage.textContent = message;
        }

        toast.className = `toast ${type} show`;

        // 设置图标
        const icons = {
            success: 'ri-check-line',
            error: 'ri-close-line',
            warning: 'ri-alert-line',
            info: 'ri-information-line'
        };
        toastIcon.className = `toast-icon ${icons[type] || icons.info}`;

        // 根据消息长度调整显示时间
        const displayTime = message.length > 100 ? 5000 : 3000;
        setTimeout(() => {
            toast.classList.remove('show');
        }, displayTime);
    },

    // 格式化日期
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    },

    // 格式化时间
    formatTime(timeString) {
        if (!timeString) return '--:--';
        return timeString.slice(0, 5);
    },

    // 获取状态文本
    getStatusText(status) {
        const statusMap = {
            pending: '待审核',
            approved: '已通过',
            rejected: '已拒绝',
            completed: '已完成',
            cancelled: '已取消'
        };
        return statusMap[status] || status;
    },

    // 获取状态样式类
    getStatusClass(status) {
        return `status-${status}`;
    },

    // 验证表单
    validateForm(formData, rules) {
        const errors = [];

        for (const [field, rule] of Object.entries(rules)) {
            const value = formData[field];

            if (rule.required && !value) {
                errors.push(`${rule.label}不能为空`);
                continue;
            }

            if (rule.type === 'email' && value && !this.validateEmail(value)) {
                errors.push(`${rule.label}格式不正确`);
            }

            if (rule.type === 'phone' && value && !this.validatePhone(value)) {
                errors.push(`${rule.label}格式不正确`);
            }

            if (rule.minLength && value && value.length < rule.minLength) {
                errors.push(`${rule.label}长度至少${rule.minLength}位`);
            }

            if (rule.confirm && formData[rule.confirm] !== value) {
                errors.push(`${rule.label}与确认${rule.label}不一致`);
            }
        }

        return errors;
    },

    // 验证邮箱
    validateEmail(email) {
        const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return pattern.test(email);
    },

    // 验证手机号
    validatePhone(phone) {
        const pattern = /^1[3-9]\d{9}$/;
        return pattern.test(phone);
    },

    // 设置最小日期为今天
    setMinDate(inputId) {
        const input = document.getElementById(inputId);
        if (input) {
            const today = new Date().toISOString().split('T')[0];
            input.min = today;
        }
    },

    // 设置默认日期为第二天
    setDefaultDate(inputId) {
        const input = document.getElementById(inputId);
        if (input) {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            input.value = tomorrow.toISOString().split('T')[0];
        }
    },

    // 设置默认时间为整点（下一个整点）
    setDefaultTime(inputId) {
        const input = document.getElementById(inputId);
        if (input) {
            const now = new Date();
            const nextHour = new Date(now.getTime() + 60 * 60 * 1000);
            const hours = nextHour.getHours().toString().padStart(2, '0');
            input.value = `${hours}:00`;
        }
    },

    // 设置结束时间（开始时间后1小时）
    setEndTime(startTimeId, endTimeId) {
        const startTimeInput = document.getElementById(startTimeId);
        const endTimeInput = document.getElementById(endTimeId);

        if (startTimeInput && endTimeInput && startTimeInput.value && startTimeInput.value.trim() !== '') {
            try {
                const [hours, minutes] = startTimeInput.value.split(':').map(Number);

                // 验证时间格式是否有效
                if (isNaN(hours) || isNaN(minutes) || hours < 0 || hours > 23 || minutes < 0 || minutes > 59) {
                    console.warn('Invalid time format:', startTimeInput.value);
                    return;
                }

                const startTime = new Date();
                startTime.setHours(hours, minutes, 0, 0);

                const endTime = new Date(startTime.getTime() + 60 * 60 * 1000);
                const endTimeStr = endTime.toTimeString().slice(0, 5);

                endTimeInput.value = endTimeStr;
                endTimeInput.min = startTimeInput.value;
            } catch (error) {
                console.error('Error setting end time:', error);
            }
        }
    },

    // 验证身份证号码
    validateIdCard(idCard) {
        // 简单的身份证格式验证（15位或18位）
        const pattern = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/;
        return pattern.test(idCard);
    },

    // 显示加载状态
    showLoading(message = '加载中...') {
        // 移除已存在的加载提示
        this.hideLoading();

        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'globalLoading';
        loadingDiv.innerHTML = `
            <div class="loading-overlay">
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p class="loading-text">${message}</p>
                </div>
            </div>
        `;

        // 添加样式
        loadingDiv.querySelector('.loading-overlay').style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            animation: fadeIn 0.3s ease-in-out;
        `;

        loadingDiv.querySelector('.loading-spinner').style.cssText = `
            background: white;
            padding: 20px 30px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        `;

        loadingDiv.querySelector('.spinner').style.cssText = `
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        `;

        loadingDiv.querySelector('.loading-text').style.cssText = `
            margin: 0;
            color: #333;
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;

        // 添加动画样式
        if (!document.getElementById('loadingStyles')) {
            const style = document.createElement('style');
            style.id = 'loadingStyles';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(loadingDiv);
    },

    // 隐藏加载状态
    hideLoading() {
        const loadingDiv = document.getElementById('globalLoading');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
};

// 认证管理
const Auth = {
    // 登录
    async login(username, password) {
        try {
            const data = await Utils.request('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });

            // 保存认证信息
            AppState.token = data.access_token;
            AppState.user = data.user;
            AppState.isAuthenticated = true;

            // 保存到本地存储
            localStorage.setItem(APP_CONFIG.STORAGE_KEYS.TOKEN, data.access_token);
            localStorage.setItem(APP_CONFIG.STORAGE_KEYS.USER, JSON.stringify(data.user));

            // 如果是学生、家长或班主任，加载学生出校申请
            if (["student", "parent", "teacher"].includes(data.user.user_type)) {
                setTimeout(() => {
                    if (typeof window.studentExitApp !== 'undefined') {
                        window.studentExitApp.updateApplicationSectionsByUserType(data.user);
                    }
                }, 500);
            }

            Utils.showToast('登录成功', 'success');
            return data;
        } catch (error) {
            // 显示登录错误提示（如果登录模态框是打开的）
            if (typeof showLoginError === 'function') {
                let errorMessage = error.message;

                // 根据错误类型提供不同的提示信息
                if (error.message.includes('用户名或密码错误') || error.message.includes('密码错误')) {
                    errorMessage = '用户名或密码错误，请检查后重试';
                } else if (error.message.includes('用户不存在') || error.message.includes('not found')) {
                    errorMessage = '用户不存在，请检查用户名或<a href="/register" style="color: #007bff; text-decoration: underline;">立即注册</a>';
                } else if (error.message.includes('登录失败，请稍后重试') || error.message.includes('500')) {
                    errorMessage = '服务器错误，请稍后重试或联系管理员';
                }

                showLoginError(errorMessage);
            }
            Utils.showToast(error.message, 'error');
            throw error;
        }
    },

    // 注册
    async register(userData) {
        try {
            const data = await Utils.request('/api/auth/register', {
                method: 'POST',
                body: JSON.stringify(userData)
            });

            Utils.showToast('注册成功，请登录', 'success');
            return data;
        } catch (error) {
            Utils.showToast(error.message, 'error');
            throw error;
        }
    },

    // 退出登录
    logout() {
        // 防止重复调用
        if (window.isLoggingOut) {
            console.log('退出登录已在进行中，跳过重复调用');
            return;
        }

        console.log('=== 开始退出登录 ===');

        // 设置全局退出标志，防止其他逻辑重新显示登录模态框
        window.isLoggingOut = true;
        isModalOperationInProgress = false;

        AppState.token = null;
        AppState.user = null;
        AppState.isAuthenticated = false;

        // 清除本地存储
        localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.TOKEN);
        localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.USER);

        // 清除所有可能的定时器和异步操作
        if (window.logoutTimer) {
            clearTimeout(window.logoutTimer);
        }

        // 显示退出提示
        Utils.showToast('已退出登录', 'info');

        // 立即显示登录模态框
        const modal = document.getElementById('loginModal');
        if (modal) {
            console.log('退出登录：显示登录模态框');
            // 直接调用showModal，绕过showLoginModal的检查
            UI.showModal('loginModal');
            UI.restoreRememberedCredentials();
        }

        // 重置退出标志
        setTimeout(() => {
            window.isLoggingOut = false;
        }, 200);

        console.log('=== 退出登录完成 ===');
    },

    // 初始化认证状态
    async initAuth() {
        const token = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.TOKEN);
        const userStr = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.USER);

        if (token && userStr) {
            try {
                AppState.token = token;
                AppState.user = JSON.parse(userStr);

                // 验证token是否仍然有效
                try {
                    // 使用获取用户信息接口来验证token
                    await Utils.request('/api/auth/profile', {
                        method: 'GET'
                    });

                    AppState.isAuthenticated = true;
                    // 更新UI
                    UI.updateUserInfo();
                } catch (error) {
                    // Token无效，清除认证信息
                    console.log('Token已失效，需要重新登录');
                    // 清除状态但不显示提示
                    AppState.token = null;
                    AppState.user = null;
                    AppState.isAuthenticated = false;
                    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.TOKEN);
                    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.USER);
                }
            } catch (error) {
                // 清除状态但不显示提示
                AppState.token = null;
                AppState.user = null;
                AppState.isAuthenticated = false;
                localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.TOKEN);
                localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.USER);
            }
        }
    },

    // 检查认证状态
    checkAuth() {
        if (!AppState.isAuthenticated && !window.isLoggingOut) {
            UI.showLoginModal();
            return false;
        }
        return true;
    }
};

// 页面管理
const PageManager = {
    // 切换页面
    switchPage(pageName) {
        // 隐藏所有页面
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });

        // 显示目标页面
        const targetPage = document.getElementById(pageName + 'Page');
        if (targetPage) {
            targetPage.classList.add('active');
            AppState.currentPage = pageName;
        }

        // 更新导航栏状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });

        const activeNavItem = document.querySelector(`[data-page="${pageName}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }

        // 页面切换时的处理
        this.onPageSwitch(pageName);
    },

    // 页面切换处理
    onPageSwitch(pageName) {
        switch (pageName) {
            case APP_CONFIG.PAGES.HOME:
                HomePage.load();
                break;
            case APP_CONFIG.PAGES.VISIT:
                VisitPage.load();
                break;
            case APP_CONFIG.PAGES.FACE:
                FacePage.load();
                break;
            case APP_CONFIG.PAGES.PROFILE:
                ProfilePage.load();
                break;
            case 'review':
                ReviewPage.load();
                break;
        }
    }
};

// UI管理
const UI = {
    // 初始化UI
    init() {
        this.initNavigation();
        this.initModals();
        this.initForms();
    },

    // 初始化导航
    initNavigation() {
        // 底部导航点击事件
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const pageName = item.dataset.page;
                if (Auth.checkAuth()) {
                    PageManager.switchPage(pageName);
                }
            });
        });
    },

    // 初始化模态框
    initModals() {
        // 登录模态框
        const loginModal = document.getElementById('loginModal');

        // 关闭按钮
        const closeLoginModalBtn = document.getElementById('closeLoginModal');
        if (closeLoginModalBtn) {
            closeLoginModalBtn.addEventListener('click', () => {
                this.hideModal('loginModal');
            });
        }

        // 点击背景关闭模态框
        if (loginModal) {
            loginModal.addEventListener('click', (e) => {
                if (e.target === loginModal) {
                    this.hideModal('loginModal');
                }
            });
        }
    },

    // 初始化表单
    initForms() {
        // 登录表单
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const rememberMeCheckbox = document.getElementById('rememberMe');
            const rememberMe = rememberMeCheckbox ? rememberMeCheckbox.checked : false;

            try {
                await Auth.login(username, password);

                // 处理记住密码
                if (rememberMe) {
                    localStorage.setItem(APP_CONFIG.STORAGE_KEYS.REMEMBER_USERNAME, username);
                    localStorage.setItem(APP_CONFIG.STORAGE_KEYS.REMEMBER_PASSWORD, password);
                } else {
                    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.REMEMBER_USERNAME);
                    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.REMEMBER_PASSWORD);
                }

                this.hideModal('loginModal');
                UI.updateUserInfo();
                PageManager.switchPage(APP_CONFIG.PAGES.HOME);
            } catch (error) {
                // 错误已由Auth处理
            }
        });

      },

    // 显示模态框
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`模态框 #${modalId} 不存在`);
            return;
        }

        // 检查模态框是否已经可见，避免重复显示
        if (modal.classList.contains('active') && modal.classList.contains('visible')) {
            console.log(`模态框 #${modalId} 已经可见，跳过重复显示`);
            return;
        }

        console.log(`显示模态框 #${modalId}:`, modal);

        // 强制滚动到页面顶部
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;

        // 将模态框移到body的最后面，确保它在最上层
        if (modal.parentNode !== document.body) {
            document.body.appendChild(modal);
        }

        // 移除隐藏类，添加激活类
        modal.classList.remove('hidden', 'fade-out');
        modal.classList.add('active', 'visible');

        // 设置正常的显示样式
        modal.style.cssText = `
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 9999 !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: rgba(0, 0, 0, 0.8) !important;
            backdrop-filter: blur(5px) !important;
            transform: translateZ(0) !important;
            padding: 20px !important;
            box-sizing: border-box !important;
        `;

        // 强制模态框内容也可见
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.cssText = `
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                background: white !important;
                position: relative !important;
                z-index: 10000 !important;
                margin: auto !important;
                max-width: 90% !important;
                max-height: 90% !important;
                overflow: auto !important;
                border-radius: 8px !important;
            `;
        }

        // 防止页面滚动
        document.body.style.overflow = 'hidden';
        document.documentElement.style.overflow = 'hidden';

        // 强制重绘
        modal.offsetHeight;

        console.log(`模态框 #${modalId} 已强制显示，位置:`, {
            offsetTop: modal.offsetTop,
            offsetLeft: modal.offsetLeft,
            offsetWidth: modal.offsetWidth,
            offsetHeight: modal.offsetHeight,
            computedZIndex: window.getComputedStyle(modal).zIndex,
            position: window.getComputedStyle(modal).position
        });

        // 添加模态框点击事件监听（点击背景关闭）
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                console.log(`点击模态框背景，关闭 #${modalId}`);
                this.hideModal(modalId);
            }
        });

        // 添加ESC键关闭
        const handleEscape = (e) => {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                console.log(`按ESC键关闭模态框 #${modalId}`);
                this.hideModal(modalId);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

        // 延迟检查
        setTimeout(() => {
            const rect = modal.getBoundingClientRect();
            console.log(`模态框 #${modalId} 位置检查:`, {
                top: rect.top,
                left: rect.left,
                width: rect.width,
                height: rect.height,
                isVisible: rect.width > 0 && rect.height > 0
            });

            // 强制显示在视口中心
            if (rect.top < 0 || rect.left < 0) {
                modal.style.top = '0px';
                modal.style.left = '0px';
                console.log('强制调整模态框位置到视口顶部');
            }
        }, 100);
    },

    // 隐藏模态框
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`模态框 #${modalId} 不存在`);
            return;
        }

        console.log(`隐藏模态框 #${modalId}`);

        // 移除激活类，添加隐藏类
        modal.classList.remove('active', 'visible');
        modal.classList.add('hidden', 'fade-out');

        // 恢复页面滚动
        document.body.style.overflow = '';
        document.documentElement.style.overflow = '';

        // 立即隐藏元素（不等待动画）
        modal.style.display = 'none';
        modal.style.visibility = 'hidden';
        modal.style.opacity = '0';
        modal.style.zIndex = '';

        // 移除所有强制样式
        modal.style.cssText = '';

        // 移除模态框内容样式
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.cssText = '';
        }

        // 移除调试样式
        const debugStyles = document.getElementById('forceModalDebugStyles');
        if (debugStyles) {
            debugStyles.remove();
        }

        console.log(`模态框 #${modalId} 已完全隐藏`);
    },

    // 显示登录模态框
    showLoginModal() {
        // 防止重复调用和退出状态冲突
        if (isModalOperationInProgress || window.isLoggingOut) {
            console.log('登录模态框操作已在进行中或正在退出，跳过重复调用');
            return;
        }

        isModalOperationInProgress = true;
        this.showModal('loginModal');
        this.restoreRememberedCredentials();

        // 重置操作状态
        setTimeout(() => {
            isModalOperationInProgress = false;
        }, 200);
    },

    // 恢复记住的凭据
    restoreRememberedCredentials() {
        const rememberedUsername = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.REMEMBER_USERNAME);
        const rememberedPassword = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.REMEMBER_PASSWORD);

        if (rememberedUsername && rememberedPassword) {
            const usernameField = document.getElementById('username');
            const passwordField = document.getElementById('password');
            const rememberMeField = document.getElementById('rememberMe');

            if (usernameField) usernameField.value = rememberedUsername;
            if (passwordField) passwordField.value = rememberedPassword;
            if (rememberMeField) rememberMeField.checked = true;
        }
    },

    // 更新用户信息
    updateUserInfo() {
        if (AppState.user) {
            // 更新顶部用户信息
            const userName = document.getElementById('userName');
            const userInfo = document.querySelector('#userInfo .name');

            if (userName) userName.textContent = AppState.user.real_name;
            if (userInfo) userInfo.textContent = AppState.user.real_name;

            // 更新个人中心信息
            const profileName = document.getElementById('profileName');
            const profileRole = document.getElementById('profileRole');

            if (profileName) profileName.textContent = AppState.user.real_name;
            if (profileRole) {
                const roleMap = {
                    alumni: '校友',
                    teacher: '教师',
                    security: '保安',
                    admin: '管理员'
                };
                profileRole.textContent = roleMap[AppState.user.user_type] || '用户';
            }

            // 根据用户类型显示/隐藏审核管理入口
            const reviewManagementItem = document.getElementById('reviewManagement');
            if (reviewManagementItem) {
                if (AppState.user.user_type === 'teacher' || AppState.user.user_type === 'admin') {
                    reviewManagementItem.style.display = 'block';
                } else {
                    reviewManagementItem.style.display = 'none';
                }
            }

            // 根据用户类型显示快捷操作
            const quickVisit = document.getElementById('quickVisit');
            const studentExitApplication = document.getElementById('studentExitApplication');
            const parentApplyForExit = document.getElementById('parentApplyForExit');
            const teacherApproval = document.getElementById('teacherApproval');
            const quickFace = document.getElementById('quickFace');
            const quickQR = document.getElementById('quickQR');
            const studentExitQRCode = document.getElementById('studentExitQRCode');
            const quickAlumniCard = document.getElementById('quickAlumniCard');

            // 如果用户未登录，显示基础按钮
            if (!AppState.user) {
                // 未登录用户可以看到基础功能，点击时会提示登录
                if (quickVisit) quickVisit.style.display = 'block';
                if (quickFace) quickFace.style.display = 'block';
                if (studentExitApplication) studentExitApplication.style.display = 'block';

                // 隐藏需要登录的功能
                if (quickQR) quickQR.style.display = 'none';
                if (studentExitQRCode) studentExitQRCode.style.display = 'none';
                if (quickAlumniCard) quickAlumniCard.style.display = 'none';
                if (parentApplyForExit) parentApplyForExit.style.display = 'none';
                if (teacherApproval) teacherApproval.style.display = 'none';
                return;
            }

            // 已登录用户的显示逻辑
            // 快速申请 - 所有用户都可以看到
            if (quickVisit) {
                quickVisit.style.display = 'block';
            }

            // 人脸注册 - 所有用户都可以看到
            if (quickFace) {
                quickFace.style.display = 'block';
            }

            // 访问二维码 - 已登录用户可以看到
            if (quickQR) {
                quickQR.style.display = 'block';
            }

            // 电子校友卡 - 校友和学生用户可以看到
            if (quickAlumniCard) {
                if (["alumni", "student"].includes(AppState.user.user_type)) {
                    quickAlumniCard.style.display = 'block';
                } else {
                    quickAlumniCard.style.display = 'none';
                }
            }

            // 学生出校申请 - 学生、家长、教师可以看到
            if (studentExitApplication) {
                if (["student", "parent", "teacher"].includes(AppState.user.user_type)) {
                    studentExitApplication.style.display = 'block';
                } else {
                    studentExitApplication.style.display = 'none';
                }
            }

            // 离校验证码 - 学生、家长、教师可以看到
            if (studentExitQRCode) {
                if (["student", "parent", "teacher"].includes(AppState.user.user_type)) {
                    studentExitQRCode.style.display = 'block';
                } else {
                    studentExitQRCode.style.display = 'none';
                }
            }

            // 为孩子申请出校 - 家长可以看到
            if (parentApplyForExit) {
                if (AppState.user.user_type === 'parent') {
                    parentApplyForExit.style.display = 'block';
                } else {
                    parentApplyForExit.style.display = 'none';
                }
            }

            // 审批管理 - 教师、管理员可以看到
            if (teacherApproval) {
                if (AppState.user.user_type === 'teacher' || AppState.user.user_type === 'admin') {
                    teacherApproval.style.display = 'block';
                } else {
                    teacherApproval.style.display = 'none';
                }
            }
        }
    },

    // 隐藏加载动画
    hideLoading() {
        console.log('=== hideLoading 开始执行 ===');
        const loadingScreen = document.getElementById('loadingScreen');
        console.log('找到 loadingScreen:', !!loadingScreen);

        if (loadingScreen) {
            console.log('隐藏加载动画前的 display:', loadingScreen.style.display);
            console.log('隐藏加载动画前的 visibility:', loadingScreen.style.visibility);
            console.log('隐藏加载动画前的 opacity:', loadingScreen.style.opacity);

            // 使用多种方式强制隐藏
            loadingScreen.style.display = 'none';
            loadingScreen.style.visibility = 'hidden';
            loadingScreen.style.opacity = '0';
            loadingScreen.style.zIndex = '-9999';

            // 移除元素
            if (loadingScreen.parentNode) {
                loadingScreen.parentNode.removeChild(loadingScreen);
            }

            console.log('=== 加载动画已被强制移除 ===');
        } else {
            console.log('未找到 loadingScreen 元素');
            // 尝试查找所有可能的加载动画
            const allLoadingElements = document.querySelectorAll('[id*="loading"], [class*="loading"]');
            console.log('找到的加载相关元素:', allLoadingElements.length);
            allLoadingElements.forEach((el, index) => {
                console.log(`加载元素 ${index}:`, el.tagName, el.id, el.className);
                el.style.display = 'none';
                el.style.visibility = 'hidden';
            });
        }
    }
};

// 首页逻辑
const HomePage = {
    // 加载首页数据
    async load() {
        try {
            // 加载最近申请
            await this.loadRecentApplications();

            // 加载待审批申请
            await this.loadPendingApprovals();

            // 加载校历活动
            await this.loadCalendarEvents();

            // 绑定快捷操作事件
            this.bindQuickActions();
        } catch (error) {
            console.error('加载首页失败:', error);
        }
    },

    // 加载最近申请
    async loadRecentApplications() {
        try {
            // 检查是否已登录
            if (!AppState.isAuthenticated) {
                const container = document.getElementById('recentApplications');
                if (container) {
                    container.innerHTML = '<p class="text-center text-secondary">请先登录</p>';
                }
                return;
            }

            const container = document.getElementById('recentApplications');
            let allApplications = [];

            try {
                // 1. 加载访问申请
                let visitApiUrl = '/api/visits/applications?per_page=3';
                if (AppState.user.user_type === 'teacher' || AppState.user.user_type === 'admin') {
                    // 教师和管理员优先显示待审核的申请
                    visitApiUrl = '/api/visits/applications?status=pending&per_page=3';
                }

                const visitData = await Utils.request(visitApiUrl);
                if (visitData.applications && visitData.applications.length > 0) {
                    // 为访问申请添加类型标识
                    const visitApplications = visitData.applications.map(app => ({
                        ...app,
                        application_type: 'visit',
                        application_status: app.application_status || app.status
                    }));
                    allApplications = allApplications.concat(visitApplications);
                }
            } catch (error) {
                console.warn('加载访问申请失败:', error);
            }

            try {
                // 2. 加载学生出校申请
                console.log('正在加载学生出校申请...');
                // 添加时间戳防止缓存
                const timestamp = Date.now();
                const studentExitData = await Utils.request(`/api/student-exit/applications/recent?t=${timestamp}`);

                console.log('学生出校API响应:', studentExitData);

                if (studentExitData.success && studentExitData.applications && studentExitData.applications.length > 0) {
                    console.log('学生出校API响应数据:', {
                        success: studentExitData.success,
                        applicationCount: studentExitData.applications?.length || 0,
                        applications: studentExitData.applications
                    });

                    // 为学生出校申请添加类型标识
                    const studentExitApplications = studentExitData.applications.map(app => {
                        console.log('处理学生出校申请:', app);
                        return {
                            ...app,
                            application_type: 'student_exit',
                            application_status: app.status || app.application_status,
                            applicant_name: app.student_name || app.applicant_name,
                            visit_date: app.exit_date,
                            visit_time: app.exit_time,
                            purpose: app.reason
                        };
                    });
                    allApplications = allApplications.concat(studentExitApplications);
                    console.log(`成功添加${studentExitApplications.length}个学生出校申请`);
                } else {
                    console.log('没有找到学生出校申请或API返回格式错误');
                }
            } catch (error) {
                console.error('加载学生出校申请异常:', error);
            }

            // 如果没有任何申请
            if (allApplications.length === 0) {
                if (AppState.user.user_type === 'teacher' || AppState.user.user_type === 'admin') {
                    container.innerHTML = '<p class="text-center text-secondary">暂无待审核申请</p>';
                } else {
                    container.innerHTML = '<p class="text-center text-secondary">暂无申请记录</p>';
                }
                return;
            }

            // 按时间排序（最新的在前）
            allApplications.sort((a, b) => {
                const dateA = new Date(a.created_at || a.application_date || 0);
                const dateB = new Date(b.created_at || b.application_date || 0);
                return dateB - dateA;
            });

            console.log(`总共加载了${allApplications.length}个申请，开始渲染...`);

            // 按时间排序（最新的在前）
            allApplications.sort((a, b) => {
                const dateA = new Date(a.created_at || a.application_date || 0);
                const dateB = new Date(b.created_at || b.application_date || 0);
                return dateB - dateA;
            });

            // 只显示前3个
            const displayApplications = allApplications.slice(0, 3);
            console.log(`将显示前${displayApplications.length}个申请:`, displayApplications);

            if (displayApplications.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">暂无申请记录</p>';
            } else {
                const htmlContent = displayApplications.map(app => this.renderRecentApplication(app)).join('');
                console.log('生成的HTML内容:', htmlContent);
                container.innerHTML = htmlContent;
            }

            // 绑定点击事件（包括删除按钮）
            this.bindApplicationClickEvents();
        } catch (error) {
            console.error('加载最近申请失败:', error);
            const container = document.getElementById('recentApplications');
            if (container && error.message && error.message.includes('401')) {
                container.innerHTML = '<p class="text-center text-secondary">请先登录</p>';
            } else if (container) {
                container.innerHTML = '<p class="text-center text-secondary">加载失败</p>';
            }
        }
    },

    // 加载待审批申请
    async loadPendingApprovals() {
        try {
            console.log('加载待审批申请...');

            // 只有家长和老师才显示待审批申请
            if (!AppState.user || !['parent', 'teacher'].includes(AppState.user.user_type)) {
                const pendingSection = document.getElementById('pendingApprovalsSection');
                if (pendingSection) {
                    pendingSection.style.display = 'none';
                }
                return;
            }

            const data = await Utils.request('/api/student-exit/applications/pending-approval');
            const container = document.getElementById('pendingApprovalsList');
            const pendingSection = document.getElementById('pendingApprovalsSection');

            console.log('获取到的待审批申请数据:', data);

            if (!container || !pendingSection) {
                console.warn('待审批申请容器不存在');
                return;
            }

            const applications = data.applications || [];
            console.log(`找到${applications.length}个待审批申请`);

            if (applications.length === 0) {
                pendingSection.style.display = 'none';
                return;
            }

            // 显示待审批申请区域
            pendingSection.style.display = 'block';

            // 渲染待审批申请列表
            const htmlContent = applications.map(app => this.renderPendingApprovalApplication(app)).join('');
            container.innerHTML = htmlContent;

            // 绑定事件
            this.bindPendingApprovalEvents();

        } catch (error) {
            console.error('加载待审批申请失败:', error);
            const pendingSection = document.getElementById('pendingApprovalsSection');
            if (pendingSection) {
                pendingSection.style.display = 'none';
            }
        }
    },

    // 渲染待审批申请
    renderPendingApprovalApplication(app) {
        const userType = AppState.user.user_type;
        const isStudentExit = true; // 这个API只返回学生出校申请

        return `
            <div class="pending-approval-item" data-id="${app.id}">
                <div class="approval-content">
                    <div class="approval-header">
                        <span class="approval-type">学生出校申请</span>
                        <span class="approval-date">${Utils.formatDate(app.exit_date)}</span>
                    </div>
                    <div class="approval-details">
                        <p><strong>学生:</strong> ${app.student_name || '未知'}</p>
                        <p><strong>事由:</strong> ${app.exit_reason}</p>
                        <p><strong>时间:</strong> ${app.exit_time || ''}</p>
                    </div>
                </div>
                <div class="approval-actions">
                    ${userType === 'parent' ? `
                        <button class="btn btn-success btn-sm acknowledge-btn" data-id="${app.id}">
                            <i class="ri-check-line"></i> 确认知晓
                        </button>
                    ` : `
                        <button class="btn btn-success btn-sm approve-btn" data-id="${app.id}">
                            <i class="ri-check-line"></i> 批准
                        </button>
                        <button class="btn btn-danger btn-sm reject-btn" data-id="${app.id}">
                            <i class="ri-close-line"></i> 拒绝
                        </button>
                    `}
                </div>
            </div>
        `;
    },

    // 绑定待审批申请事件
    bindPendingApprovalEvents() {
        const userType = AppState.user.user_type;

        if (userType === 'parent') {
            // 家长确认事件
            document.querySelectorAll('.acknowledge-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const applicationId = parseInt(btn.dataset.id);
                    await this.parentAcknowledgeApproval(applicationId);
                });
            });
        } else if (userType === 'teacher') {
            // 老师批准/拒绝事件
            document.querySelectorAll('.approve-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const applicationId = parseInt(btn.dataset.id);
                    await this.teacherApproveApplication(applicationId);
                });
            });

            document.querySelectorAll('.reject-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const applicationId = parseInt(btn.dataset.id);
                    await this.teacherRejectApplication(applicationId);
                });
            });
        }
    },

    // 家长确认待审批申请
    async parentAcknowledgeApproval(applicationId) {
        try {
            const data = await Utils.request(`/api/student-exit/applications/${applicationId}/acknowledge`, {
                method: 'POST',
                body: JSON.stringify({
                    note: '家长已知晓并同意此申请'
                })
            });

            if (data.success || data.message) {
                Utils.showToast(data.message || '已确认知晓此申请', 'success');
                // 重新加载待审批申请
                await this.loadPendingApprovals();
                // 重新加载最近申请
                await this.loadRecentApplications();
            } else {
                Utils.showToast(data.error || '确认失败', 'error');
            }
        } catch (error) {
            console.error('家长确认申请失败:', error);
            Utils.showToast('确认失败，请重试', 'error');
        }
    },

    // 老师批准申请
    async teacherApproveApplication(applicationId) {
        try {
            const data = await Utils.request(`/api/student-exit/applications/${applicationId}/approve`, {
                method: 'POST',
                body: JSON.stringify({
                    action: 'approve',
                    note: '班主任批准'
                })
            });

            if (data.success || data.message) {
                Utils.showToast(data.message || '已批准申请', 'success');
                // 重新加载待审批申请
                await this.loadPendingApprovals();
                // 重新加载最近申请
                await this.loadRecentApplications();
            } else {
                Utils.showToast(data.error || '批准失败', 'error');
            }
        } catch (error) {
            console.error('老师批准申请失败:', error);
            Utils.showToast('批准失败，请重试', 'error');
        }
    },

    // 老师拒绝申请
    async teacherRejectApplication(applicationId) {
        try {
            const data = await Utils.request(`/api/student-exit/applications/${applicationId}/approve`, {
                method: 'POST',
                body: JSON.stringify({
                    action: 'reject',
                    note: '班主任拒绝'
                })
            });

            if (data.success || data.message) {
                Utils.showToast(data.message || '已拒绝申请', 'success');
                // 重新加载待审批申请
                await this.loadPendingApprovals();
                // 重新加载最近申请
                await this.loadRecentApplications();
            } else {
                Utils.showToast(data.error || '拒绝失败', 'error');
            }
        } catch (error) {
            console.error('老师拒绝申请失败:', error);
            Utils.showToast('拒绝失败，请重试', 'error');
        }
    },

    // 加载校历活动
    async loadCalendarEvents() {
        try {
            console.log('加载校历活动...');
            const data = await Utils.request('/api/public/calendar/events');
            const container = document.getElementById('eventsContainer');
            const prevBtn = document.getElementById('eventsPrevBtn');
            const nextBtn = document.getElementById('eventsNextBtn');
            const indicatorsContainer = document.getElementById('eventsIndicators');

            if (!data.events || data.events.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">暂无校园活动</p>';
                if (prevBtn) prevBtn.style.display = 'none';
                if (nextBtn) nextBtn.style.display = 'none';
                if (indicatorsContainer) indicatorsContainer.innerHTML = '';
                return;
            }

            // 只显示当前日期之后的活动
            const today = new Date();
            today.setHours(0, 0, 0, 0); // 设置为当天的开始时间

            const futureEvents = data.events
                .map(event => ({ ...event, eventDate: new Date(event.start_date) }))
                .filter(event => {
                    // 过滤掉今天之前的活动，保留今天及之后的活动
                    return event.eventDate >= today;
                })
                .sort((a, b) => a.eventDate - b.eventDate); // 按日期升序排列

            if (futureEvents.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">暂无即将到来的校园活动</p>';
                if (prevBtn) prevBtn.style.display = 'none';
                if (nextBtn) nextBtn.style.display = 'none';
                if (indicatorsContainer) indicatorsContainer.innerHTML = '';
                return;
            }

            // 显示最多最近的5个活动
            const eventsToShow = futureEvents.slice(0, 5);
            container.innerHTML = eventsToShow.map(event => this.renderCalendarEvent(event)).join('');

            // 绑定轮播控制
            this.bindCarouselControls();

            console.log(`成功加载 ${eventsToShow.length} 个即将到来的校历活动`);

        } catch (error) {
            console.error('加载校历活动失败:', error);
            const container = document.getElementById('eventsContainer');
            if (container) {
                container.innerHTML = '<p class="text-center text-secondary">加载校园活动失败</p>';
            }
        }
    },

    // 渲染校历活动项
    renderCalendarEvent(event) {
        const eventDate = new Date(event.start_date);
        const isToday = eventDate.toDateString() === new Date().toDateString();
        const daysUntil = Math.ceil((eventDate - new Date()) / (1000 * 60 * 60 * 24));

        const eventTypeMap = {
            'anniversary': { icon: 'ri-calendar-2-line', color: '#1976d2', label: '校庆' },
            'festival': { icon: 'ri-star-line', color: '#f59e0b', label: '节日' },
            'activity': { icon: 'ri-flag-line', color: '#10b981', label: '活动' },
            'club': { icon: 'ri-team-line', color: '#8b5cf6', label: '社团' },
            'holiday': { icon: 'ri-rest-time-line', color: '#ef4444', label: '假期' },
            'exam': { icon: 'ri-file-text-line', color: '#6366f1', label: '考试' },
            'meeting': { icon: 'ri-group-line', color: '#84cc16', label: '会议' }
        };

        const typeInfo = eventTypeMap[event.event_type] || { icon: 'ri-calendar-line', color: '#6b7280', label: '活动' };
        const dateStr = Utils.formatDate(event.start_date);

        return `
            <div class="event-item ${isToday ? 'today' : ''}">
                <div class="event-icon" style="color: ${typeInfo.color}">
                    <i class="${typeInfo.icon}"></i>
                </div>
                <div class="event-content">
                    <div class="event-header">
                        <h4 class="event-title">${event.title}</h4>
                        <span class="event-type" style="background-color: ${typeInfo.color}20; color: ${typeInfo.color}">${typeInfo.label}</span>
                    </div>
                    <div class="event-meta">
                        <span class="event-date">
                            <i class="ri-calendar-line"></i>
                            ${dateStr}
                        </span>
                        ${!event.all_day ? `
                            <span class="event-time">
                                <i class="ri-time-line"></i>
                                ${event.start_time} - ${event.end_time}
                            </span>
                        ` : ''}
                        ${daysUntil === 0 ? '<span class="event-today">今天</span>' :
                          daysUntil > 0 ? `<span class="event-countdown">${daysUntil}天后</span>` : ''}
                    </div>
                    ${event.description ? `<p class="event-description">${event.description}</p>` : ''}
                </div>
            </div>
        `;
    },

    // 绑定轮播控制
    bindCarouselControls() {
        const container = document.getElementById('eventsContainer');
        const prevBtn = document.getElementById('eventsPrevBtn');
        const nextBtn = document.getElementById('eventsNextBtn');

        if (!container || !prevBtn || !nextBtn) return;

        let currentIndex = 0;
        const items = container.querySelectorAll('.event-item');
        if (items.length === 0) return;

        const showItem = (index) => {
            items.forEach((item, i) => {
                item.style.display = i === index ? 'block' : 'none';
            });

            // 更新指示器
            const indicatorsContainer = document.getElementById('eventsIndicators');
            if (indicatorsContainer) {
                const indicators = indicatorsContainer.querySelectorAll('.indicator');
                indicators.forEach((indicator, i) => {
                    indicator.classList.toggle('active', i === index);
                });
            }
        };

        prevBtn.addEventListener('click', () => {
            currentIndex = (currentIndex - 1 + items.length) % items.length;
            showItem(currentIndex);
        });

        nextBtn.addEventListener('click', () => {
            currentIndex = (currentIndex + 1) % items.length;
            showItem(currentIndex);
        });

        // 自动轮播
        setInterval(() => {
            currentIndex = (currentIndex + 1) % items.length;
            showItem(currentIndex);
        }, 5000);

        // 初始显示第一个
        showItem(0);
    },

    // 渲染最近申请卡片
    renderRecentApplication(app) {
        const isTeacherOrAdmin = AppState.user.user_type === 'teacher' || AppState.user.user_type === 'admin';
        // 根据申请类型选择正确的状态函数
        const isStudentExit = app.application_type === 'student_exit';
        const statusClass = isStudentExit ?
            StudentExitUtils.getStatusClass(app.application_status) :
            Utils.getStatusClass(app.application_status);
        const statusText = isStudentExit ?
            StudentExitUtils.getStatusText(app.application_status) :
            Utils.getStatusText(app.application_status);

        // 检查是否可以删除（只能删除自己的申请，且状态为pending或cancelled）
        const canDelete = AppState.user &&
                           (AppState.user.id === app.applicant_id || AppState.user.id === app.user_id) &&
                           ['pending', 'cancelled'].includes(app.application_status);

        // 根据申请类型确定显示信息
        const applicationTypeText = isStudentExit ? '学生出校' : '访问申请';
        const displayDate = isStudentExit ? Utils.formatDate(app.exit_date) : Utils.formatDate(app.visit_date);
        const displayPurpose = isStudentExit ? app.reason : app.visit_purpose;
        const displayTime = isStudentExit ? (app.exit_time || '') : (app.visit_time || '');

        // 获取详细的审批状态
        const approvalStatuses = this.getDetailedApprovalStatus(app, isStudentExit);

        return `
            <div class="recent-application-container" data-id="${app.id}" data-type="${app.application_type || 'visit'}">
                <div class="application-item recent-application-card ${isTeacherOrAdmin ? 'clickable' : ''}"
                     data-id="${app.id}" data-status="${app.application_status}" data-type="${app.application_type || 'visit'}">

                    <div class="application-content">
                        <div class="application-header">
                            <span class="application-type">${applicationTypeText}</span>
                            <span class="application-date">${displayDate}</span>
                            ${displayTime ? `<span class="application-time">${displayTime}</span>` : ''}
                        </div>
                        <div class="application-purpose">${displayPurpose}</div>
                        <div class="application-target" style="font-weight: 500; color: #333;">
                            ${isStudentExit ?
                                (app.applicant_name ? `申请人: ${app.applicant_name}` :
                                 app.student_name ? `学生: ${app.student_name}` :
                                 '申请人信息') :
                                (isTeacherOrAdmin && app.applicant ?
                                    `申请人: ${app.applicant.real_name}` :
                                    (app.target_person ? `拜访对象: ${app.target_person}` :
                                     app.visitor_name ? `访客: ${app.visitor_name}` : '访客信息')
                                )
                            }
                        </div>
                    </div>

                    <div class="application-statuses">
                        <div class="application-status ${statusClass}">
                            ${statusText}
                        </div>
                        ${approvalStatuses.teacherStatus}
                        ${approvalStatuses.parentStatus}
                        ${isTeacherOrAdmin && ['pending', 'parent_approved'].includes(app.application_status) && app.can_approve ? `
                        <div class="quick-review-actions">
                            <button class="btn btn-success btn-sm quick-approve-btn" data-id="${app.id}">
                                <i class="ri-check-line"></i>
                                通过
                            </button>
                            <button class="btn btn-danger btn-sm quick-reject-btn" data-id="${app.id}">
                                <i class="ri-close-line"></i>
                                拒绝
                            </button>
                        </div>
                        ` : ''}
                        ${canDelete ? `
                        <button class="btn btn-danger btn-sm delete-application-btn" data-id="${app.id}">
                            <i class="ri-delete-bin-line"></i>
                        </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    },

    // 获取详细的审批状态
    getDetailedApprovalStatus(app, isStudentExit) {
        let teacherStatus = '';
        let parentStatus = '';

        if (isStudentExit) {
            // 学生出校申请的状态显示
            const teacherApprovalStatus = app.teacher_approval_status || 'pending';
            const parentApprovalStatus = app.parent_approval_status || 'pending';
            const applicationStatus = app.application_status || 'pending';

            teacherStatus = `
                <div class="status-indicator">
                    <span class="status-dot ${teacherApprovalStatus === 'approved' ? 'approved' : 'pending'}"></span>
                    <span>老师${teacherApprovalStatus === 'approved' ? '已通过' : teacherApprovalStatus === 'rejected' ? '已拒绝' : '未审批'}</span>
                </div>
            `;

            // 只有老师审批通过后才显示家长状态
            if (teacherApprovalStatus === 'approved') {
                parentStatus = `
                    <div class="status-indicator">
                        <span class="status-dot ${parentApprovalStatus === 'approved' ? 'approved' : parentApprovalStatus === 'rejected' ? 'rejected' : 'pending'}"></span>
                        <span>家长${parentApprovalStatus === 'approved' ? '已同意' : parentApprovalStatus === 'rejected' ? '已拒绝' : '未确认'}</span>
                    </div>
                `;
            }
        } else {
            // 访问申请的状态显示
            const applicationStatus = app.application_status || 'pending';

            teacherStatus = `
                <div class="status-indicator">
                    <span class="status-dot ${applicationStatus === 'approved' ? 'approved' : applicationStatus === 'rejected' ? 'rejected' : 'pending'}"></span>
                    <span>老师${applicationStatus === 'approved' ? '已通过' : applicationStatus === 'rejected' ? '已拒绝' : '未审批'}</span>
                </div>
            `;
        }

        return { teacherStatus, parentStatus };
    },

    // 绑定申请卡片点击事件
    bindApplicationClickEvents() {
        // 卡片点击事件 - 进入审核页面并筛选对应状态
        document.querySelectorAll('.recent-application-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // 如果点击的是按钮，不触发卡片点击事件
                if (e.target.closest('.quick-review-actions') ||
                    e.target.closest('.delete-action')) {
                    return;
                }

                const status = card.dataset.status;
                this.goToReviewPage(status);
            });
        });

        // 快速通过按钮
        document.querySelectorAll('.quick-approve-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.dataset.id;
                await this.quickReviewApplication(id, true);
            });
        });

        // 快速拒绝按钮
        document.querySelectorAll('.quick-reject-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.dataset.id;

                // 简单的拒绝理由输入
                const reason = prompt('请输入拒绝理由:');
                if (!reason || !reason.trim()) {
                    Utils.showToast('请输入拒绝理由', 'warning');
                    return;
                }

                await this.quickReviewApplication(id, false, reason.trim());
            });
        });

        // 删除申请按钮
        document.querySelectorAll('.delete-application-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.dataset.id;
                await this.deleteApplication(id);
            });
        });
    },

    // 快速审核申请
    async quickReviewApplication(id, approve, note = '') {
        try {
            // 需要确定申请类型，使用不同的API端点
            const applicationElement = document.querySelector(`[data-id="${id}"]`);
            const applicationType = applicationElement?.dataset.type || 'visit';

            let endpoint;
            if (applicationType === 'student_exit') {
                endpoint = `/api/student-exit/applications/${id}/approve`;
            } else {
                endpoint = `/api/visits/applications/${id}/approve`;
            }

            await Utils.request(endpoint, {
                method: 'POST',
                body: JSON.stringify({
                    approve: approve,
                    note: note
                })
            });

            Utils.showToast(`申请已${approve ? '通过' : '拒绝'}`, 'success');

            // 重新加载最近申请，强制刷新缓存
            await this.loadRecentApplications();

            // 如果在审核管理页面，也刷新审核列表
            if (typeof ReviewPage !== 'undefined' && ReviewPage.loadApplications) {
                await ReviewPage.loadApplications();
            }
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 绑定左滑删除事件
    
    // 删除申请
    async deleteApplication(applicationId, container = null) {
        try {
            // 如果没有提供container，通过ID查找
            if (!container) {
                container = document.querySelector(`.recent-application-container[data-id="${applicationId}"]`);
            }

            if (!container) {
                Utils.showToast('找不到要删除的申请记录', 'error');
                return;
            }

            // 确认删除
            const confirmed = confirm('确定要删除这个申请记录吗？此操作不可恢复。');
            if (!confirmed) {
                return;
            }

            Utils.showLoading('删除申请中...');

            await Utils.request(`/api/visits/applications/${applicationId}/cancel`, {
                method: 'POST'
            });

            Utils.showToast('申请已删除', 'success');

            // 添加删除动画
            const card = container.querySelector('.recent-application-card');
            card.style.transition = 'all 0.3s ease';
            card.style.transform = 'translateX(-100%) scale(0)';
            card.style.opacity = '0';

            // 移除元素
            setTimeout(() => {
                container.remove();

                // 如果没有申请了，显示空状态
                const remainingApps = document.querySelectorAll('.recent-application-container');
                if (remainingApps.length === 0) {
                    const container = document.getElementById('recentApplications');
                    if (container) {
                        container.innerHTML = '<p class="text-center text-secondary">暂无申请记录</p>';
                    }
                }
            }, 300);

        } catch (error) {
            Utils.showToast(error.message, 'error');
            // 恢复卡片状态
            const card = container.querySelector('.recent-application-card');
            card.style.transform = 'translateX(0)';
            card.style.opacity = '1';
        } finally {
            Utils.hideLoading();
        }
    },

    // 跳转到审核页面
    goToReviewPage(statusFilter = 'pending') {
        // 检查用户权限 - 学生账号不能访问审批管理
        if (AppState.user && AppState.user.user_type === 'student') {
            Utils.showToast('学生账号没有权限访问审批管理页面', 'error');
            return;
        }

        // 隐藏所有页面
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });

        // 显示审核页面
        const reviewPage = document.getElementById('reviewPage');
        if (reviewPage) {
            reviewPage.classList.add('active');

            // 加载审核页面并设置筛选器
            ReviewPage.currentFilter = statusFilter;
            ReviewPage.load();

            // 设置对应的筛选标签为激活状态
            setTimeout(() => {
                document.querySelectorAll('.filter-tab').forEach(tab => {
                    tab.classList.remove('active');
                    if (tab.dataset.status === statusFilter) {
                        tab.classList.add('active');
                    }
                });
            }, 100);
        }
    },

    // 绑定快捷操作
    bindQuickActions() {
        // 防止重复绑定
        if (APP_CONFIG.EVENTS_BOUND.QUICK_ACTIONS) {
            console.log('=== 快捷操作已绑定，跳过 ===');
            return;
        }

        console.log('=== 开始绑定快捷操作 ===');

        // 快速申请
        const quickVisit = document.getElementById('quickVisit');
        console.log('quickVisit元素:', quickVisit);
        if (quickVisit) {
            quickVisit.addEventListener('click', (e) => {
                console.log('quickVisit点击事件触发');
                e.preventDefault();
                e.stopPropagation();
                if (!Auth.checkAuth()) {
                    Utils.showToast('请先登录', 'warning');
                    PageManager.switchPage(APP_CONFIG.PAGES.LOGIN);
                    return;
                }
                PageManager.switchPage(APP_CONFIG.PAGES.VISIT);
            });
            console.log('quickVisit事件绑定成功');
        }

        // 人脸注册
        const quickFace = document.getElementById('quickFace');
        console.log('quickFace元素:', quickFace);
        if (quickFace) {
            quickFace.addEventListener('click', (e) => {
                console.log('quickFace点击事件触发');
                e.preventDefault();
                e.stopPropagation();
                PageManager.switchPage(APP_CONFIG.PAGES.FACE);
            });
            console.log('quickFace事件绑定成功');
        }

        // 我的二维码
        const quickQR = document.getElementById('quickQR');
        console.log('quickQR元素:', quickQR);
        if (quickQR) {
            quickQR.addEventListener('click', async (e) => {
                console.log('quickQR点击事件触发');
                e.preventDefault();
                e.stopPropagation();
                if (Auth.checkAuth()) {
                    await FacePage.showQRCode();
                } else {
                    Utils.showToast('请先登录', 'error');
                }
            });
            console.log('quickQR事件绑定成功');
        }

        // 离校验证码
        const studentExitQRCode = document.getElementById('studentExitQRCode');
        console.log('studentExitQRCode元素:', studentExitQRCode);
        if (studentExitQRCode) {
            studentExitQRCode.addEventListener('click', async (e) => {
                console.log('studentExitQRCode点击事件触发');
                e.preventDefault();
                e.stopPropagation();
                if (Auth.checkAuth()) {
                    await HomePage.showStudentExitQRCode();
                } else {
                    Utils.showToast('请先登录', 'error');
                }
            });
            console.log('studentExitQRCode事件绑定成功');
        }

        // 电子校友卡
        const quickAlumniCard = document.getElementById('quickAlumniCard');
        console.log('quickAlumniCard元素:', quickAlumniCard);
        if (quickAlumniCard) {
            quickAlumniCard.addEventListener('click', (e) => {
                console.log('quickAlumniCard点击事件触发');
                e.preventDefault();
                e.stopPropagation();
                PageManager.switchPage(APP_CONFIG.PAGES.ALUMNI_CARD);
            });
            console.log('quickAlumniCard事件绑定成功');
        }

        // 学生出校申请
        const studentExitApplication = document.getElementById('studentExitApplication');
        console.log('studentExitApplication元素:', studentExitApplication);
        if (studentExitApplication) {
            studentExitApplication.addEventListener('click', (e) => {
                console.log('studentExitApplication点击事件触发');
                e.preventDefault();
                e.stopPropagation();
                if (!Auth.checkAuth()) {
                    Utils.showToast('请先登录', 'warning');
                    PageManager.switchPage(APP_CONFIG.PAGES.LOGIN);
                    return;
                }

                // 显示模态框
                UI.showModal('studentExitApplicationModal');

                // 重置表单状态并加载学生信息
                if (window.studentExitApp) {
                    setTimeout(() => {
                        console.log('开始重置表单状态...');
                        window.studentExitApp.resetFormState('student');
                        window.studentExitApp.loadAvailableStudents('student');

                        // 延迟更长时间确保HomePage对象已初始化
                        setTimeout(() => {
                            console.log('检查HomePage对象:', typeof HomePage);
                            console.log('检查bindStudentExitFormEvents函数:', typeof HomePage?.bindStudentExitFormEvents);
                            console.log('HomePage对象的所有方法:', Object.getOwnPropertyNames(HomePage));
                            console.log('HomePage.bindStudentExitFormEvents:', HomePage.bindStudentExitFormEvents);

                            // 重新绑定表单提交事件
                            if (typeof HomePage === 'object' && typeof HomePage.bindStudentExitFormEvents === 'function') {
                                console.log('调用bindStudentExitFormEvents函数...');
                                HomePage.bindStudentExitFormEvents();
                            } else {
                                console.warn('HomePage.bindStudentExitFormEvents 函数不存在，跳过绑定');
                            }
                        }, 200);
                    }, 100);
                }
            });
            console.log('studentExitApplication事件绑定成功');
        }

        // 为孩子申请出校
        const parentApplyForExit = document.getElementById('parentApplyForExit');
        console.log('parentApplyForExit元素:', parentApplyForExit);
        if (parentApplyForExit) {
            parentApplyForExit.addEventListener('click', (e) => {
                console.log('parentApplyForExit点击事件触发');
                e.preventDefault();
                e.stopPropagation();

                // 显示模态框
                UI.showModal('parentApplyForExitModal');

                // 加载学生列表到家长申请表单
                if (window.studentExitApp) {
                    setTimeout(() => {
                        window.studentExitApp.loadAvailableStudents('parent');
                    }, 100);
                }
            });
            console.log('parentApplyForExit事件绑定成功');
        }

        // 审批管理
        const teacherApproval = document.getElementById('teacherApproval');
        console.log('teacherApproval元素:', teacherApproval);
        if (teacherApproval) {
            teacherApproval.addEventListener('click', (e) => {
                console.log('teacherApproval点击事件触发');
                e.preventDefault();
                e.stopPropagation();

                // 检查ReviewPage是否已加载，如果未加载则等待或使用替代方法
                if (typeof ReviewPage !== 'undefined' && ReviewPage.goToReviewPage) {
                    console.log('使用ReviewPage.goToReviewPage跳转');
                    ReviewPage.goToReviewPage('pending');
                } else {
                    console.log('ReviewPage未加载，使用替代跳转方法');
                    // 替代方法：手动实现审批页面跳转逻辑
                    HomePage.fallbackToReviewPage('pending');
                }
            });
            console.log('teacherApproval事件绑定成功');
        }

        // 标记为已绑定
        APP_CONFIG.EVENTS_BOUND.QUICK_ACTIONS = true;
        console.log('=== 快捷操作绑定完成 ===');
    },

    // 审批页面跳转的备用方法（用于处理代码加载顺序问题）
    fallbackToReviewPage(statusFilter = 'pending') {
        console.log('使用备用方法跳转到审批页面，状态筛选:', statusFilter);

        // 检查用户权限 - 学生账号不能访问审批管理
        if (AppState.user && AppState.user.user_type === 'student') {
            Utils.showToast('学生账号没有权限访问审批管理页面', 'error');
            return;
        }

        // 隐藏所有页面
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });

        // 显示审核页面
        const reviewPage = document.getElementById('reviewPage');
        if (reviewPage) {
            reviewPage.classList.add('active');
            Utils.showToast('正在加载审批数据...', 'success');

            // 设置初始筛选状态
            if (typeof ReviewPage !== 'undefined') {
                ReviewPage.currentFilter = statusFilter;
                ReviewPage.load();
            } else {
                // 如果ReviewPage还没加载，尝试延迟加载
                setTimeout(() => {
                    if (typeof ReviewPage !== 'undefined') {
                        ReviewPage.currentFilter = statusFilter;
                        ReviewPage.load();
                    } else {
                        // 最后的备用方案：直接显示页面提示用户稍等
                        console.warn('ReviewPage对象仍未加载，请刷新页面重试');
                        Utils.showToast('页面加载中，请稍后...', 'warning');
                    }
                }, 500);
            }

            // 设置对应的筛选标签为激活状态
            setTimeout(() => {
                document.querySelectorAll('.filter-tab').forEach(tab => {
                    tab.classList.remove('active');
                    if (tab.dataset.status === statusFilter) {
                        tab.classList.add('active');
                    }
                });
            }, 100);

            // 更新底部导航栏状态
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            const reviewNav = document.querySelector('[data-page="reviewPage"]');
            if (reviewNav) {
                reviewNav.classList.add('active');
            }

            // 更新页面标题
            const pageTitle = document.querySelector('.page-title');
            if (pageTitle) {
                pageTitle.textContent = '审批管理';
            }

            console.log('备用方法跳转审批页面完成');
        } else {
            console.error('找不到审批页面元素');
            Utils.showToast('页面加载失败，请刷新重试', 'error');
        }
    },

    // 显示学生离校验证码
    async showStudentExitQRCode() {
        try {
            console.log('=== 开始显示学生离校验证码 ===');
            Utils.showLoading('生成离校验证码...');

            // 检查用户类型
            if (!["student", "parent", "teacher"].includes(AppState.user.user_type)) {
                Utils.showToast('只有学生、家长、教师可以查看离校验证码', 'warning');
                return;
            }

            // 获取已通过的学生出校申请（今天的）
            let apiUrl = '/api/student-exit/applications';
            let params = new URLSearchParams({
                'status': 'approved',
                'limit': '10'  // 获取更多记录以筛选当天的
            });

            if (AppState.user.user_type === 'student') {
                params.append('student_id', AppState.user.id);
            }

            console.log('请求参数:', params.toString());

            const response = await fetch(`${apiUrl}?${params}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('获取出校申请失败');
            }

            const data = await response.json();
            console.log('获取到的申请数据:', data);
            console.log('data.success:', data.success);
            console.log('data.applications:', data.applications);
            console.log('data.applications.length:', data.applications ? data.applications.length : 'undefined');

            if (!data.applications || data.applications.length === 0) {
                console.log('条件检查失败，显示提示信息');
                console.log('!data.applications =', !data.applications);
                console.log('data.applications.length === 0 =', data.applications ? data.applications.length === 0 : 'data.applications is undefined');
                Utils.showToast('暂无已通过的出校申请', 'info');
                return;
            }

            // 筛选出今天的申请
            const today = new Date().toISOString().split('T')[0];
            console.log('今天的日期:', today);
            console.log('所有申请的详细数据:', data.applications);

            const todayApplications = data.applications.filter(app => {
                // 更灵活的日期比较
                let isToday = false;
                if (app.exit_date) {
                    // 如果已经是YYYY-MM-DD格式，直接比较
                    if (app.exit_date.includes('-')) {
                        isToday = app.exit_date === today;
                    } else {
                        // 如果是其他格式，尝试转换
                        try {
                            const appDate = new Date(app.exit_date);
                            isToday = appDate.toISOString().split('T')[0] === today;
                        } catch (e) {
                            console.warn('日期格式错误:', app.exit_date);
                        }
                    }
                }

                console.log('检查申请:', {
                    id: app.id,
                    exit_date: app.exit_date,
                    application_status: app.application_status,
                    is_today: isToday,
                    is_approved: app.application_status === 'approved'
                });
                return isToday && app.application_status === 'approved';
            });

            console.log('今天的申请:', todayApplications);

            // 临时调试：暂时不限制日期，显示所有已批准的申请
            if (todayApplications.length === 0) {
                console.log('没有今天的申请，尝试使用所有已批准的申请进行调试');
                // 暂时使用第一个已批准的申请进行调试
                const allApproved = data.applications.filter(app => app.application_status === 'approved');
                if (allApproved.length > 0) {
                    console.log('使用第一个已批准的申请进行调试:', allApproved[0]);
                    todayApplications.push(allApproved[0]);
                }
            }

            if (todayApplications.length === 0) {
                console.log('没有找到任何已批准的申请，显示提示信息');
                Utils.showToast('没有已通过的离校申请', 'info');
                return;
            }

            // 取第一个申请
            const application = todayApplications[0];
            console.log('选择的申请:', application);

            // 获取该申请的二维码
            try {
                console.log('开始获取二维码，申请ID:', application.id);
                const qrResponse = await Utils.request(`/api/student-exit/applications/${application.id}/qr-code`);
                console.log('二维码响应:', qrResponse);

                if (!qrResponse.qr_code && !qrResponse.verification_code) {
                    console.log('二维码响应数据为空:', qrResponse);
                    Utils.showToast('无法生成验证码，请稍后重试', 'error');
                    return;
                }

                console.log('准备显示二维码模态框');
                // 继续处理二维码显示...
                try {
                    HomePage.displayQRCodeModal(application, qrResponse);
                    console.log('二维码模态框显示调用完成');
                } catch (modalError) {
                    console.error('显示模态框时出错:', modalError);
                    Utils.showToast('显示验证码失败: ' + modalError.message, 'error');
                }

            } catch (qrError) {
                console.error('获取二维码失败:', qrError);
                Utils.showToast('获取二维码失败: ' + (qrError.message || '未知错误'), 'error');
                return;
            }

        } catch (error) {
            console.error('生成离校验证码失败:', error);
            Utils.showToast('生成验证码失败，请重试', 'error');
        } finally {
            Utils.hideLoading();
        }
    },

    // 显示二维码模态框
    displayQRCodeModal(application, qrResponse) {
        console.log('=== 开始创建二维码模态框 ===');
        console.log('申请数据:', application);
        console.log('二维码数据:', qrResponse);

        try {
            // 生成QR码容器
            const qrContainer = document.createElement('div');
            qrContainer.style.textAlign = 'center';
            qrContainer.style.padding = '20px';

            // 显示验证码
            const verificationCodeDiv = document.createElement('div');
            verificationCodeDiv.style.fontSize = '24px';
            verificationCodeDiv.style.fontWeight = 'bold';
            verificationCodeDiv.style.color = '#333';
            verificationCodeDiv.style.marginBottom = '20px';
            verificationCodeDiv.style.letterSpacing = '4px';
            verificationCodeDiv.textContent = qrResponse.verification_code || '暂无验证码';

            // 创建二维码容器
            const qrCodeCanvas = document.createElement('canvas');
            qrCodeCanvas.id = 'studentExitQRCodeDisplay';
            qrCodeCanvas.style.width = '200px';
            qrCodeCanvas.style.height = '200px';
            qrCodeCanvas.style.marginBottom = '20px';

            const infoDiv = document.createElement('div');
            infoDiv.style.fontSize = '14px';
            infoDiv.style.color = '#666';
            infoDiv.innerHTML = `
                <p><strong>学生：</strong>${application.student_name || '未知'}</p>
                <p><strong>出校日期：</strong>${application.exit_date || ''}</p>
                <p><strong>出校时间：</strong>${application.exit_time_start || ''}</p>
                <p><strong>状态：</strong><span style="color: #28a745;">已通过</span></p>
                <p style="color: #ff9800; font-size: 12px;">验证码有效期至 ${qrResponse.expires_at ? new Date(qrResponse.expires_at).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'}) : '当天23:59'}</p>
            `;

            qrContainer.appendChild(verificationCodeDiv);
            qrContainer.appendChild(qrCodeCanvas);
            qrContainer.appendChild(infoDiv);

            // 创建模态框
            const modal = document.createElement('div');
            modal.className = 'modal active visible';
            modal.id = 'studentExitQRModal';
            modal.style.cssText = `
                display: flex !important;
                visibility: visible !important;
                opacity: 1 !important;
                z-index: 9999 !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                background: rgba(0, 0, 0, 0.8) !important;
                backdrop-filter: blur(5px) !important;
                align-items: center !important;
                justify-content: center !important;
            `;

            const modalContent = document.createElement('div');
            modalContent.className = 'modal-content';
            modalContent.style.cssText = `
                background: white;
                border-radius: 8px;
                max-width: 400px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
                padding: 0;
                position: relative;
            `;

            const modalHeader = document.createElement('div');
            modalHeader.className = 'modal-header';
            modalHeader.style.cssText = `
                padding: 20px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            `;

            const modalTitle = document.createElement('h3');
            modalTitle.textContent = '离校验证码';
            modalTitle.style.cssText = `
                margin: 0;
                font-size: 18px;
                color: #333;
            `;

            const closeButton = document.createElement('button');
            closeButton.innerHTML = '×';
            closeButton.style.cssText = `
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #666;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
            `;
            closeButton.onclick = () => {
                document.body.removeChild(modal);
            };

            modalHeader.appendChild(modalTitle);
            modalHeader.appendChild(closeButton);

            const modalBody = document.createElement('div');
            modalBody.className = 'modal-body';
            modalBody.style.cssText = `
                padding: 20px;
            `;
            modalBody.appendChild(qrContainer);

            modalContent.appendChild(modalHeader);
            modalContent.appendChild(modalBody);
            modal.appendChild(modalContent);

            console.log('模态框创建完成，准备添加到页面');
            document.body.appendChild(modal);
            console.log('模态框已添加到页面');

            // 生成QR码
            setTimeout(async () => {
                if (typeof QRCode !== 'undefined') {
                    try {
                        // 使用后端返回的二维码数据生成QR码
                        const qrData = qrResponse.qr_code ? JSON.parse(qrResponse.qr_code) : {
                            type: 'student_exit',
                            id: application.id,
                            student_name: application.student_name,
                            verification_code: qrResponse.verification_code,
                            exit_date: application.exit_date
                        };

                        console.log('生成QR码，数据:', qrData);

                        await QRCode.toCanvas(qrCodeCanvas, JSON.stringify(qrData), {
                            width: 200,
                            height: 200,
                            margin: 2,
                            color: {
                                dark: '#000000',
                                light: '#FFFFFF'
                            }
                        });
                        console.log('QR码生成成功');
                    } catch (error) {
                        console.error('生成QR码失败:', error);
                        // 如果生成失败，显示简单的文字信息
                        qrCodeCanvas.style.display = 'none';
                    }
                } else {
                    console.error('QR码生成库未加载');
                    Utils.showToast('QR码生成库未加载', 'error');
                    qrCodeCanvas.style.display = 'none';
                }
            }, 100);

            // 点击背景关闭
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                }
            });

        } catch (error) {
            console.error('创建模态框失败:', error);
            Utils.showToast('显示验证码失败', 'error');
        }
    },

    // 绑定学生出校申请表单事件
    bindStudentExitFormEvents() {
        const studentExitForm = document.getElementById('studentExitApplicationForm');
        console.log('=== 绑定学生出校申请表单事件 ===');
        console.log('学生出校申请表单元素:', studentExitForm);

        if (studentExitForm) {
            console.log('✅ 找到表单元素，开始绑定事件');
            console.log('表单当前属性:', {
                method: studentExitForm.method,
                action: studentExitForm.action,
                onsubmit: studentExitForm.onsubmit
            });

            // 强制设置表单属性
            studentExitForm.method = 'post';
            studentExitForm.action = 'javascript:void(0)';
            console.log('强制设置表单属性后:', {
                method: studentExitForm.method,
                action: studentExitForm.action
            });

            // 移除现有的事件监听器（如果有的话）
            const newForm = studentExitForm.cloneNode(true);
            studentExitForm.parentNode.replaceChild(newForm, studentExitForm);

            // 绑定新的事件监听器
            const formElement = document.getElementById('studentExitApplicationForm');
            console.log('获取新的表单元素:', formElement);

            // 添加多个事件监听器确保捕获提交
            formElement.addEventListener('submit', (e) => {
                console.log('=== 学生出校申请表单提交事件触发 (submit) ===');
                console.log('事件对象:', e);
                console.log('事件目标:', e.target);
                e.preventDefault();
                e.stopPropagation();
                console.log('阻止默认提交行为，调用AJAX提交');
                // 直接使用API提交学生出校申请
                this.submitStudentExitApplicationDirect();
            });

            // 也监听 click 事件来捕获提交按钮点击
            const submitBtn = formElement.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                console.log('找到提交按钮:', submitBtn);
                submitBtn.addEventListener('click', (e) => {
                    console.log('=== 提交按钮点击事件触发 ===');
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('阻止按钮默认行为，调用表单提交');
                    // 直接使用API提交学生出校申请
                    this.submitStudentExitApplicationDirect();
                });
            } else {
                console.warn('未找到提交按钮');
            }

            console.log('✅ 学生出校申请表单事件绑定成功');
        } else {
            console.error('❌ 未找到学生出校申请表单元素');
            // 尝试查找所有表单元素
            const allForms = document.querySelectorAll('form');
            console.log('页面中的所有表单元素:', allForms);
        }
    },

    // 直接提交学生出校申请的简化方法
    async submitStudentExitApplicationDirect() {
        try {
            console.log('=== 开始直接提交学生出校申请 ===');
            Utils.showLoading('正在提交申请...');

            const form = document.getElementById('studentExitApplicationForm');
            if (!form) {
                console.error('表单不存在');
                Utils.showToast('表单不存在', 'error');
                return;
            }

            // 获取表单数据
            const formData = new FormData(form);
            console.log('表单数据:', Object.fromEntries(formData.entries()));

            // 强制获取最新的当前用户信息
            console.log('=== 强制刷新当前用户信息 ===');
            const profileResponse = await fetch('/api/auth/profile', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                }
            });

            const profileData = await profileResponse.json();
            console.log('当前用户信息:', profileData.user);

            if (!profileData.user) {
                Utils.showToast('获取用户信息失败', 'error');
                return;
            }

            // 强制更新AppState.user
            AppState.user = profileData.user;
            localStorage.setItem('app_user', JSON.stringify(profileData.user));

            // 如果当前用户是学生，强制使用学生自己的ID，隐藏学生选择
            let studentId;
            if (AppState.user.user_type === 'student') {
                studentId = AppState.user.id;
                console.log('当前用户是学生，使用学生ID:', studentId);

                // 隐藏学生选择区域
                const studentSelectSection = document.getElementById('studentInfoSection');
                const studentInfoDisplay = document.getElementById('studentInfoDisplay');
                if (studentSelectSection) {
                    studentSelectSection.style.display = 'none';
                    console.log('已隐藏学生选择区域');
                }
                if (studentInfoDisplay) {
                    studentInfoDisplay.style.display = 'block';
                    console.log('已显示学生信息区域');
                }
            } else {
                // 非学生用户，从表单获取选择的学生ID
                const studentSelect = formData.get('studentSelect');
                if (!studentSelect) {
                    Utils.showToast('请选择学生', 'error');
                    return;
                }
                studentId = parseInt(studentSelect);
                console.log('非学生用户，从表单获取学生ID:', studentId);
            }

            // 构建申请数据
            const applicationData = {
                student_id: studentId,
                exit_date: formData.get('exitDate'),
                exit_time_start: formData.get('exitTimeStart'),
                exit_time_end: formData.get('exitTimeEnd'),
                exit_reason: formData.get('exitReason'),
                destination: formData.get('destination') || '',
                emergency_contact: formData.get('emergencyContact') || '',
                emergency_phone: formData.get('emergencyPhone') || ''
            };

            console.log('申请数据:', applicationData);

            // 验证必填字段
            if (!applicationData.exit_date || !applicationData.exit_time_start || !applicationData.exit_time_end || !applicationData.exit_reason) {
                Utils.showToast('请填写所有必填字段：出校日期、时间、原因', 'error');
                return;
            }

            // 调用API提交申请
            const response = await Utils.request('/api/student-exit/applications', {
                method: 'POST',
                body: JSON.stringify(applicationData)
            });

            console.log('API响应:', response);

            Utils.showToast('申请提交成功！', 'success');

            // 清空表单
            form.reset();

            // 刷新申请列表
            if (typeof this.loadRecentApplications === 'function') {
                await this.loadRecentApplications();
            }

            // 关闭模态框
            UI.hideModal('studentExitApplicationModal');

        } catch (error) {
            console.error('提交学生出校申请失败:', error);
            Utils.showToast('提交失败：' + error.message, 'error');
        } finally {
            Utils.hideLoading();
        }
    }
};

// 访问申请页面逻辑
const VisitPage = {
    // 加载页面
    async load() {
        this.initForm();
        await this.loadVisitHistory();
    },

    // 初始化表单
    initForm() {
        const form = document.getElementById('visitApplicationForm');

        // 设置日期限制
        Utils.setMinDate('visitDate');
        Utils.setDefaultDate('visitDate');
        Utils.setDefaultTime('timeStart');
        Utils.setDefaultTime('timeEnd');
        Utils.setEndTime('timeStart', 'timeEnd');

        // 自动填充访问人信息
        this.autoFillVisitorInfo();

        // 绑定表单事件
        this.bindFormEvents();

        // 绑定时间变化事件
        document.getElementById('timeStart')?.addEventListener('change', () => {
            Utils.setEndTime('timeStart', 'timeEnd');
        });

        // 表单提交事件
        form?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitForm();
        });
    },

    // 自动填充访问人信息
    autoFillVisitorInfo() {
        if (AppState.user) {
            document.getElementById('visitorName').value = AppState.user.real_name || '';
            document.getElementById('visitorPhone').value = AppState.user.phone || '';
            document.getElementById('visitorEmail').value = AppState.user.email || '';
            document.getElementById('visitorIdCard').value = AppState.user.id_card || '';
        }
    },

    // 绑定表单事件
    bindFormEvents() {
        // 访问对象选择变化事件
        document.getElementById('visitTarget')?.addEventListener('change', (e) => {
            const targetValue = e.target.value;
            const teacherInfoGroup = document.getElementById('teacherInfoGroup');
            const customTargetGroup = document.getElementById('customTargetGroup');

            if (targetValue === 'teacher') {
                teacherInfoGroup.style.display = 'block';
                customTargetGroup.style.display = 'none';
            } else if (targetValue === 'custom') {
                teacherInfoGroup.style.display = 'none';
                customTargetGroup.style.display = 'block';
            } else {
                teacherInfoGroup.style.display = 'none';
                customTargetGroup.style.display = 'none';
            }

            // 清空相关字段
            if (targetValue !== 'teacher') {
                document.getElementById('targetDepartment').value = '';
                document.getElementById('targetTeacher').value = '';
            }
            if (targetValue !== 'custom') {
                document.getElementById('customTargetName').value = '';
                document.getElementById('customTargetPhone').value = '';
            }

            // 清除相关字段的验证状态
            this.clearFieldValidation();
        });

        // 拜访对象部门变化事件
        document.getElementById('targetDepartment')?.addEventListener('change', (e) => {
            const department = e.target.value;
            const teacherSelect = document.getElementById('targetTeacher');

            if (department && teacherSelect) {
                this.loadTeachersByDepartment(department);
            } else {
                teacherSelect.innerHTML = '<option value="">请选择教师</option>';
            }
        });

        // 工作ID输入框失去焦点时自动验证ID是否存在
        document.getElementById('targetWorkId')?.addEventListener('blur', (e) => {
            const workId = e.target.value.trim();
            if (workId) {
                this.validateTargetIdExists(workId);
            } else {
                this.clearValidationStatus();
            }
        });

        // 姓名输入框失去焦点时自动验证姓名匹配
        document.getElementById('targetPerson')?.addEventListener('blur', (e) => {
            const workId = document.getElementById('targetWorkId')?.value.trim();
            const personName = e.target.value.trim();
            if (workId && personName) {
                this.validateTargetPerson();
            }
        });

        // 拜访对象验证按钮事件（手动验证）
        document.getElementById('validateTargetBtn')?.addEventListener('click', () => {
            this.validateTargetPerson();
        });

        // 支持回车键验证
        document.getElementById('targetPerson')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.validateTargetPerson();
            }
        });

        // 添加同行人按钮事件
        document.getElementById('addCompanion')?.addEventListener('click', () => {
            this.addCompanion();
        });

        
        // 学生出校申请表单提交事件
        // 学生出校申请表单提交事件将在显示模态框时绑定

        // 家长为孩子申请表单提交事件
        document.getElementById('parentApplyForExitForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitParentExitApplication();
        });

        // 初始化实时字段验证
        this.setupFieldValidation();
    },

    // 提交学生出校申请
    async submitStudentExitApplication() {
        try {
            console.log('=== 开始提交学生出校申请 ===');
            Utils.showLoading('正在提交申请...');

            const form = document.getElementById('studentExitApplicationForm');
            if (!form) {
                console.error('表单不存在');
                Utils.showToast('表单不存在', 'error');
                return;
            }

            console.log('找到表单:', form);

            // 获取表单数据
            const formData = new FormData(form);
            console.log('表单数据:', Object.fromEntries(formData.entries()));

            // 检查 window.studentExitApp 是否存在
            console.log('window.studentExitApp:', window.studentExitApp);

            // 使用新的方法获取学生ID（支持学生用户自动加载）
            const studentId = window.studentExitApp ? window.studentExitApp.getCurrentStudentId('student') : null;
            console.log('获取到的学生ID:', studentId);

            if (!studentId) {
                console.error('无法获取学生信息，尝试从当前用户获取');
                // 备用方案：直接使用当前登录用户ID（如果是学生）
                if (AppState.user && AppState.user.user_type === 'student') {
                    const fallbackStudentId = AppState.user.id;
                    console.log('使用备用学生ID:', fallbackStudentId);

                    const applicationData = {
                        student_id: fallbackStudentId,
                        exit_date: formData.get('exit_date'),
                        exit_time_start: formData.get('exit_time_start'),
                        exit_time_end: formData.get('exit_time_end'),
                        exit_reason: formData.get('exit_reason'),
                        destination: formData.get('destination') || '',
                        transport_method: formData.get('transport_method') || '',
                        emergency_contact: formData.get('emergency_contact') || '',
                        emergency_phone: formData.get('emergency_phone') || ''
                    };

                    console.log('申请数据:', applicationData);
                    await this.submitApplicationData(applicationData, form);
                    return;
                }

                Utils.showToast('无法获取学生信息', 'error');
                return;
            }

            const applicationData = {
                student_id: studentId,
                exit_date: formData.get('exit_date'),
                exit_time_start: formData.get('exit_time_start'),
                exit_time_end: formData.get('exit_time_end'),
                exit_reason: formData.get('exit_reason'),
                destination: formData.get('destination') || '',
                transport_method: formData.get('transport_method') || '',
                emergency_contact: formData.get('emergency_contact') || '',
                emergency_phone: formData.get('emergency_phone') || ''
            };

            console.log('申请数据:', applicationData);
            await this.submitApplicationData(applicationData, form);

        } catch (error) {
            console.error('提交学生出校申请失败:', error);
            Utils.showToast('提交失败，请重试', 'error');
        } finally {
            Utils.hideLoading();
        }
    },

    // 通用的申请数据提交函数
    async submitApplicationData(applicationData, form) {
        console.log('开始提交申请数据:', applicationData);

        // 验证必填字段
        const requiredFields = ['exit_date', 'exit_time_start', 'exit_time_end', 'exit_reason'];
        for (const field of requiredFields) {
            if (!applicationData[field]) {
                console.error(`必填字段 ${field} 为空`);
                Utils.showToast('请填写所有必填字段', 'error');
                return;
            }
        }

        try {
            // 提交申请
            const response = await fetch('/api/student-exit/applications', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(applicationData)
            });

            console.log('API响应状态:', response.status);
            const result = await response.json();
            console.log('API响应数据:', result);

            if (response.ok) {
                // 显示成功消息，包含状态信息
                const successMessage = '申请提交成功！等待家长和班主任审批';
                Utils.showToast(successMessage, 'success');

                // 重置表单
                if (form) {
                    form.reset();
                }
                this.hideStudentInfoDisplay();

                // 刷新申请列表
                console.log('刷新申请列表...');
                await HomePage.loadRecentApplications();

                // 关闭模态框
                setTimeout(() => {
                    const modal = document.getElementById('studentExitApplicationModal');
                    if (modal) {
                        UI.hideModal('studentExitApplicationModal');
                    }
                }, 1500);

            } else {
                console.error('提交失败:', result);
                Utils.showToast(result.error || '提交失败', 'error');
            }

        } catch (error) {
            console.error('API调用失败:', error);
            Utils.showToast('网络错误，请重试', 'error');
        }
    },

    // 提交家长出校申请
    async submitParentExitApplication() {
        try {
            Utils.showLoading('正在提交申请...');

            const form = document.getElementById('parentApplyForExitForm');
            if (!form) {
                Utils.showToast('表单不存在', 'error');
                return;
            }

            // 获取表单数据
            const formData = new FormData(form);
            const studentSelect = document.getElementById('parentStudentSelect');

            if (!studentSelect || !studentSelect.value) {
                Utils.showToast('请选择学生', 'error');
                return;
            }

            const applicationData = {
                student_id: studentSelect.value,
                exit_date: formData.get('exit_date'),
                exit_time_start: formData.get('exit_time_start'),
                exit_time_end: formData.get('exit_time_end'),
                exit_reason: formData.get('exit_reason'),
                destination: formData.get('destination') || '',
                transport_method: formData.get('transport_method') || '',
                emergency_contact: formData.get('emergency_contact') || '',
                emergency_phone: formData.get('emergency_phone') || ''
            };

            // 验证必填字段
            const requiredFields = ['exit_date', 'exit_time_start', 'exit_time_end', 'exit_reason'];
            for (const field of requiredFields) {
                if (!applicationData[field]) {
                    Utils.showToast('请填写所有必填字段', 'error');
                    return;
                }
            }

            // 提交申请
            const response = await fetch('/api/student-exit/applications', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(applicationData)
            });

            const result = await response.json();

            if (response.ok) {
                Utils.showToast('申请提交成功！', 'success');
                form.reset();
                this.hideStudentInfoDisplay();
                // 刷新申请列表
                HomePage.loadRecentApplications();
            } else {
                Utils.showToast(result.error || '提交失败', 'error');
            }

        } catch (error) {
            console.error('提交家长出校申请失败:', error);
            Utils.showToast('提交失败，请重试', 'error');
        } finally {
            Utils.hideLoading();
        }
    },

    // 隐藏学生信息显示
    hideStudentInfoDisplay() {
        const displaySection = document.getElementById('studentInfoDisplay');
        if (displaySection) {
            displaySection.style.display = 'none';
        }
    },

    // 验证受访者ID是否存在
    async validateTargetIdExists(workId) {
        const validationStatus = document.getElementById('validationStatus');

        if (!workId) {
            this.clearValidationStatus();
            return;
        }

        // 显示验证中状态
        this.showValidationStatus('loading', '正在验证受访者ID...');

        try {
            // 调用后端API仅验证ID是否存在
            const response = await Utils.request('/api/visits/check-target-id', {
                method: 'POST',
                body: JSON.stringify({
                    target_work_id: workId
                })
            });

            if (response.success) {
                this.showValidationStatus('info',
                    `✅ 找到受访者：${response.user_info.real_name}（${response.user_info.user_type}）<br>请继续输入姓名进行验证`);

                // 存储用户信息供后续验证使用
                this.cachedTargetUserInfo = response.user_info;

                // 启用姓名输入框
                const nameInput = document.getElementById('targetPerson');
                if (nameInput) {
                    nameInput.disabled = false;
                    nameInput.placeholder = `请输入 ${response.user_info.real_name} 进行验证`;
                }
            }

        } catch (error) {
            this.showValidationStatus('error', `❌ ${error.message || '受访者ID不存在'}`);

            // 清空部门信息
            const deptInput = document.getElementById('targetDepartment');
            if (deptInput) {
                deptInput.value = '';
            }

            // 禁用姓名输入框
            const nameInput = document.getElementById('targetPerson');
            if (nameInput) {
                nameInput.disabled = true;
                nameInput.placeholder = '请先输入有效的受访者ID';
                nameInput.value = '';
            }

            this.cachedTargetUserInfo = null;
        }
    },

    // 清除验证状态
    clearValidationStatus() {
        const validationStatus = document.getElementById('validationStatus');
        if (validationStatus) {
            validationStatus.innerHTML = '';
            validationStatus.className = 'validation-status';
        }

        // 重置姓名输入框
        const nameInput = document.getElementById('targetPerson');
        if (nameInput) {
            nameInput.disabled = false;
            nameInput.placeholder = '请输入受访者真实姓名';
        }

        // 清空部门信息
        const deptInput = document.getElementById('targetDepartment');
        if (deptInput) {
            deptInput.value = '';
        }

        this.cachedTargetUserInfo = null;
    },

    // 清除验证状态
    clearValidationStatus() {
        const validationStatus = document.getElementById('validationStatus');
        if (validationStatus) {
            validationStatus.innerHTML = '';
            validationStatus.className = 'validation-status';
        }

        // 重置姓名输入框
        const nameInput = document.getElementById('targetPerson');
        if (nameInput) {
            nameInput.disabled = false;
            nameInput.placeholder = '请输入受访者真实姓名';
        }

        // 清空部门信息
        const deptInput = document.getElementById('targetDepartment');
        if (deptInput) {
            deptInput.value = '';
        }

        this.cachedTargetUserInfo = null;
    },

    // 根据工作ID查询拜访对象信息
    // 验证受访者信息（双重验证：ID + 姓名）
    async validateTargetPerson() {
        const workId = document.getElementById('targetWorkId')?.value.trim();
        const personName = document.getElementById('targetPerson')?.value.trim();
        const validateBtn = document.getElementById('validateTargetBtn');
        const validationStatus = document.getElementById('validationStatus');

        // 检查必填字段
        if (!workId || !personName) {
            this.showValidationStatus('error', '请同时填写受访者ID和姓名');
            return;
        }

        // 显示验证中状态
        if (validateBtn) {
            validateBtn.disabled = true;
            validateBtn.innerHTML = '<span class="btn-icon">⟳</span>验证中...';
        }
        this.showValidationStatus('loading', '正在验证受访者信息...');

        try {
            // 调用后端验证API
            const response = await Utils.request('/api/visits/validate-target', {
                method: 'POST',
                body: JSON.stringify({
                    target_work_id: workId,
                    target_person: personName
                })
            });

            if (response.success) {
                // 验证成功，填充部门信息
                const deptInput = document.getElementById('targetDepartment');
                if (deptInput && response.user_info.department_info) {
                    deptInput.value = response.user_info.department_info;
                }

                this.showValidationStatus('success',
                    `✅ 验证成功！${response.user_info.real_name}（${response.user_info.user_type} - ${response.user_info.department_info}）`);

                Utils.showToast('受访者信息验证通过', 'success');
            }

        } catch (error) {
            // 验证失败，显示错误信息
            this.showValidationStatus('error', `❌ ${error.message || '验证失败'}`);

            // 清空部门信息
            const deptInput = document.getElementById('targetDepartment');
            if (deptInput) {
                deptInput.value = '';
            }
        } finally {
            // 恢复按钮状态
            if (validateBtn) {
                validateBtn.disabled = false;
                validateBtn.innerHTML = '<span class="btn-icon">✓</span>验证';
            }
        }
    },

    // 显示验证状态
    showValidationStatus(type, message) {
        const statusDiv = document.getElementById('validationStatus');
        if (!statusDiv) return;

        statusDiv.className = `validation-status ${type}`;
        statusDiv.textContent = message;

        if (type === 'loading') {
            statusDiv.style.display = 'block';
        } else if (type === 'success') {
            statusDiv.style.display = 'block';
            // 成功消息3秒后自动隐藏
            setTimeout(() => {
                if (statusDiv.className.includes('success')) {
                    statusDiv.style.display = 'none';
                }
            }, 3000);
        } else if (type === 'error') {
            statusDiv.style.display = 'block';
            // 错误消息5秒后自动隐藏
            setTimeout(() => {
                if (statusDiv.className.includes('error')) {
                    statusDiv.style.display = 'none';
                }
            }, 5000);
        }
    },

    // 清空拜访对象信息
    clearTargetInfo() {
        const targetPersonInput = document.getElementById('targetPerson');
        const targetDepartmentInput = document.getElementById('targetDepartment');

        if (targetPersonInput) targetPersonInput.value = '';
        if (targetDepartmentInput) targetDepartmentInput.value = '';
    },

    // 加载指定部门的教师列表
    async loadTeachersByDepartment(department) {
        try {
            const data = await Utils.request(`/users/teachers?department=${encodeURIComponent(department)}`);
            const teacherSelect = document.getElementById('targetTeacher');

            if (data.teachers && data.teachers.length > 0) {
                teacherSelect.innerHTML = '<option value="">请选择教师</option>' +
                    data.teachers.map(teacher =>
                        `<option value="${teacher.id}">${teacher.real_name}</option>`
                    ).join('');
            } else {
                teacherSelect.innerHTML = '<option value="">该部门暂无教师</option>';
            }
        } catch (error) {
            console.error('加载教师列表失败:', error);
            const teacherSelect = document.getElementById('targetTeacher');
            teacherSelect.innerHTML = '<option value="">加载教师列表失败</option>';
        }
    },

    // 提交表单
    async submitForm() {
        console.log('开始提交申请...');

        // 检查用户是否已登录
        if (!AppState.isAuthenticated || !AppState.user) {
            Utils.showToast('❌ 请先登录后再提交申请', 'error');
            console.log('用户未登录，提交失败');
            return;
        }

        console.log('用户已登录:', AppState.user.real_name);

        if (!this.validateForm()) {
            console.log('表单验证失败');
            return;
        }

        // 获取提交按钮并显示加载状态
        const submitBtn = document.querySelector('#visitApplicationForm button[type="submit"]');
        const originalText = submitBtn.textContent;

        // 禁用提交按钮并显示加载状态
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> 提交中...';
        submitBtn.style.opacity = '0.7';

        const formData = this.getFormData();
        console.log('表单数据:', formData);

        try {
            console.log('发送API请求...');
            const response = await Utils.request('/api/visits/applications', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            console.log('API响应:', response);

            // 详细的成功信息
            const visitDate = Utils.formatDate(formData.visit_date);
            const timeRange = `${formData.visit_time_start} - ${formData.visit_time_end}`;
            const targetPerson = formData.target_person || '未指定';

            Utils.showToast(
                `✅ 申请提交成功！\n📅 访问日期：${visitDate}\n🕐 访问时间：${timeRange}\n👤 拜访对象：${targetPerson}\n\n申请已提交审核，请等待批准\n3秒后自动返回首页...`,
                'success'
            );

            // 延迟3秒后返回首页
            setTimeout(() => {
                window.location.href = '/'; // 返回首页
            }, 3000);

        } catch (error) {
            console.error('提交申请失败:', error);
            Utils.showToast(
                `❌ 申请提交失败\n${error.message || '请检查网络连接或联系管理员'}`,
                'error'
            );
        } finally {
            // 恢复提交按钮状态
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="ri-send-plane-line"></i> 提交申请`;
            submitBtn.style.opacity = '';
        }
    },

    // 获取表单数据
    getFormData() {
        const getValue = (id) => document.getElementById(id)?.value || '';

        // 获取同行人数据
        const companions = this.getCompanionsData();

        return {
            visit_date: getValue('visitDate'),
            visit_time_start: getValue('timeStart'),
            visit_time_end: getValue('timeEnd'),
            visit_purpose: getValue('visitPurpose'),
            target_work_id: getValue('targetWorkId'),
            target_person: getValue('targetPerson'),
            target_department: getValue('targetDepartment'),
            visitor_name: getValue('visitorName'),
            visitor_phone: getValue('visitorPhone'),
            visitor_email: getValue('visitorEmail'),
            visitor_id_card: getValue('visitorIdCard'),
            visit_type: 'in-person',
            companions: companions  // 添加同行人数据
        };
    },

    // 验证表单
    validateForm() {
        const getValue = (id) => document.getElementById(id)?.value || '';
        const errors = [];

        // 验证必填字段
        if (!getValue('visitDate')) errors.push('请选择访问日期');
        if (!getValue('timeStart')) errors.push('请选择开始时间');
        if (!getValue('timeEnd')) errors.push('请选择结束时间');
        if (!getValue('visitPurpose')) errors.push('请填写访问事由');
        if (!getValue('visitorName')) errors.push('请填写访问人姓名');
        if (!getValue('visitorPhone')) errors.push('请填写访问人电话');
        if (!getValue('visitorIdCard')) errors.push('请填写访问人身份证号');
        if (!getValue('targetWorkId')) errors.push('请填写拜访对象工作ID');

        // 验证拜访对象信息（基于工作ID）
        const targetWorkId = getValue('targetWorkId');
        const targetPerson = getValue('targetPerson');

        if (!targetWorkId) {
            errors.push('请填写拜访对象工作ID');
        } else if (!targetPerson) {
            errors.push('请输入有效的工作ID以自动填充拜访对象信息');
        }

        // 验证时间逻辑
        const timeStart = getValue('timeStart');
        const timeEnd = getValue('timeEnd');
        if (timeStart && timeEnd && timeStart >= timeEnd) {
            errors.push('结束时间必须晚于开始时间');
        }

        // 验证电话格式
        const visitorPhone = getValue('visitorPhone');
        if (visitorPhone && !Utils.validatePhone(visitorPhone)) {
            errors.push('访问人电话格式不正确');
        }

        // 验证身份证格式
        const visitorIdCard = getValue('visitorIdCard');
        if (visitorIdCard && !Utils.validateIdCard(visitorIdCard)) {
            errors.push('访问人身份证号格式不正确');
        }

        if (errors.length > 0) {
            console.log('表单验证错误详情:', errors);
            Utils.showToast(errors.join('；'), 'error');
            return false;
        }

        return true;
    },

    // 实时字段验证
    setupFieldValidation() {
        const fields = [
            { id: 'visitDate', required: true, message: '请选择访问日期' },
            { id: 'timeStart', required: true, message: '请选择开始时间' },
            { id: 'timeEnd', required: true, message: '请选择结束时间' },
            { id: 'visitPurpose', required: true, message: '请填写访问事由' },
            { id: 'visitorName', required: true, message: '请填写访问人姓名' },
            { id: 'visitorPhone', required: true, message: '请填写访问人电话' },
            { id: 'visitorIdCard', required: true, message: '请填写访问人身份证号' },
            { id: 'targetWorkId', required: true, message: '请填写拜访对象工作ID' }
        ];

        fields.forEach(field => {
            const element = document.getElementById(field.id);
            if (element) {
                // 添加输入事件监听
                element.addEventListener('input', () => this.validateField(field));
                element.addEventListener('change', () => this.validateField(field));
                element.addEventListener('blur', () => this.validateField(field));
            }
        });

        // 时间字段特殊处理
        const timeStartElement = document.getElementById('timeStart');
        const timeEndElement = document.getElementById('timeEnd');
        if (timeStartElement && timeEndElement) {
            timeStartElement.addEventListener('change', () => this.validateTimeFields());
            timeEndElement.addEventListener('change', () => this.validateTimeFields());
        }

        // 工作ID特殊处理
        const targetWorkIdElement = document.getElementById('targetWorkId');
        if (targetWorkIdElement) {
            targetWorkIdElement.addEventListener('input', () => {
                this.validateField({ id: 'targetWorkId', required: true, message: '请填写拜访对象工作ID' });
                // 延迟验证拜访对象信息，因为API调用需要时间
                setTimeout(() => this.validateTargetPerson(), 500);
            });
        }
    },

    // 验证单个字段
    validateField(field) {
        const element = document.getElementById(field.id);
        if (!element) return true;

        const value = element.value || '';
        const isValid = !field.required || value.trim() !== '';

        this.setFieldValidationState(element, isValid, field.message);

        return isValid;
    },

    // 验证时间字段
    validateTimeFields() {
        const timeStartElement = document.getElementById('timeStart');
        const timeEndElement = document.getElementById('timeEnd');

        if (!timeStartElement || !timeEndElement) return true;

        const timeStart = timeStartElement.value;
        const timeEnd = timeEndElement.value;

        let startValid = true;
        let endValid = true;

        if (!timeStart) {
            this.setFieldValidationState(timeStartElement, false, '请选择开始时间');
            startValid = false;
        } else {
            this.setFieldValidationState(timeStartElement, true, '');
        }

        if (!timeEnd) {
            this.setFieldValidationState(timeEndElement, false, '请选择结束时间');
            endValid = false;
        } else if (timeStart && timeStart >= timeEnd) {
            this.setFieldValidationState(timeEndElement, false, '结束时间必须晚于开始时间');
            endValid = false;
        } else {
            this.setFieldValidationState(timeEndElement, true, '');
        }

        return startValid && endValid;
    },

    // 验证拜访对象信息
    validateTargetPerson() {
        const targetWorkIdElement = document.getElementById('targetWorkId');
        const targetPersonElement = document.getElementById('targetPerson');

        if (!targetWorkIdElement || !targetPersonElement) return true;

        const targetWorkId = targetWorkIdElement.value.trim();
        const targetPerson = targetPersonElement.value.trim();

        if (!targetWorkId) {
            this.setFieldValidationState(targetWorkIdElement, false, '请填写拜访对象工作ID');
            return false;
        }

        if (!targetPerson) {
            this.setFieldValidationState(targetWorkIdElement, false, '请输入有效的工作ID以自动填充拜访对象信息');
            return false;
        }

        this.setFieldValidationState(targetWorkIdElement, true, '');
        return true;
    },

    // 设置字段验证状态
    setFieldValidationState(element, isValid, errorMessage) {
        if (!element) return;

        // 移除之前的状态类
        element.classList.remove('is-valid', 'is-invalid');

        // 查找或创建错误消息元素
        let errorElement = element.parentNode.querySelector('.field-error-message');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error-message';
            element.parentNode.appendChild(errorElement);
        }

        if (isValid) {
            element.classList.add('is-valid');
            errorElement.textContent = '';
            errorElement.style.display = 'none';
        } else {
            element.classList.add('is-invalid');
            errorElement.textContent = errorMessage;
            errorElement.style.display = 'block';
            errorElement.style.color = '#dc3545';
            errorElement.style.fontSize = '0.875rem';
            errorElement.style.marginTop = '0.25rem';
        }
    },

    // 清除所有字段验证状态
    clearFieldValidation() {
        const elements = document.querySelectorAll('.is-valid, .is-invalid');
        elements.forEach(element => {
            element.classList.remove('is-valid', 'is-invalid');
        });

        const errorMessages = document.querySelectorAll('.field-error-message');
        errorMessages.forEach(element => {
            element.textContent = '';
            element.style.display = 'none';
        });
    },

    // 加载申请历史
    async loadVisitHistory() {
        try {
            console.log('开始加载申请历史...');
            const data = await Utils.request('/api/visits/applications');
            console.log('获取到申请历史数据:', data);

            const container = document.getElementById('visitHistory');

            if (data.applications.length === 0) {
                console.log('没有申请记录');
                container.innerHTML = '<p class="text-center text-secondary">暂无申请记录</p>';
                return;
            }

            console.log(`渲染 ${data.applications.length} 条申请记录`);
            container.innerHTML = data.applications.map(app => this.renderHistoryItem(app)).join('');

            // 绑定历史项点击事件
            this.bindHistoryItemClickEvents();
        } catch (error) {
            console.error('加载申请历史失败:', error);
            const container = document.getElementById('visitHistory');
            if (container) {
                container.innerHTML = '<p class="text-center text-secondary">加载失败</p>';
            }
        }
    },

    // 渲染历史记录项
    renderHistoryItem(app) {
        const statusClass = Utils.getStatusClass(app.application_status);
        const statusText = Utils.getStatusText(app.application_status);

        return `
            <div class="history-item" data-id="${app.id}">
                <div class="history-header">
                    <span class="history-date">${Utils.formatDate(app.visit_date)}</span>
                    <span class="history-status ${statusClass}">${statusText}</span>
                </div>
                <div class="history-content">
                    <div class="history-purpose">${app.visit_purpose}</div>
                    <div class="history-target">拜访对象: ${app.target_person || '未指定'}</div>
                    <div class="history-time">时间: ${Utils.formatTime(app.visit_time_start)} - ${Utils.formatTime(app.visit_time_end)}</div>
                </div>
                <div class="history-actions">
                    ${this.renderHistoryActions(app)}
                </div>
            </div>
        `;
    },

    // 渲染历史记录操作按钮
    renderHistoryActions(app) {
        let actions = '';

        if (['pending', 'parent_approved', 'teacher_approved'].includes(app.application_status)) {
            actions += `
                <button class="btn btn-sm btn-warning" onclick="VisitPage.cancelApplication(${app.id})">
                    <i class="ri-close-line"></i> 取消申请
                </button>
            `;
        }

        if (app.application_status === 'approved') {
            actions += `
                <button class="btn btn-sm btn-success" onclick="VisitPage.startVisit(${app.id})">
                    <i class="ri-check-line"></i> 开始访问
                </button>
            `;
        }

        actions += `
            <button class="btn btn-sm btn-info" onclick="VisitPage.viewDetails(${app.id})">
                <i class="ri-eye-line"></i> 查看详情
            </button>
        `;

        return actions;
    },

    // 绑定历史项点击事件
    bindHistoryItemClickEvents() {
        document.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // 如果点击的是按钮，不触发卡片点击事件
                if (e.target.closest('.history-actions')) {
                    return;
                }

                const id = item.dataset.id;
                this.viewDetails(id);
            });
        });
    },

    // 取消申请
    async cancelApplication(id) {
        if (!confirm('确定要取消这个申请吗？')) {
            return;
        }

        try {
            await Utils.request(`/api/visits/applications/${id}/cancel`, {
                method: 'POST'
            });

            Utils.showToast('申请已取消', 'success');
            await this.loadVisitHistory();
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 开始访问
    async startVisit(id) {
        try {
            await Utils.request(`/api/visits/applications/${id}/start`, {
                method: 'POST'
            });

            Utils.showToast('访问已开始', 'success');
            await this.loadVisitHistory();
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 查看详情
    async viewDetails(id) {
        try {
            // 检查是否已登录
            if (!AppState.token && !window.isLoggingOut) {
                Utils.showToast('请先登录后查看详情', 'warning');
                // 跳转到登录页面
                AppState.logout();
                return;
            }

            Utils.showLoading('加载申请详情...');

            const response = await Utils.request(`/api/visits/applications/${id}`);

            if (response.success) {
                this.showVisitDetailsModal(response.data);
            } else {
                Utils.showToast('获取申请详情失败', 'error');
            }
        } catch (error) {
            Utils.hideLoading();
            console.error('获取申请详情失败:', error);

            // 检查是否是认证错误
            if (error.message && error.message.includes('401') && !window.isLoggingOut) {
                Utils.showToast('登录已过期，请重新登录', 'warning');
                AppState.logout();
                return;
            }

            // 检查是否是权限错误
            if (error.message && error.message.includes('403')) {
                Utils.showToast('没有权限查看此申请', 'error');
                return;
            }

            Utils.showToast('获取申请详情失败，请重试', 'error');
        }
    },

    // 显示访问申请详情模态框
    showVisitDetailsModal(application) {
        // 创建详情内容
        const statusColors = {
            'pending': '#ff9800',
            'approved': '#4caf50',
            'rejected': '#f44336',
            'cancelled': '#9e9e9e',
            'completed': '#2196f3'
        };

        const statusTexts = {
            'pending': '待处理',
            'approved': '已通过',
            'rejected': '已拒绝',
            'cancelled': '已取消',
            'completed': '已完成'
        };

        const detailsHtml = `
            <div class="visit-details">
                <div class="detail-section">
                    <h3>基本信息</h3>
                    <div class="detail-row">
                        <span class="detail-label">申请人：</span>
                        <span class="detail-value">${application.applicant?.real_name || '未知'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">访问日期：</span>
                        <span class="detail-value">${application.visit_date || '未设置'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">访问时间：</span>
                        <span class="detail-value">${application.visit_time_start || '未设置'} - ${application.visit_time_end || '未设置'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">访问目的：</span>
                        <span class="detail-value">${application.visit_purpose || '未填写'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">申请状态：</span>
                        <span class="detail-value" style="color: ${statusColors[application.application_status] || '#666'}; font-weight: 600;">
                            ${statusTexts[application.application_status] || application.application_status}
                        </span>
                    </div>
                </div>

                ${application.application_status === 'approved' ? `
                <div class="detail-section">
                    <h3>审批信息</h3>
                    <div class="detail-row">
                        <span class="detail-label">审批人：</span>
                        <span class="detail-value">${application.approver_name || '未知'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">审批时间：</span>
                        <span class="detail-value">${application.approval_time ? new Date(application.approval_time).toLocaleString() : '未知'}</span>
                    </div>
                    ${application.approval_note ? `
                    <div class="detail-row">
                        <span class="detail-label">审批备注：</span>
                        <span class="detail-value">${application.approval_note}</span>
                    </div>
                    ` : ''}
                </div>
                ` : ''}

                ${application.target_person ? `
                <div class="detail-section">
                    <h3>访问对象</h3>
                    <div class="detail-row">
                        <span class="detail-label">访问对象：</span>
                        <span class="detail-value">${application.target_person}</span>
                    </div>
                </div>
                ` : ''}

                ${application.vehicle ? `
                <div class="detail-section">
                    <h3>车辆信息</h3>
                    <div class="detail-row">
                        <span class="detail-label">车牌号：</span>
                        <span class="detail-value">${application.vehicle.plate_number || '未提供'}</span>
                    </div>
                    ${application.vehicle.car_model ? `
                    <div class="detail-row">
                        <span class="detail-label">车型：</span>
                        <span class="detail-value">${application.vehicle.car_model}</span>
                    </div>
                    ` : ''}
                    ${application.vehicle.color ? `
                    <div class="detail-row">
                        <span class="detail-label">颜色：</span>
                        <span class="detail-value">${application.vehicle.color}</span>
                    </div>
                    ` : ''}
                </div>
                ` : ''}

                <div class="detail-section">
                    <h3>申请信息</h3>
                    <div class="detail-row">
                        <span class="detail-label">申请时间：</span>
                        <span class="detail-value">${new Date(application.created_at).toLocaleString()}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">申请编号：</span>
                        <span class="detail-value">#${application.id.toString().padStart(6, '0')}</span>
                    </div>
                </div>
            </div>
        `;

        // 更新模态框内容
        document.getElementById('visitDetailsContent').innerHTML = detailsHtml;

        // 绑定关闭事件
        document.getElementById('closeVisitDetailsModal').addEventListener('click', () => {
            UI.hideModal('visitDetailsModal');
        });
        document.getElementById('closeVisitDetails').addEventListener('click', () => {
            UI.hideModal('visitDetailsModal');
        });

        // 显示模态框
        UI.hideLoading();
        UI.showModal('visitDetailsModal');
    },

    // 添加同行人
    addCompanion() {
        const companionList = document.getElementById('companionList');
        if (!companionList) {
            console.error('companionList元素未找到');
            return;
        }

        // 获取当前同行人数量
        const currentCompanions = companionList.children.length;
        const maxCompanions = 10; // 最多10个同行人

        if (currentCompanions >= maxCompanions) {
            Utils.showToast('同行人数量已达上限（最多10人）', 'warning');
            return;
        }

        const companionIndex = currentCompanions + 1;
        const companionId = `companion_${companionIndex}`;

        // 创建同行人表单HTML
        const companionHtml = `
            <div class="companion-item" id="${companionId}" style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 10px; position: relative;">
                <div class="companion-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0; color: #495057; font-size: 14px; font-weight: 600;">
                        <i class="ri-user-line"></i> 同行人 ${companionIndex}
                    </h4>
                    <button type="button" class="btn btn-outline btn-sm remove-companion" data-id="${companionId}" style="padding: 4px 8px; font-size: 12px;">
                        <i class="ri-close-line"></i> 删除
                    </button>
                </div>
                <div class="companion-form" style="display: grid; gap: 10px;">
                    <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 4px; font-size: 12px; color: #6c757d;">姓名 <span style="color: #dc3545;">*</span></label>
                            <input type="text" name="companion_name_${companionIndex}" placeholder="请输入姓名" required
                                   style="width: 100%; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 4px; font-size: 12px; color: #6c757d;">联系电话 <span style="color: #dc3545;">*</span></label>
                            <input type="tel" name="companion_phone_${companionIndex}" placeholder="请输入手机号" required
                                   style="width: 100%; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 4px; font-size: 12px; color: #6c757d;">身份证号</label>
                            <input type="text" name="companion_idcard_${companionIndex}" placeholder="请输入身份证号（选填）" maxlength="18"
                                   style="width: 100%; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 4px; font-size: 12px; color: #6c757d;">关系</label>
                            <select name="companion_relation_${companionIndex}" style="width: 100%; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                                <option value="">请选择关系</option>
                                <option value="家人">家人</option>
                                <option value="朋友">朋友</option>
                                <option value="同事">同事</option>
                                <option value="同学">同学</option>
                                <option value="其他">其他</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 添加到DOM
        companionList.insertAdjacentHTML('beforeend', companionHtml);

        // 绑定删除按钮事件
        const removeBtn = document.querySelector(`#${companionId} .remove-companion`);
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                this.removeCompanion(companionId);
            });
        }

        // 添加动画效果
        const newCompanion = document.getElementById(companionId);
        if (newCompanion) {
            newCompanion.style.opacity = '0';
            newCompanion.style.transform = 'translateY(-10px)';
            newCompanion.style.transition = 'all 0.3s ease';

            setTimeout(() => {
                newCompanion.style.opacity = '1';
                newCompanion.style.transform = 'translateY(0)';
            }, 10);
        }

        // 滚动到新添加的同行人
        setTimeout(() => {
            newCompanion.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);

        console.log(`已添加同行人 ${companionIndex}`);
    },

    // 删除同行人
    removeCompanion(companionId) {
        const companion = document.getElementById(companionId);
        if (companion) {
            // 添加删除动画
            companion.style.transition = 'all 0.3s ease';
            companion.style.opacity = '0';
            companion.style.transform = 'translateX(20px)';

            setTimeout(() => {
                companion.remove();

                // 重新编号剩余的同行人
                this.renumberCompanions();

                Utils.showToast('同行人已删除', 'info');
            }, 300);
        }
    },

    // 重新编号同行人
    renumberCompanions() {
        const companionList = document.getElementById('companionList');
        if (!companionList) return;

        const companions = companionList.querySelectorAll('.companion-item');
        companions.forEach((companion, index) => {
            const newIndex = index + 1;
            const newId = `companion_${newIndex}`;

            // 更新ID
            companion.id = newId;

            // 更新标题
            const title = companion.querySelector('h4');
            if (title) {
                title.innerHTML = `<i class="ri-user-line"></i> 同行人 ${newIndex}`;
            }

            // 更新删除按钮的data-id
            const removeBtn = companion.querySelector('.remove-companion');
            if (removeBtn) {
                removeBtn.setAttribute('data-id', newId);
                // 重新绑定事件
                removeBtn.removeEventListener('click', () => {});
                removeBtn.addEventListener('click', () => {
                    this.removeCompanion(newId);
                });
            }

            // 更新表单字段的name属性
            const nameInput = companion.querySelector('input[name^="companion_name_"]');
            const phoneInput = companion.querySelector('input[name^="companion_phone_"]');
            const idcardInput = companion.querySelector('input[name^="companion_idcard_"]');
            const relationSelect = companion.querySelector('select[name^="companion_relation_"]');

            if (nameInput) nameInput.name = `companion_name_${newIndex}`;
            if (phoneInput) phoneInput.name = `companion_phone_${newIndex}`;
            if (idcardInput) idcardInput.name = `companion_idcard_${newIndex}`;
            if (relationSelect) relationSelect.name = `companion_relation_${newIndex}`;
        });
    },

    // 获取同行人数据
    getCompanionsData() {
        const companionList = document.getElementById('companionList');
        if (!companionList) return [];

        const companions = [];
        const companionItems = companionList.querySelectorAll('.companion-item');

        companionItems.forEach((companion, index) => {
            const companionIndex = index + 1;
            const nameInput = companion.querySelector(`input[name="companion_name_${companionIndex}"]`);
            const phoneInput = companion.querySelector(`input[name="companion_phone_${companionIndex}"]`);
            const idcardInput = companion.querySelector(`input[name="companion_idcard_${companionIndex}"]`);
            const relationSelect = companion.querySelector(`select[name="companion_relation_${companionIndex}"]`);

            if (nameInput && phoneInput && nameInput.value.trim() && phoneInput.value.trim()) {
                companions.push({
                    name: nameInput.value.trim(),
                    phone: phoneInput.value.trim(),
                    id_card: idcardInput ? idcardInput.value.trim() : '',
                    relation: relationSelect ? relationSelect.value : ''
                });
            }
        });

        return companions;
    },
};

// 人脸识别页面逻辑
const FacePage = {
    // 当前选择的文件
    currentFile: null,

    // 加载页面
    async load() {
        await this.loadFaceStatus();
        this.initImageUpload();
        this.bindEvents();
    },

    // 初始化图片上传功能
    initImageUpload() {
        const uploadArea = document.getElementById('faceUploadArea');
        const fileInput = document.getElementById('faceImageInput');

        if (!uploadArea || !fileInput) {
            console.warn('Face upload elements not found');
            return;
        }

        // 文件选择事件
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileSelect(file);
            }
        });

        // 拖拽事件
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });
    },

    // 处理文件选择
    handleFileSelect(file) {
        // 验证文件类型
        if (!file.type.startsWith('image/')) {
            Utils.showToast('请选择图片文件', 'error');
            return;
        }

        // 验证文件大小（5MB）
        if (file.size > 5 * 1024 * 1024) {
            Utils.showToast('图片大小不能超过5MB', 'error');
            return;
        }

        this.currentFile = file;
        this.previewImage(file);
    },

    // 预览图片
    previewImage(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const uploadArea = document.getElementById('faceUploadArea');
            const previewContainer = document.getElementById('facePreview');
            const previewImage = document.getElementById('facePreviewImage');

            if (previewContainer && previewImage) {
                previewImage.src = e.target.result;
                uploadArea.style.display = 'none';
                previewContainer.style.display = 'block';

                // 显示取消按钮
                this.showCancelButton();
            }
        };
        reader.readAsDataURL(file);
    },

    // 显示取消按钮
    showCancelButton() {
        const previewContainer = document.getElementById('facePreview');

        // 检查是否已经有取消按钮
        let cancelBtn = document.getElementById('cancelImageBtn');
        if (!cancelBtn) {
            cancelBtn = document.createElement('button');
            cancelBtn.id = 'cancelImageBtn';
            cancelBtn.className = 'btn btn-outline';
            cancelBtn.innerHTML = '<i class="ri-close-line"></i> 取消';
            cancelBtn.style.marginTop = '10px';

            cancelBtn.addEventListener('click', () => {
                this.cancelImageUpload();
            });

            previewContainer.appendChild(cancelBtn);
        }
    },

    // 取消图片上传
    cancelImageUpload() {
        this.currentFile = null;

        // 重置文件输入框
        const fileInput = document.getElementById('faceImageInput');
        if (fileInput) {
            fileInput.value = '';
        }

        // 隐藏预览，显示上传区域
        const uploadArea = document.getElementById('faceUploadArea');
        const previewContainer = document.getElementById('facePreview');

        if (uploadArea && previewContainer) {
            uploadArea.style.display = 'block';
            previewContainer.style.display = 'none';
        }

        // 移除取消按钮
        const cancelBtn = document.getElementById('cancelImageBtn');
        if (cancelBtn) {
            cancelBtn.remove();
        }
    },

    // 加载人脸注册状态
    async loadFaceStatus() {
        try {
            const data = await Utils.request('/api/faces/status');
            this.updateFaceStatus(data);

            // 如果已注册，加载详细信息
            if (data.registered) {
                await this.loadFaceInfo();
            }
        } catch (error) {
            console.error('加载人脸状态失败:', error);
            this.updateFaceStatus({ registered: false });
        }
    },

    // 加载人脸信息详情
    async loadFaceInfo() {
        try {
            const data = await Utils.request('/api/faces/info');
            this.updateFaceInfoDisplay(data);
        } catch (error) {
            console.error('加载人脸信息失败:', error);
        }
    },

    // 更新人脸信息显示
    updateFaceInfoDisplay(data) {
        if (!data.registered) {
            // 隐藏人脸信息管理区域，显示注册区域
            const faceManagement = document.getElementById('faceManagement');
            const faceRegister = document.getElementById('faceRegister');
            if (faceManagement) faceManagement.style.display = 'none';
            if (faceRegister) faceRegister.style.display = 'block';
            return;
        }

        // 更新人脸信息显示
        const registeredFaceImage = document.getElementById('registeredFaceImage');
        const registrationTime = document.getElementById('faceRegistrationTime');
        const qualityScore = document.getElementById('faceQualityScore');

        if (registeredFaceImage && data.face_image_path) {
            // 确保使用相对路径，添加时间戳防止缓存
            let imagePath = data.face_image_path;
            // 如果路径以/开头，直接使用；否则添加/
            if (!imagePath.startsWith('/')) {
                imagePath = '/' + imagePath;
            }

            // 添加图片加载错误处理
            registeredFaceImage.onload = function() {
                console.log('人脸图片加载成功:', imagePath);
            };
            registeredFaceImage.onerror = function() {
                console.error('人脸图片加载失败:', imagePath);
                // 使用默认图片或隐藏
                registeredFaceImage.style.display = 'none';
            };

            registeredFaceImage.src = imagePath + '?t=' + Date.now();
            registeredFaceImage.style.display = 'block';
        } else {
            // 如果没有图片路径，隐藏图片元素
            if (registeredFaceImage) {
                registeredFaceImage.style.display = 'none';
            }
        }

        if (registrationTime) {
            registrationTime.textContent = data.registration_time || '-';
        }

        if (qualityScore) {
            qualityScore.textContent = data.quality_score ? data.quality_score.toFixed(1) : '-';
        }

        // 显示人脸信息管理区域，隐藏注册区域
        const faceManagement = document.getElementById('faceManagement');
        const faceRegister = document.getElementById('faceRegister');
        if (faceManagement) faceManagement.style.display = 'block';
        if (faceRegister) faceRegister.style.display = 'none';
    },

    // 删除人脸数据
    async deleteFaceData() {
        if (!confirm('确定要删除人脸信息吗？删除后需要重新注册。')) {
            return;
        }

        try {
            Utils.showLoading('正在删除人脸信息...');

            const response = await fetch('/api/faces/delete', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`
                }
            });

            const data = await response.json();
            Utils.hideLoading();

            if (response.ok) {
                Utils.showToast('人脸信息删除成功', 'success');

                // 重新加载人脸状态
                await this.loadFaceStatus();

                // 重置文件输入
                this.currentFile = null;
                const fileInput = document.getElementById('faceImageInput');
                if (fileInput) fileInput.value = '';
            } else {
                Utils.showToast(data.error || '删除失败', 'error');
            }
        } catch (error) {
            Utils.hideLoading();
            Utils.showToast('网络错误，请重试', 'error');
            console.error('Delete face error:', error);
        }
    },

    // 显示人脸预览模态框
    showFacePreviewModal() {
        const modal = document.getElementById('facePreviewModal');
        const modalImage = document.getElementById('modalFaceImage');
        const registeredImage = document.getElementById('registeredFaceImage');

        if (modal && modalImage && registeredImage) {
            modalImage.src = registeredImage.src;
            modal.style.display = 'block';
        }
    },

    // 隐藏人脸预览模态框
    hideFacePreviewModal() {
        const modal = document.getElementById('facePreviewModal');
        if (modal) {
            modal.style.display = 'none';
        }
    },

    // 更新人脸状态显示
    updateFaceStatus(data) {
        const statusElement = document.getElementById('faceStatusText') || document.getElementById('faceStatus');
        const actionButton = document.getElementById('faceActionButton');

        if (statusElement) {
            if (data.registered) {
                statusElement.textContent = '已注册';
                statusElement.className = 'status-registered';
            } else {
                statusElement.textContent = '未注册';
                statusElement.className = 'status-unregistered';
            }
        }

        if (actionButton) {
            if (data.registered) {
                actionButton.textContent = '重新注册';
                actionButton.className = 'btn btn-warning';
            } else {
                actionButton.textContent = '开始注册';
                actionButton.className = 'btn btn-primary';
            }
        }
    },

    // 绑定事件
    bindEvents() {
        // 人脸注册按钮
        document.getElementById('faceActionButton')?.addEventListener('click', () => {
            this.startFaceRegistration();
        });

        // 人脸识别按钮
        document.getElementById('faceRecognitionBtn')?.addEventListener('click', () => {
            this.startFaceRecognition();
        });

        // 提交人脸注册按钮
        document.getElementById('submitFace')?.addEventListener('click', () => {
            this.submitFaceRegistration();
        });

        // 重新拍照按钮
        document.getElementById('retakePhoto')?.addEventListener('click', () => {
            this.cancelImageUpload();
        });

        // 更新人脸按钮
        document.getElementById('updateFaceBtn')?.addEventListener('click', () => {
            this.startFaceRegistration();
        });

        // 删除人脸按钮
        document.getElementById('deleteFaceBtn')?.addEventListener('click', () => {
            this.deleteFaceData();
        });
    },

    // 开始人脸注册
    async startFaceRegistration() {
        // 显示注册区域，隐藏管理区域
        const faceRegister = document.getElementById('faceRegister');
        const faceManagement = document.getElementById('faceManagement');

        if (faceRegister) {
            faceRegister.style.display = 'block';
        }
        if (faceManagement) {
            faceManagement.style.display = 'none';
        }

        // 滚动到上传区域
        const uploadArea = document.getElementById('faceUploadArea');
        if (uploadArea) {
            uploadArea.scrollIntoView({ behavior: 'smooth' });
            Utils.showToast('请选择或拍摄人脸照片', 'info');
        }
    },

    // 提交人脸注册
    async submitFaceRegistration() {
        if (!this.currentFile) {
            Utils.showToast('请先选择图片', 'error');
            return;
        }

        // 验证用户登录状态
        if (!AppState.isAuthenticated) {
            Utils.showToast('请先登录后再进行人脸注册', 'warning');
            return;
        }

        try {
            Utils.showLoading('正在上传人脸图片...');

            const formData = new FormData();
            formData.append('image', this.currentFile);

            const response = await fetch('/api/faces/register', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`
                },
                body: formData
            });

            const data = await response.json();

            Utils.hideLoading();

            if (response.ok) {
                // 检查是否有相似度信息（更新时会有）
                if (data.similarity_score !== undefined) {
                    Utils.showToast(`人脸更新成功，相似度${data.similarity_score.toFixed(1)}%`, 'success');
                } else {
                    Utils.showToast('人脸注册成功', 'success');
                }
                this.cancelImageUpload(); // 清理预览
                await this.loadFaceStatus(); // 重新加载状态
            } else {
                const errorMessage = data.error || data.message || '人脸注册失败';

                // 如果是相似度验证失败，显示详细信息
                if (data.similarity_score !== undefined && data.threshold !== undefined) {
                    Utils.showToast(`相似度验证失败：${data.similarity_score.toFixed(1)}%（需≥${data.threshold}%）`, 'error');
                } else {
                    Utils.showToast(errorMessage, 'error');
                }
                console.error('Face registration error:', data);
            }
        } catch (error) {
            Utils.hideLoading();
            Utils.showToast('网络错误，请重试', 'error');
            console.error('Face registration error:', error);
        }
    },

    // 开始人脸识别
    async startFaceRecognition() {
        try {
            Utils.showLoading('正在启动人脸识别...');

            // 检查摄像头权限
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            stream.getTracks().forEach(track => track.stop());

            Utils.hideLoading();

            // 启动人脸识别流程
            await this.performFaceRecognition();
        } catch (error) {
            Utils.hideLoading();

            if (error.name === 'NotAllowedError') {
                Utils.showToast('请允许访问摄像头', 'error');
            } else {
                Utils.showToast('启动摄像头失败: ' + error.message, 'error');
            }
        }
    },

    // 执行人脸识别
    async performFaceRecognition() {
        try {
            Utils.showLoading('正在进行人脸识别...');

            // 这里应该调用人脸识别API
            // 由于这是前端代码，实际的人脸处理需要后端支持

            // 模拟人脸识别过程
            await new Promise(resolve => setTimeout(resolve, 3000));

            Utils.hideLoading();
            Utils.showToast('人脸识别成功', 'success');

            // 识别成功后可以进行相应操作，比如打开门禁
            this.onFaceRecognitionSuccess();
        } catch (error) {
            Utils.hideLoading();
            Utils.showToast('人脸识别失败: ' + error.message, 'error');
        }
    },

    // 显示访问二维码
    async showQRCode() {
        try {
            Utils.showLoading('检查访问申请状态...');

            // 获取用户的已通过申请
            const response = await Utils.request('/api/visits/applications?status=approved&limit=1');
            const approvedApplications = response.applications || [];

            if (approvedApplications.length === 0) {
                Utils.hideLoading();
                this.showStartApplicationModal();
                return;
            }

            // 使用最新的已通过申请生成二维码
            const application = approvedApplications[0];
            await this.showVisitQRCode(application);
            Utils.hideLoading();

        } catch (error) {
            Utils.hideLoading();
            console.error('获取访问申请失败:', error);
            Utils.showToast('获取访问申请失败，请重试', 'error');
        }
    },

    // 显示开始申请确认模态框
    showStartApplicationModal() {
        // 创建模态框HTML
        const modalHtml = `
            <div class="modal" id="startApplicationModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>访问申请</h3>
                        <button class="modal-close" onclick="UI.hideModal('startApplicationModal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center" style="padding: 20px;">
                            <div class="info-icon" style="font-size: 48px; color: #1976d2; margin-bottom: 20px;">
                                📋
                            </div>
                            <p style="font-size: 16px; color: #333; margin-bottom: 15px;">
                                您当前没有有效的访问申请
                            </p>
                            <p style="font-size: 14px; color: #666; margin-bottom: 25px;">
                                是否现在提交一个新的访问申请？
                            </p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline" onclick="UI.hideModal('startApplicationModal')">
                            取消
                        </button>
                        <button class="btn btn-primary" onclick="FacePage.startNewApplication()">
                            开始申请
                        </button>
                    </div>
                </div>
            </div>
        `;

        // 添加到页面并显示
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        UI.showModal('startApplicationModal');
    },

    // 开始新的访问申请
    startNewApplication() {
        UI.hideModal('startApplicationModal');
        // 切换到访问申请页面
        PageManager.switchPage(APP_CONFIG.PAGES.VISIT);
    },

    // 显示具体申请的访问二维码
    async showVisitQRCode(application) {
        try {
            // 生成访问二维码内容
            const qrContent = JSON.stringify({
                application_id: application.id,
                visitor_name: application.applicant_name || application.applicant?.real_name || '未知',
                visit_date: application.visit_date,
                visit_purpose: application.visit_purpose,
                status: 'approved',
                timestamp: Date.now()
            });

            // 生成二维码
            const canvas = document.createElement('canvas');
            await QRCode.toCanvas(canvas, qrContent, {
                width: 200,
                height: 200,
                color: {
                    dark: '#1976d2',
                    light: '#ffffff'
                }
            });

            // 显示二维码模态框
            this.showQRModal(canvas.toDataURL(), application);

        } catch (error) {
            Utils.hideLoading();
            console.error('生成访问二维码失败:', error);
            Utils.showToast('生成访问二维码失败', 'error');
        }
    },

    // 显示二维码模态框
    showQRModal(qrDataUrl, application) {
        // 创建模态框HTML
        const modalHtml = `
            <div class="modal" id="visitQRModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>访问二维码</h3>
                        <button class="modal-close" onclick="UI.hideModal('visitQRModal')">&times;</button>
                    </div>
                    <div class="modal-body text-center">
                        <div class="qr-code-container">
                            <img src="${qrDataUrl}" alt="访问二维码" style="width: 200px; height: 200px;" />
                        </div>
                        <div class="qr-code-info">
                            <p><strong>访客：</strong>${application.applicant_name || application.applicant?.real_name || '未知'}</p>
                            <p><strong>访问日期：</strong>${Utils.formatDate(application.visit_date)}</p>
                            <p><strong>访问事由：</strong>${application.visit_purpose}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 如果已存在模态框，先移除
        const existingModal = document.getElementById('visitQRModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 显示模态框
        const modal = document.getElementById('visitQRModal');
        if (modal) {
            modal.classList.add('active');
        }

        // 自动隐藏加载状态
        Utils.hideLoading();
    },

    // 人脸识别成功回调
    onFaceRecognitionSuccess() {
        // 可以在这里添加识别成功后的逻辑
        // 比如记录访问日志、打开门禁等
        Utils.showToast('验证通过，欢迎进入校园', 'success');
    }
};

// 个人中心页面逻辑
const ProfilePage = {
    // 加载页面
    async load() {
        await this.loadProfileData();
        this.bindEvents();
    },

    // 加载个人资料数据
    async loadProfileData() {
        try {
            // 加载统计数据
            await this.loadStatistics();

            // 加载校友档案（如果是校友）
            if (AppState.user.user_type === 'alumni') {
                await this.loadAlumniProfile();
            }
        } catch (error) {
            console.error('加载个人资料失败:', error);
        }
    },

    // 加载统计数据
    async loadStatistics() {
        try {
            // 获取访问次数 - 使用存在的接口或设置默认值
            try {
                const visitData = await Utils.request('/api/visits/statistics');
                const visitCountElement = document.getElementById('visitCount');
                if (visitCountElement) {
                    visitCountElement.textContent = visitData.total_visits || '0';
                }
            } catch (error) {
                console.warn('访问统计接口不可用，使用默认值');
                const visitCountElement = document.getElementById('visitCount');
                if (visitCountElement) {
                    visitCountElement.textContent = '0';
                }
            }

            // 获取人脸注册状态
            try {
                const faceData = await Utils.request('/api/faces/status');
                const faceRegisteredElement = document.getElementById('faceRegistered');
                if (faceRegisteredElement) {
                    faceRegisteredElement.textContent = faceData.registered ? '已注册' : '未注册';
                }
            } catch (error) {
                console.warn('人脸状态接口不可用，使用默认值');
                const faceRegisteredElement = document.getElementById('faceRegistered');
                if (faceRegisteredElement) {
                    faceRegisteredElement.textContent = '未注册';
                }
            }
        } catch (error) {
            console.error('加载统计数据失败:', error);
            // 设置默认值
            const visitCountElement = document.getElementById('visitCount');
            const faceRegisteredElement = document.getElementById('faceRegistered');
            if (visitCountElement) {
                visitCountElement.textContent = '0';
            }
            if (faceRegisteredElement) {
                faceRegisteredElement.textContent = '未注册';
            }
        }
    },

    // 加载审核统计数据
    async loadReviewStatistics() {
        try {
            // 获取访客申请统计数据
            const visitPending = await Utils.request('/api/visits/applications?status=pending&per_page=1');
            const visitApproved = await Utils.request('/api/visits/applications?status=approved&per_page=1');
            const visitRejected = await Utils.request('/api/visits/applications?status=rejected&per_page=1');

            // 获取学生出校申请统计数据
            const studentPending = await Utils.request('/api/student-exit/applications?status=pending&per_page=1');
            const studentApproved = await Utils.request('/api/student-exit/applications?status=approved&per_page=1');
            const studentRejected = await Utils.request('/api/student-exit/applications?status=rejected&per_page=1');
            const studentTeacherApproved = await Utils.request('/api/student-exit/applications?status=teacher_approved&per_page=1');

            // 计算总数 - 兼容不同的数据结构
            const visitPendingTotal = visitPending.pagination?.total || visitPending.total || 0;
            const visitApprovedTotal = visitApproved.pagination?.total || visitApproved.total || 0;
            const visitRejectedTotal = visitRejected.pagination?.total || visitRejected.total || 0;
            const studentPendingTotal = studentPending.pagination?.total || studentPending.total || 0;
            const studentApprovedTotal = studentApproved.pagination?.total || studentApproved.total || 0;
            const studentRejectedTotal = studentRejected.pagination?.total || studentRejected.total || 0;
            const studentTeacherApprovedTotal = studentTeacherApproved.pagination?.total || studentTeacherApproved.total || 0;

            const totalPending = visitPendingTotal + studentPendingTotal;
            const totalApproved = visitApprovedTotal + studentApprovedTotal;
            const totalRejected = visitRejectedTotal + studentRejectedTotal;

            // 更新统计显示
            const pendingElement = document.getElementById('pendingCount');
            const approvedElement = document.getElementById('approvedCount');
            const rejectedElement = document.getElementById('rejectedCount');
            const dashboardPendingElement = document.getElementById('dashboardPendingCount');

            if (pendingElement) {
                // 只显示真正待审核的数量，不包括待家长确认的
                pendingElement.textContent = totalPending;
            }
            if (approvedElement) {
                approvedElement.textContent = totalApproved;
            }
            if (rejectedElement) {
                rejectedElement.textContent = totalRejected;
            }
            if (dashboardPendingElement) {
                // 仪表板待处理事项 = 待审核 + 待家长确认
                const totalDashboardPending = totalPending + studentTeacherApprovedTotal;
                dashboardPendingElement.textContent = totalDashboardPending;
            }

        } catch (error) {
            console.error('加载审核统计失败:', error);
            // 设置默认值
            const pendingElement = document.getElementById('pendingCount');
            const approvedElement = document.getElementById('approvedCount');
            const rejectedElement = document.getElementById('rejectedCount');
            const dashboardPendingElement = document.getElementById('dashboardPendingCount');

            if (pendingElement) pendingElement.textContent = '0';
            if (approvedElement) approvedElement.textContent = '0';
            if (rejectedElement) rejectedElement.textContent = '0';
            if (dashboardPendingElement) dashboardPendingElement.textContent = '0';
        }
    },

    // 加载校友档案
    async loadAlumniProfile() {
        try {
            const data = await Utils.request('/api/alumni/profile');
            if (data.profile) {
                const profile = data.profile;
                document.getElementById('graduationYear').textContent = profile.graduation_year || '未知';
                document.getElementById('major').textContent = profile.major || '未知';
                document.getElementById('company').textContent = profile.company || '未知';
                document.getElementById('position').textContent = profile.position || '未知';
            }
        } catch (error) {
            console.error('加载校友档案失败:', error);
        }
    },

    // 绑定事件
    bindEvents() {
        // 编辑资料
        document.getElementById('editProfile')?.addEventListener('click', () => {
            this.showEditProfileModal();
        });

  
        // 修改密码
        document.getElementById('changePassword')?.addEventListener('click', () => {
            this.showChangePasswordModal();
        });

        // 我的二维码
        document.getElementById('myQRCode')?.addEventListener('click', async () => {
            await this.showAlumniCardQRCode();
        });

        // 访问记录
        document.getElementById('visitRecords')?.addEventListener('click', () => {
            this.showVisitRecordsModal();
        });

        // 关于我们
        document.getElementById('about')?.addEventListener('click', () => {
            this.showAboutModal();
        });

        // 审核管理
        document.getElementById('reviewManagement')?.addEventListener('click', () => {
            // 隐藏所有页面
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
            });

            // 显示审核页面
            const reviewPage = document.getElementById('reviewPage');
            if (reviewPage) {
                reviewPage.classList.add('active');
                ReviewPage.load();
            }
        });

        // 退出登录
        document.getElementById('logout')?.addEventListener('click', () => {
            Auth.logout();
        });

        // 绑定模态框事件
        this.bindModalEvents();
    },

    // 绑定模态框事件
    bindModalEvents() {
        // 编辑资料模态框
        document.getElementById('closeEditProfileModal')?.addEventListener('click', () => {
            UI.hideModal('editProfileModal');
        });
        document.getElementById('cancelEditProfile')?.addEventListener('click', () => {
            UI.hideModal('editProfileModal');
        });
        document.getElementById('editProfileForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProfile();
        });

    
        // 修改密码模态框
        document.getElementById('closeChangePasswordModal')?.addEventListener('click', () => {
            UI.hideModal('changePasswordModal');
        });
        document.getElementById('cancelChangePassword')?.addEventListener('click', () => {
            UI.hideModal('changePasswordModal');
        });
        document.getElementById('changePasswordForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.changePassword();
        });

        // 访问记录模态框
        document.getElementById('closeVisitRecordsModal')?.addEventListener('click', () => {
            UI.hideModal('visitRecordsModal');
        });

        // 关于我们模态框
        document.getElementById('closeAboutModal')?.addEventListener('click', () => {
            UI.hideModal('aboutModal');
        });
    },

    // 显示编辑资料模态框
    showEditProfileModal() {
        try {
            console.log('开始显示编辑资料模态框');

            // 检查AppState是否存在
            if (!AppState || !AppState.user) {
                console.error('AppState或AppState.user不存在');
                this.showToast('用户数据未加载，请稍后重试', 'error');
                return;
            }

            console.log('当前用户数据:', AppState.user);

            // 检查模态框元素是否存在
            const modal = document.getElementById('editProfileModal');
            if (!modal) {
                console.error('editProfileModal元素不存在');
                this.showToast('页面元素缺失，请刷新页面重试', 'error');
                return;
            }

            // 填充当前用户信息
            // 基本信息
            const editRealName = document.getElementById('editRealName');
            const editEmail = document.getElementById('editEmail');
            const editPhone = document.getElementById('editPhone');
            const editIdCard = document.getElementById('editIdCard');

            if (editRealName) editRealName.value = AppState.user.real_name || '';
            if (editEmail) editEmail.value = AppState.user.email || '';
            if (editPhone) editPhone.value = AppState.user.phone || '';
            if (editIdCard) editIdCard.value = AppState.user.id_card || '';

            // 校友档案信息
            const alumniProfile = AppState.user.alumni_profile;
            if (alumniProfile && typeof alumniProfile === 'object') {
                console.log('校友档案数据:', alumniProfile);

                const alumniGraduationYear = document.getElementById('alumniGraduationYear');
                const alumniStudentId = document.getElementById('alumniStudentId');
                const alumniClassName = document.getElementById('alumniClassName');
                const alumniDepartment = document.getElementById('alumniDepartment');
                const alumniMajor = document.getElementById('alumniMajor');
                const alumniContactTeacher = document.getElementById('alumniContactTeacher');
                const alumniContactTeacherPhone = document.getElementById('alumniContactTeacherPhone');
                const alumniEmergencyContact = document.getElementById('alumniEmergencyContact');
                const alumniEmergencyPhone = document.getElementById('alumniEmergencyPhone');
                const alumniCompany = document.getElementById('alumniCompany');
                const alumniPosition = document.getElementById('alumniPosition');
                const alumniIndustry = document.getElementById('alumniIndustry');

                if (alumniGraduationYear) alumniGraduationYear.value = alumniProfile.graduation_year || '';
                if (alumniStudentId) alumniStudentId.value = alumniProfile.student_id || '';
                if (alumniClassName) alumniClassName.value = alumniProfile.class_name || '';
                if (alumniDepartment) alumniDepartment.value = alumniProfile.department || '';
                if (alumniMajor) alumniMajor.value = alumniProfile.major || '';
                if (alumniContactTeacher) alumniContactTeacher.value = alumniProfile.contact_teacher || '';
                if (alumniContactTeacherPhone) alumniContactTeacherPhone.value = alumniProfile.contact_teacher_phone || '';
                if (alumniEmergencyContact) alumniEmergencyContact.value = alumniProfile.emergency_contact || '';
                if (alumniEmergencyPhone) alumniEmergencyPhone.value = alumniProfile.emergency_phone || '';
                if (alumniCompany) alumniCompany.value = alumniProfile.company || '';
                if (alumniPosition) alumniPosition.value = alumniProfile.position || '';
                if (alumniIndustry) alumniIndustry.value = alumniProfile.industry || '';
            }

            console.log('准备显示模态框');
            UI.showModal('editProfileModal');
            console.log('编辑资料模态框显示完成');

        } catch (error) {
            console.error('显示编辑资料模态框时发生错误:', error);
            // 显示错误提示给用户
            this.showToast('打开编辑页面失败，请稍后重试', 'error');
        }
    },

    // 保存个人资料
    async saveProfile() {
        try {
            // 基本信息
            const formData = {
                real_name: document.getElementById('editRealName')?.value || '',
                email: document.getElementById('editEmail')?.value || '',
                phone: document.getElementById('editPhone')?.value || '',
                id_card: document.getElementById('editIdCard')?.value || ''
            };

            // 校友档案信息
            const alumniData = {
                graduation_year: document.getElementById('alumniGraduationYear')?.value || '',
                student_id: document.getElementById('alumniStudentId')?.value || '',
                class_name: document.getElementById('alumniClassName')?.value || '',
                department: document.getElementById('alumniDepartment')?.value || '',
                major: document.getElementById('alumniMajor')?.value || '',
                contact_teacher: document.getElementById('alumniContactTeacher')?.value || '',
                contact_teacher_phone: document.getElementById('alumniContactTeacherPhone')?.value || '',
                emergency_contact: document.getElementById('alumniEmergencyContact')?.value || '',
                emergency_phone: document.getElementById('alumniEmergencyPhone')?.value || '',
                company: document.getElementById('alumniCompany')?.value || '',
                position: document.getElementById('alumniPosition')?.value || '',
                industry: document.getElementById('alumniIndustry')?.value || ''
            };

            // 只有当校友信息字段不为空时才添加到请求中
            const hasAlumniData = Object.values(alumniData).some(val => val.trim() !== '');
            if (hasAlumniData) {
                formData.alumni_profile = alumniData;
            }

            const data = await Utils.request('/api/auth/profile', {
                method: 'PUT',
                body: JSON.stringify(formData)
            });

            // 更新本地用户信息
            AppState.user = { ...AppState.user, ...data.user };
            localStorage.setItem(APP_CONFIG.STORAGE_KEYS.USER, JSON.stringify(AppState.user));

            // 更新UI显示
            UI.updateUserInfo();

            UI.hideModal('editProfileModal');
            Utils.showToast('校友档案保存成功', 'success');
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

  
    // 显示修改密码模态框
    showChangePasswordModal() {
        document.getElementById('currentPassword').value = '';
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmNewPassword').value = '';
        UI.showModal('changePasswordModal');
    },

    // 修改密码
    async changePassword() {
        try {
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmNewPassword').value;

            // 验证输入
            if (!currentPassword || !newPassword || !confirmPassword) {
                Utils.showToast('请填写所有密码字段', 'error');
                return;
            }

            if (newPassword !== confirmPassword) {
                Utils.showToast('新密码与确认密码不一致', 'error');
                return;
            }

            if (newPassword.length < 6) {
                Utils.showToast('新密码长度至少6位', 'error');
                return;
            }

            await Utils.request('/api/auth/change-password', {
                method: 'POST',
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            UI.hideModal('changePasswordModal');
            Utils.showToast('密码修改成功', 'success');
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 显示电子校友卡二维码
    async showAlumniCardQRCode() {
        console.log('=== showQRCode 开始执行 ===');

        if (!AppState.user) {
            console.log('用户未登录');
            Utils.showToast('请先登录', 'error');
            return;
        }

        console.log('当前用户:', AppState.user);

        // 生成二维码内容（可以包含用户ID、姓名等信息）
        const qrContent = JSON.stringify({
            user_id: AppState.user.id,
            real_name: AppState.user.real_name,
            user_type: AppState.user.user_type,
            timestamp: Date.now()
        });

        console.log('二维码内容:', qrContent);

        // 显示二维码模态框
        const qrModal = document.getElementById('qrCodeModal');
        console.log('qrCodeModal元素:', qrModal);

        if (qrModal) {
            // 清空并设置二维码容器
            const qrContainer = document.getElementById('qrCodeContainer');
            console.log('qrCodeContainer元素:', qrContainer);

            if (qrContainer) {
                // 清空容器
                qrContainer.innerHTML = '';

                // 创建二维码div
                const qrDiv = document.createElement('div');
                qrDiv.id = 'qrcode';
                qrDiv.style.textAlign = 'center';

                // 使用qrcode.js库生成二维码（参考电子校友卡实现）
                if (typeof QRCode !== 'undefined' && QRCode.toCanvas) {
                    console.log('使用QRCode.toCanvas生成二维码（参考电子校友卡）');

                    try {
                        // 创建canvas元素（参考电子校友卡实现）
                        const canvas = document.createElement('canvas');

                        // 生成访问二维码内容（简化版）
                        const visitQrContent = JSON.stringify({
                            type: 'visit_pass',
                            user_id: AppState.user.id,
                            real_name: AppState.user.real_name,
                            valid_from: new Date().toISOString(),
                            valid_until: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24小时有效期
                            timestamp: Date.now()
                        });

                        console.log('访问二维码内容:', visitQrContent);

                        // 使用toCanvas方法生成二维码（参考电子校友卡）
                        await QRCode.toCanvas(canvas, visitQrContent, {
                            width: 200,
                            height: 200,
                            margin: 1,
                            color: {
                                dark: '#1976d2',  // 使用电子校友卡的蓝色
                                light: '#ffffff'
                            },
                            errorCorrectionLevel: 'M'
                        });

                        // 将canvas添加到容器
                        qrDiv.appendChild(canvas);

                        // 添加访问凭证信息
                        const infoDiv = document.createElement('div');
                        infoDiv.style.cssText = `
                            margin-top: 15px;
                            padding: 10px;
                            background: #f8f9fa;
                            border-radius: 6px;
                            font-size: 12px;
                            color: #666;
                        `;

                        const validFrom = new Date().toLocaleString('zh-CN');
                        const validUntil = new Date(Date.now() + 24 * 60 * 60 * 1000).toLocaleString('zh-CN');

                        infoDiv.innerHTML = `
                            <div style="text-align: center; margin-bottom: 8px;">
                                <strong style="color: #1976d2; font-size: 14px;">访问凭证</strong>
                            </div>
                            <div style="margin-bottom: 4px;"><strong>访客:</strong> ${AppState.user.real_name}</div>
                            <div style="margin-bottom: 4px;"><strong>有效期:</strong></div>
                            <div style="margin-bottom: 2px; font-size: 11px;">从: ${validFrom}</div>
                            <div style="margin-bottom: 8px; font-size: 11px;">至: ${validUntil}</div>
                            <div style="text-align: center; font-size: 11px; color: #999;">
                                请在入口处出示此二维码
                            </div>
                        `;

                        qrDiv.appendChild(infoDiv);
                        console.log('访问二维码生成成功');

                    } catch (error) {
                        console.error('生成访问二维码时出错:', error);
                        // 如果生成失败，显示文本内容
                        qrDiv.innerHTML = `
                            <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; word-break: break-all; max-width: 300px; margin: 0 auto; border: 2px solid orange;">
                                <h4 style="color: #ff6600; margin-top: 0;">二维码生成失败</h4>
                                <p style="color: #666; font-size: 12px;">错误: ${error.message}</p>
                                <small style="color: #666;">二维码内容:</small><br>
                                <small>${qrContent}</small>
                            </div>
                        `;
                    }
                } else {
                    console.log('QRCode.toCanvas不可用，显示文本内容');
                    // 如果QRCode库不可用，显示文本内容作为备选
                    qrDiv.innerHTML = `
                        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; word-break: break-all; max-width: 300px; margin: 0 auto; border: 2px solid red;">
                            <h4 style="color: #ff0000; margin-top: 0;">访问凭证</h4>
                            <div style="margin-bottom: 8px;"><strong>访客:</strong> ${AppState.user.real_name}</div>
                            <div style="margin-bottom: 8px;"><strong>有效期:</strong> 24小时</div>
                            <small style="color: #666;">二维码内容:</small><br>
                            <small style="font-size: 10px;">${qrContent}</small>
                        </div>
                        <p style="margin-top: 10px; color: #666; font-size: 12px;">
                            请在入口处出示此凭证
                        </p>
                    `;
                }

                qrContainer.appendChild(qrDiv);
                console.log('二维码已添加到容器');
            } else {
                console.error('qrCodeContainer不存在');
            }

            console.log('准备显示模态框');
            UI.showModal('qrCodeModal');
        } else {
            console.error('qrCodeModal不存在');
            Utils.showToast('二维码功能暂时不可用', 'info');
        }
    },

    // 显示访问记录模态框
    async showVisitRecordsModal() {
        try {
            Utils.showLoading('加载访问记录...');

            const data = await Utils.request('/api/visits/records');
            const container = document.getElementById('visitRecordsContainer');

            if (data.records.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">暂无访问记录</p>';
            } else {
                container.innerHTML = data.records.map(record => this.renderVisitRecord(record)).join('');
            }

            Utils.hideLoading();
            UI.showModal('visitRecordsModal');
        } catch (error) {
            Utils.hideLoading();
            Utils.showToast('加载访问记录失败', 'error');
        }
    },

    // 渲染访问记录
    renderVisitRecord(record) {
        const statusClass = Utils.getStatusClass(record.status);
        const statusText = Utils.getStatusText(record.status);

        return `
            <div class="record-item">
                <div class="record-header">
                    <span class="record-date">${Utils.formatDate(record.visit_date)}</span>
                    <span class="record-status ${statusClass}">${statusText}</span>
                </div>
                <div class="record-content">
                    <div class="record-purpose">${record.visit_purpose}</div>
                    <div class="record-time">
                        ${Utils.formatTime(record.visit_time_start)} - ${Utils.formatTime(record.visit_time_end)}
                    </div>
                    ${record.actual_checkin_time ? `
                        <div class="record-checkin">
                            实际进入时间: ${new Date(record.actual_checkin_time).toLocaleString('zh-CN')}
                        </div>
                    ` : ''}
                    ${record.status === 'approved' ? `
                        <div class="record-qr">
                            <button class="btn btn-primary btn-sm" onclick="ProfilePage.showVisitQRCode(${record.id})">
                                <i class="fas fa-qrcode"></i> 访问二维码
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    },

    // 显示访问二维码
    async showVisitQRCode(applicationId) {
        try {
            Utils.showLoading('生成访问二维码...');

            // 获取访问申请详情
            const data = await Utils.request(`/api/visits/applications/${applicationId}`);
            const application = data.data;

            if (application.status !== 'approved') {
                Utils.showToast('只有已通过的申请才能生成访问二维码', 'error');
                return;
            }

            // 生成二维码内容
            const qrContent = JSON.stringify({
                application_id: application.id,
                visitor_name: application.applicant_name,
                visit_date: application.visit_date,
                visit_purpose: application.visit_purpose,
                status: 'approved',
                timestamp: Date.now()
            });

            // 显示访问二维码模态框
            this.showVisitQRCodeModal(qrContent, application);

            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            Utils.showToast('生成访问二维码失败: ' + error.message, 'error');
        }
    },

    // 显示访问二维码模态框
    showVisitQRCodeModal(qrContent, application) {
        // 创建访问二维码模态框
        let modal = document.getElementById('visitQRCodeModal');
        if (!modal) {
            const modalHtml = `
                <div class="modal" id="visitQRCodeModal">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>访问凭证二维码</h3>
                            <button class="modal-close" onclick="UI.hideModal('visitQRCodeModal')">&times;</button>
                        </div>
                        <div class="modal-body text-center">
                            <div id="visitQrCodeContainer" style="padding: 20px;">
                                <!-- QR码将在这里生成 -->
                            </div>
                            <div class="mt-3">
                                <p><strong>访客:</strong> ${application.applicant_name}</p>
                                <p><strong>访问日期:</strong> ${Utils.formatDate(application.visit_date)}</p>
                                <p><strong>访问事由:</strong> ${application.visit_purpose}</p>
                                <p class="text-muted small">请在入口处出示此二维码</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            modal = document.getElementById('visitQRCodeModal');
        }

        // 生成二维码
        const qrContainer = document.getElementById('visitQrCodeContainer');
        if (qrContainer) {
            // 清空容器
            qrContainer.innerHTML = '';

            // 创建二维码
            const qrDiv = document.createElement('div');
            qrDiv.id = 'visitQrCode';
            qrDiv.style.textAlign = 'center';

            // 使用qrcode.js库生成二维码
            if (typeof QRCode !== 'undefined') {
                new QRCode(qrDiv, {
                    text: qrContent,
                    width: 200,
                    height: 200,
                    colorDark: '#000000',
                    colorLight: '#ffffff',
                    correctLevel: QRCode.CorrectLevel.H
                });
            } else {
                // 如果没有qrcode.js库，显示文本内容作为备选
                qrDiv.innerHTML = `
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; word-break: break-all; max-width: 300px; margin: 0 auto;">
                        <small style="color: #666;">二维码内容:</small><br>
                        <small>${qrContent}</small>
                    </div>
                `;
            }

            qrContainer.appendChild(qrDiv);
        }

        // 显示模态框
        UI.showModal('visitQRCodeModal');
    },

    // 显示关于我们模态框
    showAboutModal() {
        UI.showModal('aboutModal');
    }
};

// 学生离校申请相关工具函数
const StudentExitUtils = {
    getStatusText(status) {
        const statusMap = {
            'pending': '待审核',
            'parent_approved': '家长已同意',
            'teacher_approved': '等待家长知晓',
            'approved': '已通过',
            'rejected': '已拒绝',
            'processing': '处理中',
            'completed': '已完成',
            'cancelled': '已取消'
        };
        return statusMap[status] || status;
    },

    getStatusClass(status) {
        const classMap = {
            'pending': 'status-pending',
            'parent_approved': 'status-processing',
            'teacher_approved': 'status-processing',
            'approved': 'status-approved',
            'rejected': 'status-rejected',
            'processing': 'status-processing',
            'completed': 'status-completed',
            'cancelled': 'status-cancelled'
        };
        return classMap[status] || 'status-unknown';
    },

    getExitTypeText(type) {
        const typeMap = {
            'weekend': '周末离校',
            'holiday': '节假日离校',
            'graduation': '毕业离校',
            'temporary': '临时离校',
            'emergency': '紧急离校'
        };
        return typeMap[type] || type;
    },

    formatDate(dateString) {
        if (!dateString) return '未设置';
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN');
    },

    formatTime(timeString) {
        if (!timeString) return '未设置';
        return timeString.substring(0, 5);
    }
};

// 审核管理页面逻辑
const ReviewPage = {
    currentFilter: 'pending',
    currentPage: 1,
    itemsPerPage: 10,

    // 加载页面
    async load() {
        // 检查用户权限 - 学生账号不能访问审批管理
        if (AppState.user && AppState.user.user_type === 'student') {
            Utils.showToast('学生账号没有权限访问审批管理页面', 'error');
            // 返回首页
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
            });
            const homePage = document.getElementById('homePage');
            if (homePage) {
                homePage.classList.add('active');
            }
            return;
        }

        await this.loadApplications();
        // 使用 HomePage 的统计函数
        if (typeof HomePage !== 'undefined' && HomePage.loadReviewStatistics) {
            await HomePage.loadReviewStatistics();
        }
        this.bindEvents();
    },

    // 绑定事件
    bindEvents() {
        // 筛选标签
        const filterTabs = document.querySelectorAll('.filter-tab');
        console.log(`找到 ${filterTabs.length} 个筛选标签`);
        filterTabs.forEach((tab, index) => {
            console.log(`绑定第 ${index + 1} 个筛选标签:`, tab.dataset.status);
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('筛选标签被点击:', tab.dataset.status);
                this.setFilter(tab.dataset.status);
            });
        });

        // 搜索框
        document.getElementById('searchInput')?.addEventListener('input', (e) => {
            this.searchApplications(e.target.value);
        });

        // 刷新按钮
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.loadApplications();
        });

        // 退出按钮
        document.getElementById('exitReview')?.addEventListener('click', () => {
            PageManager.switchPage(APP_CONFIG.PAGES.HOME);
        });

        // 刷新按钮
        document.getElementById('refreshReviewList')?.addEventListener('click', () => {
            this.loadApplications();
        });
    },

    // 设置筛选器
    setFilter(status) {
        console.log('设置筛选器:', status);
        this.currentFilter = status;
        this.currentPage = 1;

        // 更新标签状态
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.status === status) {
                tab.classList.add('active');
                console.log('激活标签:', status);
            }
        });

        this.loadApplications();
    },

    // 搜索申请
    searchApplications(keyword) {
        // 实现搜索逻辑
        this.loadApplications(keyword);
    },

    // 加载申请列表
    async loadApplications(searchKeyword = '') {
        try {
            Utils.showLoading('加载申请列表...');

            // 添加时间戳防止缓存
            const timestamp = Date.now();
            let allApplications = [];

            // 1. 加载访问申请
            let visitApiUrl = `/api/visits/applications?status=${this.currentFilter}&page=${this.currentPage}&per_page=${this.itemsPerPage}&t=${timestamp}`;
            if (searchKeyword) {
                visitApiUrl += `&search=${encodeURIComponent(searchKeyword)}`;
            }

            try {
                const visitData = await Utils.request(visitApiUrl);
                if (visitData.applications && visitData.applications.length > 0) {
                    // 为访问申请添加类型标识
                    const visitApplications = visitData.applications.map(app => ({
                        ...app,
                        application_type: 'visit',
                        application_status: app.application_status || app.status
                    }));
                    allApplications = allApplications.concat(visitApplications);
                    console.log(`成功加载 ${visitApplications.length} 个访问申请`);
                } else {
                    console.log('没有找到访问申请数据');
                }
            } catch (error) {
                console.warn('加载访问申请失败:', error);
                Utils.showToast('加载访问申请失败', 'warning');
            }

            // 2. 加载学生出校申请
            try {
                let studentExitApiUrl = `/api/student-exit/applications?status=${this.currentFilter}&page=${this.currentPage}&per_page=${this.itemsPerPage}&t=${timestamp}`;
                if (searchKeyword) {
                    studentExitApiUrl += `&search=${encodeURIComponent(searchKeyword)}`;
                }

                const studentExitData = await Utils.request(studentExitApiUrl);
                if (studentExitData.applications && studentExitData.applications.length > 0) {
                    // 为学生出校申请添加类型标识
                    const studentExitApplications = studentExitData.applications.map(app => ({
                        ...app,
                        application_type: 'student_exit',
                        application_status: app.application_status,
                        applicant_name: app.student_name,
                        visit_date: app.exit_date,
                        visit_time: app.exit_time,
                        purpose: app.reason
                    }));
                    allApplications = allApplications.concat(studentExitApplications);
                    console.log(`成功加载 ${studentExitApplications.length} 个学生出校申请`);
                } else {
                    console.log('没有找到学生出校申请数据');
                }
            } catch (error) {
                console.warn('加载学生出校申请失败:', error);
                // 如果只是功能不存在，不显示错误提示
                if (error.message && error.message.includes('404')) {
                    console.log('学生出校申请功能未启用');
                } else {
                    Utils.showToast('加载学生出校申请失败', 'warning');
                }
            }

            // 合并数据并渲染
            const combinedData = {
                applications: allApplications,
                total: allApplications.length,
                page: this.currentPage,
                per_page: this.itemsPerPage,
                pagination: {
                    current_page: this.currentPage,
                    pages: 1,
                    total: allApplications.length,
                    per_page: this.itemsPerPage
                }
            };

            this.renderApplications(combinedData);

            // 更新统计数据
            if (typeof HomePage !== 'undefined' && HomePage.loadReviewStatistics) {
                await HomePage.loadReviewStatistics();
            }

            // 如果两个API都没有数据，显示提示信息
            if (allApplications.length === 0) {
                Utils.showToast('暂无申请数据', 'info');
            }

            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            console.error('加载申请列表失败:', error);
            Utils.showToast('加载申请列表失败', 'error');
        }
    },

    // 渲染申请列表
    renderApplications(data) {
        const container = document.getElementById('reviewApplicationsList');

        if (data.applications.length === 0) {
            container.innerHTML = '<p class="text-center text-secondary">暂无申请记录</p>';
            return;
        }

        container.innerHTML = data.applications.map(app => this.renderApplicationItem(app)).join('');

        // 绑定操作按钮事件
        this.bindApplicationEvents();

        // 渲染分页
        this.renderPagination(data.pagination);
    },

    // 获取申请人姓名
    getApplicantName(app, isStudentExit) {
        if (isStudentExit) {
            // 学生离校申请：优先显示 student_name，其次是 applicant_name，最后是 applicant.real_name
            if (app.student_name) {
                return app.student_name;
            } else if (app.applicant_name) {
                return app.applicant_name;
            } else if (app.applicant && app.applicant.real_name) {
                return app.applicant.real_name;
            } else {
                return `学生申请 #${app.id}`;
            }
        } else {
            // 访客申请：优先显示 applicant_name，其次是 applicant.real_name
            if (app.applicant_name) {
                return app.applicant_name;
            } else if (app.applicant && app.applicant.real_name) {
                return app.applicant.real_name;
            } else {
                return '未知申请人';
            }
        }
    },

    // 渲染申请项
    renderApplicationItem(app) {
        // 判断申请类型
        const isStudentExit = app.exit_date !== undefined || app.application_type === 'student_exit';

        let statusClass, statusText, title, details;

        if (isStudentExit) {
            // 学生离校申请
            statusClass = StudentExitUtils.getStatusClass(app.application_status);
            statusText = StudentExitUtils.getStatusText(app.application_status);
            title = `${StudentExitUtils.getExitTypeText(app.exit_type || 'temporary')}申请`;

            const returnDate = app.return_date || app.return_time || '';
            const returnTime = app.return_time || app.return_time_end || '';

            details = `
                <div><strong>离校类型:</strong> ${StudentExitUtils.getExitTypeText(app.exit_type || 'temporary')}</div>
                <div><strong>离校时间:</strong> ${StudentExitUtils.formatDate(app.exit_date)} ${StudentExitUtils.formatTime(app.exit_time_start || '')}</div>
                ${returnDate || returnTime ? `<div><strong>返校时间:</strong> ${StudentExitUtils.formatDate(returnDate)} ${StudentExitUtils.formatTime(returnTime)}</div>` : ''}
                <div><strong>离校事由:</strong> ${app.exit_reason || '未提供'}</div>
                <div><strong>联系电话:</strong> ${app.contact_phone || '未提供'}</div>
            `;
        } else {
            // 访客申请
            statusClass = Utils.getStatusClass(app.application_status);
            statusText = Utils.getStatusText(app.application_status);
            title = '访客申请';

            details = `
                <div><strong>拜访对象:</strong> ${app.target_person || '未指定'}</div>
                <div><strong>访问时间:</strong> ${Utils.formatTime(app.visit_time_start || app.time_start)} - ${Utils.formatTime(app.visit_time_end || app.time_end)}</div>
                <div><strong>访问事由:</strong> ${app.visit_purpose || '未提供'}</div>
                ${app.visitor_phone ? `<div><strong>联系电话:</strong> ${app.visitor_phone}</div>` : ''}
            `;
        }

        return `
            <div class="application-item" data-id="${app.id}" data-type="${isStudentExit ? 'student_exit' : 'visit'}" style="flex-direction: column !important; padding: 0 !important; margin-bottom: 6px !important; border-radius: 6px !important; overflow: hidden !important; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08) !important; border: 1px solid var(--border) !important; background: var(--surface) !important;">
                <!-- 头部区域 -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color-light) 100%); color: white;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 28px; height: 28px; background: rgba(255, 255, 255, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; color: white;">
                            <i class="ri-user-3-line"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; font-size: 12px; font-weight: 600; color: white;">${this.getApplicantName(app, isStudentExit)}</h3>
                            <p style="margin: 1px 0 0 0; font-size: 10px; color: rgba(255, 255, 255, 0.8);">${Utils.formatDate(isStudentExit ? app.exit_date : app.visit_date)}</p>
                        </div>
                    </div>
                    <span class="application-status ${statusClass}" style="background: rgba(255, 255, 255, 0.2) !important; color: white !important; border: none !important; font-weight: 500 !important; padding: 3px 8px !important; border-radius: 12px !important; font-size: 10px !important;">${statusText}</span>
                </div>

                <!-- 内容区域 -->
                <div style="padding: 8px 10px;">
                    <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 6px; font-size: 12px; font-weight: 600; color: var(--text-primary);">
                        <i class="ri-file-list-3-line" style="color: var(--primary-color); font-size: 12px;"></i>
                        <span>${title}</span>
                    </div>

                    <div style="background: var(--background-secondary); border-radius: 4px; padding: 6px 8px; margin-bottom: 6px;">
                        ${details.replace(/div>/g, 'div style="margin-bottom: 3px; font-size: 11px; color: var(--text-secondary);">').replace(/strong>/g, 'strong style="color: var(--text-primary); font-weight: 500; min-width: 60px; display: inline-block;">')}
                    </div>

                    ${app.review_note ? `
                        <div style="background: #f8f9fa; border-left: 3px solid var(--info-color); border-radius: 3px; padding: 5px 8px; display: flex; align-items: flex-start; gap: 5px; margin-bottom: 6px;">
                            <i class="ri-message-3-line" style="color: var(--info-color); font-size: 12px; margin-top: 1px;"></i>
                            <div style="flex: 1; font-size: 11px; color: var(--text-secondary);">
                                <strong style="color: var(--text-primary);">审核意见:</strong> ${app.review_note}
                            </div>
                        </div>
                    ` : ''}
                </div>

                <!-- 操作区域 -->
                <div style="padding: 6px 10px; background: var(--background-secondary); border-top: 1px solid var(--border);">
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                        ${this.renderApplicationActions(app, isStudentExit)}
                    </div>
                </div>
            </div>
        `;
    },

    // 渲染申请操作按钮
    renderApplicationActions(app, isStudentExit = false) {
        let actionButtons = '';

        if (['pending', 'parent_approved'].includes(app.application_status) && app.can_approve) {
            actionButtons += `
                <button class="btn btn-success btn-sm approve-btn" data-id="${app.id}" data-type="${isStudentExit ? 'student_exit' : 'visit'}" style="min-width: 50px; display: flex; align-items: center; justify-content: center; gap: 3px; font-size: 10px; padding: 5px 8px; border-radius: 3px; margin-right: 4px;">
                    <i class="ri-check-line"></i>
                    通过
                </button>
                <button class="btn btn-danger btn-sm reject-btn" data-id="${app.id}" data-type="${isStudentExit ? 'student_exit' : 'visit'}" style="min-width: 50px; display: flex; align-items: center; justify-content: center; gap: 3px; font-size: 10px; padding: 5px 8px; border-radius: 3px; margin-right: 4px;">
                    <i class="ri-close-line"></i>
                    拒绝
                </button>
            `;
        } else if (app.application_status === 'approved' || app.application_status === 'rejected') {
            // 为已审批的申请添加撤销按钮 - 只有老师和管理员可以撤销
            const userType = AppState.user ? AppState.user.user_type : '';
            const isTeacherOrAdmin = userType === 'teacher' || userType === 'admin';

            if (isTeacherOrAdmin) {
                actionButtons += `
                    <button class="btn btn-warning btn-sm revoke-btn" data-id="${app.id}" data-type="${isStudentExit ? 'student_exit' : 'visit'}" style="min-width: 50px; display: flex; align-items: center; justify-content: center; gap: 3px; font-size: 10px; padding: 5px 8px; border-radius: 3px; margin-right: 4px;">
                        <i class="ri-refresh-line"></i>
                        撤销
                    </button>
                `;
            }
        }

        // 详情按钮始终在右侧
        return `
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 4px;">
                <div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
                    ${actionButtons}
                </div>
                <button class="btn btn-primary btn-sm details-btn" data-id="${app.id}" data-type="${isStudentExit ? 'student_exit' : 'visit'}" style="min-width: 60px; display: flex; align-items: center; justify-content: center; gap: 3px; font-size: 10px; padding: 5px 8px; border-radius: 3px; background: var(--primary-color); color: white; border: none;">
                    <i class="ri-eye-line"></i>
                    查看详情
                </button>
            </div>
        `;
    },

    // 绑定申请操作事件
    bindApplicationEvents() {
        // 通过按钮
        document.querySelectorAll('.approve-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const type = btn.dataset.type;
                await this.reviewApplication(id, true, '', type);
            });
        });

        // 拒绝按钮
        document.querySelectorAll('.reject-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const type = btn.dataset.type;
                const reason = prompt('请输入拒绝理由:');
                if (reason && reason.trim()) {
                    await this.reviewApplication(id, false, reason.trim(), type);
                } else {
                    Utils.showToast('请输入拒绝理由', 'warning');
                }
            });
        });

        // 撤销审批按钮
        document.querySelectorAll('.revoke-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const type = btn.dataset.type;
                await this.revokeApplication(id, type);
            });
        });

        // 详情按钮
        document.querySelectorAll('.details-btn').forEach(btn => {
            console.log(`[DEBUG] 绑定详情按钮事件: ID=${btn.dataset.id}, type=${btn.dataset.type}`);
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                const type = btn.dataset.type;
                console.log(`[DEBUG] 点击详情按钮: ID=${id}, type=${type}`);
                this.showApplicationDetails(id, type);
            });
        });
    },

    // 审核申请
    async reviewApplication(id, approve, note = '', type = 'visit') {
        try {
            const endpoint = type === 'student_exit'
                ? `/api/student-exit/applications/${id}/approve`
                : `/api/visits/applications/${id}/approve`;

            // 学生离校申请和访客申请使用不同的数据格式
            const requestData = type === 'student_exit'
                ? {
                    action: approve ? 'approve' : 'reject',
                    note: note
                }
                : {
                    approve: approve,
                    note: note
                };

            await Utils.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(requestData)
            });

            Utils.showToast(`申请已${approve ? '通过' : '拒绝'}`, 'success');
            // 重新加载审批管理页面
            await this.loadApplications();
            // 重新加载统计信息
            if (typeof HomePage !== 'undefined' && HomePage.loadReviewStatistics) {
                await HomePage.loadReviewStatistics();
            }
            // 重新加载待审批申请（如果在首页）
            if (typeof HomePage !== 'undefined' && HomePage.loadPendingApprovals) {
                await HomePage.loadPendingApprovals();
            }
            // 重新加载最近申请
            if (typeof HomePage !== 'undefined' && HomePage.loadRecentApplications) {
                await HomePage.loadRecentApplications();
            }
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 撤销审批
    async revokeApplication(id, type = 'visit') {
        try {
            // 确认撤销
            const confirmed = confirm('确定要撤销这个申请的审批吗？撤销后申请将重新变为待审核状态。');
            if (!confirmed) {
                return;
            }

            Utils.showLoading('撤销审批中...');

            const endpoint = type === 'student_exit'
                ? `/api/student-exit/applications/${id}/revoke`
                : `/api/visits/applications/${id}/revoke`;

            await Utils.request(endpoint, {
                method: 'POST'
            });

            Utils.showToast('审批已撤销', 'success');
            // 重新加载审批管理页面
            await this.loadApplications();
            // 重新加载统计信息
            if (typeof HomePage !== 'undefined' && HomePage.loadReviewStatistics) {
                await HomePage.loadReviewStatistics();
            }
            // 重新加载待审批申请（如果在首页）
            if (typeof HomePage !== 'undefined' && HomePage.loadPendingApprovals) {
                await HomePage.loadPendingApprovals();
            }
            // 重新加载最近申请
            if (typeof HomePage !== 'undefined' && HomePage.loadRecentApplications) {
                await HomePage.loadRecentApplications();
            }
        } catch (error) {
            // 处理详细的权限错误信息
            let errorMessage = error.message;
            if (error.detail) {
                errorMessage += `\n${error.detail}`;
            }
            Utils.showToast(errorMessage, 'error');
        } finally {
            // 确保加载状态被清除
            Utils.hideLoading();
        }
    },

    // 显示申请详情
    async showApplicationDetails(id, type = 'visit') {
        try {
            console.log(`[DEBUG] 显示申请详情: ID=${id}, type=${type}`);
            const endpoint = type === 'student_exit'
                ? `/api/student-exit/applications/${id}`
                : `/api/visits/applications/${id}`;

            const data = await Utils.request(endpoint);
            const app = data.application;
            console.log(`[DEBUG] API返回的申请数据:`, app);

            // 判断申请类型
            const isStudentExit = app.exit_date !== undefined || app.application_type === 'student_exit';
            console.log(`[DEBUG] 是否为学生出校申请: ${isStudentExit}`);

            let detailsContent;

            if (isStudentExit) {
                // 学生离校申请详情
                const studentName = this.getApplicantName(app, true);
                console.log(`[DEBUG] 获取到的学生姓名: "${studentName}"`);
                console.log(`[DEBUG] 用于姓名提取的原始数据:`, {
                    student_name: app.student_name,
                    applicant_name: app.applicant_name,
                    applicant: app.applicant
                });
                detailsContent = `
                    <div class="application-details" style="text-align: left; padding: 10px;">
                        <h4 style="text-align: center; margin-bottom: 15px; color: #333;">学生离校申请详情</h4>
                        <div class="detail-section" style="margin-bottom: 15px;">
                            <h5 style="color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px; font-size: 14px;">申请人信息</h5>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>学生姓名:</strong> ${studentName}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>班级:</strong> ${app.class_name || '未提供'}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>联系电话:</strong> ${app.emergency_phone || app.contact_phone || '未提供'}</p>
                        </div>
                        <div class="detail-section" style="margin-bottom: 15px;">
                            <h5 style="color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px; font-size: 14px;">离校信息</h5>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>离校类型:</strong> ${StudentExitUtils.getExitTypeText(app.exit_type || 'temporary')}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>离校日期:</strong> ${StudentExitUtils.formatDate(app.exit_date)}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>离校时间:</strong> ${StudentExitUtils.formatTime(app.exit_time_start || '')}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>返校日期:</strong> ${StudentExitUtils.formatDate(app.return_date)}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>返校时间:</strong> ${StudentExitUtils.formatTime(app.return_time || '')}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>离校事由:</strong> ${app.exit_reason || '未提供'}</p>
                        </div>
                        <div class="detail-section" style="margin-bottom: 10px;">
                            <h5 style="color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px; font-size: 14px;">申请状态</h5>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>当前状态:</strong> <span class="status-${app.application_status}">${StudentExitUtils.getStatusText(app.application_status)}</span></p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>老师审批:</strong> ${app.teacher_approval_status === 'approved' ? '✅ 已通过' : app.teacher_approval_status === 'rejected' ? '❌ 已拒绝' : '⏳ 未审批'}</p>
                            ${app.teacher_approval_status === 'approved' ? `
                                <p style="margin: 6px 0; font-size: 13px;"><strong>家长确认:</strong> ${app.parent_approval_status === 'approved' ? '✅ 已确认' : '⏳ 未确认'}</p>
                            ` : ''}
                            <p style="margin: 6px 0; font-size: 13px;"><strong>申请时间:</strong> ${new Date(app.created_at).toLocaleString('zh-CN')}</p>
                            ${app.teacher_approval_time ? `
                                <p style="margin: 6px 0; font-size: 13px;"><strong>老师审批时间:</strong> ${new Date(app.teacher_approval_time).toLocaleString('zh-CN')}</p>
                            ` : ''}
                            ${app.parent_approval_time ? `
                                <p style="margin: 6px 0; font-size: 13px;"><strong>家长确认时间:</strong> ${new Date(app.parent_approval_time).toLocaleString('zh-CN')}</p>
                            ` : ''}
                        </div>
                    </div>
                `;
            } else {
                // 访客申请详情
                const visitorName = app.visitor_name || (app.applicant ? app.applicant.real_name : '未知访客');
                detailsContent = `
                    <div class="application-details" style="text-align: left; padding: 10px;">
                        <h4 style="text-align: center; margin-bottom: 15px; color: #333;">访客申请详情</h4>
                        <div class="detail-section" style="margin-bottom: 15px;">
                            <h5 style="color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px; font-size: 14px;">访客信息</h5>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>访客姓名:</strong> ${visitorName}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>联系电话:</strong> ${app.visitor_phone || '未提供'}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>身份证:</strong> ${app.visitor_id_card || '未提供'}</p>
                        </div>
                        <div class="detail-section" style="margin-bottom: 15px;">
                            <h5 style="color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px; font-size: 14px;">访问信息</h5>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>访问日期:</strong> ${Utils.formatDate(app.visit_date)}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>访问时间:</strong> ${Utils.formatTime(app.visit_time_start || app.time_start)} - ${Utils.formatTime(app.visit_time_end || app.time_end)}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>访问事由:</strong> ${app.visit_purpose}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>拜访对象:</strong> ${app.target_person || '未指定'}</p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>对象电话:</strong> ${app.target_phone || '未提供'}</p>
                        </div>
                        <div class="detail-section" style="margin-bottom: 10px;">
                            <h5 style="color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px; font-size: 14px;">申请状态</h5>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>当前状态:</strong> <span class="status-${app.application_status}">${Utils.getStatusText(app.application_status)}</span></p>
                            <p style="margin: 6px 0; font-size: 13px;"><strong>申请时间:</strong> ${new Date(app.created_at).toLocaleString('zh-CN')}</p>
                            ${app.reviewed_at ? `
                                <p style="margin: 6px 0; font-size: 13px;"><strong>审核时间:</strong> ${new Date(app.reviewed_at).toLocaleString('zh-CN')}</p>
                            ` : ''}
                            ${app.reviewed_by ? `
                                <p style="margin: 6px 0; font-size: 13px;"><strong>审核人:</strong> ${app.reviewer_name || '未知'}</p>
                            ` : ''}
                            ${app.review_note ? `
                                <p style="margin: 6px 0; font-size: 13px;"><strong>审核意见:</strong> ${app.review_note}</p>
                            ` : ''}
                        </div>
                    </div>
                `;
            }

            // 生成操作按钮
            const actionButtons = this.generateActionButtons(app, isStudentExit);

            // 显示详情模态框
            UI.showModal('applicationDetailsModal');
            const modalBody = document.querySelector('#applicationDetailsModal .modal-body');
            const modalFooter = document.querySelector('#applicationDetailsModal .modal-footer');

            if (modalBody) {
                modalBody.innerHTML = detailsContent;
                if (modalFooter) {
                    modalFooter.innerHTML = actionButtons;
                }
            } else {
                // 如果模态框不存在，创建一个临时的模态框
                const modalHtml = `
                    <div class="modal" id="tempApplicationDetailsModal" style="background: rgba(0,0,0,0.5) !important;">
                        <div class="modal-dialog modal-lg" style="margin: 10px auto !important; max-width: 500px !important;">
                            <div class="modal-content" style="margin: 0 !important; padding: 0 !important; border: none !important; border-radius: 8px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.15) !important;">
                                <div class="modal-header" style="padding: 15px 20px !important; border-bottom: 1px solid #e0e0e0 !important; background: #fff !important;">
                                    <h5 class="modal-title" style="margin: 0 !important; font-size: 16px !important; color: #333 !important;">申请详情</h5>
                                    <button type="button" class="btn-close" onclick="UI.hideModal('tempApplicationDetailsModal')" style="font-size: 18px !important; opacity: 0.7 !important;"></button>
                                </div>
                                <div class="modal-body" style="padding: 0 !important; text-align: left; background: #fff !important;">
                                    ${detailsContent}
                                </div>
                                <div class="modal-footer" style="padding: 12px 20px !important; border-top: 1px solid #e0e0e0 !important; background: #fff !important;">
                                    ${actionButtons}
                                    <button type="button" class="btn btn-secondary" onclick="UI.hideModal('tempApplicationDetailsModal')" style="font-size: 13px !important; padding: 6px 12px !important;">关闭</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                const tempModal = document.getElementById('tempApplicationDetailsModal');
                if (tempModal) {
                    UI.showModal('tempApplicationDetailsModal');
                    // 绑定操作按钮事件
                    this.bindActionButtons(tempModal, app, isStudentExit);
                    // 手动绑定关闭事件，移除临时模态框
                    const closeButtons = tempModal.querySelectorAll('.btn-close, .btn-secondary');
                    closeButtons.forEach(button => {
                        button.addEventListener('click', () => {
                            UI.hideModal('tempApplicationDetailsModal');
                            tempModal.remove();
                        });
                    });
                } else {
                    // 绑定现有模态框的操作按钮事件
                    this.bindActionButtons(document, app, isStudentExit);
                }
            }
        } catch (error) {
            Utils.showToast('加载申请详情失败', 'error');
        }
    },

    // 生成操作按钮
    generateActionButtons(app, isStudentExit) {
        if (!AppState.user) return '';

        const userType = AppState.user.user_type;
        let buttons = '';

        if (isStudentExit) {
            // 学生出校申请的按钮
            if (userType === 'parent' && app.teacher_approval_status === 'approved' && app.parent_approval_status === 'pending') {
                // 家长确认按钮（只有老师审批通过后才显示）
                buttons += `
                    <button type="button" class="btn btn-success" onclick="ReviewPage.parentAcknowledge(${app.id})">
                        <i class="ri-check-line"></i> 确认知晓
                    </button>
                `;
            } else if (userType === 'teacher' && AppState.user.is_class_teacher && app.teacher_approval_status === 'pending') {
                // 班主任审批按钮
                buttons += `
                    <button type="button" class="btn btn-success" onclick="ReviewPage.teacherApprove(${app.id})">
                        <i class="ri-check-line"></i> 批准
                    </button>
                    <button type="button" class="btn btn-danger" onclick="ReviewPage.teacherReject(${app.id})">
                        <i class="ri-close-line"></i> 拒绝
                    </button>
                `;
            }
        } else {
            // 访问申请的按钮
            if (userType === 'teacher' && ['pending'].includes(app.application_status)) {
                buttons += `
                    <button type="button" class="btn btn-success" onclick="ReviewPage.approveVisit(${app.id})">
                        <i class="ri-check-line"></i> 批准
                    </button>
                    <button type="button" class="btn btn-danger" onclick="ReviewPage.rejectVisit(${app.id})">
                        <i class="ri-close-line"></i> 拒绝
                    </button>
                `;
            }
        }

        return buttons;
    },

    // 绑定操作按钮事件
    bindActionButtons(container, app, isStudentExit) {
        // 这里可以添加更复杂的事件绑定逻辑
        // 目前使用onclick内联事件，简单直接
    },

    // 家长确认申请
    async parentAcknowledge(applicationId) {
        try {
            const data = await Utils.request('/api/student-exit/applications/' + applicationId + '/acknowledge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    note: '家长已知晓并同意此申请'
                })
            });

            if (data.success) {
                Utils.showToast('已确认知晓此申请', 'success');
                // 关闭模态框
                UI.hideModal('applicationDetailsModal');
                UI.hideModal('tempApplicationDetailsModal');
                // 刷新列表
                if (typeof HomePage !== 'undefined' && HomePage.loadRecentApplications) {
                    await HomePage.loadRecentApplications();
                }
                if (typeof ReviewPage !== 'undefined' && ReviewPage.loadApplications) {
                    await ReviewPage.loadApplications();
                }
            } else {
                Utils.showToast(data.error || '确认失败', 'error');
            }
        } catch (error) {
            console.error('家长确认申请失败:', error);
            Utils.showToast('确认失败，请重试', 'error');
        }
    },

    // 老师批准申请
    async teacherApprove(applicationId) {
        try {
            const data = await Utils.request('/api/student-exit/applications/' + applicationId + '/approve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'approve',
                    note: '班主任批准'
                })
            });

            if (data.success) {
                Utils.showToast('已批准申请', 'success');
                UI.hideModal('applicationDetailsModal');
                UI.hideModal('tempApplicationDetailsModal');
                // 刷新列表
                if (typeof HomePage !== 'undefined' && HomePage.loadRecentApplications) {
                    await HomePage.loadRecentApplications();
                }
                if (typeof ReviewPage !== 'undefined' && ReviewPage.loadApplications) {
                    await ReviewPage.loadApplications();
                }
            } else {
                Utils.showToast(data.error || '批准失败', 'error');
            }
        } catch (error) {
            console.error('老师批准申请失败:', error);
            Utils.showToast('批准失败，请重试', 'error');
        }
    },

    // 老师拒绝申请
    async teacherReject(applicationId) {
        try {
            const data = await Utils.request('/api/student-exit/applications/' + applicationId + '/approve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'reject',
                    note: '班主任拒绝'
                })
            });

            if (data.success) {
                Utils.showToast('已拒绝申请', 'success');
                UI.hideModal('applicationDetailsModal');
                UI.hideModal('tempApplicationDetailsModal');
                // 刷新列表
                if (typeof HomePage !== 'undefined' && HomePage.loadRecentApplications) {
                    await HomePage.loadRecentApplications();
                }
                if (typeof ReviewPage !== 'undefined' && ReviewPage.loadApplications) {
                    await ReviewPage.loadApplications();
                }
            } else {
                Utils.showToast(data.error || '拒绝失败', 'error');
            }
        } catch (error) {
            console.error('老师拒绝申请失败:', error);
            Utils.showToast('拒绝失败，请重试', 'error');
        }
    },

    // 渲染分页
    renderPagination(pagination) {
        const container = document.getElementById('reviewPagination');
        if (!container) {
            console.warn('reviewPagination container not found');
            return;
        }

        // 检查分页数据是否存在
        if (!pagination) {
            console.warn('pagination data is undefined');
            container.innerHTML = '';
            return;
        }

        // 兼容不同的分页数据结构
        const totalPages = pagination.total_pages || pagination.pages || 1;
        const currentPage = pagination.current_page || pagination.page || 1;

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let paginationHtml = '<div class="pagination">';

        // 上一页
        if (currentPage > 1) {
            paginationHtml += `<button class="btn btn-sm" onclick="ReviewPage.goToPage(${currentPage - 1})">上一页</button>`;
        }

        // 页码
        for (let i = 1; i <= totalPages; i++) {
            const activeClass = i === currentPage ? 'active' : '';
            paginationHtml += `<button class="btn btn-sm ${activeClass}" onclick="ReviewPage.goToPage(${i})">${i}</button>`;
        }

        // 下一页
        if (currentPage < totalPages) {
            paginationHtml += `<button class="btn btn-sm" onclick="ReviewPage.goToPage(${currentPage + 1})">下一页</button>`;
        }

        paginationHtml += '</div>';
        container.innerHTML = paginationHtml;
    },

    // 跳转到指定页面
    goToPage(page) {
        this.currentPage = page;
        this.loadApplications();
    }
};

// 应用初始化
document.addEventListener('DOMContentLoaded', async () => {
    console.log('=== 应用初始化开始 ===');

    try {
        // 初始化UI
        UI.init();

        // 初始化认证状态
        await Auth.initAuth();

        // 隐藏加载动画
        UI.hideLoading();

        // 根据认证状态显示相应页面
        if (AppState.isAuthenticated) {
            PageManager.switchPage(APP_CONFIG.PAGES.HOME);
        } else if (!window.isLoggingOut) {
            UI.showLoginModal();
        }

        console.log('=== 应用初始化完成 ===');
    } catch (error) {
        console.error('应用初始化失败:', error);
        Utils.showToast('应用初始化失败，请刷新页面重试', 'error');
        UI.hideLoading();
    }
});

// 导出全局对象（如果需要）
window.App = {
    config: APP_CONFIG,
    state: AppState,
    utils: Utils,
    auth: Auth,
    ui: UI,
    pageManager: PageManager,
    homePage: HomePage,
    visitPage: VisitPage,
    facePage: FacePage,
    profilePage: ProfilePage,
    reviewPage: ReviewPage
};

// 全局函数，用于HTML中的onclick调用
function showFacePreviewModal() {
    FacePage.showFacePreviewModal();
}

function hideFacePreviewModal() {
    FacePage.hideFacePreviewModal();
}

// 增强的最近申请刷新函数
async function refreshRecentApplications() {
    const refreshBtn = document.getElementById('refreshRecentApplications');
    const refreshIcon = document.getElementById('refreshIcon');
    const refreshText = document.getElementById('refreshText');
    const recentApplicationsContainer = document.getElementById('recentApplications');

    if (!refreshBtn || !refreshIcon || !refreshText || !recentApplicationsContainer) {
        console.error('刷新按钮元素未找到');
        return;
    }

    try {
        console.log('=== 开始刷新最近申请 ===');

        // 检查认证状态
        console.log('认证状态检查:', {
            isAuthenticated: AppState.isAuthenticated,
            hasToken: !!AppState.token,
            userId: AppState.user?.id,
            userType: AppState.user?.user_type,
            tokenLength: AppState.token?.length
        });

        if (!AppState.isAuthenticated || !AppState.token) {
            throw new Error('用户未登录或令牌无效');
        }

        // 显示加载状态
        refreshIcon.className = 'ri-loader-4-line animate-spin';
        refreshText.textContent = '刷新中...';
        refreshBtn.disabled = true;

        // 记录刷新开始时间
        const startTime = Date.now();

        // 调用原始刷新函数
        await HomePage.loadRecentApplications();

        // 记录刷新完成时间
        const endTime = Date.now();
        const duration = endTime - startTime;

        console.log(`=== 刷新完成，耗时: ${duration}ms ===`);

        // 检查容器内容
        const containerContent = recentApplicationsContainer.innerHTML;
        const hasApplications = containerContent.includes('application-item') || containerContent.includes('recent-application-container');

        console.log('容器内容检查:', {
            hasContent: !!containerContent,
            hasApplications: hasApplications,
            contentLength: containerContent.length
        });

        // 恢复按钮状态
        refreshIcon.className = 'ri-refresh-line';
        refreshText.textContent = '刷新';
        refreshBtn.disabled = false;

        // 如果没有申请内容，显示调试信息
        if (!hasApplications) {
            console.log('⚠️ 警告: 没有找到申请内容');

            // 在容器中显示调试信息（仅在开发模式）
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                const debugInfo = document.createElement('div');
                debugInfo.style.cssText = `
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 4px;
                    padding: 10px;
                    margin-top: 10px;
                    font-size: 12px;
                    color: #856404;
                `;
                debugInfo.innerHTML = `
                    <strong>调试信息：</strong><br>
                    - 刷新时间: ${new Date().toLocaleTimeString()}<br>
                    - 刷新耗时: ${duration}ms<br>
                    - 用户状态: ${AppState.isAuthenticated ? '已登录' : '未登录'}<br>
                    - 用户类型: ${AppState.user ? AppState.user.user_type : '未知'}<br>
                    - Token存在: ${!!AppState.token}<br>
                    - API地址: ${window.APP_CONFIG ? window.APP_CONFIG.API_URL : '未知'}
                `;
                recentApplicationsContainer.appendChild(debugInfo);
            }
        } else {
            console.log('✅ 刷新成功，找到申请内容');
        }

    } catch (error) {
        console.error('刷新最近申请失败:', error);

        // 恢复按钮状态
        refreshIcon.className = 'ri-refresh-line';
        refreshText.textContent = '刷新';
        refreshBtn.disabled = false;

        // 显示错误信息
        if (recentApplicationsContainer) {
            recentApplicationsContainer.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #dc3545;">
                    <i class="ri-error-warning-line" style="font-size: 24px;"></i>
                    <p>刷新失败，请重试</p>
                    <p style="font-size: 12px; color: #6c757d;">错误: ${error.message}</p>
                </div>
            `;
        }
    }
};

// 将主要对象导出到全局作用域
window.HomePage = HomePage;
window.Auth = Auth;
window.UI = UI;
window.Utils = Utils;
window.AppState = AppState;
window.APP_CONFIG = APP_CONFIG;
window.PageManager = PageManager;