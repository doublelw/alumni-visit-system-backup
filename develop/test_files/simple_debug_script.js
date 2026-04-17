// 简单的调试脚本 - 直接在管理界面Console中运行

console.log('=== 开始调试用户创建问题 ===');

// 1. 检查认证状态
console.log('1. 认证状态检查:');
console.log('   AdminState.token存在:', !!AdminState.token);
console.log('   AdminState.isAuthenticated:', AdminState.isAuthenticated);
console.log('   localStorage token存在:', !!localStorage.getItem('admin_token'));

// 2. 检查关键函数
console.log('2. 函数检查:');
console.log('   UsersPage存在:', typeof UsersPage !== 'undefined');
console.log('   UsersPage.addUser存在:', typeof UsersPage?.addUser === 'function');
console.log('   AdminUtils.request存在:', typeof AdminUtils?.request === 'function');

// 3. 测试API连接
console.log('3. 测试API连接...');
async function testApi() {
    try {
        const response = await AdminUtils.request('/admin/users');
        console.log('   ✅ API连接成功');
        console.log('   用户数量:', response.users?.length || 0);
    } catch (error) {
        console.log('   ❌ API连接失败:', error.message);
    }
}
testApi();

// 4. 设置调试监听器
console.log('4. 设置调试监听器...');
const originalAddUser = UsersPage?.addUser;
if (originalAddUser) {
    UsersPage.addUser = async function() {
        console.log('=== 用户创建开始 ===');
        try {
            console.log('   表单数据收集...');
            const formData = {
                username: document.getElementById('addUsername')?.value?.trim(),
                password: document.getElementById('addPassword')?.value,
                real_name: document.getElementById('addRealName')?.value?.trim(),
                email: document.getElementById('addEmail')?.value?.trim(),
                phone: document.getElementById('addPhone')?.value?.trim(),
                user_type: document.getElementById('addUserType')?.value
            };
            console.log('   表单数据:', formData);

            console.log('   调用原始addUser方法...');
            const result = await originalAddUser.call(this);
            console.log('   ✅ 用户创建成功');
            return result;
        } catch (error) {
            console.error('   ❌ 用户创建失败:', error.message);
            console.error('   错误详情:', error);
            throw error;
        }
    };
    console.log('   ✅ 调试监听器已设置');
} else {
    console.log('   ❌ UsersPage.addUser方法不存在');
}

console.log('=== 调试脚本加载完成 ===');
console.log('现在请打开添加用户模态框，填写信息并点击创建按钮');