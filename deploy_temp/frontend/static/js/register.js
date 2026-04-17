// 校友注册页面脚本 - 温馨回家主题
// Version: 20251114_1 - 优化注册用户体验：移除用户名唯一约束，添加用户名建议功能

// 全局变量
let currentStep = 'welcome';
let formData = {};

// DOM 元素
const welcomeStep = document.getElementById('welcomeStep');
const basicInfoStep = document.getElementById('basicInfoStep');
const alumniInfoStep = document.getElementById('alumniInfoStep');
const completeStep = document.getElementById('completeStep');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    attachEventListeners();
    setupPasswordToggles();
    setupInputValidation();

    // 显示欢迎动画
    setTimeout(() => {
        if (welcomeStep) {
            welcomeStep.style.opacity = '1';
        }
    }, 100);
});

// 初始化表单
function initializeForm() {
    // 设置当前步骤 - 欢迎页面不需要动画
    const welcomeElement = document.getElementById('welcomeStep');
    if (welcomeElement) {
        welcomeElement.classList.add('active');
        welcomeElement.style.opacity = '1';
        welcomeElement.style.transform = 'translateX(0)';
    }

    // 收集表单数据
    collectFormData();
}

// 附加事件监听器
function attachEventListeners() {
    // 密码显示/隐藏切换
    document.querySelectorAll('.password-toggle').forEach(button => {
        button.addEventListener('click', togglePassword);
    });

    // 实时验证
    document.addEventListener('input', handleRealTimeValidation);

    // 失去焦点验证
    document.addEventListener('blur', handleBlurValidation, true);

    // 表单提交 - 阻止默认提交行为，因为我们使用按钮点击处理
    const alumniInfoForm = document.getElementById('alumniInfoForm');
    if (alumniInfoForm) {
        alumniInfoForm.addEventListener('submit', function(event) {
            event.preventDefault();
        });
    }
}

// 设置密码切换
function setupPasswordToggles() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        const toggleButton = input.parentElement.querySelector('.password-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', () => {
                const type = input.type === 'password' ? 'text' : 'password';
                input.type = type;
                toggleButton.innerHTML = type === 'password' ?
                    '<i class="ri-eye-off-line"></i>' :
                    '<i class="ri-eye-line"></i>';
            });
        }
    });
}

// 设置输入验证
function setupInputValidation() {
    // 用户名验证
    const usernameInput = document.getElementById('username');
    if (usernameInput) {
        usernameInput.addEventListener('input', debounce(function() {
            validateUsername(usernameInput.value);
        }, 500));
    }

    // 身份证验证
    const idCardInput = document.getElementById('idCard');
    if (idCardInput) {
        idCardInput.addEventListener('input', debounce(function() {
            validateIdCard(idCardInput.value);
        }, 500));
    }

    // 手机号验证
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            validatePhone(input.value);
        }, 300));
    });

    // 邮箱验证
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('input', debounce(function() {
            validateEmail(emailInput.value);
        }, 500));
    }

    // 密码确认验证
    const confirmPasswordInput = document.getElementById('confirmPassword');
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            validatePasswordMatch();
        });
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 步骤导航函数
function showWelcome() {
    hideAllSteps();
    showStep('welcome', 'right');
    currentStep = 'welcome';
}

function showBasicInfo() {
    hideAllSteps();
    showStep('basicInfo', 'left');
    currentStep = 'basicInfo';
    focusFirstInput('basicInfoForm');
}

function showAlumniInfo() {
    if (validateBasicInfoStep()) {
        hideAllSteps();
        showStep('alumniInfo', 'left');
        currentStep = 'alumniInfo';
        focusFirstInput('alumniInfoForm');
    }
}

function showCompleteStep() {
    if (validateCompleteStep()) {
        submitRegistration();
    }
}

function hideAllSteps() {
    if (welcomeStep) welcomeStep.classList.remove('active');
    if (basicInfoStep) basicInfoStep.classList.remove('active');
    if (alumniInfoStep) alumniInfoStep.classList.remove('active');
    if (completeStep) completeStep.classList.remove('active');
}

function showStep(step, direction = 'left') {
    const stepElement = document.getElementById(step + 'Step');
    if (stepElement) {
        // 首先设置进入方向的初始位置
        if (direction === 'left') {
            stepElement.style.transform = 'translateX(100%)';
        } else if (direction === 'right') {
            stepElement.style.transform = 'translateX(-100%)';
        }

        stepElement.classList.add('active');

        // 触发动画
        setTimeout(() => {
            stepElement.style.transform = 'translateX(0)';
        }, 50);
    }
}

function focusFirstInput(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const firstInput = form.querySelector('input:not([type="hidden"])');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 300);
        }
    }
}

// 验证函数
function validateBasicInfoStep() {
    let isValid = true;
    const basicInfoForm = document.getElementById('basicInfoForm');

    if (!basicInfoForm) {
        return false;
    }

    const requiredFields = basicInfoForm.querySelectorAll('[required]');

    requiredFields.forEach((field) => {
        if (!validateField(field)) {
            isValid = false;
        }
    });

    // 验证密码强度
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        const password = passwordInput.value;
        if (!validatePasswordStrength(password)) {
            isValid = false;
        }
    }

    // 验证密码确认
    if (!validatePasswordMatch()) {
        isValid = false;
    }

    // 验证身份证
    const idCardInput = document.getElementById('idCard');
    if (idCardInput) {
        const idCard = idCardInput.value;
        if (idCard && !validateIdCard(idCard)) {
            isValid = false;
        }
    }

    if (!isValid) {
        showToast('请填写所有必填字段并确保格式正确', 'error');
    }

    return isValid;
}

function validateAlumniInfoStep() {
    let isValid = true;
    const basicInfoForm = document.getElementById('basicInfoForm');
    const alumniInfoForm = document.getElementById('alumniInfoForm');

    if (!basicInfoForm || !alumniInfoForm) return false;

    // 收集基本信息
    collectBasicInfoData();

    // 验证校友信息必填字段
    const requiredFields = alumniInfoForm.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });

    // 验证毕业年份
    const graduationYearInput = document.getElementById('graduationYear');
    if (graduationYearInput) {
        const graduationYear = graduationYearInput.value;
        const currentYear = new Date().getFullYear();
        const year = parseInt(graduationYear);

        if (year < 1950 || year > currentYear) {
            showFieldError('graduationYear', '毕业年份应在1950年至' + currentYear + '年之间');
            isValid = false;
        }
    }

    // 验证紧急联系人电话（如果填写了的话）
    const emergencyPhone = document.getElementById('emergencyPhone').value;
    if (emergencyPhone && emergencyPhone.trim() !== '' && !validatePhone(emergencyPhone)) {
        showFieldError('emergencyPhone', '请输入有效的手机号码');
        isValid = false;
    }

    if (!isValid) {
        showToast('请填写所有必填字段并确保格式正确', 'error');
    }

    return isValid;
}

function validateCompleteStep() {
    // 收集所有表单数据
    collectAlumniInfoData();

    // 最终验证
    if (!validateBasicInfoStep() || !validateAlumniInfoStep()) {
        return false;
    }

    return true;
}

// 字段验证
function validateField(field) {
    let isValid = true;
    clearFieldError(field);

    // 必填验证
    if (field.hasAttribute('required') && !field.value.trim()) {
        showFieldError(field, '此字段为必填项');
        return false;
    }

    // 类型验证
    switch (field.type) {
        case 'email':
            if (field.value && !validateEmail(field.value)) {
                showFieldError(field, '请输入有效的邮箱地址');
                isValid = false;
            }
            break;
        case 'tel':
            if (field.value && !validatePhone(field.value)) {
                showFieldError(field, '请输入有效的手机号码');
                isValid = false;
            }
            break;
        case 'text':
            if (field.id === 'idCard' && field.value && !validateIdCard(field.value)) {
                isValid = false;
            }
            if (field.id === 'username' && field.value && !validateUsername(field.value)) {
                isValid = false;
            }
            break;
        case 'number':
            if (field.value && (isNaN(field.value) || field.value < 0)) {
                showFieldError(field, '请输入有效的数字');
                isValid = false;
            }
            break;
    }

    // 长度验证
    if (field.hasAttribute('minlength') && field.value.length < field.getAttribute('minlength')) {
        showFieldError(field, `最少需要${field.getAttribute('minlength')}个字符`);
        isValid = false;
    }

    if (field.hasAttribute('maxlength') && field.value.length > field.getAttribute('maxlength')) {
        showFieldError(field, `最多允许${field.getAttribute('maxlength')}个字符`);
        isValid = false;
    }

    return isValid;
}

// 具体验证函数
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePhone(phone) {
    const phoneRegex = /^1[3-9]\d{9}$/;
    return phoneRegex.test(phone);
}

function validateIdCard(idCard) {
    // 如果身份证号为空，不进行验证（实时验证时可能为空）
    if (!idCard || idCard.trim() === '') {
        clearFieldError('idCard');
        return true;
    }

    idCard = idCard.trim();
    const idCardRegex = /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/;

    if (!idCardRegex.test(idCard)) {
        showFieldError('idCard', '请输入有效的18位身份证号码');
        return false;
    }

    // 验证校验码
    if (!validateIdCardChecksum(idCard)) {
        showFieldError('idCard', '身份证号码校验码不正确');
        return false;
    }

    clearFieldError('idCard');
    return true;
}

function validateIdCardChecksum(idCard) {
    const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2];
    const checksums = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2'];

    let sum = 0;
    for (let i = 0; i < 17; i++) {
        sum += parseInt(idCard[i]) * weights[i];
    }

    const checksum = checksums[sum % 11];
    return idCard[17].toUpperCase() === checksum;
}

function validateUsername(username) {
    // 如果用户名为空，不进行验证（实时验证时可能为空）
    if (!username || username.trim() === '') {
        clearFieldError('username');
        return true;
    }

    username = username.trim();

    if (username.length < 4 || username.length > 20) {
        showFieldError('username', '用户名长度应在4-20个字符之间');
        return false;
    }

    const usernameRegex = /^[a-zA-Z0-9_]+$/;
    if (!usernameRegex.test(username)) {
        showFieldError('username', '用户名只能包含字母、数字和下划线');
        return false;
    }

    clearFieldError('username');
    return true;
}

function validatePasswordStrength(password) {
    // 如果密码为空，不进行验证（实时验证时可能为空）
    if (!password || password.trim() === '') {
        clearFieldError('password');
        return true;
    }

    if (password.length < 8) {
        showFieldError('password', '密码长度至少8位');
        return false;
    }

    let score = 0;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;

    if (score < 2) {
        showFieldError('password', '密码应包含字母、数字或特殊字符中的至少2种');
        return false;
    }

    clearFieldError('password');
    return true;
}

function validatePasswordMatch() {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');

    if (!passwordInput || !confirmPasswordInput) {
        return true; // 如果元素不存在，跳过验证
    }

    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    if (confirmPassword && password !== confirmPassword) {
        showFieldError('confirmPassword', '两次输入的密码不一致');
        return false;
    }

    clearFieldError('confirmPassword');
    return true;
}

// 错误显示
function showFieldError(fieldOrId, message) {
    const field = typeof fieldOrId === 'string' ? document.getElementById(fieldOrId) : fieldOrId;
    if (!field) return;

    field.classList.add('error');

    // 移除已存在的错误消息
    let errorElement = field.parentElement.querySelector('.error-message');
    if (errorElement) {
        errorElement.remove();
    }

    // 添加错误消息
    errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    errorElement.style.cssText = `
        color: var(--error-color);
        font-size: 12px;
        margin-top: 4px;
        animation: fadeIn 0.3s ease-out;
    `;

    field.parentElement.appendChild(errorElement);
}

function clearFieldError(fieldOrId) {
    const field = typeof fieldOrId === 'string' ? document.getElementById(fieldOrId) : fieldOrId;
    if (!field) return;

    field.classList.remove('error');

    const errorElement = field.parentElement.querySelector('.error-message');
    if (errorElement) {
        errorElement.remove();
    }
}

// 实时验证
function handleRealTimeValidation(event) {
    const field = event.target;
    if (field.type !== 'checkbox' && field.type !== 'radio') {
        validateField(field);
    }
}

// 失去焦点验证
function handleBlurValidation(event) {
    const field = event.target;
    validateField(field);
}

// 数据收集函数
function collectBasicInfoData() {
    const basicInfoForm = document.getElementById('basicInfoForm');
    if (!basicInfoForm) return;

    const inputs = basicInfoForm.querySelectorAll('input');
    inputs.forEach(input => {
        formData[input.name] = input.value;
    });
}

function collectAlumniInfoData() {
    const alumniInfoForm = document.getElementById('alumniInfoForm');
    if (!alumniInfoForm) return;

    const inputs = alumniInfoForm.querySelectorAll('input');
    inputs.forEach(input => {
        formData[input.name] = input.value;
    });
}

function collectFormData() {
    const allInputs = document.querySelectorAll('input');
    allInputs.forEach(input => {
        if (input.name) {
            if (input.type === 'checkbox') {
                formData[input.name] = input.checked;
            } else {
                formData[input.name] = input.value;
            }
        }
    });
}

// 提交注册
async function submitRegistration() {
    // 显示加载状态
    showToast('正在提交注册信息...', 'info');

    // 调试：打印表单数据
    console.log('提交的表单数据:', formData);

    try {
        // 发送注册请求
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            // 显示成功页面
            hideAllSteps();
            showStep('complete', 'left');
            currentStep = 'complete';

            showToast('注册成功！欢迎回到实验大家庭！', 'success');
        } else {
            // 处理不同类型的错误
            if (result.field === 'username' && result.suggestions && result.suggestions.length > 0) {
                // 用户名重复，显示建议
                showUsernameSuggestions(result.message, result.suggestions);
            } else if (result.field === 'phone') {
                // 手机号重复，显示详细提示
                showToast(result.message, 'error');
                if (result.detail) {
                    // 可以在错误提示下方显示详细信息
                    setTimeout(() => {
                        showToast(result.detail, 'warning');
                    }, 2000);
                }
            } else {
                // 其他错误，显示标准错误信息
                showToast(result.message || '注册失败，请重试', 'error');
            }
        }
    } catch (error) {
        console.error('注册错误:', error);
        showToast('网络错误，请检查网络连接后重试', 'error');
    }
}

// 密码显示/隐藏切换
function togglePassword(event) {
    const button = event.currentTarget;
    const targetId = button.getAttribute('data-target');
    const input = document.getElementById(targetId);

    if (input) {
        const type = input.type === 'password' ? 'text' : 'password';
        input.type = type;

        const icon = button.querySelector('i');
        icon.className = type === 'password' ? 'ri-eye-off-line' : 'ri-eye-line';
    }
}

// 跳转函数
function goToLogin() {
    window.location.href = '/login';
}

function goToHome() {
    window.location.href = '/';
}

// 模态框功能
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Toast 提示
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');
    const toastIcon = toast.querySelector('.toast-icon');

    // 设置消息和类型
    toastMessage.textContent = message;
    toast.className = `toast ${type}`;

    // 设置图标
    switch (type) {
        case 'success':
            toastIcon.className = 'ri-check-line toast-icon';
            break;
        case 'error':
            toastIcon.className = 'ri-close-circle-line toast-icon';
            break;
        case 'warning':
            toastIcon.className = 'ri-alert-line toast-icon';
            break;
        default:
            toastIcon.className = 'ri-information-line toast-icon';
    }

    // 显示 Toast
    toast.classList.add('show');

    // 自动隐藏
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 显示用户名建议
function showUsernameSuggestions(message, suggestions) {
    // 创建一个模态框来显示用户名建议
    const modal = document.createElement('div');
    modal.className = 'username-suggestions-modal';
    modal.innerHTML = `
        <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>用户名已存在</h3>
                    <button class="modal-close" onclick="this.closest('.username-suggestions-modal').remove()">
                        <i class="ri-close-line"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                    <p class="suggestions-intro">请选择以下建议的用户名：</p>
                    <div class="suggestions-list">
                        ${suggestions.map(username => `
                            <button class="suggestion-btn" onclick="selectUsername('${username}')">
                                ${username}
                            </button>
                        `).join('')}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.username-suggestions-modal').remove()">
                        自己输入
                    </button>
                </div>
            </div>
        </div>
    `;

    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        .username-suggestions-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10000;
        }

        .modal-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-content {
            background: white;
            border-radius: 12px;
            padding: 0;
            max-width: 400px;
            width: 90%;
            max-height: 80vh;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }

        .modal-header h3 {
            margin: 0;
            color: #2c3e50;
            font-size: 18px;
        }

        .modal-close {
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: #6c757d;
            padding: 5px;
            border-radius: 5px;
        }

        .modal-close:hover {
            background: #f8f9fa;
            color: #495057;
        }

        .modal-body {
            padding: 20px;
        }

        .modal-body p {
            margin-bottom: 15px;
            color: #6c757d;
        }

        .suggestions-intro {
            font-weight: 500;
            color: #495057;
        }

        .suggestions-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .suggestion-btn {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 12px 16px;
            text-align: left;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: inherit;
            font-size: 14px;
        }

        .suggestion-btn:hover {
            background: #e3f2fd;
            border-color: #2196f3;
            color: #1976d2;
        }

        .modal-footer {
            padding: 20px;
            border-top: 1px solid #e9ecef;
            text-align: right;
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }

        .btn-secondary:hover {
            background: #5a6268;
        }
    `;

    // 添加到页面
    document.head.appendChild(style);
    document.body.appendChild(modal);
}

// 选择用户名
function selectUsername(username) {
    // 填充用户名输入框
    const usernameInput = document.getElementById('username');
    if (usernameInput) {
        usernameInput.value = username;
        formData.username = username;

        // 触发验证
        validateUsername(username);

        // 添加成功动画效果
        usernameInput.style.borderColor = '#28a745';
        usernameInput.style.boxShadow = '0 0 0 0.2rem rgba(40, 167, 69, 0.25)';
        setTimeout(() => {
            usernameInput.style.borderColor = '';
            usernameInput.style.boxShadow = '';
        }, 2000);
    }

    // 关闭模态框
    const modal = document.querySelector('.username-suggestions-modal');
    if (modal) {
        modal.remove();
    }

    // 显示成功提示
    showToast(`已选择用户名：${username}`, 'success');
}

// 键盘导航支持
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter 提交当前步骤
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        switch (currentStep) {
            case 'welcome':
                showBasicInfo();
                break;
            case 'basicInfo':
                showAlumniInfo();
                break;
            case 'alumniInfo':
                showCompleteStep();
                break;
        }
    }

    // Escape 返回上一步
    if (event.key === 'Escape') {
        switch (currentStep) {
            case 'basicInfo':
                showWelcome();
                break;
            case 'alumniInfo':
                showBasicInfo();
                break;
        }
    }
});

// 页面可见性变化时的处理
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // 页面隐藏时保存数据
        collectFormData();
        localStorage.setItem('registerFormData', JSON.stringify(formData));
        localStorage.setItem('registerCurrentStep', currentStep);
    } else {
        // 页面显示时恢复数据
        const savedData = localStorage.getItem('registerFormData');
        const savedStep = localStorage.getItem('registerCurrentStep');

        if (savedData) {
            try {
                formData = JSON.parse(savedData);
                restoreFormData();
            } catch (e) {
                console.error('恢复表单数据失败:', e);
            }
        }

        if (savedStep && savedStep !== 'complete') {
            // 恢复到之前的步骤
            switch (savedStep) {
                case 'basicInfo':
                    showBasicInfo();
                    break;
                case 'alumniInfo':
                    showAlumniInfo();
                    break;
                default:
                    showWelcome();
            }
        }
    }
});

// 恢复表单数据
function restoreFormData() {
    Object.keys(formData).forEach(key => {
        const input = document.querySelector(`[name="${key}"]`);
        if (input && formData[key]) {
            input.value = formData[key];
        }
    });
}

// 页面卸载时清理数据
window.addEventListener('beforeunload', function() {
    // 清理本地存储
    if (currentStep === 'complete') {
        localStorage.removeItem('registerFormData');
        localStorage.removeItem('registerCurrentStep');
    }
});

// 错误处理
window.addEventListener('error', function(event) {
    console.error('页面错误:', event.error);
    showToast('页面出现错误，请刷新后重试', 'error');
});

// 添加无障碍支持
function setupAccessibility() {
    // 为表单字段添加适当的 ARIA 属性
    const requiredFields = document.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.setAttribute('aria-required', 'true');
    });

    // 为步骤添加 aria-current
    updateStepAccessibility();
}

function updateStepAccessibility() {
    // 根据当前步骤设置无障碍属性
    const steps = ['welcome', 'basicInfo', 'alumniInfo', 'complete'];
    steps.forEach(stepId => {
        const stepElement = document.getElementById(stepId + 'Step');
        if (stepElement) {
            stepElement.removeAttribute('aria-current');
            if (currentStep === stepId) {
                stepElement.setAttribute('aria-current', 'step');
            }
        }
    });
}

// 初始化无障碍功能
setupAccessibility();

// 添加页面加载动画
window.addEventListener('load', function() {
    document.body.style.opacity = '1';
});

// 添加触摸支持
let touchStartY = 0;
let touchEndY = 0;

document.addEventListener('touchstart', function(event) {
    touchStartY = event.changedTouches[0].screenY;
});

document.addEventListener('touchend', function(event) {
    touchEndY = event.changedTouches[0].screenY;
    handleSwipe();
});

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartY - touchEndY;

    if (Math.abs(diff) > swipeThreshold) {
        // 向上滑动 - 进入下一步
        if (diff > 0) {
            switch (currentStep) {
                case 'welcome':
                    showBasicInfo();
                    break;
                case 'basicInfo':
                    showAlumniInfo();
                    break;
            }
        }
        // 向下滑动 - 返回上一步
        else {
            switch (currentStep) {
                case 'basicInfo':
                    showWelcome();
                    break;
                case 'alumniInfo':
                    showBasicInfo();
                    break;
            }
        }
    }
}

// 添加CSS动画样式
const style = document.createElement('style');
style.textContent = `
    .input-wrapper input.error {
        border-color: var(--error-color);
        box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.1);
    }

    .animate-spin {
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);