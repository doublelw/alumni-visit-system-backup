/**
 * 移动端应用JavaScript - 版本 5.1 (修复版)
 * 校友入校登记系统
 * 更新时间: 2025-01-23 00:05
 */

console.log('=== MOBILE.JS 版本 5.1 已加载 ===');

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

    // 加载校历活动
    async loadCalendarEvents() {
        try {
            console.log('加载校历活动...');
            const data = await Utils.request('/public/calendar/events');
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

        // 拜访对象工作ID输入事件（带防抖）
        let searchTimeout;
        document.getElementById('targetWorkId')?.addEventListener('input', (e) => {
            const workId = e.target.value.trim();

            // 清除之前的定时器
            clearTimeout(searchTimeout);

            // 设置新的定时器，500ms后执行搜索
            searchTimeout = setTimeout(() => {
                this.lookupTargetPerson(workId);
            }, 500);
        });
    },

    // 根据工作ID查询拜访对象信息
    async lookupTargetPerson(workId) {
        try {
            // 如果工作ID为空，清空相关字段
            if (!workId) {
                this.clearTargetInfo();
                return;
            }

            // 至少输入3个字符才开始查询
            if (workId.length < 3) {
                return;
            }

            // 显示查询中状态
            const targetPersonInput = document.getElementById('targetPerson');
            if (targetPersonInput) {
                targetPersonInput.placeholder = '查询中...';
                targetPersonInput.style.color = '#999';
            }

            // 调用API查询拜访对象信息
            const data = await Utils.request(`/target-persons/search?work_id=${encodeURIComponent(workId)}`);

            // 填充拜访对象信息
            const targetDepartmentInput = document.getElementById('targetDepartment');

            if (targetPersonInput) {
                targetPersonInput.value = data.name;
                targetPersonInput.placeholder = '系统自动填充';
                targetPersonInput.style.color = '';
            }
            if (targetDepartmentInput) targetDepartmentInput.value = data.department;

            Utils.showToast(`已找到拜访对象：${data.name}（${data.department}）`, 'success');

        } catch (error) {
            // 清空相关字段
            this.clearTargetInfo();

            // 恢复placeholder
            const targetPersonInput = document.getElementById('targetPerson');
            if (targetPersonInput) {
                targetPersonInput.placeholder = '系统自动填充';
                targetPersonInput.style.color = '';
            }

            // 只有在输入足够长度后才显示错误提示
            if (workId.length >= 6) {
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
            const response = await Utils.request('/visits/applications', {
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
            visit_type: 'in-person'
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
        const targetDepartment = getValue('targetDepartment');

        if (!targetWorkId) {
            errors.push('请填写拜访对象工作ID');
        } else if (!targetPerson) {
            errors.push('请输入有效的工作ID以自动填充拜访对象信息');
        } else if (!targetDepartment) {
            errors.push('拜访对象部门信息不完整');
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
            Utils.showToast(errors.join('；'), 'error');
            return false;
        }

        return true;
    },

    // 加载申请历史
    async loadVisitHistory() {
        try {
            console.log('开始加载申请历史...');
            const data = await Utils.request('/visits/applications');
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

        if (app.application_status === 'pending') {
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
            await Utils.request(`/visits/applications/${id}/cancel`, {
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
            await Utils.request(`/visits/applications/${id}/start`, {
                method: 'POST'
            });

            Utils.showToast('访问已开始', 'success');
            await this.loadVisitHistory();
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 查看详情
    viewDetails(id) {
        // 显示申请详情模态框
        // 这里可以实现详情查看功能
        Utils.showToast('详情查看功能开发中', 'info');
    }
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
            const data = await Utils.request('/faces/status');
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
            const data = await Utils.request('/faces/info');
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
            registeredFaceImage.src = imagePath + '?t=' + Date.now();
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
                const visitData = await Utils.request('/visits/statistics');
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
                const faceData = await Utils.request('/faces/status');
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

    // 加载校友档案
    async loadAlumniProfile() {
        try {
            const data = await Utils.request('/alumni/profile');
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

            const data = await Utils.request('/auth/profile', {
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
        document.getElementById('confirmPassword').value = '';
        UI.showModal('changePasswordModal');
    },

    // 修改密码
    async changePassword() {
        try {
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;

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

            await Utils.request('/auth/change-password', {
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

    // 显示二维码
    showQRCode() {
        if (!AppState.user) {
            Utils.showToast('请先登录', 'error');
            return;
        }

        // 生成二维码内容（可以包含用户ID、姓名等信息）
        const qrContent = JSON.stringify({
            user_id: AppState.user.id,
            real_name: AppState.user.real_name,
            user_type: AppState.user.user_type,
            timestamp: Date.now()
        });

        // 显示二维码模态框
        const qrModal = document.getElementById('qrCodeModal');
        if (qrModal) {
            // 这里可以使用二维码库生成二维码
            // 为了演示，我们显示一个简单的文本
            const qrContainer = document.getElementById('qrCodeContainer');
            if (qrContainer) {
                qrContainer.innerHTML = `
                    <div style="text-align: center; padding: 20px;">
                        <div style="font-size: 12px; word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 4px;">
                            ${qrContent}
                        </div>
                        <p style="margin-top: 10px; color: #666; font-size: 12px;">
                            请使用校园系统扫描此二维码
                        </p>
                    </div>
                `;
            }
            UI.showModal('qrCodeModal');
        } else {
            Utils.showToast('二维码功能暂时不可用', 'info');
        }
    },

    // 显示访问记录模态框
    async showVisitRecordsModal() {
        try {
            Utils.showLoading('加载访问记录...');

            const data = await Utils.request('/visits/records');
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
                </div>
            </div>
        `;
    },

    // 显示关于我们模态框
    showAboutModal() {
        UI.showModal('aboutModal');
    }
};

// 审核管理页面逻辑
const ReviewPage = {
    currentFilter: 'pending',
    currentPage: 1,
    itemsPerPage: 10,

    // 加载页面
    async load() {
        await this.loadApplications();
        this.bindEvents();
    },

    // 绑定事件
    bindEvents() {
        // 筛选标签
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.addEventListener('click', () => {
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

        // 返回按钮
        document.getElementById('backToProfile')?.addEventListener('click', () => {
            PageManager.switchPage(APP_CONFIG.PAGES.PROFILE);
        });
    },

    // 设置筛选器
    setFilter(status) {
        this.currentFilter = status;
        this.currentPage = 1;

        // 更新标签状态
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.status === status) {
                tab.classList.add('active');
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

            let apiUrl = `/visits/applications?status=${this.currentFilter}&page=${this.currentPage}&per_page=${this.itemsPerPage}`;

            if (searchKeyword) {
                apiUrl += `&search=${encodeURIComponent(searchKeyword)}`;
            }

            const data = await Utils.request(apiUrl);
            this.renderApplications(data);

            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
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

    // 渲染申请项
    renderApplicationItem(app) {
        const statusClass = Utils.getStatusClass(app.application_status);
        const statusText = Utils.getStatusText(app.application_status);

        return `
            <div class="application-item" data-id="${app.id}">
                <div class="application-header">
                    <div class="applicant-info">
                        <span class="applicant-name">${app.applicant ? app.applicant.real_name : '未知'}</span>
                        <span class="application-date">${Utils.formatDate(app.visit_date)}</span>
                    </div>
                    <span class="application-status ${statusClass}">${statusText}</span>
                </div>
                <div class="application-content">
                    <div class="application-purpose">${app.visit_purpose}</div>
                    <div class="application-details">
                        <div><strong>拜访对象:</strong> ${app.target_person || '未指定'}</div>
                        <div><strong>访问时间:</strong> ${Utils.formatTime(app.visit_time_start)} - ${Utils.formatTime(app.visit_time_end)}</div>
                        <div><strong>联系电话:</strong> ${app.visitor_phone || '未提供'}</div>
                    </div>
                    ${app.review_note ? `
                        <div class="review-note">
                            <strong>审核意见:</strong> ${app.review_note}
                        </div>
                    ` : ''}
                </div>
                <div class="application-actions">
                    ${this.renderApplicationActions(app)}
                </div>
            </div>
        `;
    },

    // 渲染申请操作按钮
    renderApplicationActions(app) {
        let actions = '';

        if (app.application_status === 'pending') {
            actions += `
                <button class="btn btn-success btn-sm approve-btn" data-id="${app.id}">
                    <i class="ri-check-line"></i> 通过
                </button>
                <button class="btn btn-danger btn-sm reject-btn" data-id="${app.id}">
                    <i class="ri-close-line"></i> 拒绝
                </button>
            `;
        }

        actions += `
            <button class="btn btn-info btn-sm details-btn" data-id="${app.id}">
                <i class="ri-eye-line"></i> 详情
            </button>
        `;

        return actions;
    },

    // 绑定申请操作事件
    bindApplicationEvents() {
        // 通过按钮
        document.querySelectorAll('.approve-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                await this.reviewApplication(id, true);
            });
        });

        // 拒绝按钮
        document.querySelectorAll('.reject-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const reason = prompt('请输入拒绝理由:');
                if (reason && reason.trim()) {
                    await this.reviewApplication(id, false, reason.trim());
                } else {
                    Utils.showToast('请输入拒绝理由', 'warning');
                }
            });
        });

        // 详情按钮
        document.querySelectorAll('.details-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                this.showApplicationDetails(id);
            });
        });
    },

    // 审核申请
    async reviewApplication(id, approve, note = '') {
        try {
            await Utils.request(`/visits/applications/${id}/approve`, {
                method: 'POST',
                body: JSON.stringify({
                    approve: approve,
                    note: note
                })
            });

            Utils.showToast(`申请已${approve ? '通过' : '拒绝'}`, 'success');
            await this.loadApplications();
        } catch (error) {
            Utils.showToast(error.message, 'error');
        }
    },

    // 显示申请详情
    async showApplicationDetails(id) {
        try {
            const data = await Utils.request(`/visits/applications/${id}`);
            const app = data.application;

            // 创建详情模态框内容
            const detailsContent = `
                <div class="application-details">
                    <h4>申请详情</h4>
                    <div class="detail-section">
                        <h5>申请人信息</h5>
                        <p><strong>姓名:</strong> ${app.applicant ? app.applicant.real_name : '未知'}</p>
                        <p><strong>电话:</strong> ${app.visitor_phone || '未提供'}</p>
                        <p><strong>邮箱:</strong> ${app.visitor_email || '未提供'}</p>
                        <p><strong>身份证:</strong> ${app.visitor_id_card || '未提供'}</p>
                    </div>
                    <div class="detail-section">
                        <h5>访问信息</h5>
                        <p><strong>访问日期:</strong> ${Utils.formatDate(app.visit_date)}</p>
                        <p><strong>访问时间:</strong> ${Utils.formatTime(app.visit_time_start)} - ${Utils.formatTime(app.visit_time_end)}</p>
                        <p><strong>访问事由:</strong> ${app.visit_purpose}</p>
                        <p><strong>拜访对象:</strong> ${app.target_person || '未指定'}</p>
                        <p><strong>对象电话:</strong> ${app.target_phone || '未提供'}</p>
                    </div>
                    <div class="detail-section">
                        <h5>申请状态</h5>
                        <p><strong>当前状态:</strong> <span class="status-${app.application_status}">${Utils.getStatusText(app.application_status)}</span></p>
                        <p><strong>申请时间:</strong> ${new Date(app.created_at).toLocaleString('zh-CN')}</p>
                        ${app.reviewed_at ? `
                            <p><strong>审核时间:</strong> ${new Date(app.reviewed_at).toLocaleString('zh-CN')}</p>
                        ` : ''}
                        ${app.reviewed_by ? `
                            <p><strong>审核人:</strong> ${app.reviewer_name || '未知'}</p>
                        ` : ''}
                        ${app.review_note ? `
                            <p><strong>审核意见:</strong> ${app.review_note}</p>
                        ` : ''}
                    </div>
                </div>
            `;

            // 显示详情模态框
            alert(detailsContent); // 简单显示，实际应该使用模态框
        } catch (error) {
            Utils.showToast('加载申请详情失败', 'error');
        }
    },

    // 渲染分页
    renderPagination(pagination) {
        const container = document.getElementById('reviewPagination');
        if (!container || pagination.total_pages <= 1) {
            container.innerHTML = '';
            return;
        }

        let paginationHtml = '<div class="pagination">';

        // 上一页
        if (pagination.current_page > 1) {
            paginationHtml += `<button class="btn btn-sm" onclick="ReviewPage.goToPage(${pagination.current_page - 1})">上一页</button>`;
        }

        // 页码
        for (let i = 1; i <= pagination.total_pages; i++) {
            const activeClass = i === pagination.current_page ? 'active' : '';
            paginationHtml += `<button class="btn btn-sm ${activeClass}" onclick="ReviewPage.goToPage(${i})">${i}</button>`;
        }

        // 下一页
        if (pagination.current_page < pagination.total_pages) {
            paginationHtml += `<button class="btn btn-sm" onclick="ReviewPage.goToPage(${pagination.current_page + 1})">下一页</button>`;
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
        } else {
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