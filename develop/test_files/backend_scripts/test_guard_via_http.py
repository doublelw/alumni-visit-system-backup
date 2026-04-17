"""
通过HTTP接口测试门卫验证（避免模块导入问题）
"""
import sys
import os
import time
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code
from app.models.user import User
from app.models.visit_application import VisitApplication
from datetime import datetime, date, time as dt_time


def test_via_http():
    """通过HTTP接口测试"""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("通过HTTP接口测试优化后的门卫验证")
        print("=" * 70)

        # 查找校友用户
        user = User.query.filter_by(user_type='alumni', status='active').first()
        if not user:
            user = User.query.filter_by(user_type='parent', status='active').first()

        if not user:
            print("[X] 未找到测试用户")
            return False

        print(f"\n[用户] {user.real_name} ({user.user_type})")
        print(f"      手机: {user.phone}")

        # 创建审批记录
        print(f"\n[创建] 审批记录...")
        from app import db

        application = VisitApplication(
            applicant_id=user.id,
            visit_date=date.today(),
            visit_time_start=dt_time(8, 0),
            visit_time_end=dt_time(20, 0),
            visit_purpose=f'{user.real_name}进校',
            target_person=user.real_name,
            qr_code='dummy_code_a',
            application_status='approved',
            approved_by=1,
            approval_time=datetime.utcnow(),
            approval_note=f"审批日期: {date.today()}"
        )

        db.session.add(application)
        db.session.commit()

        print(f"[OK] 审批记录ID: {application.id}")

        # 生成码B
        print(f"\n[生成] 码B...")
        time.sleep(1)
        code_b = generate_hmac_code(user.phone, user.wechat_password, int(time.time()))
        print(f"[OK] 码B: {code_b}")

        # 通过HTTP请求测试门卫验证
        print(f"\n[HTTP] POST /api/guard/verify")

        # 注意：这需要Flask服务器正在运行
        try:
            # 测试服务器是否运行
            response = requests.post('http://127.0.0.1:5000/api/guard/verify',
                                    json={'code': code_b, 'guard_name': 'test'},
                                    timeout=5)

            print(f"[状态码] {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('data', {})
                    if result.get('valid'):
                        print(f"\n[SUCCESS] 验证成功！")
                        print(f"     码类型: {result.get('code_type')}")
                        user_info = result.get('user_info', {})
                        print(f"     姓名: {user_info.get('name')}")
                        print(f"     类型: {user_info.get('type')}")
                        print(f"     手机: {user_info.get('phone')}")

                        # 清理
                        db.session.delete(application)
                        db.session.commit()
                        return True
                    else:
                        print(f"\n[X] 验证失败: {result.get('message')}")
                else:
                    print(f"\n[X] 请求失败: {data}")
            else:
                print(f"\n[X] HTTP错误: {response.status_code}")
                print(f"     响应: {response.text}")

        except requests.exceptions.ConnectionError:
            print(f"\n[!] 无法连接到服务器")
            print(f"     请确保Flask服务器正在运行: python run.py")
            print(f"\n[提示] 您可以手动测试:")
            print(f"     1. 启动服务器: python run.py")
            print(f"     2. 在浏览器或Postman中测试:")
            print(f"        POST http://127.0.0.1:5000/api/guard/verify")
            print(f"        Content-Type: application/json")
            print(f'        {{"code": "{code_b}", "guard_name": "test"}}')

        except Exception as e:
            print(f"\n[!] 测试失败: {str(e)}")

        # 清理
        db.session.delete(application)
        db.session.commit()

        return False


if __name__ == '__main__':
    print("\n注意：此测试需要Flask服务器正在运行")
    print("启动服务器：cd backend && python run.py\n")

    success = test_via_http()
    sys.exit(0 if success else 1)
