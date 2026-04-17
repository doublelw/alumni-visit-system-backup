#!/usr/bin/env python3
"""
完整关系管理功能测试
测试所有组织管理和用户关系管理的API接口
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def login_admin():
    """登录管理员账户"""
    print("=== 登录管理员账户 ===")
    login_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }

    try:
        response = requests.post(f"{BASE_URL}/admin/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ 管理员登录成功: {data.get('message', '')}")
                return data.get("access_token")
            else:
                print(f"❌ 登录失败: {data.get('message', '未知错误')}")
                return None
        else:
            print(f"❌ 登录请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def get_auth_headers(token):
    """获取认证头"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_organization_apis(headers):
    """测试组织管理API"""
    print("\n=== 测试组织管理API ===")

    # 1. 获取组织列表
    print("1. 获取组织列表...")
    try:
        response = requests.get(f"{BASE_URL}/admin/api/organizations", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                organizations = data.get("organizations", [])
                print(f"✅ 获取组织列表成功，共 {len(organizations)} 个组织")

                # 打印前几个组织信息
                for org in organizations[:3]:
                    print(f"   - {org['name']} ({org['org_type']})")
            else:
                print(f"❌ 获取组织列表失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")

    # 2. 创建测试组织
    print("\n2. 创建测试组织...")
    test_org = {
        "name": "测试班级关系管理",
        "code": "TEST_RELATION_CLASS",
        "org_type": "class",
        "description": "用于测试关系管理功能的班级",
        "class_teacher_id": None,
        "head_teacher_id": None
    }

    try:
        response = requests.post(f"{BASE_URL}/admin/api/organizations",
                               headers=headers, json=test_org)
        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                org_id = data.get("organization", {}).get("id")
                print(f"✅ 创建组织成功: ID={org_id}")
                return org_id
            else:
                print(f"❌ 创建组织失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")

    return None

def test_teacher_selection_api(headers, org_id):
    """测试教师选择API"""
    print(f"\n=== 测试教师选择API (组织ID: {org_id}) ===")

    try:
        response = requests.get(f"{BASE_URL}/admin/api/organizations/{org_id}/available-teachers",
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                teachers = data.get("teachers", [])
                print(f"✅ 获取可用教师列表成功，共 {len(teachers)} 位教师")

                if teachers:
                    # 返回第一个教师ID用于后续测试
                    teacher_id = teachers[0]["id"]
                    print(f"   可选教师: {teachers[0]['real_name']} (ID: {teacher_id})")
                    return teacher_id
                else:
                    print("   没有可用的教师")
            else:
                print(f"❌ 获取教师列表失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")

    return None

def test_organization_update(headers, org_id, teacher_id):
    """测试组织更新（设置教师）"""
    print(f"\n=== 测试组织更新 (组织ID: {org_id}, 教师ID: {teacher_id}) ===")

    update_data = {
        "name": "测试班级关系管理-已更新",
        "code": "TEST_RELATION_CLASS",
        "org_type": "class",
        "description": "用于测试关系管理功能的班级（已设置班主任）",
        "class_teacher_id": teacher_id,
        "head_teacher_id": teacher_id
    }

    try:
        response = requests.put(f"{BASE_URL}/admin/api/organizations/{org_id}",
                              headers=headers, json=update_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ 更新组织成功")
                org_data = data.get("organization", {})
                if org_data.get("class_teacher"):
                    print(f"   班主任: {org_data['class_teacher']['real_name']}")
                if org_data.get("head_teacher"):
                    print(f"   年级组长: {org_data['head_teacher']['real_name']}")
            else:
                print(f"❌ 更新组织失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")

def test_user_apis(headers):
    """测试用户管理API"""
    print("\n=== 测试用户管理API ===")

    # 1. 获取用户列表
    print("1. 获取用户列表...")
    try:
        response = requests.get(f"{BASE_URL}/admin/api/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                users = data.get("users", [])
                print(f"✅ 获取用户列表成功，共 {len(users)} 个用户")

                # 查找学生和家长用户
                student_id = None
                parent_id = None

                for user in users:
                    if user["user_type"] == "student" and not student_id:
                        student_id = user["id"]
                        print(f"   找到学生: {user['real_name']} (ID: {student_id})")
                    elif user["user_type"] == "parent" and not parent_id:
                        parent_id = user["id"]
                        print(f"   找到家长: {user['real_name']} (ID: {parent_id})")

                    if student_id and parent_id:
                        break

                return student_id, parent_id
            else:
                print(f"❌ 获取用户列表失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")

    return None, None

def test_user_relationship_apis(headers, student_id, parent_id):
    """测试用户关系管理API"""
    if not student_id or not parent_id:
        print("\n=== 跳过用户关系测试（缺少学生或家长用户）===")
        return

    print(f"\n=== 测试用户关系管理API (学生ID: {student_id}, 家长ID: {parent_id}) ===")

    # 1. 获取学生当前关系
    print("1. 获取学生当前关系...")
    try:
        response = requests.get(f"{BASE_URL}/admin/api/users/{student_id}/relationships",
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ 获取学生关系成功")
                relationships = data.get("relationships", {})
                print(f"   当前家长数量: {len(relationships.get('parents', []))}")
                print(f"   当前组织: {relationships.get('organization', {}).get('name', '无')}")
            else:
                print(f"❌ 获取学生关系失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")

    # 2. 更新学生关系（设置家长）
    print("\n2. 更新学生关系（设置家长）...")
    relationship_data = {
        "parent_ids": [parent_id],
        "organization_id": None
    }

    try:
        response = requests.put(f"{BASE_URL}/admin/api/users/{student_id}/relationships",
                              headers=headers, json=relationship_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ 更新学生关系成功")
                relationships = data.get("relationships", {})
                parents = relationships.get("parents", [])
                if parents:
                    print(f"   设置家长: {parents[0]['real_name']}")
            else:
                print(f"❌ 更新学生关系失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")

def main():
    """主测试函数"""
    print("开始完整关系管理功能测试...")
    print(f"测试目标: {BASE_URL}")

    # 1. 登录获取token
    token = login_admin()
    if not token:
        print("❌ 无法登录，终止测试")
        return

    headers = get_auth_headers(token)

    # 2. 测试组织管理API
    org_id = test_organization_apis(headers)

    # 3. 如果组织创建成功，继续测试
    if org_id:
        teacher_id = test_teacher_selection_api(headers, org_id)
        if teacher_id:
            test_organization_update(headers, org_id, teacher_id)

    # 4. 测试用户管理API
    student_id, parent_id = test_user_apis(headers)

    # 5. 测试用户关系管理API
    test_user_relationship_apis(headers, student_id, parent_id)

    print("\n=== 测试完成 ===")
    print("所有关系管理功能测试已执行完毕。")

if __name__ == "__main__":
    main()