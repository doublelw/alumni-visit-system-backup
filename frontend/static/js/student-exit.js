/**
 * 学生出校申请相关功能
 */

class StudentExitApplication {
    constructor() {
        this.bindEvents();
    }

    bindEvents() {
        // 绑定审批按钮事件
        document.addEventListener('click', (e) => {
            if (e.target.matches('.approve-btn')) {
                const applicationId = e.target.dataset.id;
                const action = e.target.dataset.action;
                this.approveApplication(applicationId, action);
            }
        });

        // 绑定学生申请表单的学生选择事件
        const studentSelect = document.getElementById('studentSelect');
        if (studentSelect) {
            studentSelect.addEventListener('change', (e) => {
                this.handleStudentSelection(e.target.value, 'student');
            });
        }

        // 绑定家长申请表单的学生选择事件
        const parentStudentSelect = document.getElementById('parentStudentSelect');
        if (parentStudentSelect) {
            parentStudentSelect.addEventListener('change', (e) => {
                this.handleStudentSelection(e.target.value, 'parent');
            });
        }
    }

    // 加载最近申请
    async loadRecentApplications() {
        try {
            const response = await fetch('/api/student-exit/applications/recent', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (data.applications && data.applications.length > 0) {
                this.renderRecentApplications(data.applications);
            } else {
                this.showEmptyState("recentApplicationsList", "暂无最近申请");
            }
        } catch (error) {
            console.error("加载最近申请失败:", error);
            this.showErrorState("recentApplicationsList", "加载失败，请重试");
        }
    }

    // 加载待审批申请
    async loadPendingApprovals() {
        try {
            const response = await fetch('/api/student-exit/applications/pending-approval', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (data.applications && data.applications.length > 0) {
                this.renderPendingApprovals(data.applications);
            } else {
                this.showEmptyState("pendingApprovalsList", "暂无待审批申请");
            }
        } catch (error) {
            console.error("加载待审批申请失败:", error);
            this.showErrorState("pendingApprovalsList", "加载失败，请重试");
        }
    }

    // 渲染最近申请列表
    renderRecentApplications(applications) {
        const container = document.getElementById("recentApplicationsList");
        if (!container) return;

        const html = applications.map(app => `
            <div class="application-item" data-id="${app.id}">
                <div class="application-header">
                    <div class="student-info">
                        <span class="student-name">${app.student_name}</span>
                        <span class="student-class">${app.student_class || ''}</span>
                    </div>
                    <div class="application-status ${this.getStatusClass(app.application_status)}">
                        ${this.getStatusText(app.application_status)}
                    </div>
                </div>
                <div class="application-details">
                    <div class="detail-row">
                        <span class="label">出校时间:</span>
                        <span class="value">${app.exit_date} ${app.exit_time_start}-${app.exit_time_end}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">出校原因:</span>
                        <span class="value">${app.exit_reason}</span>
                    </div>
                    ${app.destination ? `
                    <div class="detail-row">
                        <span class="label">目的地:</span>
                        <span class="value">${app.destination}</span>
                    </div>
                    ` : ''}
                </div>
                <div class="approval-status">
                    ${this.renderApprovalStatus(app)}
                </div>
                ${app.application_status === 'approved' ? `
                <div class="qr-code-section mt-3">
                    <button class="btn btn-primary btn-sm" onclick="studentExitApp.showQRCode(${app.id})">
                        <i class="ri-qr-code-line"></i>
                        查看出校二维码
                    </button>
                </div>
                ` : ''}
            </div>
        `).join("");

        container.innerHTML = html;
    }

    // 渲染待审批申请列表
    renderPendingApprovals(applications) {
        const container = document.getElementById("pendingApprovalsList");
        if (!container) return;

        const html = applications.map(app => `
            <div class="approval-item" data-id="${app.id}">
                <div class="approval-header">
                    <div class="student-info">
                        <span class="student-name">${app.student_name}</span>
                        <span class="student-class">${app.student_class || ''}</span>
                    </div>
                    <div class="application-status ${this.getStatusClass(app.application_status)}">
                        ${this.getStatusText(app.application_status)}
                    </div>
                </div>
                <div class="approval-details">
                    <div class="detail-row">
                        <span class="label">出校时间:</span>
                        <span class="value">${app.exit_date} ${app.exit_time_start}-${app.exit_time_end}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">出校原因:</span>
                        <span class="value">${app.exit_reason}</span>
                    </div>
                    ${app.destination ? `
                    <div class="detail-row">
                        <span class="label">目的地:</span>
                        <span class="value">${app.destination}</span>
                    </div>
                    ` : ''}
                </div>
                <div class="approval-status">
                    ${this.renderApprovalStatus(app)}
                </div>
                ${app.can_approve ? `
                <div class="approval-actions">
                    <button class="btn btn-success btn-sm approve-btn" data-id="${app.id}" data-action="approve">
                        <i class="ri-check-line"></i>
                        通过
                    </button>
                    <button class="btn btn-danger btn-sm approve-btn" data-id="${app.id}" data-action="reject">
                        <i class="ri-close-line"></i>
                        拒绝
                    </button>
                </div>
                ${app.application_status === 'approved' ? `
                <div class="qr-code-section mt-3">
                    <button class="btn btn-primary btn-sm" onclick="studentExitApp.showQRCode(${app.id})">
                        <i class="ri-qr-code-line"></i>
                        查看出校二维码
                    </button>
                </div>
                ` : ''}
                ` : ''}
            </div>
        `).join("");

        container.innerHTML = html;
    }

    // 渲染审批状态
    renderApprovalStatus(app) {
        let statusHtml = '';

        if (app.parent_approval_status === 'pending') {
            statusHtml += '<span class="approval-badge pending">待家长审批</span>';
        } else if (app.parent_approval_status === 'approved') {
            statusHtml += '<span class="approval-badge approved">家长已通过</span>';
        } else if (app.parent_approval_status === 'rejected') {
            statusHtml += '<span class="approval-badge rejected">家长已拒绝</span>';
        }

        if (app.teacher_approval_status === 'pending') {
            statusHtml += '<span class="approval-badge pending">待班主任审批</span>';
        } else if (app.teacher_approval_status === 'approved') {
            statusHtml += '<span class="approval-badge approved">班主任已通过</span>';
        } else if (app.teacher_approval_status === 'rejected') {
            statusHtml += '<span class="approval-badge rejected">班主任已拒绝</span>';
        }

        return statusHtml;
    }

    // 获取状态样式类
    getStatusClass(status) {
        const statusMap = {
            'pending': 'status-pending',
            'parent_approved': 'status-parent-approved',
            'teacher_approved': 'status-teacher-approved',
            'approved': 'status-approved',
            'rejected': 'status-rejected',
            'completed': 'status-completed',
            'cancelled': 'status-cancelled'
        };
        return statusMap[status] || 'status-unknown';
    }

    // 获取状态文本
    getStatusText(status) {
        const statusMap = {
            'pending': '待审批',
            'parent_approved': '家长已通过',
            'teacher_approved': '等待家长知晓',
            'approved': '已批准',
            'rejected': '已拒绝',
            'completed': '已完成',
            'cancelled': '已取消'
        };
        return statusMap[status] || '未知状态';
    }

    // 审批申请
    async approveApplication(applicationId, action) {
        try {
            // 对于家长审批，需要先进行人脸验证
            const currentUser = await this.getCurrentUser();
            if (currentUser.user_type === 'parent' && action === 'approve') {
                // 家长同意时需要人脸验证
                const faceVerified = await this.verifyParentFace();
                if (!faceVerified) {
                    return; // 人脸验证失败，直接返回
                }
            }

            // 简化流程：教师和家长都无需填写审批意见
            const note = '';

            Utils.showLoading('正在提交审批...');

            const response = await fetch(`/api/student-exit/applications/${applicationId}/approve`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: action,
                    note: note || '',
                    face_verified: currentUser.user_type === 'parent' && action === 'approve' ? true : false
                })
            });

            const data = await response.json();
            if (data.success) {
                Utils.showToast(`审批${action === 'approve' ? '通过' : '拒绝'}成功`, 'success');
                // 重新加载申请列表
                this.loadPendingApprovals();
                this.loadRecentApplications();
            } else {
                Utils.showToast(data.message || '审批失败', 'error');
            }

        } catch (error) {
            console.error('审批申请失败:', error);
            Utils.showToast('审批失败，请重试', 'error');
        } finally {
            Utils.hideLoading();
        }
    }

    // 显示空状态
    showEmptyState(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="ri-inbox-line empty-icon"></i>
                    <p class="empty-message">${message}</p>
                </div>
            `;
        }
    }

    // 显示错误状态
    showErrorState(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <i class="ri-error-warning-line error-icon"></i>
                    <p class="error-message">${message}</p>
                    <button class="btn btn-outline btn-sm" onclick="studentExitApp.${containerId === 'recentApplicationsList' ? 'loadRecentApplications' : 'loadPendingApprovals'}()">
                        <i class="ri-refresh-line"></i>
                        重试
                    </button>
                </div>
            `;
        }
    }

    // 根据用户类型更新申请区域显示
    updateApplicationSectionsByUserType(user) {
        // 隐藏所有申请区域
        const recentSection = document.getElementById("recentApplicationsSection");
        const pendingSection = document.getElementById("pendingApprovalsSection");

        if (recentSection) recentSection.style.display = "none";
        if (pendingSection) pendingSection.style.display = "none";

        // 根据用户类型显示相应区域
        if (["student", "parent", "teacher"].includes(user.user_type)) {
            if (recentSection) {
                recentSection.style.display = "block";
                this.loadRecentApplications();
            }
        }

        // 如果是有审批权限的用户，显示待审批区域
        if ((user.user_type === "parent") || (user.user_type === "teacher" && user.is_class_teacher)) {
            if (pendingSection) {
                pendingSection.style.display = "block";
                this.loadPendingApprovals();
            }
        }
    }

    // 获取当前用户信息
    async getCurrentUser() {
        try {
            const response = await fetch('/api/auth/profile', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            return data.user;
        } catch (error) {
            console.error('获取用户信息失败:', error);
            return null;
        }
    }

    // 家长人脸验证
    async verifyParentFace() {
        return new Promise((resolve) => {
            // 创建人脸验证模态框
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            modal.innerHTML = `
                <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                    <h3 class="text-lg font-semibold mb-4">人脸验证</h3>
                    <p class="text-gray-600 mb-4">请进行人脸验证以确认您的身份</p>

                    <div class="border-2 border-dashed border-gray-300 rounded-lg p-4 mb-4 text-center">
                        <video id="parentFaceVideo" class="w-full rounded-lg mb-4" style="display: none;"></video>
                        <canvas id="parentFaceCanvas" class="hidden"></canvas>
                        <div id="faceVerificationStatus" class="text-sm text-gray-500">
                            <i class="ri-camera-line mr-1"></i>点击下方按钮开始人脸识别
                        </div>
                    </div>

                    <div class="flex justify-end space-x-3">
                        <button id="cancelFaceVerify" class="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                            取消
                        </button>
                        <button id="startFaceVerify" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                            开始验证
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            let videoStream = null;
            let isVerified = false;

            const video = document.getElementById('parentFaceVideo');
            const canvas = document.getElementById('parentFaceCanvas');
            const statusDiv = document.getElementById('faceVerificationStatus');

            // 绑定事件
            document.getElementById('cancelFaceVerify').onclick = () => {
                if (videoStream) {
                    videoStream.getTracks().forEach(track => track.stop());
                }
                document.body.removeChild(modal);
                resolve(false);
            };

            document.getElementById('startFaceVerify').onclick = async () => {
                try {
                    if (!videoStream) {
                        // 初始化摄像头
                        videoStream = await navigator.mediaDevices.getUserMedia({
                            video: { width: 640, height: 480 }
                        });
                        video.srcObject = videoStream;
                        video.style.display = 'block';
                        video.play();

                        statusDiv.innerHTML = '<i class="ri-camera-line mr-1"></i>摄像头已开启，请对准面部';
                        return;
                    }

                    // 捕获人脸图像
                    const context = canvas.getContext('2d');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);

                    const faceImage = canvas.toDataURL('image/jpeg', 0.8);

                    statusDiv.innerHTML = '<i class="ri-loader-4-line animate-spin mr-1"></i>正在验证人脸...';

                    // 发送到后端验证
                    const response = await fetch('/api/auth/face-login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            face_image: faceImage,
                            user_id: (await this.getCurrentUser()).id
                        })
                    });

                    const data = await response.json();
                    if (data.access_token) {
                        statusDiv.innerHTML = '<i class="ri-check-line text-green-600 mr-1"></i>人脸验证成功';
                        isVerified = true;

                        setTimeout(() => {
                            if (videoStream) {
                                videoStream.getTracks().forEach(track => track.stop());
                            }
                            document.body.removeChild(modal);
                            resolve(true);
                        }, 1000);
                    } else {
                        statusDiv.innerHTML = '<i class="ri-close-line text-red-600 mr-1"></i>人脸验证失败，请重试';
                    }

                } catch (error) {
                    console.error('人脸验证失败:', error);
                    statusDiv.innerHTML = '<i class="ri-error-warning-line text-red-600 mr-1"></i>人脸验证失败，请重试';
                }
            };
        });
    }

    // 显示出校二维码
    async showQRCode(applicationId) {
        try {
            Utils.showLoading('正在生成二维码...');

            const response = await fetch(`/api/student-exit/applications/${applicationId}/qr-code`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (data.qr_code) {
                this.showQRCodeModal(data, applicationId);
            } else {
                Utils.showToast('二维码生成失败', 'error');
            }

        } catch (error) {
            console.error('获取二维码失败:', error);
            Utils.showToast('获取二维码失败，请重试', 'error');
        } finally {
            Utils.hideLoading();
        }
    }

    // 显示二维码模态框
    showQRCodeModal(data, applicationId) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold text-gray-900">学生出校二维码</h3>
                    <button id="closeQRModal" class="text-gray-400 hover:text-gray-600">
                        <i class="ri-close-line text-2xl"></i>
                    </button>
                </div>

                <div class="text-center mb-4">
                    <div class="mb-4">
                        <div class="text-lg font-semibold text-gray-800 mb-2">
                            ${data.student_name || '学生姓名'}
                        </div>
                        <div class="text-sm text-gray-600">
                            ${data.class_id || '班级信息'}
                        </div>
                    </div>

                    <div class="border-2 border-gray-200 rounded-lg p-4 mb-4 bg-gray-50">
                        <div class="text-xs text-gray-500 mb-2">验证码</div>
                        <div class="text-3xl font-bold text-blue-600 tracking-widest">
                            ${data.verification_code || '000000'}
                        </div>
                        <div class="text-xs text-gray-500 mt-2">
                            请向保安人员出示此验证码
                        </div>
                    </div>

                    <div class="text-sm text-gray-600 mb-4">
                        <div><strong>出校时间:</strong> ${data.exit_date} ${data.exit_time_start}</div>
                        <div><strong>返校时间:</strong> ${data.exit_time_end}</div>
                        <div><strong>出校原因:</strong> ${data.exit_reason}</div>
                        ${data.destination ? `<div><strong>目的地:</strong> ${data.destination}</div>` : ''}
                    </div>

                    ${data.expires_at ? `
                    <div class="text-xs text-orange-600 bg-orange-50 p-2 rounded">
                        <i class="ri-time-line mr-1"></i>
                        二维码有效期至: ${new Date(data.expires_at).toLocaleString()}
                    </div>
                    ` : ''}
                </div>

                <div class="flex justify-center space-x-3">
                    <button id="closeQRModalBtn" class="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600">
                        关闭
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 绑定关闭事件
        const closeModal = () => {
            document.body.removeChild(modal);
        };

        document.getElementById('closeQRModal').onclick = closeModal;
        document.getElementById('closeQRModalBtn').onclick = closeModal;

        // 点击背景关闭
        modal.onclick = (e) => {
            if (e.target === modal) {
                closeModal();
            }
        };
    }

    // 加载可选学生列表
    async loadAvailableStudents(formType = 'student') {
        try {
            // 检查当前用户是否为学生
            const currentUser = await this.getCurrentUser();
            if (currentUser && currentUser.user_type === 'student') {
                // 学生用户自动加载自己的信息，隐藏选择下拉框
                await this.autoLoadStudentInfo(currentUser, formType);
                return;
            }

            // 非学生用户加载可选学生列表
            const response = await fetch('/api/student-exit/students', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (data.success && data.students) {
                this.populateStudentSelect(data.students, formType);
            }
        } catch (error) {
            console.error("加载学生列表失败:", error);
        }
    }

    // 自动加载学生信息（学生用户专用）
    async autoLoadStudentInfo(student, formType = 'student') {
        try {
            // 隐藏学生选择下拉框并移除required属性
            const studentSelectSection = document.getElementById('studentInfoSection');
            const studentSelect = document.getElementById('studentSelect');
            if (studentSelectSection) {
                studentSelectSection.style.display = 'none';
            }
            if (studentSelect) {
                studentSelect.removeAttribute('required');
            }

            // 显示学生信息卡片
            const displaySection = document.getElementById('studentInfoDisplay');
            const displayStudentId = document.getElementById('displayStudentId');
            const displayStudentName = document.getElementById('displayStudentName');
            const displayStudentClass = document.getElementById('displayStudentClass');

            if (displaySection && displayStudentId && displayStudentName && displayStudentClass) {
                displayStudentId.textContent = student.student_id || '';
                displayStudentName.textContent = student.real_name || '';
                displayStudentClass.textContent = student.class_id || '';
                displaySection.style.display = 'block';
            }

            // 自动填充紧急联系人信息
            this.autoFillEmergencyContact(student, formType);

            console.log('学生信息已自动加载:', student.real_name);
        } catch (error) {
            console.error("自动加载学生信息失败:", error);
        }
    }

    // 填充学生选择下拉框
    populateStudentSelect(students, formType = 'student') {
        const selectId = formType === 'parent' ? 'parentStudentSelect' : 'studentSelect';
        const studentSelect = document.getElementById(selectId);
        if (!studentSelect) return;

        // 清空现有选项
        studentSelect.innerHTML = formType === 'parent' ?
            '<option value="">请选择要申请出校的学生</option>' :
            '<option value="">请选择学生</option>';

        // 添加学生选项
        students.forEach(student => {
            const option = document.createElement('option');
            option.value = student.id;
            option.textContent = `${student.real_name} (${student.student_id}) - ${student.class_name}`;
            option.dataset.studentInfo = JSON.stringify(student);
            studentSelect.appendChild(option);
        });
    }

    // 处理学生选择
    async handleStudentSelection(studentId, formType = 'student') {
        if (!studentId) {
            // 清空学生信息显示
            this.hideStudentInfo(formType);
            return;
        }

        try {
            // 获取学生详细信息
            const response = await fetch(`/api/student-exit/student/${studentId}/info`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (data.success && data.student) {
                this.displayStudentInfo(data.student, formType);
                this.autoFillEmergencyContact(data.student, formType);
            }
        } catch (error) {
            console.error("获取学生信息失败:", error);
        }
    }

    // 显示学生信息
    displayStudentInfo(student, formType = 'student') {
        // 学生申请表单有学生信息显示区域
        if (formType === 'student') {
            const displaySection = document.getElementById('studentInfoDisplay');
            const displayStudentId = document.getElementById('displayStudentId');
            const displayStudentName = document.getElementById('displayStudentName');
            const displayStudentClass = document.getElementById('displayStudentClass');

            if (displaySection && displayStudentId && displayStudentName && displayStudentClass) {
                displayStudentId.textContent = student.student_id;
                displayStudentName.textContent = student.real_name;
                displayStudentClass.textContent = student.class_name;
                displaySection.style.display = 'block';
            }
        }
    }

    // 隐藏学生信息显示
    hideStudentInfo(formType = 'student') {
        if (formType === 'student') {
            const displaySection = document.getElementById('studentInfoDisplay');
            if (displaySection) {
                displaySection.style.display = 'none';
            }
        }
    }

    // 自动填充紧急联系人信息
    autoFillEmergencyContact(student, formType = 'student') {
        // 根据表单类型选择对应的紧急联系人输入框
        const contactId = formType === 'parent' ? 'parentEmergencyContact' : 'emergency_contact';
        const phoneId = formType === 'parent' ? 'parentEmergencyPhone' : 'emergency_phone';

        const emergencyContactInput = document.getElementById(contactId);
        const emergencyPhoneInput = document.getElementById(phoneId);

        if (emergencyContactInput && student.emergency_contact) {
            emergencyContactInput.value = student.emergency_contact;
        }

        if (emergencyPhoneInput && student.emergency_phone) {
            emergencyPhoneInput.value = student.emergency_phone;
        }
    }

    // 获取当前选中的学生ID（用于表单提交）
    getCurrentStudentId(formType = 'student') {
        // 对于学生用户，直接返回当前用户的ID
        if (formType === 'student' && AppState.user && AppState.user.user_type === 'student') {
            return AppState.user.id;
        }

        // 对于其他用户，从下拉框获取选择的ID
        const selectId = formType === 'parent' ? 'parentStudentSelect' : 'studentSelect';
        const studentSelect = document.getElementById(selectId);
        return studentSelect ? studentSelect.value : null;
    }

    // 重置表单状态（用于重新打开模态框时）
    resetFormState(formType = 'student') {
        if (formType === 'student') {
            // 显示学生选择下拉框（如果之前被隐藏了）
            const studentSelectSection = document.getElementById('studentInfoSection');
            const studentSelect = document.getElementById('studentSelect');
            if (studentSelectSection) {
                studentSelectSection.style.display = 'block';
            }
            if (studentSelect) {
                studentSelect.value = '';
                // 恢复required属性，因为HTML中原本就有required
                studentSelect.setAttribute('required', '');
            }

            // 隐藏学生信息卡片
            const displaySection = document.getElementById('studentInfoDisplay');
            if (displaySection) {
                displaySection.style.display = 'none';
            }
        }
    }
}

// 全局实例
const studentExitApp = new StudentExitApplication();

// 添加到全局作用域以便HTML中的onclick调用
window.studentExitApp = studentExitApp;