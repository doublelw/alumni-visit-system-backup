// 返校日活动报名页面脚本

// 菜品列表
const dishList = [
    // 红烧肉类
    '红烧肉', '糖醋里脊', '红烧排骨', '红烧鸡翅', '红烧猪蹄',
    '红烧带鱼', '红烧茄子', '红烧豆腐',

    // 川菜类
    '水煮肉片', '毛血旺', '水煮鱼', '酸菜鱼',
    '川香肉丝', '鱼香肉丝', '京酱肉丝', '宫保鸡丁',
    '回锅肉', '麻婆豆腐', '蚂蚁上树',

    // 炒菜类
    '干煸四季豆', '干煸豆角', '干煸土豆丝', '干煸牛肉丝',
    '辣子鸡丁', '宫爆鸡丁', '青椒肉丝', '芹菜肉丝',
    '蒜苔肉丝', '洋葱肉丝', '韭菜肉丝',

    // 特色菜类
    '鱼香茄子', '地三鲜', '麻婆豆腐',
    '家常豆腐', '肉末茄子', '肉末豆腐',

    // 汤羹类
    '酸菜粉丝汤', '紫菜蛋花汤', '西红柿鸡蛋汤',
    '冬瓜排骨汤', '玉米排骨汤', '萝卜排骨汤',
    '海带豆腐汤',

    // 小炒类
    '青椒土豆丝', '酸辣土豆丝', '蒜蓉菠菜', '清炒时蔬',
    '蚝油生菜', '炒合菜', '炒豆芽',

    // 鸡蛋类
    '西红柿炒鸡蛋', '韭菜炒鸡蛋', '黄瓜炒鸡蛋',
    '苦瓜炒鸡蛋', '青椒炒鸡蛋',

    // 主食类
    '蛋炒饭', '扬州炒饭', '酱油炒饭',
    '盖浇饭', '咖喱炒饭', '海鲜炒饭'
];

// 选中的菜品
let selectedDishes = [];

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    loadUserInfo();
    setupEventListeners();
});

// 初始化表单
function initializeForm() {
    // 生成菜品选择网格
    generateDishGrid();

    // 设置默认菜品提示
    setDefaultDishPlaceholders();
}

// 加载用户信息
function loadUserInfo() {
    // 从localStorage获取注册信息
    const savedData = localStorage.getItem('registerFormData');
    if (savedData) {
        try {
            const formData = JSON.parse(savedData);
            if (formData.username) {
                document.getElementById('username').value = formData.username;
            }
            if (formData.phone) {
                document.getElementById('contactPhone').value = formData.phone;
            }
        } catch (e) {
            console.error('加载用户信息失败:', e);
        }
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 就餐选择变化
    document.getElementById('willDine').addEventListener('change', function(e) {
        const dishSelection = document.getElementById('dishSelection');
        const diningCompanionsSelection = document.getElementById('diningCompanionsSelection');
        if (e.target.checked) {
            dishSelection.style.display = 'block';
            diningCompanionsSelection.style.display = 'block';
        } else {
            dishSelection.style.display = 'none';
            diningCompanionsSelection.style.display = 'none';
            // 清空菜品选择
            clearDishSelection();
        }
    });

    // 表单提交
    document.getElementById('eventRegistrationForm').addEventListener('submit', function(e) {
        e.preventDefault();
        submitRegistration();
    });
}

// 设置默认菜品提示
function setDefaultDishPlaceholders() {
    const placeholders = ['溜肉段', '锅包肉', '菠萝古老肉', '大盘鸡'];
    placeholders.forEach((dish, index) => {
        const input = document.getElementById(`dish${index + 1}`);
        if (input && !input.value) {
            input.placeholder = `菜品${index + 1}（如：${dish}）`;
        }
    });
}

// 生成菜品选择网格
function generateDishGrid() {
    const dishGrid = document.getElementById('dishGrid');
    dishGrid.innerHTML = '';

    dishList.forEach(dish => {
        const dishItem = document.createElement('div');
        dishItem.className = 'dish-item';
        dishItem.innerHTML = `
            <input type="checkbox" id="dish-${dish}" value="${dish}">
            <label for="dish-${dish}">${dish}</label>
        `;

        // 添加点击事件
        dishItem.addEventListener('click', function(e) {
            if (e.target.type !== 'checkbox') {
                const checkbox = dishItem.querySelector('input[type="checkbox"]');
                checkbox.checked = !checkbox.checked;
            }
            updateSelection();
        });

        dishGrid.appendChild(dishItem);
    });
}

// 显示菜谱弹窗
function showMenuModal() {
    document.getElementById('menuModal').classList.add('active');
    document.body.style.overflow = 'hidden';

    // 恢复之前的选择状态
    restoreDishSelection();
    updateSelection();
}

// 关闭菜谱弹窗
function closeMenuModal() {
    document.getElementById('menuModal').classList.remove('active');
    document.body.style.overflow = '';
}

// 更新选择状态
function updateSelection() {
    const checkboxes = document.querySelectorAll('#dishGrid input[type="checkbox"]:checked');
    selectedDishes = Array.from(checkboxes).map(cb => cb.value);

    // 更新选择数量显示
    document.getElementById('selectedCount').textContent = selectedDishes.length;

    // 更新选择信息
    const selectionInfo = document.getElementById('selectionInfo');
    if (selectedDishes.length === 0) {
        selectionInfo.textContent = '请选择4个您最想吃的菜品';
        selectionInfo.style.background = '#fff3cd';
        selectionInfo.style.color = '#856404';
    } else if (selectedDishes.length < 4) {
        selectionInfo.textContent = `已选择${selectedDishes.length}个菜品，请再选择${4 - selectedDishes.length}个`;
        selectionInfo.style.background = '#fff3cd';
        selectionInfo.style.color = '#856404';
    } else if (selectedDishes.length === 4) {
        selectionInfo.textContent = '已完成选择！';
        selectionInfo.style.background = '#d4edda';
        selectionInfo.style.color = '#155724';
    } else {
        selectionInfo.textContent = `已选择${selectedDishes.length}个菜品，请取消选择${selectedDishes.length - 4}个`;
        selectionInfo.style.background = '#f8d7da';
        selectionInfo.style.color = '#721c24';
    }

    // 更新确认按钮状态
    const confirmBtn = document.getElementById('confirmSelectionBtn');
    confirmBtn.disabled = selectedDishes.length !== 4;

    // 更新菜品项样式
    document.querySelectorAll('.dish-item').forEach(item => {
        const checkbox = item.querySelector('input[type="checkbox"]');
        if (checkbox.checked) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

// 恢复菜品选择状态
function restoreDishSelection() {
    // 清空当前选择
    document.querySelectorAll('#dishGrid input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });

    // 从表单中获取已选择的菜品
    const dishInputs = [
        document.getElementById('dish1').value,
        document.getElementById('dish2').value,
        document.getElementById('dish3').value,
        document.getElementById('dish4').value
    ].filter(dish => dish.trim());

    // 选中对应的菜品
    dishInputs.forEach(dish => {
        const checkbox = document.getElementById(`dish-${dish}`);
        if (checkbox) {
            checkbox.checked = true;
        }
    });
}

// 确认菜品选择
function confirmSelection() {
    if (selectedDishes.length !== 4) {
        showToast('请选择恰好4个菜品', 'error');
        return;
    }

    // 填充到表单中
    selectedDishes.forEach((dish, index) => {
        const input = document.getElementById(`dish${index + 1}`);
        if (input) {
            input.value = dish;
        }
    });

    closeMenuModal();
    showToast('菜品选择成功！', 'success');
}

// 绑定确认按钮事件
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('confirmSelectionBtn').addEventListener('click', confirmSelection);
});

// 清空菜品选择
function clearDishSelection() {
    for (let i = 1; i <= 4; i++) {
        const input = document.getElementById(`dish${i}`);
        if (input) {
            input.value = '';
        }
    }
    selectedDishes = [];
}

// 验证表单
function validateForm() {
    const username = document.getElementById('username').value.trim();
    const willDine = document.getElementById('willDine').checked;
    const contactPhone = document.getElementById('contactPhone').value.trim();

    if (!username) {
        showToast('用户名不能为空', 'error');
        return false;
    }

    if (!contactPhone) {
        showToast('联系电话不能为空', 'error');
        return false;
    }

    // 验证手机号格式
    if (!/^1[3-9]\d{9}$/.test(contactPhone)) {
        showToast('请输入有效的手机号码', 'error');
        return false;
    }

    // 如果选择就餐，验证就餐人数和菜品选择
    if (willDine) {
        // 验证就餐人数
        const diningCompanions = document.getElementById('diningCompanions').value;
        if (!diningCompanions) {
            showToast('请选择就餐人数', 'error');
            return false;
        }

        // 验证菜品选择
        const dishInputs = [
            document.getElementById('dish1').value.trim(),
            document.getElementById('dish2').value.trim(),
            document.getElementById('dish3').value.trim(),
            document.getElementById('dish4').value.trim()
        ];

        const validDishes = dishInputs.filter(dish => dish);
        if (validDishes.length !== 4) {
            showToast('请选择4个菜品', 'error');
            return false;
        }

        // 检查是否有重复
        const uniqueDishes = [...new Set(validDishes)];
        if (uniqueDishes.length !== 4) {
            showToast('不能选择重复的菜品', 'error');
            return false;
        }
    }

    return true;
}

// 提交报名
async function submitRegistration() {
    if (!validateForm()) {
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="ri-loader-4-line animate-spin"></i> 提交中...';

    try {
        const formData = {
            username: document.getElementById('username').value.trim(),
            willDine: document.getElementById('willDine').checked,
            contactPhone: document.getElementById('contactPhone').value.trim(),
            notes: document.getElementById('notes').value.trim()
        };

        // 如果选择就餐，添加菜品信息和就餐人数
        if (formData.willDine) {
            const dishes = [
                document.getElementById('dish1').value.trim(),
                document.getElementById('dish2').value.trim(),
                document.getElementById('dish3').value.trim(),
                document.getElementById('dish4').value.trim()
            ];
            formData.favoriteDishes = JSON.stringify(dishes);

            // 添加就餐人数
            const diningCompanions = document.getElementById('diningCompanions').value;
            if (diningCompanions) {
                formData.diningCompanions = parseInt(diningCompanions);
            }
        }

        const response = await fetch('/api/event/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            showToast(result.message || '报名成功！', 'success');

            // 如果API返回了redirect_url，则跳转到验证码页面
            if (result.redirect_url) {
                setTimeout(() => {
                    window.location.href = result.redirect_url;
                }, 2000);
            } else {
                // 如果没有redirect_url，默认跳转到registerOnce页面
                setTimeout(() => {
                    window.location.href = '/registerOnce';
                }, 2000);
            }
        } else {
            showToast(result.message || '报名失败，请重试', 'error');
        }
    } catch (error) {
        console.error('报名错误:', error);
        showToast('网络错误，请检查网络连接后重试', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="ri-check-line"></i> 确认报名';
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

// 键盘导航支持
document.addEventListener('keydown', function(event) {
    // ESC 关闭弹窗
    if (event.key === 'Escape') {
        closeMenuModal();
    }
});

// 页面加载动画
window.addEventListener('load', function() {
    document.body.style.opacity = '1';
});