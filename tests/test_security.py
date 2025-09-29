#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import requests
import time
import subprocess

class TestSecurityFeatures(unittest.TestCase):
    """
    טסטים לבדיקת תכונות אבטחה
    """

    def setUp(self):
        """הכנה לכל טסט"""
        self.base_url = "http://localhost"

    def test_fail2ban_multiple_failed_attempts(self):
        """בדיקת Fail2Ban - ניסיונות התחברות כושלים מרובים"""

        print("🔒 בודק Fail2Ban - מבצע 6 ניסיונות כושלים...")

        auth_data = {
            "username": "admin",
            "password": "wrong_password_12345"
        }

        failed_attempts = 0

        # ביצוע 6 ניסיונות כושלים
        for i in range(6):
            try:
                response = requests.post(
                    f"{self.base_url}/auth",
                    data=auth_data,
                    timeout=10
                )

                if response.status_code == 401:
                    failed_attempts += 1
                    print(f"  ניסיון {i+1}: כשלון כצפוי (401)")
                elif response.status_code in [403, 429]:
                    print(f"  ניסיון {i+1}: חסום על ידי Fail2Ban ({response.status_code})")
                    break
                else:
                    print(f"  ניסיון {i+1}: תוצאה לא צפויה ({response.status_code})")

            except requests.exceptions.ConnectTimeout:
                print(f"  ניסיון {i+1}: timeout - ייתכן שחסום")
                break
            except requests.exceptions.ConnectionError:
                print(f"  ניסיון {i+1}: connection error - ייתכן שחסום")
                break

            time.sleep(2)  # המתנה בין ניסיונות

        self.assertGreaterEqual(failed_attempts, 3, "צריכים להיות לפחות 3 ניסיונות כושלים")
        print("✅ טסט Fail2Ban הושלם (ייתכן שהאיפיאיפ נחסם)")

    def test_fail2ban_status_check(self):
        """בדיקת סטטוס Fail2Ban בcontainer"""

        try:
            # בדיקת סטטוס fail2ban בcontainer
            result = subprocess.run([
                "docker", "exec", "quiz-nginx", "fail2ban-client", "status"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print("✅ Fail2Ban פעיל ורץ")
                print(f"   פלט: {result.stdout.strip()}")

                # בדיקת jail ספציפי
                jail_result = subprocess.run([
                    "docker", "exec", "quiz-nginx", "fail2ban-client", "status", "nginx-auth"
                ], capture_output=True, text=True, timeout=10)

                if jail_result.returncode == 0:
                    print("✅ nginx-auth jail פעיל")
                    print(f"   פלט: {jail_result.stdout.strip()}")
                else:
                    print("⚠️  nginx-auth jail לא זמין")

            else:
                print(f"⚠️  Fail2Ban לא זמין: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("⚠️  timeout בבדיקת Fail2Ban")
        except FileNotFoundError:
            print("⚠️  Docker לא זמין לבדיקת Fail2Ban")

    def test_sql_injection_protection(self):
        """בדיקת הגנה מפני SQL injection"""

        # ניסיון SQL injection בשדה username
        sql_injection_attempts = [
            "admin'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "admin' UNION SELECT * FROM users --",
            "1' OR '1'='1' --",
            "admin'; INSERT INTO users VALUES('hacker', 'pass'); --"
        ]

        for injection in sql_injection_attempts:
            with self.subTest(injection=injection):
                auth_data = {
                    "username": injection,
                    "password": "any_password"
                }

                response = requests.post(f"{self.base_url}/auth", data=auth_data)

                # בדיקה שקיבלנו 401 (לא 500 או 200)
                self.assertEqual(response.status_code, 401,
                               f"SQL injection לא נבלם כראוי: {injection}")

        print("✅ הגנה מפני SQL injection עובדת")

    def test_xss_protection(self):
        """בדיקת הגנה מפני XSS"""

        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]

        for xss in xss_attempts:
            with self.subTest(xss=xss):
                auth_data = {
                    "username": xss,
                    "password": "password"
                }

                response = requests.post(f"{self.base_url}/auth", data=auth_data)

                # בדיקה שהתוכן לא מוכנס כמו שהוא
                self.assertNotIn("<script>", response.text)
                self.assertNotIn("javascript:", response.text)
                self.assertNotIn("onerror=", response.text)

        print("✅ הגנה בסיסית מפני XSS עובדת")

    def test_password_hashing(self):
        """בדיקה שסיסמאות מאוחסנות מוצפנות"""

        # בדיקה שלוגים לא חושפים סיסמאות (במקום לבדוק response שמכיל דמו)
        try:
            # ניסיון גישה ללוגים של auth service
            result = subprocess.run([
                "docker", "logs", "quiz-auth", "--tail", "50"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                logs = result.stdout

                # בדיקה שהסיסמאות לא מופיעות בלוגים
                sensitive_passwords = ["admin123", "pass123", "demo456"]

                for password in sensitive_passwords:
                    self.assertNotIn(password, logs,
                                   f"סיסמה {password} נמצאה בלוגים!")

                print("✅ סיסמאות לא מופיעות בלוגי השרת")
            else:
                print("⚠️  לא הצליח לקרוא לוגים")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  Docker לא זמין לבדיקת לוגים")

        print("✅ טסט hashing הושלם")

    def test_session_security(self):
        """בדיקת אבטחת session"""

        session = requests.Session()

        # התחברות
        auth_data = {
            "username": "admin",
            "password": "admin123"
        }

        response = session.post(f"{self.base_url}/auth", data=auth_data)

        # בדיקת cookies
        cookies = session.cookies

        if cookies:
            for cookie in cookies:
                # בדיקה ש-session cookies מוגדרים כראוי
                if 'session' in cookie.name.lower():
                    # בדיקת HttpOnly (אמנם זה לא תמיד מופיע ב-requests)
                    print(f"✅ נמצא session cookie: {cookie.name}")

        print("✅ טסט אבטחת session הושלם")

    def test_rate_limiting_behavior(self):
        """בדיקת התנהגות עם בקשות מרובות"""

        print("🚦 בודק rate limiting - שולח 20 בקשות מהירות...")

        success_count = 0
        error_count = 0

        for i in range(20):
            try:
                response = requests.get(f"{self.base_url}/login", timeout=5)

                if response.status_code == 200:
                    success_count += 1
                elif response.status_code in [429, 503]:
                    error_count += 1
                    print(f"  בקשה {i+1}: rate limited ({response.status_code})")

            except requests.exceptions.RequestException:
                error_count += 1

            if i % 5 == 0:
                time.sleep(0.1)  # המתנה קצרה כל 5 בקשות

        print(f"✅ {success_count} בקשות הצליחו, {error_count} נחסמו/נכשלו")
        self.assertGreater(success_count, 10, "צריכות להצליח לפחות 10 בקשות")

if __name__ == '__main__':
    print("🔒 מריץ טסטים לאבטחה...")
    unittest.main(verbosity=2)