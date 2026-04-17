#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查门卫验证问题
"""

import sys
sys.path.insert(0, 'D:\\Project\\校友入校登记\\backend')

from app import create_app, db
from app.models.user import User
from app.models.visit_application import VisitApplication
from datetime import date, datetime

def check_verification_status():
    """检查验证状态"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Gate Verification Diagnostic")
        print("=" * 60)
        print()

        # 1. Check today's approved records
        today = date.today()
        print(f"[DATE] Today: {today}")
        print()

        print("[1] Check today's approved records (visit_date == today, application_status == 'approved')")
        approved_today = VisitApplication.query.filter(
            VisitApplication.visit_date == today,
            VisitApplication.application_status == 'approved'
        ).all()

        print(f"   Count: {len(approved_today)}")
        if approved_today:
            for app_record in approved_today:
                applicant = User.query.get(app_record.applicant_id)
                print(f"   - ID: {app_record.id}, Applicant: {applicant.real_name if applicant else 'N/A'}, "
                      f"Type: {applicant.user_type if applicant else 'N/A'}, "
                      f"Visit Date: {app_record.visit_date}, "
                      f"Approval Time: {app_record.approval_time}, "
                      f"Access Code: {app_record.access_code}")
        else:
            print("   [X] No approved records for today!")
        print()

        # 2. Check all approved records (any date)
        print("[2] Check all approved records (any date)")
        all_approved = VisitApplication.query.filter(
            VisitApplication.application_status == 'approved'
        ).order_by(VisitApplication.visit_date.desc()).limit(10).all()

        print(f"   Count: {len(all_approved)}")
        if all_approved:
            for app_record in all_approved:
                applicant = User.query.get(app_record.applicant_id)
                date_status = "[OK] Today" if app_record.visit_date == today else f"[--] {app_record.visit_date}"
                print(f"   - ID: {app_record.id}, Applicant: {applicant.real_name if applicant else 'N/A'}, "
                      f"Visit Date: {date_status}, "
                      f"Approval Time: {app_record.approval_time}, "
                      f"Access Code: {app_record.access_code}")
        print()

        # 3. Check recent records
        print("[3] Check recent 10 records")
        recent_apps = VisitApplication.query.order_by(
            VisitApplication.created_at.desc()
        ).limit(10).all()

        for app_record in recent_apps:
            applicant = User.query.get(app_record.applicant_id)
            date_status = "[OK] Today" if app_record.visit_date == today else f"[--] {app_record.visit_date}"
            print(f"   - ID: {app_record.id}, Applicant: {applicant.real_name if applicant else 'N/A'}, "
                  f"Status: {app_record.application_status}, "
                  f"Visit Date: {date_status}, "
                  f"Access Code: {app_record.access_code}")
        print()

        # 4. Test HMAC generation and verification
        print("[4] Test HMAC Generation")
        from app.utils.hmac_utils import generate_hmac_code, verify_hmac_code

        # Use first approved record for testing
        if approved_today:
            test_app = approved_today[0]
            applicant = User.query.get(test_app.applicant_id)

            print(f"   Test User: {applicant.real_name} ({applicant.user_type})")
            print(f"   Phone: {applicant.phone}")

            # Generate approval code (3-minute window)
            test_code = generate_hmac_code(applicant.phone, applicant.wechat_password, minutes=3)
            print(f"   Generated Code: {test_code}")

            # Verify approval code
            verification = verify_hmac_code(test_code, applicant.phone, applicant.wechat_password, 3)
            print(f"   Verification Result: {'[PASS]' if verification['valid'] else '[FAIL]'}")
            if not verification['valid']:
                print(f"   Error Message: {verification['message']}")

            # Test student leave code
            if applicant.user_type == 'parent' and test_app.access_code:
                print(f"   Student Exit Code: {test_app.access_code}")
        print()

        # 5. Diagnostic recommendations
        print("=" * 60)
        print("[DIAGNOSTIC RECOMMENDATIONS]")
        print("=" * 60)

        if not approved_today:
            print("[X] Issue: No approved records for today!")
            print()
            print("Possible reasons:")
            print("1. Teacher approval set visit_date to a different day")
            print("2. application_status is not 'approved'")
            print("3. No approval records in database for today")
            print()
            print("Recommendations:")
            print("- Check teacher approval code, ensure visit_date is set to today")
            print("- Verify application_status is correctly set to 'approved'")
            print("- Check all approval records in admin panel")
        else:
            print("[OK] Today's approval records are normal")
            print()
            print("If verification still fails, possible reasons:")
            print("1. HMAC code mismatch (time window issue)")
            print("2. Incorrect code input at frontend")
            print("3. Backend verification logic bug")

        print()

if __name__ == '__main__':
    check_verification_status()
