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

        const response = await fetch(baseUrl + url, {
            ...defaultOptions,
            ...options
        });

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
            throw new Error(data.error || `请求失败 (${response.status})`);
        }

        return data;
    },

    // 显示Toast提示
    showToast(title, message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastIcon = document.getElementById('toastIcon');
        const toastTitle = document.getElementById('toastTitle');
        const toastMessage = document.getElementById('toastMessage');

        toastTitle.textContent = title;
        toastMessage.textContent = message;
        toast.className = `fixed top-4 right-4 z-50 toast-${type} fade-in`;

        // 设置图标
        const icons = {
            success: 'bi-check-circle-fill text-green-600',
            error: 'bi-x-circle-fill text-red-600',
            warning: 'bi-exclamation-triangle-fill text-yellow-600',
            info: 'bi-info-circle-fill text-blue-600'
        };
        toastIcon.className = `text-2xl mr-3 ${icons[type] || icons.info}`;

        // 显示toast
        toast.classList.remove('hidden');

        // 3秒后自动隐藏
        setTimeout(() => {
            toast.classList.add('hidden');
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
        return new Date(date).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
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

            // 使用主系统登录API
            const data = await SecurityUtils.request('/login', {
                method: 'POST',
                body: JSON.stringify({ username, password }),
                baseUrl: SECURITY_CONFIG.LOGIN_API
            });

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
            SecurityUtils.showToast('登录失败', error.message, 'error');
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
        const shiftStatus = document.getElementById('shiftStatus');
        const checkInBtn = document.getElementById('checkInBtn');
        const checkOutBtn = document.getElementById('checkOutBtn');

        switch (shift.status) {
            case 'scheduled':
                shiftStatus.textContent = '未签到';
                shiftStatus.className = 'text-xs text-yellow-600';
                checkInBtn.disabled = false;
                checkOutBtn.disabled = true;
                break;
            case 'checked_in':
                shiftStatus.textContent = '工作中';
                shiftStatus.className = 'text-xs text-green-600';
                checkInBtn.disabled = true;
                checkOutBtn.disabled = false;
                break;
            case 'checked_out':
                shiftStatus.textContent = '已下班';
                shiftStatus.className = 'text-xs text-gray-600';
                checkInBtn.disabled = true;
                checkOutBtn.disabled = true;
                break;
            case 'absent':
                shiftStatus.textContent = '缺勤';
                shiftStatus.className = 'text-xs text-red-600';
                checkInBtn.disabled = true;
                checkOutBtn.disabled = true;
                break;
        }

        // 更新班次时间
        if (shift.shift_start && shift.shift_end) {
            document.getElementById('shiftTime').textContent =
                `${shift.shift_start} - ${shift.shift_end}`;
        }

        // 更新工作时长
        if (shift.check_in_time) {
            const duration = SecurityUtils.formatDuration(
                shift.check_in_time,
                shift.check_out_time
            );
            document.getElementById('workDuration').textContent = duration;
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

        // 更新当前时间
        document.getElementById('currentTime').textContent =
            now.toLocaleTimeString('zh-CN', { hour12: false });

        // 更新今日日期
        document.getElementById('todayDate').textContent =
            now.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'long'
            });
    }
};

// 访客验证
const VisitorVerification = {
    currentMode: null,
    qrCameraStream: null,
    faceCameraStream: null,

    // 初始化验证模式
    init() {
        // 绑定验证模式按钮
        document.getElementById('qrScanBtn').addEventListener('click', () => {
            this.showVerificationMode('qr');
        });

        document.getElementById('faceScanBtn').addEventListener('click', () => {
            this.showVerificationMode('face');
        });

        document.getElementById('manualBtn').addEventListener('click', () => {
            this.showVerificationMode('manual');
        });

        // 绑定二维码扫描按钮
        document.getElementById('openCameraBtn').addEventListener('click', () => {
            this.showCameraScanArea();
        });

        document.getElementById('uploadImageBtn').addEventListener('click', () => {
            this.showImageUploadArea();
        });

        document.getElementById('manualInputBtn').addEventListener('click', () => {
            this.showManualInputArea();
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

        // 绑定手动输入验证按钮
        document.getElementById('verifyManualQrBtn').addEventListener('click', () => {
            this.verifyQrCode();
        });

        // 绑定人脸识别按钮
        document.getElementById('startFaceScanBtn').addEventListener('click', () => {
            this.startFaceScan();
        });

        // 绑定手动验证按钮
        document.getElementById('verifyManualBtn').addEventListener('click', () => {
            this.verifyManual();
        });

        // 绑定同行人管理按钮
        document.getElementById('addCompanionBtn').addEventListener('click', () => {
            this.addCompanion();
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

    // 显示手动输入区域
    showManualInputArea() {
        this.hideAllScanAreas();
        document.getElementById('manualInputArea').classList.remove('hidden');
        document.getElementById('manualInputArea').classList.add('fade-in');
    },

    // 隐藏所有扫描区域
    hideAllScanAreas() {
        document.getElementById('cameraScanArea').classList.add('hidden');
        document.getElementById('imageUploadArea').classList.add('hidden');
        document.getElementById('manualInputArea').classList.add('hidden');
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

            requestAnimationFrame(scan);
        };

        requestAnimationFrame(scan);
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
                    this.verifyApplicationId(applicationId);
                    return;
                }
                throw new Error('无效的二维码格式');
            }

            if (data.type === 'visit_application' && data.id) {
                this.verifyApplicationId(data.id);
            } else {
                throw new Error('二维码不是有效的访问申请');
            }

        } catch (error) {
            SecurityUtils.showToast('二维码错误', error.message, 'error');
        }
    },

    // 验证申请ID
    async verifyApplicationId(applicationId) {
        try {
            SecurityUtils.showLoading('验证中...');

            const data = await SecurityUtils.request('/visit/verify-qr', {
                method: 'POST',
                body: JSON.stringify({ application_id: applicationId })
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
            'face': 'faceScanSection',
            'manual': 'manualSection'
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

    // 验证二维码
    async verifyQrCode() {
        const applicationId = document.getElementById('applicationIdInput').value.trim();

        if (!applicationId) {
            SecurityUtils.showToast('输入错误', '请输入访问申请编号', 'warning');
            return;
        }

        if (isNaN(applicationId) || parseInt(applicationId) < 1) {
            SecurityUtils.showToast('输入错误', '请输入有效的访问申请编号', 'warning');
            return;
        }

        try {
            SecurityUtils.showLoading('验证中...');

            const data = await SecurityUtils.request('/visit/verify-qr', {
                method: 'POST',
                body: JSON.stringify({ application_id: parseInt(applicationId) })
            });

            SecurityState.currentLogId = data.log_id;
            this.showVerificationResult(data);

        } catch (error) {
            SecurityUtils.showToast('验证失败', error.message, 'error');
            this.showVerificationResult({ valid: false, error: error.message });
        } finally {
            SecurityUtils.hideLoading();
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

    // 手动验证
    async verifyManual() {
        const name = document.getElementById('manualName').value.trim();
        const phone = document.getElementById('manualPhone').value.trim();
        const purpose = document.getElementById('manualPurpose').value.trim();
        const target = document.getElementById('manualTarget').value.trim();

        if (!name || !phone) {
            SecurityUtils.showToast('输入错误', '请填写访客姓名和联系电话', 'warning');
            return;
        }

        // 获取同行人信息
        const companions = this.getCompanions();

        try {
            SecurityUtils.showLoading('验证访客信息...');

            // 构建访客信息对象
            const visitorData = {
                visitor_info: {
                    name: name,
                    phone: phone
                },
                visit_purpose: purpose || '临时访问',
                target_person: target || '未指定',
                companions: companions,
                verification_method: 'manual',
                manual_verification: true
            };

            // 创建临时访客记录进行验证
            const resultDiv = document.getElementById('verificationResult');
            resultDiv.classList.remove('hidden');

            resultDiv.innerHTML = `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 fade-in">
                    <div class="flex items-center mb-4">
                        <i class="bi bi-person-check-fill text-blue-600 text-2xl mr-3"></i>
                        <h3 class="text-lg font-semibold text-blue-800">
                            手动验证访客信息
                        </h3>
                    </div>

                    <div class="bg-white rounded-lg p-4 mb-4">
                        <h4 class="font-medium text-gray-900 mb-3">访客基本信息</h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <p class="text-sm text-gray-600">访客姓名</p>
                                <p class="font-medium text-gray-900">${name}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">联系电话</p>
                                <p class="font-medium text-gray-900">${phone}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">访问目的</p>
                                <p class="font-medium text-gray-900">${purpose || '临时访问'}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">被访人</p>
                                <p class="font-medium text-gray-900">${target || '未指定'}</p>
                            </div>
                        </div>

                        ${companions.length > 0 ? `
                            <div class="mt-4 pt-4 border-t border-gray-200">
                                <h5 class="font-medium text-gray-900 mb-2">同行人信息 (${companions.length}人)</h5>
                                <div class="space-y-2">
                                    ${companions.map((companion, index) => `
                                        <div class="flex items-center space-x-3 text-sm">
                                            <i class="bi bi-person text-gray-500"></i>
                                            <span class="font-medium">${companion.name}</span>
                                            <span class="text-gray-600">${companion.phone}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <div class="flex justify-center space-x-4">
                        <button onclick="AccessControl.grantManualAccess(${JSON.stringify(visitorData).replace(/"/g, '&quot;')})"
                                class="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-semibold">
                            <i class="bi bi-check-circle mr-2"></i>
                            允许进入
                        </button>
                        <button onclick="VisitorVerification.clearResult()"
                                class="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors font-semibold">
                            <i class="bi bi-x-circle mr-2"></i>
                            取消
                        </button>
                    </div>
                </div>
            `;

            resultDiv.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            SecurityUtils.showToast('验证失败', error.message, 'error');
        } finally {
            SecurityUtils.hideLoading();
        }
    },

    // 显示验证结果
    showVerificationResult(data) {
        const resultDiv = document.getElementById('verificationResult');

        if (data.valid && data.application) {
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
                            <p class="text-sm text-gray-600">被访人</p>
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

    // 添加同行人
    addCompanion() {
        const companionsList = document.getElementById('companionsList');

        // 如果是第一个同行人，清除占位内容
        if (companionsList.querySelector('.text-gray-500')) {
            companionsList.innerHTML = '';
        }

        const companionCount = companionsList.children.length;
        const companionDiv = document.createElement('div');
        companionDiv.className = 'bg-white border border-gray-200 rounded-lg p-3 fade-in companion-item';
        companionDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3 flex-1">
                    <i class="bi bi-person text-gray-600"></i>
                    <div class="flex-1 grid grid-cols-2 gap-3">
                        <input type="text" class="companion-name px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                               placeholder="同行人姓名" data-companion-index="${companionCount}">
                        <input type="text" class="companion-phone px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                               placeholder="联系电话" data-companion-index="${companionCount}">
                    </div>
                </div>
                <button onclick="VisitorVerification.removeCompanion(this)"
                        class="ml-3 text-red-600 hover:text-red-800 hover:bg-red-50 p-2 rounded-lg transition-colors"
                        title="删除同行人">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;

        companionsList.appendChild(companionDiv);

        // 聚焦到新添加的姓名输入框
        const nameInput = companionDiv.querySelector('.companion-name');
        nameInput.focus();
    },

    // 删除同行人
    removeCompanion(button) {
        const companionItem = button.closest('.companion-item');
        if (companionItem) {
            companionItem.remove();

            // 如果没有同行人了，显示占位内容
            const companionsList = document.getElementById('companionsList');
            if (companionsList.children.length === 0) {
                companionsList.innerHTML = `
                    <div class="text-center text-gray-500 py-2">
                        <i class="bi bi-people text-2xl mb-2"></i>
                        <p class="text-sm">暂无同行人</p>
                    </div>
                `;
            }
        }
    },

    // 获取同行人信息
    getCompanions() {
        const companions = [];
        const companionItems = document.querySelectorAll('.companion-item');

        companionItems.forEach(item => {
            const nameInput = item.querySelector('.companion-name');
            const phoneInput = item.querySelector('.companion-phone');

            if (nameInput && phoneInput) {
                const name = nameInput.value.trim();
                const phone = phoneInput.value.trim();

                if (name && phone) {
                    companions.push({
                        name: name,
                        phone: phone
                    });
                }
            }
        });

        return companions;
    },

    // 清除验证结果
    clearResult() {
        document.getElementById('verificationResult').classList.add('hidden');
        document.getElementById('applicationIdInput').value = '';

        // 清空手动输入
        document.getElementById('manualName').value = '';
        document.getElementById('manualPhone').value = '';
        document.getElementById('manualPurpose').value = '';
        document.getElementById('manualTarget').value = '';

        // 清空同行人信息
        const companionsList = document.getElementById('companionsList');
        companionsList.innerHTML = `
            <div class="text-center text-gray-500 py-2">
                <i class="bi bi-people text-2xl mb-2"></i>
                <p class="text-sm">暂无同行人</p>
            </div>
        `;
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

    // 手动验证允许进入
    async grantManualAccess(visitorData) {
        try {
            SecurityUtils.showLoading('处理中...');

            const notes = prompt('请输入备注信息（可选）:');

            // 创建手动访问记录
            const logData = {
                security_id: SecurityState.security.id,
                action_type: 'manual_entry',
                verification_method: 'manual',
                action_result: 'success',
                access_granted: true,
                visitor_name: visitorData.visitor_info.name,
                visitor_phone: visitorData.visitor_info.phone,
                visit_purpose: visitorData.visit_purpose,
                target_person: visitorData.target_person,
                companions: visitorData.companions,
                notes: notes || '',
                manual_verification: true
            };

            // 记录访问日志
            await SecurityUtils.request('/logs', {
                method: 'POST',
                body: JSON.stringify(logData)
            });

            SecurityUtils.showToast('放行成功',
                `已允许${visitorData.visitor_info.name}进入${visitorData.companions.length > 0 ? `（含${visitorData.companions.length}名同行人）` : ''}`,
                'success');

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
    // 加载操作记录
    async loadLogs() {
        try {
            const data = await SecurityUtils.request('/logs');

            const container = document.getElementById('logsContainer');

            if (data.logs && data.logs.length > 0) {
                container.innerHTML = data.logs.map(log => `
                    <div class="log-item ${log.action_result} bg-gray-50 rounded-lg p-4 hover-card">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-3">
                                <div class="flex-shrink-0">
                                    ${this.getActionIcon(log.action_type, log.action_result)}
                                </div>
                                <div>
                                    <p class="font-medium text-gray-900">
                                        ${this.getActionDescription(log)}
                                    </p>
                                    <p class="text-sm text-gray-600">
                                        ${SecurityUtils.formatTime(log.created_at)}
                                    </p>
                                </div>
                            </div>
                            <div class="text-right">
                                ${this.getStatusBadge(log)}
                            </div>
                        </div>
                        ${log.notes ? `<p class="mt-2 text-sm text-gray-600">备注：${log.notes}</p>` : ''}
                    </div>
                `).join('');
            } else {
                container.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <i class="bi bi-inbox text-4xl mb-2"></i>
                        <p>暂无操作记录</p>
                    </div>
                `;
            }

        } catch (error) {
            console.error('加载操作记录失败:', error);
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
    document.getElementById('logoutBtn').addEventListener('click', function() {
        if (confirm('确定要退出系统吗？')) {
            SecurityAuth.logout();
        }
    });

    // 绑定签到签退按钮
    document.getElementById('checkInBtn').addEventListener('click', function() {
        SecurityProfile.checkIn();
    });

    document.getElementById('checkOutBtn').addEventListener('click', function() {
        if (confirm('确定要签退吗？')) {
            SecurityProfile.checkOut();
        }
    });

    // 绑定刷新记录按钮
    document.getElementById('refreshLogsBtn').addEventListener('click', function() {
        AccessLogs.loadLogs();
    });

    // 初始化访客验证
    VisitorVerification.init();

    // 允许回车键触发二维码验证
    document.getElementById('applicationIdInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            VisitorVerification.verifyQrCode();
        }
    });
});