/**
 * PC端管理界面JavaScript
 * 校友入校登记系统管理后台
 */

// 应用配置
const ADMIN_CONFIG = {
    API_BASE_URL: window.Config ? window.Config.API_BASE_URL + '/api' : '/api',
    STORAGE_KEYS: {
        TOKEN: 'admin_token',
        USER: 'admin_user'
    },
    PAGES: {
        DASHBOARD: 'dashboard',
        USERS: 'users',
        ORGANIZATION: 'organization',
        VISIT_APPLICATIONS: 'visit-applications',
        VISIT_RECORDS: 'visit-records',
        STATISTICS: 'statistics',
        BATCH_APPROVE: 'batch-approve',
        CALENDAR: 'calendar',
        SURVEY: 'survey',
        EVENT_STATISTICS: 'event-statistics',
        KEY_MANAGEMENT: 'key-management'
    }
};

// 应用状态
const AdminState = {
    currentPage: ADMIN_CONFIG.PAGES.DASHBOARD,
    user: null,
    token: null,
    isAuthenticated: false,
    charts: {}
};

// 工具函数
const AdminUtils = {
    // API请求封装
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (AdminState.token) {
            defaultOptions.headers['Authorization'] = `Bearer ${AdminState.token}`;
        }

        const response = await fetch(ADMIN_CONFIG.API_BASE_URL + url, {
            ...defaultOptions,
            ...options
        });

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
            // 如果是401错误，说明token过期或无效
            if (response.status === 401) {
                console.error('401错误 - Token无效或过期');
                console.error('响应数据:', data);
                console.error('当前AdminState.token:', AdminState.token ? AdminState.token.substring(0, 50) + '...' : 'null');

                // 不要立即logout，先尝试检查token是否真的过期
                try {
                    // 检查token是否可以解析
                    const tokenParts = AdminState.token ? AdminState.token.split('.') : [];
                    if (tokenParts.length === 3) {
                        const payload = JSON.parse(atob(tokenParts[1]));
                        const now = Math.floor(Date.now() / 1000);
                        if (payload.exp && payload.exp > now) {
                            console.log('Token还未过期，可能是其他认证问题');
                            throw new Error('认证失败，但token未过期: ' + (data.error || '未知错误'));
                        }
                    }
                } catch (tokenError) {
                    console.error('Token解析失败:', tokenError);
                }

                console.log('Token确实过期或无效，执行logout');
                AdminAuth.logout();
                throw new Error('Token has expired');
            }
            // 如果是403错误，说明权限不足
            if (response.status === 403) {
                console.error('Access forbidden - checking authentication...');
                // 检查认证状态，可能需要重新登录
                if (!AdminAuth.initAuth()) {
                    AdminAuth.logout();
                    throw new Error('Authentication required');
                }
                throw new Error(data.error || 'Access forbidden');
            }
            throw new Error(data.error || `请求失败 (${response.status})`);
        }

        return data;
    },

    // 显示Toast提示
    showToast(message, type = 'info') {
        const toast = document.getElementById('adminToast');
        if (!toast) {
            console.warn('Toast element not found:', message);
            return;
        }

        const toastMessage = toast.querySelector('.toast-message');
        const toastIcon = toast.querySelector('.toast-icon');

        if (!toastMessage || !toastIcon) {
            console.warn('Toast elements not found:', message);
            return;
        }

        toastMessage.textContent = message;
        toast.className = `toast ${type} show`;

        const icons = {
            success: 'ri-check-line',
            error: 'ri-close-line',
            warning: 'ri-alert-line',
            info: 'ri-information-line'
        };
        toastIcon.className = `toast-icon ${icons[type] || icons.info}`;

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
        if (!timeString) return '-';
        return timeString.slice(0, 5);
    },

    // 格式化日期时间
    formatDateTime(dateTimeString) {
        const date = new Date(dateTimeString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // 获取状态文本
    getStatusText(status) {
        const statusMap = {
            pending: '待审核',
            approved: '已通过',
            rejected: '已拒绝',
            completed: '已完成',
            cancelled: '已取消',
            active: '激活',
            inactive: '禁用'
        };
        return statusMap[status] || status;
    },

    // 获取状态样式类
    getStatusClass(status) {
        return `status-${status}`;
    },

    // 获取用户类型文本
    getUserTypeText(type) {
        const typeMap = {
            student: '学生',
            parent: '家长',
            alumni: '校友',
            teacher: '教师',
            security: '保安',
            admin: '管理员',
            external_visitor: '访客'
        };

        if (!type) return type;

        // 处理多类型（逗号分隔的字符串）
        if (typeof type === 'string' && type.includes(',')) {
            const types = type.split(',').map(t => t.trim());
            return types.map(t => typeMap[t] || t).join('、');
        }

        return typeMap[type] || type;
    },

    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 显示确认对话框
    showConfirm(message, onConfirm) {
        const modal = document.getElementById('confirmModal');
        const messageEl = document.getElementById('confirmMessage');
        const confirmBtn = document.getElementById('confirmAction');
        const cancelBtn = document.getElementById('cancelConfirm');

        messageEl.textContent = message;
        modal.classList.add('active');

        const handleConfirm = () => {
            modal.classList.remove('active');
            onConfirm();
            cleanup();
        };

        const handleCancel = () => {
            modal.classList.remove('active');
            cleanup();
        };

        const cleanup = () => {
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
        };

        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
    },

    // 显示加载提示
    showLoading(message = '加载中...') {
        // 移除已存在的loading
        this.hideLoading();

        const loadingEl = document.createElement('div');
        loadingEl.id = 'admin-loading';
        loadingEl.className = 'admin-loading';
        loadingEl.innerHTML = `
            <div class="admin-loading-backdrop"></div>
            <div class="admin-loading-content">
                <div class="admin-loading-spinner"></div>
                <div class="admin-loading-text">${message}</div>
            </div>
        `;

        // 添加样式
        const style = document.createElement('style');
        style.id = 'admin-loading-style';
        style.textContent = `
            .admin-loading {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 9999;
            }
            .admin-loading-backdrop {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
            }
            .admin-loading-content {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 20px 30px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                text-align: center;
            }
            .admin-loading-spinner {
                width: 32px;
                height: 32px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #007bff;
                border-radius: 50%;
                animation: admin-loading-spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            .admin-loading-text {
                color: #333;
                font-size: 14px;
            }
            @keyframes admin-loading-spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(loadingEl);
    },

    // 隐藏加载提示
    hideLoading() {
        const loadingEl = document.getElementById('admin-loading');
        const styleEl = document.getElementById('admin-loading-style');

        if (loadingEl) {
            loadingEl.remove();
        }
        if (styleEl) {
            styleEl.remove();
        }
    }
};

// 认证管理
const AdminAuth = {
    // 初始化认证状态
    initAuth() {
        console.log('=== Initializing Authentication ===');
        const token = localStorage.getItem(ADMIN_CONFIG.STORAGE_KEYS.TOKEN);
        const userStr = localStorage.getItem(ADMIN_CONFIG.STORAGE_KEYS.USER);

        console.log('Token from storage:', token ? 'exists' : 'missing');
        console.log('User from storage:', userStr ? 'exists' : 'missing');

        if (token && userStr) {
            try {
                AdminState.token = token;
                AdminState.user = JSON.parse(userStr);
                AdminState.isAuthenticated = true;

                console.log('User data:', AdminState.user);
                console.log('User type:', AdminState.user.user_type);

                // 检查用户是否为管理员
                if (AdminState.user.user_type !== 'admin') {
                    console.error('User is not admin:', AdminState.user.user_type);
                    this.logout();
                    return false;
                }

                console.log('User is admin, validating token...');

                // 验证token格式
                if (!this.validateToken(token)) {
                    console.warn('Token格式无效，清除认证信息');
                    this.logout();
                    return false;
                }

                console.log('Authentication successful');
                this.updateUI();
                return true;
            } catch (error) {
                console.error('解析用户数据失败:', error);
                this.logout();
            }
        } else {
            console.log('No token or user data found');
        }
        return false;
    },

    // 验证token格式 - 简化版本
    validateToken(token) {
        if (!token || typeof token !== 'string') {
            console.log('Token is missing or not a string');
            return false;
        }

        // 简单的JWT token格式验证 (header.payload.signature)
        const parts = token.split('.');
        if (parts.length !== 3) {
            console.log('Token does not have 3 parts:', parts.length);
            return false;
        }

        try {
            // 尝试解析payload - 使用更兼容的方法
            const base64Url = parts[1].replace(/-/g, '+').replace(/_/g, '/');
            const payload = JSON.parse(window.atob(base64Url));
            console.log('Token payload:', payload);

            // 检查token是否过期
            const now = Math.floor(Date.now() / 1000);
            if (payload.exp && payload.exp < now) {
                console.log('Token expired:', new Date(payload.exp * 1000));
                return false;
            }

            console.log('Token valid, expires:', new Date(payload.exp * 1000));
            return true;
        } catch (error) {
            console.error('Token validation failed:', error);
            return false;
        }
    },

    // 更新UI
    updateUI() {
        if (AdminState.user) {
            document.getElementById('adminName').textContent = AdminState.user.real_name;
        }
    },

    // 退出登录
    logout() {
        AdminState.token = null;
        AdminState.user = null;
        AdminState.isAuthenticated = false;

        localStorage.removeItem(ADMIN_CONFIG.STORAGE_KEYS.TOKEN);
        localStorage.removeItem(ADMIN_CONFIG.STORAGE_KEYS.USER);

        window.location.href = '/admin-login';
    }
};

// 页面管理
const AdminPageManager = {
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
            AdminState.currentPage = pageName;
        }

        // 更新导航栏状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });

        const activeNavItem = document.querySelector(`[data-page="${pageName}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }

        // 更新面包屑
        this.updateBreadcrumb(pageName);

        // 页面切换时的处理
        this.onPageSwitch(pageName);
    },

    // 更新面包屑
    updateBreadcrumb(pageName) {
        const currentPageEl = document.getElementById('currentPage');
        const pageNames = {
            dashboard: '仪表板',
            users: '用户管理',
            organization: '组织管理',
            'visit-applications': '访问申请',
            'visit-records': '访问记录',
            statistics: '数据统计',
            'batch-approve': '批量授权',
            calendar: '校历管理',
            survey: '问卷管理',
            'database-backup': '数据库备份',
            'event-statistics': '返校日报名统计'
        };
        currentPageEl.textContent = pageNames[pageName] || pageName;
    },

    // 页面切换处理
    onPageSwitch(pageName) {
        switch (pageName) {
            case ADMIN_CONFIG.PAGES.DASHBOARD:
                DashboardPage.load();
                break;
            case ADMIN_CONFIG.PAGES.USERS:
                // 添加延迟以确保CSS过渡完成后再加载页面内容
                setTimeout(() => {
                    UsersPage.load();
                }, 350); // 略长于CSS过渡时间(300ms)
                break;
            case ADMIN_CONFIG.PAGES.ORGANIZATION:
                OrganizationPage.load();
                break;
            case ADMIN_CONFIG.PAGES.VISIT_APPLICATIONS:
                VisitApplicationsPage.load();
                break;
            case ADMIN_CONFIG.PAGES.VISIT_RECORDS:
                VisitRecordsPage.load();
                break;
            case ADMIN_CONFIG.PAGES.STATISTICS:
                StatisticsPage.load();
                break;
            case ADMIN_CONFIG.PAGES.BATCH_APPROVE:
                BatchApprovePage.load();
                break;
            case ADMIN_CONFIG.PAGES.CALENDAR:
                CalendarPage.load();
                break;
            case ADMIN_CONFIG.PAGES.SURVEY:
                SurveyPage.load();
                break;
            case ADMIN_CONFIG.PAGES.EVENT_STATISTICS:
                console.log('=== 初始化返校日报名统计页面 ===');
                EventStatisticsPage.init();
                break;
            case ADMIN_CONFIG.PAGES.KEY_MANAGEMENT:
                console.log('=== 初始化密钥管理页面 ===');
                KeyManagementPage.init();
                KeyManagementPage.load();
                break;
            case 'database-backup':
                console.log('=== 初始化数据库备份页面 ===');
                DatabaseBackupPage.init();
                break;
        }
    }
};

// 仪表板页面
const DashboardPage = {
    // 加载数据
    async load() {
        try {
            const data = await AdminUtils.request('/admin/dashboard');
            this.updateStats(data.statistics);
            this.initCharts(data.visit_trend, data.purpose_stats, data);
            this.loadRecentActivity();
            // this.loadRecentCalendarEvents();  // 已禁用校历事件功能
            this.bindEvents();
            this.renderDetailedStatistics(data);
        } catch (error) {
            console.error('加载仪表板数据失败:', error);
            AdminUtils.showToast('加载仪表板数据失败', 'error');
        }
    },

    // 绑定事件
    bindEvents() {
        // 导出制卡数据按钮
        const exportBtn = document.getElementById('exportCardDataBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportCardData();
            });
        }
    },

    // 导出制卡数据
    async exportCardData() {
        try {
            AdminUtils.showToast('正在导出制卡数据...', 'info');

            // 创建下载链接
            const response = await fetch('/admin/export/card-data', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                // 获取文件名
                const contentDisposition = response.headers.get('content-disposition');
                let filename = '制卡中心数据导出.xlsx';
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                    if (filenameMatch && filenameMatch[1]) {
                        filename = filenameMatch[1].replace(/['"]/g, '');
                    }
                }

                // 获取文件数据
                const blob = await response.blob();

                // 创建下载链接
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                AdminUtils.showToast('制卡数据导出成功', 'success');
            } else {
                const error = await response.json();
                AdminUtils.showToast(`导出失败: ${error.error || '未知错误'}`, 'error');
            }
        } catch (error) {
            console.error('导出制卡数据失败:', error);
            AdminUtils.showToast('导出制卡数据失败', 'error');
        }
    },

    // 更新统计数据
    updateStats(stats) {
        document.getElementById('totalUsers').textContent = stats.total_users || 0;
        document.getElementById('totalAlumni').textContent = stats.total_alumni || 0;
        document.getElementById('todayVisits').textContent = stats.today_visits || 0;
        // 只更新仪表板的待处理事项，不覆盖审核管理页面的统计
        document.getElementById('dashboardPendingCount').textContent =
            (stats.pending_alumni || 0) + (stats.pending_visits || 0);

        // 添加统计卡片点击事件
        this.addStatCardClickListeners(stats);
    },

    // 添加统计卡片点击事件监听器
    addStatCardClickListeners(stats) {
        // 总用户数卡片 - 点击跳转到用户列表
        const totalUsersCard = document.getElementById('totalUsers').parentElement.parentElement;
        totalUsersCard.style.cursor = 'pointer';
        totalUsersCard.onclick = () => {
            AdminPageManager.switchPage(ADMIN_CONFIG.PAGES.USERS);
        };

        // 注册校友卡片 - 点击跳转到校友列表并筛选
        const totalAlumniCard = document.getElementById('totalAlumni').parentElement.parentElement;
        totalAlumniCard.style.cursor = 'pointer';
        totalAlumniCard.onclick = () => {
            AdminPageManager.switchPage(ADMIN_CONFIG.PAGES.USERS);
            // 延迟执行筛选，确保页面已切换
            setTimeout(() => {
                // 设置用户类型筛选为校友
                const userTypeFilter = document.getElementById('userTypeFilter');
                if (userTypeFilter) {
                    userTypeFilter.value = 'alumni';
                    // 触发筛选
                    const filterEvent = new Event('change');
                    userTypeFilter.dispatchEvent(filterEvent);
                }
                // 设置排序为最新注册
                const sortBy = document.getElementById('sortBy');
                if (sortBy) {
                    sortBy.value = 'created_at';
                    const sortEvent = new Event('change');
                    sortBy.dispatchEvent(sortEvent);
                }
            }, 100);
        };

        // 今日访问卡片 - 点击跳转到访问记录页面
        const todayVisitsCard = document.getElementById('todayVisits').parentElement.parentElement;
        todayVisitsCard.style.cursor = 'pointer';
        todayVisitsCard.onclick = () => {
            AdminPageManager.switchPage(ADMIN_CONFIG.PAGES.VISIT_RECORDS);
        };

        // 待处理事项卡片 - 点击弹出待处理事项列表
        const pendingCountCard = document.getElementById('dashboardPendingCount').parentElement.parentElement;
        pendingCountCard.style.cursor = 'pointer';
        pendingCountCard.onclick = () => {
            this.showPendingItemsList(stats);
        };
    },

    // 显示待处理事项列表
    showPendingItemsList(stats) {
        const pendingItems = [];

        // 收集待处理事项
        if (stats.pending_alumni > 0) {
            pendingItems.push({
                type: 'alumni',
                count: stats.pending_alumni,
                text: `待审核校友 (${stats.pending_alumni})`,
                page: ADMIN_CONFIG.PAGES.USERS
            });
        }

        if (stats.pending_visits > 0) {
            pendingItems.push({
                type: 'visit',
                count: stats.pending_visits,
                text: `待处理访问申请 (${stats.pending_visits})`,
                page: ADMIN_CONFIG.PAGES.VISIT_APPLICATIONS
            });
        }

        if (pendingItems.length === 0) {
            AdminUtils.showToast('暂无待处理事项', 'info');
            return;
        }

        // 创建弹出层
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        `;

        // 创建弹出内容
        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            max-width: 400px;
            width: 90%;
            text-align: center;
        `;

        content.innerHTML = `
            <h3 style="margin-bottom: 20px; color: #1976d2;">待处理事项</h3>
            <div style="margin-bottom: 25px;">
                ${pendingItems.map(item => `
                    <div style="
                        padding: 12px 16px;
                        margin: 8px 0;
                        background: #f5f5f5;
                        border-radius: 8px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        border-left: 4px solid #1976d2;
                    " onclick="
                        ${item.type === 'alumni' ? `
                            AdminPageManager.switchPage('${item.page}');
                            setTimeout(() => {
                                const userTypeFilter = document.getElementById('userTypeFilter');
                                if (userTypeFilter) {
                                    userTypeFilter.value = 'alumni';
                                    const filterEvent = new Event('change');
                                    userTypeFilter.dispatchEvent(filterEvent);
                                }
                            }, 100);
                        ` : `AdminPageManager.switchPage('${item.page}');`}
                        document.body.remove(document.querySelector('[data-pending-modal]'))
                    ">
                        <div style="font-weight: 500; color: #333;">${item.text}</div>
                        <div style="font-size: 12px; color: #666; margin-top: 4px;">点击跳转处理</div>
                    </div>
                `).join('')}
            </div>
            <button style="
                background: #1976d2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            " onclick="document.body.remove(document.querySelector('[data-pending-modal]'));">关闭</button>
        `;

        modal.setAttribute('data-pending-modal', 'true');
        modal.appendChild(content);
        document.body.appendChild(modal);

        // 点击背景关闭
        modal.onclick = (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        };
    },

    // 初始化图表
    initCharts(visitTrend, purposeStats, fullData) {
        // 访问趋势图
        const trendCtx = document.getElementById('visitTrendChart');
        if (trendCtx) {
            if (AdminState.charts.trend) {
                AdminState.charts.trend.destroy();
            }

            AdminState.charts.trend = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: visitTrend.map(item => item.date.substring(5)),  // 只显示月-日
                    datasets: [{
                        label: '访问次数',
                        data: visitTrend.map(item => item.visits),
                        borderColor: '#1976d2',
                        backgroundColor: 'rgba(25, 118, 210, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // 访问目的分布图
        const purposeCtx = document.getElementById('purposeChart');
        if (purposeCtx) {
            if (AdminState.charts.purpose) {
                AdminState.charts.purpose.destroy();
            }

            AdminState.charts.purpose = new Chart(purposeCtx, {
                type: 'doughnut',
                data: {
                    labels: purposeStats.map(item => item.purpose),
                    datasets: [{
                        data: purposeStats.map(item => item.count),
                        backgroundColor: [
                            '#1976d2',
                            '#00c853',
                            '#ff9800',
                            '#dc004e',
                            '#9c27b0'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    },

    // 渲染详细统计数据
    renderDetailedStatistics(data) {
        // 渲染学生请假统计
        this.renderLeaveStatistics(data.leave_statistics);

        // 渲染校友入校统计
        this.renderAlumniStatistics(data.alumni_statistics);

        // 渲染访客统计
        this.renderVisitorStatistics(data.visitor_statistics);
    },

    // 渲染学生请假统计
    renderLeaveStatistics(leaveStats) {
        if (!leaveStats) return;

        const container = document.getElementById('leaveStatisticsContainer');
        if (!container) return;

        // 按年级统计
        const gradeHTML = leaveStats.by_grade && leaveStats.by_grade.length > 0 ?
            leaveStats.by_grade.map(item => `
                <div class="stat-item">
                    <span class="stat-label">${item.grade}</span>
                    <span class="stat-value">${item.count} 次</span>
                </div>
            `).join('') :
            '<p class="text-center text-secondary">暂无数据</p>';

        // 按班级统计（前10名）
        const classHTML = leaveStats.by_class && leaveStats.by_class.length > 0 ?
            leaveStats.by_class.slice(0, 10).map(item => `
                <div class="stat-item">
                    <span class="stat-label">${item.grade} ${item.class_name}</span>
                    <span class="stat-value">${item.count} 次</span>
                </div>
            `).join('') :
            '<p class="text-center text-secondary">暂无数据</p>';

        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="stat-card">
                        <h6>按年级统计</h6>
                        <div class="stat-list">
                            ${gradeHTML}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="stat-card">
                        <h6>按班级统计（TOP 10）</h6>
                        <div class="stat-list">
                            ${classHTML}
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    // 渲染校友入校统计
    renderAlumniStatistics(alumniStats) {
        if (!alumniStats) return;

        const container = document.getElementById('alumniStatisticsContainer');
        if (!container) return;

        // 按毕业年份统计
        const yearHTML = alumniStats.by_graduation_year && alumniStats.by_graduation_year.length > 0 ?
            alumniStats.by_graduation_year.slice(0, 10).map(item => `
                <div class="stat-item">
                    <span class="stat-label">${item.year} 届</span>
                    <span class="stat-value">${item.count} 人</span>
                </div>
            `).join('') :
            '<p class="text-center text-secondary">暂无数据</p>';

        // 按学部统计
        const divisionHTML = alumniStats.by_division && alumniStats.by_division.length > 0 ?
            alumniStats.by_division.map(item => `
                <div class="stat-item">
                    <span class="stat-label">${item.division}</span>
                    <span class="stat-value">${item.count} 人</span>
                </div>
            `).join('') :
            '<p class="text-center text-secondary">暂无数据</p>';

        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="stat-card">
                        <h6>按毕业年份统计（TOP 10）</h6>
                        <div class="stat-list">
                            ${yearHTML}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="stat-card">
                        <h6>按学部统计</h6>
                        <div class="stat-list">
                            ${divisionHTML}
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    // 渲染访客统计
    renderVisitorStatistics(visitorStats) {
        if (!visitorStats) return;

        const container = document.getElementById('visitorStatisticsContainer');
        if (!container) return;

        // 按受访者统计
        const personHTML = visitorStats.by_target_person && visitorStats.by_target_person.length > 0 ?
            visitorStats.by_target_person.slice(0, 10).map(item => `
                <div class="stat-item">
                    <span class="stat-label">${item.person}</span>
                    <span class="stat-value">${item.count} 次</span>
                </div>
            `).join('') :
            '<p class="text-center text-secondary">暂无数据</p>';

        // 按部门统计
        const deptHTML = visitorStats.by_department && visitorStats.by_department.length > 0 ?
            visitorStats.by_department.map(item => `
                <div class="stat-item">
                    <span class="stat-label">${item.department}</span>
                    <span class="stat-value">${item.count} 次</span>
                </div>
            `).join('') :
            '<p class="text-center text-secondary">暂无数据</p>';

        // 按状态统计
        const statusHTML = visitorStats.by_status && visitorStats.by_status.length > 0 ?
            visitorStats.by_status.map(item => `
                <div class="stat-item">
                    <span class="stat-label">${this.getStatusLabel(item.status)}</span>
                    <span class="stat-value">${item.count}</span>
                </div>
            `).join('') :
            '<p class="text-center text-secondary">暂无数据</p>';

        container.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <div class="stat-card">
                        <h6>按受访者统计（TOP 10）</h6>
                        <div class="stat-list">
                            ${personHTML}
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <h6>按部门统计</h6>
                        <div class="stat-list">
                            ${deptHTML}
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <h6>按状态统计</h6>
                        <div class="stat-list">
                            ${statusHTML}
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    // 获取状态标签
    getStatusLabel(status) {
        const labels = {
            'pending': '待审批',
            'approved': '已批准',
            'completed': '已完成',
            'rejected': '已拒绝',
            'cancelled': '已取消'
        };
        return labels[status] || status;
    },

    // 加载最近活动
    async loadRecentActivity() {
        try {
            const data = await AdminUtils.request('/visits/records?per_page=5');
            const container = document.getElementById('recentActivity');

            if (data.records.length === 0) {
                container.innerHTML = '<p class="text-center text-secondary">暂无最近活动</p>';
                return;
            }

            container.innerHTML = data.records.map(record => `
                <div class="activity-item">
                    <div class="activity-icon" style="background: ${this.getIconColor(record.verification_method)}">
                        <i class="ri-${this.getIcon(record.verification_method)}-line"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">${record.user.real_name} 入校访问</div>
                        <div class="activity-time">${AdminUtils.formatDateTime(record.entry_time)}</div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('加载最近活动失败:', error);
        }
    },

    getIcon(method) {
        const iconMap = {
            face: 'user-face',
            qr_code: 'qr-code',
            manual: 'user-follow'
        };
        return iconMap[method] || 'user';
    },

    getIconColor(method) {
        const colorMap = {
            face: 'linear-gradient(135deg, #00c853, #00e676)',
            qr_code: 'linear-gradient(135deg, #1976d2, #42a5f5)',
            manual: 'linear-gradient(135deg, #ff9800, #ffa726)'
        };
        return colorMap[method] || 'linear-gradient(135deg, #757575, #9e9e9e)';
    },

    // 加载最近校历事件
    async loadRecentCalendarEvents() {
        try {
            const params = new URLSearchParams({
                status: 'published',
                per_page: 5,
                sort_by: 'start_date',
                order: 'asc'
            });

            const data = await AdminUtils.request(`/calendar/events?${params}`);
            const container = document.getElementById('recentCalendarEvents');

            if (!container) {
                // 如果容器不存在，添加到仪表板
                this.addCalendarEventsSection();
                setTimeout(() => this.renderCalendarEvents(data.events), 100);
                return;
            }

            this.renderCalendarEvents(data.events);
        } catch (error) {
            console.error('加载校历事件失败:', error);
        }
    },

    // 添加校历事件区域到仪表板
    addCalendarEventsSection() {
        const chartsGrid = document.querySelector('.charts-grid');
        if (!chartsGrid) return;

        const calendarSection = document.createElement('div');
        calendarSection.className = 'calendar-events-section';
        calendarSection.innerHTML = `
            <div class="section-header">
                <h3>近期活动</h3>
                <a href="#calendar" class="view-all" data-page="calendar">查看全部</a>
            </div>
            <div class="events-list" id="recentCalendarEvents">
                <!-- 动态加载 -->
            </div>
        `;

        chartsGrid.parentNode.insertBefore(calendarSection, chartsGrid.nextSibling);

        // 绑定查看全部链接的点击事件
        calendarSection.querySelector('.view-all').addEventListener('click', (e) => {
            e.preventDefault();
            AdminPageManager.switchPage('calendar');
        });
    },

    // 渲染校历事件列表
    renderCalendarEvents(events) {
        const container = document.getElementById('recentCalendarEvents');
        if (!container) return;

        if (events.length === 0) {
            container.innerHTML = '<p class="text-center text-secondary">暂无近期活动</p>';
            return;
        }

        container.innerHTML = events.map(event => {
            const isUpcoming = new Date(event.start_date) >= new Date();
            const daysUntil = this.getDaysUntil(event.start_date);
            const eventTypeClass = `event-type-${event.event_type}`;

            return `
                <div class="event-item ${isUpcoming ? 'upcoming' : 'past'}">
                    <div class="event-indicator ${eventTypeClass}">
                        <i class="ri-${this.getEventIcon(event.event_type)}-line"></i>
                    </div>
                    <div class="event-content">
                        <div class="event-header">
                            <div class="event-title">${event.title}</div>
                            <div class="event-date">${daysUntil}</div>
                        </div>
                        <div class="event-meta">
                            <span class="event-type-badge">${this.getEventTypeText(event.event_type)}</span>
                            <span class="event-location">${event.location || '无地点'}</span>
                            <span class="event-date-time">${this.formatEventDateTime(event)}</span>
                        </div>
                        ${event.description ? `<div class="event-description">${event.description}</div>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    },

    // 获取活动图标
    getEventIcon(eventType) {
        const iconMap = {
            anniversary: 'gift',
            festival: ' lantern',
            activity: 'calendar-event',
            club: 'group',
            meeting: 'team',
            holiday: 'rest-time',
            exam: 'file-list-3'
        };
        return iconMap[eventType] || 'calendar';
    },

    // 获取事件类型文本
    getEventTypeText(type) {
        const types = {
            anniversary: '周年活动',
            festival: '传统节日',
            activity: '校园活动',
            club: '社团活动',
            meeting: '重要会议',
            holiday: '假期',
            exam: '考试'
        };
        return types[type] || type;
    },

    // 计算距离活动还有多少天
    getDaysUntil(startDate) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const eventDate = new Date(startDate);
        eventDate.setHours(0, 0, 0, 0);

        const diffTime = eventDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays < 0) {
            return `已过去 ${Math.abs(diffDays)} 天`;
        } else if (diffDays === 0) {
            return '今天';
        } else if (diffDays === 1) {
            return '明天';
        } else if (diffDays <= 7) {
            return `${diffDays} 天后`;
        } else {
            return AdminUtils.formatDate(startDate);
        }
    },

    // 格式化活动日期时间
    formatEventDateTime(event) {
        const dateStr = AdminUtils.formatDate(event.start_date);

        if (event.start_time) {
            return `${dateStr} ${event.start_time}`;
        }

        return dateStr;
    }
};

// 用户管理页面
const UsersPage = {
    currentPage: 1,
    filters: {},

    // 加载数据
    async load() {
        this.bindEvents();
        await this.loadUsers();
    },

    // 绑定事件
    bindEvents() {
        // 添加用户按钮
        const addUserBtn = document.querySelector('[onclick="UsersPage.showAddUserModal()"]');
        if (!addUserBtn) {
            // 如果没有onclick属性，查找包含"添加用户"文本的按钮
            const allButtons = document.querySelectorAll('button');
            allButtons.forEach(btn => {
                if (btn.textContent.includes('添加用户')) {
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        console.log('添加用户按钮被点击');
                        console.log('UsersPage对象:', UsersPage);
                        console.log('showAddUserModal方法:', typeof UsersPage.showAddUserModal);

                        if (typeof UsersPage.showAddUserModal === 'function') {
                            UsersPage.showAddUserModal();
                        } else {
                            // 备用方法：直接显示模态框
                            const modal = document.getElementById('addUserModal');
                            if (modal) {
                                modal.classList.add('show');
                                modal.style.display = 'flex';
                                modal.style.visibility = 'visible';
                                modal.style.opacity = '1';
                                document.body.style.overflow = 'hidden';
                                // 清空表单
                                if (typeof AdminUtils.resetAddUserForm === 'function') {
                                    AdminUtils.resetAddUserForm();
                                }
                            }
                        }
                    });
                }
            });
        }

        // 绑定全选复选框事件
        this.bindSelectAllEvent();

        // 绑定添加用户按钮（通过ID）
        const addUserBtnById = document.getElementById('addUserBtn');
        if (addUserBtnById) {
            addUserBtnById.addEventListener('click', () => {
                if (typeof AdminUtils.showAddUserModal === 'function') {
                    AdminUtils.showAddUserModal();
                } else {
                    // 备用方法
                    const modal = document.getElementById('addUserModal');
                    if (modal) {
                        modal.classList.add('show');
                        modal.style.display = 'flex';
                        modal.style.visibility = 'visible';
                        modal.style.opacity = '1';
                        document.body.style.overflow = 'hidden';
                    }
                }
            });
        }

        // 绑定批量删除按钮
        const batchDeleteBtn = document.getElementById('batchDeleteBtn');
        if (batchDeleteBtn) {
            batchDeleteBtn.addEventListener('click', () => {
                this.batchDeleteUsers();
            });
        }

        // 绑定批量导入按钮
        const batchImportBtn = document.getElementById('batchImportBtn');
        if (batchImportBtn) {
            batchImportBtn.addEventListener('click', () => {
                this.showBatchImportModal();
            });
        }

        // 绑定批量导出按钮
        const batchExportBtn = document.getElementById('batchExportBtn');
        if (batchExportBtn) {
            batchExportBtn.addEventListener('click', () => {
                this.batchExportUsers();
            });
        }

        // 绑定导出制卡数据按钮
        const exportCardDataBtn = document.getElementById('exportCardDataBtn');
        if (exportCardDataBtn) {
            exportCardDataBtn.addEventListener('click', () => {
                this.exportCardData();
            });
        }

        // 绑定刷新用户按钮
        const refreshUsersBtn = document.getElementById('refreshUsersBtn');
        if (refreshUsersBtn) {
            refreshUsersBtn.addEventListener('click', () => {
                this.refreshUsers();
            });
        }

        // 搜索
        const searchInput = document.getElementById('userSearch');
        if (searchInput) {
            searchInput.addEventListener('input', AdminUtils.debounce(() => {
                this.filters.search = searchInput.value;
                this.currentPage = 1;
                this.loadUsers();
            }, 500));
        }

        // 类型过滤
        const typeFilter = document.getElementById('userTypeFilter');
        if (typeFilter) {
            typeFilter.addEventListener('change', () => {
                this.filters.user_type = typeFilter.value;
                this.currentPage = 1;
                this.loadUsers();
            });
        }

        // 状态过滤
        const statusFilter = document.getElementById('userStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                this.filters.status = statusFilter.value;
                this.currentPage = 1;
                this.loadUsers();
            });
        }

        // 编辑模态框用户类型变化时显示/隐藏可拜访选项
        const editUserTypeSelect = document.getElementById('editUserType');
        if (editUserTypeSelect) {
            editUserTypeSelect.addEventListener('change', () => {
                const visitableGroup = document.getElementById('visitableGroup');
                // 所有用户类型都可以设置拜访权限
                if (['teacher', 'admin', 'alumni', 'security'].includes(editUserTypeSelect.value)) {
                    visitableGroup.style.display = 'block';
                } else {
                    visitableGroup.style.display = 'none';
                }
            });
        }

        // 添加用户模态框用户类型变化事件绑定在showAddUserModal中

        // 模态框外部点击关闭
        const userEditModal = document.getElementById('userEditModal');
        if (userEditModal) {
            userEditModal.addEventListener('click', (e) => {
                if (e.target === userEditModal) {
                    this.hideEditModal();
                }
            });
        }
    },

    // 添加新用户
    async addUser() {
        console.log('🚀🚀🚀 UsersPage.addUser开始执行');

        try {
            // 收集表单数据
            const formData = {
                username: document.getElementById('addUsername')?.value?.trim(),
                password: document.getElementById('addPassword')?.value?.trim(),
                real_name: document.getElementById('addRealName')?.value?.trim(),
                email: document.getElementById('addEmail')?.value?.trim(),
                phone: document.getElementById('addPhone')?.value?.trim(),
                user_type: document.getElementById('addUserType')?.value || 'teacher',
                student_id: document.getElementById('addStudentId')?.value?.trim(),
                employee_id: document.getElementById('addEmployeeId')?.value?.trim(),
                class_id: document.getElementById('addClassId')?.value?.trim(),
                grade: document.getElementById('addGrade')?.value?.trim(),
                is_class_teacher: document.getElementById('addIsClassTeacher')?.checked
            };

            // 添加拜访权限设置
            const visitableTypes = ['teacher', 'admin', 'alumni', 'security'];
            if (visitableTypes.includes(formData.user_type)) {
                formData.is_visitable = document.getElementById('addIsVisitable')?.checked || false;
            }

            console.log('📍 收集到的表单数据:', formData);

            // 验证必填字段
            const requiredFields = ['username', 'password', 'real_name', 'email', 'user_type'];
            for (const field of requiredFields) {
                if (!formData[field]) {
                    AdminUtils.showToast(`请填写${this.getFieldName(field)}`, 'error');
                    return;
                }
            }

            console.log('✅ 必填字段验证通过');

            // 验证邮箱格式
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(formData.email)) {
                AdminUtils.showToast('请填写有效的邮箱地址', 'error');
                return;
            }

            // 验证密码长度
            if (formData.password.length < 6) {
                AdminUtils.showToast('密码长度至少6位', 'error');
                return;
            }

            console.log('✅ 所有验证通过');

            // 使用直接的fetch请求，绕过有问题的AdminUtils.request
            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            console.log('📍 Token存在，准备发送请求...');

            const requestData = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify(formData)
            };

            console.log('📍 发送请求配置:', requestData);

            const response = await fetch(ADMIN_CONFIG.API_BASE_URL + '/admin/users', requestData);
            console.log('📍 响应状态:', response.status);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `请求失败 (${response.status})`);
            }

            const data = await response.json();
            console.log('📍 响应数据:', data);

            if (data.message) {
                AdminUtils.showToast('用户创建成功', 'success');
                this.hideAddUserModal();
                this.loadUsers(); // 重新加载用户列表
            } else {
                AdminUtils.showToast('用户创建失败: ' + (data.error || '未知错误'), 'error');
            }

        } catch (error) {
            console.error('❌ UsersPage.addUser执行失败:', error);
            AdminUtils.showToast('创建用户失败: ' + error.message, 'error');
        }
    },

    // 检查密码强度
    checkPasswordStrength(password) {
        const strengthIndicator = document.getElementById('passwordStrength');
        const strengthBar = strengthIndicator.querySelector('.strength-bar');
        const strengthText = strengthIndicator.querySelector('.strength-text');
        let strength = 0;
        let strengthLevel = 'weak';
        let strengthTextContent = '密码强度：弱';

        // 检查长度
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;

        // 检查复杂度
        if (/[a-z]/.test(password)) strength++; // 小写字母
        if (/[A-Z]/.test(password)) strength++; // 大写字母
        if (/\d/.test(password)) strength++; // 数字
        if (/[^a-zA-Z\d]/.test(password)) strength++; // 特殊字符

        // 根据强度等级设置样式
        if (strength <= 2) {
            strengthLevel = 'weak';
            strengthTextContent = '密码强度：弱';
        } else if (strength <= 4) {
            strengthLevel = 'medium';
            strengthTextContent = '密码强度：中';
        } else {
            strengthLevel = 'strong';
            strengthTextContent = '密码强度：强';
        }

        // 更新样式
        strengthIndicator.className = `password-strength-indicator strength-${strengthLevel}`;
        strengthText.textContent = strengthTextContent;
    },

    // 获取字段中文名
    getFieldName(field) {
        const fieldNames = {
            username: '用户名',
            password: '密码',
            real_name: '真实姓名',
            email: '邮箱',
            user_type: '用户类型'
        };
        return fieldNames[field] || field;
    },

    // 显示添加用户模态框
    showAddUserModal() {
        const modal = document.getElementById('addUserModal');
        if (modal) {
            modal.classList.add('show');
            // 强制设置显示样式，确保模态框可见
            modal.style.display = 'flex';
            modal.style.visibility = 'visible';
            modal.style.opacity = '1';
            document.body.style.overflow = 'hidden';
            // 清空表单
            this.resetAddUserForm();

            // 绑定用户类型变化事件
            this.bindAddUserTypeChange();
        }
    },

    // 隐藏添加用户模态框
    hideAddUserModal() {
        const modal = document.getElementById('addUserModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.style.visibility = 'hidden';
            modal.style.opacity = '0';
        }
        document.body.style.overflow = '';
    },

    // 重置添加用户表单
    resetAddUserForm() {
        document.getElementById('addUsername').value = '';
        document.getElementById('addPassword').value = '';
        document.getElementById('addRealName').value = '';
        document.getElementById('addEmail').value = '';
        document.getElementById('addPhone').value = '';
        document.getElementById('addUserType').value = 'teacher';
        document.getElementById('addStudentId').value = '';
        document.getElementById('addEmployeeId').value = '';
        document.getElementById('addClassId').value = '';
        document.getElementById('addGrade').value = '';
        document.getElementById('addIsClassTeacher').checked = false;
    },

    // 绑定添加用户模态框的用户类型变化事件
    bindAddUserTypeChange() {
        const addUserTypeSelect = document.getElementById('addUserType');
        if (!addUserTypeSelect) return;

        // 移除旧的事件监听器
        const newSelect = addUserTypeSelect.cloneNode(true);
        addUserTypeSelect.parentNode.replaceChild(newSelect, addUserTypeSelect);

        // 添加新的事件监听器
        newSelect.addEventListener('change', () => {
            const userType = newSelect.value;
            this.updateAddUserFieldsVisibility(userType);
        });

        // 绑定密码输入事件
        const passwordInput = document.getElementById('addPassword');
        if (passwordInput) {
            passwordInput.addEventListener('input', (e) => {
                this.checkPasswordStrength(e.target.value);
            });
        }

        // 初始化字段可见性
        this.updateAddUserFieldsVisibility(newSelect.value);
    },

    // 更新添加用户字段的可见性
    updateAddUserFieldsVisibility(userType) {
        const studentIdGroup = document.getElementById('addStudentIdGroup');
        const employeeIdGroup = document.getElementById('addEmployeeIdGroup');
        const classIdGroup = document.getElementById('addClassIdGroup');
        const gradeGroup = document.getElementById('addGradeGroup');
        const isClassTeacherGroup = document.getElementById('addIsClassTeacherGroup');
        const visitableGroup = document.getElementById('addVisitableGroup');
        const visitableDivider = document.getElementById('addVisitableDivider');
        const studentFieldsDivider = document.getElementById('addStudentFieldsDivider');

        // 隐藏所有可选字段和分割线
        if (studentIdGroup) studentIdGroup.style.display = 'none';
        if (employeeIdGroup) employeeIdGroup.style.display = 'none';
        if (classIdGroup) classIdGroup.style.display = 'none';
        if (gradeGroup) gradeGroup.style.display = 'none';
        if (isClassTeacherGroup) isClassTeacherGroup.style.display = 'none';
        if (visitableGroup) visitableGroup.style.display = 'none';
        if (visitableDivider) visitableDivider.style.display = 'none';
        if (studentFieldsDivider) studentFieldsDivider.style.display = 'none';

        // 根据用户类型显示相应字段
        switch (userType) {
            case 'student':
                if (studentFieldsDivider) studentFieldsDivider.style.display = 'block';
                if (studentIdGroup) studentIdGroup.style.display = 'block';
                if (classIdGroup) classIdGroup.style.display = 'block';
                if (gradeGroup) gradeGroup.style.display = 'block';
                break;
            case 'teacher':
                if (visitableDivider) visitableDivider.style.display = 'block';
                if (studentFieldsDivider) studentFieldsDivider.style.display = 'block';
                if (employeeIdGroup) employeeIdGroup.style.display = 'block';
                if (classIdGroup) classIdGroup.style.display = 'block';
                if (isClassTeacherGroup) isClassTeacherGroup.style.display = 'block';
                if (visitableGroup) visitableGroup.style.display = 'block';
                break;
            case 'parent':
                // 家长通常不需要这些字段
                break;
            case 'alumni':
                if (visitableDivider) visitableDivider.style.display = 'block';
                if (studentFieldsDivider) studentFieldsDivider.style.display = 'block';
                if (studentIdGroup) studentIdGroup.style.display = 'block';
                if (visitableGroup) visitableGroup.style.display = 'block';
                break;
            case 'security':
                if (visitableDivider) visitableDivider.style.display = 'block';
                if (studentFieldsDivider) studentFieldsDivider.style.display = 'block';
                if (employeeIdGroup) employeeIdGroup.style.display = 'block';
                if (visitableGroup) visitableGroup.style.display = 'block';
                break;
            case 'admin':
                if (visitableDivider) visitableDivider.style.display = 'block';
                if (studentFieldsDivider) studentFieldsDivider.style.display = 'block';
                if (employeeIdGroup) employeeIdGroup.style.display = 'block';
                if (visitableGroup) visitableGroup.style.display = 'block';
                break;
        }
    },

    // 加载用户列表
    async loadUsers() {
        try {
            console.log('📍 UsersPage.loadUsers 开始执行');

            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: 20,
                ...this.filters
            });

            console.log('📍 查询参数:', params.toString());

            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                console.error('❌ 未找到认证token');
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            const response = await fetch(ADMIN_CONFIG.API_BASE_URL + `/admin/users?${params}`, {
                method: 'GET',
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
            });

            console.log('📍 用户列表响应状态:', response.status);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `请求失败 (${response.status})`);
            }

            const data = await response.json();
            console.log('📍 用户列表数据:', data);

            if (data.users && data.pagination) {
                this.renderUsers(data.users);
                this.renderPagination(data.pagination);
            } else {
                console.error('❌ 用户列表数据格式不正确:', data);
                AdminUtils.showToast('用户列表数据格式错误', 'error');
            }
        } catch (error) {
            console.error('❌ 加载用户列表失败:', error);
            AdminUtils.showToast('加载用户列表失败: ' + error.message, 'error');
        }
    },

    // 渲染用户表格
    renderUsers(users) {
        const tbody = document.querySelector('#usersTable tbody');
        if (!tbody) return;

        // 计算序号的起始值
        const startIndex = (this.currentPage - 1) * 20 + 1;

        tbody.innerHTML = users.map((user, index) => {
            const serialNumber = startIndex + index;
            return `
            <tr>
                <td>
                    <input type="checkbox" class="user-checkbox" data-user-id="${user.id}" title="选择用户">
                </td>
                <td>${serialNumber}</td>
                <td>${user.username}</td>
                <td>${user.real_name}</td>
                <td>${AdminUtils.getUserTypeText(user.user_type)}</td>
                <td>${user.email}</td>
                <td>${user.phone}</td>
                <td><span class="status-badge ${user.status}">${AdminUtils.getStatusText(user.status)}</span></td>
                <td>
                    ${user.is_visitable ? `
                        <span class="visitable-badge visitable">
                            可拜访 ${user.employee_id ? `(ID: ${user.employee_id})` : ''}
                        </span>
                    ` : '-'}
                </td>
                <td>${AdminUtils.formatDate(user.created_at)}</td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline" onclick="UsersPage.editUser(${user.id})" title="编辑">
                            <i class="ri-edit-line"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="UsersPage.toggleStatus(${user.id}, '${user.status}')" title="${user.status === 'active' ? '禁用' : '启用'}">
                            <i class="ri-${user.status === 'active' ? 'disable' : 'enable'}-line"></i>
                        </button>
                        <button class="btn btn-sm btn-outline btn-danger" onclick="UsersPage.deleteUser(${user.id}, '${user.username}')" title="删除">
                            <i class="ri-delete-bin-line"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        }).join('');

        // 绑定全选复选框事件
        this.bindSelectAllEvent();
    },

    // 渲染分页
    renderPagination(pagination) {
        const container = document.getElementById('usersPagination');
        if (!container) {
            console.warn('usersPagination element not found');
            return;
        }

        let html = '';

        // 上一页
        html += `<button ${pagination.has_prev ? '' : 'disabled'} onclick="UsersPage.goToPage(${pagination.page - 1})">上一页</button>`;

        // 页码
        for (let i = 1; i <= pagination.pages; i++) {
            html += `<button class="${i === pagination.page ? 'active' : ''}" onclick="UsersPage.goToPage(${i})">${i}</button>`;
        }

        // 下一页
        html += `<button ${pagination.has_next ? '' : 'disabled'} onclick="UsersPage.goToPage(${pagination.page + 1})">下一页</button>`;

        container.innerHTML = html;
    },

    // 跳转页面
    goToPage(page) {
        this.currentPage = page;
        this.loadUsers();
    },

    // 绑定全选复选框事件
    bindSelectAllEvent() {
        const selectAllCheckbox = document.getElementById('selectAllUsers');
        const userCheckboxes = document.querySelectorAll('.user-checkbox');

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                const isChecked = e.target.checked;
                userCheckboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                });
            });
        }

        // 为每个用户复选框添加事件监听
        userCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateSelectAllCheckbox();
            });
        });
    },

    // 更新全选复选框状态
    updateSelectAllCheckbox() {
        const selectAllCheckbox = document.getElementById('selectAllUsers');
        const userCheckboxes = document.querySelectorAll('.user-checkbox');
        const checkedCheckboxes = document.querySelectorAll('.user-checkbox:checked');
        const batchDeleteBtn = document.getElementById('batchDeleteBtn');
        const selectedCount = document.getElementById('selectedCount');

        if (selectAllCheckbox) {
            if (userCheckboxes.length === 0) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            } else if (checkedCheckboxes.length === 0) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            } else if (checkedCheckboxes.length === userCheckboxes.length) {
                selectAllCheckbox.checked = true;
                selectAllCheckbox.indeterminate = false;
            } else {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = true;
            }
        }

        // 更新批量删除按钮状态
        if (batchDeleteBtn && selectedCount) {
            const count = checkedCheckboxes.length;
            selectedCount.textContent = count;

            if (count > 0) {
                batchDeleteBtn.style.display = 'inline-flex';
            } else {
                batchDeleteBtn.style.display = 'none';
            }
        }
    },

    // 获取选中的用户ID列表
    getSelectedUserIds() {
        const checkedCheckboxes = document.querySelectorAll('.user-checkbox:checked');
        return Array.from(checkedCheckboxes).map(checkbox =>
            parseInt(checkbox.dataset.userId)
        );
    },

    // 获取选中的用户数量
    getSelectedUsersCount() {
        return document.querySelectorAll('.user-checkbox:checked').length;
    },

    // 隐藏添加用户模态框
    hideAddUserModal() {
        const modal = document.getElementById('addUserModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.style.visibility = 'hidden';
            modal.style.opacity = '0';
        }
        document.body.style.overflow = '';
    },

    // 切换密码可见性
    togglePasswordVisibility(fieldId) {
        const passwordField = document.getElementById(fieldId);
        const toggleIcon = document.getElementById(fieldId + 'ToggleIcon');

        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            toggleIcon.className = 'ri-eye-off-line';
        } else {
            passwordField.type = 'password';
            toggleIcon.className = 'ri-eye-line';
        }
    },

    // 检查密码强度
    checkPasswordStrength(password) {
        const strengthIndicator = document.getElementById('passwordStrength');
        const strengthBar = strengthIndicator.querySelector('.strength-bar');
        const strengthText = strengthIndicator.querySelector('.strength-text');

        let strength = 0;
        let strengthLevel = 'weak';
        let strengthTextContent = '密码强度：弱';

        // 检查长度
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;

        // 检查复杂度
        if (/[a-z]/.test(password)) strength++; // 小写字母
        if (/[A-Z]/.test(password)) strength++; // 大写字母
        if (/\d/.test(password)) strength++; // 数字
        if (/[^a-zA-Z\d]/.test(password)) strength++; // 特殊字符

        // 根据强度等级设置样式
        if (strength <= 2) {
            strengthLevel = 'weak';
            strengthTextContent = '密码强度：弱';
        } else if (strength <= 4) {
            strengthLevel = 'medium';
            strengthTextContent = '密码强度：中';
        } else {
            strengthLevel = 'strong';
            strengthTextContent = '密码强度：强';
        }

        // 更新样式
        strengthIndicator.className = `password-strength-indicator strength-${strengthLevel}`;
        strengthText.textContent = strengthTextContent;
    },

    // 显示批量导入模态框
    showBatchImportModal() {
        const modal = document.getElementById('batchImportModal');
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
            modal.style.visibility = 'visible';
            modal.style.opacity = '1';
            document.body.style.overflow = 'hidden';
            this.resetBatchImportForm();
            this.bindBatchImportEvents();
        }
    },

    // 隐藏批量导入模态框
    hideBatchImportModal() {
        const modal = document.getElementById('batchImportModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.style.visibility = 'hidden';
            modal.style.opacity = '0';
        }
        document.body.style.overflow = '';
    },

    // 重置批量导入表单
    resetBatchImportForm() {
        document.getElementById('fileInput').value = '';
        document.getElementById('uploadStep').style.display = 'block';
        document.getElementById('previewStep').style.display = 'none';
        document.getElementById('resultStep').style.display = 'none';
        document.getElementById('confirmImportBtn').style.display = 'none';
        document.getElementById('downloadTemplateBtn').style.display = 'inline-flex';
        document.getElementById('closeImportResultBtn').style.display = 'none';
        document.getElementById('previewTableBody').innerHTML = '';
        document.getElementById('importSummary').innerHTML = '';
    },

    // 绑定批量导入事件
    bindBatchImportEvents() {
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');

        // 文件选择事件
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileUpload(file);
            }
        });

        // 拖拽事件
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) {
                this.handleFileUpload(file);
            }
        });
    },

    // 处理文件上传
    async handleFileUpload(file) {
        try {
            console.log('=== 开始处理文件上传 ===');
            console.log('文件名:', file.name);
            console.log('文件大小:', file.size, 'bytes');
            console.log('文件类型:', file.type);

            // 检查文件类型
            if (!file.name.match(/\.(xlsx|xls|csv)$/)) {
                AdminUtils.showToast('请选择Excel文件 (.xlsx, .xls) 或 CSV文件 (.csv)', 'error');
                return;
            }

            // 检查文件大小 (10MB)
            if (file.size > 10 * 1024 * 1024) {
                AdminUtils.showToast('文件大小不能超过10MB', 'error');
                return;
            }

            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                console.error('❌ 未找到认证token');
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            console.log('✓ Token存在');

            // 创建FormData
            const formData = new FormData();
            formData.append('file', file);
            // 添加文件类型信息
            formData.append('file_type', file.name.endsWith('.csv') ? 'csv' : 'excel');

            console.log('✓ FormData已创建');

            AdminUtils.showLoading('正在解析文件...');

            // 发送到服务器进行解析
            const response = await fetch('/api/admin/users/import-preview', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            console.log('✓ 响应状态:', response.status);

            AdminUtils.hideLoading();

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error('❌ 文件上传失败:', errorData);
                throw new Error(errorData.error || `文件上传失败 (${response.status})`);
            }

            const result = await response.json();
            console.log('✓ 解析结果:', result);

            if (result.success) {
                console.log('✓ 显示预览，用户数量:', result.data.users.length);
                this.showImportPreview(result.data);
            } else {
                console.error('❌ 解析失败:', result);
                AdminUtils.showToast('文件解析失败: ' + (result.message || result.error || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('❌ 文件上传失败:', error);
            AdminUtils.hideLoading();
            AdminUtils.showToast('文件上传失败: ' + error.message, 'error');
        }
    },

    // 显示导入预览
    showImportPreview(data) {
        console.log('=== 显示导入预览 ===');
        console.log('用户数量:', data.users.length);

        // 切换步骤显示
        const uploadStep = document.getElementById('uploadStep');
        const previewStep = document.getElementById('previewStep');
        const confirmBtn = document.getElementById('confirmImportBtn');
        const downloadBtn = document.getElementById('downloadTemplateBtn');

        console.log('上传步骤元素:', uploadStep);
        console.log('预览步骤元素:', previewStep);
        console.log('确认导入按钮元素:', confirmBtn);
        console.log('下载模板按钮元素:', downloadBtn);

        uploadStep.style.display = 'none';
        previewStep.style.display = 'block';
        confirmBtn.style.display = 'inline-flex';
        downloadBtn.style.display = 'none';

        console.log('✓ 已切换到预览步骤');
        console.log('✓ 确认导入按钮已显示');

        // 更新预览数量
        document.getElementById('previewCount').textContent = data.users.length;

        // 生成预览表格 - 使用制卡中心格式
        const tbody = document.getElementById('previewTableBody');
        tbody.innerHTML = data.users.map(user => {
            // 构建部门信息
            const orgInfo = [user.org_level1, user.org_level2, user.org_level3, user.org_level4]
                .filter(level => level && level.trim())
                .join(' > ');

            return `
            <tr>
                <td>${user.username || '-'}</td>
                <td>${user.real_name || '-'}</td>
                <td>${AdminUtils.getUserTypeText(user.user_type)}</td>
                <td>${user.phone || '-'}</td>
                <td>${user.id_card || '-'}</td>
                <td>${user.subsidy_type !== undefined ? user.subsidy_type : '-'}</td>
                <td>${orgInfo || '-'}</td>
                <td><span class="status-badge ${user.valid ? 'success' : 'error'}">${user.valid ? '正常' : '错误'}</span></td>
            </tr>
            `;
        }).join('');

        // 存储预览数据供确认时使用
        this.importPreviewData = data;
        console.log('=== 预览显示完成 ===');
    },

    // 确认批量导入
    async confirmBatchImport() {
        try {
            AdminUtils.showLoading('正在导入用户...');

            const response = await AdminUtils.request('/api/admin/users/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    users: this.importPreviewData.users
                })
            });

            if (response.success) {
                this.showImportResult(response.data);
                // 重新加载用户列表
                await this.loadUsers();
            } else {
                AdminUtils.showToast('导入失败: ' + (response.message || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('批量导入失败:', error);
            AdminUtils.showToast('批量导入失败: ' + error.message, 'error');
        } finally {
            AdminUtils.hideLoading();
        }
    },

    // 显示导入结果
    showImportResult(data) {
        document.getElementById('previewStep').style.display = 'none';
        document.getElementById('resultStep').style.display = 'block';
        document.getElementById('confirmImportBtn').style.display = 'none';
        document.getElementById('closeImportResultBtn').style.display = 'inline-flex';

        const summary = document.getElementById('importSummary');
        summary.innerHTML = `
            <h4>导入完成</h4>
            <p>总数：<strong>${data.total}</strong></p>
            <p>成功：<span class="success-count">${data.success}</span></p>
            <p>失败：<span class="error-count">${data.failed}</span></p>
            ${data.warnings > 0 ? `<p>警告：<span class="warning-count">${data.warnings}</span></p>` : ''}
            ${data.errors && data.errors.length > 0 ? `
                <div class="error-details">
                    <h5>错误详情：</h5>
                    <ul>
                        ${data.errors.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
    },

    // 下载用户模板
    async downloadUserTemplate() {
        try {
            console.log('=== 开始下载用户模板 ===');

            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                console.error('❌ 未找到认证token');
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            console.log('✓ Token存在:', token ? 'Yes' : 'No');

            const response = await fetch('/api/admin/users/template', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            console.log('✓ 响应状态:', response.status);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error('❌ 下载失败:', errorData);
                throw new Error(errorData.error || `下载失败 (${response.status})`);
            }

            const blob = await response.blob();
            console.log('✓ Blob大小:', blob.size, 'bytes');

            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = '用户导入模板.xlsx';
            link.style.display = 'none';
            document.body.appendChild(link);

            console.log('✓ 触发下载');
            link.click();

            // 清理
            setTimeout(() => {
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            }, 100);

            AdminUtils.showToast('模板下载成功', 'success');
            console.log('=== 下载完成 ===');
        } catch (error) {
            console.error('❌ 下载模板失败:', error);
            AdminUtils.showToast('下载模板失败: ' + error.message, 'error');
        }
    },

    // 批量导出用户
    async batchExportUsers() {
        try {
            AdminUtils.showLoading('正在导出用户数据...');

            // 获取当前筛选条件
            const params = new URLSearchParams();
            if (this.filters.search) params.append('search', this.filters.search);
            if (this.filters.user_type) params.append('user_type', this.filters.user_type);
            if (this.filters.status) params.append('status', this.filters.status);

            const response = await fetch(`/admin/users/export?${params}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error('导出失败');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `用户数据_${new Date().toISOString().split('T')[0]}.xlsx`;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            AdminUtils.showToast('导出成功', 'success');
        } catch (error) {
            console.error('批量导出失败:', error);
            AdminUtils.showToast('导出失败: ' + error.message, 'error');
        } finally {
            AdminUtils.hideLoading();
        }
    },

    // 导出制卡数据
    async exportCardData() {
        try {
            AdminUtils.showToast('正在导出制卡数据...', 'info');

            const response = await fetch('/api/admin/export/card-data', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;

                // 生成文件名
                const now = new Date();
                const dateStr = now.toISOString().split('T')[0];
                const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-');
                a.download = `制卡数据_${dateStr}_${timeStr}.xlsx`;

                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                AdminUtils.showToast('制卡数据导出成功', 'success');
            } else {
                const error = await response.json();
                AdminUtils.showToast(`导出失败: ${error.error || '未知错误'}`, 'error');
            }
        } catch (error) {
            console.error('导出制卡数据失败:', error);
            AdminUtils.showToast('导出制卡数据失败', 'error');
        }
    },

    // 批量删除用户
    async batchDeleteUsers() {
        const selectedIds = this.getSelectedUserIds();

        if (selectedIds.length === 0) {
            AdminUtils.showToast('请选择要删除的用户', 'warning');
            return;
        }

        // 确认删除
        const confirmed = confirm(`确定要删除选中的 ${selectedIds.length} 个用户吗？此操作不可恢复！`);
        if (!confirmed) {
            return;
        }

        try {
            // 发送删除请求
            const response = await AdminUtils.request('/admin/users/batch-delete', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_ids: selectedIds
                })
            });

            if (response.success) {
                AdminUtils.showToast(`成功删除 ${selectedIds.length} 个用户`, 'success');

                // 清空选择状态
                document.getElementById('selectAllUsers').checked = false;
                document.getElementById('selectAllUsers').indeterminate = false;

                // 重新加载用户列表
                await this.loadUsers();
            } else {
                AdminUtils.showToast('删除失败: ' + (response.message || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('批量删除用户失败:', error);
            AdminUtils.showToast('删除失败: ' + error.message, 'error');
        }
    },

    // 刷新用户列表
    async refreshUsers() {
        try {
            // 显示刷新按钮的加载状态
            const refreshBtn = document.getElementById('refreshUsersBtn');
            if (refreshBtn) {
                const originalContent = refreshBtn.innerHTML;
                refreshBtn.innerHTML = '<i class="ri-loader-4-line"></i> 刷新中...';
                refreshBtn.disabled = true;

                // 添加旋转动画
                refreshBtn.querySelector('i').style.animation = 'spin 1s linear infinite';
            }

            // 重置到第一页
            this.currentPage = 1;

            // 重新加载用户数据
            await this.loadUsers();

            // 恢复按钮状态
            if (refreshBtn) {
                refreshBtn.innerHTML = originalContent;
                refreshBtn.disabled = false;

                // 移除旋转动画
                const icon = refreshBtn.querySelector('i');
                if (icon) {
                    icon.style.animation = '';
                }
            }

            AdminUtils.showToast('用户列表已刷新', 'success');
        } catch (error) {
            console.error('刷新用户列表失败:', error);
            AdminUtils.showToast('刷新失败: ' + error.message, 'error');

            // 恢复按钮状态
            const refreshBtn = document.getElementById('refreshUsersBtn');
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i class="ri-refresh-line"></i> 刷新';
                refreshBtn.disabled = false;
            }
        }
    },

    // 保存用户
    async saveUser() {
        try {
            const userId = document.getElementById('editUserId').value;

            // 获取选中的用户类型
            const selectedTypes = [];
            const checkboxes = document.querySelectorAll('#editUserTypes input[type="checkbox"]:checked');
            checkboxes.forEach(cb => selectedTypes.push(cb.value));

            if (selectedTypes.length === 0) {
                AdminUtils.showToast('请至少选择一个用户类型', 'error');
                return;
            }

            const formData = {
                real_name: document.getElementById('editRealName').value.trim(),
                email: document.getElementById('editEmail').value.trim(),
                phone: document.getElementById('editPhone').value.trim(),
                user_type: selectedTypes.join(','), // 将数组转为逗号分隔的字符串
                status: document.getElementById('editStatus').value,
                student_id: document.getElementById('editStudentId').value.trim(),
                employee_id: document.getElementById('editEmployeeId').value.trim()
            };

            // 如果包含可设置拜访权限的用户类型，添加可拜访权限
            const visitableTypes = ['teacher', 'admin', 'alumni', 'security'];
            if (selectedTypes.some(type => visitableTypes.includes(type))) {
                formData.is_visitable = document.getElementById('editIsVisitable').checked;
            }

            console.log('📍 准备保存的用户数据:', formData);
            console.log('📍 选中的用户类型:', selectedTypes);

            // 验证必填字段
            if (!formData.real_name || !formData.email || !formData.phone) {
                AdminUtils.showToast('请填写所有必填字段', 'error');
                return;
            }

            const data = await AdminUtils.request(`/admin/users/${userId}`, {
                method: 'PUT',
                body: JSON.stringify(formData)
            });

            console.log('📍 保存响应:', data);

            if (data.success) {
                AdminUtils.showToast('用户信息更新成功', 'success');
                this.hideEditModal();
                this.loadUsers();
            }
        } catch (error) {
            AdminUtils.showToast('保存失败: ' + error.message, 'error');
        }
    },

    // 切换可拜访权限
    async toggleVisitable(userId, isVisitable) {
        try {
            const data = await AdminUtils.request(`/admin/users/${userId}/visitable`, {
                method: 'PUT',
                body: JSON.stringify({ is_visitable: isVisitable })
            });

            if (data.success) {
                const status = isVisitable ? '可拜访' : '不可拜访';
                AdminUtils.showToast(`用户已设置为${status}`, 'success');
                this.loadUsers();
            }
        } catch (error) {
            AdminUtils.showToast('设置失败: ' + error.message, 'error');
        }
    },

    // 切换用户状态
    async toggleStatus(userId, currentStatus) {
        const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
        const action = newStatus === 'active' ? '激活' : '禁用';

        AdminUtils.showConfirm(`确定要${action}该用户吗？`, async () => {
            try {
                await AdminUtils.request(`/admin/users/${userId}/status`, {
                    method: 'PUT',
                    body: JSON.stringify({ status: newStatus })
                });

                AdminUtils.showToast(`用户${action}成功`, 'success');
                this.loadUsers();
            } catch (error) {
                AdminUtils.showToast(`用户${action}失败`, 'error');
            }
        });
    },

    // 显示编辑模态框
    showEditModal() {
        const modal = document.getElementById('editUserModal');
        if (modal) {
            modal.classList.add('show');
            // 强制设置显示样式，确保模态框可见
            modal.style.display = 'flex';
            modal.style.visibility = 'visible';
            modal.style.opacity = '1';
            document.body.style.overflow = 'hidden';
        }
    },

    // 隐藏编辑模态框
    hideEditModal() {
        const modal = document.getElementById('editUserModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.style.visibility = 'hidden';
            modal.style.opacity = '0';
        }
        document.body.style.overflow = '';
    },

    // 关闭编辑模态框 (别名方法)
    closeEditModal() {
        this.hideEditModal();
    },

    // 加载编辑对话框中的用户角色信息
    async loadEditUserRoles(userId) {
        try {
            // 获取用户角色
            const rolesData = await AdminUtils.request(`/roles/user/${userId}`);
            if (rolesData.success) {
                const currentRoles = rolesData.data.roles;
                const currentRolesHtml = currentRoles.map(role => `
                    <div class="role-item assigned">
                        <div class="role-info">
                            <h6>${role.display_name}</h6>
                            <p>${role.description || '暂无描述'}</p>
                        </div>
                        <div class="role-actions">
                            <span class="role-badge">已分配</span>
                            <button class="btn btn-sm btn-outline btn-danger" onclick="UsersPage.removeRole(${role.id}, ${userId})" title="取消分配">
                                <i class="ri-close-line"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
                document.getElementById('editCurrentRoles').innerHTML = currentRolesHtml || '<p style="color: var(--text-secondary); font-size: 12px;">暂无角色</p>';
            }

            // 获取所有可用角色
            const allRolesData = await AdminUtils.request('/roles');
            if (allRolesData.success) {
                const allRoles = allRolesData.data.roles;
                const assignedRoleIds = new Set(rolesData.data?.roles?.map(r => r.id) || []);

                const availableRoles = allRoles.filter(role => !assignedRoleIds.has(role.id));
                const availableRolesHtml = availableRoles.map(role => `
                    <div class="role-item">
                        <div class="role-info">
                            <h6>${role.display_name}</h6>
                            <p>${role.description || '暂无描述'}</p>
                        </div>
                        <button class="btn btn-sm btn-primary" onclick="UsersPage.assignRoleInEdit(${userId}, ${role.id})">
                            分配
                        </button>
                    </div>
                `).join('');
                document.getElementById('editAvailableRoles').innerHTML = availableRolesHtml || '<p style="color: var(--text-secondary); font-size: 12px;">暂无可分配角色</p>';
            }

        } catch (error) {
            console.error('加载角色信息失败:', error);
            document.getElementById('editCurrentRoles').innerHTML = '<p style="color: var(--error-color); font-size: 12px;">加载失败</p>';
            document.getElementById('editAvailableRoles').innerHTML = '<p style="color: var(--error-color); font-size: 12px;">加载失败</p>';
        }
    },

    // 刷新用户角色信息
    async refreshUserRoles() {
        const userId = document.getElementById('editUserId').value;
        if (userId) {
            await this.loadEditUserRoles(userId);
            AdminUtils.showToast('角色信息已刷新', 'success');
        }
    },

    // 在编辑对话框中分配角色
    async assignRoleInEdit(userId, roleId) {
        try {
            const data = await AdminUtils.request('/roles/assign', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: userId,
                    role_id: roleId
                })
            });

            if (data.success) {
                AdminUtils.showToast('角色分配成功', 'success');
                // 延迟一下，让Toast显示完成
                await new Promise(resolve => setTimeout(resolve, 100));

                try {
                    await this.loadEditUserRoles(userId); // 重新加载角色信息
                } catch (loadError) {
                    AdminUtils.showToast('角色信息更新失败，但分配成功', 'warning');
                }
            } else {
                AdminUtils.showToast(data.message || '角色分配失败', 'error');
            }
        } catch (error) {
            AdminUtils.showToast('角色分配失败', 'error');
        }
    },

    // 取消分配角色
    async removeRole(roleId, userId) {
        if (!confirm('确定要取消分配此角色吗？')) {
            return;
        }

        try {
            const data = await AdminUtils.request('/roles/unassign', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: userId,
                    role_id: roleId
                })
            });

            if (data.success) {
                AdminUtils.showToast('角色取消分配成功', 'success');
                // 延迟一下，让Toast显示完成
                await new Promise(resolve => setTimeout(resolve, 100));

                try {
                    await this.loadEditUserRoles(userId); // 重新加载角色信息
                } catch (loadError) {
                    AdminUtils.showToast('角色信息更新失败，但取消成功', 'warning');
                }
            } else {
                AdminUtils.showToast(data.message || '角色取消分配失败', 'error');
            }
        } catch (error) {
            AdminUtils.showToast('角色取消分配失败', 'error');
        }
    },

    // 编辑用户
    async editUser(userId) {
        console.log('📍 开始编辑用户，ID:', userId);
        try {
            // 直接从API获取用户最新数据
            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            console.log('📍 从API获取用户最新信息');

            // 直接使用单个用户API获取用户最新数据
            const userResponse = await fetch(ADMIN_CONFIG.API_BASE_URL + `/admin/users/${userId}`, {
                method: 'GET',
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
            });

            if (!userResponse.ok) {
                throw new Error(`获取用户信息失败: ${userResponse.status}`);
            }

            const userResult = await userResponse.json();
            const user = userResult.user || userResult;
            console.log('📍 获取到用户最新信息:', user);
            console.log('📍 用户类型详情:', user.user_type, typeof user.user_type);

            if (!user) {
                throw new Error('用户不存在');
            }

            // 填充编辑表单
            document.getElementById('editUserId').value = user.id;
            document.getElementById('editUsername').value = user.username;
            document.getElementById('editRealName').value = user.real_name;
            document.getElementById('editEmail').value = user.email;
            document.getElementById('editPhone').value = user.phone;

            // 设置用户类型 - 处理多选复选框
            console.log('📍 填充表单用户类型:', user.user_type);

            // 清空所有复选框
            const checkboxes = document.querySelectorAll('#editUserTypes input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = false);

            // 解析用户类型（支持字符串和数组格式）
            let userTypes = [];
            if (typeof user.user_type === 'string') {
                if (user.user_type.includes(',')) {
                    userTypes = user.user_type.split(',').map(t => t.trim());
                } else {
                    userTypes = [user.user_type];
                }
            } else if (Array.isArray(user.user_type)) {
                userTypes = user.user_type;
            }

            // 设置选中的复选框
            userTypes.forEach(type => {
                const checkbox = document.getElementById(`editType${type.charAt(0).toUpperCase() + type.slice(1)}`);
                if (checkbox) {
                    checkbox.checked = true;
                }
            });

            console.log('📍 设置的用户类型:', userTypes);
            console.log('📍 选中的复选框:', Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value));

            document.getElementById('editStatus').value = user.status;
            console.log('📍 状态设置:', user.status, '表单状态值:', document.getElementById('editStatus').value);

            // 填充可选字段
            document.getElementById('editStudentId').value = user.student_id || '';
            document.getElementById('editEmployeeId').value = user.employee_id || '';
            document.getElementById('editClassId').value = user.class_id || '';
            document.getElementById('editGrade').value = user.grade || '';
            document.getElementById('editIsClassTeacher').checked = user.is_class_teacher || false;

            // 清空密码字段
            document.getElementById('editPassword').value = '';

            // 设置拜访权限
            const editIsVisitable = document.getElementById('editIsVisitable');
            if (editIsVisitable) {
                editIsVisitable.checked = user.is_visitable || false;
            }

            // 根据用户类型显示相应字段
            this.updateEditUserFieldsVisibility(user.user_type);

            // 移除标志，允许change事件处理器执行
            setTimeout(() => {
                // 不再需要userTypeElement，因为我们使用复选框
                console.log('📍 用户类型设置完成，change事件已启用');
            }, 100);

            // 显示编辑模态框
            this.showEditUserModal();

        } catch (error) {
            console.error('❌ 编辑用户失败:', error);
            AdminUtils.showToast('编辑用户失败: ' + error.message, 'error');
        }
    },

    // 显示编辑用户模态框
    showEditUserModal() {
        const modal = document.getElementById('editUserModal');
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
            modal.style.visibility = 'visible';
            modal.style.opacity = '1';
            document.body.style.overflow = 'hidden';

            // 绑定用户类型变化事件
            this.bindEditUserTypeChange();
        }
    },

    // 隐藏编辑用户模态框
    hideEditUserModal() {
        const modal = document.getElementById('editUserModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.style.visibility = 'hidden';
            modal.style.opacity = '0';
        }
        document.body.style.overflow = '';
    },

    // 绑定编辑用户模态框的用户类型变化事件
    bindEditUserTypeChange() {
        const editUserTypeSelect = document.getElementById('editUserType');
        if (!editUserTypeSelect) return;

        // 移除旧的事件监听器
        const newSelect = editUserTypeSelect.cloneNode(true);
        editUserTypeSelect.parentNode.replaceChild(newSelect, editUserTypeSelect);

        // 添加新的事件监听器
        newSelect.addEventListener('change', () => {
            const userType = newSelect.value;
            this.updateEditUserFieldsVisibility(userType);
        });

        // 初始化字段可见性
        this.updateEditUserFieldsVisibility(newSelect.value);
    },

    // 更新编辑用户字段的可见性
    updateEditUserFieldsVisibility(userType) {
        const editStudentIdGroup = document.getElementById('editStudentIdGroup');
        const editEmployeeIdGroup = document.getElementById('editEmployeeIdGroup');
        const editClassIdGroup = document.getElementById('editClassIdGroup');
        const editGradeGroup = document.getElementById('editGradeGroup');
        const editIsClassTeacherGroup = document.getElementById('editIsClassTeacherGroup');

        // 隐藏所有可选字段
        if (editStudentIdGroup) editStudentIdGroup.style.display = 'none';
        if (editEmployeeIdGroup) editEmployeeIdGroup.style.display = 'none';
        if (editClassIdGroup) editClassIdGroup.style.display = 'none';
        if (editGradeGroup) editGradeGroup.style.display = 'none';
        if (editIsClassTeacherGroup) editIsClassTeacherGroup.style.display = 'none';

        // 根据用户类型显示相应字段
        switch (userType) {
            case 'student':
                if (editStudentIdGroup) editStudentIdGroup.style.display = 'block';
                if (editClassIdGroup) editClassIdGroup.style.display = 'block';
                if (editGradeGroup) editGradeGroup.style.display = 'block';
                break;
            case 'teacher':
                if (editEmployeeIdGroup) editEmployeeIdGroup.style.display = 'block';
                if (editClassIdGroup) editClassIdGroup.style.display = 'block';
                if (editIsClassTeacherGroup) editIsClassTeacherGroup.style.display = 'block';
                break;
            case 'parent':
                break;
            case 'alumni':
                if (editStudentIdGroup) editStudentIdGroup.style.display = 'block';
                break;
            case 'security':
                if (editEmployeeIdGroup) editEmployeeIdGroup.style.display = 'block';
                break;
            case 'admin':
                if (editEmployeeIdGroup) editEmployeeIdGroup.style.display = 'block';
                break;
        }
    },

    // 保存编辑的用户信息
    async saveEditUser() {
        console.log('📍 开始保存编辑的用户信息');
        try {
            const userId = document.getElementById('editUserId').value;

            // 获取选中的用户类型
            const selectedTypes = [];
            const checkboxes = document.querySelectorAll('#editUserTypes input[type="checkbox"]:checked');
            checkboxes.forEach(cb => selectedTypes.push(cb.value));
            const userTypeValue = selectedTypes.length > 0 ? selectedTypes.join(',') : 'teacher';

            console.log('📍 选中的用户类型复选框:', selectedTypes);
            console.log('📍 最终用户类型值:', userTypeValue);

            // 获取密码字段（如果填写了的话）
            const password = document.getElementById('editPassword')?.value?.trim();

            const formData = {
                username: document.getElementById('editUsername')?.value?.trim(),
                real_name: document.getElementById('editRealName')?.value?.trim(),
                email: document.getElementById('editEmail')?.value?.trim(),
                phone: document.getElementById('editPhone')?.value?.trim(),
                user_type: userTypeValue,
                status: document.getElementById('editStatus')?.value || 'active',
                student_id: document.getElementById('editStudentId')?.value?.trim(),
                employee_id: document.getElementById('editEmployeeId')?.value?.trim(),
                class_id: document.getElementById('editClassId')?.value?.trim(),
                grade: document.getElementById('editGrade')?.value?.trim(),
                is_class_teacher: document.getElementById('editIsClassTeacher')?.checked,
                is_visitable: document.getElementById('editIsVisitable')?.checked
            };

            // 只有当密码不为空时才添加到formData中
            if (password) {
                formData.password = password;
            }

            console.log('📍 编辑的用户数据:', formData);

            // 验证必填字段
            const requiredFields = ['username', 'real_name', 'email'];
            for (const field of requiredFields) {
                if (!formData[field]) {
                    AdminUtils.showToast(`请填写${this.getFieldName(field)}`, 'error');
                    return;
                }
            }

            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            const response = await fetch(ADMIN_CONFIG.API_BASE_URL + `/admin/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `更新用户失败 (${response.status})`);
            }

            const data = await response.json();
            console.log('📍 更新响应:', data);

            if (data.message) {
                AdminUtils.showToast('用户信息更新成功', 'success');
                this.hideEditUserModal();
                this.loadUsers(); // 重新加载用户列表
            } else {
                AdminUtils.showToast('用户信息更新失败: ' + (data.error || '未知错误'), 'error');
            }

        } catch (error) {
            console.error('❌ 保存编辑用户失败:', error);
            AdminUtils.showToast('保存编辑用户失败: ' + error.message, 'error');
        }
    },

    // 删除用户
    async deleteUser(userId, username) {
        console.log('📍 开始删除用户，ID:', userId, '用户名:', username);

        // 确认删除
        if (!confirm(`确定要删除用户 "${username}" 吗？此操作不可恢复。`)) {
            return;
        }

        try {
            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            const response = await fetch(ADMIN_CONFIG.API_BASE_URL + `/admin/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `删除用户失败 (${response.status})`);
            }

            const data = await response.json();
            console.log('📍 删除响应:', data);

            if (data.message) {
                AdminUtils.showToast('用户删除成功', 'success');
                this.loadUsers(); // 重新加载用户列表
            } else {
                AdminUtils.showToast('用户删除失败: ' + (data.error || '未知错误'), 'error');
            }

        } catch (error) {
            console.error('❌ 删除用户失败:', error);
            AdminUtils.showToast('删除用户失败: ' + error.message, 'error');
        }
    },

    // 批量删除用户
    async batchDeleteUsers() {
        console.log('📍 开始批量删除用户');

        const userIds = this.getSelectedUserIds();
        if (userIds.length === 0) {
            AdminUtils.showToast('请先选择要删除的用户', 'warning');
            return;
        }

        if (!confirm(`确定要删除选中的 ${userIds.length} 个用户吗？此操作不可恢复。`)) {
            return;
        }

        try {
            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            const response = await fetch(ADMIN_CONFIG.API_BASE_URL + '/admin/users/batch-delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify({ user_ids: userIds })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `批量删除失败 (${response.status})`);
            }

            const data = await response.json();
            console.log('📍 批量删除响应:', data);

            if (data.message) {
                AdminUtils.showToast(`成功删除 ${userIds.length} 个用户`, 'success');
                this.loadUsers(); // 重新加载用户列表
            } else {
                AdminUtils.showToast('批量删除失败: ' + (data.error || '未知错误'), 'error');
            }

        } catch (error) {
            console.error('❌ 批量删除用户失败:', error);
            AdminUtils.showToast('批量删除失败: ' + error.message, 'error');
        }
    },

    // 切换用户状态
    async toggleStatus(userId, currentStatus) {
        console.log('📍 切换用户状态，ID:', userId, '当前状态:', currentStatus);

        const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
        const actionText = newStatus === 'active' ? '启用' : '禁用';

        if (!confirm(`确定要${actionText}该用户吗？`)) {
            return;
        }

        try {
            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            const response = await fetch(ADMIN_CONFIG.API_BASE_URL + `/admin/users/${userId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify({ status: newStatus })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `${actionText}用户失败 (${response.status})`);
            }

            const data = await response.json();
            console.log('📍 状态切换响应:', data);

            if (data.message) {
                AdminUtils.showToast(`用户${actionText}成功`, 'success');
                this.loadUsers(); // 重新加载用户列表
            } else {
                AdminUtils.showToast(`${actionText}用户失败: ` + (data.error || '未知错误'), 'error');
            }

        } catch (error) {
            console.error('❌ 切换用户状态失败:', error);
            AdminUtils.showToast(`${actionText}用户失败: ` + error.message, 'error');
        }
    },

    // 切换教师可访问状态
    async toggleVisitable(userId, isVisitable) {
        console.log('📍 切换教师可访问状态，ID:', userId, '新状态:', isVisitable);

        try {
            const token = AdminState.token || localStorage.getItem('admin_token');
            if (!token) {
                AdminUtils.showToast('未找到认证token，请重新登录', 'error');
                return;
            }

            const response = await fetch(ADMIN_CONFIG.API_BASE_URL + `/admin/users/${userId}/visitable`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify({ is_visitable: isVisitable })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `更新访问权限失败 (${response.status})`);
            }

            const data = await response.json();
            console.log('📍 访问权限更新响应:', data);

            if (data.message) {
                AdminUtils.showToast('访问权限更新成功', 'success');
                this.loadUsers(); // 重新加载用户列表
            } else {
                AdminUtils.showToast('访问权限更新失败: ' + (data.error || '未知错误'), 'error');
            }

        } catch (error) {
            console.error('❌ 切换访问权限失败:', error);
            AdminUtils.showToast('切换访问权限失败: ' + error.message, 'error');
        }
    },

    // 初始化事件监听器
    initEventListeners() {
        console.log('🔧 UsersPage.initEventListeners() 初始化用户管理页面事件监听器');

        // 添加用户按钮
        const addUserBtn = document.getElementById('addUserBtn');
        if (addUserBtn) {
            addUserBtn.addEventListener('click', () => {
                console.log('🚀 点击添加用户按钮');
                this.showAddUserModal();
            });
            console.log('✅ 添加用户按钮事件监听器已绑定');
        } else {
            console.log('❌ 找不到添加用户按钮');
        }

        // 批量删除按钮
        const batchDeleteBtn = document.getElementById('batchDeleteBtn');
        if (batchDeleteBtn) {
            batchDeleteBtn.addEventListener('click', () => {
                console.log('🚀 点击批量删除按钮');
                this.batchDeleteUsers();
            });
            console.log('✅ 批量删除按钮事件监听器已绑定');
        } else {
            console.log('❌ 找不到批量删除按钮');
        }

        // 编辑用户表单提交
        const editUserForm = document.getElementById('editUserForm');
        if (editUserForm) {
            editUserForm.addEventListener('submit', (e) => {
                e.preventDefault();
                console.log('🚀 提交编辑用户表单');
                this.saveEditUser();
            });
            console.log('✅ 编辑用户表单提交事件监听器已绑定');
        } else {
            console.log('❌ 找不到编辑用户表单');
        }

        // 编辑用户类型变化事件 - 绑定到复选框
        const editUserTypesContainer = document.getElementById('editUserTypes');
        if (editUserTypesContainer) {
            editUserTypesContainer.addEventListener('change', (e) => {
                if (e.target.type === 'checkbox') {
                    console.log('🚀 编辑用户类型变化:', e.target.value, e.target.checked);

                    // 获取当前选中的所有用户类型
                    const selectedTypes = [];
                    const checkboxes = editUserTypesContainer.querySelectorAll('input[type="checkbox"]:checked');
                    checkboxes.forEach(cb => selectedTypes.push(cb.value));

                    this.updateEditUserFieldsVisibility(selectedTypes.join(','));
                }
            });
            console.log('✅ 编辑用户类型复选框变化事件监听器已绑定');
        } else {
            console.log('❌ 找不到编辑用户类型复选框容器');
        }

        // 编辑密码强度检查
        const editPassword = document.getElementById('editPassword');
        if (editPassword) {
            editPassword.addEventListener('input', () => {
                this.checkPasswordStrength('editPassword', 'editPassword-strength-fill', 'editPassword-strength-text');
            });
            console.log('✅ 编辑密码强度检查事件监听器已绑定');
        } else {
            console.log('❌ 找不到编辑密码输入框');
        }

        console.log('✅ UsersPage 事件监听器初始化完成');
    },

    // 更新编辑用户字段可见性
    updateEditUserFieldsVisibility(userTypeString) {
        console.log('🚀 更新编辑用户字段可见性:', userTypeString);

        // 解析用户类型字符串，支持多类型
        let userTypes = [];
        if (typeof userTypeString === 'string') {
            if (userTypeString.includes(',')) {
                userTypes = userTypeString.split(',').map(t => t.trim());
            } else if (userTypeString) {
                userTypes = [userTypeString];
            }
        } else if (Array.isArray(userTypeString)) {
            userTypes = userTypeString;
        }

        console.log('📍 解析的用户类型:', userTypes);

        // 安全地获取和隐藏所有角色特定字段
        const fields = [
            'editStudentIdGroup',
            'editEmployeeIdGroup',
            'editClassIdGroup',
            'editGradeGroup',
            'editIsClassTeacherGroup'
        ];

        // 隐藏所有可选字段
        fields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                element.style.display = 'none';
            }
        });

        // 根据用户类型显示相应字段 - 支持多用户类型
        userTypes.forEach(userType => {
            switch (userType) {
                case 'student':
                    this.showField('editStudentIdGroup');
                    this.showField('editClassIdGroup');
                    this.showField('editGradeGroup');
                    break;
                case 'teacher':
                    this.showField('editEmployeeIdGroup');
                    this.showField('editClassIdGroup');
                    this.showField('editGradeGroup');
                    this.showField('editIsClassTeacherGroup');
                    break;
                case 'alumni':
                    this.showField('editStudentIdGroup');
                    this.showField('editClassIdGroup');
                    this.showField('editGradeGroup');
                    break;
            }
        });
    },

    // 辅助方法：安全显示字段
    showField(fieldId) {
        const element = document.getElementById(fieldId);
        if (element) {
            element.style.display = 'block';
        } else {
            console.warn(`⚠️ 字段元素不存在: ${fieldId}`);
        }
    }
  };


// 访问申请页面
const VisitApplicationsPage = {
    currentPage: 1,
    currentStatus: '',
    filters: {
        search: '',
        status: '',
        start_date: '',
        end_date: ''
    },
    selectedApplications: new Set(),

    async load() {
        this.bindEvents();
        await this.loadApplications();
    },

    bindEvents() {
        // 搜索输入
        const searchInput = document.getElementById('visitSearch');
        if (searchInput) {
            searchInput.addEventListener('input', AdminUtils.debounce(() => {
                this.filters.search = searchInput.value;
                this.currentPage = 1;
                this.loadApplications();
            }, 500));
        }

        // 状态筛选
        const statusFilter = document.getElementById('visitStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                this.filters.status = statusFilter.value;
                this.currentPage = 1;
                this.loadApplications();
            });
        }

        // 日期筛选
        const startDate = document.getElementById('visitStartDate');
        const endDate = document.getElementById('visitEndDate');
        if (startDate) {
            startDate.addEventListener('change', () => {
                this.filters.start_date = startDate.value;
                this.currentPage = 1;
                this.loadApplications();
            });
        }
        if (endDate) {
            endDate.addEventListener('change', () => {
                this.filters.end_date = endDate.value;
                this.currentPage = 1;
                this.loadApplications();
            });
        }

        // 刷新按钮
        const refreshBtn = document.getElementById('refreshVisitList');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadApplications();
            });
        }

        // 导入第三方数据按钮
        const importBtn = document.getElementById('importExternalData');
        if (importBtn) {
            importBtn.addEventListener('click', () => {
                this.showImportModal();
            });
        }

        // 批量审核按钮
        const batchApproveBtn = document.getElementById('batchApproveBtn');
        if (batchApproveBtn) {
            batchApproveBtn.addEventListener('click', () => {
                this.showBatchApproveModal();
            });
        }

        // 导出数据按钮
        const exportBtn = document.getElementById('exportVisitData');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportData();
            });
        }

        // 校历导入相关按钮
        document.getElementById('importEventsBtn')?.addEventListener('click', () => {
            CalendarPage.showImportModal();
        });

        document.getElementById('downloadTemplateBtn')?.addEventListener('click', () => {
            CalendarPage.downloadTemplate();
        });

        // 全选复选框
        const selectAllCheckbox = document.getElementById('selectAllVisits');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                this.selectAll(e.target.checked);
            });
        }
    },

    async loadApplications() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: 20,
                ...this.filters
            });

            // 分别加载访问申请和学生出校申请，处理可能的错误
            let visitData = { applications: [], statistics: {}, pagination: { total: 0 } };
            let studentExitData = { applications: [], statistics: {}, pagination: { total: 0 } };

            try {
                visitData = await AdminUtils.request(`/visits/applications?${params}`);
            } catch (error) {
                console.error('加载访问申请失败:', error);
                AdminUtils.showToast('加载访问申请失败', 'warning');
            }

            try {
                studentExitData = await AdminUtils.request(`/student-exit/applications?${params}`);
            } catch (error) {
                console.error('加载学生出校申请失败:', error);
                // 如果只是功能不存在，不显示错误提示
                if (error.message && error.message.includes('404')) {
                    console.log('学生出校申请功能未启用');
                } else {
                    AdminUtils.showToast('加载学生出校申请失败', 'warning');
                }
            }

            // 合并两种申请数据
            const allApplications = [
                ...visitData.applications.map(app => ({...app, application_type: 'visit'})),
                ...studentExitData.applications.map(app => ({...app, application_type: 'student_exit'}))
            ];

            // 合并统计数据
            const combinedStatistics = {
                pending: (visitData.statistics?.pending || 0) + (studentExitData.statistics?.pending || 0),
                approved: (visitData.statistics?.approved || 0) + (studentExitData.statistics?.approved || 0),
                rejected: (visitData.statistics?.rejected || 0) + (studentExitData.statistics?.rejected || 0),
                completed: (visitData.statistics?.completed || 0) + (studentExitData.statistics?.completed || 0)
            };

            // 合并分页信息
            const combinedPagination = {
                page: this.currentPage,
                per_page: 20,
                total: (visitData.pagination?.total || 0) + (studentExitData.pagination?.total || 0),
                pages: Math.ceil(((visitData.pagination?.total || 0) + (studentExitData.pagination?.total || 0)) / 20)
            };

            this.updateStatistics(combinedStatistics);
            this.renderApplicationsTable(allApplications);
            this.renderPagination(combinedPagination);
            this.updateTotalCount(combinedPagination.total);

            // 如果两个API都失败了
            if (visitData.applications.length === 0 && studentExitData.applications.length === 0) {
                AdminUtils.showToast('暂无申请数据', 'info');
            }
        } catch (error) {
            console.error('加载申请失败:', error);
            AdminUtils.showToast('加载申请失败', 'error');
        }
    },

    updateStatistics(stats) {
        document.getElementById('visitPendingCount').textContent = stats.pending || 0;
        document.getElementById('visitApprovedCount').textContent = stats.approved || 0;
        document.getElementById('visitRejectedCount').textContent = stats.rejected || 0;
        document.getElementById('visitCompletedCount').textContent = stats.completed || 0;
    },

    updateTotalCount(total) {
        document.getElementById('visitTotalCount').textContent = `共 ${total} 条记录`;
    },

    renderApplicationsTable(applications) {
        const tbody = document.getElementById('visitApplicationsTableBody');

        if (applications.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" class="text-center text-secondary">暂无数据</td></tr>';
            return;
        }

        tbody.innerHTML = applications.map(app => {
            // 根据申请类型显示不同的信息
            if (app.application_type === 'student_exit') {
                // 学生出校申请
                return `
                    <tr>
                        <td>
                            <input type="checkbox"
                                   class="application-checkbox"
                                   data-id="${app.id}"
                                   data-type="student_exit"
                                   ${this.selectedApplications.has(`${app.id}_student_exit`) ? 'checked' : ''}
                                   onchange="VisitApplicationsPage.toggleSelection(${app.id}, this.checked, 'student_exit')">
                        </td>
                        <td>
                            <div class="user-info">
                                <div class="user-name">${app.student ? app.student.real_name : '未知学生'}</div>
                                <div class="user-type">学生出校申请</div>
                                <div class="user-class">${app.student ? app.student.class_name : '无班级信息'}</div>
                                <div class="applicant-info">申请人: ${app.applicant ? app.applicant.real_name : '未知'} (${app.applicant ? app.applicant.user_type : ''})</div>
                            </div>
                        </td>
                        <td>${AdminUtils.formatDate(app.exit_date)}</td>
                        <td>${AdminUtils.formatTime(app.exit_time_start)} - ${AdminUtils.formatTime(app.exit_time_end)}</td>
                        <td>
                            <div class="purpose-cell">
                                <div class="purpose-text">${app.exit_reason}</div>
                                ${app.remarks ? `<div class="remarks-text">${app.remarks}</div>` : ''}
                            </div>
                        </td>
                        <td>-</td>
                        <td>
                            <span class="text-muted">学生出校</span>
                        </td>
                        <td>${AdminUtils.formatDateTime(app.created_at)}</td>
                        <td>
                            <div class="review-actions">
                                <div class="status-row">
                                    <span class="status-badge ${app.application_status}">
                                        ${this.getStudentExitStatusText(app.application_status)}
                                    </span>
                                </div>
                                <div class="approver-info">审核人：${this.getApproverName(app)}</div>
                                <div class="action-buttons">
                                    ${this.renderStudentExitActionButtons(app)}
                                </div>
                            </div>
                        </td>
                    </tr>
                `;
            } else {
                // 访问申请（原有逻辑）
                return `
                    <tr>
                        <td>
                            <input type="checkbox"
                                   class="application-checkbox"
                                   data-id="${app.id}"
                                   data-type="visit"
                                   ${this.selectedApplications.has(`${app.id}_visit`) ? 'checked' : ''}
                                   onchange="VisitApplicationsPage.toggleSelection(${app.id}, this.checked, 'visit')">
                        </td>
                        <td>
                            <div class="user-info">
                                <div class="user-name">${app.user ? app.user.real_name : '未知用户'}</div>
                                <div class="user-type">访问申请</div>
                                <div class="user-phone">${app.user ? app.user.phone : '无'}</div>
                                <div class="user-email">${app.user ? app.user.email : '无'}</div>
                                ${app.alumni_profile ? `<div class="user-alumni">${app.alumni_profile.division} - ${app.alumni_profile.class_name}</div>` : ''}
                            </div>
                        </td>
                        <td>${AdminUtils.formatDate(app.visit_date)}</td>
                        <td>${AdminUtils.formatTime(app.time_start)} - ${AdminUtils.formatTime(app.time_end)}</td>
                        <td>
                            <div class="purpose-cell">
                                <div class="purpose-text">${app.visit_purpose}</div>
                                ${app.remarks ? `<div class="remarks-text">${app.remarks}</div>` : ''}
                            </div>
                        </td>
                        <td>${app.interviewee || '-'}</td>
                        <td>
                            ${app.vehicle ? `
                                <div class="vehicle-info">
                                    <div class="vehicle-plate">${app.vehicle.plate_number}</div>
                                    <div class="vehicle-model">${app.vehicle.brand} ${app.vehicle.model}</div>
                                </div>
                            ` : '<span class="text-muted">无车辆</span>'}
                        </td>
                        <td>${AdminUtils.formatDateTime(app.created_at)}</td>
                        <td>
                            <div class="review-actions">
                                <div class="status-row">
                                    <span class="status-badge ${app.status}">
                                        ${AdminUtils.getStatusText(app.status)}
                                    </span>
                                </div>
                                <div class="approver-info">审核人：${app.approver_name || '-'}</div>
                                <div class="action-buttons">
                                    ${this.renderActionButtons(app)}
                                </div>
                            </div>
                        </td>
                    </tr>
                `;
            }
        }).join('');

        // 更新全选状态
        this.updateSelectAllState();
    },

    renderActionButtons(application) {
        switch (application.status) {
            case 'pending':
                return `
                    <button class="btn btn-sm btn-success" onclick="VisitApplicationsPage.approve(${application.id})" title="通过">
                        <i class="ri-check-line"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="VisitApplicationsPage.reject(${application.id})" title="拒绝">
                        <i class="ri-close-line"></i>
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="VisitApplicationsPage.viewDetails(${application.id})" title="查看详情">
                        <i class="ri-eye-line"></i>
                    </button>
                `;
            case 'approved':
                return `
                    <button class="btn btn-sm btn-warning" onclick="VisitApplicationsPage.cancel(${application.id})" title="取消">
                        <i class="ri-close-line"></i>
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="VisitApplicationsPage.viewDetails(${application.id})" title="查看详情">
                        <i class="ri-eye-line"></i>
                    </button>
                `;
            case 'rejected':
                return `
                    <button class="btn btn-sm btn-success" onclick="VisitApplicationsPage.reapprove(${application.id})" title="重新审核">
                        <i class="ri-refresh-line"></i>
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="VisitApplicationsPage.viewDetails(${application.id})" title="查看详情">
                        <i class="ri-eye-line"></i>
                    </button>
                `;
            default:
                return `
                    <button class="btn btn-sm btn-outline" onclick="VisitApplicationsPage.viewDetails(${application.id})" title="查看详情">
                        <i class="ri-eye-line"></i>
                    </button>
                `;
        }
    },

    renderPagination(pagination) {
        const container = document.getElementById('visitApplicationsPagination');
        let html = '';

        // 上一页
        html += `<button ${pagination.has_prev ? '' : 'disabled'} onclick="VisitApplicationsPage.goToPage(${pagination.page - 1})">上一页</button>`;

        // 页码
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);

        if (startPage > 1) {
            html += `<button onclick="VisitApplicationsPage.goToPage(1)">1</button>`;
            if (startPage > 2) html += `<span>...</span>`;
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === pagination.page ? 'active' : ''}" onclick="VisitApplicationsPage.goToPage(${i})">${i}</button>`;
        }

        if (endPage < pagination.pages) {
            if (endPage < pagination.pages - 1) html += `<span>...</span>`;
            html += `<button onclick="VisitApplicationsPage.goToPage(${pagination.pages})">${pagination.pages}</button>`;
        }

        // 下一页
        html += `<button ${pagination.has_next ? '' : 'disabled'} onclick="VisitApplicationsPage.goToPage(${pagination.page + 1})">下一页</button>`;

        container.innerHTML = html;
    },

    toggleSelection(appId, checked, type = 'visit') {
        const key = `${appId}_${type}`;
        if (checked) {
            this.selectedApplications.add(key);
        } else {
            this.selectedApplications.delete(key);
        }
        this.updateBatchActionButton();
    },

    selectAll(checked) {
        const checkboxes = document.querySelectorAll('.application-checkbox');
        checkboxes.forEach(checkbox => {
            const appId = parseInt(checkbox.dataset.id);
            checkbox.checked = checked;
            if (checked) {
                this.selectedApplications.add(appId);
            } else {
                this.selectedApplications.delete(appId);
            }
        });
        this.updateBatchActionButton();
    },

    updateSelectAllState() {
        const selectAllCheckbox = document.getElementById('selectAllVisits');
        const checkboxes = document.querySelectorAll('.application-checkbox');
        const checkedBoxes = document.querySelectorAll('.application-checkbox:checked');

        if (checkboxes.length === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (checkedBoxes.length === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (checkedBoxes.length === checkboxes.length) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
            selectAllCheckbox.checked = false;
        }
    },

    updateBatchActionButton() {
        const batchBtn = document.getElementById('batchApproveBtn');
        if (this.selectedApplications.size > 0) {
            batchBtn.innerHTML = `<i class="ri-check-double-line"></i> 批量审核 (${this.selectedApplications.size})`;
            batchBtn.disabled = false;
        } else {
            batchBtn.innerHTML = '<i class="ri-check-double-line"></i> 批量审核';
            batchBtn.disabled = true;
        }
    },

    async approve(applicationId) {
        AdminUtils.showConfirm('确定要通过这个访问申请吗？', async () => {
            try {
                await AdminUtils.request(`/visits/applications/${applicationId}/approve`, {
                    method: 'POST',
                    body: JSON.stringify({ approve: true })
                });

                AdminUtils.showToast('访问申请已通过', 'success');
                this.loadApplications();
            } catch (error) {
                AdminUtils.showToast('审核操作失败', 'error');
            }
        });
    },

    async reject(applicationId) {
        AdminUtils.showConfirm('确定要拒绝这个访问申请吗？', async () => {
            try {
                await AdminUtils.request(`/visits/applications/${applicationId}/approve`, {
                    method: 'POST',
                    body: JSON.stringify({ approve: false })
                });

                AdminUtils.showToast('访问申请已拒绝', 'success');
                this.loadApplications();
            } catch (error) {
                AdminUtils.showToast('审核操作失败', 'error');
            }
        });
    },

    async cancel(applicationId) {
        AdminUtils.showConfirm('确定要取消这个访问申请吗？', async () => {
            try {
                await AdminUtils.request(`/visits/applications/${applicationId}/cancel`, {
                    method: 'POST'
                });

                AdminUtils.showToast('访问申请已取消', 'success');
                this.loadApplications();
            } catch (error) {
                AdminUtils.showToast('取消操作失败', 'error');
            }
        });
    },

    async reapprove(applicationId) {
        AdminUtils.showConfirm('确定要重新审核这个访问申请吗？', async () => {
            try {
                await AdminUtils.request(`/visits/applications/${applicationId}/approve`, {
                    method: 'POST',
                    body: JSON.stringify({ approve: true })
                });

                AdminUtils.showToast('访问申请重新审核成功', 'success');
                this.loadApplications();
            } catch (error) {
                AdminUtils.showToast('重新审核失败', 'error');
            }
        });
    },

    async viewDetails(applicationId) {
        try {
            const data = await AdminUtils.request(`/visits/applications/${applicationId}`);
            const application = data.data;

            const modalHtml = `
                <div class="modal" id="visitApplicationDetailModal">
                    <div class="modal-content large">
                        <div class="modal-header">
                            <h3>访问申请详情</h3>
                            <button class="modal-close" onclick="VisitApplicationsPage.closeDetailModal()">
                                <i class="ri-close-line"></i>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="application-detail">
                                <div class="detail-section">
                                    <h4>申请人信息</h4>
                                    <div class="detail-grid">
                                        <div class="detail-item">
                                            <label>姓名：</label>
                                            <span>${application.user ? application.user.real_name : '未知用户'}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>电话：</label>
                                            <span>${application.user ? application.user.phone : '无'}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>邮箱：</label>
                                            <span>${application.user ? application.user.email : '无'}</span>
                                        </div>
                                        ${application.alumni_profile ? `
                                        <div class="detail-item">
                                            <label>院系班级：</label>
                                            <span>${application.alumni_profile.division} - ${application.alumni_profile.class_name}</span>
                                        </div>
                                        ` : ''}
                                    </div>
                                </div>

                                <div class="detail-section">
                                    <h4>访问信息</h4>
                                    <div class="detail-grid">
                                        <div class="detail-item">
                                            <label>访问日期：</label>
                                            <span>${AdminUtils.formatDate(application.visit_date)}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>访问时间：</label>
                                            <span>${AdminUtils.formatTime(application.time_start)} - ${AdminUtils.formatTime(application.time_end)}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>访问事由：</label>
                                            <span>${application.visit_purpose}</span>
                                        </div>
                                        <div class="detail-item full-width">
                                            <label>申请状态：</label>
                                            <span class="status-badge ${application.application_status}">
                                                ${AdminUtils.getStatusText(application.application_status)}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                ${application.vehicle ? `
                                <div class="detail-section">
                                    <h4>车辆信息</h4>
                                    <div class="detail-grid">
                                        <div class="detail-item">
                                            <label>车牌号：</label>
                                            <span>${application.vehicle.plate_number}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>车辆类型：</label>
                                            <span>${application.vehicle.vehicle_type}</span>
                                        </div>
                                    </div>
                                </div>
                                ` : ''}

                                ${application.remarks ? `
                                <div class="detail-section">
                                    <h4>备注信息</h4>
                                    <p>${application.remarks}</p>
                                </div>
                                ` : ''}

                                <div class="detail-section">
                                    <h4>申请信息</h4>
                                    <div class="detail-grid">
                                        <div class="detail-item">
                                            <label>申请时间：</label>
                                            <span>${AdminUtils.formatDateTime(application.created_at)}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>申请ID：</label>
                                            <span>${application.id}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-outline" onclick="VisitApplicationsPage.closeDetailModal()">关闭</button>
                            ${application.application_status === 'pending' ? `
                                <button class="btn btn-success" onclick="VisitApplicationsPage.approve(${application.id})">
                                    <i class="ri-check-line"></i>
                                    通过申请
                                </button>
                                <button class="btn btn-danger" onclick="VisitApplicationsPage.reject(${application.id})">
                                    <i class="ri-close-line"></i>
                                    拒绝申请
                                </button>
                            ` : ''}
                            ${application.application_status === 'approved' ? `
                                <button class="btn btn-warning" onclick="VisitApplicationsPage.cancel(${application.id})">
                                    <i class="ri-close-line"></i>
                                    取消申请
                                </button>
                            ` : ''}
                            ${application.application_status === 'rejected' ? `
                                <button class="btn btn-success" onclick="VisitApplicationsPage.reapprove(${application.id})">
                                    <i class="ri-refresh-line"></i>
                                    重新审核
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;

            // 移除现有模态框
            const existingModal = document.getElementById('visitApplicationDetailModal');
            if (existingModal) {
                existingModal.remove();
            }

            // 添加新模态框
            document.body.insertAdjacentHTML('beforeend', modalHtml);

            // 显示模态框
            const modal = document.getElementById('visitApplicationDetailModal');
            if (modal) {
                // 添加active类来显示模态框
                modal.classList.add('active');
            }

        } catch (error) {
            console.error('Error loading application details:', error);
            AdminUtils.showToast('加载申请详情失败', 'error');
        }
    },

    closeDetailModal() {
        const modal = document.getElementById('visitApplicationDetailModal');
        if (modal) {
            modal.classList.remove('active');
        }
    },

    filterByStatus(status) {
        this.filters.status = status;
        this.currentPage = 1;

        // 更新筛选器状态
        document.getElementById('visitStatusFilter').value = status;

        this.loadApplications();
    },

    goToPage(page) {
        this.currentPage = page;
        this.loadApplications();
    },

    showImportModal() {
        AdminUtils.showConfirm('确定要从第三方系统导入数据吗？此操作将同步外部数据到当前系统。', async () => {
            try {
                // TODO: Implement import-external endpoint in visits blueprint
                AdminUtils.showToast('导入功能暂未实现', 'warning');
                return;
            } catch (error) {
                AdminUtils.showToast('导入失败', 'error');
            }
        });
    },

    showBatchApproveModal() {
        if (this.selectedApplications.size === 0) {
            AdminUtils.showToast('请先选择要批量操作的申请', 'warning');
            return;
        }

        AdminUtils.showConfirm(`确定要批量审核选中的 ${this.selectedApplications.size} 个申请吗？`, async () => {
            try {
                const data = await AdminUtils.request('/visits/batch-approve', {
                    method: 'POST',
                    body: JSON.stringify({
                        application_ids: Array.from(this.selectedApplications),
                        approve: true
                    })
                });

                AdminUtils.showToast(`成功批量审核 ${data.processed_count} 个申请`, 'success');
                this.selectedApplications.clear();
                this.loadApplications();
            } catch (error) {
                AdminUtils.showToast('批量审核失败', 'error');
            }
        });
    },

    async exportData() {
        try {
            const params = new URLSearchParams({
                ...this.filters,
                export: 'csv'
            });

            // TODO: Implement applications export or redirect to records export
            AdminUtils.showToast('导出功能暂未实现', 'warning');
            return;
        } catch (error) {
            AdminUtils.showToast('数据导出失败', 'error');
        }
    },

    // 学生出校申请相关辅助函数
    getStudentExitStatusText(status) {
        const statusMap = {
            'pending': '待审批',
            'parent_approved': '家长通过',
            'teacher_approved': '老师通过',
            'approved': '已通过',
            'rejected': '已拒绝',
            'completed': '已完成',
            'cancelled': '已取消'
        };
        return statusMap[status] || status;
    },

    getApproverName(app) {
        if (app.application_type === 'student_exit') {
            // 学生出校申请的审批人
            if (app.parent_approved_by && app.teacher_approved_by) {
                return '家长、老师已审批';
            } else if (app.parent_approved_by) {
                return '家长已审批';
            } else if (app.teacher_approved_by) {
                return '老师已审批';
            }
            return '-';
        } else {
            // 访问申请的审批人
            return app.approver_name || '-';
        }
    },

    renderStudentExitActionButtons(app) {
        switch (app.application_status) {
            case 'pending':
            case 'parent_approved':
            case 'teacher_approved':
                return `
                    <button class="btn btn-sm btn-success" onclick="VisitApplicationsPage.approveStudentExit(${app.id})" title="通过">
                        <i class="ri-check-line"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="VisitApplicationsPage.rejectStudentExit(${app.id})" title="拒绝">
                        <i class="ri-close-line"></i>
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="VisitApplicationsPage.viewStudentExitDetails(${app.id})" title="查看详情">
                        <i class="ri-eye-line"></i>
                    </button>
                `;
            case 'approved':
                return `
                    <button class="btn btn-sm btn-warning" onclick="VisitApplicationsPage.cancelStudentExit(${app.id})" title="取消">
                        <i class="ri-close-line"></i>
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="VisitApplicationsPage.viewStudentExitDetails(${app.id})" title="查看详情">
                        <i class="ri-eye-line"></i>
                    </button>
                `;
            case 'rejected':
                return `
                    <button class="btn btn-sm btn-success" onclick="VisitApplicationsPage.reapproveStudentExit(${app.id})" title="重新审核">
                        <i class="ri-refresh-line"></i>
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="VisitApplicationsPage.viewStudentExitDetails(${app.id})" title="查看详情">
                        <i class="ri-eye-line"></i>
                    </button>
                `;
            default:
                return `
                    <button class="btn btn-sm btn-outline" onclick="VisitApplicationsPage.viewStudentExitDetails(${app.id})" title="查看详情">
                        <i class="ri-eye-line"></i>
                    </button>
                `;
        }
    },

    // 学生出校申请审批方法
    async approveStudentExit(applicationId) {
        AdminUtils.showConfirm('确定要通过该学生出校申请吗？', async () => {
            try {
                const response = await AdminUtils.request(`/student-exit/applications/${applicationId}/approve`, {
                    method: 'POST',
                    body: JSON.stringify({
                        approve: true,
                        note: '管理员审批通过'
                    })
                });

                if (response.success) {
                    AdminUtils.showToast('审批通过', 'success');
                    this.loadApplications(); // 刷新列表
                } else {
                    AdminUtils.showToast(response.message || '审批失败', 'error');
                }
            } catch (error) {
                console.error('审批失败:', error);
                AdminUtils.showToast('审批失败', 'error');
            }
        });
    },

    async rejectStudentExit(applicationId) {
        AdminUtils.showConfirm('确定要拒绝该学生出校申请吗？', async () => {
            try {
                const response = await AdminUtils.request(`/student-exit/applications/${applicationId}/approve`, {
                    method: 'POST',
                    body: JSON.stringify({
                        approve: false,
                        note: '管理员审批拒绝'
                    })
                });

                if (response.success) {
                    AdminUtils.showToast('已拒绝申请', 'info');
                    this.loadApplications(); // 刷新列表
                } else {
                    AdminUtils.showToast(response.message || '操作失败', 'error');
                }
            } catch (error) {
                console.error('操作失败:', error);
                AdminUtils.showToast('操作失败', 'error');
            }
        });
    },

    async viewStudentExitDetails(applicationId) {
        // 这里可以实现学生出校申请的详情查看功能
        AdminUtils.showToast('详情查看功能开发中', 'info');
    },

    async cancelStudentExit(applicationId) {
        AdminUtils.showConfirm('确定要取消该学生出校申请吗？', async () => {
            try {
                const response = await AdminUtils.request(`/student-exit/applications/${applicationId}/cancel`, {
                    method: 'POST'
                });

                if (response.success) {
                    AdminUtils.showToast('已取消申请', 'info');
                    this.loadApplications(); // 刷新列表
                } else {
                    AdminUtils.showToast(response.message || '操作失败', 'error');
                }
            } catch (error) {
                console.error('操作失败:', error);
                AdminUtils.showToast('操作失败', 'error');
            }
        });
    },

    async reapproveStudentExit(applicationId) {
        AdminUtils.showConfirm('确定要重新审核该学生出校申请吗？', async () => {
            try {
                const response = await AdminUtils.request(`/student-exit/applications/${applicationId}/reapprove`, {
                    method: 'POST'
                });

                if (response.success) {
                    AdminUtils.showToast('已重新提交审核', 'info');
                    this.loadApplications(); // 刷新列表
                } else {
                    AdminUtils.showToast(response.message || '操作失败', 'error');
                }
            } catch (error) {
                console.error('操作失败:', error);
                AdminUtils.showToast('操作失败', 'error');
            }
        });
    }
};

// 访问记录页面
const VisitRecordsPage = {
    currentPage: 1,
    perPage: 20,
    filters: {
        start_date: '',
        end_date: '',
        verification_method: '',
        gate_name: '',
        status: ''
    },

    async load() {
        this.bindEvents();
        this.setDefaultDates();
        await this.loadRecords();
        await this.loadStatistics();
    },

    bindEvents() {
        // 搜索和筛选事件
        document.getElementById('recordStartDate')?.addEventListener('change', () => {
            this.filters.start_date = document.getElementById('recordStartDate').value;
            this.currentPage = 1;
            this.loadRecords();
        });

        document.getElementById('recordEndDate')?.addEventListener('change', () => {
            this.filters.end_date = document.getElementById('recordEndDate').value;
            this.currentPage = 1;
            this.loadRecords();
        });

        // 导出按钮事件
        const exportBtn = document.querySelector('#visit-recordsPage .btn-outline');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportRecords());
        }
    },

    setDefaultDates() {
        // 设置默认日期范围（最近30天）
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));

        const startDateInput = document.getElementById('recordStartDate');
        const endDateInput = document.getElementById('recordEndDate');

        if (startDateInput && !this.filters.start_date) {
            startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
            this.filters.start_date = startDateInput.value;
        }

        if (endDateInput && !this.filters.end_date) {
            endDateInput.value = today.toISOString().split('T')[0];
            this.filters.end_date = endDateInput.value;
        }
    },

    async loadRecords() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                ...this.filters
            });

            const data = await AdminUtils.request(`/visits/records?${params}`);
            this.renderRecordsTable(data.records);
            this.renderPagination(data.pagination);
        } catch (error) {
            console.error('加载访问记录失败:', error);
            AdminUtils.showToast('加载访问记录失败', 'error');
        }
    },

    async loadStatistics() {
        try {
            const stats = await AdminUtils.request('/visits/records/statistics');
            this.renderStatistics(stats);
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    },

    renderRecordsTable(records) {
        const tbody = document.querySelector('#recordsTable tbody');
        if (!tbody) return;

        if (records.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-secondary">
                        <i class="ri-inbox-line" style="font-size: 2rem; display: block; margin-bottom: 0.5rem;"></i>
                        暂无访问记录
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = records.map(record => {
            const user = record.user || {};
            const vehicle = record.vehicle || {};
            const visitApplication = record.visit_application || {};

            // 格式化时间
            const entryTime = record.entry_time ?
                new Date(record.entry_time).toLocaleString('zh-CN') : '-';
            const exitTime = record.exit_time ?
                new Date(record.exit_time).toLocaleString('zh-CN') : '-';

            // 状态显示
            const statusClass = record.status === 'completed' ? 'success' : 'warning';
            const statusText = record.status === 'completed' ? '已完成' : '进行中';
            const statusIcon = record.status === 'completed' ? 'ri-check-line' : 'ri-time-line';

            // 验证方式显示
            const verificationMethods = {
                'face': '人脸识别',
                'qr_code': '二维码',
                'manual': '人工核验'
            };

            const verificationMethod = verificationMethods[record.verification_method] || record.verification_method;

            return `
                <tr>
                    <td>
                        <div class="user-info">
                            <div class="user-avatar">
                                <i class="ri-user-fill"></i>
                            </div>
                            <div class="user-details">
                                <div class="user-name">${user.real_name || user.username || '未知用户'}</div>
                                <div class="user-meta">${user.email || ''}</div>
                            </div>
                        </div>
                    </td>
                    <td>${entryTime.split(' ')[0]}</td>
                    <td>${entryTime.split(' ')[1]}</td>
                    <td>
                        <div class="purpose-cell">
                            <div class="purpose-text">${visitApplication.visit_purpose || record.notes || '-'}</div>
                            ${vehicle.plate_number ? `<div class="vehicle-info"><i class="ri-car-line"></i> ${vehicle.plate_number}</div>` : ''}
                        </div>
                    </td>
                    <td>
                        <span class="verification-method ${record.verification_method}">
                            <i class="ri-${this.getVerificationIcon(record.verification_method)}-line"></i>
                            ${verificationMethod}
                        </span>
                    </td>
                    <td>${record.gate_name || '-'}</td>
                    <td>
                        <span class="status-badge ${statusClass}">
                            <i class="${statusIcon}"></i>
                            ${statusText}
                        </span>
                    </td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-outline" onclick="VisitRecordsPage.viewRecordDetail(${record.id})" title="查看详情">
                                <i class="ri-eye-line"></i>
                            </button>
                            ${record.status === 'active' ? `
                                <button class="btn btn-sm btn-success" onclick="VisitRecordsPage.recordExit(${record.id})" title="登记离开">
                                    <i class="ri-logout-box-line"></i>
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    },

    getVerificationIcon(method) {
        const icons = {
            'face': 'user-face',
            'qr_code': 'qr-code',
            'manual': 'user-search'
        };
        return icons[method] || 'shield-check';
    },

    renderPagination(pagination) {
        // 使用通用分页工具
        PaginationHelper.renderPaginationWithPerPage(
            'recordsPagination',
            pagination,
            'VisitRecordsPage.goToPage',
            this.perPage,
            [10, 20, 50, 100]
        );
    },

    renderStatistics(stats) {
        // 这里可以在页面顶部显示统计信息
        // 例如：总记录数、进行中记录、已完成记录等
        const statsHtml = `
            <div class="visit-stats">
                <div class="stat-item">
                    <span class="stat-value">${stats.total_records || 0}</span>
                    <span class="stat-label">总记录</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.active_records || 0}</span>
                    <span class="stat-label">进行中</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.today_records || 0}</span>
                    <span class="stat-label">今日访问</span>
                </div>
            </div>
        `;

        // 在页面标题下方插入统计信息
        const pageHeader = document.querySelector('#visit-recordsPage .page-header');
        if (pageHeader && !pageHeader.querySelector('.visit-stats')) {
            const statsDiv = document.createElement('div');
            statsDiv.innerHTML = statsHtml;
            pageHeader.appendChild(statsDiv.firstElementChild);
        }
    },

    goToPage(page) {
        this.currentPage = page;
        this.loadRecords();
    },

    async viewRecordDetail(recordId) {
        try {
            const record = await AdminUtils.request(`/visits/records/${recordId}`);
            this.showRecordDetailModal(record);
        } catch (error) {
            console.error('获取记录详情失败:', error);
            AdminUtils.showToast('获取记录详情失败', 'error');
        }
    },

    showRecordDetailModal(record) {
        const user = record.user || {};
        const vehicle = record.vehicle || {};
        const visitApplication = record.visit_application || {};
        const securityGuard = record.security_guard || {};

        const modalHtml = `
            <div class="modal" id="recordDetailModal">
                <div class="modal-content large">
                    <div class="modal-header">
                        <h3>访问记录详情</h3>
                        <button class="modal-close" onclick="VisitRecordsPage.closeDetailModal()">
                            <i class="ri-close-line"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="record-detail">
                            <div class="detail-section">
                                <h4>访客信息</h4>
                                <div class="detail-grid">
                                    <div class="detail-item">
                                        <label>姓名：</label>
                                        <span>${user.real_name || user.username || '-'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <label>邮箱：</label>
                                        <span>${user.email || '-'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <label>电话：</label>
                                        <span>${user.phone || '-'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <label>用户类型：</label>
                                        <span>${this.getUserTypeText(user.user_type)}</span>
                                    </div>
                                </div>
                            </div>

                            <div class="detail-section">
                                <h4>访问信息</h4>
                                <div class="detail-grid">
                                    <div class="detail-item">
                                        <label>进入时间：</label>
                                        <span>${record.entry_time ? new Date(record.entry_time).toLocaleString('zh-CN') : '-'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <label>离开时间：</label>
                                        <span>${record.exit_time ? new Date(record.exit_time).toLocaleString('zh-CN') : '未离开'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <label>访问目的：</label>
                                        <span>${visitApplication.visit_purpose || record.notes || '-'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <label>验证方式：</label>
                                        <span>${this.getVerificationMethodText(record.verification_method)}</span>
                                    </div>
                                    <div class="detail-item">
                                        <label>闸机：</label>
                                        <span>${record.gate_name || '-'}</span>
                                    </div>
                                    <div class="detail-item">
                                        <label>状态：</label>
                                        <span class="status-badge ${record.status === 'completed' ? 'success' : 'warning'}">
                                            ${record.status === 'completed' ? '已完成' : '进行中'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            ${vehicle.plate_number ? `
                                <div class="detail-section">
                                    <h4>车辆信息</h4>
                                    <div class="detail-grid">
                                        <div class="detail-item">
                                            <label>车牌号：</label>
                                            <span>${vehicle.plate_number}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>车型：</label>
                                            <span>${vehicle.vehicle_type || '-'}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>颜色：</label>
                                            <span>${vehicle.color || '-'}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>品牌：</label>
                                            <span>${vehicle.brand || '-'}</span>
                                        </div>
                                    </div>
                                </div>
                            ` : ''}

                            ${securityGuard.username ? `
                                <div class="detail-section">
                                    <h4>安保信息</h4>
                                    <div class="detail-grid">
                                        <div class="detail-item">
                                            <label>当值保安：</label>
                                            <span>${securityGuard.real_name || securityGuard.username}</span>
                                        </div>
                                        <div class="detail-item">
                                            <label>记录时间：</label>
                                            <span>${record.created_at ? new Date(record.created_at).toLocaleString('zh-CN') : '-'}</span>
                                        </div>
                                    </div>
                                </div>
                            ` : ''}

                            ${record.notes ? `
                                <div class="detail-section">
                                    <h4>备注信息</h4>
                                    <p>${record.notes}</p>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline" onclick="VisitRecordsPage.closeDetailModal()">关闭</button>
                        ${record.status === 'active' ? `
                            <button class="btn btn-success" onclick="VisitRecordsPage.recordExit(${record.id})">
                                <i class="ri-logout-box-line"></i>
                                登记离开
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;

        // 移除现有模态框
        const existingModal = document.getElementById('recordDetailModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        document.getElementById('recordDetailModal').style.display = 'flex';
    },

    closeDetailModal() {
        const modal = document.getElementById('recordDetailModal');
        if (modal) {
            modal.remove();
        }
    },

    async recordExit(recordId) {
        try {
            const exitTime = new Date().toISOString();
            const notes = prompt('请输入离开备注（可选）：');

            const result = await AdminUtils.request(`/visits/records/${recordId}/exit`, {
                method: 'POST',
                body: JSON.stringify({
                    exit_time: exitTime,
                    notes: notes || ''
                })
            });

            AdminUtils.showToast('离开登记成功', 'success');
            this.closeDetailModal();
            this.loadRecords();
            this.loadStatistics();
        } catch (error) {
            console.error('登记离开失败:', error);
            AdminUtils.showToast('登记离开失败', 'error');
        }
    },

    async exportRecords() {
        try {
            // 构建导出参数
            const params = new URLSearchParams({
                format: 'excel', // 默认导出为Excel格式
                ...this.filters
            });

            // 显示加载提示
            AdminUtils.showToast('正在导出访问记录...', 'info');

            // 使用fetch请求获取文件
            const token = localStorage.getItem('admin_token');
            const response = await fetch(`/api/visits/records/export?${params}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '导出失败');
            }

            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `访问记录_${new Date().toISOString().slice(0, 19).replace(/:/g, '')}.xlsx`;

            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }

            // 创建blob并下载
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();

            // 清理
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            AdminUtils.showToast('导出成功', 'success');
        } catch (error) {
            console.error('导出失败:', error);
            AdminUtils.showToast('导出失败: ' + error.message, 'error');
        }
    },

    getUserTypeText(userType) {
        const types = {
            'student': '学生',
            'parent': '家长',
            'alumni': '校友',
            'teacher': '教师',
            'security': '保安',
            'admin': '管理员'
        };

        if (!userType) return userType;

        // 处理多类型（逗号分隔的字符串）
        if (typeof userType === 'string' && userType.includes(',')) {
            const typeArray = userType.split(',').map(t => t.trim());
            return typeArray.map(t => types[t] || t).join('、');
        }

        return types[userType] || userType;
    },

    getVerificationMethodText(method) {
        const methods = {
            'face': '人脸识别',
            'qr_code': '二维码',
            'manual': '人工核验'
        };
        return methods[method] || method;
    },

    
  
  };

// 数据统计页面
const StatisticsPage = {
    currentTab: 'student-leaves',
    chart: null,
    leaveChart: null,
    alumniChart: null,
    visitChart: null,

    async load() {
        this.initTabs();
        this.bindEvents();
        await this.loadStudentLeaveStats();
    },

    initTabs() {
        // 标签页切换
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
    },

    switchTab(tabName) {
        this.currentTab = tabName;

        // 销毁旧图表
        if (this.leaveChart) {
            this.leaveChart.destroy();
            this.leaveChart = null;
        }
        if (this.alumniChart) {
            this.alumniChart.destroy();
            this.alumniChart = null;
        }
        if (this.visitChart) {
            this.visitChart.destroy();
            this.visitChart = null;
        }

        // 更新标签按钮状态
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active');
            }
        });

        // 更新内容区域
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        // 加载对应的数据
        switch(tabName) {
            case 'student-leaves':
                this.loadStudentLeaveStats();
                break;
            case 'alumni-visits':
                this.loadAlumniVisitStats();
                break;
            case 'visit-records':
                this.loadVisitRecordStats();
                break;
            case 'trends':
                this.loadTrendData();
                break;
        }
    },

    bindEvents() {
        // 学生请假统计
        document.getElementById('refreshLeaveStats').addEventListener('click', () => {
            this.loadStudentLeaveStats();
        });

        document.getElementById('exportLeaveStats').addEventListener('click', () => {
            this.exportStats('leave');
        });

        document.getElementById('leaveTimeRange').addEventListener('change', () => {
            this.loadStudentLeaveStats();
        });

        document.getElementById('leaveGroupBy').addEventListener('change', () => {
            this.loadStudentLeaveStats();
        });

        // 校友返校统计
        document.getElementById('refreshAlumniStats').addEventListener('click', () => {
            this.loadAlumniVisitStats();
        });

        document.getElementById('exportAlumniStats').addEventListener('click', () => {
            this.exportStats('alumni');
        });

        document.getElementById('alumniTimeRange').addEventListener('change', () => {
            this.loadAlumniVisitStats();
        });

        document.getElementById('alumniGroupBy').addEventListener('change', () => {
            this.loadAlumniVisitStats();
        });

        // 访问记录统计
        document.getElementById('refreshVisitStats').addEventListener('click', () => {
            this.loadVisitRecordStats();
        });

        document.getElementById('exportVisitStats').addEventListener('click', () => {
            this.exportStats('visit');
        });

        document.getElementById('visitTimeRange').addEventListener('change', () => {
            this.loadVisitRecordStats();
        });

        document.getElementById('visitGroupBy').addEventListener('change', () => {
            this.loadVisitRecordStats();
        });

        // 趋势分析
        document.getElementById('refreshTrend').addEventListener('click', () => {
            this.loadTrendData();
        });

        document.getElementById('trendType').addEventListener('change', () => {
            this.loadTrendData();
        });

        document.getElementById('trendTimeRange').addEventListener('change', () => {
            this.loadTrendData();
        });
    },

    async loadStudentLeaveStats() {
        try {
            const timeRange = document.getElementById('leaveTimeRange').value;
            const groupBy = document.getElementById('leaveGroupBy').value;

            const params = new URLSearchParams({
                time_range: timeRange,
                group_by: groupBy
            });

            const data = await AdminUtils.request(`/statistics/student-leaves?${params}`);
            this.renderLeaveStatsTable(data);
        } catch (error) {
            console.error('加载学生请假统计失败:', error);
            AdminUtils.showToast('加载统计数据失败', 'error');
        }
    },

    renderLeaveStatsTable(data) {
        const thead = document.getElementById('leaveStatsTableHeader');
        const tbody = document.getElementById('leaveStatsTableBody');

        // 更新统计摘要
        this.updateLeaveSummary(data);

        // 渲染图表
        this.renderLeaveChart(data);

        // 根据分组方式设置表头
        if (data.group_by === 'class') {
            thead.innerHTML = `
                <th>班级</th>
                <th>请假次数</th>
                <th>请假人数</th>
                <th>平均次数</th>
            `;
            tbody.innerHTML = data.data.map(row => {
                const avg = row.student_count > 0 ? (row.leave_count / row.student_count).toFixed(1) : '0';
                return `
                <tr>
                    <td><strong>${row.class_name}</strong></td>
                    <td><span class="badge bg-primary">${row.leave_count}</span></td>
                    <td>${row.student_count}</td>
                    <td>${avg}</td>
                </tr>
            `}).join('');
        } else if (data.group_by === 'grade') {
            thead.innerHTML = `
                <th>年级</th>
                <th>请假次数</th>
                <th>请假人数</th>
                <th>平均次数</th>
            `;
            tbody.innerHTML = data.data.map(row => {
                const avg = row.student_count > 0 ? (row.leave_count / row.student_count).toFixed(1) : '0';
                return `
                <tr>
                    <td><strong>${row.grade_name}</strong></td>
                    <td><span class="badge bg-primary">${row.leave_count}</span></td>
                    <td>${row.student_count}</td>
                    <td>${avg}</td>
                </tr>
            `}).join('');
        } else if (data.group_by === 'student') {
            thead.innerHTML = `
                <th>排名</th>
                <th>学生姓名</th>
                <th>班级</th>
                <th>请假次数</th>
            `;
            tbody.innerHTML = data.data.map((row, index) => `
                <tr>
                    <td><span class="badge ${index < 3 ? 'bg-warning' : 'bg-secondary'}">#${index + 1}</span></td>
                    <td><strong>${row.student_name}</strong></td>
                    <td>${row.class_name}</td>
                    <td><span class="badge bg-primary">${row.count}</span></td>
                </tr>
            `).join('');
        }

        if (data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">暂无数据</td></tr>';
        }
    },

    updateLeaveSummary(data) {
        // 计算统计数据
        const totalLeaves = data.data.reduce((sum, row) => sum + (row.leave_count || row.count || 0), 0);
        const totalStudents = data.data.reduce((sum, row) => sum + (row.student_count || 0), 0);
        const avgLeaves = totalStudents > 0 ? (totalLeaves / totalStudents).toFixed(1) : '0';

        // 找出请假最多的班级/年级
        let topClass = '-';
        if (data.group_by === 'class' && data.data.length > 0) {
            const top = data.data.reduce((max, row) => row.leave_count > max.leave_count ? row : max, data.data[0]);
            topClass = `${top.class_name}(${top.leave_count}次)`;
        } else if (data.group_by === 'grade' && data.data.length > 0) {
            const top = data.data.reduce((max, row) => row.leave_count > max.leave_count ? row : max, data.data[0]);
            topClass = `${top.grade_name}(${top.leave_count}次)`;
        } else if (data.group_by === 'student' && data.data.length > 0) {
            topClass = `${data.data[0].student_name}(${data.data[0].count}次)`;
        }

        // 更新卡片
        document.getElementById('totalLeaves').textContent = totalLeaves;
        document.getElementById('totalStudents').textContent = totalStudents;
        document.getElementById('avgLeaves').textContent = avgLeaves;
        document.getElementById('topClass').textContent = topClass;
    },

    renderLeaveChart(data) {
        const canvas = document.getElementById('leaveChart');
        if (!canvas) return;

        // 销毁旧图表
        if (this.leaveChart) {
            this.leaveChart.destroy();
        }

        // 准备图表数据
        const labels = [];
        const values = [];
        const colors = [];

        if (data.group_by === 'class') {
            data.data.forEach((row, index) => {
                labels.push(row.class_name);
                values.push(row.leave_count);
                colors.push(`hsl(${(index * 360 / data.data.length)}, 70%, 60%)`);
            });
        } else if (data.group_by === 'grade') {
            data.data.forEach((row, index) => {
                labels.push(row.grade_name);
                values.push(row.leave_count);
                colors.push(`hsl(${(index * 360 / data.data.length)}, 70%, 60%)`);
            });
        } else if (data.group_by === 'student') {
            // 只显示前10名
            data.data.slice(0, 10).forEach((row, index) => {
                labels.push(row.student_name);
                values.push(row.count);
                colors.push(`hsl(${(index * 360 / Math.min(data.data.length, 10))}, 70%, 60%)`);
            });
        }

        // 创建图表
        const ctx = canvas.getContext('2d');
        this.leaveChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '请假次数',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: data.group_by === 'class' ? '各班级请假统计' :
                              data.group_by === 'grade' ? '各年级请假统计' :
                              '学生请假次数排行（前10名）',
                        font: {
                            size: 14
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    },

    async loadAlumniVisitStats() {
        try {
            const timeRange = document.getElementById('alumniTimeRange').value;
            const groupBy = document.getElementById('alumniGroupBy').value;

            const params = new URLSearchParams({
                time_range: timeRange,
                group_by: groupBy
            });

            const data = await AdminUtils.request(`/statistics/alumni-visits?${params}`);
            this.renderAlumniStatsTable(data);
        } catch (error) {
            console.error('加载校友返校统计失败:', error);
            AdminUtils.showToast('加载统计数据失败', 'error');
        }
    },

    renderAlumniStatsTable(data) {
        const thead = document.getElementById('alumniStatsTableHeader');
        const tbody = document.getElementById('alumniStatsTableBody');

        if (data.group_by === 'grade') {
            thead.innerHTML = `
                <th>毕业年份</th>
                <th>返校次数</th>
                <th>返校人数</th>
            `;
            tbody.innerHTML = data.data.map(row => `
                <tr>
                    <td><strong>${row.graduation_year}</strong></td>
                    <td><span class="badge bg-primary">${row.visit_count}</span></td>
                    <td>${row.visitor_count}</td>
                </tr>
            `).join('');
        } else if (data.group_by === 'student') {
            thead.innerHTML = `
                <th>排名</th>
                <th>校友姓名</th>
                <th>毕业年份</th>
                <th>班级</th>
                <th>返校次数</th>
            `;
            tbody.innerHTML = data.data.map((row, index) => `
                <tr>
                    <td><span class="badge ${index < 3 ? 'bg-warning' : 'bg-secondary'}">#${index + 1}</span></td>
                    <td><strong>${row.alumni_name}</strong></td>
                    <td>${row.graduation_year}</td>
                    <td>${row.class_name}</td>
                    <td><span class="badge bg-primary">${row.visit_count}</span></td>
                </tr>
            `).join('');
        } else if (data.group_by === 'year_segment') {
            thead.innerHTML = `
                <th>年代段</th>
                <th>返校次数</th>
                <th>返校人数</th>
            `;
            tbody.innerHTML = data.data.map(row => `
                <tr>
                    <td><strong>${row.year_segment}</strong></td>
                    <td><span class="badge bg-primary">${row.visit_count}</span></td>
                    <td>${row.visitor_count}</td>
                </tr>
            `).join('');
        }

        if (data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-secondary">暂无数据</td></tr>';
        }
    },

    async loadVisitRecordStats() {
        try {
            const timeRange = document.getElementById('visitTimeRange').value;
            const groupBy = document.getElementById('visitGroupBy').value;

            const params = new URLSearchParams({
                time_range: timeRange,
                group_by: groupBy
            });

            const data = await AdminUtils.request(`/statistics/visit-records?${params}`);
            this.renderVisitStatsTable(data);
        } catch (error) {
            console.error('加载访问记录统计失败:', error);
            AdminUtils.showToast('加载统计数据失败', 'error');
        }
    },

    renderVisitStatsTable(data) {
        const thead = document.getElementById('visitStatsTableHeader');
        const tbody = document.getElementById('visitStatsTableBody');

        if (data.group_by === 'host') {
            thead.innerHTML = `
                <th>排名</th>
                <th>受访老师</th>
                <th>受访次数</th>
                <th>访客人数</th>
            `;
            tbody.innerHTML = data.data.map((row, index) => `
                <tr>
                    <td><span class="badge ${index < 3 ? 'bg-warning' : 'bg-secondary'}">#${index + 1}</span></td>
                    <td><strong>${row.host_name}</strong></td>
                    <td><span class="badge bg-primary">${row.visit_count}</span></td>
                    <td>${row.visitor_count}</td>
                </tr>
            `).join('');
        } else if (data.group_by === 'visitor_type') {
            thead.innerHTML = `
                <th>访客类型</th>
                <th>访问次数</th>
                <th>访客人数</th>
            `;
            tbody.innerHTML = data.data.map(row => `
                <tr>
                    <td><strong>${row.visitor_type_name}</strong></td>
                    <td><span class="badge bg-primary">${row.visit_count}</span></td>
                    <td>${row.visitor_count}</td>
                </tr>
            `).join('');
        } else if (data.group_by === 'purpose') {
            thead.innerHTML = `
                <th>访问目的</th>
                <th>访问次数</th>
                <th>访客人数</th>
            `;
            tbody.innerHTML = data.data.map(row => `
                <tr>
                    <td><strong>${row.purpose_category}</strong></td>
                    <td><span class="badge bg-primary">${row.visit_count}</span></td>
                    <td>${row.visitor_count}</td>
                </tr>
            `).join('');
        }

        if (data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">暂无数据</td></tr>';
        }
    },

    async loadTrendData() {
        try {
            const type = document.getElementById('trendType').value;
            const timeRange = document.getElementById('trendTimeRange').value;

            const params = new URLSearchParams({
                type: type,
                time_range: timeRange
            });

            const data = await AdminUtils.request(`/statistics/trend?${params}`);
            this.renderTrendChart(data);
        } catch (error) {
            console.error('加载趋势数据失败:', error);
            AdminUtils.showToast('加载趋势数据失败', 'error');
        }
    },

    renderTrendChart(data) {
        const lineCanvas = document.getElementById('trendLineChart');
        const barCanvas = document.getElementById('trendBarChart');

        if (!lineCanvas || !barCanvas) return;

        const lineCtx = lineCanvas.getContext('2d');
        const barCtx = barCanvas.getContext('2d');

        // 清除之前的图表
        if (this.lineChart) {
            this.lineChart.destroy();
        }
        if (this.barChart) {
            this.barChart.destroy();
        }

        // 准备数据
        const labels = data.data.map(d => {
            const date = new Date(d.date);
            return `${date.getMonth() + 1}/${date.getDate()}`;
        });
        const values = data.data.map(d => d.count);
        const title = data.type === 'leaves' ? '学生请假趋势' : '访问记录趋势';

        // 颜色配置
        const colors = {
            leaves: { primary: 'rgba(255, 152, 0, 0.8)', secondary: 'rgba(255, 152, 0, 0.2)' },
            visits: { primary: 'rgba(33, 150, 243, 0.8)', secondary: 'rgba(33, 150, 243, 0.2)' }
        };
        const colorSet = data.type === 'leaves' ? colors.leaves : colors.visits;

        // 创建折线图
        this.lineChart = new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: title,
                    data: values,
                    borderColor: colorSet.primary,
                    backgroundColor: colorSet.secondary,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });

        // 创建柱状图
        this.barChart = new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '数量',
                    data: values,
                    backgroundColor: colorSet.primary,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    },

    async exportStats(type) {
        try {
            let statType, filename;

            switch(type) {
                case 'leave':
                    statType = 'leaves';
                    filename = '学生请假统计';
                    break;
                case 'alumni':
                    statType = 'alumni';
                    filename = '校友返校统计';
                    break;
                case 'visit':
                    statType = 'visits';
                    filename = '访问记录统计';
                    break;
            }

            // 获取当前的筛选条件
            let url = `/statistics/export/${statType}`;
            const params = new URLSearchParams();

            if (this.currentTab === 'student-leaves') {
                params.append('time_range', document.getElementById('leaveTimeRange').value);
                params.append('group_by', document.getElementById('leaveGroupBy').value);
            } else if (this.currentTab === 'alumni-visits') {
                params.append('time_range', document.getElementById('alumniTimeRange').value);
                params.append('group_by', document.getElementById('alumniGroupBy').value);
            } else if (this.currentTab === 'visit-records') {
                params.append('time_range', document.getElementById('visitTimeRange').value);
                params.append('group_by', document.getElementById('visitGroupBy').value);
            }

            if (params.toString()) {
                url += `?${params}`;
            }

            // 下载Excel文件
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('导出失败');
            }

            const blob = await response.blob();
            const downloadUrl = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `${filename}_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(downloadUrl);

            AdminUtils.showToast('Excel导出成功', 'success');
        } catch (error) {
            console.error('导出失败:', error);
            AdminUtils.showToast('导出失败: ' + error.message, 'error');
        }
    },
};

// 批量授权页面
const BatchApprovePage = {
    async load() {
        this.bindEvents();
    },

    bindEvents() {
        const typeSelect = document.getElementById('batchType');
        const targetSelect = document.getElementById('batchTarget');
        const form = document.getElementById('batchApproveForm');

        // 类型变化时加载目标选项
        typeSelect.addEventListener('change', async () => {
            const type = typeSelect.value;
            targetSelect.innerHTML = '<option value="">加载中...</option>';
            targetSelect.disabled = false;

            if (type) {
                try {
                    const options = await this.loadTargetOptions(type);
                    targetSelect.innerHTML = '<option value="">请选择目标</option>' +
                        options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('');
                } catch (error) {
                    targetSelect.innerHTML = '<option value="">加载失败</option>';
                    targetSelect.disabled = true;
                }
            } else {
                targetSelect.innerHTML = '<option value="">请先选择授权类型</option>';
                targetSelect.disabled = true;
            }
        });

        // 表单提交
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitBatchApprove();
        });

        // 预览按钮
        document.getElementById('previewBatch').addEventListener('click', () => {
            this.previewBatch();
        });
    },

    async loadTargetOptions(type) {
        // 模拟加载选项，实际应该调用API
        if (type === 'year') {
            return [
                { value: '2020', label: '2020届' },
                { value: '2019', label: '2019届' },
                { value: '2018', label: '2018届' }
            ];
        } else if (type === 'division') {
            return [
                { value: '高中部', label: '高中部' },
                { value: '初中部', label: '初中部' },
                { value: '国际部', label: '国际部' },
                { value: '新疆部', label: '新疆部' },
                { value: '北校区', label: '北校区' }
            ];
        } else {
            return [];
        }
    },

    async submitBatchApprove() {
        const formData = {
            type: document.getElementById('batchType').value,
            target_value: document.getElementById('batchTarget').value,
            visit_date: document.getElementById('batchDate').value,
            time_start: document.getElementById('batchStartTime').value,
            time_end: document.getElementById('batchEndTime').value,
            visit_purpose: document.getElementById('batchPurpose').value
        };

        try {
            const data = await AdminUtils.request('/admin/batch-approve', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            AdminUtils.showToast(`成功为 ${data.count} 位校友创建访问授权`, 'success');
            document.getElementById('batchApproveForm').reset();
            document.getElementById('batchPreview').style.display = 'none';
        } catch (error) {
            AdminUtils.showToast('批量授权失败', 'error');
        }
    },

    previewBatch() {
        // 实现预览功能
        AdminUtils.showToast('预览功能开发中', 'info');
    }
};

// 校历管理页面
const CalendarPage = {
    currentPage: 1,
    currentView: 'list', // 'list' or 'calendar'
    currentMonth: new Date().getMonth(),
    currentYear: new Date().getFullYear(),
    filters: {
        year: '',
        month: '',
        event_type: '',
        status: 'published',
        search: ''
    },
    editingEventId: null,

    async load() {
        this.bindEvents();
        await this.loadEvents();
        await this.loadStatistics();
    },

    bindEvents() {
        // 视图切换
        document.getElementById('calendarViewBtn')?.addEventListener('click', () => {
            this.switchView('calendar');
        });
        document.getElementById('listViewBtn')?.addEventListener('click', () => {
            this.switchView('list');
        });

        // 新建事件按钮
        document.getElementById('createEventBtn')?.addEventListener('click', () => {
            this.showEventModal();
        });
        document.getElementById('addEventBtn')?.addEventListener('click', () => {
            this.showEventModal();
        });
        document.getElementById('newEventBtn')?.addEventListener('click', () => {
            this.showEventModal();
        });

        // 刷新按钮
        document.getElementById('refreshCalendarList')?.addEventListener('click', () => {
            this.loadEvents();
            this.loadStatistics();
        });
        document.getElementById('refreshCalendarBtn')?.addEventListener('click', () => {
            this.loadEvents();
            this.loadStatistics();
        });

        // 筛选器
        document.getElementById('calendarYearFilter')?.addEventListener('change', (e) => {
            this.filters.year = e.target.value;
            this.currentPage = 1;
            this.loadEvents();
        });

        document.getElementById('calendarMonthFilter')?.addEventListener('change', (e) => {
            this.filters.month = e.target.value;
            this.currentPage = 1;
            this.loadEvents();
        });

        document.getElementById('calendarTypeFilter')?.addEventListener('change', (e) => {
            this.filters.event_type = e.target.value;
            this.currentPage = 1;
            this.loadEvents();
        });

        document.getElementById('calendarStatusFilter')?.addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.currentPage = 1;
            this.loadEvents();
        });

        document.getElementById('calendarSearch')?.addEventListener('input', AdminUtils.debounce((e) => {
            this.filters.search = e.target.value;
            this.currentPage = 1;
            this.loadEvents();
        }, 500));

        // 事件表单提交
        const eventForm = document.getElementById('eventForm');
        if (eventForm) {
            eventForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveEvent();
            });
        }

        // 月历导航
        document.getElementById('prevMonthBtn')?.addEventListener('click', () => {
            this.navigateMonth(-1);
        });

        document.getElementById('nextMonthBtn')?.addEventListener('click', () => {
            this.navigateMonth(1);
        });

        document.getElementById('todayBtn')?.addEventListener('click', () => {
            this.goToToday();
        });
    },

    async loadEvents() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: 20,
                ...this.filters
            });

            const data = await AdminUtils.request(`/calendar/events?${params}`);

            if (this.currentView === 'list') {
                this.renderEventsList(data.events);
                this.renderPagination(data.pagination);
            } else {
                this.renderCalendarView(data.events);
            }
        } catch (error) {
            console.error('加载校历事件失败:', error);
            AdminUtils.showToast('加载校历事件失败', 'error');
        }
    },

    async loadStatistics() {
        try {
            const stats = await AdminUtils.request('/calendar/statistics');
            this.updateStatistics(stats);
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    },

    updateStatistics(stats) {
        document.getElementById('totalEvents').textContent = stats.total_events || 0;
        document.getElementById('publishedEvents').textContent = stats.published_events || 0;
        document.getElementById('upcomingEvents').textContent = stats.upcoming_events || 0;
        document.getElementById('anniversaryEvents').textContent = stats.anniversary_events || 0;
    },

    renderEventsList(events) {
        const tbody = document.getElementById('eventsTableBody');

        if (events.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-secondary">暂无数据</td></tr>';
            return;
        }

        tbody.innerHTML = events.map(event => `
            <tr>
                <td>
                    <span class="event-type ${event.event_type}">
                        ${this.getEventTypeText(event.event_type)}
                    </span>
                </td>
                <td>
                    <div class="event-title">${event.title}</div>
                    ${event.description ? `<div class="event-description">${event.description}</div>` : ''}
                </td>
                <td>
                    <div class="event-date">
                        <div>${AdminUtils.formatDate(event.start_date)}</div>
                        ${event.end_date && event.end_date !== event.start_date ?
                            `<div class="text-muted">${AdminUtils.formatDate(event.end_date)}</div>` : ''}
                    </div>
                    ${event.start_time ? `<div class="event-time">${event.start_time}${event.end_time ? ' - ' + event.end_time : ''}</div>` : ''}
                </td>
                <td>${event.location || '-'}</td>
                <td>
                    <span class="priority-badge priority-${event.priority}">
                        ${this.getPriorityText(event.priority)}
                    </span>
                </td>
                <td>
                    <span class="status-badge ${event.status}">
                        ${AdminUtils.getStatusText(event.status)}
                    </span>
                </td>
                <td>
                    <div class="target-audience">
                        ${this.getTargetAudienceText(event.target_audience, event.target_graduation_years, event.target_divisions)}
                    </div>
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline" onclick="CalendarPage.viewEvent(${event.id})" title="查看">
                            <i class="ri-eye-line"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="CalendarPage.editEvent(${event.id})" title="编辑">
                            <i class="ri-edit-line"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="CalendarPage.deleteEvent(${event.id})" title="删除">
                            <i class="ri-delete-bin-line"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    },

    renderCalendarView(events) {
        const calendarContainer = document.getElementById('calendarContainer');
        if (!calendarContainer) return;

        // 生成月历
        const firstDay = new Date(this.currentYear, this.currentMonth, 1).getDay();
        const daysInMonth = new Date(this.currentYear, this.currentMonth + 1, 0).getDate();

        let html = `
            <div class="calendar-header">
                <h3>${this.currentYear}年${this.currentMonth + 1}月</h3>
            </div>
            <div class="calendar-grid">
                <div class="calendar-weekdays">
                    <div class="weekday">日</div>
                    <div class="weekday">一</div>
                    <div class="weekday">二</div>
                    <div class="weekday">三</div>
                    <div class="weekday">四</div>
                    <div class="weekday">五</div>
                    <div class="weekday">六</div>
                </div>
                <div class="calendar-days">
        `;

        // 空白日期
        for (let i = 0; i < firstDay; i++) {
            html += '<div class="calendar-day empty"></div>';
        }

        // 日期格子
        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${this.currentYear}-${String(this.currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayEvents = events.filter(event => {
                const eventDate = event.start_date;
                return eventDate <= dateStr && (!event.end_date || event.end_date >= dateStr);
            });

            const isToday = this.isToday(day);
            html += `
                <div class="calendar-day ${isToday ? 'today' : ''}">
                    <div class="day-number">${day}</div>
                    <div class="day-events">
                        ${dayEvents.slice(0, 3).map(event => `
                            <div class="event-dot event-type-${event.event_type}"
                                 title="${event.title}"
                                 onclick="CalendarPage.viewEvent(${event.id})">
                            </div>
                        `).join('')}
                        ${dayEvents.length > 3 ? `<div class="more-events">+${dayEvents.length - 3}</div>` : ''}
                    </div>
                </div>
            `;
        }

        html += '</div></div>';
        calendarContainer.innerHTML = html;
    },

    renderPagination(pagination) {
        const container = document.getElementById('calendarPagination');
        if (!container) return;

        let html = '';

        html += `<button ${pagination.has_prev ? '' : 'disabled'} onclick="CalendarPage.goToPage(${pagination.page - 1})">上一页</button>`;

        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === pagination.page ? 'active' : ''}" onclick="CalendarPage.goToPage(${i})">${i}</button>`;
        }

        html += `<button ${pagination.has_next ? '' : 'disabled'} onclick="CalendarPage.goToPage(${pagination.page + 1})">下一页</button>`;

        container.innerHTML = html;
    },

    switchView(view) {
        this.currentView = view;

        // 更新按钮状态
        document.getElementById('calendarViewBtn')?.classList.toggle('active', view === 'calendar');
        document.getElementById('listViewBtn')?.classList.toggle('active', view === 'list');

        // 切换视图
        document.getElementById('eventsListContainer')?.classList.toggle('hidden', view !== 'list');
        document.getElementById('calendarContainer')?.classList.toggle('hidden', view !== 'calendar');

        // 重新加载数据
        this.loadEvents();
    },

    navigateMonth(direction) {
        this.currentMonth += direction;
        if (this.currentMonth > 11) {
            this.currentMonth = 0;
            this.currentYear++;
        } else if (this.currentMonth < 0) {
            this.currentMonth = 11;
            this.currentYear--;
        }
        this.loadEvents();
    },

    goToToday() {
        const today = new Date();
        this.currentMonth = today.getMonth();
        this.currentYear = today.getFullYear();
        this.loadEvents();
    },

    isToday(day) {
        const today = new Date();
        return day === today.getDate() &&
               this.currentMonth === today.getMonth() &&
               this.currentYear === today.getFullYear();
    },

    showEventModal(eventId = null) {
        this.editingEventId = eventId;
        const modal = document.getElementById('eventModal');
        const form = document.getElementById('eventForm');

        if (eventId) {
            // 编辑模式 - 加载事件数据
            this.loadEventToForm(eventId);
        } else {
            // 新建模式 - 重置表单
            form.reset();
            document.getElementById('eventModalTitle').textContent = '新建事件';
        }

        modal.classList.add('active');
    },

    async loadEventToForm(eventId) {
        try {
            const event = await AdminUtils.request(`/calendar/events/${eventId}`);

            document.getElementById('eventModalTitle').textContent = '编辑事件';
            document.getElementById('eventTitle').value = event.title;
            document.getElementById('eventDescription').value = event.description || '';
            document.getElementById('eventType').value = event.event_type;
            document.getElementById('eventStartDate').value = event.start_date;
            document.getElementById('eventEndDate').value = event.end_date || '';
            document.getElementById('eventStartTime').value = event.start_time || '';
            document.getElementById('eventEndTime').value = event.end_time || '';
            document.getElementById('eventAllDay').checked = event.all_day || false;
            document.getElementById('eventLocation').value = event.location || '';
            document.getElementById('eventPriority').value = event.priority;
            document.getElementById('eventStatus').value = event.status;
            document.getElementById('eventTargetAudience').value = event.target_audience;
            document.getElementById('eventTargetGraduationYears').value = event.target_graduation_years || '';
            document.getElementById('eventTargetDivisions').value = event.target_divisions || '';
            document.getElementById('eventContactPerson').value = event.contact_person || '';
            document.getElementById('eventContactPhone').value = event.contact_phone || '';
            document.getElementById('eventContactEmail').value = event.contact_email || '';

            // 特殊字段
            if (event.event_type === 'anniversary') {
                document.getElementById('eventAnniversaryYear').value = event.anniversary_year || '';
                document.getElementById('eventGraduationYear').value = event.graduation_year || '';
            } else if (event.event_type === 'club') {
                document.getElementById('eventClubName').value = event.club_name || '';
                document.getElementById('eventClubType').value = event.club_type || '';
            }

        } catch (error) {
            console.error('加载事件数据失败:', error);
            AdminUtils.showToast('加载事件数据失败', 'error');
        }
    },

    async saveEvent() {
        const form = document.getElementById('eventForm');
        const formData = new FormData(form);

        const eventData = {
            title: formData.get('title'),
            description: formData.get('description'),
            event_type: formData.get('event_type'),
            start_date: formData.get('start_date'),
            end_date: formData.get('end_date') || null,
            start_time: formData.get('start_time') || null,
            end_time: formData.get('end_time') || null,
            all_day: formData.get('all_day') === 'on',
            location: formData.get('location'),
            priority: formData.get('priority'),
            status: formData.get('status'),
            target_audience: formData.get('target_audience'),
            target_graduation_years: formData.get('target_graduation_years') || null,
            target_divisions: formData.get('target_divisions') || null,
            contact_person: formData.get('contact_person'),
            contact_phone: formData.get('contact_phone'),
            contact_email: formData.get('contact_email')
        };

        // 特殊字段
        if (eventData.event_type === 'anniversary') {
            eventData.anniversary_year = formData.get('anniversary_year') || null;
            eventData.graduation_year = formData.get('graduation_year') || null;
        } else if (eventData.event_type === 'club') {
            eventData.club_name = formData.get('club_name');
            eventData.club_type = formData.get('club_type');
        }

        try {
            if (this.editingEventId) {
                await AdminUtils.request(`/calendar/events/${this.editingEventId}`, {
                    method: 'PUT',
                    body: JSON.stringify(eventData)
                });
                AdminUtils.showToast('事件更新成功', 'success');
            } else {
                await AdminUtils.request('/calendar/events', {
                    method: 'POST',
                    body: JSON.stringify(eventData)
                });
                AdminUtils.showToast('事件创建成功', 'success');
            }

            this.closeEventModal();
            this.loadEvents();
            this.loadStatistics();
        } catch (error) {
            console.error('保存事件失败:', error);
            AdminUtils.showToast('保存事件失败', 'error');
        }
    },

    async deleteEvent(eventId) {
        AdminUtils.showConfirm('确定要删除这个事件吗？', async () => {
            try {
                await AdminUtils.request(`/calendar/events/${eventId}`, {
                    method: 'DELETE'
                });
                AdminUtils.showToast('事件删除成功', 'success');
                this.loadEvents();
                this.loadStatistics();
            } catch (error) {
                AdminUtils.showToast('删除事件失败', 'error');
            }
        });
    },

    viewEvent(eventId) {
        // 显示事件详情模态框
        this.showEventDetailModal(eventId);
    },

    editEvent(eventId) {
        this.showEventModal(eventId);
    },

    async showEventDetailModal(eventId) {
        try {
            const event = await AdminUtils.request(`/calendar/events/${eventId}`);
            const modal = document.getElementById('eventDetailModal');

            document.getElementById('detailTitle').textContent = event.title;
            document.getElementById('detailDescription').textContent = event.description || '无描述';
            document.getElementById('detailType').textContent = this.getEventTypeText(event.event_type);
            document.getElementById('detailDate').textContent = this.formatEventDate(event);
            document.getElementById('detailLocation').textContent = event.location || '无地点';
            document.getElementById('detailPriority').textContent = this.getPriorityText(event.priority);
            document.getElementById('detailStatus').textContent = AdminUtils.getStatusText(event.status);
            document.getElementById('detailTargetAudience').textContent = this.getTargetAudienceText(
                event.target_audience, event.target_graduation_years, event.target_divisions
            );
            document.getElementById('detailContact').textContent = this.formatContactInfo(event);

            modal.classList.add('active');
        } catch (error) {
            console.error('加载事件详情失败:', error);
            AdminUtils.showToast('加载事件详情失败', 'error');
        }
    },

    closeEventModal() {
        document.getElementById('eventModal')?.classList.remove('active');
        this.editingEventId = null;
    },

    goToPage(page) {
        this.currentPage = page;
        this.loadEvents();
    },

    // 辅助方法
    getEventTypeText(type) {
        const types = {
            anniversary: '周年活动',
            festival: '传统节日',
            activity: '校园活动',
            club: '社团活动',
            meeting: '重要会议',
            holiday: '假期',
            exam: '考试'
        };
        return types[type] || type;
    },

    getPriorityText(priority) {
        const priorities = {
            urgent: '紧急',
            high: '高',
            medium: '中',
            low: '低'
        };
        return priorities[priority] || priority;
    },

    getTargetAudienceText(audience, graduationYears, divisions) {
        let text = {
            all: '全部',
            alumni: '校友',
            students: '学生',
            teachers: '教师',
            specific: '特定群体'
        }[audience] || audience;

        if (graduationYears && typeof graduationYears === 'string') {
            text += ` (${graduationYears.split(',').map(y => y + '届').join(', ')})`;
        }

        if (divisions && typeof divisions === 'string') {
            text += ` [${divisions.split(',').join(', ')}]`;
        }

        return text;
    },

    formatEventDate(event) {
        let dateText = AdminUtils.formatDate(event.start_date);

        if (event.end_date && event.end_date !== event.start_date) {
            dateText += ` 至 ${AdminUtils.formatDate(event.end_date)}`;
        }

        if (event.start_time) {
            dateText += ` ${event.start_time}`;
            if (event.end_time) {
                dateText += ` - ${event.end_time}`;
            }
        }

        if (event.all_day) {
            dateText += ' (全天)';
        }

        return dateText;
    },

    formatContactInfo(event) {
        let contact = '';
        if (event.contact_person) {
            contact += event.contact_person;
        }
        if (event.contact_phone) {
            contact += (contact ? ' | ' : '') + event.contact_phone;
        }
        if (event.contact_email) {
            contact += (contact ? ' | ' : '') + event.contact_email;
        }
        return contact || '无联系信息';
    },

    // 校历导入功能
    showImportModal() {
        const modal = document.getElementById('importModal');
        if (modal) {
            modal.classList.add('active');
            this.resetImportModal();
        }
    },

    resetImportModal() {
        // 重置导入模态框状态
        this.importData = {
            file: null,
            preview: null,
            validated: false
        };

        // 重置步骤显示
        this.showImportStep(1);

        // 重置表单和文件
        document.getElementById('importFileInput').value = '';
        document.getElementById('uploadFileName').textContent = '';
        document.getElementById('importPreviewContainer').style.display = 'none';
        document.getElementById('importResultContainer').style.display = 'none';
        document.getElementById('importConfirmBtn').disabled = true;
        document.getElementById('importConfirmBtn').textContent = '确认导入';

        // 重置拖拽区域
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.classList.remove('drag-over');
        }

        // 清理重试选项
        const retryContainer = document.querySelector('.retry-container');
        if (retryContainer) {
            retryContainer.remove();
        }

        // 清理进度条
        this.hideImportProgress();

        // 清理错误详情
        const errorDetails = document.querySelector('.import-error-details');
        if (errorDetails) {
            errorDetails.remove();
        }

        // 清理预览内容
        const validationErrors = document.getElementById('validationErrors');
        if (validationErrors) {
            validationErrors.innerHTML = '';
        }

        const previewTableBody = document.getElementById('previewTableBody');
        if (previewTableBody) {
            previewTableBody.innerHTML = '';
        }

        const importResults = document.getElementById('importResults');
        if (importResults) {
            importResults.innerHTML = '';
        }

        // 重置统计信息显示
        const statisticsElements = [
            'validRecordsCount', 'errorRecordsCount', 'totalRecordsCount',
            'importedCount', 'skippedCount', 'errorImportCount', 'previewMoreInfo'
        ];

        statisticsElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = '0';
            }
        });
    },

    showImportStep(stepNumber) {
        // 隐藏所有步骤
        document.querySelectorAll('.import-step').forEach(step => {
            step.classList.remove('active');
        });

        // 显示当前步骤
        const currentStep = document.getElementById(`importStep${stepNumber}`);
        if (currentStep) {
            currentStep.classList.add('active');
        }

        // 更新步骤指示器
        document.querySelectorAll('.step-indicator').forEach(indicator => {
            indicator.classList.remove('active');
        });

        const activeIndicators = document.querySelectorAll(`.step-indicator:nth-child(-n+${stepNumber})`);
        activeIndicators.forEach(indicator => {
            indicator.classList.add('active');
        });
    },

    async downloadTemplate() {
        try {
            const response = await fetch(`${ADMIN_CONFIG.API_BASE_URL}/calendar/import/template`, {
                headers: {
                    'Authorization': `Bearer ${AdminState.token}`
                }
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '校历导入模板.xlsx';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                AdminUtils.showToast('模板下载成功', 'success');
            } else {
                throw new Error('模板下载失败');
            }
        } catch (error) {
            console.error('下载模板失败:', error);
            AdminUtils.showToast('下载模板失败', 'error');
        }
    },

    handleFileSelect(file) {
        if (!file) return;

        // 验证文件类型
        const allowedTypes = [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'
        ];

        if (!allowedTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
            AdminUtils.showToast('请选择Excel文件(.xlsx, .xls)或CSV文件', 'error');
            return;
        }

        // 验证文件大小 (10MB)
        if (file.size > 10 * 1024 * 1024) {
            AdminUtils.showToast('文件大小不能超过10MB', 'error');
            return;
        }

        // 验证文件名
        if (!this.validateFileName(file.name)) {
            AdminUtils.showToast('文件名包含非法字符，请重新命名', 'error');
            return;
        }

        this.importData.file = file;
        document.getElementById('uploadFileName').textContent = file.name;
        document.getElementById('importConfirmBtn').disabled = false;

        // 自动开始上传预览
        setTimeout(() => this.uploadAndPreview(), 500);
    },

  validateFileName(fileName) {
        // 检查文件名是否包含非法字符
        const invalidChars = /[<>:"/\\|?*\x00-\x1f]/;
        if (invalidChars.test(fileName)) {
            return false;
        }

        // 检查文件名长度
        if (fileName.length > 255) {
            return false;
        }

        return true;
    },

    async uploadAndPreview() {
        if (!this.importData.file) {
            AdminUtils.showToast('请先选择文件', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', this.importData.file);

        try {
            // 显示加载状态
            const uploadBtn = document.getElementById('importConfirmBtn');
            const originalText = uploadBtn.textContent;
            uploadBtn.disabled = true;
            uploadBtn.textContent = '上传中...';

            // 添加请求超时处理
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时

            const data = await AdminUtils.request('/calendar/import/upload', {
                method: 'POST',
                body: formData,
                headers: {}, // 不设置Content-Type，让浏览器自动设置multipart/form-data
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // 恢复按钮状态
            uploadBtn.disabled = false;
            uploadBtn.textContent = '确认导入';

            if (data.success) {
                this.importData.preview = data;
                this.importData.validated = true;

                // 显示预览数据
                this.renderImportPreview(data);

                // 切换到步骤2
                this.showImportStep(2);
            } else {
                this.handleUploadError(data);
            }
        } catch (error) {
            clearTimeout(timeoutId);
            this.handleUploadError(error);
        }
    },

  handleUploadError(error) {
        console.error('上传文件失败:', error);

        let errorMessage = '上传文件失败';

        if (error.name === 'AbortError') {
            errorMessage = '上传超时，请检查网络连接后重试';
        } else if (error.message) {
            if (error.message.includes('413')) {
                errorMessage = '文件过大，请压缩后重新上传';
            } else if (error.message.includes('415')) {
                errorMessage = '文件格式不支持，请使用Excel或CSV文件';
            } else if (error.message.includes('401')) {
                errorMessage = '登录已过期，请重新登录';
                setTimeout(() => AdminAuth.logout(), 2000);
            } else if (error.message.includes('500')) {
                errorMessage = '服务器内部错误，请稍后重试';
            } else {
                errorMessage = '上传失败: ' + error.message;
            }
        } else if (error.error) {
            errorMessage = error.error;
        }

        AdminUtils.showToast(errorMessage, 'error');

        // 恢复按钮状态
        const uploadBtn = document.getElementById('importConfirmBtn');
        uploadBtn.disabled = false;
        uploadBtn.textContent = '确认导入';

        // 显示重试提示
        this.showRetryOption();
    },

  showRetryOption() {
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            const retryHtml = `
                <div class="retry-message">
                    <p>上传失败，您可以:</p>
                    <button class="btn btn-sm btn-outline" onclick="CalendarPage.retryUpload()">
                        <i class="ri-refresh-line"></i> 重新上传
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="CalendarPage.showImportModal()">
                        <i class="ri-upload-2-line"></i> 选择其他文件
                    </button>
                </div>
            `;

            // 在上传区域后添加重试选项
            let retryContainer = document.querySelector('.retry-container');
            if (!retryContainer) {
                retryContainer = document.createElement('div');
                retryContainer.className = 'retry-container';
                uploadArea.parentNode.insertBefore(retryContainer, uploadArea.nextSibling);
            }
            retryContainer.innerHTML = retryHtml;
        }
    },

  retryUpload() {
        const retryContainer = document.querySelector('.retry-container');
        if (retryContainer) {
            retryContainer.remove();
        }
        this.uploadAndPreview();
    },

    renderImportPreview(data) {
        const container = document.getElementById('importPreviewContainer');
        if (!container) return;

        const { preview, validation_errors, statistics } = data;

        // 显示验证错误
        if (validation_errors && validation_errors.length > 0) {
            const errorsHtml = validation_errors.map(error =>
                `<div class="validation-error">
                    <strong>第${error.row}行:</strong> ${error.field} - ${error.message}
                </div>`
            ).join('');

            document.getElementById('validationErrors').innerHTML = errorsHtml;
        } else {
            document.getElementById('validationErrors').innerHTML =
                '<div class="success-message">✓ 数据验证通过，未发现错误</div>';
        }

        // 显示预览表格
        const tableBody = document.getElementById('previewTableBody');
        if (preview && preview.length > 0) {
            const tableHtml = preview.slice(0, 10).map(event => `
                <tr>
                    <td>${event.title || '-'}</td>
                    <td>${this.getEventTypeText(event.event_type) || '-'}</td>
                    <td>${event.start_date || '-'}</td>
                    <td>${event.location || '-'}</td>
                    <td><span class="priority-badge priority-${event.priority || 'medium'}">${this.getPriorityText(event.priority || 'medium')}</span></td>
                </tr>
            `).join('');

            tableBody.innerHTML = tableHtml;

            if (preview.length > 10) {
                document.getElementById('previewMoreInfo').textContent =
                    `显示前10条，共${preview.length}条记录`;
            }
        } else {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">暂无有效数据</td></tr>';
        }

        // 显示统计信息
        if (statistics) {
            document.getElementById('validRecordsCount').textContent = statistics.valid_records || 0;
            document.getElementById('errorRecordsCount').textContent = statistics.error_records || 0;
            document.getElementById('totalRecordsCount').textContent = statistics.total_records || 0;
        }

        container.style.display = 'block';
    },

    async confirmImport() {
        if (!this.importData.validated || !this.importData.preview) {
            AdminUtils.showToast('请先上传并预览数据', 'error');
            return;
        }

        // 验证预览数据
        if (!this.validateImportData()) {
            return;
        }

        try {
            // 显示加载状态
            const confirmBtn = document.getElementById('importConfirmBtn');
            const originalText = confirmBtn.textContent;
            confirmBtn.disabled = true;
            confirmBtn.textContent = '导入中...';

            // 显示进度指示器
            this.showImportProgress();

            const data = await AdminUtils.request('/calendar/import/confirm', {
                method: 'POST',
                body: JSON.stringify({
                    preview_data: this.importData.preview.preview
                })
            });

            // 恢复按钮状态
            confirmBtn.disabled = false;
            confirmBtn.textContent = '完成导入';

            if (data.success) {
                // 显示导入结果
                this.renderImportResult(data);

                // 切换到步骤3
                this.showImportStep(3);

                // 刷新校历事件列表
                this.loadEvents();
                this.loadStatistics();

                AdminUtils.showToast('数据导入成功', 'success');
            } else {
                this.handleImportError(data);
            }
        } catch (error) {
            this.handleImportError(error);
        }
    },

  validateImportData() {
        const preview = this.importData.preview.preview;

        if (!preview || preview.length === 0) {
            AdminUtils.showToast('没有有效的数据可以导入', 'error');
            return false;
        }

        // 检查必填字段
        const missingRequiredFields = [];
        for (let i = 0; i < preview.length; i++) {
            const event = preview[i];
            if (!event.title) {
                missingRequiredFields.push(`第${i + 2}行: 缺少标题`);
            }
            if (!event.start_date) {
                missingRequiredFields.push(`第${i + 2}行: 缺少开始日期`);
            }
            if (!event.event_type) {
                missingRequiredFields.push(`第${i + 2}行: 缺少事件类型`);
            }
        }

        if (missingRequiredFields.length > 0) {
            AdminUtils.showToast('数据验证失败: ' + missingRequiredFields.slice(0, 3).join('; ') +
                              (missingRequiredFields.length > 3 ? '...' : ''), 'error');
            return false;
        }

        return true;
    },

  showImportProgress() {
        const progressHtml = `
            <div class="import-progress">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-text">正在导入数据，请稍候...</div>
            </div>
        `;

        // 在预览容器中显示进度条
        const previewContainer = document.getElementById('importPreviewContainer');
        const progressContainer = document.createElement('div');
        progressContainer.className = 'import-progress-container';
        progressContainer.innerHTML = progressHtml;
        previewContainer.appendChild(progressContainer);

        // 模拟进度动画
        const progressFill = progressContainer.querySelector('.progress-fill');
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
        }, 200);

        // 保存interval ID以便清理
        this.progressInterval = interval;
    },

  hideImportProgress() {
        const progressContainer = document.querySelector('.import-progress-container');
        if (progressContainer) {
            progressContainer.remove();
        }
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
    },

  handleImportError(error) {
        console.error('导入失败:', error);

        this.hideImportProgress();

        let errorMessage = '导入失败';

        if (error.message) {
            if (error.message.includes('401')) {
                errorMessage = '登录已过期，请重新登录';
                setTimeout(() => AdminAuth.logout(), 2000);
            } else if (error.message.includes('409')) {
                errorMessage = '数据冲突，请检查是否有重复的事件';
            } else if (error.message.includes('422')) {
                errorMessage = '数据格式错误，请检查文件内容';
            } else if (error.message.includes('500')) {
                errorMessage = '服务器内部错误，请稍后重试';
            } else {
                errorMessage = '导入失败: ' + error.message;
            }
        } else if (error.error) {
            errorMessage = error.error;
        }

        AdminUtils.showToast(errorMessage, 'error');

        // 恢复按钮状态
        const confirmBtn = document.getElementById('importConfirmBtn');
        if (confirmBtn) {
            confirmBtn.disabled = false;
            confirmBtn.textContent = '确认导入';
        }

        // 显示详细错误信息
        if (error.details && error.details.length > 0) {
            this.showImportErrorDetails(error.details);
        }
    },

  showImportErrorDetails(details) {
        const errorsHtml = details.map(detail =>
            `<div class="error-detail">
                <strong>${detail.title || '未知事件'}:</strong> ${detail.error}
            </div>`
        ).join('');

        // 在预览容器中显示错误详情
        const previewContainer = document.getElementById('importPreviewContainer');
        const errorContainer = document.createElement('div');
        errorContainer.className = 'import-error-details';
        errorContainer.innerHTML = `
            <h4>导入错误详情:</h4>
            <div class="error-list">${errorsHtml}</div>
            <button class="btn btn-sm btn-outline" onclick="this.parentElement.remove()">
                关闭
            </button>
        `;
        previewContainer.appendChild(errorContainer);
    },

    renderImportResult(data) {
        const container = document.getElementById('importResultContainer');
        if (!container) return;

        const { statistics } = data;

        // 显示导入结果统计
        if (statistics) {
            document.getElementById('importedCount').textContent = statistics.imported_records || 0;
            document.getElementById('skippedCount').textContent = statistics.skipped_records || 0;
            document.getElementById('errorImportCount').textContent = statistics.import_errors || 0;
        }

        // 显示详细结果
        const resultsHtml = [];

        if (data.imported_events && data.imported_events.length > 0) {
            resultsHtml.push('<div class="result-section"><h4>成功导入的事件:</h4><ul>');
            data.imported_events.forEach(event => {
                resultsHtml.push(`<li>${event.title} (${this.getEventTypeText(event.event_type)})</li>`);
            });
            resultsHtml.push('</ul></div>');
        }

        if (data.import_errors_details && data.import_errors_details.length > 0) {
            resultsHtml.push('<div class="result-section error-section"><h4>导入失败的事件:</h4><ul>');
            data.import_errors_details.forEach(error => {
                resultsHtml.push(`<li>${error.title || '未知事件'}: ${error.error}</li>`);
            });
            resultsHtml.push('</ul></div>');
        }

        document.getElementById('importResults').innerHTML = resultsHtml.join('') ||
            '<div class="result-section">无详细信息</div>';

        container.style.display = 'block';
    },

    closeImportModal() {
        const modal = document.getElementById('importModal');
        if (modal) {
            modal.classList.remove('active');
        }
        this.resetImportModal();
    }
};

// UI初始化
const AdminUI = {
    init() {
        this.initSidebar();
        this.initNavigation();
        this.initGlobalSearch();
        this.initLogout();
        this.initModals();
    },

    initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');
        const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
        const sidebarOverlay = document.getElementById('sidebarOverlay');

        // 侧边栏切换
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });

        // 移动端侧边栏切换
        mobileSidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
        });

        // 点击遮罩层关闭侧边栏
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', () => {
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
            });
        }

        // 点击外部关闭移动端侧边栏
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 &&
                !sidebar.contains(e.target) &&
                !mobileSidebarToggle.contains(e.target) &&
                (!sidebarOverlay || !sidebarOverlay.contains(e.target))) {
                sidebar.classList.remove('active');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.remove('active');
                }
            }
        });

        // 点击导航项后自动关闭移动端侧边栏
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('active');
                    if (sidebarOverlay) {
                        sidebarOverlay.classList.remove('active');
                    }
                }
            });
        });
    },

    initNavigation() {
        // 导航点击事件
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const pageName = item.dataset.page;
                AdminPageManager.switchPage(pageName);

                // 移动端关闭侧边栏
                if (window.innerWidth <= 768) {
                    document.getElementById('sidebar').classList.remove('active');
                }
            });
        });
    },

    initGlobalSearch() {
        const searchInput = document.getElementById('globalSearch');
        if (searchInput) {
            searchInput.addEventListener('input', AdminUtils.debounce((e) => {
                const query = e.target.value;
                // 实现全局搜索功能
                console.log('全局搜索:', query);
            }, 500));
        }
    },

    initLogout() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                AdminAuth.logout();
            });
        }
    },

    initModals() {
        // 事件模态框关闭事件
        const eventModal = document.getElementById('eventModal');
        const eventDetailModal = document.getElementById('eventDetailModal');

        // 点击背景关闭模态框
        eventModal?.addEventListener('click', (e) => {
            if (e.target === eventModal) {
                CalendarPage.closeEventModal();
            }
        });

        eventDetailModal?.addEventListener('click', (e) => {
            if (e.target === eventDetailModal) {
                eventDetailModal.classList.remove('active');
            }
        });

        // 关闭按钮事件
        const closeButtons = document.querySelectorAll('.modal-close, .modal-cancel');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    modal.classList.remove('active');
                    if (modal.id === 'eventModal') {
                        CalendarPage.editingEventId = null;
                    }
                }
            });
        });

        // 导入模态框事件
        const importModal = document.getElementById('importModal');
        const importFileInput = document.getElementById('importFileInput');
        const uploadArea = document.getElementById('uploadArea');
        const importConfirmBtn = document.getElementById('importConfirmBtn');
        const importCancelBtn = document.getElementById('importCancelBtn');
        const importCloseBtn = document.getElementById('importCloseBtn');

        // 文件选择事件
        importFileInput?.addEventListener('change', (e) => {
            const file = e.target.files[0];
            CalendarPage.handleFileSelect(file);
        });

        // 拖拽上传事件
        uploadArea?.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea?.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });

        uploadArea?.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            CalendarPage.handleFileSelect(file);
        });

        // 点击上传区域触发文件选择
        uploadArea?.addEventListener('click', () => {
            importFileInput?.click();
        });

        // 确认导入按钮事件
        importConfirmBtn?.addEventListener('click', () => {
            if (CalendarPage.importData.validated) {
                CalendarPage.confirmImport();
            } else {
                CalendarPage.uploadAndPreview();
            }
        });

        // 取消和关闭按钮事件
        importCancelBtn?.addEventListener('click', () => {
            CalendarPage.closeImportModal();
        });

        importCloseBtn?.addEventListener('click', () => {
            CalendarPage.closeImportModal();
        });

        // 点击背景关闭导入模态框
        importModal?.addEventListener('click', (e) => {
            if (e.target === importModal) {
                CalendarPage.closeImportModal();
            }
        });

        // 全局键盘事件
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                eventModal?.classList.remove('active');
                eventDetailModal?.classList.remove('active');
                importModal?.classList.remove('active');
                CalendarPage.editingEventId = null;
            }
        });
    }
};

// 拜访对象管理页面

// 组织管理页面
const OrganizationPage = {
    currentPage: 1,
    rolesPage: 1,
    editingOrgId: null,
    editingRoleId: null,

    // 加载数据
    async load() {
        try {
            console.log('Loading organization page...');
            await this.loadStats();
            await this.loadOrganizations();
            await this.loadRoles();
            this.initEventListeners();
        } catch (error) {
            console.error('Failed to load organization page:', error);
            AdminUtils.showToast('加载组织管理页面失败: ' + error.message, 'error');
        }
    },

    // 加载统计数据
    async loadStats() {
        try {
            const data = await AdminUtils.request('/organization/stats');
            if (data.success) {
                const stats = data.data;
                document.getElementById('totalOrgs').textContent = stats.total_orgs || 0;
                document.getElementById('totalOrgUsers').textContent = stats.total_users || 0;
                document.getElementById('totalOrgRoles').textContent = stats.total_roles || 0;
                document.getElementById('totalOrgTeachers').textContent = stats.total_teachers || 0;
            }
        } catch (error) {
            console.error('Failed to load organization stats:', error);
        }
    },

    // 加载组织列表
    async loadOrganizations(page = 1, filters = {}) {
        try {
            this.currentPage = page;
            const params = new URLSearchParams({
                page: page,
                per_page: 20,
                ...filters
            });

            const data = await AdminUtils.request(`/organization/list?${params}`);
            if (data.success) {
                this.renderOrganizationsTable(data.data.organizations, data.data.pagination);
                document.getElementById('orgTotalCount').textContent = `共 ${data.data.pagination.total} 条记录`;
            }
        } catch (error) {
            console.error('Failed to load organizations:', error);
            const tbody = document.getElementById('organizationsTableBody');
            tbody.innerHTML = '<tr><td colspan="10" class="error">加载组织数据失败: ' + error.message + '</td></tr>';
        }
    },

    // 渲染组织表格
    renderOrganizationsTable(organizations, pagination) {
        const tbody = document.getElementById('organizationsTableBody');

        if (organizations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 20px;">暂无组织数据</td></tr>';
            return;
        }

        let html = '';
        organizations.forEach(org => {
            const userCount = Math.floor(Math.random() * 20) + 1; // 模拟用户数量
            const parentOrg = organizations.find(o => o.id === org.parent_id);

            html += `
                <tr>
                    <td><strong>${org.name}</strong></td>
                    <td>${org.code}</td>
                    <td><span class="org-type-badge org-type-${org.org_type}">${this.getOrgTypeLabel(org.org_type)}</span></td>
                    <td>${org.level}</td>
                    <td>${parentOrg ? parentOrg.name : '无'}</td>
                    <td><span class="status-badge status-${org.status}">${org.status === 'active' ? '启用' : '禁用'}</span></td>
                    <td>${org.contact_person || '-'}</td>
                    <td>${userCount}</td>
                    <td>${new Date(org.created_at).toLocaleDateString()}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-outline" onclick="OrganizationPage.editOrg(${org.id})">
                                <i class="ri-edit-line"></i>
                                编辑
                            </button>
                            <button class="btn btn-sm btn-outline btn-danger" onclick="OrganizationPage.deleteOrg(${org.id})">
                                <i class="ri-delete-bin-line"></i>
                                删除
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
        this.renderPagination('organizationsPagination', pagination, 'loadOrganizations');
    },

    // 加载角色列表
    async loadRoles(page = 1) {
        try {
            this.rolesPage = page;
            const data = await AdminUtils.request('/organization/roles');
            if (data.success) {
                this.renderRolesTable(data.data);
                document.getElementById('rolesTotalCount').textContent = `共 ${data.data.length} 条记录`;
            }
        } catch (error) {
            console.error('Failed to load roles:', error);
            const tbody = document.getElementById('rolesTableBody');
            tbody.innerHTML = '<tr><td colspan="7" class="error">加载角色数据失败: ' + error.message + '</td></tr>';
        }
    },

    // 渲染角色表格
    renderRolesTable(roles) {
        const tbody = document.getElementById('rolesTableBody');

        if (roles.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">暂无角色数据</td></tr>';
            return;
        }

        let html = '';
        roles.forEach(role => {
            let permissions = [];
            try {
                permissions = JSON.parse(role.permissions || '[]');
            } catch (error) {
                console.warn('Failed to parse permissions for role:', role.name, error);
                permissions = [];
            }

            html += `
                <tr>
                    <td><strong>${role.name}</strong></td>
                    <td>${role.display_name}</td>
                    <td>${role.description || '-'}</td>
                    <td>
                        <div class="permissions-list">
                            ${permissions.slice(0, 3).map(perm => `<span class="permission-tag">${this.getPermissionLabel(perm)}</span>`).join('')}
                            ${permissions.length > 3 ? `<span class="permission-more">+${permissions.length - 3}更多</span>` : ''}
                        </div>
                    </td>
                    <td><span class="status-badge status-${role.status}">${role.status === 'active' ? '启用' : '禁用'}</span></td>
                    <td>${new Date(role.created_at).toLocaleDateString()}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-outline" onclick="OrganizationPage.editRole(${role.id})">
                                <i class="ri-edit-line"></i>
                                编辑
                            </button>
                            <button class="btn btn-sm btn-outline btn-danger" onclick="OrganizationPage.deleteRole(${role.id})">
                                <i class="ri-delete-bin-line"></i>
                                删除
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    },

    // 渲染分页
    renderPagination(containerId, pagination, loadFunction) {
        const container = document.getElementById(containerId);

        if (pagination.pages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = '<div class="pagination-controls">';

        // 上一页
        if (pagination.has_prev) {
            html += `<button class="btn btn-sm btn-outline" onclick="OrganizationPage.${loadFunction}(${pagination.page - 1})">上一页</button>`;
        }

        // 页码
        for (let i = Math.max(1, pagination.page - 2); i <= Math.min(pagination.pages, pagination.page + 2); i++) {
            const active = i === pagination.page ? 'active' : '';
            html += `<button class="btn btn-sm ${active}" onclick="OrganizationPage.${loadFunction}(${i})">${i}</button>`;
        }

        // 下一页
        if (pagination.has_next) {
            html += `<button class="btn btn-sm btn-outline" onclick="OrganizationPage.${loadFunction}(${pagination.page + 1})">下一页</button>`;
        }

        html += `<span class="pagination-info">第 ${pagination.page} 页，共 ${pagination.pages} 页</span>`;
        html += '</div>';

        container.innerHTML = html;
    },

    // 添加组织
    addOrg() {
        this.editingOrgId = null;
        document.getElementById('orgModalTitle').textContent = '添加组织';
        document.getElementById('orgForm').reset();
        this.loadParentOrgOptions();
        this.showOrgModal();
    },

    // 编辑组织
    async editOrg(id) {
        try {
            const data = await AdminUtils.request(`/organization/${id}`);
            if (data.success) {
                this.editingOrgId = id;
                const org = data.data.organization;

                document.getElementById('orgModalTitle').textContent = '编辑组织';
                document.getElementById('orgName').value = org.name;
                document.getElementById('orgCode').value = org.code;
                document.getElementById('orgType').value = org.org_type;
                document.getElementById('orgDescription').value = org.description || '';
                document.getElementById('orgStatus').value = org.status;
                document.getElementById('orgSortOrder').value = org.sort_order;
                document.getElementById('orgContactPerson').value = org.contact_person || '';
                document.getElementById('orgContactPhone').value = org.contact_phone || '';
                document.getElementById('orgContactEmail').value = org.contact_email || '';
                document.getElementById('orgAddress').value = org.address || '';

                await this.loadParentOrgOptions(id);
                document.getElementById('orgParentId').value = org.parent_id || '';

                this.showOrgModal();
            }
        } catch (error) {
            console.error('Failed to load organization:', error);
            AdminUtils.showToast('加载组织信息失败: ' + error.message, 'error');
        }
    },

    // 保存组织
    async saveOrg() {
        try {
            const formData = {
                name: document.getElementById('orgName').value,
                code: document.getElementById('orgCode').value,
                org_type: document.getElementById('orgType').value,
                parent_id: document.getElementById('orgParentId').value || null,
                description: document.getElementById('orgDescription').value,
                status: document.getElementById('orgStatus').value,
                sort_order: parseInt(document.getElementById('orgSortOrder').value),
                contact_person: document.getElementById('orgContactPerson').value,
                contact_phone: document.getElementById('orgContactPhone').value,
                contact_email: document.getElementById('orgContactEmail').value,
                address: document.getElementById('orgAddress').value
            };

            let url = '/organization';
            let method = 'POST';

            if (this.editingOrgId) {
                url = `/organization/${this.editingOrgId}`;
                method = 'PUT';
            }

            const response = await AdminUtils.request(url, {
                method,
                body: JSON.stringify(formData)
            });

            if (response.success) {
                AdminUtils.showToast(this.editingOrgId ? '组织更新成功' : '组织创建成功', 'success');
                this.closeOrgModal();
                this.loadOrganizations(this.currentPage, this.getCurrentFilters());
                this.loadStats();
            } else {
                AdminUtils.showToast('操作失败: ' + response.message, 'error');
            }
        } catch (error) {
            console.error('Failed to save organization:', error);
            AdminUtils.showToast('保存组织失败: ' + error.message, 'error');
        }
    },

    // 删除组织
    async deleteOrg(id) {
        if (!confirm('确定要删除这个组织吗？此操作不可恢复。')) {
            return;
        }

        try {
            const response = await AdminUtils.request(`/organization/${id}`, {
                method: 'DELETE'
            });

            if (response.success) {
                AdminUtils.showToast('组织删除成功', 'success');
                this.loadOrganizations(this.currentPage, this.getCurrentFilters());
                this.loadStats();
            } else {
                AdminUtils.showToast('删除失败: ' + response.message, 'error');
            }
        } catch (error) {
            console.error('Failed to delete organization:', error);
            AdminUtils.showToast('删除组织失败: ' + error.message, 'error');
        }
    },

    // 加载父级组织选项
    async loadParentOrgOptions(excludeId = null) {
        try {
            const data = await AdminUtils.request('/organization/list');
            if (data.success) {
                const select = document.getElementById('orgParentId');
                select.innerHTML = '<option value="">无父级组织</option>';

                data.data.organizations.forEach(org => {
                    if (org.id !== excludeId) {
                        const indent = '　'.repeat(org.level - 1);
                        select.innerHTML += `<option value="${org.id}">${indent}${org.name}</option>`;
                    }
                });
            }
        } catch (error) {
            console.error('Failed to load parent org options:', error);
        }
    },

    // 添加角色
    addRole() {
        this.editingRoleId = null;
        document.getElementById('roleModalTitle').textContent = '添加角色';
        document.getElementById('roleForm').reset();
        this.showRoleModal();
    },

    // 编辑角色
    async editRole(id) {
        try {
            const data = await AdminUtils.request(`/organization/roles`);
            if (data.success) {
                const role = data.data.find(r => r.id === id);
                if (role) {
                    this.editingRoleId = id;

                    document.getElementById('roleModalTitle').textContent = '编辑角色';
                    document.getElementById('roleName').value = role.name;
                    document.getElementById('roleDisplayName').value = role.display_name;
                    document.getElementById('roleDescription').value = role.description || '';
                    document.getElementById('roleStatus').value = role.status;

                    // 设置权限复选框
                    const permissions = JSON.parse(role.permissions || '[]');
                    document.querySelectorAll('#permissionsGrid input[type="checkbox"]').forEach(checkbox => {
                        checkbox.checked = permissions.includes(checkbox.value);
                    });

                    this.showRoleModal();
                }
            }
        } catch (error) {
            console.error('Failed to load role:', error);
            AdminUtils.showToast('加载角色信息失败: ' + error.message, 'error');
        }
    },

    // 保存角色
    async saveRole() {
        try {
            const permissions = [];
            document.querySelectorAll('#permissionsGrid input[type="checkbox"]:checked').forEach(checkbox => {
                permissions.push(checkbox.value);
            });

            const formData = {
                name: document.getElementById('roleName').value,
                display_name: document.getElementById('roleDisplayName').value,
                description: document.getElementById('roleDescription').value,
                permissions: JSON.stringify(permissions),
                status: document.getElementById('roleStatus').value
            };

            let method = 'POST';

            if (this.editingRoleId) {
                method = 'PUT';
            }

            const response = await AdminUtils.request('/organization/roles', {
                method,
                body: JSON.stringify(formData)
            });

            if (response.success) {
                AdminUtils.showToast(this.editingRoleId ? '角色更新成功' : '角色创建成功', 'success');
                this.closeRoleModal();
                this.loadRoles();
                this.loadStats();
            } else {
                AdminUtils.showToast('操作失败: ' + response.message, 'error');
            }
        } catch (error) {
            console.error('Failed to save role:', error);
            AdminUtils.showToast('保存角色失败: ' + error.message, 'error');
        }
    },

    // 删除角色
    async deleteRole(id) {
        if (!confirm('确定要删除这个角色吗？此操作不可恢复。')) {
            return;
        }

        try {
            const response = await AdminUtils.request(`/organization/roles/${id}`, {
                method: 'DELETE'
            });

            if (response.success) {
                AdminUtils.showToast('角色删除成功', 'success');
                this.loadRoles();
                this.loadStats();
            } else {
                AdminUtils.showToast('删除失败: ' + response.message, 'error');
            }
        } catch (error) {
            console.error('Failed to delete role:', error);
            AdminUtils.showToast('删除角色失败: ' + error.message, 'error');
        }
    },

    // 显示组织模态框
    showOrgModal() {
        document.getElementById('orgModal').classList.add('active');
    },

    // 关闭组织模态框
    closeOrgModal() {
        document.getElementById('orgModal').classList.remove('active');
        this.editingOrgId = null;
    },

    // 显示角色模态框
    showRoleModal() {
        document.getElementById('roleModal').classList.add('active');
    },

    // 关闭角色模态框
    closeRoleModal() {
        document.getElementById('roleModal').classList.remove('active');
        this.editingRoleId = null;
    },

    // 获取当前筛选条件
    getCurrentFilters() {
        return {
            search: document.getElementById('orgSearch').value,
            org_type: document.getElementById('orgTypeFilter').value,
            status: document.getElementById('orgStatusFilter').value
        };
    },

    // 获取组织类型标签
    getOrgTypeLabel(type) {
        const labels = {
            'school': '学校',
            'campus': '校区',
            'graduation_year': '毕业年份',
            'class': '班级',
            'office': '办公室',
            'club_category': '社团类别',
            'club': '社团',
            'other': '其他'
        };
        return labels[type] || type;
    },

    // 获取权限标签
    getPermissionLabel(permission) {
        const labels = {
            'user_management': '用户管理',
            'org_management': '组织管理',
            'visit_approval': '访问审批',
            'system_settings': '系统设置',
            'data_export': '数据导出',
            'audit_logs': '审计日志',
            'security_monitoring': '安全监控',
            'emergency_contact': '紧急联系',
            'alumni_management': '校友管理',
            'event_management': '活动管理',
            'class_management': '班级管理',
            'student_communication': '学生沟通',
            'profile_management': '资料管理',
            'visit_application': '访问申请',
            'event_registration': '活动报名'
        };
        return labels[permission] || permission;
    },

    // 初始化事件监听器
    initEventListeners() {
        // 刷新数据按钮
        const refreshBtn = document.getElementById('refreshOrgData');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.load();
            });
        }

        // 添加组织按钮
        const addOrgBtn = document.getElementById('addOrgBtn');
        if (addOrgBtn) {
            addOrgBtn.addEventListener('click', () => {
                this.addOrg();
            });
        }

        // 添加角色按钮
        const addRoleBtn = document.getElementById('addRoleBtn');
        if (addRoleBtn) {
            addRoleBtn.addEventListener('click', () => {
                this.addRole();
            });
        }

        // 搜索和筛选
        const searchInput = document.getElementById('orgSearch');
        const typeFilter = document.getElementById('orgTypeFilter');
        const statusFilter = document.getElementById('orgStatusFilter');

        const handleFilter = () => {
            this.loadOrganizations(1, this.getCurrentFilters());
        };

        if (searchInput) searchInput.addEventListener('input', handleFilter);
        if (typeFilter) typeFilter.addEventListener('change', handleFilter);
        if (statusFilter) statusFilter.addEventListener('change', handleFilter);

        // 模态框背景点击关闭
        const orgModal = document.getElementById('orgModal');
        const roleModal = document.getElementById('roleModal');

        if (orgModal) {
            orgModal.addEventListener('click', (e) => {
                if (e.target === orgModal) {
                    this.closeOrgModal();
                }
            });
        }

        if (roleModal) {
            roleModal.addEventListener('click', (e) => {
                if (e.target === roleModal) {
                    this.closeRoleModal();
                }
            });
        }

        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeOrgModal();
                this.closeRoleModal();
            }
        });
    }
};

// 应用初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== Admin Application Initializing ===');

    // 检查认证状态
    const authResult = AdminAuth.initAuth();
    console.log('Auth initialization result:', authResult);

    if (!authResult) {
        console.log('Not authenticated, redirecting to login...');
        // 如果未认证，重定向到登录页面
        window.location.href = '/admin-login';
        return;
    }

    console.log('Authentication successful, initializing UI...');

    // 初始化UI
    AdminUI.init();

    // 加载默认页面
    console.log('Loading default page...');
    AdminPageManager.switchPage(ADMIN_CONFIG.PAGES.DASHBOARD);

    // 初始化导航事件监听器
    document.querySelectorAll('.nav-item[data-page]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const pageName = item.getAttribute('data-page');
            console.log('Navigation clicked:', pageName);
            AdminPageManager.switchPage(pageName);
        });
    });

    // 初始化用户管理页面事件监听器
    UsersPage.initEventListeners();

    // 处理窗口大小变化
    window.addEventListener('resize', AdminUtils.debounce(() => {
        // 响应式处理
        if (window.innerWidth > 768) {
            document.getElementById('sidebar').classList.remove('active');
        }
    }, 250));
});

// 返校日报名统计页面
const EventStatisticsPage = {
    currentPage: 1,
    perPage: 50,
    filters: {
        will_dine: '',
        search: ''
    },
    statistics: null,

    init() {
        this.load();
    },

    async load() {
        await this.loadStatistics();
        await this.loadRegistrations();
        this.bindEvents();
    },

    bindEvents() {
        // 刷新按钮
        const refreshBtn = document.getElementById('refreshEventStats');
        if (refreshBtn) {
            refreshBtn.onclick = () => this.refreshData();
        }

        // 导出按钮
        const exportBtn = document.getElementById('exportEventStats');
        if (exportBtn) {
            exportBtn.onclick = () => this.exportData();
        }

        // 筛选条件
        const diningFilter = document.getElementById('diningFilter');
        if (diningFilter) {
            diningFilter.addEventListener('change', (e) => {
                this.filters.will_dine = e.target.value;
                this.currentPage = 1;
                this.loadRegistrations();
            });
        }

        // 清除筛选按钮
        const clearFiltersBtn = document.getElementById('clearFilters');
        if (clearFiltersBtn) {
            clearFiltersBtn.onclick = () => this.clearFilters();
        }
    },

    async loadStatistics() {
        try {
            const data = await AdminUtils.request('/event/statistics');
            this.statistics = data.statistics;

            this.renderStatistics();
        } catch (error) {
            console.error('加载统计数据失败:', error);
            AdminUtils.showToast('加载统计数据失败', 'error');
        }
    },

    async loadRegistrations() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                ...this.filters
            });

            // 如果有搜索关键词，添加到参数中
            if (this.filters.search) {
                params.set('search', this.filters.search);
            }

            const data = await AdminUtils.request(`/event/registrations?${params}`);

            this.renderRegistrationsTable(data.registrations);
            this.renderPagination(data.pagination);
        } catch (error) {
            console.error('加载报名列表失败:', error);
            AdminUtils.showToast('加载报名列表失败', 'error');
        }
    },

    renderStatistics() {
        if (!this.statistics) return;

        // 更新统计卡片
        const totalElement = document.getElementById('totalRegistrations');
        const diningElement = document.getElementById('diningRegistrations');
        const nonDiningElement = document.getElementById('nonDiningRegistrations');

        if (totalElement) totalElement.textContent = this.statistics.total_registrations;
        if (diningElement) diningElement.textContent = this.statistics.dining_registrations;
        if (nonDiningElement) nonDiningElement.textContent = this.statistics.non_dining_registrations;

        // 渲染菜品统计图表
        this.renderDishChart();
    },

    renderDishChart() {
        if (!this.statistics.dish_statistics || this.statistics.dish_statistics.length === 0) {
            const chartContainer = document.getElementById('dishChartContainer');
            if (chartContainer) {
                chartContainer.innerHTML = '<p class="text-muted">暂无菜品统计数据</p>';
            }
            return;
        }

        const chartContainer = document.getElementById('dishChartContainer');
        if (!chartContainer) return;

        let chartHTML = '<div class="dish-statistics">';

        this.statistics.dish_statistics.forEach((item, index) => {
            const percentage = this.statistics.dining_registrations > 0 ?
                ((item.count / this.statistics.dining_registrations) * 100).toFixed(1) : 0;

            chartHTML += `
                <div class="dish-item">
                    <div class="dish-name">${item.dish}</div>
                    <div class="dish-bar-container">
                        <div class="dish-bar" style="width: ${percentage}%"></div>
                    </div>
                    <div class="dish-count">${item.count} (${percentage}%)</div>
                </div>
            `;
        });

        chartHTML += '</div>';
        chartContainer.innerHTML = chartHTML;
    },

    renderRegistrationsTable(registrations) {
        const tbody = document.getElementById('registrationTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (registrations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 2rem;">暂无报名数据</td></tr>';
            return;
        }

        registrations.forEach((reg, index) => {
            const row = document.createElement('tr');
            const regTime = reg.registration_time ? new Date(reg.registration_time).toLocaleString() : '-';

            // 计算序号 (当前页数-1)*每页数量 + 当前索引 + 1
            const currentPage = this.currentPage || 1;
            const pageSize = this.perPage || 50;
            const serialNumber = (currentPage - 1) * pageSize + index + 1;

            row.innerHTML = `
                <td class="text-center">${serialNumber}</td>
                <td>${reg.username}</td>
                <td>${reg.real_name}</td>
                <td>${reg.contact_phone || '-'}</td>
                <td>
                    <span class="badge ${reg.will_dine ? 'badge-success' : 'badge-secondary'}">
                        ${reg.will_dine ? '就餐' : '不就餐'}
                    </span>
                </td>
                <td>
                    ${reg.will_dine && reg.favorite_dishes ?
                        JSON.parse(reg.favorite_dishes).join(', ') : '-'}
                </td>
                <td class="text-center"><strong>${reg.verification_code || '-'}</strong></td>
                <td>${regTime}</td>
                <td>${reg.notes || '-'}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-outline" onclick="EventStatisticsPage.viewDetails(${reg.id})" title="查看详情">
                            <i class="ri-eye-line"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="EventStatisticsPage.cancelRegistration(${reg.id})" title="取消报名">
                            <i class="ri-close-line"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    },

    renderPagination(pagination) {
        PaginationHelper.renderPaginationWithPerPage(
            'registrationPagination',
            pagination,
            'EventStatisticsPage.goToPage',
            this.perPage
        );
    },

    async refreshData() {
        AdminUtils.showToast('正在刷新数据...', 'info');
        await this.loadStatistics();
        await this.loadRegistrations();
        AdminUtils.showToast('数据刷新成功', 'success');
    },

    async exportData() {
        try {
            // 获取所有数据用于导出
            const allParams = new URLSearchParams({
                page: 1,
                per_page: 1000, // 导出所有数据
                ...this.filters
            });

            const data = await AdminUtils.request(`/event/registrations?${allParams}`);

            // 创建CSV内容
            let csvContent = '\ufeff'; // BOM for UTF-8
            csvContent += '姓名,用户名,联系电话,就餐选择,菜品选择,验证码,备注,报名时间\n';

            data.registrations.forEach(reg => {
                const dishes = reg.will_dine && reg.favorite_dishes ?
                    JSON.parse(reg.favorite_dishes).join(';') : '';
                const notes = reg.notes || '';
                const regTime = reg.registration_time || '';

                csvContent += `"${reg.real_name}","${reg.username}","${reg.contact_phone || ''}",`;
                csvContent += `"${reg.will_dine ? '就餐' : '不就餐'}","${dishes}","${reg.verification_code || ''}","${notes}","${regTime}"\n`;
            });

            // 创建下载链接
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `返校日报名统计_${new Date().toISOString().slice(0, 10)}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            AdminUtils.showToast('数据导出成功', 'success');
        } catch (error) {
            console.error('导出数据失败:', error);
            AdminUtils.showToast('导出数据失败', 'error');
        }
    },

    clearFilters() {
        this.filters = {
            will_dine: '',
            search: ''
        };

        // 重置筛选器UI
        const diningFilter = document.getElementById('diningFilter');

        if (diningFilter) diningFilter.value = '';

        this.currentPage = 1;
        this.loadRegistrations();
        AdminUtils.showToast('筛选条件已清除', 'info');
    },

    viewDetails(registrationId) {
        // 显示报名详情
        AdminUtils.showToast('查看详情功能开发中...', 'info');
    },

    async cancelRegistration(registrationId) {
        if (!confirm('确定要取消这个报名吗？此操作不可恢复。')) {
            return;
        }

        try {
            await AdminUtils.request(`/event/cancel/${registrationId}`, {
                method: 'POST'
            });

            AdminUtils.showToast('报名已取消', 'success');
            await this.loadStatistics();
            await this.loadRegistrations();
        } catch (error) {
            console.error('取消报名失败:', error);
            AdminUtils.showToast('取消报名失败', 'error');
        }
    },

    goToPage(page) {
        this.currentPage = page;
        this.loadRegistrations();
    },

    changePerPage(newPerPage) {
        this.perPage = parseInt(newPerPage);
        this.currentPage = 1;
        this.loadRegistrations();
    }
};

// 问卷管理页面
const SurveyPage = {
    currentPage: 1,
    editingSurveyId: null,
    editingQuestionId: null,
    filters: {
        search: '',
        status: '',
        event_id: ''
    },

    async load() {
        this.bindEvents();
        await this.loadSurveys();
        await this.loadStatistics();
        await this.loadEvents();
    },

    bindEvents() {
        // 创建问卷按钮
        document.getElementById('createSurveyBtn')?.addEventListener('click', () => {
            this.showSurveyModal();
        });
        document.getElementById('addSurveyBtn')?.addEventListener('click', () => {
            this.showSurveyModal();
        });

        // 刷新按钮
        document.getElementById('refreshSurveyList')?.addEventListener('click', () => {
            this.loadSurveys();
            this.loadStatistics();
        });

        // 导出按钮
        document.getElementById('exportSurveysBtn')?.addEventListener('click', () => {
            this.exportSurveys();
        });

        // 批量导入问题按钮
        document.getElementById('importQuestionsBtn')?.addEventListener('click', () => {
            this.showImportModal();
        });

        // 搜索和筛选
        document.getElementById('surveySearch')?.addEventListener('input', AdminUtils.debounce((e) => {
            this.filters.search = e.target.value;
            this.currentPage = 1;
            this.loadSurveys();
        }, 300));

        document.getElementById('surveyStatusFilter')?.addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.currentPage = 1;
            this.loadSurveys();
        });

        document.getElementById('surveyEventFilter')?.addEventListener('change', (e) => {
            this.filters.event_id = e.target.value;
            this.currentPage = 1;
            this.loadSurveys();
        });
    },

    async loadSurveys() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: 20,
                ...this.filters
            });

            const data = await AdminUtils.request(`/survey/surveys?${params}`);

            this.renderSurveysTable(data.surveys);
            this.renderPagination(data.pagination);
            document.getElementById('surveyTotalCount').textContent = `共 ${data.pagination.total} 条记录`;
        } catch (error) {
            console.error('加载问卷列表失败:', error);
            AdminUtils.showToast('加载问卷列表失败', 'error');
        }
    },

    async loadStatistics() {
        try {
            const data = await AdminUtils.request('/survey/surveys?per_page=1000');
            const surveys = data.surveys;

            const totalSurveys = surveys.length;
            const publishedSurveys = surveys.filter(s => s.status === 'published').length;
            const totalResponses = surveys.reduce((sum, s) => sum + s.responses_count, 0);
            const avgCompletionRate = totalSurveys > 0 ?
                Math.round(surveys.reduce((sum, s) => sum + (s.completion_rate || 0), 0) / totalSurveys) : 0;

            document.getElementById('totalSurveys').textContent = totalSurveys;
            document.getElementById('publishedSurveys').textContent = publishedSurveys;
            document.getElementById('totalResponses').textContent = totalResponses;
            document.getElementById('avgCompletionRate').textContent = avgCompletionRate + '%';
        } catch (error) {
            console.error('加载统计信息失败:', error);
        }
    },

    async loadEvents() {
        try {
            const data = await AdminUtils.request('/calendar/events?per_page=1000');
            const select = document.getElementById('surveyEventFilter');
            const modalSelect = document.getElementById('surveyModalEvent');

            if (select) {
                select.innerHTML = '<option value="">全部事件</option>';
                data.events.forEach(event => {
                    select.innerHTML += `<option value="${event.id}">${event.title}</option>`;
                });
            }

            if (modalSelect) {
                modalSelect.innerHTML = '<option value="">请选择事件（可选）</option>';
                data.events.forEach(event => {
                    modalSelect.innerHTML += `<option value="${event.id}">${event.title}</option>`;
                });
            }
        } catch (error) {
            console.error('加载事件列表失败:', error);
        }
    },

    renderSurveysTable(surveys) {
        const tbody = document.getElementById('surveysTableBody');
        tbody.innerHTML = '';

        if (surveys.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem;">暂无问卷数据</td></tr>';
            return;
        }

        surveys.forEach(survey => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="survey-title">
                        <strong>${survey.title}</strong>
                        ${survey.description ? `<br><small class="text-muted">${survey.description.substring(0, 50)}...</small>` : ''}
                    </div>
                </td>
                <td>${survey.event_title || '-'}</td>
                <td>
                    <span class="status-badge status-${survey.status}">
                        ${this.getStatusText(survey.status)}
                    </span>
                </td>
                <td>${survey.questions_count || 0}</td>
                <td>${survey.responses_count || 0}</td>
                <td>${survey.completion_rate || 0}%</td>
                <td>${new Date(survey.created_at).toLocaleDateString()}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-outline" onclick="SurveyPage.viewSurvey(${survey.id})" title="查看">
                            <i class="ri-eye-line"></i>
                        </button>
                        <button class="btn btn-sm btn-primary" onclick="SurveyPage.editSurvey(${survey.id})" title="编辑">
                            <i class="ri-edit-line"></i>
                        </button>
                        <button class="btn btn-sm btn-success" onclick="SurveyPage.viewStatistics(${survey.id})" title="统计">
                            <i class="ri-bar-chart-line"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="SurveyPage.deleteSurvey(${survey.id})" title="删除">
                            <i class="ri-delete-bin-line"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    },

    renderPagination(pagination) {
        const container = document.getElementById('surveyPagination');
        container.innerHTML = '';

        if (pagination.pages <= 1) return;

        const createButton = (page, text, disabled = false) => {
            const button = document.createElement('button');
            button.className = 'pagination-btn';
            if (disabled) button.disabled = true;
            if (page === pagination.page) button.classList.add('active');
            button.textContent = text;
            button.onclick = () => {
                this.currentPage = page;
                this.loadSurveys();
            };
            return button;
        };

        // 上一页
        container.appendChild(createButton(pagination.page - 1, '上一页', !pagination.has_prev));

        // 页码
        for (let i = 1; i <= pagination.pages; i++) {
            if (i === 1 || i === pagination.pages || (i >= pagination.page - 2 && i <= pagination.page + 2)) {
                container.appendChild(createButton(i, i));
            } else if (i === pagination.page - 3 || i === pagination.page + 3) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.className = 'pagination-dots';
                container.appendChild(dots);
            }
        }

        // 下一页
        container.appendChild(createButton(pagination.page + 1, '下一页', !pagination.has_next));
    },

    getStatusText(status) {
        const statusMap = {
            'draft': '草稿',
            'published': '已发布',
            'closed': '已关闭',
            'archived': '已归档'
        };
        return statusMap[status] || status;
    },

    showSurveyModal(surveyId = null) {
        this.editingSurveyId = surveyId;
        const modal = document.getElementById('surveyModal');
        const form = document.getElementById('surveyForm');

        if (surveyId) {
            // 编辑模式 - 加载问卷数据
            this.loadSurveyToForm(surveyId);
        } else {
            // 新建模式 - 重置表单
            form.reset();
            document.getElementById('surveyModalTitle').textContent = '创建问卷';
            document.getElementById('surveyModalQuestions').innerHTML = '';
        }

        modal.classList.add('active');
    },

    async loadSurveyToForm(surveyId) {
        try {
            const data = await AdminUtils.request(`/survey/surveys/${surveyId}`);
            const survey = data.survey;

            document.getElementById('surveyModalTitle').textContent = '编辑问卷';
            document.getElementById('surveyModalTitle').value = survey.title;
            document.getElementById('surveyModalDescription').value = survey.description || '';
            document.getElementById('surveyModalEvent').value = survey.event_id || '';
            document.getElementById('surveyModalStatus').value = survey.status;
            document.getElementById('surveyModalType').value = survey.type || 'custom';
            document.getElementById('surveyModalAnonymous').checked = survey.is_anonymous;
            document.getElementById('surveyModalPublic').checked = survey.is_public;
            document.getElementById('surveyModalRequireLogin').checked = survey.require_login;

            if (survey.start_time) {
                document.getElementById('surveyModalStartTime').value = new Date(survey.start_time).toISOString().slice(0, 16);
            }
            if (survey.end_time) {
                document.getElementById('surveyModalEndTime').value = new Date(survey.end_time).toISOString().slice(0, 16);
            }

            this.renderQuestions(survey.questions || []);
        } catch (error) {
            console.error('加载问卷数据失败:', error);
            AdminUtils.showToast('加载问卷数据失败', 'error');
        }
    },

    renderQuestions(questions) {
        const container = document.getElementById('surveyModalQuestions');
        container.innerHTML = '';

        questions.forEach((question, index) => {
            this.addQuestionToList(question, index);
        });
    },

    addQuestionToList(question, index) {
        const container = document.getElementById('surveyModalQuestions');
        const questionDiv = document.createElement('div');
        questionDiv.className = 'survey-question-item';
        questionDiv.dataset.questionId = question.id || 'new_' + Date.now();

        questionDiv.innerHTML = `
            <div class="question-header">
                <span class="question-number">问题 ${index + 1}</span>
                <div class="question-actions">
                    <button type="button" class="btn btn-sm btn-outline" onclick="SurveyPage.editQuestion('${questionDiv.dataset.questionId}')">
                        <i class="ri-edit-line"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-danger" onclick="SurveyPage.removeQuestion('${questionDiv.dataset.questionId}')">
                        <i class="ri-delete-bin-line"></i>
                    </button>
                </div>
            </div>
            <div class="question-content">
                <strong>类型：</strong>${this.getQuestionTypeText(question.question_type)}<br>
                <strong>内容：</strong>${question.question_text}<br>
                ${question.is_required ? '<span class="required-badge">必答</span>' : '<span class="optional-badge">选答</span>'}
                ${question.options ? `<br><strong>选项：</strong>${question.options.join(', ')}` : ''}
            </div>
        `;

        container.appendChild(questionDiv);
    },

    getQuestionTypeText(type) {
        const typeMap = {
            'single_choice': '单选题',
            'multiple_choice': '多选题',
            'text': '单行文本',
            'textarea': '多行文本',
            'rating': '评分题',
            'number': '数字题'
        };
        return typeMap[type] || type;
    },

    closeSurveyModal() {
        document.getElementById('surveyModal').classList.remove('active');
        this.editingSurveyId = null;
    },

    async saveSurvey() {
        try {
            const formData = {
                title: document.getElementById('surveyModalTitle').value,
                description: document.getElementById('surveyModalDescription').value,
                event_id: document.getElementById('surveyModalEvent').value || null,
                status: document.getElementById('surveyModalStatus').value,
                is_anonymous: document.getElementById('surveyModalAnonymous').checked,
                is_public: document.getElementById('surveyModalPublic').checked,
                require_login: document.getElementById('surveyModalRequireLogin').checked,
                start_time: document.getElementById('surveyModalStartTime').value || null,
                end_time: document.getElementById('surveyModalEndTime').value || null,
                questions: this.collectQuestions()
            };

            if (!formData.title.trim()) {
                AdminUtils.showToast('请输入问卷标题', 'error');
                return;
            }

            let response;
            if (this.editingSurveyId) {
                response = await AdminUtils.request(`/survey/surveys/${this.editingSurveyId}`, {
                    method: 'PUT',
                    body: JSON.stringify(formData)
                });
            } else {
                response = await AdminUtils.request('/survey/surveys', {
                    method: 'POST',
                    body: JSON.stringify(formData)
                });
            }

            AdminUtils.showToast(this.editingSurveyId ? '问卷更新成功' : '问卷创建成功', 'success');
            this.closeSurveyModal();
            this.loadSurveys();
            this.loadStatistics();
        } catch (error) {
            console.error('保存问卷失败:', error);
            AdminUtils.showToast('保存问卷失败', 'error');
        }
    },

    collectQuestions() {
        const questions = [];
        const questionItems = document.querySelectorAll('.survey-question-item');

        questionItems.forEach((item, index) => {
            // 这里需要根据实际的编辑界面来收集问题数据
            // 暂时返回空数组，需要在完善问题编辑功能后实现
        });

        return questions;
    },

    async deleteSurvey(surveyId) {
        if (!confirm('确定要删除这个问卷吗？此操作不可恢复。')) {
            return;
        }

        try {
            await AdminUtils.request(`/survey/surveys/${surveyId}`, {
                method: 'DELETE'
            });

            AdminUtils.showToast('问卷删除成功', 'success');
            this.loadSurveys();
            this.loadStatistics();
        } catch (error) {
            console.error('删除问卷失败:', error);
            AdminUtils.showToast('删除问卷失败', 'error');
        }
    },

    async viewStatistics(surveyId) {
        try {
            const data = await AdminUtils.request(`/survey/surveys/${surveyId}/statistics`);
            this.showStatisticsModal(data);
        } catch (error) {
            console.error('加载统计数据失败:', error);
            AdminUtils.showToast('加载统计数据失败', 'error');
        }
    },

    showStatisticsModal(data) {
        const modal = document.getElementById('surveyStatsModal');
        const content = document.getElementById('surveyStatsContent');

        document.getElementById('statsSurveyTitle').textContent = data.survey.title;
        document.getElementById('statsTotalResponses').textContent = data.total_responses;
        document.getElementById('statsCompletionRate').textContent = data.completion_rate.toFixed(1) + '%';

        // 渲染统计图表
        content.innerHTML = '';
        data.statistics.forEach(stat => {
            const statDiv = document.createElement('div');
            statDiv.className = 'question-statistics';

            if (stat.question_type === 'single_choice' || stat.question_type === 'multiple_choice') {
                statDiv.innerHTML = this.renderChoiceStatistics(stat);
            } else if (stat.question_type === 'rating' || stat.question_type === 'number') {
                statDiv.innerHTML = this.renderNumberStatistics(stat);
            } else {
                statDiv.innerHTML = this.renderTextStatistics(stat);
            }

            content.appendChild(statDiv);
        });

        modal.classList.add('active');
    },

    renderChoiceStatistics(stat) {
        let html = `
            <div class="stat-question">
                <h4>${stat.question_text}</h4>
                <div class="chart-container">
                    <canvas id="chart_${stat.id}" width="400" height="200"></canvas>
                </div>
                <div class="options-summary">
        `;

        Object.entries(stat.option_counts).forEach(([option, count]) => {
            const percentage = ((count / stat.answer_count) * 100).toFixed(1);
            html += `
                <div class="option-stat">
                    <span class="option-label">${option}</span>
                    <div class="option-bar">
                        <div class="option-fill" style="width: ${percentage}%"></div>
                    </div>
                    <span class="option-count">${count} (${percentage}%)</span>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    },

    renderNumberStatistics(stat) {
        return `
            <div class="stat-question">
                <h4>${stat.question_text}</h4>
                <div class="number-stats">
                    <div class="stat-item">
                        <label>平均分：</label>
                        <span class="stat-value">${stat.average?.toFixed(2) || '-'}</span>
                    </div>
                    <div class="stat-item">
                        <label>最高分：</label>
                        <span class="stat-value">${stat.max || '-'}</span>
                    </div>
                    <div class="stat-item">
                        <label>最低分：</label>
                        <span class="stat-value">${stat.min || '-'}</span>
                    </div>
                </div>
            </div>
        `;
    },

    renderTextStatistics(stat) {
        return `
            <div class="stat-question">
                <h4>${stat.question_text}</h4>
                <div class="text-responses">
                    <div class="responses-summary">
                        <span>共 ${stat.answer_count} 个回答</span>
                    </div>
                    <div class="responses-list">
                        ${stat.text_answers?.slice(0, 5).map(answer =>
                            `<div class="response-item">"${answer}"</div>`
                        ).join('') || ''}
                        ${stat.text_answers?.length > 5 ? '<div class="more-responses">...</div>' : ''}
                    </div>
                </div>
            </div>
        `;
    },

    closeStatsModal() {
        document.getElementById('surveyStatsModal').classList.remove('active');
    },

    async exportStats() {
        // 实现统计报告导出功能
        AdminUtils.showToast('导出功能开发中...', 'info');
    },

    addQuestion() {
        this.editingQuestionId = null;
        const modal = document.getElementById('questionModal');
        document.getElementById('questionModalTitle').textContent = '添加问题';
        document.getElementById('questionForm').reset();
        document.getElementById('questionOptions').style.display = 'none';
        document.getElementById('ratingOptions').style.display = 'none';
        modal.classList.add('active');
    },

    onQuestionTypeChange() {
        const type = document.getElementById('questionType').value;
        const optionsDiv = document.getElementById('questionOptions');
        const ratingDiv = document.getElementById('ratingOptions');

        if (type === 'single_choice' || type === 'multiple_choice') {
            optionsDiv.style.display = 'block';
            ratingDiv.style.display = 'none';
            this.initializeOptions();
        } else if (type === 'rating') {
            optionsDiv.style.display = 'none';
            ratingDiv.style.display = 'block';
        } else {
            optionsDiv.style.display = 'none';
            ratingDiv.style.display = 'none';
        }
    },

    initializeOptions() {
        const optionsList = document.getElementById('optionsList');
        optionsList.innerHTML = '';

        // 添加两个默认选项
        this.addOptionInput('选项 1');
        this.addOptionInput('选项 2');
    },

    addOptionInput(value = '') {
        const optionsList = document.getElementById('optionsList');
        const optionDiv = document.createElement('div');
        optionDiv.className = 'option-input';
        optionDiv.innerHTML = `
            <input type="text" placeholder="选项内容" value="${value}" class="option-text">
            <button type="button" class="btn btn-sm btn-danger" onclick="SurveyPage.removeOptionInput(this)">
                <i class="ri-delete-bin-line"></i>
            </button>
        `;
        optionsList.appendChild(optionDiv);
    },

    addQuestionOption() {
        this.addOptionInput();
    },

    removeOptionInput(button) {
        const optionsList = document.getElementById('optionsList');
        if (optionsList.children.length > 2) {
            button.parentElement.remove();
        } else {
            AdminUtils.showToast('至少需要保留两个选项', 'error');
        }
    },

    saveQuestion() {
        const questionData = this.collectQuestionData();
        if (!questionData) return;

        // 添加到问题列表
        this.addQuestionToList(questionData, document.querySelectorAll('.survey-question-item').length);

        this.closeQuestionModal();
        AdminUtils.showToast('问题添加成功', 'success');
    },

    collectQuestionData() {
        const questionText = document.getElementById('questionText').value.trim();
        const questionType = document.getElementById('questionType').value;
        const isRequired = document.getElementById('questionRequired').checked;

        if (!questionText) {
            AdminUtils.showToast('请输入问题内容', 'error');
            return null;
        }

        if (!questionType) {
            AdminUtils.showToast('请选择问题类型', 'error');
            return null;
        }

        const questionData = {
            question_text: questionText,
            question_type: questionType,
            is_required: isRequired,
            order_index: 0
        };

        if (questionType === 'single_choice' || questionType === 'multiple_choice') {
            const options = this.collectOptions();
            if (options.length < 2) {
                AdminUtils.showToast('选择题至少需要两个选项', 'error');
                return null;
            }
            questionData.options = options;
        }

        return questionData;
    },

    collectOptions() {
        const optionInputs = document.querySelectorAll('.option-text');
        const options = [];

        optionInputs.forEach(input => {
            const value = input.value.trim();
            if (value) {
                options.push(value);
            }
        });

        return options;
    },

    closeQuestionModal() {
        document.getElementById('questionModal').classList.remove('active');
        this.editingQuestionId = null;
    },

    showImportModal() {
        const modal = document.getElementById('importQuestionsModal');
        modal.classList.add('active');
    },

    closeImportModal() {
        document.getElementById('importQuestionsModal').classList.remove('active');
    },

    async downloadQuestionTemplate() {
        AdminUtils.showToast('模板下载功能开发中...', 'info');
    },

    async exportSurveys() {
        AdminUtils.showToast('导出功能开发中...', 'info');
    }
};

// 数据库备份页面
const DatabaseBackupPage = {
    currentSettings: {
        maxBackupFiles: 10,
        backupPath: '/var/backups/lsalumni',
        autoBackup: true,
        backupTime: '02:00',
        incrementalBackup: true,
        fullBackupInterval: 7
    },

    init() {
        this.load();
        this.bindEvents();
    },

    async load() {
        await this.loadSettings();
        await this.loadBackupHistory();
        await this.loadScheduleStatus();
    },

    bindEvents() {
        // 绑定备份类型选择事件
        const backupTypeRadios = document.querySelectorAll('input[name="backupType"]');
        backupTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => this.updateBackupTypeLabels());
        });

        // 绑定恢复方式选择事件
        const restoreTypeRadios = document.querySelectorAll('input[name="restoreType"]');
        restoreTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => this.updateRestoreFields());
        });
    },

    async loadSettings() {
        try {
            const data = await AdminUtils.request('/api/api/admin/backup/settings');
            this.currentSettings = data.settings;
            this.renderSettings();
        } catch (error) {
            console.error('加载备份设置失败:', error);
        }
    },

    async loadBackupHistory() {
        try {
            const data = await AdminUtils.request('/api/api/admin/backup/history');
            this.renderBackupHistory(data.history || []);
        } catch (error) {
            console.error('加载备份历史失败:', error);
            this.renderBackupHistory([]);
        }
    },

    async loadScheduleStatus() {
        try {
            const data = await AdminUtils.request('/api/admin/backup/schedule');
            this.renderScheduleStatus(data);
        } catch (error) {
            console.error('加载调度状态失败:', error);
        }
    },

    renderSettings() {
        // 基本设置
        const maxFilesEl = document.getElementById('maxBackupFiles');
        const backupPathEl = document.getElementById('backupPath');
        const autoBackupEl = document.getElementById('autoBackup');
        const backupTimeEl = document.getElementById('backupTime');
        const incrementalBackupEl = document.getElementById('incrementalBackup');
        const fullBackupIntervalEl = document.getElementById('fullBackupInterval');

        if (maxFilesEl) maxFilesEl.value = this.currentSettings.maxBackupFiles;
        if (backupPathEl) backupPathEl.value = this.currentSettings.backupPath;
        if (autoBackupEl) autoBackupEl.checked = this.currentSettings.autoBackup;
        if (backupTimeEl) backupTimeEl.value = this.currentSettings.backupTime;
        if (incrementalBackupEl) incrementalBackupEl.checked = this.currentSettings.incrementalBackup;
        if (fullBackupIntervalEl) fullBackupIntervalEl.value = this.currentSettings.fullBackupInterval;

        this.updateBackupTypeLabels();
    },

    renderScheduleStatus(scheduleData) {
        const statusEl = document.getElementById('scheduleStatus');
        if (!statusEl) return;

        if (scheduleData.auto_backup_enabled) {
            const nextRun = scheduleData.next_run ?
                new Date(scheduleData.next_run).toLocaleString('zh-CN') : '未知';
            statusEl.innerHTML = `
                <span class="status-indicator success"></span>
                自动备份已启用，下次运行时间: ${nextRun}
            `;
        } else {
            statusEl.innerHTML = `
                <span class="status-indicator inactive"></span>
                自动备份已禁用
            `;
        }
    },

    renderBackupHistory(history) {
        const tbody = document.getElementById('backupHistoryTableBody');
        if (!tbody) return;

        if (history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无备份记录</td></tr>';
            return;
        }

        tbody.innerHTML = history.map(backup => {
            const createdTime = backup.created_at_formatted || new Date(backup.created_at).toLocaleString('zh-CN');
            const typeClass = this.getTypeClass(backup.type);
            const sizeFormatted = backup.size_formatted || this.formatFileSize(backup.size || 0);
            const canRestore = backup.type === 'full' || this.canUseIncrementalBackup(backup);

            return `
                <tr>
                    <td>${createdTime}</td>
                    <td><span class="backup-type ${typeClass}">${this.getTypeLabel(backup.type)}</span></td>
                    <td>${sizeFormatted}</td>
                    <td>${backup.base_backup ? '基于: ' + backup.base_backup : '完整备份'}</td>
                    <td>${canRestore ?
                        `<button class="btn btn-sm btn-primary" onclick="DatabaseBackupPage.showRestoreDialog('${backup.filename}')" title="恢复到此备份">
                            <i class="ri-refresh-line"></i> 恢复
                        </button>` :
                        '<span class="text-muted">不可恢复</span>'}
                    </td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-success" onclick="DatabaseBackupPage.downloadBackupFile('${backup.filename}')" title="下载备份文件">
                                <i class="ri-download-line"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="DatabaseBackupPage.deleteBackup('${backup.filename}')" title="删除备份">
                                <i class="ri-delete-bin-line"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    },

    updateBackupTypeLabels() {
        const incrementalEnabled = document.getElementById('incrementalBackup')?.checked;
        const serverLabel = document.querySelector('label[for="serverBackup"]');
        const downloadLabel = document.querySelector('label[for="downloadBackup"]');
        const dualLabel = document.querySelector('label[for="dualBackup"]');

        if (incrementalEnabled && serverLabel) {
            serverLabel.innerHTML = '<input type="radio" id="serverBackup" name="backupType" value="auto" checked> 智能备份 (增量/完整)';
        } else if (serverLabel) {
            serverLabel.innerHTML = '<input type="radio" id="serverBackup" name="backupType" value="auto" checked> 完整备份';
        }
    },

    updateRestoreFields() {
        const restoreType = document.querySelector('input[name="restoreType"]:checked')?.value;
        const fileSection = document.getElementById('restoreFileSection');
        const dateSection = document.getElementById('restoreDateSection');

        if (fileSection) fileSection.style.display = restoreType === 'file' ? 'block' : 'none';
        if (dateSection) dateSection.style.display = restoreType === 'date' ? 'block' : 'none';
    },

    canUseIncrementalBackup(backup) {
        // 检查增量备份是否可用于恢复
        return backup.type === 'incremental' && backup.base_backup;
    },

    getTypeClass(type) {
        const typeMap = {
            'full': 'success',
            'incremental': 'warning',
            'auto': 'primary'
        };
        return typeMap[type] || 'primary';
    },

    getTypeLabel(type) {
        const typeMap = {
            'full': '完整备份',
            'incremental': '增量备份',
            'auto': '智能备份'
        };
        return typeMap[type] || '未知';
    },

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    },

    async createServerBackup() {
        this.setButtonLoading('serverBackupBtn', true);
        try {
            const backupType = document.querySelector('input[name="backupType"]:checked')?.value || 'auto';

            const data = await AdminUtils.request('/api/admin/backup/server', {
                method: 'POST',
                body: JSON.stringify({ type: backupType })
            });

            const backupTypeText = data.backup?.type === 'incremental' ? '增量' : '完整';
            AdminUtils.showToast(`${backupTypeText}备份已创建: ${data.backup?.filename}`, 'success');
            await this.loadBackupHistory();
        } catch (error) {
            console.error('创建服务器备份失败:', error);
            AdminUtils.showToast('创建服务器备份失败: ' + error.message, 'error');
        } finally {
            this.setButtonLoading('serverBackupBtn', false);
        }
    },

    async downloadBackup() {
        this.setButtonLoading('downloadBackupBtn', true);
        try {
            const backupType = document.querySelector('input[name="backupType"]:checked')?.value || 'auto';

            const data = await AdminUtils.request('/api/admin/backup/download', {
                method: 'POST',
                body: JSON.stringify({ type: backupType })
            });

            if (data.download_url) {
                // 创建下载链接
                const link = document.createElement('a');
                link.href = data.download_url;
                link.download = data.filename || `database_backup_${new Date().toISOString().slice(0, 10)}.db`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                AdminUtils.showToast('备份文件下载已开始', 'success');
            }
        } catch (error) {
            console.error('下载备份失败:', error);
            AdminUtils.showToast('下载备份失败: ' + error.message, 'error');
        } finally {
            this.setButtonLoading('downloadBackupBtn', false);
        }
    },

    async createDualBackup() {
        this.setButtonLoading('dualBackupBtn', true);
        try {
            const backupType = document.querySelector('input[name="backupType"]:checked')?.value || 'auto';

            const data = await AdminUtils.request('/api/admin/backup/dual', {
                method: 'POST',
                body: JSON.stringify({ type: backupType })
            });

            AdminUtils.showToast('双重备份已创建', 'success');

            // 如果有下载链接，自动触发下载
            if (data.download_info?.download_url) {
                const link = document.createElement('a');
                link.href = data.download_info.download_url;
                link.download = data.download_info.filename || `database_backup_${new Date().toISOString().slice(0, 10)}.db`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }

            await this.loadBackupHistory();
        } catch (error) {
            console.error('创建双重备份失败:', error);
            AdminUtils.showToast('创建双重备份失败: ' + error.message, 'error');
        } finally {
            this.setButtonLoading('dualBackupBtn', false);
        }
    },

    async downloadBackupFile(filename) {
        try {
            // 直接使用文件下载链接
            const link = document.createElement('a');
            link.href = `/api/admin/backup/download_file/${filename}`;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            AdminUtils.showToast('备份文件下载已开始', 'success');
        } catch (error) {
            console.error('下载备份文件失败:', error);
            AdminUtils.showToast('下载备份文件失败', 'error');
        }
    },

    showRestoreDialog(filename) {
        const modal = document.getElementById('restoreModal');
        if (!modal) return;

        // 设置恢复文件名
        const filenameInput = document.getElementById('restoreFilename');
        if (filenameInput) filenameInput.value = filename;

        // 显示模态框
        modal.style.display = 'block';
        this.updateRestoreFields();
    },

    async restoreDatabase() {
        const restoreType = document.querySelector('input[name="restoreType"]:checked')?.value;

        let restoreData = {};
        if (restoreType === 'file') {
            const filename = document.getElementById('restoreFilename')?.value;
            if (!filename) {
                AdminUtils.showToast('请选择要恢复的备份文件', 'error');
                return;
            }
            restoreData.filename = filename;
        } else if (restoreType === 'date') {
            const targetDate = document.getElementById('restoreTargetDate')?.value;
            if (!targetDate) {
                AdminUtils.showToast('请选择目标恢复日期', 'error');
                return;
            }
            restoreData.targetDate = targetDate;
        }

        // 确认恢复操作
        const confirmMessage = `确定要恢复到${restoreType === 'file' ? restoreData.filename : restoreData.targetDate}吗？此操作将覆盖当前数据库！`;
        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            this.setButtonLoading('confirmRestoreBtn', true);

            const data = await AdminUtils.request('/api/admin/backup/restore', {
                method: 'POST',
                body: JSON.stringify(restoreData)
            });

            AdminUtils.showToast(`数据库已成功恢复: ${data.message}`, 'success');

            // 关闭模态框
            document.getElementById('restoreModal').style.display = 'none';

            // 提示用户刷新页面
            setTimeout(() => {
                if (confirm('数据库恢复完成，是否刷新页面以确保数据同步？')) {
                    window.location.reload();
                }
            }, 1000);

        } catch (error) {
            console.error('恢复数据库失败:', error);
            AdminUtils.showToast('恢复数据库失败: ' + error.message, 'error');
        } finally {
            this.setButtonLoading('confirmRestoreBtn', false);
        }
    },

    async deleteBackup(filename) {
        if (!confirm(`确定要删除备份文件 "${filename}" 吗？此操作不可恢复。`)) {
            return;
        }

        try {
            await AdminUtils.request(`/api/admin/backup/delete/${filename}`, {
                method: 'POST'
            });

            AdminUtils.showToast('备份已删除', 'success');
            await this.loadBackupHistory();
        } catch (error) {
            console.error('删除备份失败:', error);
            AdminUtils.showToast('删除备份失败', 'error');
        }
    },

    async saveSettings() {
        const formData = {
            maxBackupFiles: parseInt(document.getElementById('maxBackupFiles')?.value || 10),
            backupPath: document.getElementById('backupPath')?.value || '/var/backups/lsalumni',
            autoBackup: document.getElementById('autoBackup')?.checked || false,
            backupTime: document.getElementById('backupTime')?.value || '02:00',
            incrementalBackup: document.getElementById('incrementalBackup')?.checked || false,
            fullBackupInterval: parseInt(document.getElementById('fullBackupInterval')?.value || 7)
        };

        // 验证设置
        if (formData.maxBackupFiles < 1 || formData.maxBackupFiles > 50) {
            AdminUtils.showToast('最大备份文件数量必须在1-50之间', 'error');
            return;
        }

        if (formData.fullBackupInterval < 1 || formData.fullBackupInterval > 30) {
            AdminUtils.showToast('完整备份间隔必须在1-30天之间', 'error');
            return;
        }

        try {
            await AdminUtils.request('/api/admin/backup/settings', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            AdminUtils.showToast('备份设置已保存', 'success');
            await this.loadSettings();
            await this.loadScheduleStatus();
        } catch (error) {
            console.error('保存备份设置失败:', error);
            AdminUtils.showToast('保存备份设置失败: ' + error.message, 'error');
        }
    },

    setButtonLoading(buttonId, isLoading) {
        const button = document.getElementById(buttonId);
        if (!button) return;

        if (isLoading) {
            button.disabled = true;
            button.innerHTML = '<span class="backup-loading"></span> 处理中...';
        } else {
            button.disabled = false;
            // 恢复按钮原始文本
            if (buttonId === 'serverBackupBtn') {
                const incrementalEnabled = document.getElementById('incrementalBackup')?.checked;
                button.innerHTML = `<i class="ri-upload-cloud-line"></i> ${incrementalEnabled ? '智能备份' : '服务器备份'}`;
            } else if (buttonId === 'downloadBackupBtn') {
                button.innerHTML = '<i class="ri-download-2-line"></i> 下载备份';
            } else if (buttonId === 'dualBackupBtn') {
                button.innerHTML = '<i class="ri-database-2-line"></i> 双重备份';
            } else if (buttonId === 'confirmRestoreBtn') {
                button.innerHTML = '<i class="ri-refresh-line"></i> 确认恢复';
            }
        }
    }
};

// 密钥管理页面
const KeyManagementPage = {
    API_BASE_URL: '/api/admin/keys',
    autoRotateDays: 30, // 默认30天
    currentPage: 1,
    perPage: 20,

    // 初始化页面
    init() {
        console.log('KeyManagementPage 初始化');
        this.bindEvents();
    },

    // 绑定事件
    bindEvents() {
        const autoRotateSelect = document.getElementById('autoRotateDays');
        if (autoRotateSelect) {
            autoRotateSelect.addEventListener('change', (e) => {
                this.autoRotateDays = parseInt(e.target.value);
                this.updateNextRotateDate();
            });
        }
    },

    // 加载页面数据
    async load() {
        await this.loadKeyStatus();
        await this.loadHistory();
    },

    // 加载密钥状态
    async loadKeyStatus() {
        this.showLoading(true);

        try {
            const response = await fetch(`${this.API_BASE_URL}/status`);
            const result = await response.json();

            if (result.success) {
                this.updateStatusCards(result.data);
            } else {
                this.showAlert('获取密钥状态失败: ' + (result.error || result.message || '未知错误'), true);
            }
        } catch (error) {
            console.error('加载密钥状态失败:', error);
            this.showAlert('网络错误，请检查服务器连接', true);
        } finally {
            this.showLoading(false);
        }
    },

    // 更新状态卡片
    updateStatusCards(data) {
        const electronicCard = data.electronic_card_key;
        const daysSince = electronicCard.days_since_change || 0;
        const needsRotation = electronicCard.needs_rotation;

        // 更新已使用天数
        const daysEl = document.getElementById('electronicCardDays');
        if (daysEl) daysEl.textContent = daysSince + ' 天';

        // 更新状态图标和文本
        const statusIconEl = document.getElementById('electronicCardStatusIcon');
        const statusTextEl = document.getElementById('electronicCardStatusText');

        if (statusIconEl && statusTextEl) {
            if (needsRotation) {
                statusIconEl.className = 'stat-icon red';
                statusTextEl.textContent = '需要更换';
                statusTextEl.style.color = '#dc3545';
            } else {
                statusIconEl.className = 'stat-icon green';
                statusTextEl.textContent = '状态良好';
                statusTextEl.style.color = '#28a745';
            }
        }

        // 更新最后更换时间
        const lastChangedEl = document.getElementById('electronicCardLastChanged');
        if (lastChangedEl) lastChangedEl.textContent = electronicCard.last_changed || '--';

        // 更新下次更换时间
        this.updateNextRotateDate();
    },

    // 更新下次更换时间
    updateNextRotateDate() {
        const lastChangedEl = document.getElementById('electronicCardLastChanged');
        const nextDateEl = document.getElementById('nextRotateDate');

        if (!lastChangedEl || !nextDateEl) return;

        const lastChangedStr = lastChangedEl.textContent;
        if (!lastChangedStr || lastChangedStr === '--') {
            nextDateEl.textContent = '--';
            return;
        }

        if (this.autoRotateDays === 0) {
            nextDateEl.textContent = '已禁用自动更换';
            return;
        }

        // 计算下次更换日期
        const lastChanged = new Date(lastChangedStr);
        const nextRotate = new Date(lastChanged);
        nextRotate.setDate(nextRotate.getDate() + this.autoRotateDays);

        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        nextDateEl.textContent = nextRotate.toLocaleDateString('zh-CN', options);
    },

    // 更换密钥
    async rotateKey(keyType) {
        const keyName = '电子校友卡HMAC密钥';

        if (!confirm(`确定要更换${keyName}吗？\n\n⚠️ 更换后需要重启Flask服务才能生效！\n\n更换密钥后，旧的校友卡将无法验证，请确保所有用户已重新生成。`)) {
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch(`${this.API_BASE_URL}/rotate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    key_type: keyType
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert(`✅ ${keyName}更换成功！\n\n密钥预览: ${result.data.new_key_preview}\n更换时间: ${result.data.changed_at}\n操作人: ${result.data.changed_by}\n\n⚠️ 请重启Flask服务使新密钥生效！`);
                await this.loadKeyStatus();
                await this.loadHistory();
            } else {
                this.showAlert('❌ 更换失败: ' + (result.error || result.message || '未知错误'), true);
            }
        } catch (error) {
            console.error('更换密钥失败:', error);
            this.showAlert('❌ 网络错误，请检查服务器连接', true);
        } finally {
            this.showLoading(false);
        }
    },

    // 加载历史记录
    async loadHistory(page = null) {
        if (page !== null) {
            this.currentPage = page;
        }

        try {
            const response = await fetch(
                `${this.API_BASE_URL}/history?page=${this.currentPage}&per_page=${this.perPage}`
            );
            const result = await response.json();

            if (result.success) {
                this.renderHistory(result.data.history, result.data.pagination);
            } else {
                document.getElementById('keyHistoryBody').innerHTML =
                    '<tr><td colspan="6" class="text-center">加载失败</td></tr>';
            }
        } catch (error) {
            console.error('加载历史失败:', error);
            document.getElementById('keyHistoryBody').innerHTML =
                '<tr><td colspan="6" class="text-center">加载失败</td></tr>';
        }
    },

    // 渲染历史记录
    renderHistory(history, pagination) {
        const tbody = document.getElementById('keyHistoryBody');

        if (!history || history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">暂无历史记录</td></tr>';
            document.getElementById('keyHistoryPagination').innerHTML = '';
            return;
        }

        let html = '';
        history.forEach((record, index) => {
            const keyTypeName = record.key_type === 'electronic_card' ? '电子卡密钥' : 'JWT密钥';
            const serialNumber = (this.currentPage - 1) * this.perPage + index + 1;
            html += `
                <tr>
                    <td class="text-center">${serialNumber}</td>
                    <td>${record.changed_at}</td>
                    <td>${keyTypeName}</td>
                    <td>${record.old_key_preview}</td>
                    <td>${record.new_key_preview}</td>
                    <td>${record.changed_by}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;

        // 渲染分页控件
        this.renderPagination(pagination);
    },

    // 渲染分页控件
    renderPagination(pagination) {
        PaginationHelper.renderPaginationWithPerPage(
            'keyHistoryPagination',
            pagination,
            'KeyManagementPage.loadHistory',
            this.perPage,
            [10, 20, 50]
        );
    },

    // 切换页码
    goToPage(page) {
        this.currentPage = page;
        this.loadHistory();
    },

    // 修改每页显示条数
    changePerPage(newPerPage) {
        this.perPage = parseInt(newPerPage);
        this.currentPage = 1;
        this.loadHistory();
    },

    // 显示提示消息
    showAlert(message, isError = false) {
        const alertDiv = document.getElementById('keyMgmtAlert');
        if (alertDiv) {
            alertDiv.textContent = message;
            alertDiv.className = 'alert alert-' + (isError ? 'error' : 'success');
            alertDiv.style.display = 'block';

            setTimeout(() => {
                alertDiv.style.display = 'none';
            }, 5000);
        }
    },

    // 显示加载状态
    showLoading(show) {
        const loadingDiv = document.getElementById('keyMgmtLoading');
        if (loadingDiv) {
            loadingDiv.style.display = show ? 'block' : 'none';
        }
    }
};

// 通用分页工具类
const PaginationHelper = {
    // 默认每页显示选项
    defaultPerPageOptions: [10, 20, 50, 100],

    // 创建带每页显示条数选择的分页
    renderPaginationWithPerPage(containerId, pagination, loadFunction, currentPerPage = 20, perPageOptions = null) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (pagination.pages <= 1 && pagination.total <= (perPageOptions ? Math.min(...perPageOptions) : 10)) {
            container.innerHTML = '';
            return;
        }

        const options = perPageOptions || this.defaultPerPageOptions;
        let html = '<div class="pagination-wrapper">';

        // 每页显示条数选择
        if (pagination.total > options[0]) {
            html += '<div class="per-page-selector">';
            html += '<label for="perPageSelect">每页显示：</label>';
            html += `<select id="perPageSelect_${containerId}" class="per-page-select" onchange="PaginationHelper.onPerPageChange('${containerId}', this.value, '${loadFunction}')">`;

            for (const option of options) {
                const selected = option == currentPerPage ? 'selected' : '';
                html += `<option value="${option}" ${selected}>${option}条</option>`;
            }

            html += '</select>';
            html += '</div>';
        }

        // 分页控件
        html += '<div class="pagination-controls">';

        // 上一页
        if (pagination.has_prev) {
            html += `<button class="btn btn-sm btn-outline" onclick="${loadFunction}(${pagination.page - 1})">
                <i class="ri-arrow-left-s-line"></i> 上一页
            </button>`;
        }

        // 页码
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);

        if (startPage > 1) {
            html += `<button class="btn btn-sm btn-outline" onclick="${loadFunction}(1)">1</button>`;
            if (startPage > 2) {
                html += '<span class="pagination-ellipsis">...</span>';
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === pagination.page ? 'active' : '';
            html += `<button class="btn btn-sm ${activeClass}" onclick="${loadFunction}(${i})">${i}</button>`;
        }

        if (endPage < pagination.pages) {
            if (endPage < pagination.pages - 1) {
                html += '<span class="pagination-ellipsis">...</span>';
            }
            html += `<button class="btn btn-sm btn-outline" onclick="${loadFunction}(${pagination.pages})">${pagination.pages}</button>`;
        }

        // 下一页
        if (pagination.has_next) {
            html += `<button class="btn btn-sm btn-outline" onclick="${loadFunction}(${pagination.page + 1})">
                下一页 <i class="ri-arrow-right-s-line"></i>
            </button>`;
        }

        html += '</div>';

        // 统计信息
        html += `<div class="pagination-info">
            显示第 ${(pagination.page - 1) * currentPerPage + 1} - ${Math.min(pagination.page * currentPerPage, pagination.total)} 条，共 ${pagination.total} 条记录
        </div>`;

        html += '</div>';

        container.innerHTML = html;
    },

    // 处理每页显示条数变化
    onPerPageChange(containerId, newPerPage, loadFunction) {
        // 获取当前的页面对象并更新per_page设置
        const pageName = this.getPageNameFromContainer(containerId);
        if (pageName && window[pageName]) {
            window[pageName].perPage = parseInt(newPerPage);
            window[pageName].currentPage = 1; // 重置到第一页

            // 调用对应页面的加载函数
            const loadMethodName = this.getLoadMethodName(loadFunction);
            if (loadMethodName && window[pageName][loadMethodName]) {
                window[pageName][loadMethodName]();
            }
        }
    },

    // 根据容器ID获取页面名称
    getPageNameFromContainer(containerId) {
        const mapping = {
            'usersPagination': 'UsersPage',
            'organizationsPagination': 'OrganizationPage',
            'rolesPagination': 'RolesPage',
            'visitApplicationsPagination': 'VisitApplicationsPage',
            'recordsPagination': 'VisitRecordsPage',
            'eventsPagination': 'EventsPage',
            'surveyPagination': 'SurveyPage',
            'registrationPagination': 'EventStatisticsPage',
            'keyHistoryPagination': 'KeyManagementPage'
        };
        return mapping[containerId];
    },

    // 根据load函数字符串获取方法名
    getLoadMethodName(loadFunction) {
        // 提取方法名，例如从 "UsersPage.loadUsers" 提取 "loadUsers"
        const parts = loadFunction.split('.');
        return parts.length > 1 ? parts[1] : parts[0];
    }
};

// 处理网络错误
window.addEventListener('unhandledrejection', (event) => {
    if (event.reason.message && event.reason.message.includes('401')) {
        AdminAuth.logout();
    }
});