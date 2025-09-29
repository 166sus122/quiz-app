#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטי אינטגרציה לnginx proxy עם session management
בודק את הזרימה המלאה דרך nginx reverse proxy
"""

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

import requests
import time
import json
import subprocess
import sys
import unittest
from urllib.parse import urljoin

# כתובת בסיס של האפליקציה דרך nginx
BASE_URL = "http://localhost"
TIMEOUT = 10

class TestNginxIntegration(unittest.TestCase):
    """טסטים לאינטגרציה עם nginx proxy"""

    @classmethod
    def setUpClass(cls):
        """הכנה לפני הטסטים"""
        print("מכין טסטי nginx integration...")
        # בדיקה שהשירותים זמינים
        cls.wait_for_services()

    @classmethod
    def wait_for_services(cls):
        """ממתין שהשירותים יהיו זמינים"""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{BASE_URL}/login", timeout=5)
                if response.status_code == 200:
                    print("✓ השירותים זמינים")
                    return
            except requests.exceptions.RequestException:
                pass

            if attempt < max_attempts - 1:
                print(f"ממתין לשירותים... ({attempt + 1}/{max_attempts})")
                time.sleep(2)

        raise Exception("השירותים לא זמינים אחרי 60 שניות")

    def test_nginx_root_redirect(self):
        """בדיקה שroot path מפנה ל-login"""
        response = requests.get(f"{BASE_URL}/", allow_redirects=False)
        assert response.status_code == 301
        assert "/login" in response.headers.get('Location', '')

    def test_login_page_loads(self):
        """בדיקה שדף הlogin נטען דרך nginx"""
        response = requests.get(f"{BASE_URL}/login")
        assert response.status_code == 200
        assert "אפליקציית חידות" in response.text
        assert "שם משתמש" in response.text
        assert "סיסמה" in response.text

    def test_authentication_flow_via_nginx(self):
        """בדיקת זרימת אימות מלאה דרך nginx"""
        session = requests.Session()

        # 1. טעינת דף login
        response = session.get(f"{BASE_URL}/login")
        assert response.status_code == 200

        # 2. שליחת פרטי התחברות
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        response = session.post(f"{BASE_URL}/auth", data=login_data, allow_redirects=False)
        assert response.status_code == 302
        assert "/quiz" in response.headers.get('Location', '')

        # 3. בדיקת session cookies
        assert 'session' in session.cookies

        # 4. אימות session דרך verify endpoint
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 200
        data = response.json()
        assert data['authenticated'] is True
        assert data['username'] == 'admin'

        # 5. גישה לדף החידות
        response = session.get(f"{BASE_URL}/quiz")
        assert response.status_code == 200
        assert "משחק החידות" in response.text

        # 6. גישה ל-API
        response = session.get(f"{BASE_URL}/api/question")
        assert response.status_code == 200
        question_data = response.json()
        assert 'question' in question_data
        assert 'id' in question_data

    def test_failed_authentication_via_nginx(self):
        """בדיקת כישלון אימות דרך nginx"""
        session = requests.Session()

        # שליחת פרטי התחברות שגויים
        login_data = {
            'username': 'wrong_user',
            'password': 'wrong_pass'
        }
        response = session.post(f"{BASE_URL}/auth", data=login_data)
        assert response.status_code == 401
        assert "שם משתמש או סיסמה שגויים" in response.text

        # בדיקה שאין session cookie
        assert 'session' not in session.cookies

        # בדיקה שאין גישה ל-verify
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 401

        # בדיקה שאין גישה ל-API
        response = session.get(f"{BASE_URL}/api/question")
        assert response.status_code == 200  # יחזיר error עם redirect
        data = response.json()
        assert data.get('error') == 'לא מאומת'
        assert data.get('redirect') == '/login'

    def test_session_persistence_across_requests(self):
        """בדיקת התמדת session בין בקשות"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'user1', 'password': 'pass123'}
        response = session.post(f"{BASE_URL}/auth", data=login_data, allow_redirects=False)
        assert response.status_code == 302

        # בקשות מרובות עם אותו session
        for i in range(5):
            response = session.get(f"{BASE_URL}/verify")
            assert response.status_code == 200
            data = response.json()
            assert data['username'] == 'user1'

            # קבלת שאלה
            response = session.get(f"{BASE_URL}/api/question")
            assert response.status_code == 200
            time.sleep(0.5)

    def test_logout_via_nginx(self):
        """בדיקת יציאה דרך nginx"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'demo', 'password': 'demo456'}
        response = session.post(f"{BASE_URL}/auth", data=login_data, allow_redirects=False)
        assert response.status_code == 302

        # אימות שמחובר
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 200
        data = response.json()
        assert data['authenticated'] is True

        # יציאה
        response = session.get(f"{BASE_URL}/logout", allow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get('Location', '')

        # בדיקה שהsession בוטל
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 401

    def test_cookie_domain_and_path(self):
        """בדיקת הגדרות cookies דרך nginx"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post(f"{BASE_URL}/auth", data=login_data)

        # בדיקת cookie properties
        session_cookie = session.cookies.get('session')
        assert session_cookie is not None

        # בדיקה שהcookie עובד בבקשות שונות
        for endpoint in ['/verify', '/quiz', '/api/question']:
            response = session.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 200

    def test_concurrent_sessions(self):
        """בדיקת מספר sessions במקביל"""
        sessions = []
        users = [
            ('admin', 'admin123'),
            ('user1', 'pass123'),
            ('demo', 'demo456')
        ]

        # יצירת sessions במקביל
        for username, password in users:
            session = requests.Session()
            login_data = {'username': username, 'password': password}
            response = session.post(f"{BASE_URL}/auth", data=login_data, allow_redirects=False)
            assert response.status_code == 302
            sessions.append((session, username))

        # בדיקה שכל הsessions עובדים
        for session, expected_username in sessions:
            response = session.get(f"{BASE_URL}/verify")
            assert response.status_code == 200
            data = response.json()
            assert data['username'] == expected_username

            # קבלת שאלה
            response = session.get(f"{BASE_URL}/api/question")
            assert response.status_code == 200

    def test_nginx_headers_forwarding(self):
        """בדיקת העברת headers דרך nginx"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post(f"{BASE_URL}/auth", data=login_data, allow_redirects=False)
        assert response.status_code == 302

        # בקשה עם headers מיוחדים
        custom_headers = {
            'User-Agent': 'TestClient/1.0',
            'X-Test-Header': 'test-value'
        }

        response = session.get(f"{BASE_URL}/verify", headers=custom_headers)
        assert response.status_code == 200

        # nginx אמור להעביר את הבקשה עם כל הheaders הנדרשים
        # (לא נוכל לבדוק את הheaders המועברים ישירות, אבל נבדוק שהתשובה תקינה)
        data = response.json()
        assert data['authenticated'] is True

    def test_different_endpoints_routing(self):
        """בדיקת ניתוב של endpoints שונים דרך nginx"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # בדיקת endpoints שונים
        endpoints_tests = [
            ('/verify', 200, 'auth-service'),
            ('/quiz', 200, 'quiz-service'),
            ('/api/question', 200, 'quiz-service'),
            ('/logout', 302, 'auth-service'),
        ]

        for endpoint, expected_status, service in endpoints_tests:
            response = session.get(f"{BASE_URL}{endpoint}", allow_redirects=False)
            assert response.status_code == expected_status, f"Failed for {endpoint} (expected {expected_status}, got {response.status_code})"

    def test_large_request_handling(self):
        """בדיקת טיפול בבקשות גדולות דרך nginx"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # שליחת תשובה לשאלה
        large_data = {
            'question_id': 1,
            'answer': True,
            'extra_data': 'x' * 1000  # נתונים גדולים
        }

        response = session.post(f"{BASE_URL}/api/answer",
                              json=large_data,
                              headers={'Content-Type': 'application/json'})
        # הבקשה אמורה לעבור דרך nginx בלי בעיות
        assert response.status_code in [200, 400, 404]  # תלוי ברישום השאלה

if __name__ == "__main__":
    # הרצת הטסטים
    print("🚀 מריץ טסטי nginx integration...")
    if HAS_PYTEST:
        pytest.main([__file__, "-v", "--tb=short"])
    else:
        unittest.main(verbosity=2)