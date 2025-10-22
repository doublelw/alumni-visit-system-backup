"""
组织架构模型
"""

from datetime import datetime
from app import db
from .user import User

class Organization(db.Model):
    """组织架构表"""
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    name = db.Column(db.String(200), nullable=False, comment='组织名称')
    code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='组织代码')
    description = db.Column(db.Text, comment='组织描述')

    # 层级关系
    parent_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True, comment='父级组织ID')
    level = db.Column(db.Integer, default=1, comment='组织层级')
    path = db.Column(db.String(500), comment='组织路径，如/1/2/3')

    # 组织类型
    org_type = db.Column(db.Enum('school', 'campus', 'graduation_year', 'class', 'club_category', 'club', 'office', 'other'),
                         nullable=False, default='class', comment='组织类型')

    # 状态和排序
    status = db.Column(db.Enum('active', 'inactive'), default='active', comment='状态')
    sort_order = db.Column(db.Integer, default=0, comment='排序')

    # 联系信息
    contact_person = db.Column(db.String(100), comment='联系人')
    contact_phone = db.Column(db.String(20), comment='联系电话')
    contact_email = db.Column(db.String(100), comment='联系邮箱')
    address = db.Column(db.String(500), comment='地址')

    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人ID')

    # 关系
    children = db.relationship('Organization', backref='parent', remote_side=[id])
    creator = db.relationship('User', foreign_keys=[created_by])
    # 用户关系由User模型的organization backref定义

    def __repr__(self):
        return f'<Organization {self.name}>'

    def to_dict(self, include_children=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'parent_id': self.parent_id,
            'level': self.level,
            'path': self.path,
            'org_type': self.org_type,
            'status': self.status,
            'sort_order': self.sort_order,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

        if include_children:
            data['children'] = [child.to_dict() for child in self.children if child.status == 'active']

        return data

    def get_full_path(self):
        """获取完整路径名称"""
        if self.path:
            path_ids = self.path.split('/')[1:]  # 去掉空字符串
            orgs = Organization.query.filter(Organization.id.in_(path_ids)).order_by(Organization.level).all()
            return ' / '.join([org.name for org in orgs])
        return self.name

    def update_path(self):
        """更新组织路径"""
        if self.parent_id:
            parent = Organization.query.get(self.parent_id)
            if parent:
                self.path = f"{parent.path}/{self.id}"
                self.level = parent.level + 1
            else:
                self.path = f"/{self.id}"
                self.level = 1
        else:
            self.path = f"/{self.id}"
            self.level = 1

    def before_save(self):
        """保存前更新路径"""
        self.update_path()

    @staticmethod
    def get_root_orgs():
        """获取根级组织"""
        return Organization.query.filter_by(parent_id=None, status='active').order_by(Organization.sort_order, Organization.name).all()

    @staticmethod
    def get_tree():
        """获取组织树结构"""
        root_orgs = Organization.get_root_orgs()
        return [org.to_dict(include_children=True) for org in root_orgs]

class UserRoleAssignment(db.Model):
    """用户角色分配表"""
    __tablename__ = 'user_role_assignments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('user_roles.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True, comment='组织ID，为空表示全局角色')

    # 状态和时间
    status = db.Column(db.Enum('active', 'inactive'), default='active', comment='状态')
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='分配人ID')
    expires_at = db.Column(db.DateTime, nullable=True, comment='过期时间')

    # 关系
    user = db.relationship('User', backref='role_assignments', foreign_keys=[user_id])
    role = db.relationship('UserRole', backref='assignments', foreign_keys=[role_id])
    organization = db.relationship('Organization', backref='role_assignments')
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by])

    def __repr__(self):
        return f'<UserRoleAssignment User:{self.user_id} Role:{self.role_id}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'organization_id': self.organization_id,
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'assigned_by': self.assigned_by,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'user': self.user.to_dict() if self.user else None,
            'role': self.role.to_dict() if self.role else None,
            'organization': self.organization.to_dict() if self.organization else None
        }

class UserRole(db.Model):
    """用户角色表"""
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    name = db.Column(db.String(50), nullable=False, unique=True, comment='角色名称')
    display_name = db.Column(db.String(100), nullable=False, comment='显示名称')
    description = db.Column(db.Text, comment='角色描述')

    # 权限
    permissions = db.Column(db.Text, comment='权限列表，JSON格式')

    # 状态
    status = db.Column(db.Enum('active', 'inactive'), default='active', comment='状态')

    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人ID')

    # 关系
    creator = db.relationship('User', foreign_keys=[created_by])
    # users关系通过User模型的roles backref定义

    def __repr__(self):
        return f'<UserRole {self.name}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'permissions': self.permissions,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

    def has_permission(self, permission):
        """检查是否具有指定权限"""
        if not self.permissions:
            return False
        try:
            permissions = eval(self.permissions)  # 注意：生产环境应使用json.loads
            return permission in permissions
        except:
            return False

    def get_permissions(self):
        """获取权限列表"""
        if not self.permissions:
            return []
        try:
            permissions = eval(self.permissions)  # 注意：生产环境应使用json.loads
            return permissions if isinstance(permissions, list) else []
        except:
            return []

# 组织相关的静态方法
def generate_uuid():
    """生成UUID"""
    import uuid
    return str(uuid.uuid4())