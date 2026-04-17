/**
 * PC端管理界面JavaScript
 * 校友入校登记系统管理后台
 */

// 应用配置
const ADMIN_CONFIG = {
    API_BASE_URL: '/api',
    STORAGE_KEYS: {
        TOKEN: 'admin_token',
        USER: 'admin_user'
    },
    PAGES: {
        DASHBOARD: 'dashboard',
        USERS: 'users',
        ALUMNI_APPROVE: 'alumni-approve',
        VISIT_APPLICATIONS: 'visit-applications',
        VISIT_RECORDS: 'visit-records',
        VEHICLES: 'vehicles',
        STATISTICS: 'statistics',
        BATCH_APPROVE: 'batch-approve'
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

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '请求失败');
        }

        return data;
    },

    // 显示Toast提示
    showToast(message, type = 'info') {
        const toast = document.getElementById('adminToast');
        const toastMessage = toast.querySelector('.toast-message');
        const toastIcon = toast.querySelector('.toast-icon');

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
            alumni: '校友',
            teacher: '教师',
            security: '保安',
            admin: '管理员'
        };
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
    }
};

// 认证管理
const AdminAuth = {
    // 初始化认证状态
    initAuth() {
        const token = localStorage.getItem(ADMIN_CONFIG.STORAGE_KEYS.TOKEN);
        const userStr = localStorage.getItem(ADMIN_CONFIG.STORAGE_KEYS.USER);

        if (token && userStr) {
            try {
                AdminState.token = token;
                AdminState.user = JSON.parse(userStr);
                AdminState.isAuthenticated = true;

                // 检查用户是否为管理员
                if (AdminState.user.user_type !== 'admin') {
                    this.logout();
                    return false;
                }

                this.updateUI();
                return true;
            } catch (error) {
                this.logout();
            }
        }
        return false;
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

        window.location.href = '/templates/index.html';
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
            'alumni-approve': '校友审核',
            'visit-applications': '访问申请',
            'visit-records': '访问记录',
            vehicles: '车辆管理',
            statistics: '数据统计',
            'batch-approve': '批量授权'
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
                UsersPage.load();
                break;
            case ADMIN_CONFIG.PAGES.ALUMNI_APPROVE:
                AlumniApprovePage.load();
                break;
            case ADMIN_CONFIG.PAGES.VISIT_APPLICATIONS:
                VisitApplicationsPage.load();
                break;
            case ADMIN_CONFIG.PAGES.VISIT_RECORDS:
                VisitRecordsPage.load();
                break;
            case ADMIN_CONFIG.PAGES.VEHICLES:
                VehiclesPage.load();
                break;
            case ADMIN_CONFIG.PAGES.STATISTICS:
                StatisticsPage.load();
                break;
            case ADMIN_CONFIG.PAGES.BATCH_APPROVE:
                BatchApprovePage.load();
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
            this.initCharts(data.visit_trend, data.purpose_stats);
            this.loadRecentActivity();
        } catch (error) {
            console.error('加载仪表板数据失败:', error);
            AdminUtils.showToast('加载仪表板数据失败', 'error');
        }
    },

    // 更新统计数据
    updateStats(stats) {
        document.getElementById('totalUsers').textContent = stats.total_users || 0;
        document.getElementById('totalAlumni').textContent = stats.total_alumni || 0;
        document.getElementById('todayVisits').textContent = stats.today_visits || 0;
        document.getElementById('pendingCount').textContent =
            (stats.pending_alumni || 0) + (stats.pending_visits || 0) + (stats.pending_vehicles || 0);
    },

    // 初始化图表
    initCharts(visitTrend, purposeStats) {
        // 访问趋势图
        const trendCtx = document.getElementById('visitTrendChart');
        if (trendCtx) {
            if (AdminState.charts.trend) {
                AdminState.charts.trend.destroy();
            }

            AdminState.charts.trend = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: visitTrend.map(item => item.date),
                    datasets: [{
                        label: '访问次数',
                        data: visitTrend.map(item => item.count),
                        borderColor: '#1976d2',
                        backgroundColor: 'rgba(25, 118, 210, 0.1)',
                        tension: 0.4
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
    },

    // 加载用户列表
    async loadUsers() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: 20,
                ...this.filters
            });

            const data = await AdminUtils.request(`/admin/users?${params}`);
            this.renderUsers(data.users);
            this.renderPagination(data.pagination);
        } catch (error) {
            console.error('加载用户列表失败:', error);
            AdminUtils.showToast('加载用户列表失败', 'error');
        }
    },

    // 渲染用户表格
    renderUsers(users) {
        const tbody = document.querySelector('#usersTable tbody');
        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.username}</td>
                <td>${user.real_name}</td>
                <td>${AdminUtils.getUserTypeText(user.user_type)}</td>
                <td>${user.email}</td>
                <td>${user.phone}</td>
                <td><span class="status-badge ${user.status}">${AdminUtils.getStatusText(user.status)}</span></td>
                <td>${AdminUtils.formatDate(user.created_at)}</td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline" onclick="UsersPage.editUser(${user.id})">
                            <i class="ri-edit-line"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="UsersPage.toggleStatus(${user.id}, '${user.status}')">
                            <i class="ri-${user.status === 'active' ? 'disable' : 'enable'}-line"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    },

    // 渲染分页
    renderPagination(pagination) {
        const container = document.getElementById('usersPagination');
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

    // 编辑用户
    editUser(userId) {
        AdminUtils.showToast('编辑用户功能开发中', 'info');
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
    }
};

// 校友审核页面
const AlumniApprovePage = {
    currentPage: 1,

    async load() {
        await this.loadPendingAlumni();
    },

    async loadPendingAlumni() {
        try {
            const data = await AdminUtils.request(`/admin/alumni-approve?page=${this.currentPage}&per_page=20`);
            this.renderAlumniList(data.alumni);
            this.renderPagination(data.pagination);
        } catch (error) {
            console.error('加载待审核校友失败:', error);
            AdminUtils.showToast('加载待审核校友失败', 'error');
        }
    },

    renderAlumniList(alumni) {
        const container = document.getElementById('alumniApproveList');

        if (alumni.length === 0) {
            container.innerHTML = '<p class="text-center text-secondary">暂无待审核的校友申请</p>';
            return;
        }

        container.innerHTML = alumni.map(alumni => `
            <div class="approve-item ${alumni.approval_status}">
                <div class="approve-header">
                    <div class="approve-title">${alumni.user.real_name}</div>
                    <div class="approve-status ${AdminUtils.getStatusClass(alumni.approval_status)}">
                        ${AdminUtils.getStatusText(alumni.approval_status)}
                    </div>
                </div>
                <div class="approve-details">
                    <div class="approve-detail">
                        <label>学号</label>
                        <span>${alumni.student_id}</span>
                    </div>
                    <div class="approve-detail">
                        <label>毕业年份</label>
                        <span>${alumni.graduation_year}</span>
                    </div>
                    <div class="approve-detail">
                        <label>班级</label>
                        <span>${alumni.class_name}</span>
                    </div>
                    <div class="approve-detail">
                        <label>院系</label>
                        <span>${alumni.department}</span>
                    </div>
                    <div class="approve-detail">
                        <label>专业</label>
                        <span>${alumni.major}</span>
                    </div>
                    <div class="approve-detail">
                        <label>手机号</label>
                        <span>${alumni.user.phone}</span>
                    </div>
                </div>
                <div class="approve-actions">
                    <button class="btn btn-outline" onclick="AlumniApprovePage.reject(${alumni.id})">
                        <i class="ri-close-line"></i>
                        拒绝
                    </button>
                    <button class="btn btn-primary" onclick="AlumniApprovePage.approve(${alumni.id})">
                        <i class="ri-check-line"></i>
                        通过
                    </button>
                </div>
            </div>
        `).join('');
    },

    async approve(profileId) {
        AdminUtils.showConfirm('确定要通过该校友的审核吗？', async () => {
            try {
                await AdminUtils.request(`/admin/alumni/${profileId}/approve`, {
                    method: 'POST',
                    body: JSON.stringify({ approve: true })
                });

                AdminUtils.showToast('校友审核通过', 'success');
                this.loadPendingAlumni();
            } catch (error) {
                AdminUtils.showToast('审核操作失败', 'error');
            }
        });
    },

    async reject(profileId) {
        AdminUtils.showConfirm('确定要拒绝该校友的审核吗？', async () => {
            try {
                await AdminUtils.request(`/admin/alumni/${profileId}/approve`, {
                    method: 'POST',
                    body: JSON.stringify({ approve: false })
                });

                AdminUtils.showToast('校友审核已拒绝', 'success');
                this.loadPendingAlumni();
            } catch (error) {
                AdminUtils.showToast('审核操作失败', 'error');
            }
        });
    },

    renderPagination(pagination) {
        // 实现分页逻辑
    }
};

// 访问申请页面
const VisitApplicationsPage = {
    async load() {
        AdminUtils.showToast('访问申请页面功能开发中', 'info');
    }
};

// 访问记录页面
const VisitRecordsPage = {
    async load() {
        AdminUtils.showToast('访问记录页面功能开发中', 'info');
    }
};

// 车辆管理页面
const VehiclesPage = {
    async load() {
        AdminUtils.showToast('车辆管理页面功能开发中', 'info');
    }
};

// 数据统计页面
const StatisticsPage = {
    async load() {
        try {
            const data = await AdminUtils.request('/admin/statistics');
            this.updateStats(data);
            this.initCharts(data);
        } catch (error) {
            console.error('加载统计数据失败:', error);
            AdminUtils.showToast('加载统计数据失败', 'error');
        }
    },

    updateStats(data) {
        document.getElementById('totalApplications').textContent = data.total_applications || 0;
        document.getElementById('approvedApplications').textContent =
            data.application_stats.find(s => s.status === 'approved')?.count || 0;
        // 更新其他统计数据
    },

    initCharts(data) {
        // 实现统计图表
    }
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
        } else if (type === 'department') {
            return [
                { value: '计算机学院', label: '计算机学院' },
                { value: '物理学院', label: '物理学院' },
                { value: '数学学院', label: '数学学院' }
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

// UI初始化
const AdminUI = {
    init() {
        this.initSidebar();
        this.initNavigation();
        this.initGlobalSearch();
        this.initLogout();
    },

    initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');
        const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');

        // 侧边栏切换
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });

        // 移动端侧边栏切换
        mobileSidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });

        // 点击外部关闭移动端侧边栏
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 &&
                !sidebar.contains(e.target) &&
                !mobileSidebarToggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
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
    }
};

// 应用初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查认证状态
    if (!AdminAuth.initAuth()) {
        // 如果未认证，重定向到登录页面
        window.location.href = '/templates/index.html';
        return;
    }

    // 初始化UI
    AdminUI.init();

    // 加载默认页面
    AdminPageManager.switchPage(ADMIN_CONFIG.PAGES.DASHBOARD);

    // 处理窗口大小变化
    window.addEventListener('resize', AdminUtils.debounce(() => {
        // 响应式处理
        if (window.innerWidth > 768) {
            document.getElementById('sidebar').classList.remove('active');
        }
    }, 250));
});

// 处理网络错误
window.addEventListener('unhandledrejection', (event) => {
    if (event.reason.message && event.reason.message.includes('401')) {
        AdminAuth.logout();
    }
});