/**
 * 移动端应用JavaScript - 版本 5.0
 * 校友入校登记系统
 * 更新时间: 2025-01-16 11:00
 */

// 应用配置
const APP_CONFIG = {
    API_BASE_URL: 'http://localhost:5000/api',
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

        let response;
        try {
            response = await fetch(APP_CONFIG.API_BASE_URL + url, fetchOptions);
        } catch (fetchError) {
            // 简化错误处理 - 开发环境使用HTTP模式
            console.warn('API请求失败:', fetchError.message);
            throw new Error(`网络连接失败：请确保开发服务器正在运行 (${APP_CONFIG.API_BASE_URL})`);
        }

        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            // 如果响应不是JSON格式，使用默认错误消息
            if (!response.ok) {
                throw new Error(`请求失败 (${response.status})`);
            }
            data = {};
        }

        if (!response.ok) {
            throw new Error(data.error || `请求失败 (${response.status})`);
        }

        return data;
    },

    // 显示Toast提示
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastMessage = toast.querySelector('.toast-message');
        const toastIcon = toast.querySelector('.toast-icon');

        // 设置消息和样式
        toastMessage.textContent = message;
        toast.className = `toast ${type} show`;

        // 设置图标
        const icons = {
            success: 'ri-check-line',
            error: 'ri-close-line',
            warning: 'ri-alert-line',
            info: 'ri-information-line'
        };
        toastIcon.className = `toast-icon ${icons[type] || icons.info}`;

        // 3秒后自动隐藏
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
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
            const data = await Utils.request('/auth/login', {
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

            Utils.showToast('登录成功', 'success');
            return data;
        } catch (error) {
            Utils.showToast(error.message, 'error');
            throw error;
        }
    },

    // 注册
    async register(userData) {
        try {
            const data = await Utils.request('/auth/register', {
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
        AppState.token = null;
        AppState.user = null;
        AppState.isAuthenticated = false;

        // 清除本地存储
        localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.TOKEN);
        localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.USER);

        // 不显示提示，避免在初始化时显示
        // Utils.showToast('已退出登录', 'info');

        // 跳转到登录页面
        UI.showLoginModal();
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
                    await Utils.request('/auth/profile', {
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
        if (!AppState.isAuthenticated) {
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
        document.getElementById(modalId).classList.add('active');
    },

    // 隐藏模态框
    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    },

    // 显示登录模态框
    showLoginModal() {
        this.showModal('loginModal');
        this.restoreRememberedCredentials();
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

            // 根据用户类型调整API请求
            let apiUrl = '/visits/applications?per_page=3';
            if (AppState.user.user_type === 'teacher' || AppState.user.user_type === 'admin') {
                // 教师和管理员优先显示待审核的申请
                apiUrl = '/visits/applications?status=pending&per_page=3';
            }

            const data = await Utils.request(apiUrl);
            const container = document.getElementById('recentApplications');

            if (data.applications.length === 0) {
                if (AppState.user.user_type === 'teacher' || AppState.user.user_type === 'admin') {
                    container.innerHTML = '<p class="text-center text-secondary">暂无待审核申请</p>';
                } else {
                    container.innerHTML = '<p class="text-center text-secondary">暂无申请记录</p>';
                }
                return;
            }

            container.innerHTML = data.applications.map(app => this.renderRecentApplication(app)).join('');

            // 绑定点击事件（如果是教师/管理员）
            if (AppState.user.user_type === 'teacher' || AppState.user.user_type === 'admin') {
                this.bindApplicationClickEvents();
            }
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

    // 渲染最近申请卡片
    renderRecentApplication(app) {
        const isTeacherOrAdmin = AppState.user.user_type === 'teacher' || AppState.user.user_type === 'admin';
        const statusClass = Utils.getStatusClass(app.application_status);
        const statusText = Utils.getStatusText(app.application_status);

        return `
            <div class="application-item recent-application-card ${isTeacherOrAdmin ? 'clickable' : ''}"
                 data-id="${app.id}" data-status="${app.application_status}">
                <div class="application-header">
                    <span class="application-date">${Utils.formatDate(app.visit_date)}</span>
                    <span class="application-status ${statusClass}">
                        ${statusText}
                    </span>
                </div>
                <div class="application-purpose">${app.visit_purpose}</div>
                <div class="application-target">
                    ${isTeacherOrAdmin && app.applicant ?
                        `申请人: ${app.applicant.real_name}` :
                        (app.target_person ? `拜访对象: ${app.target_person}` : '')
                    }
                </div>
                ${isTeacherOrAdmin && app.application_status === 'pending' ? `
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
                ${isTeacherOrAdmin ? `
                <div class="review-hint">
                    <small><i class="ri-arrow-right-line"></i> 点击查看详情或进入审核页面</small>
                </div>
                ` : ''}
            </div>
        `;
    },

    // 绑定申请卡片点击事件
    bindApplicationClickEvents() {
        // 卡片点击事件 - 进入审核页面并筛选对应状态
        document.querySelectorAll('.recent-application-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // 如果点击的是按钮，不触发卡片点击事件
                if (e.target.closest('.quick-review-actions')) {
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
    },

    // 快速审核申请
    async quickReviewApplication(id, approve, note = '') {
        try {
            await Utils.request(`/visits/applications/${id}/approve`, {
                method: 'POST',
                body: JSON.stringify({
                    approve: approve,
                    note: note
                })
            });

            Utils.showToast(`申请已${approve ? '通过' : '拒绝'}`, 'success');

            // 重新加载最近申请
            await this.loadRecentApplications();
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 跳转到审核页面
    goToReviewPage(statusFilter = 'pending') {
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
        // 快速申请
        document.getElementById('quickVisit')?.addEventListener('click', () => {
            PageManager.switchPage(APP_CONFIG.PAGES.VISIT);
        });

        // 人脸注册
        document.getElementById('quickFace')?.addEventListener('click', () => {
            PageManager.switchPage(APP_CONFIG.PAGES.FACE);
        });

        // 我的二维码
        document.getElementById('quickQR')?.addEventListener('click', () => {
            if (Auth.checkAuth()) {
                ProfilePage.showQRCode();
            }
        });

        // 车辆管理
        document.getElementById('quickVehicle')?.addEventListener('click', () => {
            Utils.showToast('车辆管理功能开发中', 'info');
        });
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

        // 设置最小日期和默认日期
        Utils.setMinDate('visitDate');
        Utils.setDefaultDate('visitDate');

        // 设置默认时间为整点
        Utils.setDefaultTime('timeStart');
        Utils.setDefaultTime('timeEnd');

        // 确保结束时间在开始时间之后
        Utils.setEndTime('timeStart', 'timeEnd');

        // 自动填充访问人信息
        this.autoFillVisitorInfo();

        // 初始化同行人信息
        this.initCompanionInfo();

        // 绑定工作ID查询事件
        this.bindWorkIdLookup();

        // 绑定车辆信息显示事件
        this.bindVehicleToggle();

        // 设置时间范围变化监听
        const timeStart = document.getElementById('timeStart');
        const timeEnd = document.getElementById('timeEnd');

        timeStart.addEventListener('change', () => {
            // 自动设置结束时间为开始时间后1小时
            Utils.setEndTime('timeStart', 'timeEnd');
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // 验证表单
            if (!this.validateForm()) {
                return;
            }

            // 安全获取表单数据
            const getValue = (elementId) => {
                const element = document.getElementById(elementId);
                return element ? element.value : '';
            };

            const formData = {
                visit_date: getValue('visitDate'),
                visit_time_start: getValue('timeStart'),  // 后端期望 %H:%M 格式，不需要添加:00
                visit_time_end: getValue('timeEnd'),      // 后端期望 %H:%M 格式，不需要添加:00
                visit_purpose: getValue('visitPurpose'),
                target_person: getValue('targetPerson'),
                target_department: getValue('targetDepartment'),
                target_work_id: getValue('targetWorkId')
            };

            // 添加访问人信息
            formData.visitor_info = {
                name: getValue('visitorName'),
                phone: getValue('visitorPhone'),
                email: getValue('visitorEmail'),
                id_card: getValue('visitorIdCard')
            };

            // 获取同行人信息
            const companions = this.getCompanionInfo();
            if (companions.length > 0) {
                formData.companions = companions;
            }

            // 如果有车辆信息，添加到表单数据
            const hasVehicleCheckbox = document.getElementById('hasVehicle');
            if (hasVehicleCheckbox && hasVehicleCheckbox.checked) {
                formData.has_vehicle = true;
                formData.vehicle_info = {
                    license_plate: getValue('licensePlate'),
                    vehicle_type: getValue('vehicleType'),
                    vehicle_color: getValue('vehicleColor'),
                    vehicle_brand: getValue('vehicleBrand')
                };
            } else {
                formData.has_vehicle = false;
            }

            try {
                await Utils.request('/visits/applications', {
                    method: 'POST',
                    body: JSON.stringify(formData)
                });

                Utils.showToast('访问申请提交成功', 'success');
                form.reset();
                // 重新设置默认值
                Utils.setDefaultDate('visitDate');
                Utils.setDefaultTime('timeStart');
                Utils.setDefaultTime('timeEnd');
                Utils.setEndTime('timeStart', 'timeEnd');
                this.autoFillVisitorInfo(); // 重新填充访问人信息
                this.loadVisitHistory();
            } catch (error) {
                Utils.showToast(error.message, 'error');
            }
        });
    },

    // 绑定工作ID查询事件
    bindWorkIdLookup() {
        const workIdInput = document.getElementById('targetWorkId');
        if (!workIdInput) {
            return; // 如果元素不存在，直接返回
        }

        let debounceTimer;

        workIdInput.addEventListener('input', (e) => {
            const workId = e.target.value.trim();

            if (workId.length < 3) {
                this.clearTargetInfo();
                return;
            }

            // 防抖处理
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(async () => {
                await this.lookupTargetPerson(workId);
            }, 500);
        });

        workIdInput.addEventListener('blur', async (e) => {
            const workId = e.target.value.trim();
            if (workId) {
                await this.lookupTargetPerson(workId);
            }
        });
    },

    // 查询拜访对象信息
    async lookupTargetPerson(workId) {
        try {
            const data = await Utils.request(`/target-persons/search?work_id=${workId}`);

            const targetPersonInput = document.getElementById('targetPerson');
            const targetDepartmentInput = document.getElementById('targetDepartment');

            if (targetPersonInput) targetPersonInput.value = data.name;
            if (targetDepartmentInput) targetDepartmentInput.value = data.department;

            Utils.showToast('已自动填充拜访对象信息', 'success');
        } catch (error) {
            this.clearTargetInfo();
            if (workId.length >= 6) { // 只有输入了完整的ID才显示错误
                Utils.showToast('未找到该工作ID对应的拜访对象', 'error');
            }
        }
    },

    // 清空拜访对象信息
    clearTargetInfo() {
        const targetPersonInput = document.getElementById('targetPerson');
        const targetDepartmentInput = document.getElementById('targetDepartment');

        if (targetPersonInput) targetPersonInput.value = '';
        if (targetDepartmentInput) targetDepartmentInput.value = '';
    },

    // 绑定车辆信息显示事件
    bindVehicleToggle() {
        const hasVehicleCheckbox = document.getElementById('hasVehicle');
        const vehicleInfoDiv = document.getElementById('vehicleInfo');

        if (!hasVehicleCheckbox || !vehicleInfoDiv) {
            return; // 如果元素不存在，直接返回
        }

        hasVehicleCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                vehicleInfoDiv.style.display = 'block';
                // 设置必填字段
                const licensePlateInput = document.getElementById('licensePlate');
                const vehicleTypeInput = document.getElementById('vehicleType');
                const vehicleColorInput = document.getElementById('vehicleColor');

                if (licensePlateInput) licensePlateInput.required = true;
                if (vehicleTypeInput) vehicleTypeInput.required = true;
                if (vehicleColorInput) vehicleColorInput.required = true;
            } else {
                vehicleInfoDiv.style.display = 'none';
                // 清空必填要求
                const licensePlateInput = document.getElementById('licensePlate');
                const vehicleTypeInput = document.getElementById('vehicleType');
                const vehicleColorInput = document.getElementById('vehicleColor');

                if (licensePlateInput) licensePlateInput.required = false;
                if (vehicleTypeInput) vehicleTypeInput.required = false;
                if (vehicleColorInput) vehicleColorInput.required = false;
            }
        });
    },

    // 加载申请历史
    async loadVisitHistory() {
        try {
            const data = await Utils.request('/visits/applications');
            const container = document.getElementById('visitHistory');

            if (data.applications.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">暂无申请记录</p>';
                return;
            }

            container.innerHTML = data.applications.map(app => this.renderHistoryItem(app)).join('');

            // 绑定历史项点击事件
            this.bindHistoryItemClickEvents();
        } catch (error) {
            console.error('加载申请历史失败:', error);
        }
    },

    // 渲染历史申请项
    renderHistoryItem(app) {
        const statusClass = Utils.getStatusClass(app.application_status);
        const statusText = Utils.getStatusText(app.application_status);

        return `
            <div class="application-item history-item clickable" data-application='${JSON.stringify(app).replace(/'/g, '&apos;')}'>
                <div class="application-header">
                    <span class="application-date">${Utils.formatDate(app.visit_date)}</span>
                    <span class="application-status ${statusClass}">
                        ${statusText}
                    </span>
                </div>
                <div class="application-purpose">${app.visit_purpose}</div>
                <div class="application-target">
                    <div class="target-info">
                        <span class="time-info">
                            <i class="ri-time-line"></i>
                            ${Utils.formatTime(app.visit_time_start)} - ${Utils.formatTime(app.visit_time_end)}
                        </span>
                        ${app.target_person ? `
                        <span class="person-info">
                            <i class="ri-user-line"></i>
                            ${app.target_person}
                        </span>
                        ` : ''}
                        ${app.target_department ? `
                        <span class="dept-info">
                            <i class="ri-building-line"></i>
                            ${app.target_department}
                        </span>
                        ` : ''}
                    </div>
                </div>
                <div class="history-hint">
                    <small><i class="ri-file-copy-line"></i> 点击快速填充表单</small>
                </div>
            </div>
        `;
    },

    // 绑定历史项点击事件
    bindHistoryItemClickEvents() {
        document.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', () => {
                try {
                    const appData = JSON.parse(item.dataset.application.replace(/&apos;/g, "'"));
                    this.fillFormFromHistory(appData);
                } catch (error) {
                    console.error('解析历史申请数据失败:', error);
                    Utils.showToast('无法使用该历史申请数据', 'error');
                }
            });
        });
    },

    // 从历史申请填充表单
    fillFormFromHistory(appData) {
        try {
            // 填充访问目的
            const visitPurposeSelect = document.getElementById('visitPurpose');
            if (visitPurposeSelect && appData.visit_purpose) {
                // 检查是否已存在该选项
                let optionExists = false;
                for (let option of visitPurposeSelect.options) {
                    if (option.value === appData.visit_purpose) {
                        optionExists = true;
                        break;
                    }
                }

                if (!optionExists) {
                    // 添加新选项
                    const newOption = document.createElement('option');
                    newOption.value = appData.visit_purpose;
                    newOption.textContent = appData.visit_purpose;
                    visitPurposeSelect.appendChild(newOption);
                }

                visitPurposeSelect.value = appData.visit_purpose;
            }

            // 填充拜访对象信息
            if (appData.target_work_id) {
                const targetWorkIdInput = document.getElementById('targetWorkId');
                if (targetWorkIdInput) {
                    targetWorkIdInput.value = appData.target_work_id;
                    // 触发查询以填充其他信息
                    this.lookupTargetPerson(appData.target_work_id);
                }
            } else {
                // 直接填充已知信息
                const targetPersonInput = document.getElementById('targetPerson');
                const targetDepartmentInput = document.getElementById('targetDepartment');

                if (targetPersonInput && appData.target_person) {
                    targetPersonInput.value = appData.target_person;
                }
                if (targetDepartmentInput && appData.target_department) {
                    targetDepartmentInput.value = appData.target_department;
                }
            }

            // 重置时间到默认值（因为历史申请的时间已过期）
            Utils.setDefaultTime('timeStart');
            Utils.setDefaultTime('timeEnd');
            Utils.setEndTime('timeStart', 'timeEnd');

            // 重新设置默认日期（因为历史申请的日期已过期）
            Utils.setDefaultDate('visitDate');

            // 显示成功提示
            Utils.showToast('已从历史申请填充表单，请修改时间后提交', 'success');

            // 滚动到表单顶部
            const form = document.getElementById('visitApplicationForm');
            if (form) {
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

        } catch (error) {
            console.error('填充表单失败:', error);
            Utils.showToast('填充表单失败，请手动填写', 'error');
        }
    },

    // 自动填充访问人信息
    autoFillVisitorInfo() {
        if (!AppState.user || !AppState.isAuthenticated) {
            return;
        }

        const visitorNameInput = document.getElementById('visitorName');
        const visitorPhoneInput = document.getElementById('visitorPhone');
        const visitorEmailInput = document.getElementById('visitorEmail');

        if (visitorNameInput && AppState.user.real_name) {
            visitorNameInput.value = AppState.user.real_name;
        }

        if (visitorPhoneInput && AppState.user.phone) {
            visitorPhoneInput.value = AppState.user.phone;
        }

        if (visitorEmailInput && AppState.user.email) {
            visitorEmailInput.value = AppState.user.email;
        }
    },

    // 初始化同行人信息
    initCompanionInfo() {
        // 绑定添加同行人按钮
        const addCompanionBtn = document.getElementById('addCompanion');
        if (addCompanionBtn) {
            addCompanionBtn.addEventListener('click', () => {
                this.addCompanion();
            });
        }

        // 初始化同行人列表状态
        const companionList = document.getElementById('companionList');
        if (companionList && document.querySelectorAll('.companion-item').length === 0) {
            // 显示空状态提示
            companionList.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <i class="ri-user-unfollow-line text-3xl mb-2"></i>
                    <p class="text-sm">暂无同行人信息</p>
                    <p class="text-xs text-gray-400 mt-1">点击"添加同行人"按钮添加同行人</p>
                </div>
            `;
        }
    },

    // 添加同行人
    addCompanion() {
        const companionList = document.getElementById('companionList');
        if (!companionList) return;

        // 清除空状态提示
        const emptyState = companionList.querySelector('.text-center');
        if (emptyState) {
            emptyState.remove();
        }

        // 计算当前同行人数量
        const companionItems = companionList.querySelectorAll('.companion-item');
        const companionCount = companionItems.length;
        const companionItem = document.createElement('div');
        companionItem.className = 'companion-item';
        companionItem.innerHTML = `
            <div class="companion-header">
                <span class="companion-title">同行人 ${companionCount + 1}</span>
                <button type="button" class="btn btn-sm btn-outline-danger remove-companion"
                        title="删除同行人">
                    <i class="ri-delete-bin-line"></i>
                </button>
            </div>
            <div class="companion-form">
                <div class="form-row">
                    <div class="form-group">
                        <label for="companion${companionCount}_name">姓名 *</label>
                        <input type="text" id="companion${companionCount}_name" class="form-control"
                               placeholder="请输入同行人姓名" required>
                    </div>
                    <div class="form-group">
                        <label for="companion${companionCount}_phone">联系方式 *</label>
                        <input type="tel" id="companion${companionCount}_phone" class="form-control"
                               placeholder="请输入手机号" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="companion${companionCount}_id_card">身份证号码</label>
                        <input type="text" id="companion${companionCount}_id_card" class="form-control"
                               placeholder="请输入身份证号码">
                    </div>
                </div>
            </div>
        `;

        companionList.appendChild(companionItem);

        // 绑定删除按钮事件
        const removeBtn = companionItem.querySelector('.remove-companion');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                this.removeCompanion(companionItem);
            });
        }

        // 显示所有删除按钮
        this.updateRemoveButtons();
    },

    // 删除同行人
    removeCompanion(companionItem) {
        const companionList = document.getElementById('companionList');
        if (!companionList) {
            return;
        }

        // 直接删除同行人，允许删除所有同行人
        companionItem.remove();
        this.updateCompanionTitles();
        this.updateRemoveButtons();

        // 如果删除后没有同行人了，显示提示信息
        if (companionList.children.length === 0) {
            companionList.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <i class="ri-user-unfollow-line text-3xl mb-2"></i>
                    <p class="text-sm">暂无同行人信息</p>
                    <p class="text-xs text-gray-400 mt-1">点击"添加同行人"按钮添加同行人</p>
                </div>
            `;
        }
    },

    // 更新同行人标题
    updateCompanionTitles() {
        const companionItems = document.querySelectorAll('.companion-item');
        companionItems.forEach((item, index) => {
            const titleElement = item.querySelector('.companion-title');
            if (titleElement) {
                titleElement.textContent = `同行人 ${index + 1}`;
            }
        });
    },

    // 更新删除按钮显示状态
    updateRemoveButtons() {
        const companionItems = document.querySelectorAll('.companion-item');
        companionItems.forEach((item, index) => {
            const removeBtn = item.querySelector('.remove-companion');
            if (removeBtn) {
                // 始终显示删除按钮，允许用户删除所有同行人
                removeBtn.style.display = 'block';
            }
        });
    },

    // 获取同行人信息
    getCompanionInfo() {
        const companions = [];
        const companionItems = document.querySelectorAll('.companion-item');

        companionItems.forEach((item, index) => {
            const name = document.getElementById(`companion${index}_name`)?.value?.trim();
            const phone = document.getElementById(`companion${index}_phone`)?.value?.trim();
            const idCard = document.getElementById(`companion${index}_id_card`)?.value?.trim();

            if (name && phone) {
                companions.push({
                    name: name,
                    phone: phone,
                    id_card: idCard || ''
                });
            }
        });

        return companions;
    },

    // 验证表单
    validateForm() {
        const getValue = (elementId) => {
            const element = document.getElementById(elementId);
            return element ? element.value.trim() : '';
        };

        // 验证基本字段
        const requiredFields = [
            { id: 'visitorName', label: '访问人姓名' },
            { id: 'visitorPhone', label: '访问人联系方式' },
            { id: 'visitDate', label: '访问日期' },
            { id: 'timeStart', label: '开始时间' },
            { id: 'timeEnd', label: '结束时间' },
            { id: 'visitPurpose', label: '访问目的' },
            { id: 'targetPerson', label: '拜访对象' }
        ];

        for (const field of requiredFields) {
            const value = getValue(field.id);
            if (!value) {
                Utils.showToast(`${field.label}不能为空`, 'warning');
                document.getElementById(field.id)?.focus();
                return false;
            }
        }

        // 验证手机号格式
        const visitorPhone = getValue('visitorPhone');
        if (!Utils.validatePhone(visitorPhone)) {
            Utils.showToast('访问人联系方式格式不正确', 'warning');
            document.getElementById('visitorPhone')?.focus();
            return false;
        }

        // 验证邮箱格式（如果填写了）
        const visitorEmail = getValue('visitorEmail');
        if (visitorEmail && !Utils.validateEmail(visitorEmail)) {
            Utils.showToast('访问人邮箱格式不正确', 'warning');
            document.getElementById('visitorEmail')?.focus();
            return false;
        }

        // 验证身份证格式（如果填写了）
        const visitorIdCard = getValue('visitorIdCard');
        if (visitorIdCard && !Utils.validateIdCard(visitorIdCard)) {
            Utils.showToast('访问人身份证号码格式不正确', 'warning');
            document.getElementById('visitorIdCard')?.focus();
            return false;
        }

        // 验证同行人信息
        const companions = this.getCompanionInfo();
        for (let i = 0; i < companions.length; i++) {
            const companion = companions[i];

            // 验证同行人手机号格式
            if (companion.phone && !Utils.validatePhone(companion.phone)) {
                Utils.showToast(`同行人${i + 1}联系方式格式不正确`, 'warning');
                document.getElementById(`companion${i}_phone`)?.focus();
                return false;
            }

            // 验证同行人身份证格式（如果填写了）
            if (companion.id_card && !Utils.validateIdCard(companion.id_card)) {
                Utils.showToast(`同行人${i + 1}身份证号码格式不正确`, 'warning');
                document.getElementById(`companion${i}_id_card`)?.focus();
                return false;
            }
        }

        // 验证时间逻辑
        const timeStart = getValue('timeStart');
        const timeEnd = getValue('timeEnd');
        if (timeStart >= timeEnd) {
            Utils.showToast('结束时间必须晚于开始时间', 'warning');
            document.getElementById('timeEnd')?.focus();
            return false;
        }

        // 验证车辆信息（如果选择了有车辆）
        const hasVehicle = document.getElementById('hasVehicle')?.checked;
        if (hasVehicle) {
            const licensePlate = getValue('licensePlate');
            const vehicleType = getValue('vehicleType');
            const vehicleColor = getValue('vehicleColor');

            if (!licensePlate || licensePlate.trim() === '') {
                Utils.showToast('请填写车牌号', 'warning');
                document.getElementById('licensePlate')?.focus();
                return false;
            }
        }

        return true;
    },

    // 为教师协助填充表单
    fillFormForTeacher(applicantData) {
        try {
            // 填充访问人信息（申请人信息）
            const visitorNameInput = document.getElementById('visitorName');
            const visitorPhoneInput = document.getElementById('visitorPhone');
            const visitorEmailInput = document.getElementById('visitorEmail');

            if (visitorNameInput && applicantData.real_name) {
                visitorNameInput.value = applicantData.real_name;
            }
            if (visitorPhoneInput && applicantData.phone) {
                visitorPhoneInput.value = applicantData.phone;
            }
            if (visitorEmailInput && applicantData.email) {
                visitorEmailInput.value = applicantData.email;
            }

            Utils.showToast('已为申请人填充基本信息', 'success');

            // 滚动到表单顶部
            const form = document.getElementById('visitApplicationForm');
            if (form) {
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

        } catch (error) {
            console.error('协助填充失败:', error);
            Utils.showToast('协助填充失败，请手动填写', 'error');
        }
    },
};

// 人脸识别页面逻辑
const FacePage = {
    // 加载页面
    async load() {
        this.initUpload();
        await this.checkFaceStatus();
    },

    // 初始化上传功能
    initUpload() {
        const uploadArea = document.getElementById('faceUploadArea');
        const fileInput = document.getElementById('faceImageInput');
        const verifyArea = document.getElementById('faceVerifyArea');
        const verifyInput = document.getElementById('faceVerifyInput');

        // 如果已经初始化过，不再重复初始化
        if (this._uploadInitialized) {
            return;
        }
        this._uploadInitialized = true;

        // 调试信息：检查元素是否存在
        console.log('人脸上传功能初始化:', {
            uploadArea: !!uploadArea,
            fileInput: !!fileInput,
            verifyArea: !!verifyArea,
            verifyInput: !!verifyInput
        });

        // 文件输入框现在直接覆盖在上传区域上，不需要额外的事件处理
        if (uploadArea && fileInput) {
            console.log('文件输入框已设置为覆盖上传区域');
        }

        // 文件选择
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.previewImage(file);
                }
            });
        }

        // 备用文件输入框创建方法
        this.createFallbackFileInput = () => {
            console.log('创建备用文件输入框');
            const fallbackInput = document.createElement('input');
            fallbackInput.type = 'file';
            fallbackInput.accept = 'image/*';
            fallbackInput.style.position = 'absolute';
            fallbackInput.style.left = '-9999px';
            fallbackInput.style.top = '-9999px';

            fallbackInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    console.log('备用文件输入框选择了文件');
                    this.previewImage(file);
                }
                // 清理临时创建的输入框
                setTimeout(() => {
                    if (fallbackInput.parentNode) {
                        fallbackInput.parentNode.removeChild(fallbackInput);
                    }
                }, 1000);
            });

            document.body.appendChild(fallbackInput);

            // 触发文件选择
            setTimeout(() => {
                try {
                    fallbackInput.click();
                } catch (error) {
                    console.error('备用文件输入框点击失败:', error);
                }
            }, 0);
        }

        // 重新拍照
        document.getElementById('retakePhoto')?.addEventListener('click', () => {
            document.getElementById('facePreview').style.display = 'none';
            document.getElementById('faceUploadArea').style.display = 'block';
            fileInput.value = '';
            console.log('已重置到拍照状态');
        });

        // 提交人脸注册
        document.getElementById('submitFace')?.addEventListener('click', async () => {
            await this.submitFaceRegistration();
        });

        // 人脸验证
        verifyArea?.addEventListener('click', () => {
            verifyInput.click();
        });

        verifyInput?.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.verifyFace(file);
            }
        });

        // 刷新状态
        document.getElementById('refreshFaceStatus')?.addEventListener('click', () => {
            this.checkFaceStatus();
        });
    },

    // 预览图片
    previewImage(file) {
        console.log('开始预览图片:', file.name);
        console.log('文件大小:', file.size, 'bytes');
        console.log('文件类型:', file.type);

        const reader = new FileReader();
        reader.onload = (e) => {
            console.log('图片加载完成，开始显示预览');
            console.log('图片数据长度:', e.target.result.length);

            const preview = document.getElementById('facePreview');
            const previewImage = document.getElementById('facePreviewImage');
            const uploadArea = document.getElementById('faceUploadArea');
            const submitButton = document.getElementById('submitFace');
            const retakeButton = document.getElementById('retakePhoto');

            console.log('查找的元素:', {
                preview: !!preview,
                previewImage: !!previewImage,
                uploadArea: !!uploadArea,
                submitButton: !!submitButton,
                retakeButton: !!retakeButton
            });

            if (preview && previewImage && uploadArea) {
                console.log('开始显示预览卡片');

                // 设置图片源
                previewImage.src = e.target.result;
                console.log('图片源已设置');

                // 隐藏上传区域
                uploadArea.style.display = 'none';
                console.log('上传区域已隐藏');

                // 显示预览区域
                preview.style.display = 'block';
                console.log('预览区域已显示');

                // 强制重绘以确保显示
                preview.offsetHeight;

                // 确保按钮可用
                if (submitButton) {
                    submitButton.disabled = false;
                    console.log('提交按钮已启用');
                }
                if (retakeButton) {
                    retakeButton.disabled = false;
                    console.log('重拍按钮已启用');
                }

                Utils.showToast('照片已选择，可以提交注册了', 'success');
                console.log('预览显示完成');
            } else {
                console.error('预览元素不存在或查找失败:', {
                    preview: !!preview,
                    previewImage: !!previewImage,
                    uploadArea: !!uploadArea
                });
                Utils.showToast('预览显示失败，请重试', 'error');
            }
        };

        reader.onerror = (error) => {
            console.error('图片读取失败:', error);
            Utils.showToast('图片读取失败，请重试', 'error');
        };

        reader.onabort = () => {
            console.warn('图片读取被中止');
        };

        console.log('开始读取文件');
        reader.readAsDataURL(file);
    },

    // 检查人脸状态
    async checkFaceStatus() {
        try {
            const data = await Utils.request('/faces/status');
            const statusText = document.getElementById('faceStatusText');
            const faceRegister = document.getElementById('faceRegister');
            const faceVerify = document.getElementById('faceVerify');
            const faceManagement = document.getElementById('faceManagement');

            if (data.registered) {
                statusText.textContent = '已注册';
                faceRegister.style.display = 'none';
                faceVerify.style.display = 'block';
                faceManagement.style.display = 'block';

                // 加载人脸信息
                await this.loadFaceInfo(data.face_data);
            } else {
                statusText.textContent = '未注册';
                faceRegister.style.display = 'block';
                faceVerify.style.display = 'none';
                faceManagement.style.display = 'none';
            }
        } catch (error) {
            console.error('检查人脸状态失败:', error);
            document.getElementById('faceStatusText').textContent = '检查失败';
        }
    },

    // 提交人脸注册
    async submitFaceRegistration() {
        const fileInput = document.getElementById('faceImageInput');
        const file = fileInput.files[0];

        if (!file) {
            Utils.showToast('请选择图片', 'error');
            return;
        }

        // 验证用户登录状态
        if (!AppState.isAuthenticated) {
            Utils.showToast('请先登录后再进行人脸注册', 'warning');
            return;
        }

        // 显示上传中状态
        const submitBtn = document.getElementById('submitFace');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="ri-loader-4-line spin"></i> 注册中...';
        }

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await Utils.request('/faces/register', {
                method: 'POST',
                body: formData
            });

            Utils.showToast('人脸注册成功', 'success');

            // 重置表单
            document.getElementById('facePreview').style.display = 'none';
            fileInput.value = '';

            // 立即显示注册中状态
            const statusText = document.getElementById('faceStatusText');
            const faceRegister = document.getElementById('faceRegister');
            const faceVerify = document.getElementById('faceVerify');

            if (statusText) statusText.textContent = '注册中...';
            if (faceRegister) faceRegister.style.display = 'none';
            if (faceVerify) faceVerify.style.display = 'none';

            // 延迟检查人脸状态，确保后端处理完成
            setTimeout(async () => {
                await this.checkFaceStatus();

                // 重新加载页面统计信息
                if (typeof ProfilePage !== 'undefined' && ProfilePage.loadStatistics) {
                    await ProfilePage.loadStatistics();
                }

                // 显示成功提示
                Utils.showToast('人脸状态已更新', 'success');
            }, 1500);

        } catch (error) {
            console.error('人脸注册失败:', error);

            if (error.message && error.message.includes('401')) {
                Utils.showToast('登录已过期，请重新登录', 'error');
                // 401错误时自动退出登录
                setTimeout(() => {
                    Auth.logout();
                }, 2000);
            } else {
                Utils.showToast(error.message || '人脸注册失败', 'error');
            }
        } finally {
            // 恢复按钮状态
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="ri-check-line"></i> 提交注册';
            }
        }
    },

    // 验证人脸
    async verifyFace(file) {
        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await Utils.request('/faces/verify', {
                method: 'POST',
                headers: {},
                body: formData
            });

            const resultContainer = document.getElementById('faceVerifyResult');
            resultContainer.style.display = 'block';
            resultContainer.innerHTML = `
                <div class="verify-result ${response.verified ? 'success' : 'error'}">
                    <h4>
                        <i class="ri-${response.verified ? 'check' : 'close'}-circle-line"></i>
                        ${response.verified ? '验证成功' : '验证失败'}
                    </h4>
                    <div class="match-score">
                        匹配度: ${response.match_score ? (response.match_score * 100).toFixed(1) : '85.0'}%
                    </div>
                    <p>${response.message}</p>
                </div>
            `;

            if (response.verified) {
                Utils.showToast('人脸验证成功，可以入校', 'success');
            } else {
                Utils.showToast('人脸验证失败，请重试', 'error');
            }
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 加载人脸信息
    async loadFaceInfo(faceData) {
        try {
            if (!faceData) return;

            // 更新注册时间
            const registrationTime = document.getElementById('faceRegistrationTime');
            if (registrationTime && faceData.registration_time) {
                const regDate = new Date(faceData.registration_time);
                registrationTime.textContent = regDate.toLocaleString('zh-CN');
            }

            // 更新质量分数
            const qualityScore = document.getElementById('faceQualityScore');
            if (qualityScore && faceData.quality_score) {
                qualityScore.textContent = faceData.quality_score.toFixed(1);
            }

            // 加载人脸图片
            await this.loadFaceImage();

            // 绑定管理按钮事件
            this.bindManagementEvents();

        } catch (error) {
            console.error('加载人脸信息失败:', error);
        }
    },

    // 加载人脸图片
    async loadFaceImage() {
        try {
            // 从后端获取人脸图片
            const response = await fetch('/api/faces/image/current', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`
                }
            });

            if (response.ok) {
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);
                const faceImage = document.getElementById('registeredFaceImage');
                if (faceImage) {
                    faceImage.src = imageUrl;
                }
            } else {
                // 如果无法获取图片，使用默认图标
                const faceImage = document.getElementById('registeredFaceImage');
                if (faceImage) {
                    faceImage.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('加载人脸图片失败:', error);
            const faceImage = document.getElementById('registeredFaceImage');
            if (faceImage) {
                faceImage.style.display = 'none';
            }
        }
    },

    // 绑定管理按钮事件
    bindManagementEvents() {
        // 更新人脸按钮
        const updateBtn = document.getElementById('updateFaceBtn');
        if (updateBtn) {
            updateBtn.onclick = () => {
                this.showUpdateFaceDialog();
            };
        }

        // 删除人脸按钮
        const deleteBtn = document.getElementById('deleteFaceBtn');
        if (deleteBtn) {
            deleteBtn.onclick = () => {
                this.showDeleteFaceConfirm();
            };
        }
    },

    // 显示更新人脸对话框
    showUpdateFaceDialog() {
        // 创建模态框HTML
        const modalHtml = `
            <div class="modal" id="updateFaceModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>更新人脸信息</h2>
                        <button class="modal-close" onclick="this.closest('.modal').classList.remove('active')">
                            <i class="ri-close-line"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="update-face-content">
                            <div class="warning-message">
                                <i class="ri-information-line"></i>
                                <p>更新人脸信息将替换您当前已注册的人脸数据</p>
                            </div>
                            <div class="upload-area" id="updateUploadArea">
                                <input type="file" id="updateFaceInput" accept="image/*" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; z-index: 2;">
                                <div class="upload-content" style="position: relative; z-index: 1; pointer-events: none;">
                                    <i class="ri-camera-line"></i>
                                    <p>点击上传新的人脸照片</p>
                                    <small>请确保面部清晰，光线充足</small>
                                </div>
                            </div>
                            <div class="preview-area" id="updatePreviewArea" style="display: none;">
                                <img id="updatePreviewImage" alt="新人脸预览" style="width: 100%; border-radius: 8px; margin-bottom: 10px;">
                                <div class="preview-actions">
                                    <button class="btn btn-outline" id="cancelUpdateFace">
                                        <i class="ri-close-line"></i>
                                        取消
                                    </button>
                                    <button class="btn btn-primary" id="confirmUpdateFace">
                                        <i class="ri-check-line"></i>
                                        确认更新
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除已存在的模态框
        const existingModal = document.getElementById('updateFaceModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        document.getElementById('updateFaceModal').classList.add('active');

        // 绑定上传事件
        const uploadInput = document.getElementById('updateFaceInput');
        const uploadArea = document.getElementById('updateUploadArea');
        const previewArea = document.getElementById('updatePreviewArea');
        const previewImage = document.getElementById('updatePreviewImage');

        uploadInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    previewImage.src = e.target.result;
                    uploadArea.style.display = 'none';
                    previewArea.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });

        // 绑定取消按钮
        document.getElementById('cancelUpdateFace').addEventListener('click', () => {
            document.getElementById('updateFaceModal').classList.remove('active');
        });

        // 绑定确认更新按钮
        document.getElementById('confirmUpdateFace').addEventListener('click', async () => {
            await this.updateFaceRegistration(uploadInput.files[0]);
            document.getElementById('updateFaceModal').classList.remove('active');
        });
    },

    // 显示删除人脸确认对话框
    showDeleteFaceConfirm() {
        // 创建模态框HTML
        const modalHtml = `
            <div class="modal" id="deleteFaceModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>删除人脸信息</h2>
                        <button class="modal-close" onclick="this.closest('.modal').classList.remove('active')">
                            <i class="ri-close-line"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="delete-face-content">
                            <div class="warning-message" style="background: #ffebee; color: #c62828; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                                <i class="ri-error-warning-line"></i>
                                <p><strong>警告：此操作不可恢复！</strong></p>
                                <p>删除人脸信息后，您将无法使用人脸识别功能进行入校验证</p>
                            </div>
                            <div class="confirm-actions">
                                <button class="btn btn-outline" id="cancelDeleteFace">
                                    <i class="ri-close-line"></i>
                                    取消
                                </button>
                                <button class="btn btn-danger" id="confirmDeleteFace">
                                    <i class="ri-delete-bin-line"></i>
                                    确认删除
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除已存在的模态框
        const existingModal = document.getElementById('deleteFaceModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        document.getElementById('deleteFaceModal').classList.add('active');

        // 绑定按钮事件
        document.getElementById('cancelDeleteFace').addEventListener('click', () => {
            document.getElementById('deleteFaceModal').classList.remove('active');
        });

        document.getElementById('confirmDeleteFace').addEventListener('click', async () => {
            await this.deleteFaceRegistration();
            document.getElementById('deleteFaceModal').classList.remove('active');
        });
    },

    // 更新人脸注册
    async updateFaceRegistration(file) {
        if (!file) {
            Utils.showToast('请选择图片', 'error');
            return;
        }

        try {
            Utils.showLoading('正在更新人脸信息...');

            const formData = new FormData();
            formData.append('image', file);

            const response = await Utils.request('/faces/update', {
                method: 'POST',
                body: formData
            });

            Utils.hideLoading();
            Utils.showToast('人脸信息更新成功', 'success');

            // 重新加载人脸状态
            await this.checkFaceStatus();

        } catch (error) {
            Utils.hideLoading();
            console.error('更新人脸信息失败:', error);
            Utils.showToast(error.message || '更新人脸信息失败', 'error');
        }
    },

    // 删除人脸注册
    async deleteFaceRegistration() {
        try {
            Utils.showLoading('正在删除人脸信息...');

            const response = await Utils.request('/faces/delete', {
                method: 'DELETE'
            });

            Utils.hideLoading();
            Utils.showToast('人脸信息删除成功', 'success');

            // 重新加载人脸状态
            await this.checkFaceStatus();

        } catch (error) {
            Utils.hideLoading();
            console.error('删除人脸信息失败:', error);
            Utils.showToast(error.message || '删除人脸信息失败', 'error');
        }
    }
};

// 个人中心页面逻辑
const ProfilePage = {
    // 加载页面
    async load() {
        this.bindMenuItems();
        await this.loadStatistics();
    },

    // 绑定菜单项
    bindMenuItems() {
        // 编辑资料
        document.getElementById('editProfile')?.addEventListener('click', () => {
            this.showEditProfileModal();
        });

        // 校友档案
        document.getElementById('alumniProfile')?.addEventListener('click', () => {
            this.showAlumniProfileModal();
        });

        // 修改密码
        document.getElementById('changePassword')?.addEventListener('click', () => {
            this.showChangePasswordModal();
        });

        // 车辆管理
        document.getElementById('myVehicles')?.addEventListener('click', () => {
            this.showVehicleModal();
        });

        // 我的二维码
        document.getElementById('myQRCode')?.addEventListener('click', () => {
            this.showQRCode();
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
            if (confirm('确定要退出登录吗？')) {
                Auth.logout();
            }
        });

        // 绑定模态框事件
        this.bindModalEvents();
    },

    // 加载统计数据
    async loadStatistics() {
        try {
            // 获取访问申请统计
            const visitsData = await Utils.request('/visits/applications?per_page=1');
            document.getElementById('visitCount').textContent = visitsData.pagination?.total || 0;

            // 获取人脸注册状态
            try {
                const faceData = await Utils.request('/faces/status');
                document.getElementById('faceRegistered').textContent = faceData.registered ? '已注册' : '未注册';
            } catch (error) {
                document.getElementById('faceRegistered').textContent = '未知';
            }

            // 车辆数量（暂时使用模拟数据）
            document.getElementById('vehicleCount').textContent = '0';
        } catch (error) {
            console.error('加载统计数据失败:', error);
            // 设置默认值
            document.getElementById('visitCount').textContent = '0';
            document.getElementById('vehicleCount').textContent = '0';
            document.getElementById('faceRegistered').textContent = '未知';
        }
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

        // 车辆管理模态框
        document.getElementById('closeVehicleModal')?.addEventListener('click', () => {
            UI.hideModal('vehicleModal');
        });
        document.getElementById('addVehicleForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addVehicle();
        });

        // 访问记录模态框
        document.getElementById('closeVisitRecordsModal')?.addEventListener('click', () => {
            UI.hideModal('visitRecordsModal');
        });

        // 关于我们模态框
        document.getElementById('closeAboutModal')?.addEventListener('click', () => {
            UI.hideModal('aboutModal');
        });

        // 校友档案模态框
        document.getElementById('closeAlumniProfileModal')?.addEventListener('click', () => {
            UI.hideModal('alumniProfileModal');
        });
        document.getElementById('cancelAlumniProfile')?.addEventListener('click', () => {
            UI.hideModal('alumniProfileModal');
        });
        document.getElementById('alumniProfileForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveAlumniProfile();
        });
    },

    // 显示编辑资料模态框
    showEditProfileModal() {
        // 填充当前用户信息
        if (AppState.user) {
            document.getElementById('editRealName').value = AppState.user.real_name || '';
            document.getElementById('editEmail').value = AppState.user.email || '';
            document.getElementById('editPhone').value = AppState.user.phone || '';
            document.getElementById('editIdCard').value = AppState.user.id_card || '';
            document.getElementById('editAlumniInfo').value = AppState.user.alumni_info || '';
            document.getElementById('editWorkInfo').value = AppState.user.work_info || '';
        }
        UI.showModal('editProfileModal');
    },

    // 保存个人资料
    async saveProfile() {
        try {
            const formData = {
                real_name: document.getElementById('editRealName').value,
                email: document.getElementById('editEmail').value,
                phone: document.getElementById('editPhone').value,
                id_card: document.getElementById('editIdCard').value,
                alumni_info: document.getElementById('editAlumniInfo').value,
                work_info: document.getElementById('editWorkInfo').value
            };

            // 验证表单
            const errors = Utils.validateForm(formData, {
                real_name: { required: true, label: '真实姓名' },
                email: { required: true, type: 'email', label: '邮箱' },
                phone: { required: true, type: 'phone', label: '手机号' }
            });

            if (errors.length > 0) {
                Utils.showToast(errors[0], 'error');
                return;
            }

            // 验证身份证格式（如果填写了）
            if (formData.id_card && !Utils.validateIdCard(formData.id_card)) {
                Utils.showToast('身份证号码格式不正确', 'error');
                return;
            }

            // 调用API更新用户信息
            await Utils.request('/user/profile', {
                method: 'PUT',
                body: JSON.stringify(formData)
            });

            // 更新本地用户信息
            Object.assign(AppState.user, formData);
            localStorage.setItem(APP_CONFIG.STORAGE_KEYS.USER, JSON.stringify(AppState.user));

            // 更新UI显示
            UI.updateUserInfo();

            UI.hideModal('editProfileModal');
            Utils.showToast('个人资料更新成功', 'success');
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 显示修改密码模态框
    showChangePasswordModal() {
        document.getElementById('changePasswordForm').reset();
        UI.showModal('changePasswordModal');
    },

    // 修改密码
    async changePassword() {
        try {
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmNewPassword = document.getElementById('confirmNewPassword').value;

            // 验证表单
            if (!currentPassword || !newPassword || !confirmNewPassword) {
                Utils.showToast('请填写所有密码字段', 'error');
                return;
            }

            if (newPassword.length < 8) {
                Utils.showToast('新密码长度至少8位', 'error');
                return;
            }

            if (newPassword !== confirmNewPassword) {
                Utils.showToast('两次输入的新密码不一致', 'error');
                return;
            }

            // 调用API修改密码
            await Utils.request('/user/change-password', {
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

    // 显示车辆管理模态框
    async showVehicleModal() {
        await this.loadVehicles();
        UI.showModal('vehicleModal');
    },

    // 加载车辆列表
    async loadVehicles() {
        try {
            const data = await Utils.request('/user/vehicles');
            const container = document.getElementById('vehicleList');

            if (data.vehicles.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">暂无车辆信息</p>';
                return;
            }

            container.innerHTML = data.vehicles.map(vehicle => `
                <div class="vehicle-item">
                    <div class="vehicle-info">
                        <h4>${vehicle.license_plate}</h4>
                        <p>${vehicle.type} - ${vehicle.color} - ${vehicle.brand || '未知品牌'}</p>
                    </div>
                    <div class="vehicle-actions">
                        <button class="btn btn-sm btn-outline-danger" onclick="ProfilePage.removeVehicle('${vehicle.id}')">
                            删除
                        </button>
                    </div>
                </div>
            `).join('');

            // 更新车辆数量统计
            document.getElementById('vehicleCount').textContent = data.vehicles.length;
        } catch (error) {
            console.error('加载车辆列表失败:', error);
            document.getElementById('vehicleList').innerHTML = '<p class="text-center text-secondary">加载失败</p>';
        }
    },

    // 添加车辆
    async addVehicle() {
        try {
            const formData = {
                license_plate: document.getElementById('vehicleLicensePlate').value,
                type: document.getElementById('vehicleType').value,
                color: document.getElementById('vehicleColor').value,
                brand: document.getElementById('vehicleBrand').value
            };

            // 验证必填字段
            if (!formData.license_plate || !formData.type || !formData.color) {
                Utils.showToast('请填写车辆基本信息', 'error');
                return;
            }

            // 调用API添加车辆
            await Utils.request('/user/vehicles', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            // 重新加载车辆列表
            await this.loadVehicles();

            // 重置表单
            document.getElementById('addVehicleForm').reset();

            Utils.showToast('车辆添加成功', 'success');
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 删除车辆
    async removeVehicle(vehicleId) {
        if (!confirm('确定要删除这辆车吗？')) {
            return;
        }

        try {
            await Utils.request(`/user/vehicles/${vehicleId}`, {
                method: 'DELETE'
            });

            await this.loadVehicles();
            Utils.showToast('车辆删除成功', 'success');
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 显示二维码
    async showQRCode() {
        if (!AppState.isAuthenticated) {
            Utils.showToast('请先登录', 'warning');
            return;
        }

        try {
            // 加载用户的二维码列表
            const data = await Utils.request('/qr-codes/my-qr-codes');

            if (data.qr_codes.length === 0) {
                // 没有有效的访问申请，显示提示
                this.showNoQRCodeModal();
            } else {
                // 显示二维码列表
                this.showQRCodeListModal(data.qr_codes);
            }
        } catch (error) {
            Utils.showToast('加载二维码失败', 'error');
            console.error('加载二维码失败:', error);
        }
    },

    // 显示无二维码模态框
    showNoQRCodeModal() {
        // 创建动态模态框
        const modalHtml = `
            <div class="modal" id="noQRCodeModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>访问二维码</h2>
                        <button class="modal-close" onclick="this.closest('.modal').classList.remove('active')">
                            <i class="ri-close-line"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="empty-state">
                            <div class="empty-icon">
                                <i class="ri-qr-code-line"></i>
                            </div>
                            <h3>暂无有效二维码</h3>
                            <p>您目前没有已通过的访问申请，或访问时间已过期</p>
                            <p>请先提交访问申请并获得审批通过</p>
                            <button class="btn btn-primary" onclick="document.getElementById('noQRCodeModal').classList.remove('active'); PageManager.switchPage('visit')">
                                <i class="ri-add-line"></i>
                                提交访问申请
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除已存在的模态框
        const existingModal = document.getElementById('noQRCodeModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        document.getElementById('noQRCodeModal').classList.add('active');
    },

    // 显示二维码列表模态框
    showQRCodeListModal(qrCodes) {
        const modalHtml = `
            <div class="modal" id="qrCodeListModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>访问二维码</h2>
                        <button class="modal-close" onclick="this.closest('.modal').classList.remove('active')">
                            <i class="ri-close-line"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="qr-code-list">
                            ${qrCodes.map(qr => `
                                <div class="qr-code-item ${qr.is_today ? 'today' : ''}" data-id="${qr.id}">
                                    <div class="qr-info">
                                        <div class="qr-header">
                                            <h4>${qr.visitor_name}</h4>
                                            ${qr.is_today ? '<span class="today-badge">今日访问</span>' : ''}
                                        </div>
                                        <div class="qr-details">
                                            <p><i class="ri-calendar-line"></i> ${qr.visit_date}</p>
                                            <p><i class="ri-time-line"></i> ${qr.visit_time}</p>
                                            <p><i class="ri-flag-line"></i> ${qr.visit_purpose}</p>
                                            <p><i class="ri-user-line"></i> ${qr.target_person}</p>
                                        </div>
                                    </div>
                                    <div class="qr-actions">
                                        <button class="btn btn-primary btn-sm show-qr-btn" data-id="${qr.id}">
                                            <i class="ri-qr-code-line"></i>
                                            显示二维码
                                        </button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除已存在的模态框
        const existingModal = document.getElementById('qrCodeListModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        document.getElementById('qrCodeListModal').classList.add('active');

        // 绑定显示二维码按钮事件
        document.querySelectorAll('.show-qr-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const applicationId = e.target.closest('.show-qr-btn').dataset.id;
                this.showQRCodeDetail(applicationId);
            });
        });
    },

    // 显示二维码详情
    async showQRCodeDetail(applicationId) {
        try {
            // 获取二维码base64数据
            const data = await Utils.request(`/qr-codes/generate/${applicationId}/base64`);

            const modalHtml = `
                <div class="modal" id="qrCodeDetailModal">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2>访问二维码</h2>
                            <button class="modal-close" onclick="this.closest('.modal').classList.remove('active')">
                                <i class="ri-close-line"></i>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="qr-code-display">
                                <div class="qr-image-container">
                                    <img src="${data.qr_code}" alt="访问二维码" class="qr-image">
                                </div>
                                <div class="qr-info-detail">
                                    <h4>${data.visitor_name}</h4>
                                    <div class="info-grid">
                                        <div class="info-item">
                                            <i class="ri-calendar-line"></i>
                                            <span>日期: ${data.visit_date}</span>
                                        </div>
                                        <div class="info-item">
                                            <i class="ri-time-line"></i>
                                            <span>时间: ${data.visit_time}</span>
                                        </div>
                                    </div>
                                    <div class="qr-instructions">
                                        <p><strong>使用说明:</strong></p>
                                        <p>1. 请在访问时向门卫出示此二维码</p>
                                        <p>2. 门卫扫描二维码即可查看您的访问信息</p>
                                        <p>3. 此二维码仅在申请的有效时间内使用</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-outline" onclick="ProfilePage.downloadQRCode('${data.qr_code}', '${data.applicationId}')">
                                <i class="ri-download-line"></i>
                                下载二维码
                            </button>
                            <button class="btn btn-primary" onclick="this.closest('.modal').classList.remove('active')">
                                关闭
                            </button>
                        </div>
                    </div>
                </div>
            `;

            // 移除已存在的模态框
            const existingModal = document.getElementById('qrCodeDetailModal');
            if (existingModal) {
                existingModal.remove();
            }

            // 添加新模态框
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            document.getElementById('qrCodeDetailModal').classList.add('active');

        } catch (error) {
            Utils.showToast('获取二维码失败', 'error');
            console.error('获取二维码失败:', error);
        }
    },

    // 下载二维码
    downloadQRCode(qrData, applicationId) {
        try {
            // 创建下载链接
            const link = document.createElement('a');
            link.href = qrData;
            link.download = `visit_qr_${applicationId}.png`;
            link.click();

            Utils.showToast('二维码下载成功', 'success');
        } catch (error) {
            Utils.showToast('下载失败', 'error');
            console.error('下载二维码失败:', error);
        }
    },

    // 显示访问记录模态框
    async showVisitRecordsModal() {
        await this.loadVisitRecords();
        UI.showModal('visitRecordsModal');
    },

    // 加载访问记录
    async loadVisitRecords() {
        try {
            const data = await Utils.request('/visits/applications');
            const container = document.getElementById('visitRecordsList');

            if (data.applications.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">暂无访问记录</p>';
                return;
            }

            container.innerHTML = data.applications.map(app => `
                <div class="visit-record-item">
                    <div class="record-header">
                        <span class="record-date">${Utils.formatDate(app.visit_date)}</span>
                        <span class="record-status ${Utils.getStatusClass(app.application_status)}">
                            ${Utils.getStatusText(app.application_status)}
                        </span>
                    </div>
                    <div class="record-content">
                        <p><strong>访问目的：</strong>${app.visit_purpose}</p>
                        ${app.target_person ? `<p><strong>拜访对象：</strong>${app.target_person}</p>` : ''}
                        <p><strong>访问时间：</strong>${Utils.formatTime(app.visit_time_start)} - ${Utils.formatTime(app.visit_time_end)}</p>
                        ${app.approval_note ? `<p><strong>审核意见：</strong>${app.approval_note}</p>` : ''}
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('加载访问记录失败:', error);
            document.getElementById('visitRecordsList').innerHTML = '<p class="text-center text-secondary">加载失败</p>';
        }
    },

    // 显示关于我们模态框
    showAboutModal() {
        UI.showModal('aboutModal');
    },

    // 显示校友档案模态框
    async showAlumniProfileModal() {
        await this.loadAlumniProfile();
        UI.showModal('alumniProfileModal');
    },

    // 加载校友档案
    async loadAlumniProfile() {
        try {
            const data = await Utils.request('/user/profile');
            if (data.user && data.user.alumni_profile) {
                const profile = data.user.alumni_profile;

                // 填充基本字段
                document.getElementById('alumniGraduationYear').value = profile.graduation_year || '';
                document.getElementById('alumniClassName').value = profile.class_name || '';
                document.getElementById('alumniDepartment').value = profile.department || '';
                document.getElementById('alumniMajor').value = profile.major || '';
                document.getElementById('alumniStudentId').value = profile.student_id || '';
                document.getElementById('alumniIdCard').value = profile.id_card || '';

                // 填充联系信息
                document.getElementById('alumniContactTeacher').value = profile.contact_teacher || '';
                document.getElementById('alumniContactTeacherPhone').value = profile.contact_teacher_phone || '';
                document.getElementById('alumniEmergencyContact').value = profile.emergency_contact || '';
                document.getElementById('alumniEmergencyPhone').value = profile.emergency_phone || '';
            }
        } catch (error) {
            console.error('加载校友档案失败:', error);
            Utils.showToast('加载校友档案失败', 'error');
        }
    },

    // 保存校友档案
    async saveAlumniProfile() {
        try {
            const formData = {
                // 基本信息
                graduation_year: parseInt(document.getElementById('alumniGraduationYear').value) || null,
                class_name: document.getElementById('alumniClassName').value,
                department: document.getElementById('alumniDepartment').value,
                major: document.getElementById('alumniMajor').value,
                student_id: document.getElementById('alumniStudentId').value,
                id_card: document.getElementById('alumniIdCard').value,

                // 联系信息
                contact_teacher: document.getElementById('alumniContactTeacher').value,
                contact_teacher_phone: document.getElementById('alumniContactTeacherPhone').value,
                emergency_contact: document.getElementById('alumniEmergencyContact').value,
                emergency_phone: document.getElementById('alumniEmergencyPhone').value
            };

            // 验证必填字段
            const requiredFields = ['graduation_year', 'class_name', 'department', 'major', 'contact_teacher', 'contact_teacher_phone', 'emergency_contact', 'emergency_phone'];
            for (const field of requiredFields) {
                if (!formData[field]) {
                    const fieldNames = {
                        graduation_year: '毕业年份',
                        class_name: '毕业班级',
                        department: '院系',
                        major: '专业',
                        contact_teacher: '班主任',
                        contact_teacher_phone: '班主任电话',
                        emergency_contact: '紧急联系人',
                        emergency_phone: '紧急联系人电话'
                    };
                    Utils.showToast(`${fieldNames[field]}不能为空`, 'error');
                    return;
                }
            }

            // 调用API更新校友档案
            await Utils.request('/user/profile', {
                method: 'PUT',
                body: JSON.stringify(formData)
            });

            UI.hideModal('alumniProfileModal');
            Utils.showToast('校友档案更新成功', 'success');
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    }
};

// 审核管理页面逻辑
const ReviewPage = {
    currentFilter: 'pending',

    // 加载页面
    async load() {
        await this.loadStatistics();
        await this.loadApplications();
        this.bindEvents();
    },

    // 绑定事件
    bindEvents() {
        // 刷新按钮
        document.getElementById('refreshReviewList')?.addEventListener('click', () => {
            this.loadApplications();
            this.loadStatistics();
        });

        // 退出按钮
        document.getElementById('exitReview')?.addEventListener('click', () => {
            this.exitReview();
        });

        // 筛选标签
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.dataset.status;
                this.loadApplications();
            });
        });
    },

    // 加载统计数据
    async loadStatistics() {
        try {
            // 获取不同状态的申请数量
            const pending = await Utils.request('/visits/applications?status=pending&per_page=1');
            const approved = await Utils.request('/visits/applications?status=approved&per_page=1');
            const rejected = await Utils.request('/visits/applications?status=rejected&per_page=1');

            document.getElementById('pendingCount').textContent = pending.pagination?.total || 0;
            document.getElementById('approvedCount').textContent = approved.pagination?.total || 0;
            document.getElementById('rejectedCount').textContent = rejected.pagination?.total || 0;
        } catch (error) {
            console.error('加载审核统计失败:', error);
        }
    },

    // 加载申请列表
    async loadApplications() {
        try {
            const status = this.currentFilter === 'all' ? '' : this.currentFilter;
            const data = await Utils.request(`/visits/applications?status=${status}&per_page=50`);
            const container = document.getElementById('reviewApplicationsList');

            if (data.applications.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">暂无申请记录</p>';
                return;
            }

            container.innerHTML = data.applications.map(app => this.renderApplicationCard(app)).join('');

            // 绑定审核按钮事件
            this.bindReviewEvents();
        } catch (error) {
            console.error('加载申请列表失败:', error);
            const container = document.getElementById('reviewApplicationsList');
            if (container) {
                container.innerHTML = '<p class="text-center text-secondary">加载失败</p>';
            }
        }
    },

    // 渲染申请卡片
    renderApplicationCard(app) {
        const statusClass = Utils.getStatusClass(app.application_status);
        const statusText = Utils.getStatusText(app.application_status);

        return `
            <div class="application-card review-card" data-id="${app.id}">
                <div class="card-header">
                    <div class="applicant-info">
                        <div class="avatar">
                            <i class="ri-user-fill"></i>
                        </div>
                        <div class="applicant-details">
                            <h4>${app.applicant.real_name}</h4>
                            <p>${app.applicant.email || '未提供邮箱'}</p>
                        </div>
                    </div>
                    <div class="application-status ${statusClass}">
                        ${statusText}
                    </div>
                </div>

                <div class="card-content">
                    <div class="visit-details">
                        <div class="detail-item">
                            <i class="ri-calendar-line"></i>
                            <span>${Utils.formatDate(app.visit_date)}</span>
                        </div>
                        <div class="detail-item">
                            <i class="ri-time-line"></i>
                            <span>${Utils.formatTime(app.visit_time_start)} - ${Utils.formatTime(app.visit_time_end)}</span>
                        </div>
                        <div class="detail-item">
                            <i class="ri-flag-line"></i>
                            <span>${app.visit_purpose}</span>
                        </div>
                        ${app.target_person ? `
                        <div class="detail-item">
                            <i class="ri-user-line"></i>
                            <span>拜访对象: ${app.target_person} (${app.target_department})</span>
                        </div>
                        ` : ''}
                    </div>

                    ${app.application_status === 'pending' ? `
                    <div class="review-actions">
                        <textarea class="review-note" placeholder="审核意见（选填）" rows="2"></textarea>
                        <div class="action-buttons">
                            <button class="btn btn-info btn-sm assist-btn" data-id="${app.id}"
                                    data-applicant='${JSON.stringify(app.applicant).replace(/'/g, '&apos;')}'>
                                <i class="ri-user-follow-line"></i>
                                协助填写
                            </button>
                            <button class="btn btn-danger btn-sm reject-btn" data-id="${app.id}">
                                <i class="ri-close-line"></i>
                                拒绝
                            </button>
                            <button class="btn btn-success btn-sm approve-btn" data-id="${app.id}">
                                <i class="ri-check-line"></i>
                                通过
                            </button>
                        </div>
                    </div>
                    ` : ''}

                    ${app.approval_note ? `
                    <div class="approval-note">
                        <strong>审核意见:</strong> ${app.approval_note}
                    </div>
                    ` : ''}
                </div>

                <div class="card-footer">
                    <small class="text-muted">
                        申请时间: ${app.created_at ? new Date(app.created_at).toLocaleString() : '未知'}
                    </small>
                </div>
            </div>
        `;
    },

    // 绑定审核事件
    bindReviewEvents() {
        // 协助填写按钮
        document.querySelectorAll('.assist-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                try {
                    const applicantData = JSON.parse(btn.dataset.applicant.replace(/&apos;/g, "'"));
                    await this.assistApplication(applicantData);
                } catch (error) {
                    console.error('解析申请人数据失败:', error);
                    Utils.showToast('无法获取申请人信息', 'error');
                }
            });
        });

        // 通过按钮
        document.querySelectorAll('.approve-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.target.dataset.id;
                const card = e.target.closest('.review-card');
                const note = card.querySelector('.review-note')?.value || '';

                await this.reviewApplication(id, true, note);
            });
        });

        // 拒绝按钮
        document.querySelectorAll('.reject-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.target.dataset.id;
                const card = e.target.closest('.review-card');
                const note = card.querySelector('.review-note')?.value || '';

                if (!note.trim()) {
                    Utils.showToast('拒绝申请时请填写审核意见', 'warning');
                    return;
                }

                await this.reviewApplication(id, false, note);
            });
        });
    },

    // 协助申请填写
    async assistApplication(applicantData) {
        try {
            // 切换到访问申请页面
            PageManager.switchPage(APP_CONFIG.PAGES.VISIT);

            // 等待页面加载完成后填充表单
            setTimeout(() => {
                VisitPage.fillFormForTeacher(applicantData);
            }, 300);

        } catch (error) {
            console.error('协助填写失败:', error);
            Utils.showToast('协助填写失败', 'error');
        }
    },

    // 审核申请
    async reviewApplication(id, approve, note) {
        try {
            await Utils.request(`/visits/applications/${id}/approve`, {
                method: 'POST',
                body: JSON.stringify({
                    approve: approve,
                    note: note
                })
            });

            Utils.showToast(`申请已${approve ? '通过' : '拒绝'}`, 'success');

            // 重新加载数据
            await this.loadApplications();
            await this.loadStatistics();
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 退出审核管理页面
    exitReview() {
        // 切换到个人中心页面
        PageManager.switchPage(APP_CONFIG.PAGES.PROFILE);
        Utils.showToast('已退出审核管理', 'info');
    }
};

// 人脸信息预览功能
function showFacePreviewModal() {
    const faceImage = document.getElementById('registeredFaceImage');
    const previewImage = document.getElementById('facePreviewImage');

    if (faceImage && previewImage) {
        // 复制图片源到预览图
        previewImage.src = faceImage.src;

        // 显示模态框
        UI.showModal('facePreviewModal');
    } else {
        Utils.showToast('人脸图片加载失败', 'error');
    }
}

function closeFacePreviewModal() {
    UI.hideModal('facePreviewModal');
}

// 在应用初始化时添加人脸预览模态框的事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 添加关闭按钮事件监听器
    const closeFacePreviewBtn = document.getElementById('closeFacePreviewModal');
    if (closeFacePreviewBtn) {
        closeFacePreviewBtn.addEventListener('click', closeFacePreviewModal);
    }

    // 添加模态框背景点击关闭功能
    const facePreviewModal = document.getElementById('facePreviewModal');
    if (facePreviewModal) {
        facePreviewModal.addEventListener('click', function(e) {
            if (e.target === facePreviewModal) {
                closeFacePreviewModal();
            }
        });
    }
});

// 应用初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== 移动端应用版本 5.0 加载 ===');
    console.log('DOMContentLoaded 事件触发');
    console.log('当前时间:', new Date().toLocaleString());

    // 立即隐藏加载动画
    Utils.hideLoading();
    console.log('加载动画已隐藏');

    try {
        // 初始化UI
        UI.init();
        console.log('UI 初始化完成');

        // 同步检查认证状态
        const token = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.TOKEN);
        const userStr = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.USER);
        console.log('检查本地认证状态:', { hasToken: !!token, hasUser: !!userStr });

        if (token && userStr) {
            try {
                AppState.token = token;
                AppState.user = JSON.parse(userStr);
                AppState.isAuthenticated = true;
                UI.updateUserInfo();
                console.log('用户已登录:', AppState.user.username);
            } catch (e) {
                console.warn('解析用户信息失败:', e);
                AppState.token = null;
                AppState.user = null;
                AppState.isAuthenticated = false;
            }
        }

        // 检查认证状态
        if (AppState.isAuthenticated) {
            // 如果已登录，显示首页
            console.log('显示首页（已登录）');
            PageManager.switchPage(APP_CONFIG.PAGES.HOME);
        } else {
            // 如果未登录，显示登录模态框
            console.log('显示登录模态框（未登录）');
            UI.showLoginModal();
            // 显示空白页面
            PageManager.switchPage(APP_CONFIG.PAGES.HOME);
        }
    } catch (error) {
        console.error('应用初始化失败:', error);
        // 确保在出错时也能显示基本页面
        PageManager.switchPage(APP_CONFIG.PAGES.HOME);
        UI.showLoginModal();
    }
});

// 校历活动轮播功能
class CalendarEventsCarousel {
    constructor() {
        this.events = [];
        this.currentIndex = 0;
        this.container = document.getElementById('eventsContainer');
        this.prevBtn = document.getElementById('eventsPrevBtn');
        this.nextBtn = document.getElementById('eventsNextBtn');
        this.eventsSection = document.querySelector('.calendar-events');

        this.init();
    }

    init() {
        // 初始化事件监听器
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.prevEvent());
        }
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.nextEvent());
        }

        // 加载活动数据
        this.loadEvents();
    }

    async loadEvents() {
        // 设置超时保护，防止API请求挂起
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('活动加载超时')), 8000);
        });

        try {
            Utils.showLoading('加载活动信息...');

            // 获取当前日期前后3个月的活动
            const today = new Date();
            const threeMonthsAgo = new Date(today.getFullYear(), today.getMonth() - 3, 1);
            const threeMonthsLater = new Date(today.getFullYear(), today.getMonth() + 3, 0);

            const apiPromise = Utils.request(`/public/calendar/events?start_date=${threeMonthsAgo.toISOString().split('T')[0]}&end_date=${threeMonthsLater.toISOString().split('T')[0]}&status=published&limit=10`);

            // 使用Promise.race来设置超时
            const response = await Promise.race([apiPromise, timeoutPromise]);

            if (response.events && response.events.length > 0) {
                this.events = response.events;
                this.renderEvents();
                this.setupIndicators();
                this.updateNavigationButtons();

                // 显示活动区域
                if (this.eventsSection) {
                    this.eventsSection.style.display = 'block';
                }
            } else {
                // 没有活动时隐藏活动区域
                if (this.eventsSection) {
                    this.eventsSection.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('加载活动失败:', error);
            // 错误时隐藏活动区域
            if (this.eventsSection) {
                this.eventsSection.style.display = 'none';
            }
            // 如果是超时错误，显示相应提示
            if (error.message === '活动加载超时') {
                Utils.showToast('活动信息加载超时，请稍后重试', 'warning');
            }
        } finally {
            Utils.hideLoading();
        }
    }

    renderEvents() {
        if (!this.container) return;

        this.container.innerHTML = '';

        this.events.forEach((event, index) => {
            const eventCard = this.createEventCard(event, index);
            this.container.appendChild(eventCard);
        });
    }

    createEventCard(event, index) {
        const card = document.createElement('div');
        card.className = 'event-card';
        card.setAttribute('data-event-id', event.id);
        card.setAttribute('data-index', index);

        // 计算活动状态
        const eventStatus = this.getEventStatus(event);
        const statusClass = eventStatus.class;
        const statusText = eventStatus.text;

        // 获取事件类型和优先级的样式类
        const eventTypeClass = event.event_type || 'activity';
        const priorityClass = event.priority || 'medium';

        // 格式化日期
        const eventDate = this.formatEventDate(event);
        const timeRange = this.formatTimeRange(event);

        card.innerHTML = `
            <div class="event-header">
                <div class="event-type ${eventTypeClass}">
                    ${this.getEventTypeLabel(event.event_type)}
                </div>
                <div class="event-status ${statusClass}">
                    ${statusText}
                </div>
            </div>
            <div class="event-content">
                <h4 class="event-title">${event.title}</h4>
                <div class="event-meta">
                    <div class="event-date">
                        <i class="ri-calendar-line"></i>
                        ${eventDate}
                    </div>
                    ${timeRange ? `
                        <div class="event-time">
                            <i class="ri-time-line"></i>
                            ${timeRange}
                        </div>
                    ` : ''}
                    ${event.location ? `
                        <div class="event-location">
                            <i class="ri-map-pin-line"></i>
                            ${event.location}
                        </div>
                    ` : ''}
                </div>
                ${event.description ? `
                    <div class="event-description">
                        ${event.description.length > 80 ? event.description.substring(0, 80) + '...' : event.description}
                    </div>
                ` : ''}
            </div>
            <div class="event-footer">
                <div class="event-priority ${priorityClass}">
                    ${this.getPriorityLabel(event.priority)}
                </div>
                <button class="event-detail-btn" onclick="CalendarEvents.viewEventDetail(${event.id})">
                    查看详情
                </button>
            </div>
        `;

        // 添加点击事件
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('event-detail-btn')) {
                this.showEventDetail(event);
            }
        });

        return card;
    }

    getEventStatus(event) {
        const now = new Date();
        const startDate = new Date(event.start_date);
        const endDate = event.end_date ? new Date(event.end_date) : startDate;

        if (now < startDate) {
            return {
                class: 'upcoming',
                text: '即将开始'
            };
        } else if (now >= startDate && now <= endDate) {
            return {
                class: 'ongoing',
                text: '进行中'
            };
        } else {
            return {
                class: 'completed',
                text: '已结束'
            };
        }
    }

    formatEventDate(event) {
        const startDate = new Date(event.start_date);
        const endDate = event.end_date ? new Date(event.end_date) : null;

        const formatDate = (date) => {
            return `${date.getMonth() + 1}月${date.getDate()}日`;
        };

        if (endDate && startDate.toDateString() !== endDate.toDateString()) {
            return `${formatDate(startDate)} - ${formatDate(endDate)}`;
        } else {
            return formatDate(startDate);
        }
    }

    formatTimeRange(event) {
        if (event.start_time && event.end_time) {
            return `${event.start_time.substring(0, 5)} - ${event.end_time.substring(0, 5)}`;
        } else if (event.start_time) {
            return event.start_time.substring(0, 5);
        }
        return '';
    }

    getEventTypeLabel(type) {
        const labels = {
            'anniversary': '校庆活动',
            'festival': '节庆活动',
            'activity': '校园活动',
            'club': '社团活动',
            'meeting': '会议讲座',
            'holiday': '假期安排',
            'exam': '考试安排'
        };
        return labels[type] || '其他活动';
    }

    getPriorityLabel(priority) {
        const labels = {
            'high': '重要',
            'medium': '一般',
            'low': '普通'
        };
        return labels[priority] || '普通';
    }

    setupIndicators() {
        // 创建指示器容器
        let indicatorsContainer = document.querySelector('.carousel-indicators');
        if (!indicatorsContainer && this.container) {
            indicatorsContainer = document.createElement('div');
            indicatorsContainer.className = 'carousel-indicators';
            this.container.parentElement.appendChild(indicatorsContainer);
        }

        if (indicatorsContainer) {
            indicatorsContainer.innerHTML = '';

            this.events.forEach((_, index) => {
                const indicator = document.createElement('button');
                indicator.className = `indicator ${index === 0 ? 'active' : ''}`;
                indicator.setAttribute('data-index', index);
                indicator.addEventListener('click', () => this.goToEvent(index));
                indicatorsContainer.appendChild(indicator);
            });
        }
    }

    updateNavigationButtons() {
        if (this.prevBtn && this.nextBtn) {
            this.prevBtn.style.display = this.events.length <= 1 ? 'none' : 'block';
            this.nextBtn.style.display = this.events.length <= 1 ? 'none' : 'block';
        }
    }

    prevEvent() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.scrollToEvent(this.currentIndex);
            this.updateIndicators();
        }
    }

    nextEvent() {
        if (this.currentIndex < this.events.length - 1) {
            this.currentIndex++;
            this.scrollToEvent(this.currentIndex);
            this.updateIndicators();
        }
    }

    goToEvent(index) {
        if (index >= 0 && index < this.events.length) {
            this.currentIndex = index;
            this.scrollToEvent(this.currentIndex);
            this.updateIndicators();
        }
    }

    scrollToEvent(index) {
        if (!this.container) return;

        const eventCards = this.container.querySelectorAll('.event-card');
        if (eventCards[index]) {
            const cardWidth = eventCards[index].offsetWidth;
            const gap = 16; // CSS中的gap值
            const scrollPosition = index * (cardWidth + gap);

            this.container.scrollTo({
                left: scrollPosition,
                behavior: 'smooth'
            });
        }
    }

    updateIndicators() {
        const indicators = document.querySelectorAll('.carousel-indicators .indicator');
        indicators.forEach((indicator, index) => {
            indicator.classList.toggle('active', index === this.currentIndex);
        });
    }

    showEventDetail(event) {
        // 简单的活动详情展示
        const status = this.getEventStatus(event);
        const timeRange = this.formatTimeRange(event);

        let detailHTML = `
            <div class="event-detail-content">
                <h3>${event.title}</h3>
                <div class="event-detail-info">
                    <p><strong>类型:</strong> ${this.getEventTypeLabel(event.event_type)}</p>
                    <p><strong>状态:</strong> <span class="event-status ${status.class}">${status.text}</span></p>
                    <p><strong>日期:</strong> ${this.formatEventDate(event)}</p>
                    ${timeRange ? `<p><strong>时间:</strong> ${timeRange}</p>` : ''}
                    ${event.location ? `<p><strong>地点:</strong> ${event.location}</p>` : ''}
                    ${event.target_audience ? `<p><strong>面向对象:</strong> ${event.target_audience}</p>` : ''}
                    ${event.contact_info ? `<p><strong>联系方式:</strong> ${event.contact_info}</p>` : ''}
                    ${event.description ? `<p><strong>详情:</strong></p><p>${event.description}</p>` : ''}
                </div>
                <div class="event-detail-actions">
                    <button class="btn-primary" onclick="CalendarEvents.hideEventDetail()">关闭</button>
                </div>
            </div>
        `;

        // 使用现有的模态框系统显示详情
        UI.showModal(detailHTML, '活动详情');
    }

    // 监听滚动事件更新指示器
    setupScrollListener() {
        if (!this.container) return;

        this.container.addEventListener('scroll', () => {
            const scrollLeft = this.container.scrollLeft;
            const cardWidth = this.container.querySelector('.event-card')?.offsetWidth || 0;
            const gap = 16;
            const newIndex = Math.round(scrollLeft / (cardWidth + gap));

            if (newIndex !== this.currentIndex && newIndex >= 0 && newIndex < this.events.length) {
                this.currentIndex = newIndex;
                this.updateIndicators();
            }
        });
    }
}

// 全局校历活动管理对象
const CalendarEvents = {
    carousel: null,

    init() {
        // 暂时禁用日历活动功能，避免API错误
        console.log('日历活动功能暂时禁用');

        // 隐藏活动区域
        const eventsSection = document.querySelector('.calendar-events');
        if (eventsSection) {
            eventsSection.style.display = 'none';
        }

        return;
    },

    viewEventDetail(eventId) {
        if (this.carousel) {
            const event = this.carousel.events.find(e => e.id === eventId);
            if (event) {
                this.carousel.showEventDetail(event);
            }
        }
    },

    hideEventDetail() {
        UI.hideModal();
    },

    // 重新加载活动数据
    async reloadEvents() {
        if (this.carousel) {
            await this.carousel.loadEvents();
        }
    }
};

// 在页面切换时初始化或清理活动轮播
const originalSwitchPage = PageManager.switchPage;
PageManager.switchPage = function(pageId, animate = true) {
    // 调用原始方法
    originalSwitchPage.call(this, pageId, animate);

    // 如果切换到首页，初始化活动轮播
    if (pageId === 'home') {
        setTimeout(() => {
            CalendarEvents.init();
        }, 100);
    }
};

// 在应用初始化时添加活动轮播初始化
document.addEventListener('DOMContentLoaded', function() {
    // 添加关闭按钮事件监听器
    const closeFacePreviewBtn = document.getElementById('closeFacePreviewModal');
    if (closeFacePreviewBtn) {
        closeFacePreviewBtn.addEventListener('click', closeFacePreviewModal);
    }

    // 添加模态框背景点击关闭功能
    const facePreviewModal = document.getElementById('facePreviewModal');
    if (facePreviewModal) {
        facePreviewModal.addEventListener('click', function(e) {
            if (e.target === facePreviewModal) {
                closeFacePreviewModal();
            }
        });
    }
});

// 处理网络错误
window.addEventListener('unhandledrejection', (event) => {
    if (event.reason.message && event.reason.message.includes('401')) {
        Auth.logout();
    }
});