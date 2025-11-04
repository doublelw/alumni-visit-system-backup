// 专门监控logout调用的调试脚本

console.log('=== 设置Logout监控 ===');

// 重写AdminAuth.logout方法
const originalLogout = AdminAuth.logout;
AdminAuth.logout = function() {
    console.log('🚨🚨🚨 AdminAuth.logout被调用了！');
    console.log('调用堆栈:', new Error().stack);

    // 检查当前状态
    console.log('当前AdminState:', {
        token: AdminState.token ? AdminState.token.substring(0, 50) + '...' : 'null',
        isAuthenticated: AdminState.isAuthenticated,
        user: AdminState.user
    });

    console.log('localStorage状态:', {
        token: localStorage.getItem('admin_token') ? 'exists' : 'null',
        user: localStorage.getItem('admin_user') ? 'exists' : 'null'
    });

    return originalLogout.call(this);
};

// 重写所有可能导致跳转的方法
const originalRedirect = window.location.href;
console.log('监控页面跳转...');

// 监控页面跳转事件
window.addEventListener('beforeunload', function(event) {
    console.log('🔄 页面即将卸载/跳转');
    console.log('当前URL:', window.location.href);
});

// 监控window.location.assign
const originalAssign = window.location.assign;
window.location.assign = function(url) {
    console.log('🔄 window.location.assign被调用:', url);
    console.log('调用堆栈:', new Error().stack);
    return originalAssign.call(this, url);
};

// 监控window.location.replace
const originalReplace = window.location.replace;
window.location.replace = function(url) {
    console.log('🔄 window.location.replace被调用:', url);
    console.log('调用堆栈:', new Error().stack);
    return originalReplace.call(this, url);
};

console.log('✅ Logout监控已设置');
console.log('现在请尝试创建用户，观察是否有logout被调用');