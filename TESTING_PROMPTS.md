# 校友入校登记系统 - 专属测试 Prompt 套装

**项目技术栈**: Python Flask + HTML/CSS/JS + MySQL/SQLite  
**创建日期**: 2026-04-17  
**版本**: v1.0

---

# 🚀 快速开始 - 一键安装测试技能

```bash
# 安装核心测试技能
npx skills add \
anthropics/skills@webapp-testing \
anthropics/claude-plugins-official@code-review \
anthropics/claude-plugins-official@skill-creator \
supercent-io/skills-template@testing-strategies \
-g -y
```

---

# 📋 项目专属测试 Prompt 套装

## 1. 后端API测试（Flask路由）

### 1.1 用户认证API测试
```python
为Flask后端的用户认证模块生成完整API测试：

技术栈：Flask + pytest + SQLAlchemy
文件路径：backend/app/routes/auth.py
测试覆盖：
- ✅ POST /api/auth/register - 用户注册（正常、重复用户、无效数据）
- ✅ POST /api/auth/login - 用户登录（正确密码、错误密码、不存在用户）
- ✅ GET /api/auth/profile - 获取用户信息（已登录、未登录、Token过期）
- ✅ POST /api/auth/change-password - 修改密码（正常、旧密码错误、未登录）
- ✅ JWT Token生成和验证
- ✅ 权限验证（普通用户、管理员、教师）

要求：
- 使用pytest fixtures管理测试数据库
- Mock外部依赖（如邮件服务）
- 测试数据库事务回滚
- 覆盖所有HTTP状态码（200, 201, 400, 401, 403, 404, 500）
- 生成完整可运行的测试代码
```

### 1.2 校友管理API测试
```python
为校友管理模块生成完整的API测试套件：

技术栈：Flask + pytest + Factory Boy
文件路径：backend/app/routes/admin.py
核心功能：
- 校友列表查询（分页、搜索、过滤）
- 校友详情获取
- 校友档案审核（通过/拒绝）
- 批量操作（批量审核、批量导出）

测试场景：
- ✅ 权限验证（管理员、非管理员）
- ✅ 数据分页和排序
- ✅ 搜索功能（姓名、毕业年份、院系）
- ✅ 批量操作的数据一致性
- ✅ 并发操作的数据锁
- ✅ 导出功能的数据完整性

生成完整的测试代码和测试数据工厂。
```

### 1.3 访问申请API测试
```python
为访问申请管理模块生成API测试：

文件路径：backend/app/routes/（相关文件）
核心流程：
- 访问申请创建
- 申请审批流程（教师 → 管理员）
- 申请状态变更
- 访问记录生成

测试重点：
- ✅ 状态机转换验证
- ✅ 审批权限控制
- ✅ 通知机制触发
- ✅ 数据关联完整性
- ✅ 时间逻辑（有效期、过期处理）
- ✅ 并发申请处理
```

## 2. 前端测试（JavaScript E2E）

### 2.1 管理后台登录页面测试
```javascript
使用Playwright为管理后台登录页面编写E2E测试：

页面：frontend/templates/admin-login.html
测试流程：
1. 页面加载和元素渲染
2. 表单验证（空值、格式错误）
3. 正常登录流程
4. 错误处理（错误密码、验证码错误）
5. 密码显示/隐藏功能
6. 验证码刷新功能
7. 记住我功能
8. 登录后跳转

测试代码要求：
- 使用Playwright的最佳实践
- 等待策略（网络、动画、元素）
- 移动端和桌面端适配
- 网络慢速模拟
- 可访问性检查
- 生成完整可运行的测试套件
```

### 2.2 用户管理页面测试
```javascript
为用户管理页面编写完整的E2E测试：

页面：用户管理界面（/alumni-management-2025）
核心功能：
- 用户列表展示和分页
- 搜索和过滤
- 用户详情查看
- 用户状态变更（激活/禁用）
- 批量操作

测试场景：
- ✅ 列表加载和渲染性能
- ✅ 分页和排序功能
- ✅ 搜索的实时性和准确性
- ✅ 模态框交互
- ✅ 表单提交和验证
- ✅ 错误提示和加载状态
- ✅ 权限控制（不同角色看到的选项）
- ✅ 响应式布局（不同屏幕尺寸）
```

### 2.3 密码输入框交互测试
```javascript
专门测试密码输入框的交互体验（基于刚修复的UI问题）：

组件：密码输入框 + 显示/隐藏按钮
测试重点：
- ✅ 按钮可点击区域（24px x 24px）
- ✅ 输入框可点击区域不受影响
- ✅ 按钮点击响应（图标切换、密码类型切换）
- ✅ 键盘导航（Tab键、Enter键）
- ✅ 触摸设备上的响应
- ✅ 视觉反馈（hover、active状态）
- ✅ 边界情况（快速点击、长按）

使用Playwright的click()和boundingBox()验证元素尺寸。
```

## 3. 数据库测试

### 3.1 数据模型测试
```python
为SQLAlchemy模型生成完整的单元测试：

文件路径：backend/app/models/
核心模型：
- User（用户）
- AlumniProfile（校友档案）
- VisitApplication（访问申请）
- VisitRecord（访问记录）

测试内容：
- ✅ 模型字段验证（类型、长度、约束）
- ✅ 关联关系（一对多、多对多）
- ✅ 级联删除和更新
- ✅ 索引有效性
- ✅ 软删除机制
- ✅ 查询方法和性能
- ✅ 数据验证规则（手机号、身份证格式）

使用pytest + SQLAlchemy的测试数据库。
```

### 3.2 数据库迁移测试
```python
测试Flask-Migrate迁移脚本：

测试内容：
- ✅ 迁移脚本向上和向下执行
- ✅ 数据完整性保证
- ✅ 性能影响评估
- ✅ 回滚机制
- ✅ 生产数据迁移模拟

创建测试数据库，执行完整迁移流程。
```

## 4. 集成测试

### 4.1 完整用户流程测试
```python
编写端到端的集成测试，覆盖完整业务流程：

场景1：校友注册和访问申请
1. 用户注册 → 邮箱验证
2. 填写校友档案 → 提交审核
3. 管理员审核 → 通过
4. 创建访问申请 → 支付费用
5. 生成访问码 → 门卫验证
6. 访问记录生成

场景2：访客登记流程
1. 教师添加访客信息
2. 生成访客码和访问密码
3. 访客自助验证
4. 门卫验证访客码
5. 访问记录生成

每个步骤都要验证：
- 数据状态正确性
- 权限控制
- 通知触发
- 异常处理
```

### 4.2 支付集成测试
```python
测试支付功能的集成：

场景：
- ✅ 微信支付回调处理
- ✅ 支付状态同步
- ✅ 支付失败重试
- ✅ 订单状态管理
- ✅ 退款处理

Mock支付接口，测试各种支付状态。
```

## 5. 性能测试

### 5.1 API性能测试
```python
使用Locust生成API性能测试：

测试场景：
- ✅ 并发用户登录（100用户）
- ✅ 校友列表查询（含分页、搜索）
- ✅ 批量操作（1000条数据）
- ✅ 数据导出（大数据量）
- ✅ 文件上传（图片、文档）

性能指标：
- 响应时间 < 2s (95th percentile)
- 吞吐量 > 100 req/s
- 错误率 < 1%
- 数据库连接池使用率

生成Locust测试脚本和性能报告。
```

### 5.2 数据库性能测试
```python
测试数据库查询性能：

关键查询：
- ✅ 用户搜索（模糊匹配）
- ✅ 访问记录统计（聚合查询）
- ✅ 报表生成（复杂JOIN）
- ✅ 历史数据查询

优化验证：
- ✅ 索引使用情况
- ✅ 查询执行计划
- ✅ N+1查询问题
- ✅ 缓存命中率
```

## 6. 安全测试

### 6.1 认证安全测试
```python
测试用户认证的安全性：

攻击场景：
- ✅ SQL注入尝试
- ✅ 暴力破解防护（验证码、限流）
- ✅ 会话劫持防护
- ✅ Token伪造和重放
- ✅ 权限提升攻击
- ✅ 密码强度验证

使用OWASP ZAP或手工测试。
```

### 6.2 输入验证测试
```python
测试输入验证的完整性：

攻击向量：
- ✅ XSS跨站脚本（所有输入字段）
- ✅ CSRF跨站请求伪造
- ✅ 文件上传漏洞（类型、大小、内容）
- ✅ 路径遍历攻击
- ✅ 命令注入
- ✅ LDAP注入（如果使用）

每个输入字段都要测试边界值和特殊字符。
```

## 7. 兼容性测试

### 7.1 浏览器兼容性
```javascript
使用Playwright测试多浏览器兼容性：

浏览器矩阵：
- ✅ Chrome (最新版)
- ✅ Edge (最新版)
- ✅ Firefox (最新版)
- ✅ Safari (如果可用)
- ✅ 移动浏览器 (iOS Safari, Android Chrome)

测试页面：
- 登录页面
- 用户管理页面
- 表单页面
- 数据展示页面

重点测试：
- CSS渲染一致性
- JavaScript功能
- 文件上传
- 移动端适配
```

### 7.2 设备兼容性
```javascript
测试不同设备的响应式设计：

设备尺寸：
- ✅ 桌面端 (1920x1080)
- ✅ 平板 (768x1024)
- ✅ 手机 (375x667)
- ✅ 大屏手机 (414x896)

测试交互：
- 触摸操作
- 横竖屏切换
- 软键盘弹出
- 手势操作
```

## 8. 自动化测试修复

### 8.1 测试失败自动修复
```python
运行测试套件并自动修复失败：

执行步骤：
1. 运行完整测试套件
2. 分析失败原因
3. 区分产品代码bug vs 测试代码问题
4. 自动修复（更新选择器、修正等待时间、修复断言）
5. 重新运行直到全部通过
6. 生成修复报告

命令：pytest --auto-fix
```

### 8.2 选择器更新
```javascript
自动更新过时的CSS选择器：

场景：
- UI重构后元素定位失败
- 动态生成的内容
- React/Vue组件更新

工具：
- Playwright的codegen生成新选择器
- AI辅助选择器优化
- 稳定性优先（使用data-testid）
```

## 9. 代码质量检查

### 9.1 测试代码审查
```python
对以下测试代码进行专业审查：

{粘贴测试代码}

审查要点：
- 是否有假测试（总是通过的测试）
- 测试独立性（无依赖关系）
- 断言合理性和完整性
- 边界条件覆盖
- 异常场景处理
- 测试数据管理
- 可读性和可维护性
- 性能影响

输出优化后的测试代码版本。
```

### 9.2 覆盖率分析
```python
分析测试覆盖率并生成改进建议：

执行：
1. 运行pytest --cov=backend
2. 分析覆盖率报告
3. 识别未覆盖的代码路径
4. 生成补充测试用例
5. 优先级排序（风险导向）

目标：
- 单元测试覆盖率 ≥ 80%
- 关键业务逻辑覆盖率 = 100%
```

## 10. 持续集成配置

### 10.1 CI/CD测试配置
```yaml
为GitHub Actions创建CI测试配置：

触发条件：
- Pull Request创建
- 代码推送到main/master分支
- 定时执行（每日凌晨）

测试流程：
1. 环境设置（Python、Node.js）
2. 依赖安装
3. 代码风格检查（Black, Flake8）
4. 安全扫描（Bandit）
5. 单元测试（pytest）
6. 集成测试
7. E2E测试（Playwright）
8. 覆盖率报告
9. 性能基准测试
10. 构建和部署

生成完整的.github/workflows/test.yml文件。
```

---

# 🎯 快速使用指南

## 按功能模块选择Prompt

| 功能模块 | 推荐Prompt | 预计时间 |
|---------|-----------|----------|
| 用户认证 | 1.1 + 6.1 | 30分钟 |
| 校友管理 | 1.2 + 2.2 + 9.1 | 45分钟 |
| 访问申请 | 1.3 + 4.1 | 40分钟 |
| 支付功能 | 4.2 + 5.1 | 35分钟 |
| UI优化 | 2.3 + 7.1 | 25分钟 |
| 性能优化 | 5.1 + 5.2 | 50分钟 |
| 安全加固 | 6.1 + 6.2 | 40分钟 |

## 按测试类型选择

| 测试类型 | 推荐Prompt | 覆盖范围 |
|---------|-----------|----------|
| 单元测试 | 1.x + 3.1 | 代码级别 |
| 集成测试 | 4.x + 10.1 | 模块间交互 |
| E2E测试 | 2.x + 4.1 | 完整流程 |
| 性能测试 | 5.x | 系统性能 |
| 安全测试 | 6.x | 安全漏洞 |

---

# 📝 自定义Prompt模板

## 创建新功能测试
```python
实现{功能描述}，并同步生成：
1. 产品代码（Python Flask）
2. 单元测试（pytest）
3. API测试（Supertest）
4. E2E测试（Playwright）
5. 测试数据脚本
6. 性能基准测试

要求：
- 遵循项目现有代码风格
- 完整的错误处理
- 详细的注释文档
- 测试覆盖率 ≥ 80%
```

## 修复Bug并测试
```python
修复以下Bug并生成回归测试：

Bug描述：{具体描述}
相关文件：{文件路径}
错误信息：{报错内容}

要求：
1. 分析根本原因
2. 修复产品代码
3. 编写防止回归的测试
4. 验证修复效果
5. 检查是否有类似问题
```

---

# 🚀 部署和使用

## 本地测试环境搭建
```bash
# 1. 克隆项目
git clone https://github.com/doublelw/alumni-visit-system-backup

# 2. 安装测试依赖
pip install pytest pytest-cov pytest-flask
npm install -D @playwright/test

# 3. 初始化测试数据库
python -m backend.init_test_data

# 4. 运行测试
pytest                          # 单元测试
pytest --cov=backend            # 带覆盖率
npx playwright test             # E2E测试

# 5. 生成测试报告
pytest --html=report.html --cov=backend --cov-report=html
```

## CI/CD集成
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest --cov=backend --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

# 📊 测试成熟度评估

## 当前水平：Level 3 (定义级)

### 已实现 ✅
- [x] 基础单元测试框架
- [x] 部分API测试
- [x] 手工测试流程
- [x] GitHub备份建立

### 待实现 🔄
- [ ] 完整的自动化测试套件
- [ ] CI/CD集成
- [ ] 性能监控
- [ ] E2E测试自动化

### 目标：Level 4 (量化管理级)
- [ ] 测试覆盖率 ≥ 80%
- [ ] 自动化测试比例 ≥ 70%
- [ ] 性能基准建立
- [ ] 质量门禁

---

# 💡 最佳实践建议

## 测试命名规范
```python
# 好的测试命名
def test_admin_can_approve_alumni_application():
    def test_login_with_invalid_password_returns_401():
    def test_search_alumni_by_graduation_year():

# 避免的命名
def test_feature1():
def test_admin():
def test_login():
```

## 测试数据管理
```python
# 使用Factory Boy创建测试数据
class AlumniFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = AlumniProfile
        sqlalchemy_session = session

    name = factory.Sequence(lambda n: f"校友{n}")
    graduation_year = 2020
    major = "计算机科学"
```

## Mock最佳实践
```python
# Mock外部服务
@patch('backend.app.routes.auth.send_email')
def test_register_sends_email(self, mock_email):
    # 测试代码
    mock_email.assert_called_once()
```

---

**文档维护**: 持续更新  
**版本**: v1.0  
**最后更新**: 2026-04-17  
**项目**: 校友入校登记系统