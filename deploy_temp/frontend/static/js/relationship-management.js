/**
 * 用户关系管理功能
 */

// 用户关系管理页面
const UserRelationshipPage = {
    currentUserId: null,
    currentUserData: null,

    // 打开用户关系管理模态框
    async openModal(userId) {
        try {
            this.currentUserId = userId;

            // 获取用户信息和关系数据
            const data = await AdminUtils.request(`/api/admin/users/${userId}/relationships`);
            if (data.success) {
                this.currentUserData = data.user;
                this.renderUserInfo(data.user);
                this.renderRelationshipOptions(data.potential_relationships);
                this.showModal();
            }
        } catch (error) {
            console.error('Failed to load user relationships:', error);
            AdminUtils.showToast('加载用户关系失败: ' + error.message, 'error');
        }
    },

    // 渲染用户基本信息
    renderUserInfo(user) {
        const userInfoDiv = document.getElementById('userInfo');
        userInfoDiv.innerHTML = `
            <div><strong>用户名:</strong> ${user.username}</div>
            <div><strong>真实姓名:</strong> ${user.real_name}</div>
            <div><strong>用户类型:</strong> ${this.getUserTypeLabel(user.user_type)}</div>
            <div><strong>邮箱:</strong> ${user.email}</div>
            <div><strong>手机号:</strong> ${user.phone}</div>
            <div><strong>状态:</strong> ${this.getStatusLabel(user.status)}</div>
        `;
    },

    // 渲染关系选项
    renderRelationshipOptions(relationships) {
        const parentStudentSection = document.getElementById('parentStudentRelationships');
        const availableUsersList = document.getElementById('availableUsersList');
        const relationshipTargetType = document.getElementById('relationshipTargetType');

        // 如果是家长或学生，显示家长-学生关系配置
        if (this.currentUserData.user_type === 'parent' || this.currentUserData.user_type === 'student') {
            parentStudentSection.style.display = 'block';

            const targetUsers = this.currentUserData.user_type === 'parent' ? relationships.students : relationships.parents;
            const targetTypeLabel = this.currentUserData.user_type === 'parent' ? '学生' : '家长';

            relationshipTargetType.textContent = targetTypeLabel;

            availableUsersList.innerHTML = targetUsers.map(user => `
                <div class="checkbox-item" style="margin-bottom: 8px;">
                    <input type="checkbox"
                           id="user_${user.id}"
                           value="${user.id}"
                           ${user.is_related ? 'checked' : ''}
                           onchange="UserRelationshipPage.updateSelectedCount()">
                    <label for="user_${user.id}" style="cursor: pointer; margin-left: 8px;">
                        ${user.name} ${user.student_id ? '(' + user.student_id + ')' : ''} ${user.phone ? '(' + user.phone + ')' : ''}
                    </label>
                </div>
            `).join('');
        } else {
            parentStudentSection.style.display = 'none';
        }

        // 加载组织选项
        this.loadOrganizationOptions();
    },

    // 加载组织选项
    async loadOrganizationOptions() {
        try {
            const data = await AdminUtils.request('/api/admin/organizations/tree');
            if (data.success) {
                const select = document.getElementById('userOrganizationId');
                this.renderOrganizationTree(select, data.tree, 0);

                // 设置当前选中的组织
                if (this.currentUserData.organization_id) {
                    select.value = this.currentUserData.organization_id;
                }
            }
        } catch (error) {
            console.error('Failed to load organizations:', error);
        }
    },

    // 渲染组织树
    renderOrganizationTree(select, tree, level) {
        tree.forEach(org => {
            const option = document.createElement('option');
            option.value = org.id;
            option.textContent = '  '.repeat(level) + org.name;
            select.appendChild(option);

            if (org.children && org.children.length > 0) {
                this.renderOrganizationTree(select, org.children, level + 1);
            }
        });
    },

    // 更新选中数量
    updateSelectedCount() {
        const checkboxes = document.querySelectorAll('#availableUsersList input[type="checkbox"]:checked');
        // 可以在这里显示选中数量的提示
    },

    // 显示模态框
    showModal() {
        document.getElementById('userRelationshipModal').classList.add('show');
    },

    // 关闭模态框
    closeModal() {
        document.getElementById('userRelationshipModal').classList.remove('show');
        this.currentUserId = null;
        this.currentUserData = null;
    },

    // 保存关系
    async saveRelationships() {
        try {
            const relationshipData = {};

            // 如果是家长，收集选中的学生
            if (this.currentUserData.user_type === 'parent') {
                const selectedStudents = Array.from(document.querySelectorAll('#availableUsersList input[type="checkbox"]:checked'))
                    .map(checkbox => parseInt(checkbox.value));
                relationshipData.student_ids = selectedStudents;
            }

            // 如果是学生，收集选中的家长
            else if (this.currentUserData.user_type === 'student') {
                const selectedParents = Array.from(document.querySelectorAll('#availableUsersList input[type="checkbox"]:checked'))
                    .map(checkbox => parseInt(checkbox.value));
                relationshipData.parent_ids = selectedParents;
            }

            // 组织关系
            const organizationId = document.getElementById('userOrganizationId').value;
            if (organizationId) {
                relationshipData.organization_id = parseInt(organizationId);
            }

            const data = await AdminUtils.request(`/api/admin/users/${this.currentUserId}/relationships`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(relationshipData)
            });

            if (data.success) {
                AdminUtils.showToast('用户关系更新成功', 'success');
                this.closeModal();
                // 刷新用户列表
                if (typeof UsersPage !== 'undefined') {
                    UsersPage.loadUsers();
                }
            }
        } catch (error) {
            console.error('Failed to save user relationships:', error);
            AdminUtils.showToast('保存用户关系失败: ' + error.message, 'error');
        }
    },

    // 获取用户类型标签
    getUserTypeLabel(userType) {
        const labels = {
            'admin': '管理员',
            'teacher': '教师',
            'student': '学生',
            'parent': '家长',
            'security': '保安',
            'alumni': '校友'
        };
        return labels[userType] || userType;
    },

    // 获取状态标签
    getStatusLabel(status) {
        const labels = {
            'active': '启用',
            'inactive': '禁用',
            'pending': '待审核'
        };
        return labels[status] || status;
    }
};

// 扩展OrganizationPage以支持新功能
if (typeof OrganizationPage !== 'undefined') {
    // 添加组织表单类型变化处理
    OrganizationPage.initOrgTypeChangeHandler = function() {
        const orgTypeSelect = document.getElementById('orgType');
        if (orgTypeSelect) {
            orgTypeSelect.addEventListener('change', function() {
                    const orgType = this.value;
                    const classFields = document.getElementById('classFields');
                    const clubFields = document.getElementById('clubFields');

                    // 隐藏所有特殊字段
                    classFields.style.display = 'none';
                    clubFields.style.display = 'none';

                    // 根据组织类型显示相应字段
                    if (orgType === 'class') {
                        classFields.style.display = 'block';
                    } else if (orgType === 'club') {
                        clubFields.style.style.display = 'block';
                    }
                });
        }
    };

    // 添加教师选择功能
    OrganizationPage.openTeacherSelectionModal = function(targetFieldId) {
        this.currentTeacherField = targetFieldId;
        document.getElementById('teacherSelectionModal').classList.add('show');
        this.loadAvailableTeachers();
    };

    OrganizationPage.closeTeacherSelectionModal = function() {
        document.getElementById('teacherSelectionModal').classList.remove('show');
        this.currentTeacherField = null;
    };

    OrganizationPage.loadAvailableTeachers = async function() {
        try {
            const data = await AdminUtils.request('/api/admin/users?user_type=teacher&status=active&per_page=1000');
            if (data.success) {
                this.renderTeacherList(data.users);
            }
        } catch (error) {
            console.error('Failed to load teachers:', error);
            AdminUtils.showToast('加载教师列表失败: ' + error.message, 'error');
        }
    };

    OrganizationPage.renderTeacherList = function(teachers) {
        const teacherList = document.getElementById('teacherList');
        teacherList.innerHTML = teachers.map(teacher => `
            <div class="teacher-item" style="padding: 10px; border-bottom: 1px solid var(--border-color); cursor: pointer;"
                 onclick="OrganizationPage.selectTeacherValue(${teacher.id}, '${teacher.real_name}')">
                <div style="font-weight: 500;">${teacher.real_name}</div>
                <div style="font-size: 12px; color: var(--text-secondary);">
                    ${teacher.email || ''} ${teacher.phone ? '|' + teacher.phone : ''}
                </div>
            </div>
        `).join('');
    };

    OrganizationPage.selectTeacherValue = function(teacherId, teacherName) {
        const selectField = document.getElementById(this.currentTeacherField);
        if (selectField) {
            // 清空现有选项并添加新选项
            selectField.innerHTML = `<option value="${teacherId}">${teacherName}</option>`;
        }
        this.closeTeacherSelectionModal();
    };

    OrganizationPage.filterTeachers = function() {
        const searchInput = document.getElementById('teacherSearchInput');
        const searchValue = searchInput.value.toLowerCase();
        const teacherItems = document.querySelectorAll('#teacherList .teacher-item');

        teacherItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchValue) ? 'block' : 'none';
        });
    };

    OrganizationPage.selectTeacher = function() {
        // 这个方法可以用于其他选择逻辑
        this.closeTeacherSelectionModal();
    };

    // 重写保存组织方法以支持新字段
    const originalSaveOrg = OrganizationPage.saveOrg;
    OrganizationPage.saveOrg = async function() {
        // 获取基本表单数据
        const formData = {
            name: document.getElementById('orgName').value,
            code: document.getElementById('orgCode').value,
            org_type: document.getElementById('orgType').value,
            parent_id: document.getElementById('orgParentId').value || null,
            description: document.getElementById('orgDescription').value,
            status: document.getElementById('orgStatus').value,
            sort_order: parseInt(document.getElementById('orgSortOrder').value) || 0,
            contact_person: document.getElementById('orgContactPerson').value,
            contact_phone: document.getElementById('orgContactPhone').value,
            contact_email: document.getElementById('orgContactEmail').value,
            address: document.getElementById('orgAddress').value
        };

        // 添加特殊字段
        const orgType = document.getElementById('orgType').value;
        if (orgType === 'class') {
            formData.class_teacher_id = document.getElementById('classTeacherId').value || null;
            formData.head_teacher_id = document.getElementById('headTeacherId').value || null;
        } else if (orgType === 'club') {
            formData.leader_id = document.getElementById('leaderId').value || null;
        }

        try {
            const url = this.editingOrgId ?
                `/api/admin/organizations/${this.editingOrgId}` :
                '/api/admin/organizations';

            const method = this.editingOrgId ? 'PUT' : 'POST';

            const data = await AdminUtils.request(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (data.success) {
                AdminUtils.showToast(`组织${this.editingOrgId ? '更新' : '创建'}成功`, 'success');
                this.closeOrgModal();
                await this.loadOrganizations(this.currentPage);
            }
        } catch (error) {
            console.error('Failed to save organization:', error);
            AdminUtils.showToast(`保存组织失败: ${error.message}`, 'error');
        }
    };

    // 重写编辑组织方法以加载特殊字段
    const originalEditOrg = OrganizationPage.editOrg;
    OrganizationPage.editOrg = async function(orgId) {
        this.editingOrgId = orgId;

        try {
            const data = await AdminUtils.request(`/api/admin/organizations/${orgId}`);
            if (data.success) {
                const org = data.organization;

                // 填充基本字段
                document.getElementById('orgModalTitle').textContent = '编辑组织';
                document.getElementById('orgName').value = org.name || '';
                document.getElementById('orgCode').value = org.code || '';
                document.getElementById('orgType').value = org.org_type || '';
                document.getElementById('orgParentId').value = org.parent_id || '';
                document.getElementById('orgDescription').value = org.description || '';
                document.getElementById('orgStatus').value = org.status || 'active';
                document.getElementById('orgSortOrder').value = org.sort_order || 0;
                document.getElementById('orgContactPerson').value = org.contact_person || '';
                document.getElementById('orgContactPhone').value = org.contact_phone || '';
                document.getElementById('orgContactEmail').value = org.contact_email || '';
                document.getElementById('orgAddress').value = org.address || '';

                // 填充特殊字段
                if (org.org_type === 'class') {
                    document.getElementById('classTeacherId').value = org.class_teacher_id || '';
                    document.getElementById('headTeacherId').value = org.head_teacher_id || '';
                } else if (org.org_type === 'club') {
                    document.getElementById('leaderId').value = org.leader_id || '';
                }

                // 触发类型变化事件以显示正确字段
                const orgTypeSelect = document.getElementById('orgType');
                orgTypeSelect.dispatchEvent(new Event('change'));

                // 加载教师选项
                await this.loadTeacherOptions(orgId);

                // 显示模态框
                document.getElementById('orgModal').classList.add('show');
            }
        } catch (error) {
            console.error('Failed to load organization:', error);
            AdminUtils.showToast('加载组织信息失败: ' + error.message, 'error');
        }
    };

    // 加载教师选项
    OrganizationPage.loadTeacherOptions = async function(orgId) {
        try {
            const data = await AdminUtils.request(`/api/admin/organizations/${orgId}/available-teachers`);
            if (data.success) {
                const teachers = data.teachers;

                // 更新班主任选项
                const classTeacherSelect = document.getElementById('classTeacherId');
                if (classTeacherSelect) {
                    classTeacherSelect.innerHTML = '<option value="">请选择班主任</option>' +
                        teachers.map(teacher => `
                            <option value="${teacher.id}" ${teacher.is_selected.class_teacher ? 'selected' : ''}>
                                ${teacher.real_name} (${teacher.email})
                            </option>
                        `).join('');
                }

                // 更新年级组长选项
                const headTeacherSelect = document.getElementById('headTeacherId');
                if (headTeacherSelect) {
                    headTeacherSelect.innerHTML = '<option value="">请选择年级组长</option>' +
                        teachers.map(teacher => `
                            <option value="${teacher.id}" ${teacher.is_selected.head_teacher ? 'selected' : ''}>
                                ${teacher.real_name} (${teacher.email})
                            </option>
                        `).join('');
                }

                // 更新社团负责人选项
                const leaderSelect = document.getElementById('leaderId');
                if (leaderSelect) {
                    leaderSelect.innerHTML = '<option value="">请选择社团负责人</option>' +
                        teachers.map(teacher => `
                            <option value="${teacher.id}" ${teacher.is_selected.leader ? 'selected' : ''}>
                                ${teacher.real_name} (${teacher.email})
                            </option>
                        `).join('');
                }
            }
        } catch (error) {
            console.error('Failed to load teacher options:', error);
        }
    };
}

// 扩展UsersPage以支持关系管理按钮
if (typeof UsersPage !== 'undefined') {
    // 重写渲染用户行方法以添加关系管理按钮
    const originalRenderUserRow = UsersPage.renderUserRow;
    UsersPage.renderUserRow = function(user, index) {
        const userTypes = Array.isArray(user.user_type) ? user.user_type : [user.user_type];
        const userTypesHtml = userTypes.map(type =>
            `<span class="user-type-badge ${type}">${this.getUserTypeLabel(type)}</span>`
        ).join(' ');

        return `
            <tr>
                <td><input type="checkbox" class="user-checkbox" data-user-id="${user.id}"></td>
                <td>${index + 1}</td>
                <td>${user.username}</td>
                <td>${user.real_name}</td>
                <td>${userTypesHtml}</td>
                <td>${user.email}</td>
                <td>${user.phone}</td>
                <td>
                    <span class="status-badge ${user.status}">${this.getStatusLabel(user.status)}</span>
                </td>
                <td>
                    <span class="visitable-badge ${user.is_visitable ? 'yes' : 'no'}">
                        ${user.is_visitable ? '可拜访' : '不可拜访'}
                    </span>
                </td>
                <td>${this.formatDate(user.created_at)}</td>
                <td>
                    <div class="action-buttons">
                        ${user.user_type === 'parent' || user.user_type === 'student' || user.user_type === 'teacher' ?
                            `<button class="btn btn-sm btn-outline" onclick="UserRelationshipPage.openModal(${user.id})" title="关系管理">
                                <i class="ri-group-line"></i>
                            </button>` : ''
                        }
                        <button class="btn btn-sm btn-outline" onclick="UsersPage.editUser(${user.id})" title="编辑">
                            <i class="ri-edit-line"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="UsersPage.toggleUserStatus(${user.id})" title="切换状态">
                            <i class="ri-toggle-line"></i>
                        </button>
                        <button class="btn btn-sm btn-outline btn-danger" onclick="UsersPage.deleteUser(${user.id})" title="删除">
                            <i class="ri-delete-bin-line"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    };
}

// 确保AdminUtils存在
if (typeof AdminUtils === 'undefined') {
    const AdminUtils = {
        async request(url, options = {}) {
            const token = localStorage.getItem('admin_token');
            const defaultOptions = {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                ...options
            };

            const response = await fetch(url, defaultOptions);
            const data = await response.json();
            return data;
        },

        showToast(message, type = 'info') {
            // 创建toast提示的实现
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    };
}