/**
 * 保安管理端JavaScript
 * 处理保安登录、签到、访客验证等功能
 */

// 应用配置
const SECURITY_CONFIG = {
    API_BASE_URL: '/api/security-portal',
    LOGIN_API: '/api/auth',  // 使用主系统登录API
    PROFILE_API: '/api/users',  // 主系统profile API基础路径
    STORAGE_KEYS: {
        TOKEN: 'security_token',
        USER: 'security_user'
    }
};

// 应用状态
const SecurityState = {
    isAuthenticated: false,
    security: null,
    token: null,
    currentShift: null,
    verificationMode: null,
    currentLogId: null
};

// 搜索状态
const SearchState = {
    query: '',
    results: [],
    isSearching: false
};

// 工具函数
const SecurityUtils = {
    // API请求封装
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (SecurityState.token) {
            defaultOptions.headers['Authorization'] = `Bearer ${SecurityState.token}`;
        }

        // 支持自定义baseUrl
        const baseUrl = options.baseUrl || SECURITY_CONFIG.API_BASE_URL;
        delete options.baseUrl;

        const fullUrl = baseUrl + url;
        console.log('发送请求:', { method: options.method || 'GET', url: fullUrl, body: options.body });

        const response = await fetch(fullUrl, {
            ...defaultOptions,
            ...options
        });
        console.log('响应状态:', response.status, response.statusText);

        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            if (!response.ok) {
                throw new Error(`请求失败 (${response.status})`);
            }
            data = {};
        }

        if (!response.ok) {
            // 特殊处理401认证错误
            if (response.status === 401) {
                // Token过期或无效，自动登出并跳转登录页
                console.warn('Token expired or invalid, logging out...');
                SecurityAuth.logout();
                throw new Error('Authorization token is required');
            }
            throw new Error(data.error || `请求失败 (${response.status})`);
        }

        return data;
    },

    // 显示Toast提示
    showToast(title, message, type = 'info') {
        console.log('显示Toast:', { title, message, type });

        const toast = document.getElementById('toast');
        const toastIcon = document.getElementById('toastIcon');
        const toastTitle = document.getElementById('toastTitle');
        const toastMessage = document.getElementById('toastMessage');

        if (!toast || !toastIcon || !toastTitle || !toastMessage) {
            console.error('Toast元素未找到');
            return;
        }

        // 清除之前的定时器
        if (this.toastTimer) {
            clearTimeout(this.toastTimer);
        }

        // 设置内容
        toastTitle.textContent = title;
        toastMessage.textContent = message;

        // 设置样式和动画
        toast.className = `fixed top-4 right-4 z-50 rounded-lg shadow-xl p-4 flex items-center toast-${type} toast-enter`;

        // 设置图标
        const iconMap = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        toastIcon.textContent = iconMap[type] || iconMap.info;
        toastIcon.className = 'text-2xl mr-3';

        // 显示toast
        toast.classList.remove('hidden');

        // 3秒后自动隐藏
        this.toastTimer = setTimeout(() => {
            toast.classList.remove('toast-enter');
            toast.classList.add('toast-exit');

            setTimeout(() => {
                toast.classList.add('hidden');
                toast.classList.remove('toast-exit');
            }, 300);
        }, 3000);
    },

    // 显示加载状态
    showLoading(text = '处理中...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        loadingText.textContent = text;
        overlay.classList.remove('hidden');
    },

    // 隐藏加载状态
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.classList.add('hidden');
    },

    // 格式化时间
    formatTime(date) {
        const now = new Date();
        const targetDate = new Date(date);
        const isToday = targetDate.toDateString() === now.toDateString();

        if (isToday) {
            // 今天的记录只显示时间
            return targetDate.toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit'
            });
        } else {
            // 非今天的记录显示月日和时间
            return targetDate.toLocaleString('zh-CN', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    },

    // 格式化完整日期时间（用于详情弹窗）
    formatDateTime(date) {
        const targetDate = new Date(date);
        return targetDate.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    },

    // 格式化时长
    formatDuration(startTime, endTime) {
        if (!startTime) return '-';

        const start = new Date(startTime);
        const end = endTime ? new Date(endTime) : new Date();
        const duration = Math.floor((end - start) / 1000 / 60); // 分钟

        const hours = Math.floor(duration / 60);
        const minutes = duration % 60;

        if (hours > 0) {
            return `${hours}小时${minutes}分钟`;
        } else {
            return `${minutes}分钟`;
        }
    },

    // 获取动作类型文本
    getActionTypeText(actionType) {
        const typeMap = {
            'scan_qr': '二维码扫描',
            'face_verify': '人脸识别',
            'manual_entry': '手动输入',
            'grant_access': '允许通行',
            'deny_access': '拒绝通行'
        };
        return typeMap[actionType] || actionType;
    },

    // 获取验证方式文本
    getVerificationMethodText(method) {
        const methodMap = {
            'qr_code': '二维码',
            'face_recognition': '人脸识别',
            'manual': '手动',
            'id_card': '身份证'
        };
        return methodMap[method] || method;
    }
};

// 认证管理
const SecurityAuth = {
    // 登录
    async login(username, password) {
        try {
            SecurityUtils.showLoading('登录中...');
            console.log('尝试登录:', { username, password });

            // 使用主系统登录API
            const data = await SecurityUtils.request('/login', {
                method: 'POST',
                body: JSON.stringify({ username, password }),
                baseUrl: SECURITY_CONFIG.LOGIN_API
            });
            console.log('登录响应:', data);

            // 验证用户类型必须是保安
            if (data.user.user_type !== 'security') {
                throw new Error('无权限访问，此账户不是保安账户');
            }

            // 保存认证信息
            SecurityState.token = data.access_token;
            SecurityState.security = data.user;
            SecurityState.isAuthenticated = true;

            // 保存到本地存储
            localStorage.setItem(SECURITY_CONFIG.STORAGE_KEYS.TOKEN, data.access_token);
            localStorage.setItem(SECURITY_CONFIG.STORAGE_KEYS.USER, JSON.stringify(data.user));

            SecurityUtils.showToast('登录成功', `欢迎，${data.user.real_name}`, 'success');

            // 切换到主页面
            this.showMainPage();

            // 加载保安信息
            await SecurityProfile.loadProfile();

            // 开始更新时间
            TimeManager.startClock();

        } catch (error) {
            console.error('登录错误:', error);
            // 提供更友好的错误信息
            let errorMessage = error.message;
            if (errorMessage.includes('用户名或密码错误')) {
                errorMessage = '用户名或密码错误，请检查输入';
            } else if (errorMessage.includes('无权限访问')) {
                errorMessage = '账户类型错误，此账户不是保安账户';
            } else if (errorMessage.includes('网络')) {
                errorMessage = '网络连接失败，请检查网络设置';
            } else if (!errorMessage) {
                errorMessage = '登录失败，请稍后重试';
            }
            SecurityUtils.showToast('登录失败', errorMessage, 'error');
        } finally {
            SecurityUtils.hideLoading();
        }
    },

    // 登出
    logout() {
        SecurityState.isAuthenticated = false;
        SecurityState.security = null;
        SecurityState.token = null;

        // 清除本地存储
        localStorage.removeItem(SECURITY_CONFIG.STORAGE_KEYS.TOKEN);
        localStorage.removeItem(SECURITY_CONFIG.STORAGE_KEYS.USER);

        // 停止时钟
        TimeManager.stopClock();

        // 停止轮询检查
        AccessLogs.stopPolling();

        // 切换到登录页面
        this.showLoginPage();

        SecurityUtils.showToast('已退出', '您已成功退出系统', 'info');
    },

    // 显示登录页面
    showLoginPage() {
        document.getElementById('loginPage').classList.remove('hidden');
        document.getElementById('mainPage').classList.add('hidden');
    },

    // 显示主页面
    showMainPage() {
        document.getElementById('loginPage').classList.add('hidden');
        document.getElementById('mainPage').classList.remove('hidden');
    },

    // 检查登录状态
    async checkLoginStatus() {
        const token = localStorage.getItem(SECURITY_CONFIG.STORAGE_KEYS.TOKEN);
        const user = localStorage.getItem(SECURITY_CONFIG.STORAGE_KEYS.USER);

        if (token && user) {
            SecurityState.token = token;
            SecurityState.security = JSON.parse(user);

            try {
                // 使用主系统API验证token是否有效
                await SecurityUtils.request('/profile', { baseUrl: SECURITY_CONFIG.PROFILE_API });
                SecurityState.isAuthenticated = true;
                this.showMainPage();
                SecurityProfile.loadProfile();
                TimeManager.startClock();
            } catch (error) {
                // Token无效，清除本地存储
                this.logout();
            }
        } else {
            this.showLoginPage();
        }
    }
};

// 保安信息管理
const SecurityProfile = {
    // 加载保安信息
    async loadProfile() {
        try {
            const data = await SecurityUtils.request('/profile');

            // 更新保安信息
            document.getElementById('securityName').textContent = data.real_name;

            // 更新班次信息
            if (data.current_shift) {
                SecurityState.currentShift = data.current_shift;
                this.updateShiftDisplay(data.current_shift);
            }

            // 加载操作记录
            await AccessLogs.loadLogs();

        } catch (error) {
            SecurityUtils.showToast('加载信息失败', error.message, 'error');
        }
    },

    // 更新班次显示
    updateShiftDisplay(shift) {
        // 更新桌面端状态
        const shiftStatus = document.getElementById('shiftStatus');
        const checkInBtn = document.getElementById('checkInBtn');
        const checkOutBtn = document.getElementById('checkOutBtn');

        // 更新移动端状态
        const shiftStatusMobile = document.getElementById('shiftStatusMobile');
        const checkInBtnMobile = document.getElementById('checkInBtnMobile');
        const checkOutBtnMobile = document.getElementById('checkOutBtnMobile');

        let statusText = '';
        let statusClass = '';

        switch (shift.status) {
            case 'scheduled':
                statusText = '未签到';
                statusClass = 'text-yellow-600';
                checkInBtn.disabled = false;
                checkOutBtn.disabled = true;
                checkInBtnMobile.disabled = false;
                checkOutBtnMobile.disabled = true;
                break;
            case 'checked_in':
                statusText = '工作中';
                statusClass = 'text-green-600';
                checkInBtn.disabled = true;
                checkOutBtn.disabled = false;
                checkInBtnMobile.disabled = true;
                checkOutBtnMobile.disabled = false;
                break;
            case 'checked_out':
                statusText = '已下班';
                statusClass = 'text-gray-600';
                checkInBtn.disabled = true;
                checkOutBtn.disabled = true;
                checkInBtnMobile.disabled = true;
                checkOutBtnMobile.disabled = true;
                break;
            case 'absent':
                statusText = '缺勤';
                statusClass = 'text-red-600';
                checkInBtn.disabled = true;
                checkOutBtn.disabled = true;
                checkInBtnMobile.disabled = true;
                checkOutBtnMobile.disabled = true;
                break;
        }

        // 更新桌面端显示
        if (shiftStatus) {
            shiftStatus.textContent = statusText;
            shiftStatus.className = `text-sm font-medium ${statusClass}`;
        }

        // 更新移动端显示
        if (shiftStatusMobile) {
            shiftStatusMobile.textContent = statusText;
            shiftStatusMobile.className = `font-medium ${statusClass}`;
        }
    },

    // 签到
    async checkIn() {
        try {
            SecurityUtils.showLoading('签到中...');

            const data = await SecurityUtils.request('/shift/check-in', {
                method: 'POST'
            });

            SecurityState.currentShift = data.shift;
            this.updateShiftDisplay(data.shift);

            SecurityUtils.showToast('签到成功', '您已成功签到', 'success');

        } catch (error) {
            SecurityUtils.showToast('签到失败', error.message, 'error');
        } finally {
            SecurityUtils.hideLoading();
        }
    },

    // 签退
    async checkOut() {
        try {
            SecurityUtils.showLoading('签退中...');

            const data = await SecurityUtils.request('/shift/check-out', {
                method: 'POST'
            });

            SecurityState.currentShift = data.shift;
            this.updateShiftDisplay(data.shift);

            SecurityUtils.showToast('签退成功', '您已成功签退', 'success');

        } catch (error) {
            SecurityUtils.showToast('签退失败', error.message, 'error');
        } finally {
            SecurityUtils.hideLoading();
        }
    }
};

// 时间管理
const TimeManager = {
    clockInterval: null,

    startClock() {
        this.updateClock();
        this.clockInterval = setInterval(() => this.updateClock(), 1000);
    },

    stopClock() {
        if (this.clockInterval) {
            clearInterval(this.clockInterval);
            this.clockInterval = null;
        }
    },

    updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('zh-CN', { hour12: false });
        const dateString = now.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long'
        });

        // 更新桌面端时间
        const currentTimeElement = document.getElementById('currentTime');
        if (currentTimeElement) {
            currentTimeElement.textContent = timeString;
        }

        // 更新移动端时间
        const currentTimeMobileElement = document.getElementById('currentTimeMobile');
        if (currentTimeMobileElement) {
            currentTimeMobileElement.textContent = timeString;
        }

        // 更新日期
        const todayDateElement = document.getElementById('todayDate');
        if (todayDateElement) {
            todayDateElement.textContent = dateString;
        }
    }
};

// 访客验证
const VisitorVerification = {
    currentMode: null,
    qrCameraStream: null,
    faceCameraStream: null,
    qrData: null, // 存储扫描到的二维码数据

    // 初始化验证模式
    init() {
        // 绑定验证模式按钮
        document.getElementById('qrScanBtn').addEventListener('click', () => {
            this.showVerificationMode('qr');
        });

        document.getElementById('faceScanBtn').addEventListener('click', () => {
            this.showVerificationMode('face');
        });

        // 绑定二维码扫描按钮
        document.getElementById('openCameraBtn').addEventListener('click', () => {
            this.showCameraScanArea();
        });

        document.getElementById('uploadImageBtn').addEventListener('click', () => {
            this.showImageUploadArea();
        });

        // 绑定相机控制按钮
        document.getElementById('startCameraBtn').addEventListener('click', () => {
            this.startQRCamera();
        });

        document.getElementById('captureQrBtn').addEventListener('click', () => {
            this.captureQRCode();
        });

        document.getElementById('stopCameraBtn').addEventListener('click', () => {
            this.stopQRCamera();
        });

        // 绑定图片上传按钮
        document.getElementById('selectImageBtn').addEventListener('click', () => {
            document.getElementById('qrImageInput').click();
        });

        document.getElementById('qrImageInput').addEventListener('change', (e) => {
            this.handleImageUpload(e);
        });

        document.getElementById('reselectImageBtn').addEventListener('click', () => {
            this.resetImageUpload();
        });

        
        // 绑定人脸识别按钮
        document.getElementById('startFaceScanBtn').addEventListener('click', () => {
            this.startFaceScan();
        });

        
        // 支持拖拽上传
        this.setupDragAndDrop();
    },

    // 设置拖拽上传
    setupDragAndDrop() {
        const uploadArea = document.querySelector('#imageUploadArea .border-dashed');
        if (uploadArea) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                }, false);
            });

            uploadArea.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.processImageFile(files[0]);
                }
            }, false);
        }
    },

    // 显示相机扫描区域
    showCameraScanArea() {
        this.hideAllScanAreas();
        document.getElementById('cameraScanArea').classList.remove('hidden');
        document.getElementById('cameraScanArea').classList.add('fade-in');
    },

    // 显示图片上传区域
    showImageUploadArea() {
        this.hideAllScanAreas();
        document.getElementById('imageUploadArea').classList.remove('hidden');
        document.getElementById('imageUploadArea').classList.add('fade-in');
    },

  
    // 隐藏所有扫描区域
    hideAllScanAreas() {
        document.getElementById('cameraScanArea').classList.add('hidden');
        document.getElementById('imageUploadArea').classList.add('hidden');
        document.getElementById('qrScanResult').classList.add('hidden');
        this.stopQRCamera();
    },

    // 启动二维码相机
    async startQRCamera() {
        try {
            const video = document.getElementById('qrCameraVideo');
            this.qrCameraStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });
            video.srcObject = this.qrCameraStream;
            video.style.display = 'block';
            video.classList.add('active');
            video.play();

            document.getElementById('startCameraBtn').classList.add('hidden');
            document.getElementById('captureQrBtn').disabled = false;
            document.getElementById('stopCameraBtn').classList.remove('hidden');

            // 开始扫描二维码
            this.startQRScanning();

        } catch (error) {
            console.error('相机启动失败:', error);
            SecurityUtils.showToast('相机错误', '无法访问相机，请检查权限设置', 'error');
        }
    },

    // 停止二维码相机
    stopQRCamera() {
        // 停止扫描定时器
        if (this.qrScanInterval) {
            clearInterval(this.qrScanInterval);
            this.qrScanInterval = null;
        }

        if (this.qrCameraStream) {
            this.qrCameraStream.getTracks().forEach(track => track.stop());
            this.qrCameraStream = null;
        }
        const video = document.getElementById('qrCameraVideo');
        video.style.display = 'none';
        video.classList.remove('active');
        video.srcObject = null;

        document.getElementById('startCameraBtn').classList.remove('hidden');
        document.getElementById('captureQrBtn').disabled = true;
        document.getElementById('stopCameraBtn').classList.add('hidden');
    },

    // 开始二维码扫描
    startQRScanning() {
        const video = document.getElementById('qrCameraVideo');
        const canvas = document.getElementById('qrCameraCanvas');
        const context = canvas.getContext('2d');

        // 清除之前的扫描定时器
        if (this.qrScanInterval) {
            clearInterval(this.qrScanInterval);
        }

        const scan = () => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);

                const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(imageData.data, imageData.width, imageData.height);

                if (code) {
                    this.processQRCode(code.data);
                    return;
                }
            }
        };

        // 使用定时器控制扫描频率，每100ms扫描一次（10fps），减少性能消耗
        this.qrScanInterval = setInterval(scan, 100);
        scan(); // 立即执行第一次扫描
    },

    // 拍摄二维码
    captureQRCode() {
        const video = document.getElementById('qrCameraVideo');
        const canvas = document.getElementById('qrCameraCanvas');
        const context = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, imageData.width, imageData.height);

        if (code) {
            this.processQRCode(code.data);
        } else {
            SecurityUtils.showToast('识别失败', '未检测到二维码，请重新拍照', 'warning');
        }
    },

    // 处理图片上传
    handleImageUpload(event) {
        const file = event.target.files[0];
        if (file) {
            this.processImageFile(file);
        }
    },

    // 处理图片文件
    processImageFile(file) {
        if (!file.type.startsWith('image/')) {
            SecurityUtils.showToast('文件错误', '请选择图片文件', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                // 显示预览
                document.getElementById('qrPreviewImg').src = e.target.result;
                document.getElementById('qrImagePreview').classList.remove('hidden');

                // 尝试识别二维码
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.width = img.width;
                canvas.height = img.height;
                context.drawImage(img, 0, 0);

                const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(imageData.data, imageData.width, imageData.height);

                if (code) {
                    this.processQRCode(code.data);
                } else {
                    SecurityUtils.showToast('识别失败', '图片中未检测到二维码', 'warning');
                }
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    },

    // 重置图片上传
    resetImageUpload() {
        document.getElementById('qrImageInput').value = '';
        document.getElementById('qrImagePreview').classList.add('hidden');
        document.getElementById('qrPreviewImg').src = '';
        document.getElementById('qrScanResult').classList.add('hidden');
    },

    // 处理二维码数据
    processQRCode(qrData) {
        try {
            // 尝试解析JSON格式的二维码数据
            let data;
            try {
                data = JSON.parse(qrData);
            } catch (e) {
                // 如果不是JSON格式，假设是申请ID
                const applicationId = parseInt(qrData);
                if (!isNaN(applicationId) && applicationId > 0) {
                    this.storeQRData(applicationId);
                    return;
                }
                throw new Error('无效的二维码格式');
            }

            if (data.type === 'visit_application' && data.id) {
                this.storeQRData(data.id);
            } else {
                throw new Error('二维码不是有效的访问申请');
            }

        } catch (error) {
            SecurityUtils.showToast('二维码错误', error.message, 'error');
        }
    },

    // 存储二维码数据并提示输入验证码
    storeQRData(applicationId) {
        this.qrData = applicationId;
        this.showQRScanResult(`申请编号: ${applicationId} - 请输入验证码`);

        // 聚焦到验证码输入框
        document.getElementById('verificationCodeInput').focus();

        SecurityUtils.showToast('扫码成功', `已识别申请编号 ${applicationId}，请输入验证码完成验证`, 'success');
    },

    // 验证申请ID
    async verifyApplicationId(applicationId) {
        try {
            // 获取验证码
            const verificationCode = document.getElementById('verificationCodeInput').value.trim();

            if (!verificationCode) {
                SecurityUtils.showToast('验证码缺失', '请输入验证码', 'warning');
                return;
            }

            if (verificationCode.length !== 6) {
                SecurityUtils.showToast('验证码错误', '请输入6位验证码', 'warning');
                return;
            }

            SecurityUtils.showLoading('验证中...');

            const data = await SecurityUtils.request('/visit/verify-qr', {
                method: 'POST',
                body: JSON.stringify({
                    application_id: applicationId,
                    verification_code: verificationCode
                })
            });

            // 显示识别结果
            this.showQRScanResult(`申请编号: ${applicationId} - 验证成功`);

            SecurityState.currentLogId = data.log_id;
            this.showVerificationResult(data);

        } catch (error) {
            this.showQRScanResult(`申请编号: ${applicationId} - ${error.message}`);
            SecurityUtils.showToast('验证失败', error.message, 'error');
        } finally {
            SecurityUtils.hideLoading();
        }
    },

    // 显示二维码扫描结果
    showQRScanResult(text) {
        document.getElementById('qrScanResultText').textContent = text;
        document.getElementById('qrScanResult').classList.remove('hidden');
        document.getElementById('qrScanResult').classList.add('fade-in');
    },

    // 显示验证模式
    showVerificationMode(mode) {
        // 隐藏所有验证区域
        document.querySelectorAll('.verification-section').forEach(section => {
            section.classList.add('hidden');
        });

        // 显示选中的验证区域
        const sectionMap = {
            'qr': 'qrScanSection',
            'face': 'faceScanSection'
        };

        const section = document.getElementById(sectionMap[mode]);
        if (section) {
            section.classList.remove('hidden');
            section.classList.add('active', 'fade-in');
        }

        this.currentMode = mode;

        // 如果是人脸识别模式，初始化摄像头
        if (mode === 'face') {
            this.initCamera();
        } else {
            this.stopCamera();
        }
    },

    
    // 初始化摄像头
    async initCamera() {
        try {
            const video = document.getElementById('faceVideo');
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            });

            video.srcObject = stream;
            video.style.display = 'block';
            video.classList.add('active');
            video.play();

        } catch (error) {
            console.error('摄像头初始化失败:', error);
            SecurityUtils.showToast('摄像头错误', '无法访问摄像头，请检查权限设置', 'error');
        }
    },

    // 停止摄像头
    stopCamera() {
        const video = document.getElementById('faceVideo');
        if (video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
            video.srcObject = null;
            video.style.display = 'none';
            video.classList.remove('active');
        }
    },

    // 开始人脸扫描
    async startFaceScan() {
        try {
            SecurityUtils.showLoading('人脸识别中...');

            const video = document.getElementById('faceVideo');
            const canvas = document.getElementById('faceCanvas');
            const context = canvas.getContext('2d');

            // 设置canvas尺寸
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            // 捕获当前帧
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            // 转换为base64
            const imageData = canvas.toDataURL('image/jpeg', 0.8);

            // 发送人脸图像到后端进行比对
            const data = await SecurityUtils.request('/visit/verify-face-match', {
                method: 'POST',
                body: JSON.stringify({
                    image_data: imageData,
                    match_today_applications: true  // 启用与当日申请比对
                })
            });

            if (data.matches && data.matches.length > 0) {
                // 找到匹配的申请，显示选择界面
                this.showFaceMatchResults(data.matches);
            } else {
                // 没有找到匹配，提示用户
                this.showNoMatchMessage();
            }

        } catch (error) {
            SecurityUtils.showToast('人脸识别失败', error.message, 'error');
            this.showNoMatchMessage();
        } finally {
            SecurityUtils.hideLoading();
        }
    },

    // 显示人脸匹配结果
    showFaceMatchResults(matches) {
        const resultDiv = document.getElementById('verificationResult');
        resultDiv.classList.remove('hidden');

        resultDiv.innerHTML = `
            <div class="bg-green-50 border border-green-200 rounded-lg p-6 fade-in">
                <div class="flex items-center mb-4">
                    <i class="bi bi-person-check-fill text-green-600 text-2xl mr-3"></i>
                    <h3 class="text-lg font-semibold text-green-800">
                        找到匹配的访问申请 (${matches.length}个)
                    </h3>
                </div>
                <p class="text-green-700 mb-4">请选择正确的访客信息进行验证：</p>

                <div class="space-y-3">
                    ${matches.map((match, index) => `
                        <div class="bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                             onclick="VisitorVerification.selectMatchedApplication(${match.id})">
                            <div class="flex items-center justify-between">
                                <div>
                                    <p class="font-medium text-gray-900">${match.visitor_info?.name || '未填写'}</p>
                                    <p class="text-sm text-gray-600">申请编号: ${match.id}</p>
                                    <p class="text-sm text-gray-600">访问时间: ${match.visit_time_start} - ${match.visit_time_end}</p>
                                    <p class="text-sm text-gray-600">访问目的: ${match.visit_purpose}</p>
                                </div>
                                <div class="text-right">
                                    <span class="inline-block px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">
                                        匹配度: ${match.match_score}%
                                    </span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div class="flex justify-center mt-4">
                    <button onclick="VisitorVerification.clearResult()"
                            class="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors">
                        <i class="bi bi-arrow-clockwise mr-2"></i>
                        重新扫描
                    </button>
                </div>
            </div>
        `;
    },

    // 显示无匹配消息
    showNoMatchMessage() {
        const resultDiv = document.getElementById('verificationResult');
        resultDiv.classList.remove('hidden');

        resultDiv.innerHTML = `
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 fade-in">
                <div class="flex items-center mb-4">
                    <i class="bi bi-person-x text-yellow-600 text-2xl mr-3"></i>
                    <h3 class="text-lg font-semibold text-yellow-800">
                        未找到匹配的访问申请
                    </h3>
                </div>
                <p class="text-yellow-700 mb-4">
                    拍摄的人脸照片与今日访问申请不匹配，可能原因：
                </p>
                <ul class="text-sm text-yellow-700 mb-4 list-disc list-inside">
                    <li>访客尚未提交访问申请</li>
                    <li>访客未注册人脸信息</li>
                    <li>照片质量不佳或角度不正确</li>
                    <li>申请的访问日期不是今天</li>
                </ul>

                <div class="flex justify-center space-x-3">
                    <button onclick="VisitorVerification.retryFaceScan()"
                            class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                        <i class="bi bi-arrow-clockwise mr-2"></i>
                        重新拍摄
                    </button>
                    <button onclick="VisitorVerification.showOtherVerificationMethods()"
                            class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                        <i class="bi bi-list-ul mr-2"></i>
                        其他验证方式
                    </button>
                </div>
            </div>
        `;
    },

    // 选择匹配的申请
    async selectMatchedApplication(applicationId) {
        try {
            SecurityUtils.showLoading('验证申请信息...');

            const data = await SecurityUtils.request('/visit/verify-qr', {
                method: 'POST',
                body: JSON.stringify({ application_id: applicationId })
            });

            SecurityState.currentLogId = data.log_id;
            this.showVerificationResult(data);

        } catch (error) {
            SecurityUtils.showToast('验证失败', error.message, 'error');
        } finally {
            SecurityUtils.hideLoading();
        }
    },

    // 重新人脸扫描
    retryFaceScan() {
        this.clearResult();
        // 重新启动人脸识别模式
        setTimeout(() => {
            this.showVerificationMode('face');
        }, 100);
    },

    // 显示其他验证方式
    showOtherVerificationMethods() {
        this.clearResult();
        SecurityUtils.showToast('提示', '请使用二维码扫描或手动输入申请编号', 'info');

        // 自动切换到二维码扫描模式
        setTimeout(() => {
            this.showVerificationMode('qr');
        }, 1500);
    },

    
    // 显示验证结果
    showVerificationResult(data) {
        const resultDiv = document.getElementById('verificationResult');

        if (data.valid && data.application) {
            // 检查是否有接待人
            const hasHost = data.application.target_person && data.application.target_person !== '未指定' && data.application.target_person !== '';

            if (!hasHost) {
                // 显示无接待人的错误信息
                resultDiv.innerHTML = `
                    <div class="visitor-info-card invalid rounded-lg p-6 fade-in">
                        <div class="flex items-center mb-4">
                            <i class="bi bi-exclamation-triangle-fill text-yellow-600 text-2xl mr-3"></i>
                            <h3 class="text-xl font-semibold text-yellow-800">验证失败</h3>
                        </div>
                        <p class="text-yellow-700 mb-4">该访客申请没有指定接待人，按照规定必须有接待人确认方可入校。</p>
                        <p class="text-sm text-gray-600 mb-4">请访客联系相关部门指定接待人后重新申请。</p>
                        <div class="flex justify-center">
                            <button onclick="VisitorVerification.clearResult()"
                                    class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold">
                                <i class="bi bi-arrow-clockwise mr-2"></i>
                                重新验证
                            </button>
                        </div>
                    </div>
                `;
            } else {
                // 显示有效访客信息
                resultDiv.innerHTML = `
                    <div class="visitor-info-card valid rounded-lg p-6 fade-in">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-xl font-semibold text-green-800">
                                <i class="bi bi-check-circle-fill mr-2"></i>
                                访客信息验证通过
                            </h3>
                            <span class="status-badge checked-in">有效访问</span>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                            <div>
                                <p class="text-sm text-gray-600">访客姓名</p>
                                <p class="font-medium text-gray-900">${data.application.visitor_info?.name || '未填写'}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">联系电话</p>
                                <p class="font-medium text-gray-900">${data.application.visitor_info?.phone || '未填写'}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">访问日期</p>
                                <p class="font-medium text-gray-900">${data.application.visit_date}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">访问时间</p>
                                <p class="font-medium text-gray-900">${data.application.visit_time_start} - ${data.application.visit_time_end}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">访问目的</p>
                                <p class="font-medium text-gray-900">${data.application.visit_purpose}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">接待人</p>
                                <p class="font-medium text-gray-900">${data.application.target_person}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">被访部门</p>
                                <p class="font-medium text-gray-900">${data.application.target_department || '未填写'}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">申请时间</p>
                                <p class="font-medium text-gray-900">${SecurityUtils.formatTime(data.application.created_at)}</p>
                            </div>
                        </div>

                        <div class="flex justify-center space-x-4">
                            <button onclick="AccessControl.grantAccess(${data.application.id})"
                                    class="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-semibold">
                                <i class="bi bi-check-circle mr-2"></i>
                                允许进入
                            </button>
                            <button onclick="AccessControl.denyAccess(${data.application.id})"
                                    class="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors font-semibold">
                                <i class="bi bi-x-circle mr-2"></i>
                                拒绝进入
                            </button>
                            <button onclick="VisitorVerification.clearResult()"
                                    class="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors font-semibold">
                                <i class="bi bi-arrow-clockwise mr-2"></i>
                                重新验证
                            </button>
                        </div>
                    </div>
                `;
            }
        } else {
            // 显示验证失败信息
            resultDiv.innerHTML = `
                <div class="visitor-info-card invalid rounded-lg p-6 fade-in">
                    <div class="flex items-center mb-4">
                        <i class="bi bi-x-circle-fill text-red-600 text-2xl mr-3"></i>
                        <h3 class="text-xl font-semibold text-red-800">验证失败</h3>
                    </div>
                    <p class="text-red-700 mb-4">${data.error || '验证过程中发生错误'}</p>
                    <div class="flex justify-center">
                        <button onclick="VisitorVerification.clearResult()"
                                class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold">
                            <i class="bi bi-arrow-clockwise mr-2"></i>
                            重新验证
                        </button>
                    </div>
                </div>
            `;
        }

        resultDiv.classList.remove('hidden');
        resultDiv.scrollIntoView({ behavior: 'smooth' });
    },

    
    // 清除验证结果
    clearResult() {
        document.getElementById('verificationResult').classList.add('hidden');
        // 清空验证码
        document.getElementById('verificationCodeInput').value = '';
        // 清除二维码数据
        this.qrData = null;
        // 隐藏扫描结果
        document.getElementById('qrScanResult').classList.add('hidden');
    }
};

// 访问控制
const AccessControl = {
    // 允许进入
    async grantAccess(applicationId) {
        try {
            SecurityUtils.showLoading('处理中...');

            const notes = prompt('请输入备注信息（可选）:');

            const data = await SecurityUtils.request('/visit/grant-access', {
                method: 'POST',
                body: JSON.stringify({
                    application_id: applicationId,
                    log_id: SecurityState.currentLogId,
                    notes: notes || ''
                })
            });

            SecurityUtils.showToast('放行成功', '访客已允许进入', 'success');
            VisitorVerification.clearResult();

            // 刷新操作记录
            await AccessLogs.loadLogs();

        } catch (error) {
            SecurityUtils.showToast('放行失败', error.message, 'error');
        } finally {
            SecurityUtils.hideLoading();
        }
    },

    
    // 拒绝进入
    async denyAccess(applicationId) {
        try {
            const reason = prompt('请输入拒绝理由:');
            if (!reason) return;

            SecurityUtils.showLoading('处理中...');

            // 这里可以添加拒绝访问的API调用
            SecurityUtils.showToast('操作成功', '已拒绝访客进入', 'info');
            VisitorVerification.clearResult();

        } catch (error) {
            SecurityUtils.showToast('操作失败', error.message, 'error');
        } finally {
            SecurityUtils.hideLoading();
        }
    }
};

// 操作记录管理
const AccessLogs = {
    currentFilter: null, // 当前筛选类型: 'granted', 'denied', 'pending', 'all'
    lastLogCount: 0, // 记录上次访问记录的数量
    pollingInterval: null, // 轮询定时器
    lastScrollTop: 0, // 记录上次滚动位置
    isRefreshing: false, // 是否正在刷新
    currentLimit: 10, // 当前显示的记录数量
    isLoadingMore: false, // 是否正在加载更多
    hasMoreData: true, // 是否还有更多数据
    lastSearchQuery: '', // 上次搜索查询

    // 加载操作记录
    async loadLogs(filterType = null) {
        try {
            const data = await SecurityUtils.request('/logs');
            console.log('API返回的原始数据:', data);

            // 设置筛选类型
            if (filterType) {
                this.currentFilter = filterType;
            }

            const container = document.getElementById('logsContainer');
            let logs = [];

            // 获取真实记录（如果有的话）
            if (data.logs && Array.isArray(data.logs)) {
                logs = [...data.logs];
                console.log('复制真实记录后:', logs.length);
            }

            // 检查是否已经添加过测试数据，确保测试数据只添加一次
            if (!logs.some(log => log.id >= 9990)) {
                console.log('开始添加测试数据...');
                const testLogs = [
                    {
                        id: 9999,
                        visitor_name: '张总',
                        visitor_phone: '13912345678',
                        target_person: '李主任',
                        visit_purpose: '商务合作洽谈',
                        created_at: new Date().toISOString(),
                        access_granted: true,
                        action_type: 'verify_access',
                        action_result: 'success',
                        verification_method: 'qr',
                        notes: '重要客户，商务合作项目洽谈',
                        vehicle_info: {
                            plate_number: '京A88888',
                            vehicle_type: '奔驰S级',
                            color: '黑色'
                        }
                    },
                    {
                        id: 9998,
                        visitor_name: '王工',
                        visitor_phone: '13698765432',
                        target_person: '赵工程师',
                        visit_purpose: '技术方案讨论',
                        created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
                        access_granted: true,
                        action_type: 'verify_access',
                        action_result: 'success',
                        verification_method: 'face',
                        notes: '技术团队方案评审会议',
                        vehicle_info: {
                            plate_number: '沪B66666',
                            vehicle_type: '奥迪A6',
                            color: '白色'
                        }
                    },
                    {
                        id: 9997,
                        visitor_name: '刘小姐',
                        visitor_phone: '13745678901',
                        target_person: '陈经理',
                        visit_purpose: '面试',
                        created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
                        access_granted: true,
                        action_type: 'verify_access',
                        action_result: 'success',
                        verification_method: 'qr',
                        notes: '应聘软件开发工程师岗位',
                        vehicle_info: null
                    },
                    {
                        id: 9996,
                        visitor_name: '陌生访客',
                        visitor_phone: '13811112222',
                        target_person: '未填写',
                        visit_purpose: '未提供',
                        created_at: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
                        access_granted: false,
                        action_type: 'deny_access',
                        action_result: 'failed',
                        verification_method: 'qr',
                        notes: '无预约记录，拒绝进入',
                        vehicle_info: null
                    },
                    {
                        id: 9995,
                        visitor_name: '马总',
                        visitor_phone: '13555666777',
                        target_person: '孙总监',
                        visit_purpose: '项目验收',
                        created_at: new Date(Date.now() - 120 * 60 * 1000).toISOString(),
                        access_granted: true,
                        action_type: 'verify_access',
                        action_result: 'success',
                        verification_method: 'qr',
                        notes: '一期项目终验，质量检查',
                        vehicle_info: {
                            plate_number: '粤C12345',
                            vehicle_type: '宝马5系',
                            color: '深蓝色'
                        }
                    },
                    {
                        id: 9994,
                        visitor_name: '实习生小张',
                        visitor_phone: '13622334455',
                        target_person: '周老师',
                        visit_purpose: '实习报到',
                        created_at: new Date(Date.now() - 180 * 60 * 1000).toISOString(),
                        access_granted: true,
                        action_type: 'verify_access',
                        action_result: 'success',
                        verification_method: 'manual',
                        notes: '暑期实习生，HR部门安排',
                        vehicle_info: null
                    },
                    {
                        id: 9993,
                        visitor_name: '快递员小王',
                        visitor_phone: '13777888999',
                        target_person: '前台小刘',
                        visit_purpose: '快递派送',
                        created_at: new Date(Date.now() - 240 * 60 * 1000).toISOString(),
                        access_granted: true,
                        action_type: 'verify_access',
                        action_result: 'success',
                        verification_method: 'qr',
                        notes: '公司文件快递，前台签收',
                        vehicle_info: {
                            plate_number: '苏D88888',
                            vehicle_type: '五菱宏光',
                            color: '白色'
                        }
                    },
                    {
                        id: 9992,
                        visitor_name: '设备维护',
                        visitor_phone: '13599887766',
                        target_person: 'IT部门',
                        visit_purpose: '网络设备维护',
                        created_at: new Date(Date.now() - 300 * 60 * 1000).toISOString(),
                        access_granted: true,
                        action_type: 'verify_access',
                        action_result: 'success',
                        verification_method: 'qr',
                        notes: '定期网络设备检修',
                        vehicle_info: {
                            plate_number: '浙E66666',
                            vehicle_type: '福田货车',
                            color: '蓝色'
                        }
                    },
                    {
                        id: 9991,
                        visitor_name: '客户考察团',
                        visitor_phone: '13988776655',
                        target_person: '销售部',
                        visit_purpose: '工厂参观',
                        created_at: new Date(Date.now() - 360 * 60 * 1000).toISOString(),
                        access_granted: true,
                        action_type: 'verify_access',
                        action_result: 'success',
                        verification_method: 'face',
                        notes: '潜在客户参观生产线，销售部陪同',
                        vehicle_info: {
                            plate_number: '鲁F99999',
                            vehicle_type: '别克商务车',
                            color: '银色'
                        }
                    },
                    {
                        id: 9990,
                        visitor_name: '面试者李明',
                        visitor_phone: '13633445566',
                        target_person: 'HR部门',
                        visit_purpose: '二轮面试',
                        created_at: new Date(Date.now() - 420 * 60 * 1000).toISOString(),
                        access_granted: false,
                        action_type: 'deny_access',
                        action_result: 'failed',
                        verification_method: 'qr',
                        notes: '预约时间错误，已改期至明天',
                        vehicle_info: null
                    }
                ];

                // 将测试记录添加到现有记录的前面
                logs.unshift(...testLogs);
                console.log('添加测试数据后总记录数:', logs.length);
            } else {
                console.log('测试数据已存在，跳过添加');
            }

            // 更新统计数据
            console.log('开始更新统计数据...');
            this.updateStatistics(logs);
            console.log('统计数据更新完成');

            // 记录访问记录总数，用于检测新记录
            this.lastLogCount = logs.length;

            // 获取搜索查询
            const searchInput = document.getElementById('searchInput');
            const searchQuery = searchInput ? searchInput.value.trim().toLowerCase() : '';

            // 根据筛选类型和搜索条件过滤记录
            let filteredLogs = logs;
            if (this.currentFilter && this.currentFilter !== 'all') {
                const today = new Date().toDateString();
                filteredLogs = logs.filter(log => {
                    const logDate = new Date(log.created_at).toDateString() === today;
                    switch (this.currentFilter) {
                        case 'granted':
                            return logDate && log.access_granted === true;
                        case 'denied':
                            return logDate && (log.action_result === 'failed' || log.action_type === 'deny_access');
                        case 'pending':
                            return logDate && (log.action_result === 'pending' && !log.access_granted);
                        default:
                            return true;
                    }
                });
            }

            // 应用搜索过滤
            if (searchQuery) {
                filteredLogs = filteredLogs.filter(log => {
                    // 搜索访客姓名
                    if (log.visitor_name && log.visitor_name.toLowerCase().includes(searchQuery)) {
                        return true;
                    }
                    // 搜索联系电话
                    if (log.visitor_phone && log.visitor_phone.includes(searchQuery)) {
                        return true;
                    }
                    // 搜索受访人
                    if (log.target_person && log.target_person.toLowerCase().includes(searchQuery)) {
                        return true;
                    }
                    // 搜索车牌号
                    if (log.vehicle_info && log.vehicle_info.plate_number &&
                        log.vehicle_info.plate_number.toLowerCase().includes(searchQuery)) {
                        return true;
                    }
                    return false;
                });
                console.log(`搜索"${searchQuery}"找到${filteredLogs.length}条记录`);
            }

            // 按时间逆序排列（最新的在前面）
            filteredLogs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

            // 如果是新的搜索，重置显示数量
            if (searchQuery !== this.lastSearchQuery) {
                this.currentLimit = 10;
                this.lastSearchQuery = searchQuery;
            }

            // 获取当前要显示的记录
            const limitedLogs = filteredLogs.slice(0, this.currentLimit);

            // 检查是否还有更多数据
            this.hasMoreData = filteredLogs.length > this.currentLimit;

            // 更新显示数量
            this.updateRecordsCount(limitedLogs.length, filteredLogs.length);

            if (filteredLogs.length > 0) {
                let tableHTML = '';

                tableHTML += limitedLogs.map(log => `
                    <tr class="hover:bg-gray-50 transition-colors duration-200 cursor-pointer" onclick="AccessLogs.showLogDetail(${JSON.stringify(log).replace(/"/g, '&quot;')})">
                        <td class="px-4 py-3 whitespace-nowrap text-left w-1/4">
                            <div class="flex items-center">
                                <div class="flex-shrink-0 mr-2 text-base">
                                    ${this.getActionIcon(log.action_type, log.action_result)}
                                </div>
                                <div class="text-sm font-bold text-gray-900">${log.visitor_name || '未知访客'}</div>
                            </div>
                        </td>
                        <td class="px-4 py-3 whitespace-nowrap text-left w-2/5">
                            <div class="text-sm text-gray-900 truncate">${log.target_person || '-'}</div>
                        </td>
                        <td class="px-4 py-3 whitespace-nowrap text-left w-1/3">
                            <div class="text-sm text-gray-600">${SecurityUtils.formatTime(log.created_at)}</div>
                        </td>
                    </tr>
                `).join('');

                // 如果还有更多数据，添加加载更多按钮
                if (this.hasMoreData) {
                    tableHTML += `
                        <tr id="loadMoreRow">
                            <td colspan="3" class="px-4 py-4 text-center">
                                <button onclick="AccessLogs.loadMoreLogs()"
                                        class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors duration-200 flex items-center mx-auto">
                                    <i class="ri-arrow-down-line mr-2"></i>
                                    加载更多
                                </button>
                            </td>
                        </tr>
                    `;
                } else {
                    // 没有更多数据时，显示已到底部提示
                    let bottomMessage = '已到底部了';
                    let statsMessage = searchQuery ? `共找到 ${filteredLogs.length} 条匹配"${searchQuery}"的记录` : '共 ' + filteredLogs.length + ' 条记录';

                    tableHTML += `
                        <tr>
                            <td colspan="3" class="px-4 py-8 text-center">
                                <div class="flex flex-col items-center text-gray-400">
                                    <i class="ri-checkbox-circle-line text-2xl mb-2"></i>
                                    <p class="text-sm">${bottomMessage}</p>
                                    <p class="text-xs mt-1">${statsMessage}</p>
                                    ${searchQuery ? `
                                        <button onclick="document.getElementById('searchInput').value=''; AccessLogs.loadLogs(AccessLogs.currentFilter);"
                                                class="mt-2 text-blue-500 hover:text-blue-700 underline text-sm">
                                            清空搜索
                                        </button>
                                    ` : ''}
                                </div>
                            </td>
                        </tr>
                    `;
                }

                container.innerHTML = tableHTML;
            } else {
                let emptyMessage = '暂无访问记录';
                if (searchQuery) {
                    emptyMessage = `未找到匹配"${searchQuery}"的记录`;
                }
                container.innerHTML = `
                    <tr>
                        <td colspan="3" class="px-6 py-8 text-center text-gray-500">
                            <i class="ri-inbox-line text-4xl mb-2 block"></i>
                            <p>${emptyMessage}</p>
                            ${searchQuery ? `
                                <button onclick="document.getElementById('searchInput').value=''; AccessLogs.loadLogs(AccessLogs.currentFilter);"
                                        class="mt-2 text-blue-500 hover:text-blue-700 underline text-sm">
                                    显示所有记录
                                </button>
                            ` : ''}
                        </td>
                    </tr>
                `;
            }

        } catch (error) {
            console.error('加载操作记录失败:', error);
        }
    },

    // 加载更多记录
    async loadMoreLogs() {
        if (this.isLoadingMore || !this.hasMoreData) {
            return;
        }

        this.isLoadingMore = true;

        // 显示加载状态
        const loadMoreRow = document.getElementById('loadMoreRow');
        if (loadMoreRow) {
            loadMoreRow.innerHTML = `
                <td colspan="3" class="px-4 py-4 text-center">
                    <div class="flex items-center justify-center text-blue-500">
                        <i class="ri-loader-4-line animate-spin mr-2"></i>
                        正在加载...
                    </div>
                </td>
            `;
        }

        // 模拟加载延迟
        setTimeout(() => {
            this.currentLimit += 10;
            this.loadLogs(this.currentFilter);
            this.isLoadingMore = false;
        }, 500);
    },

    // 更新记录数量显示
    updateRecordsCount(currentCount, totalCount) {
        const currentCountElement = document.getElementById('currentCount');
        const recordsCountElement = document.getElementById('recordsCount');

        if (currentCountElement) {
            currentCountElement.textContent = currentCount;
        }

        if (recordsCountElement) {
            if (currentCount >= totalCount) {
                recordsCountElement.innerHTML = `共 ${totalCount} 条记录`;
            } else {
                recordsCountElement.innerHTML = `显示前 <span id="currentCount">${currentCount}</span> 条记录，共 ${totalCount} 条`;
            }
        }
    },

    // 检查是否有新的访问记录（轻量级轮询）
    async checkForNewLogs() {
        try {
            const data = await SecurityUtils.request('/logs');

            if (data.logs && data.logs.length !== this.lastLogCount) {
                // 有新的访问记录，刷新显示
                await this.loadLogs(this.currentFilter);

                // 显示新访客提示
                if (data.logs.length > this.lastLogCount) {
                    const newCount = data.logs.length - this.lastLogCount;
                    SecurityUtils.showToast('新访客', `有${newCount}位新访客到访`, 'info');
                }
            }
        } catch (error) {
            // 检查是否是认证错误
            if (error.message && error.message.includes('Authorization token is required')) {
                console.warn('认证失败，停止轮询检查');
                AccessLogs.stopPolling(); // 停止轮询，避免继续产生错误请求
                return;
            }

            // 静默处理其他错误，避免频繁的错误提示
            console.error('检查新记录失败:', error);
        }
    },

    // 开始监听新访客
    startPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        // 每10秒检查一次是否有新访客
        this.pollingInterval = setInterval(() => {
            this.checkForNewLogs();
        }, 10000); // 10秒检查一次
    },

    // 停止监听
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    },

    // 显示访问详情弹窗
    showLogDetail(log) {
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[85vh] my-4">
                <div class="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                    <h3 class="text-lg font-bold text-gray-900">访问详情</h3>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                        <i class="ri-close-line text-xl"></i>
                    </button>
                </div>

                <div class="p-4 max-h-[70vh] overflow-y-auto">
                    <!-- 基本信息 -->
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <div class="space-y-3">
                            <div>
                                <p class="text-xs text-gray-500 mb-1">访客姓名</p>
                                <p class="text-sm font-semibold text-gray-900">${log.visitor_name || '未填写'}</p>
                            </div>
                            <div>
                                <p class="text-xs text-gray-500 mb-1">联系电话</p>
                                <p class="text-sm font-semibold text-gray-900">${log.visitor_phone || '未填写'}</p>
                            </div>
                        </div>
                        <div class="space-y-3">
                            <div>
                                <p class="text-xs text-gray-500 mb-1">接待人</p>
                                <p class="text-sm font-semibold text-gray-900">${log.target_person || '未指定'}</p>
                            </div>
                            <div>
                                <p class="text-xs text-gray-500 mb-1">访问目的</p>
                                <p class="text-sm font-semibold text-gray-900">${log.visit_purpose || '临时访问'}</p>
                            </div>
                        </div>
                    </div>

                    <!-- 访问时间 -->
                    <div class="bg-gray-50 rounded-lg p-3 mb-3">
                        <div class="flex items-center justify-between">
                            <div>
                                <p class="text-xs text-gray-500 mb-1">访问时间</p>
                                <p class="text-sm font-semibold text-gray-900">${SecurityUtils.formatDateTime(log.created_at)}</p>
                            </div>
                            <div class="text-right">
                                <p class="text-xs text-gray-500 mb-1">验证方式</p>
                                <p class="text-sm font-semibold text-gray-900">${SecurityUtils.getVerificationMethodText(log.verification_method)}</p>
                            </div>
                        </div>
                    </div>

                    <!-- 车辆信息 -->
                    ${log.vehicle_info ? `
                        <div class="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
                            <h4 class="text-sm font-semibold text-green-900 mb-2 flex items-center">
                                <i class="ri-car-line mr-1 text-sm"></i>
                                车辆信息
                            </h4>
                            <div class="grid grid-cols-3 gap-2 text-xs">
                                <div>
                                    <p class="text-green-700 mb-1">车牌号</p>
                                    <p class="font-semibold text-green-900">${log.vehicle_info.plate_number || '未填写'}</p>
                                </div>
                                <div>
                                    <p class="text-green-700 mb-1">车型</p>
                                    <p class="font-semibold text-green-900">${log.vehicle_info.vehicle_type || '未填写'}</p>
                                </div>
                                <div>
                                    <p class="text-green-700 mb-1">颜色</p>
                                    <p class="font-semibold text-green-900">${log.vehicle_info.color || '未填写'}</p>
                                </div>
                            </div>
                        </div>
                    ` : `
                        <div class="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-3">
                            <h4 class="text-sm font-semibold text-gray-700 mb-1 flex items-center">
                                <i class="ri-car-line mr-1 text-sm"></i>
                                车辆信息
                            </h4>
                            <p class="text-xs text-gray-600">未登记车辆信息</p>
                        </div>
                    `}

                    <!-- 状态信息 -->
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                        <h4 class="text-sm font-semibold text-blue-900 mb-2">访问状态</h4>
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                ${this.getActionIcon(log.action_type, log.action_result)}
                                ${this.getStatusBadge(log)}
                            </div>
                            <span class="text-xs text-blue-700">
                                ${this.getActionDescription(log)}
                            </span>
                        </div>
                    </div>

                    <!-- 备注 -->
                    ${log.notes ? `
                        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                            <h4 class="text-sm font-semibold text-yellow-900 mb-1">备注信息</h4>
                            <p class="text-xs text-yellow-800">${log.notes}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        // 添加到页面
        document.body.appendChild(modal);

        // 点击背景关闭
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.remove();
            }
        });

        // ESC键关闭
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    },

    // 处理表格滑动事件
    handleTableScroll(element) {
        const scrollTop = element.scrollTop;

        // 向上滑动并且滚动到顶部时刷新
        if (scrollTop < this.lastScrollTop && scrollTop === 0 && !this.isRefreshing) {
            this.performPullToRefresh();
        }

        this.lastScrollTop = scrollTop;
    },

    // 执行下拉刷新
    async performPullToRefresh() {
        if (this.isRefreshing) return;

        this.isRefreshing = true;

        try {
            // 显示刷新提示
            SecurityUtils.showToast('刷新中', '正在获取最新访问记录...', 'info');

            // 重新加载数据
            await this.loadLogs(this.currentFilter);

            // 显示刷新成功提示
            SecurityUtils.showToast('刷新成功', '访问记录已更新', 'success');

        } catch (error) {
            SecurityUtils.showToast('刷新失败', '无法获取最新记录', 'error');
        } finally {
            this.isRefreshing = false;
        }
    },

    // 更新统计数据
    updateStatistics(logs) {
        console.log('updateStatistics 被调用，logs数量:', logs.length);
        const today = new Date().toDateString();
        const todayLogs = logs.filter(log =>
            new Date(log.created_at).toDateString() === today
        );
        console.log('今日记录数量:', todayLogs.length);

        const grantedCount = todayLogs.filter(log => log.access_granted === true).length;
        const deniedCount = todayLogs.filter(log =>
            (log.action_result === 'failed' || log.action_type === 'deny_access')
        ).length;
        const pendingCount = todayLogs.filter(log =>
            log.action_result === 'pending' && !log.access_granted
        ).length;
        const totalCount = todayLogs.length;

        console.log('统计结果:', { grantedCount, deniedCount, pendingCount, totalCount });

        // 更新统计卡片
        this.updateStatCard('todayGrantedCount', grantedCount);
        this.updateStatCard('todayDeniedCount', deniedCount);
        this.updateStatCard('pendingCount', pendingCount);
        this.updateStatCard('totalVerifications', totalCount);
    },

    // 更新统计卡片
    updateStatCard(elementId, value) {
        const element = document.getElementById(elementId);
        console.log(`updateStatCard: 尝试更新 #${elementId} 为 ${value}`);
        if (element) {
            element.textContent = value;
            console.log(`updateStatCard: 成功更新 #${elementId}`);
        } else {
            console.warn(`updateStatCard: 找不到元素 #${elementId}`);
        }
    },

    // 获取操作图标
    getActionIcon(actionType, result) {
        const baseClass = "text-2xl ";

        if (result === 'success') {
            return `<i class="bi ${this.getSuccessIcon(actionType)} ${baseClass} text-green-600"></i>`;
        } else {
            return `<i class="bi ${this.getErrorIcon(actionType)} ${baseClass} text-red-600"></i>`;
        }
    },

    getSuccessIcon(actionType) {
        const icons = {
            'scan_qr': 'bi-qr-code-scan',
            'face_verify': 'bi-person-badge',
            'manual_entry': 'bi-pencil-square',
            'grant_access': 'bi-check-circle-fill',
            'deny_access': 'bi-x-circle-fill'
        };
        return icons[actionType] || 'bi-check-circle';
    },

    getErrorIcon(actionType) {
        const icons = {
            'scan_qr': 'bi-qr-code',
            'face_verify': 'bi-person-x',
            'manual_entry': 'bi-pencil',
            'grant_access': 'bi-x-circle',
            'deny_access': 'bi-x-circle-fill'
        };
        return icons[actionType] || 'bi-x-circle';
    },

    // 获取操作描述
    getActionDescription(log) {
        if (log.action_type === 'grant_access') {
            return `允许访客 ${log.visitor_name} 进入`;
        } else if (log.action_type === 'deny_access') {
            return `拒绝访客 ${log.visitor_name} 进入`;
        } else {
            const methodText = SecurityUtils.getVerificationMethodText(log.verification_method);
            const actionText = SecurityUtils.getActionTypeText(log.action_type);
            return `${methodText}${actionText}`;
        }
    },

    // 获取状态标签
    getStatusBadge(log) {
        if (log.access_granted) {
            return '<span class="status-badge checked-in">已通行</span>';
        } else if (log.action_result === 'failed') {
            return '<span class="status-badge absent">失败</span>';
        } else {
            return '<span class="status-badge scheduled">已验证</span>';
        }
    },

    // 高亮活动卡片
    highlightActiveCard(activeCardId) {
        // 移除所有卡片的高亮状态
        const cardIds = ['grantedCard', 'deniedCard', 'pendingCard', 'totalCard'];
        cardIds.forEach(id => {
            const card = document.getElementById(id);
            if (card) {
                card.classList.remove('ring-2', 'ring-blue-500', 'ring-offset-2');
            }
        });

        // 添加高亮到当前活动卡片
        const activeCard = document.getElementById(activeCardId);
        if (activeCard) {
            activeCard.classList.add('ring-2', 'ring-blue-500', 'ring-offset-2');
        }
    }
};

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查登录状态
    SecurityAuth.checkLoginStatus();

    // 绑定登录表单
    document.getElementById('loginForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        SecurityAuth.login(username, password);
    });

    // 绑定退出按钮
    const logoutBtnDesktop = document.getElementById('logoutBtnDesktop');
    const logoutBtnMobile = document.getElementById('logoutBtnMobile');

    function handleLogout() {
        if (confirm('确定要退出系统吗？')) {
            SecurityAuth.logout();
        }
    }

    if (logoutBtnDesktop) {
        logoutBtnDesktop.addEventListener('click', handleLogout);
    }

    if (logoutBtnMobile) {
        logoutBtnMobile.addEventListener('click', handleLogout);
    }

    // 绑定签到签退按钮
    const checkInBtn = document.getElementById('checkInBtn');
    const checkOutBtn = document.getElementById('checkOutBtn');
    const checkInBtnMobile = document.getElementById('checkInBtnMobile');
    const checkOutBtnMobile = document.getElementById('checkOutBtnMobile');

    if (checkInBtn) {
        checkInBtn.addEventListener('click', function() {
            SecurityProfile.checkIn();
        });
    }

    if (checkOutBtn) {
        checkOutBtn.addEventListener('click', function() {
            if (confirm('确定要签退吗？')) {
                SecurityProfile.checkOut();
            }
        });
    }

    // 移动端按钮绑定
    if (checkInBtnMobile) {
        checkInBtnMobile.addEventListener('click', function() {
            SecurityProfile.checkIn();
        });
    }

    if (checkOutBtnMobile) {
        checkOutBtnMobile.addEventListener('click', function() {
            if (confirm('确定要签退吗？')) {
                SecurityProfile.checkOut();
            }
        });
    }

    // 绑定搜索功能
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;

        // 实时搜索，输入后300ms执行
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                console.log('执行搜索:', e.target.value);
                AccessLogs.loadLogs(AccessLogs.currentFilter);
            }, 300);
        });

        // 回车键搜索
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(searchTimeout);
                console.log('回车搜索:', e.target.value);
                AccessLogs.loadLogs(AccessLogs.currentFilter);
            }
        });

        // 清空搜索按钮
        searchInput.addEventListener('search', function(e) {
            if (!e.target.value) {
                console.log('清空搜索');
                AccessLogs.loadLogs(AccessLogs.currentFilter);
            }
        });
    }

    // 绑定统计卡片点击事件
    document.getElementById('grantedCard').addEventListener('click', function() {
        AccessLogs.loadLogs('granted');
        AccessLogs.highlightActiveCard('grantedCard');
        SecurityUtils.showToast('筛选', '显示今日通行记录', 'info');
    });

    document.getElementById('deniedCard').addEventListener('click', function() {
        AccessLogs.loadLogs('denied');
        AccessLogs.highlightActiveCard('deniedCard');
        SecurityUtils.showToast('筛选', '显示拒绝进入记录', 'info');
    });

    document.getElementById('pendingCard').addEventListener('click', function() {
        AccessLogs.loadLogs('pending');
        AccessLogs.highlightActiveCard('pendingCard');
        SecurityUtils.showToast('筛选', '显示待验证记录', 'info');
    });

    document.getElementById('totalCard').addEventListener('click', function() {
        AccessLogs.loadLogs('all');
        AccessLogs.highlightActiveCard('totalCard');
        SecurityUtils.showToast('显示全部', '显示全部访问记录', 'info');
    });

    // 记录限制选择器已移除，现在使用自动加载更多功能

    // 初始化访客验证
    VisitorVerification.init();

    // 启动新访客监听
    AccessLogs.loadLogs().then(() => {
        // 初始加载完成后，开始监听新访客
        AccessLogs.startPolling();
    }).catch(error => {
        console.error('初始加载失败:', error);
        // 即使初始加载失败，也尝试开始监听
        AccessLogs.startPolling();
    });

    // 页面关闭时停止监听
    window.addEventListener('beforeunload', function() {
        AccessLogs.stopPolling();
    });

    // 允许回车键触发验证码验证
    document.getElementById('verificationCodeInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            // 如果已经有二维码数据，触发验证
            if (VisitorVerification.qrData) {
                VisitorVerification.verifyApplicationId(VisitorVerification.qrData);
            } else {
                SecurityUtils.showToast('提示', '请先扫描二维码', 'info');
            }
        }
      });
});