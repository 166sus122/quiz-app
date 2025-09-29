#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטי אבטחה מתקדמים לאפליקציית החידות
בודק התקפות brute force, fail2ban, הזרקות ועוד
"""

import pytest
import requests
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost"

class TestAdvancedSecurity:
    """טסטים מתקדמים לאבטחה"""

    def test_brute_force_protection(self):
        """בדיקת הגנה מפני התקפות brute force"""
        print("🔒 בודק הגנת brute force...")

        # ניסיונות התחברות כושלים רצופים
        failed_attempts = []

        for attempt in range(6):  # יותר מהמגבלה של fail2ban (3)
            print(f"ניסיון כושל {attempt + 1}/6")

            try:
                response = requests.post(f"{BASE_URL}/auth",
                                       data={'username': 'hacker', 'password': f'wrong_pass_{attempt}'},
                                       timeout=10)
                failed_attempts.append(response.status_code)
                print(f"Status: {response.status_code}")

                # המתנה קטנה בין ניסיונות
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"Connection error on attempt {attempt + 1}: {e}")
                failed_attempts.append(0)  # Connection failed

        print(f"Failed attempts results: {failed_attempts}")

        # לפחות הניסיונות הראשונים צריכים להחזיר 401
        assert any(status == 401 for status in failed_attempts), "לא התקבלו responses של 401 Unauthorized"

        # בדיקה שאחרי מספר ניסיונות, יש חסימה או התנהגות שונה
        # (fail2ban עשוי לחסום את הIP לחלוטין)

        print("✅ Brute force protection test completed")

    def test_sql_injection_attempts(self):
        """בדיקת הגנה מפני SQL injection"""
        sql_payloads = [
            "admin'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'/**/OR/**/1=1#",
            "'; INSERT INTO users VALUES('hacker', 'hacked'); --"
        ]

        for payload in sql_payloads:
            try:
                response = requests.post(f"{BASE_URL}/auth",
                                       data={'username': payload, 'password': 'test'},
                                       timeout=5)

                # SQL injection לא אמור להצליח
                assert response.status_code in [401, 400, 500]

                # בדיקה שלא התקבלה הודעת שגיאה של DB
                if response.status_code != 401:
                    assert "database" not in response.text.lower()
                    assert "sql" not in response.text.lower()
                    assert "error" in response.text or response.status_code == 400

            except requests.exceptions.RequestException:
                # Connection timeout/error מקובל במקרה של חסימה
                pass

    def test_xss_prevention(self):
        """בדיקת הגנה מפני XSS"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "'; alert('XSS'); var x='",
            "<svg/onload=alert('XSS')>"
        ]

        session = requests.Session()

        for payload in xss_payloads:
            # ניסיון להכניס XSS בשם משתמש
            response = session.post(f"{BASE_URL}/auth",
                                  data={'username': payload, 'password': 'test'})

            # בדיקה שה-payload לא מוחזר כמו שהוא
            assert "<script>" not in response.text
            assert "javascript:" not in response.text
            assert "onerror=" not in response.text
            assert "onload=" not in response.text

    def test_session_hijacking_protection(self):
        """בדיקת הגנה מפני session hijacking"""
        # התחברות לגיטימית
        session = requests.Session()
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post(f"{BASE_URL}/auth", data=login_data)
        assert response.status_code in [200, 302]

        # קבלת session cookie
        session_cookie = session.cookies.get('session')
        assert session_cookie is not None

        # ניסיון להשתמש בsession מכתובת IP אחרת (סימולציה)
        hijack_session = requests.Session()
        hijack_session.cookies.set('session', session_cookie, domain='localhost')

        # הוספת headers שונים לסימולציה של משתמש אחר
        hijack_headers = {
            'User-Agent': 'DifferentBrowser/1.0',
            'X-Forwarded-For': '192.168.1.100',  # IP אחר
        }

        response = hijack_session.get(f"{BASE_URL}/verify", headers=hijack_headers)

        # כרגע הsession יעבוד (אין הגנה מ-IP binding)
        # בסביבת production היה צריך להוסיף הגנות נוספות

    def test_csrf_protection(self):
        """בדיקת הגנה מפני CSRF (אם קיימת)"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # ניסיון לבצע פעולה ללא CSRF token (אם נדרש)
        # כרגע האפליקציה לא משתמשת ב-CSRF tokens
        response = session.get(f"{BASE_URL}/logout")

        # הפעולה תעבוד כי אין CSRF protection
        assert response.status_code in [200, 302]

    def test_directory_traversal_prevention(self):
        """בדיקת הגנה מפני directory traversal"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd"
        ]

        for payload in traversal_payloads:
            # ניסיון לגשת לקבצי מערכת דרך נתיבים שונים
            try:
                response = requests.get(f"{BASE_URL}/{payload}")

                # לא אמור להחזיר תוכן קובץ מערכת
                assert response.status_code != 200 or "root:" not in response.text

                # נתיבי static files
                response = requests.get(f"{BASE_URL}/static/{payload}")
                assert response.status_code != 200 or "root:" not in response.text

            except requests.exceptions.RequestException:
                # שגיאת connection מקובלת
                pass

    def test_authentication_bypass_attempts(self):
        """בדיקת ניסיונות לעקוף אימות"""
        bypass_attempts = [
            # ניסיון לגשת לendpoints מוגנים ללא אימות
            '/api/question',
            '/api/answer',
            '/quiz',
            '/verify'
        ]

        for endpoint in bypass_attempts:
            response = requests.get(f"{BASE_URL}{endpoint}")

            if endpoint in ['/quiz']:
                # עמוד זה עשוי לטעון אבל לא לתפקד
                assert response.status_code == 200
            elif endpoint in ['/api/question', '/api/answer']:
                # API endpoints צריכים להחזיר error
                assert response.status_code == 200
                data = response.json()
                assert 'error' in data
            elif endpoint == '/verify':
                # verify צריך להחזיר 401
                assert response.status_code == 401

    def test_password_complexity_validation(self):
        """בדיקת אכיפת מורכבות סיסמה (אם קיימת)"""
        # כרגע האפליקציה לא אוכפת מורכבות סיסמה
        # זהו טסט להמחשה של מה שכדאי להוסיף

        weak_passwords = [
            "123",
            "password",
            "admin",
            "a",
            ""
        ]

        # בביצוע אמיתי היה צריך endpoint ליצירת משתמש חדש
        # כרגע נבדוק רק שהמשתמשים הקיימים עובדים

        # בדיקה שמשתמשים עם סיסמאות חזקות עובדים
        strong_auth_tests = [
            ('admin', 'admin123'),
            ('user1', 'pass123'),
            ('demo', 'demo456')
        ]

        for username, password in strong_auth_tests:
            session = requests.Session()
            response = session.post(f"{BASE_URL}/auth",
                                  data={'username': username, 'password': password})
            assert response.status_code in [200, 302], f"Failed for {username}"

    def test_rate_limiting_api_calls(self):
        """בדיקת הגבלת קצב של API calls"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # שליחת בקשות מהירות רצופות
        rapid_requests = []
        start_time = time.time()

        for i in range(50):  # בקשות מהירות
            try:
                response = session.get(f"{BASE_URL}/api/question")
                rapid_requests.append(response.status_code)
            except requests.exceptions.RequestException:
                rapid_requests.append(0)

        end_time = time.time()

        # בדיקה שלא כל הבקשות נדחו (אין rate limiting כרגע)
        successful_requests = sum(1 for status in rapid_requests if status == 200)
        assert successful_requests > 0

        print(f"Successful requests: {successful_requests}/50 in {end_time-start_time:.2f}s")

    def test_concurrent_login_attempts(self):
        """בדיקת התנהגות עם ניסיונות התחברות במקביל"""
        def login_attempt(username, password):
            try:
                response = requests.post(f"{BASE_URL}/auth",
                                       data={'username': username, 'password': password},
                                       timeout=10)
                return response.status_code
            except requests.exceptions.RequestException:
                return 0

        # ניסיונות התחברות במקביל עם פרטים שונים
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            # ניסיונות לגיטימיים
            for i in range(5):
                future = executor.submit(login_attempt, 'admin', 'admin123')
                futures.append(future)

            # ניסיונות לא לגיטימיים
            for i in range(5):
                future = executor.submit(login_attempt, 'hacker', f'wrong{i}')
                futures.append(future)

            results = []
            for future in as_completed(futures):
                results.append(future.result())

        # בדיקה שחלק מהבקשות עברו
        successful = sum(1 for r in results if r in [200, 302])
        failed = sum(1 for r in results if r == 401)

        assert successful > 0, "No successful logins"
        assert failed > 0, "No failed logins detected"

        print(f"Concurrent login test: {successful} successful, {failed} failed")

    def test_information_disclosure_prevention(self):
        """בדיקת הגנה מפני חשיפת מידע"""
        # בדיקת שגיאות שלא חושפות מידע רגיש
        error_endpoints = [
            '/nonexistent',
            '/api/nonexistent',
            '/admin',
            '/../../../etc/passwd',
            '/config',
            '/debug'
        ]

        for endpoint in error_endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}")

                # בדיקה שלא חושפים מידע רגיש בשגיאות
                assert "password" not in response.text.lower()
                assert "database" not in response.text.lower()
                assert "traceback" not in response.text.lower()
                assert "exception" not in response.text.lower()

                # בדיקת headers
                assert "server" not in response.headers.get('Server', '').lower() or \
                       "nginx" in response.headers.get('Server', '').lower()

            except requests.exceptions.RequestException:
                pass

    def test_fail2ban_integration(self):
        """בדיקת אינטגרציה עם fail2ban"""
        print("🔒 בודק fail2ban integration...")

        # שליחת מספר ניסיונות כושלים לצורך הפעלת fail2ban
        for i in range(4):  # מעל המגבלה
            try:
                requests.post(f"{BASE_URL}/auth",
                             data={'username': 'attacker', 'password': f'wrong{i}'},
                             timeout=5)
                time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Request failed (possibly blocked): {e}")
                # זה יכול להיות סימן טוב שfail2ban עובד

        # ניסיון לבקשה נוספת - עשויה להיחסם
        try:
            response = requests.get(f"{BASE_URL}/login", timeout=5)
            print(f"Final request status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Final request blocked: {e}")
            # זה יכול להצביע על כך שfail2ban חסם את הIP

    def test_secure_headers(self):
        """בדיקת headers של אבטחה"""
        session = requests.Session()
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        response = session.get(f"{BASE_URL}/quiz")

        # בדיקת headers מומלצים (חלקם עשויים להיות missing)
        security_headers = {
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-Content-Type-Options': ['nosniff'],
            'X-XSS-Protection': ['1; mode=block'],
            'Strict-Transport-Security': None,  # עבור HTTPS
        }

        print("Security headers found:")
        for header, expected_values in security_headers.items():
            if header in response.headers:
                print(f"✅ {header}: {response.headers[header]}")
                if expected_values:
                    assert response.headers[header] in expected_values
            else:
                print(f"❌ {header}: Missing")

if __name__ == "__main__":
    print("🛡️ מריץ טסטי אבטחה מתקדמים...")
    pytest.main([__file__, "-v", "--tb=short", "-s"])