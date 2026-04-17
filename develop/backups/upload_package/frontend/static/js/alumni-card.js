/**
 * 电子校友卡功能模块
 */

class AlumniCard {
    constructor() {
        this.modal = null;
        this.cardData = null;
        this.isFlipped = false;
        this.qrCodeData = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadCardData();
    }

    bindEvents() {
        // 快捷操作中的电子校友卡按钮
        const quickAlumniCard = document.getElementById('quickAlumniCard');
        if (quickAlumniCard) {
            quickAlumniCard.addEventListener('click', () => {
                this.showCard();
            });
        }

        // 模态框关闭按钮
        const closeBtn = document.getElementById('closeAlumniCardModal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideCard();
            });
        }

        // 翻转卡片按钮
        const flipBtn = document.getElementById('flipCardBtn');
        if (flipBtn) {
            flipBtn.addEventListener('click', () => {
                this.flipCard();
            });
        }

        // 返回正面按钮
        const backToFrontBtn = document.getElementById('backToFrontBtn');
        if (backToFrontBtn) {
            backToFrontBtn.addEventListener('click', () => {
                this.showFront();
            });
        }

        // 下载卡片按钮
        const downloadBtn = document.getElementById('downloadCardBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadCard();
            });
        }

        // 分享卡片按钮
        const shareBtn = document.getElementById('shareCardBtn');
        if (shareBtn) {
            shareBtn.addEventListener('click', () => {
                this.shareCard();
            });
        }

        // 点击模态框背景关闭
        this.modal = document.getElementById('alumniCardModal');
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.hideCard();
                }
            });
        }
    }

    async loadCardData() {
        try {
            // 获取当前用户信息
            const token = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.TOKEN);
            if (!token) {
                console.warn('用户未登录');
                return;
            }

            console.log('开始加载校友卡数据，token:', token.substring(0, 20) + '...');

            const response = await fetch('/api/auth/profile', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('Profile API 响应状态:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('获取到用户数据:', data);
                this.cardData = data.user;
                this.prepareQRCodeData();
                console.log('校友卡数据准备完成');
            } else {
                console.error('获取用户信息失败，状态码:', response.status);
                const errorText = await response.text();
                console.error('错误详情:', errorText);
            }
        } catch (error) {
            console.error('加载校友卡数据失败:', error);
        }
    }

    prepareQRCodeData() {
        if (!this.cardData) return;

        // 准备QR码数据
        this.qrCodeData = {
            type: 'alumni_card',
            userId: this.cardData.id,
            realName: this.cardData.real_name,
            studentId: this.cardData.alumni_profile?.student_id || '',
            graduationYear: this.cardData.alumni_profile?.graduation_year || '',
            className: this.cardData.alumni_profile?.class_name || '',
            phone: this.cardData.phone,
            email: this.cardData.email,
            timestamp: new Date().toISOString(),
            signature: this.generateSignature()
        };
    }

    generateSignature() {
        // 简单的签名生成（实际项目中应该使用更安全的签名方式）
        const data = JSON.stringify(this.qrCodeData);
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(16);
    }

    async showCard() {
        if (!this.cardData) {
            await this.loadCardData();
            if (!this.cardData) {
                this.showToast('请先登录', 'error');
                return;
            }
        }

        this.updateCardContent();
        this.generateQRCode();
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    hideCard() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
        this.showFront(); // 重置到正面
    }

    updateCardContent() {
        if (!this.cardData) return;

        // 更新正面信息
        this.updateElement('cardRealName', this.cardData.real_name || '-');
        this.updateElement('cardStudentId', this.cardData.alumni_profile?.student_id || '-');
        this.updateElement('cardGraduationYear', this.cardData.alumni_profile?.graduation_year || '-');
        this.updateElement('cardClassName', this.cardData.alumni_profile?.class_name || '-');
        this.updateElement('cardDivision', this.cardData.alumni_profile?.division || '-');

        // 更新背面信息
        this.updateElement('cardPhone', this.cardData.phone || '-');
        this.updateElement('cardEmail', this.cardData.email || '-');
        this.updateElement('cardWorkUnit', this.cardData.alumni_profile?.work_unit || '-');
        this.updateElement('cardPosition', this.cardData.alumni_profile?.position || '-');
        this.updateElement('cardCurrentCity', this.cardData.alumni_profile?.current_city || '-');

        // 身份证号脱敏显示
        const idCard = this.cardData.alumni_profile?.id_card || '';
        if (idCard.length >= 4) {
            this.updateElement('cardIdCard', idCard.slice(0, 4) + '********' + idCard.slice(-4));
        }

        // 校友档案号
        this.updateElement('cardAlumniId', 'ALU' + String(this.cardData.id).padStart(6, '0'));

        // 发卡时间
        const createTime = this.cardData.alumni_profile?.created_at || new Date().toISOString();
        this.updateElement('cardIssueTime', new Date(createTime).toLocaleDateString());

        // 设置用户头像（如果有的话）
        this.updateUserPhoto();
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateUserPhoto() {
        const photoElement = document.getElementById('cardUserPhoto');
        if (!photoElement) return;

        // 如果用户有人脸识别照片，显示人脸照片
        if (this.cardData.alumni_profile?.face_photo) {
            photoElement.innerHTML = `<img src="${this.cardData.alumni_profile.face_photo}" alt="校友照片" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
        } else {
            // 显示默认图标
            photoElement.innerHTML = '<i class="ri-user-fill"></i>';
        }
    }

    async generateQRCode() {
        if (!this.qrCodeData) return;

        const qrContainer = document.getElementById('alumniCardQRCode');
        if (!qrContainer) return;

        try {
            // 清空容器
            qrContainer.innerHTML = '';

            // 创建canvas元素
            const canvas = document.createElement('canvas');
            qrContainer.appendChild(canvas);

            // 生成QR码
            await QRCode.toCanvas(canvas, JSON.stringify(this.qrCodeData), {
                width: 120,
                height: 120,
                margin: 1,
                color: {
                    dark: '#1976d2',
                    light: '#ffffff'
                },
                errorCorrectionLevel: 'M'
            });

        } catch (error) {
            console.error('生成QR码失败:', error);
            // 如果QR码生成失败，显示占位符
            qrContainer.innerHTML = '<div style="width: 120px; height: 120px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; border-radius: 8px;"><i class="ri-qr-code-line" style="font-size: 48px; color: #999;"></i></div>';
        }
    }

    flipCard() {
        const frontCard = document.getElementById('alumniCard');
        const backCard = document.getElementById('alumniCardBack');

        if (!this.isFlipped) {
            // 显示背面
            frontCard.style.display = 'none';
            backCard.style.display = 'block';
            this.isFlipped = true;
        } else {
            // 显示正面
            this.showFront();
        }
    }

    showFront() {
        const frontCard = document.getElementById('alumniCard');
        const backCard = document.getElementById('alumniCardBack');

        frontCard.style.display = 'block';
        backCard.style.display = 'none';
        this.isFlipped = false;
    }

    async downloadCard() {
        try {
            // 使用html2canvas库来截图（这里简化处理）
            const cardElement = document.getElementById('alumniCard');
            if (!cardElement) return;

            // 创建画布
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // 设置画布尺寸
            canvas.width = 700;
            canvas.height = 400;

            // 绘制背景
            const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
            gradient.addColorStop(0, '#1976d2');
            gradient.addColorStop(1, '#1565c0');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // 添加文字内容
            ctx.fillStyle = 'white';
            ctx.font = 'bold 24px Arial';
            ctx.fillText('辽宁省实验中学 - 电子校友卡', 50, 50);

            ctx.font = '18px Arial';
            ctx.fillText(`姓名：${this.cardData.real_name || '-'}`, 50, 100);
            ctx.fillText(`学号：${this.cardData.alumni_profile?.student_id || '-'}`, 50, 130);
            ctx.fillText(`毕业年份：${this.cardData.alumni_profile?.graduation_year || '-'}`, 50, 160);
            ctx.fillText(`班级：${this.cardData.alumni_profile?.class_name || '-'}`, 50, 190);

            // 下载图片
            const link = document.createElement('a');
            link.download = `校友卡_${this.cardData.real_name}_${Date.now()}.png`;
            link.href = canvas.toDataURL();
            link.click();

            this.showToast('校友卡已下载', 'success');
        } catch (error) {
            console.error('下载失败:', error);
            this.showToast('下载失败，请稍后重试', 'error');
        }
    }

    async shareCard() {
        try {
            if (navigator.share) {
                // 使用原生分享API
                await navigator.share({
                    title: '我的电子校友卡',
                    text: `我是辽宁省实验中学${this.cardData.alumni_profile?.graduation_year || ''}届校友${this.cardData.real_name}`,
                    url: window.location.origin
                });
            } else {
                // 复制到剪贴板
                const shareText = `我是辽宁省实验中学${this.cardData.alumni_profile?.graduation_year || ''}届校友${this.cardData.real_name}`;
                await navigator.clipboard.writeText(shareText);
                this.showToast('校友信息已复制到剪贴板', 'success');
            }
        } catch (error) {
            console.error('分享失败:', error);
            this.showToast('分享失败，请稍后重试', 'error');
        }
    }

    showToast(message, type = 'info') {
        // 创建或获取toast元素
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            toast.className = 'toast';
            document.body.appendChild(toast);
        }

        // 设置消息和样式
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="toast-icon ${this.getToastIcon(type)}"></i>
                <span class="toast-message">${message}</span>
            </div>
        `;

        // 显示toast
        toast.classList.add('show');

        // 3秒后隐藏
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'ri-check-line',
            error: 'ri-close-line',
            warning: 'ri-alert-line',
            info: 'ri-information-line'
        };
        return icons[type] || icons.info;
    }

    // 公共方法：刷新校友卡数据
    async refreshCard() {
        await this.loadCardData();
        if (this.cardData && this.modal.classList.contains('active')) {
            this.updateCardContent();
            this.generateQRCode();
        }
    }
}

// 初始化校友卡功能
document.addEventListener('DOMContentLoaded', () => {
    window.alumniCard = new AlumniCard();
});

// 导出给其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AlumniCard;
}