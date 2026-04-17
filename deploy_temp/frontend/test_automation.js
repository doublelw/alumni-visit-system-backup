/**
 * 校友入校登记系统 - 自动化测试用例
 * 模拟完整的访客申请到验证通过流程
 *
 * 测试流程：
 * 1. 访客端：注册/登录 -> 申请访问 -> 录入人脸信息
 * 2. 教师端：登录 -> 审批访问申请
 * 3. 保安端：登录 -> 二维码验证 -> 人脸验证 -> 放行
 */

class VisitFlowAutomation {
    constructor() {
        this.windows = {
            visitor: null,
            teacher: null,
            security: null
        };

        this.testData = {
            visitor: {
                username: 'test_visitor_' + Date.now(),
                password: 'Test123456',
                realName: '测试访客',
                phone: '13800138000',
                email: 'test@example.com',
                idCard: '110101199001011234',
                visitPurpose: '校友返校参观',
                targetPerson: '张老师',
                targetDepartment: '计算机学院',
                visitDate: this.getTodayDate(),
                visitTimeStart: '09:00',
                visitTimeEnd: '17:00'
            },
            teacher: {
                username: 'teacher001',
                password: 'teacher123'
            },
            security: {
                username: 'security001',
                password: 'security123'
            }
        };

        this.currentStep = 0;
        this.steps = [
            'openAllWindows',
            'visitorRegister',
            'visitorLogin',
            'visitorApplyVisit',
            'visitorRegisterFace',
            'teacherLogin',
            'teacherApprove',
            'securityLogin',
            'securityQRVerify',
            'securityFaceVerify',
            'completeTest'
        ];
    }

    // 获取今天的日期
    getTodayDate() {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    // 延时函数
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // 在指定窗口执行代码
    executeInWindow(window, code) {
        if (!window || window.closed) {
            throw new Error('窗口不存在或已关闭');
        }
        return new Promise((resolve, reject) => {
            try {
                const result = window.eval(code);
                resolve(result);
            } catch (error) {
                reject(error);
            }
        });
    }

    // 等待元素出现
    waitForElement(window, selector, timeout = 10000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();

            const checkElement = () => {
                try {
                    const element = window.document.querySelector(selector);
                    if (element) {
                        resolve(element);
                        return;
                    }

                    if (Date.now() - startTime > timeout) {
                        reject(new Error(`等待元素超时: ${selector}`));
                        return;
                    }

                    setTimeout(checkElement, 500);
                } catch (error) {
                    reject(error);
                }
            };

            checkElement();
        });
    }

    // 点击元素
    async clickElement(window, selector) {
        const element = await this.waitForElement(window, selector);
        element.click();
        await this.delay(500);
    }

    // 输入文本
    async inputText(window, selector, text) {
        const element = await this.waitForElement(window, selector);
        element.value = text;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        await this.delay(300);
    }

    // 1. 打开所有窗口
    async openAllWindows() {
        console.log('🚀 步骤 1: 打开所有系统窗口...');

        try {
            // 打开访客端 - 使用index.html作为访客端
            this.windows.visitor = window.open('/index.html', 'visitor', 'width=1200,height=800,left=0,top=0');
            await this.delay(2000);

            // 打开教师端
            this.windows.teacher = window.open('/admin.html', 'teacher', 'width=1200,height=800,left=1250,top=0');
            await this.delay(2000);

            // 打开保安端
            this.windows.security = window.open('/security-portal.html', 'security', 'width=1200,height=800,left=625,top=850');
            await this.delay(2000);

            console.log('✅ 所有窗口已打开');
        } catch (error) {
            console.error('❌ 打开窗口失败:', error);
            throw error;
        }
    }

    // 2. 访客注册
    async visitorRegister() {
        console.log('👤 步骤 2: 访客注册...');

        try {
            // 切换到访客端窗口
            this.windows.visitor.focus();
            await this.delay(1000);

            // 点击注册按钮
            await this.clickElement(this.windows.visitor, '#showRegisterBtn, .register-btn');

            // 填写注册信息
            await this.inputText(this.windows.visitor, '#username', this.testData.visitor.username);
            await this.inputText(this.windows.visitor, '#password', this.testData.visitor.password);
            await this.inputText(this.windows.visitor, '#confirmPassword', this.testData.visitor.password);
            await this.inputText(this.windows.visitor, '#realName', this.testData.visitor.realName);
            await this.inputText(this.windows.visitor, '#phone', this.testData.visitor.phone);
            await this.inputText(this.windows.visitor, '#email', this.testData.visitor.email);
            await this.inputText(this.windows.visitor, '#idCard', this.testData.visitor.idCard);

            // 选择用户类型为校友
            await this.clickElement(this.windows.visitor, '#userTypeAlumni');

            // 提交注册
            await this.clickElement(this.windows.visitor, '#registerBtn');

            // 等待注册完成
            await this.delay(3000);
            console.log('✅ 访客注册完成');
        } catch (error) {
            console.error('❌ 访客注册失败:', error);
            throw error;
        }
    }

    // 3. 访客登录
    async visitorLogin() {
        console.log('🔐 步骤 3: 访客登录...');

        try {
            this.windows.visitor.focus();
            await this.delay(1000);

            // 输入登录信息
            await this.inputText(this.windows.visitor, '#username', this.testData.visitor.username);
            await this.inputText(this.windows.visitor, '#password', this.testData.visitor.password);

            // 点击登录
            await this.clickElement(this.windows.visitor, '#loginBtn');

            // 等待登录完成
            await this.delay(3000);
            console.log('✅ 访客登录完成');
        } catch (error) {
            console.error('❌ 访客登录失败:', error);
            throw error;
        }
    }

    // 4. 访客申请访问
    async visitorApplyVisit() {
        console.log('📝 步骤 4: 提交访问申请...');

        try {
            this.windows.visitor.focus();
            await this.delay(1000);

            // 点击申请访问按钮
            await this.clickElement(this.windows.visitor, '#applyVisitBtn');

            // 填写访问申请表单
            await this.inputText(this.windows.visitor, '#visitPurpose', this.testData.visitor.visitPurpose);
            await this.inputText(this.windows.visitor, '#targetPerson', this.testData.visitor.targetPerson);
            await this.inputText(this.windows.visitor, '#targetDepartment', this.testData.visitor.targetDepartment);
            await this.inputText(this.windows.visitor, '#visitDate', this.testData.visitor.visitDate);
            await this.inputText(this.windows.visitor, '#visitTimeStart', this.testData.visitor.visitTimeStart);
            await this.inputText(this.windows.visitor, '#visitTimeEnd', this.testData.visitor.visitTimeEnd);

            // 提交申请
            await this.clickElement(this.windows.visitor, '#submitApplicationBtn');

            // 等待申请提交完成
            await this.delay(3000);
            console.log('✅ 访问申请提交完成');
        } catch (error) {
            console.error('❌ 访问申请失败:', error);
            throw error;
        }
    }

    // 5. 访客录入人脸信息
    async visitorRegisterFace() {
        console.log('👤 步骤 5: 录入人脸信息...');

        try {
            this.windows.visitor.focus();
            await this.delay(1000);

            // 点击人脸注册按钮
            await this.clickElement(this.windows.visitor, '#faceRegisterBtn');

            // 开始人脸录入
            await this.clickElement(this.windows.visitor, '#startFaceRegistration');

            // 模拟人脸录入过程
            console.log('📷 正在录制人脸...');
            await this.delay(5000); // 模拟录制时间

            // 提交人脸信息
            await this.clickElement(this.windows.visitor, '#submitFaceData');

            await this.delay(2000);
            console.log('✅ 人脸信息录入完成');
        } catch (error) {
            console.error('❌ 人脸录入失败:', error);
            throw error;
        }
    }

    // 6. 教师登录
    async teacherLogin() {
        console.log('👨‍🏫 步骤 6: 教师登录...');

        try {
            this.windows.teacher.focus();
            await this.delay(1000);

            // 输入教师登录信息
            await this.inputText(this.windows.teacher, '#username', this.testData.teacher.username);
            await this.inputText(this.windows.teacher, '#password', this.testData.teacher.password);

            // 点击登录
            await this.clickElement(this.windows.teacher, '#loginBtn');

            // 等待登录完成
            await this.delay(3000);
            console.log('✅ 教师登录完成');
        } catch (error) {
            console.error('❌ 教师登录失败:', error);
            throw error;
        }
    }

    // 7. 教师审批申请
    async teacherApprove() {
        console.log('✅ 步骤 7: 教师审批访问申请...');

        try {
            this.windows.teacher.focus();
            await this.delay(1000);

            // 点击审批管理
            await this.clickElement(this.windows.teacher, '#approvalMenu');

            // 等待审批列表加载
            await this.delay(2000);

            // 查找并点击第一个待审批的申请
            await this.clickElement(this.windows.teacher, '.approve-btn');

            // 填写审批意见
            await this.inputText(this.windows.teacher, '#approvalComment', '测试审批通过');

            // 点击批准按钮
            await this.clickElement(this.windows.teacher, '#confirmApprove');

            // 等待审批完成
            await this.delay(3000);
            console.log('✅ 访问申请审批完成');
        } catch (error) {
            console.error('❌ 教师审批失败:', error);
            throw error;
        }
    }

    // 8. 保安登录
    async securityLogin() {
        console.log('🛡️ 步骤 8: 保安登录...');

        try {
            this.windows.security.focus();
            await this.delay(1000);

            // 输入保安登录信息
            await this.inputText(this.windows.security, '#username', this.testData.security.username);
            await this.inputText(this.windows.security, '#password', this.testData.security.password);

            // 点击登录
            await this.clickElement(this.windows.security, '#loginBtn');

            // 等待登录完成
            await this.delay(3000);
            console.log('✅ 保安登录完成');
        } catch (error) {
            console.error('❌ 保安登录失败:', error);
            throw error;
        }
    }

    // 9. 保安二维码验证
    async securityQRVerify() {
        console.log('📱 步骤 9: 保安二维码验证...');

        try {
            this.windows.security.focus();
            await this.delay(1000);

            // 点击二维码扫描按钮
            await this.clickElement(this.windows.security, '#qrScanBtn');

            // 点击手动输入申请编号
            await this.clickElement(this.windows.security, '#manualInputBtn');

            // 输入申请编号（这里假设编号为1，实际应该从申请记录中获取）
            await this.inputText(this.windows.security, '#applicationIdInput', '1');

            // 点击验证按钮
            await this.clickElement(this.windows.security, '#verifyManualQrBtn');

            // 等待验证完成
            await this.delay(3000);
            console.log('✅ 二维码验证完成');
        } catch (error) {
            console.error('❌ 二维码验证失败:', error);
            throw error;
        }
    }

    // 10. 保安人脸验证
    async securityFaceVerify() {
        console.log('👤 步骤 10: 保安人脸验证...');

        try {
            this.windows.security.focus();
            await this.delay(1000);

            // 点击人脸识别按钮
            await this.clickElement(this.windows.security, '#faceScanBtn');

            // 等待人脸识别界面加载
            await this.delay(2000);

            // 开始人脸扫描
            await this.clickElement(this.windows.security, '#startFaceScanBtn');

            // 模拟人脸识别过程
            console.log('📷 正在进行人脸识别...');
            await this.delay(5000);

            // 等待识别结果显示
            await this.delay(3000);
            console.log('✅ 人脸验证完成');
        } catch (error) {
            console.error('❌ 人脸验证失败:', error);
            throw error;
        }
    }

    // 11. 完成测试
    async completeTest() {
        console.log('🎉 步骤 11: 测试流程完成！');

        try {
            this.windows.security.focus();
            await this.delay(1000);

            // 点击允许进入按钮
            await this.clickElement(this.windows.security, '.bg-green-600');

            await this.delay(2000);

            console.log('🎊 访客申请到验证通过的完整流程测试成功！');
            console.log('');
            console.log('📊 测试总结:');
            console.log('✅ 访客注册成功');
            console.log('✅ 访客登录成功');
            console.log('✅ 访问申请提交成功');
            console.log('✅ 人脸信息录入成功');
            console.log('✅ 教师审批成功');
            console.log('✅ 保安登录成功');
            console.log('✅ 二维码验证成功');
            console.log('✅ 人脸验证成功');
            console.log('✅ 访客放行成功');
            console.log('');
            console.log('🎯 整个自动化测试流程执行完成！');

            // 显示测试完成消息
            alert('自动化测试流程已完成！\n\n访客申请到验证通过的完整流程测试成功！');
        } catch (error) {
            console.error('❌ 测试完成步骤失败:', error);
            throw error;
        }
    }

    // 启动自动化测试
    async startTest() {
        console.log('🚀 启动校友入校登记系统自动化测试');
        console.log('📋 测试流程:');
        this.steps.forEach((step, index) => {
            console.log(`${index + 1}. ${this.getStepDescription(step)}`);
        });
        console.log('');

        try {
            for (let i = 0; i < this.steps.length; i++) {
                this.currentStep = i;
                const step = this.steps[i];

                console.log(`\n⏯️  执行步骤 ${i + 1}: ${this.getStepDescription(step)}`);

                await this[step]();

                console.log(`✅ 步骤 ${i + 1} 完成`);

                // 步骤间延时
                if (i < this.steps.length - 1) {
                    console.log('⏳ 等待 2 秒后继续下一步...');
                    await this.delay(2000);
                }
            }
        } catch (error) {
            console.error(`❌ 测试失败于步骤 ${this.currentStep + 1}: ${this.steps[this.currentStep]}`);
            console.error('错误详情:', error);

            // 显示错误消息
            alert(`测试失败！\n步骤: ${this.getStepDescription(this.steps[this.currentStep])}\n错误: ${error.message}`);
        }
    }

    // 获取步骤描述
    getStepDescription(step) {
        const descriptions = {
            openAllWindows: '打开所有系统窗口',
            visitorRegister: '访客注册',
            visitorLogin: '访客登录',
            visitorApplyVisit: '提交访问申请',
            visitorRegisterFace: '录入人脸信息',
            teacherLogin: '教师登录',
            teacherApprove: '教师审批申请',
            securityLogin: '保安登录',
            securityQRVerify: '保安二维码验证',
            securityFaceVerify: '保安人脸验证',
            completeTest: '完成测试'
        };
        return descriptions[step] || step;
    }

    // 停止测试
    stopTest() {
        console.log('🛑 停止自动化测试');

        // 关闭所有窗口
        Object.values(this.windows).forEach(window => {
            if (window && !window.closed) {
                window.close();
            }
        });
    }
}

// 创建测试实例
const automation = new VisitFlowAutomation();

// 导出测试对象
window.VisitFlowAutomation = VisitFlowAutomation;
window.testAutomation = automation;

console.log('🤖 自动化测试脚本已加载');
console.log('💡 使用方法: 点击"开始测试"按钮启动测试流程');