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
            const token = localStorage.getItem('auth_token');
            if (!token) {
                return;
            }

            const response = await fetch('/api/auth/profile', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.cardData = data.user;
                this.prepareQRCodeData();
            }
        } catch (error) {
            console.error('加载校友卡数据失败:', error);
        }
    }

    prepareQRCodeData() {
        if (!this.cardData) return;

        // 获取当前域名和端口
        const currentHost = window.location.origin;

        // 准备QR码数据 - 只保存校友档案API链接
        this.qrCodeData = `${currentHost}/api/alumni/profile/verify/${this.cardData.id}`;
    }

    
    async showCard() {
        if (!this.cardData) {
            await this.loadCardData();
            if (!this.cardData) {
                this.showToast('请先登录', 'error');
                return;
            }
        }

        // 移除已存在的模态框
        const existingModal = document.getElementById('newAlumniCardModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 创建新的校友卡模态框
        const alumniCardModal = document.createElement('div');
        alumniCardModal.id = 'newAlumniCardModal';
        alumniCardModal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 99999;
            padding: 20px;
        `;

        // 校友档案号
        const alumniId = 'ALU' + String(this.cardData.id).padStart(6, '0');

        // 发卡时间
        const issueTime = new Date(this.cardData.alumni_profile?.created_at || new Date()).toLocaleDateString();

        // 身份证号脱敏显示
        const idCard = this.cardData.alumni_profile?.id_card || '';
        const maskedIdCard = idCard.length >= 4 ?
            idCard.slice(0, 4) + '********' + idCard.slice(-4) : '';

          // 校友卡内容 - 参考电子身份证设计风格
        alumniCardModal.innerHTML = `
            <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 3px; border-radius: 16px; max-width: 95%; width: 360px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); position: relative; margin: 10px;">
                <!-- 关闭按钮 -->
                <button onclick="this.parentElement.parentElement.remove(); document.body.style.overflow='';" style="position: absolute; top: 8px; right: 8px; background: rgba(255,255,255,0.9); border: none; font-size: 18px; cursor: pointer; color: #666; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 50%; z-index: 10; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">×</button>

                <!-- 证件卡片主体 -->
                <div style="background: white; border-radius: 14px; overflow: hidden;">
                    <!-- 证件头部 - 国徽区域样式 -->
                    <div style="background: linear-gradient(135deg, #1976d2, #1565c0); color: white; padding: 16px; text-align: center; position: relative;">
                        <div style="position: absolute; top: 8px; left: 8px; background: rgba(255,255,255,0.2); padding: 3px 6px; border-radius: 3px; font-size: 9px; font-weight: 500; writing-mode: vertical-rl; text-orientation: upright;">
                            ALUMNI CARD
                        </div>
                        <div style="font-size: 14px; font-weight: 600; margin-bottom: 2px; letter-spacing: 1px;">辽宁省实验中学</div>
                        <div style="font-size: 18px; font-weight: bold; letter-spacing: 2px;">电子校友卡</div>
                        <div style="font-size: 10px; opacity: 0.9; margin-top: 2px;">ELECTRONIC ALUMNI CARD</div>
                    </div>

                    <!-- 校友信息区域 -->
                    <div style="padding: 12px;">
                        <!-- 姓名区域 - 身份证样式 -->
                        <div style="margin-bottom: 8px;">
                            <div style="font-size: 10px; color: #666; margin-bottom: 2px; font-weight: 500;">姓名 NAME</div>
                            <div style="font-size: 18px; font-weight: bold; color: #333; border-bottom: 1px solid #e9ecef; padding-bottom: 3px; letter-spacing: 1px;">${this.cardData.real_name || '校友姓名'}</div>
                        </div>

                        <!-- 基本信息网格 - 身份证信息样式 -->
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px 6px; margin-bottom: 8px; font-size: 11px;">
                            <div>
                                <div style="font-size: 9px; color: #666; margin-bottom: 1px;">学号</div>
                                <div style="font-weight: 600; color: #333; font-family: 'Courier New', monospace; font-size: 10px;">${this.cardData.alumni_profile?.student_id || 'N/A'}</div>
                            </div>
                            <div>
                                <div style="font-size: 9px; color: #666; margin-bottom: 1px;">毕业年份</div>
                                <div style="font-weight: 600; color: #333; font-size: 10px;">${this.cardData.alumni_profile?.graduation_year || 'N/A'}</div>
                            </div>
                            <div>
                                <div style="font-size: 9px; color: #666; margin-bottom: 1px;">班级</div>
                                <div style="font-weight: 600; color: #333; font-size: 10px;">${this.cardData.alumni_profile?.class_name || 'N/A'}</div>
                            </div>
                            <div>
                                <div style="font-size: 9px; color: #666; margin-bottom: 1px;">届别</div>
                                <div style="font-weight: 600; color: #333; font-size: 10px;">${this.cardData.alumni_profile?.division || 'N/A'}</div>
                            </div>
                        </div>

                        <!-- 扩展信息区域 -->
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px 4px; margin-bottom: 8px; font-size: 10px;">
                            <div>
                                <div style="font-size: 9px; color: #666; margin-bottom: 1px;">所在城市</div>
                                <div style="font-weight: 600; color: #333; font-size: 10px;">${this.cardData.alumni_profile?.city || 'N/A'}</div>
                            </div>
                            <div>
                                <div style="font-size: 9px; color: #666; margin-bottom: 1px;">工作单位</div>
                                <div style="font-weight: 600; color: #333; font-size: 10px; word-break: break-all;">${this.cardData.alumni_profile?.company || 'N/A'}</div>
                            </div>
                        </div>

                        <!-- 职务信息（如果有） -->
                        <div style="margin-bottom: 8px; font-size: 10px;">
                            <div style="font-size: 9px; color: #666; margin-bottom: 1px;">职务</div>
                            <div style="font-weight: 600; color: #333; font-size: 10px;">${this.cardData.alumni_profile?.position || 'N/A'}</div>
                        </div>

                        <!-- 二维码和档案信息区域 -->
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                            <!-- 档案信息 -->
                            <div style="flex: 1; padding-right: 8px;">
                                <div style="font-size: 9px; color: #666; margin-bottom: 1px;">发卡时间 ISSUE DATE</div>
                                <div style="font-weight: 600; color: #333; font-size: 9px;">${issueTime}</div>
                                <div style="font-size: 9px; color: #666; margin-top: 4px; margin-bottom: 1px;">档案号 ARCHIVE NO.</div>
                                <div style="font-weight: 600; color: #1976d2; font-family: 'Courier New', monospace; font-size: 9px; word-break: break-all;">${alumniId}</div>
                                <div style="font-size: 9px; color: #666; margin-top: 4px; margin-bottom: 1px;">电话 TEL</div>
                                <div style="font-weight: 600; color: #333; font-size: 9px; word-break: break-all;">${this.cardData.phone || 'N/A'}</div>
                                <div style="font-size: 9px; color: #666; margin-top: 4px; margin-bottom: 1px;">身份证 ID</div>
                                <div style="font-weight: 600; color: #333; font-family: 'Courier New', monospace; font-size: 9px;">${maskedIdCard}</div>
                            </div>

                            <!-- 二维码区域 -->
                            <div style="text-align: center; flex-shrink: 0;">
                                <div style="background: #f8f9fa; border: 1px solid #e9ecef; padding: 8px; border-radius: 6px; display: inline-block;">
                                    <div style="font-size: 8px; color: #666; margin-bottom: 4px; text-align: center; font-weight: 500;">扫码验证</div>
                                    <div id="alumniQRCode" style="background: white; border: 1px solid #1976d2; padding: 4px; border-radius: 4px; display: inline-block; box-shadow: 0 1px 4px rgba(25,118,210,0.15);">
                                        <!-- 校友QR码将在这里显示 -->
                                    </div>
                                    <div style="font-size: 7px; color: #999; margin-top: 4px; text-align: center;">校友身份验证</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 证件底部 -->
                    <div style="background: #f8f9fa; padding: 8px 16px; text-align: center; border-top: 1px solid #e9ecef;">
                        <div style="font-size: 10px; color: #666; font-style: italic;">此卡为校友身份唯一有效证明 · Valid alumni identification</div>
                    </div>
                </div>

                <!-- 操作按钮 -->
                <div style="padding: 12px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 0 0 14px 14px;">
                    <div style="display: flex; gap: 8px;">
                        <button onclick="alumniCard.downloadCard()" style="flex: 1; background: linear-gradient(135deg, #28a745, #20c997); color: white; border: none; padding: 10px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: opacity 0.2s; box-shadow: 0 3px 10px rgba(40,167,69,0.3);" ontouchstart="this.style.opacity='0.8'" ontouchend="this.style.opacity='1'">
                            <i class="ri-download-line" style="margin-right: 3px; font-size: 12px;"></i>下载卡片
                        </button>
                        <button onclick="alumniCard.shareCard()" style="flex: 1; background: linear-gradient(135deg, #007bff, #0056b3); color: white; border: none; padding: 10px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: opacity 0.2s; box-shadow: 0 3px 10px rgba(0,123,255,0.3);" ontouchstart="this.style.opacity='0.8'" ontouchend="this.style.opacity='1'">
                            <i class="ri-share-line" style="margin-right: 3px; font-size: 12px;"></i>分享卡片
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(alumniCardModal);
        document.body.style.overflow = 'hidden';

        // 生成QR码
        this.generateQRCode();
    }

    hideCard() {
        // 移除新创建的校友卡模态框
        const modal = document.getElementById('newAlumniCardModal');
        if (modal) {
            modal.remove();
        }

        // 同时隐藏原始模态框（如果存在）
        const originalModal = document.getElementById('alumniCardModal');
        if (originalModal) {
            originalModal.style.display = 'none';
        }

        // 恢复body滚动
        document.body.style.overflow = '';
    }

    async generateQRCode() {
        console.log('generateQRCode 方法被调用');

        if (!this.qrCodeData) {
            console.warn('QR码数据为空，无法生成二维码');
            return;
        }

        // 等待QRCode库加载
        await this.waitForQRCodeLibrary();

        // 检查QRCode库是否可用
        if (typeof QRCode === 'undefined') {
            console.error('QRCode库未加载');
            this.showQRPlaceholder('QR库未加载');
            return;
        }

        // 查找已存在的QR码容器
        const qrContainer = document.getElementById('alumniQRCode');
        if (!qrContainer) {
            console.warn('未找到QR码容器');
            return;
        }

        console.log('开始生成QR码，数据:', this.qrCodeData);

        try {
            // 生成真实的QR码 (80x80 更大更清晰)
            const canvas = document.createElement('canvas');
            await QRCode.toCanvas(canvas, JSON.stringify(this.qrCodeData), {
                width: 80,
                height: 80,
                margin: 1,
                color: {
                    dark: '#1976d2',
                    light: '#ffffff'
                },
                errorCorrectionLevel: 'M'
            });

            console.log('校友QR码生成成功，Canvas尺寸:', canvas.width, 'x', canvas.height);

            // 将Canvas转换为图片
            const img = document.createElement('img');
            const dataURL = canvas.toDataURL('image/png');
            img.src = dataURL;
            img.style.cssText = `
                width: 80px;
                height: 80px;
                display: block;
                border: none;
                border-radius: 4px;
                background: white;
            `;

            // 清空容器并添加图片
            qrContainer.innerHTML = '';
            qrContainer.appendChild(img);

            console.log('校友QR码已添加到校友卡，长度:', dataURL.length);

            // 添加图片加载事件监听
            img.onload = () => {
                console.log('校友QR码图片加载成功，电子校友卡完全可用！');
            };
            img.onerror = (error) => {
                console.error('校友QR码图片加载失败:', error);
                qrContainer.innerHTML = '<div style="width: 80px; height: 80px; background: #ffebee; display: flex; align-items: center; justify-content: center; border-radius: 4px; border: 1px solid #ffcdd2; font-size: 10px; color: #d32f2f; text-align: center;">加载失败</div>';
            };

        } catch (error) {
            console.error('生成校友QR码失败:', error);
            qrContainer.innerHTML = `<div style="width: 80px; height: 80px; background: #ffebee; display: flex; align-items: center; justify-content: center; border-radius: 4px; border: 1px solid #ffcdd2; font-size: 10px; color: #d32f2f; text-align: center;">生成失败</div>`;
        }
    }

    
    async waitForQRCodeLibrary(maxWaitTime = 5000) {
        const startTime = Date.now();
        console.log('等待QRCode库加载...');

        while (typeof QRCode === 'undefined') {
            if (Date.now() - startTime > maxWaitTime) {
                console.error('等待QRCode库超时');
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        if (typeof QRCode !== 'undefined') {
            console.log('QRCode库已加载');
        }
    }

    showQRPlaceholder(message) {
        const qrContainer = document.getElementById('alumniCardQRCode');
        if (qrContainer) {
            const canvasContainer = qrContainer.querySelector('[style*="display: flex"]');
            if (canvasContainer) {
                canvasContainer.innerHTML = `<div style="width: 50px; height: 50px; background: #ffebee; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 2px; border: 1px solid #ffcdd2; font-size: 8px; color: #d32f2f; text-align: center;">
                    <i class="ri-error-warning-line" style="font-size: 16px; color: #d32f2f;"></i>
                    <span>${message}</span>
                </div>`;
            }
        }
    }

  
    
    async downloadCard() {
        try {
            // 使用html2canvas库来截图新的模态框
            const modal = document.getElementById('newAlumniCardModal');
            if (!modal) return;

            const cardElement = modal.querySelector('[style*="background: white"]');
            if (!cardElement) return;

            // 检查是否可以使用html2canvas
            if (typeof html2canvas !== 'undefined') {
                // 使用html2canvas进行截图
                const canvas = await html2canvas(cardElement, {
                    scale: 2,
                    backgroundColor: '#ffffff',
                    logging: false
                });

                // 下载图片
                const link = document.createElement('a');
                link.download = `校友卡_${this.cardData.real_name}_${Date.now()}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();

                this.showToast('校友卡已下载', 'success');
            } else {
                // 降级方案：手动绘制校友卡
                this.downloadSimpleCard();
            }
        } catch (error) {
            console.error('下载失败:', error);
            this.showToast('下载失败，请稍后重试', 'error');
        }
    }

  downloadSimpleCard() {
        try {
            // 创建画布
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // 设置画布尺寸 (更接近手机屏幕比例)
            canvas.width = 720;
            canvas.height = 960;

            // 绘制白色背景
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // 绘制顶部蓝色条
            const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
            gradient.addColorStop(0, '#1976d2');
            gradient.addColorStop(1, '#1565c0');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, 160);

            // 添加顶部装饰线
            ctx.strokeStyle = 'rgba(255,255,255,0.3)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(20, 130);
            ctx.lineTo(canvas.width - 20, 130);
            ctx.stroke();

            // 添加校徽区域装饰
            ctx.fillStyle = 'rgba(255,255,255,0.1)';
            ctx.beginPath();
            ctx.arc(80, 80, 30, 0, Math.PI * 2);
            ctx.fill();

            // 添加标题
            ctx.fillStyle = 'white';
            ctx.font = 'bold 24px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('辽宁省实验中学', canvas.width / 2, 60);
            ctx.font = 'bold 32px Arial';
            ctx.fillText('电子校友卡', canvas.width / 2, 95);

            // 添加英文标题
            ctx.font = '14px Arial';
            ctx.fillText('ELECTRONIC ALUMNI CARD', canvas.width / 2, 120);

            // 校友档案号
            const alumniId = 'ALU' + String(this.cardData.id).padStart(6, '0');
            ctx.font = '12px monospace';
            ctx.fillStyle = 'rgba(255,255,255,0.9)';
            ctx.fillText(`档案号: ${alumniId}`, canvas.width / 2, 145);

            // 绘制校友信息区域 - 仿身份证布局
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(30, 180, canvas.width - 60, 600);

            // 添加边框
            ctx.strokeStyle = '#e9ecef';
            ctx.lineWidth = 1;
            ctx.strokeRect(30, 180, canvas.width - 60, 600);

            // 左侧信息
            ctx.textAlign = 'left';
            ctx.fillStyle = '#333333';

            // 姓名
            ctx.font = 'bold 28px Arial';
            ctx.fillText('姓名', 60, 230);
            ctx.font = '24px Arial';
            ctx.fillText(this.cardData.real_name || '-', 120, 230);

            // 绘制分隔线
            ctx.strokeStyle = '#e9ecef';
            ctx.beginPath();
            ctx.moveTo(60, 250);
            ctx.lineTo(canvas.width - 60, 250);
            ctx.stroke();

            // 基本信息 - 仿身份证紧凑布局
            const leftInfoItems = [
                { label: '学号', value: this.cardData.alumni_profile?.student_id || '-', y: 290 },
                { label: '毕业年份', value: this.cardData.alumni_profile?.graduation_year || '-', y: 330 }
            ];

            const rightInfoItems = [
                { label: '班级', value: this.cardData.alumni_profile?.class_name || '-', y: 290 },
                { label: '届别', value: this.cardData.alumni_profile?.division || '-', y: 330 }
            ];

            // 扩展信息
            const extendedInfoItems = [
                { label: '所在城市', value: this.cardData.alumni_profile?.city || '-', y: 370 },
                { label: '工作单位', value: this.cardData.alumni_profile?.company || '-', y: 370 }
            ];

            const positionInfo = [
                { label: '职务', value: this.cardData.alumni_profile?.position || '-', y: 410 }
            ];

            // 底部信息
            const bottomInfoItems = [
                { label: '联系电话', value: this.cardData.phone || '-', y: 450 },
                { label: '身份证号', value: this.maskIdCard(this.cardData.alumni_profile?.id_card) || '-', y: 480 }
            ];

            // 绘制基本信息（两列）
            ctx.font = '16px Arial';
            ctx.fillStyle = '#666666';

            leftInfoItems.forEach(item => {
                ctx.fillText(item.label, 60, item.y);
                ctx.fillStyle = '#333333';
                ctx.fillText(item.value, 150, item.y);
                ctx.fillStyle = '#666666';
            });

            rightInfoItems.forEach(item => {
                ctx.fillText(item.label, 340, item.y);
                ctx.fillStyle = '#333333';
                ctx.fillText(item.value, 400, item.y);
                ctx.fillStyle = '#666666';
            });

            // 绘制扩展信息（两列）
            ctx.font = '15px Arial';

            // 城市信息（左列）
            ctx.fillText(extendedInfoItems[0].label, 60, extendedInfoItems[0].y);
            ctx.fillStyle = '#333333';
            ctx.fillText(extendedInfoItems[0].value, 150, extendedInfoItems[0].y);
            ctx.fillStyle = '#666666';

            // 工作单位信息（右列，可能较长需要换行）
            ctx.fillText(extendedInfoItems[1].label, 340, extendedInfoItems[1].y);
            ctx.fillStyle = '#333333';
            const maxWidth = 160;
            const companyText = extendedInfoItems[1].value;
            let usedLines = 1; // 记录工作单位占用的行数

            if (ctx.measureText(companyText).width > maxWidth) {
                const words = companyText.split('');
                let line = '';
                let y = extendedInfoItems[1].y;
                for (let i = 0; i < words.length; i++) {
                    const testLine = line + words[i];
                    if (ctx.measureText(testLine).width > maxWidth && line !== '') {
                        ctx.fillText(line, 400, y);
                        line = words[i];
                        y += 18;
                        usedLines++;
                    } else {
                        line = testLine;
                    }
                }
                ctx.fillText(line, 400, y);
            } else {
                ctx.fillText(companyText, 400, extendedInfoItems[1].y);
            }
            ctx.fillStyle = '#666666';

            // 职务信息 - 需要根据工作单位是否换行来调整Y坐标
            const adjustedPositionY = 410 + (usedLines > 1 ? (usedLines - 1) * 18 : 0);
            ctx.font = '15px Arial';
            ctx.fillText(positionInfo[0].label, 60, adjustedPositionY);
            ctx.fillStyle = '#333333';
            ctx.fillText(positionInfo[0].value, 150, adjustedPositionY);
            ctx.fillStyle = '#666666';

            // 底部信息 - 也需要调整Y坐标
            const adjustedBottomY = 450 + (usedLines > 1 ? (usedLines - 1) * 18 : 0);
            ctx.font = '14px Arial';
            bottomInfoItems.forEach((item, index) => {
                const currentY = adjustedBottomY + (index * 25);
                ctx.fillText(item.label, 60, currentY);
                ctx.fillStyle = '#333333';
                ctx.fillText(item.value, 150, currentY);
                ctx.fillStyle = '#666666';
            });

    
            // 右侧QR码区域
            if (this.qrCodeData) {
                // 生成二维码
                const qrCanvas = document.createElement('canvas');
                const QRCode = window.QRCode;

                QRCode.toCanvas(qrCanvas, this.qrCodeData, {
                    width: 180,
                    height: 180,
                    margin: 1,
                    color: {
                        dark: '#1976d2',
                        light: '#ffffff'
                    },
                    errorCorrectionLevel: 'M'
                }).then(() => {
                    // 绘制QR码到校友卡中间下方
                    const qrSize = 180;
                    const qrX = (canvas.width - qrSize) / 2; // 水平居中
                    const qrY = canvas.height - 280; // 距离底部280px

                    // QR码背景
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect(qrX - 10, qrY - 10, qrSize + 20, qrSize + 20);
                    ctx.strokeStyle = '#1976d2';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(qrX - 10, qrY - 10, qrSize + 20, qrSize + 20);

                    // 绘制QR码
                    ctx.drawImage(qrCanvas, qrX, qrY, qrSize, qrSize);

                    // QR码说明
                    ctx.fillStyle = '#666666';
                    ctx.font = '14px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText('扫码验证校友身份', canvas.width / 2, qrY + qrSize + 30);

                    // 完成下载
                    this.completeDownload(canvas);
                              }).catch(error => {
                    console.error('QR码生成失败:', error);
                    // 不生成QR码的情况下继续下载
                    this.completeDownload(canvas);
                });
            } else {
                this.completeDownload(canvas);
            }

        } catch (error) {
            console.error('下载失败:', error);
            this.showToast('下载失败，请稍后重试', 'error');
        }
    }

    completeDownload(canvas) {
        try {
            const ctx = canvas.getContext('2d');

            // 添加校训
            ctx.textAlign = 'center';
            ctx.fillStyle = '#1976d2';
            ctx.font = 'italic 16px Arial';
            ctx.fillText('明心知往，力行求至', canvas.width / 2, 850);

            ctx.font = '14px Arial';
            ctx.fillStyle = '#666666';
            ctx.fillText('辽宁省实验中学校训', canvas.width / 2, 875);

            // 底部信息
            ctx.font = '12px Arial';
            ctx.fillText('此卡为校友身份唯一有效证明', canvas.width / 2, 910);

            // 发卡时间
            const issueTime = new Date(this.cardData.alumni_profile?.created_at || new Date()).toLocaleDateString();
            ctx.fillText(`发卡时间: ${issueTime}`, canvas.width / 2, 935);

            // 下载图片
            const link = document.createElement('a');
            link.download = `校友卡_${this.cardData.real_name}_${Date.now()}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();

            this.showToast('校友卡已下载', 'success');
        } catch (error) {
            console.error('完成下载失败:', error);
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

    maskIdCard(idCard) {
        if (!idCard) return 'N/A';
        if (idCard.length <= 4) return idCard;
        return idCard.slice(0, 3) + '*'.repeat(idCard.length - 6) + idCard.slice(-3);
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
        const modal = document.getElementById('newAlumniCardModal');
        if (this.cardData && modal) {
            // 如果校友卡正在显示，重新渲染
            modal.remove();
            await this.showCard();
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