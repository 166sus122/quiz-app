#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים לניהול sessions ו-cookies
בודק התמדות, תפוגה, אבטחה ובידוד של sessions
"""

import pytest
import requests
import time
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost"

class TestSessionManagement:
    """טסטים לניהול sessions"""

    def test_session_creation_on_login(self):
        """בדיקת יצירת session בהתחברות"""
        session = requests.Session()

        # לפני התחברות - אין session
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 401

        # התחברות
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post(f"{BASE_URL}/auth", data=login_data, allow_redirects=False)
        assert response.status_code == 302

        # בדיקה שנוצר session cookie
        assert 'session' in session.cookies
        session_cookie = session.cookies.get('session')
        assert session_cookie is not None
        assert len(session_cookie) > 10  # cookie אמור להיות מספיק ארוך

        # בדיקה שהsession עובד
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 200
        data = response.json()
        assert data['authenticated'] is True
        assert data['username'] == 'admin'

    def test_session_persistence_across_requests(self):
        """בדיקת התמדת session בין בקשות"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'demo', 'password': 'demo456'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # בקשות מרובות - session אמור להתמיד
        for i in range(10):
            response = session.get(f"{BASE_URL}/verify")
            assert response.status_code == 200
            data = response.json()
            assert data['username'] == 'demo'
            time.sleep(0.1)

    def test_session_destruction_on_logout(self):
        """בדיקת השמדת session ביציאה"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'user1', 'password': 'pass123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # בדיקה שמחובר
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 200

        # יציאה
        response = session.get(f"{BASE_URL}/logout", allow_redirects=False)
        assert response.status_code == 302

        # בדיקה שהsession בוטל
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 401

    def test_multiple_sessions_same_user(self):
        """בדיקת מספר sessions לאותו משתמש"""
        sessions = []

        # יצירת 3 sessions לאותו משתמש
        for i in range(3):
            session = requests.Session()
            login_data = {'username': 'admin', 'password': 'admin123'}
            response = session.post(f"{BASE_URL}/auth", data=login_data)
            assert response.status_code in [200, 302]
            sessions.append(session)

        # בדיקה שכל הsessions עובדים
        for i, session in enumerate(sessions):
            response = session.get(f"{BASE_URL}/verify")
            assert response.status_code == 200
            data = response.json()
            assert data['username'] == 'admin'

        # יציאה מsession אחד
        sessions[0].get(f"{BASE_URL}/logout")

        # בדיקה שהsessions האחרים עדיין עובדים
        for i, session in enumerate(sessions[1:], 1):
            response = session.get(f"{BASE_URL}/verify")
            assert response.status_code == 200

    def test_session_isolation_between_users(self):
        """בדיקת בידוד sessions בין משתמשים"""
        # יצירת sessions למשתמשים שונים
        users = [
            ('admin', 'admin123'),
            ('user1', 'pass123'),
            ('demo', 'demo456')
        ]

        sessions_data = []

        for username, password in users:
            session = requests.Session()
            login_data = {'username': username, 'password': password}
            response = session.post(f"{BASE_URL}/auth", data=login_data)
            assert response.status_code in [200, 302]
            sessions_data.append((session, username))

        # בדיקה שכל session מזהה את המשתמש הנכון
        for session, expected_username in sessions_data:
            response = session.get(f"{BASE_URL}/verify")
            assert response.status_code == 200
            data = response.json()
            assert data['username'] == expected_username

        # בדיקה שלא ניתן לערבב sessions
        for i, (session, _) in enumerate(sessions_data):
            # שימוש בsession של משתמש אחד עם נתונים של אחר
            for j, (_, other_username) in enumerate(sessions_data):
                if i != j:
                    response = session.get(f"{BASE_URL}/verify")
                    assert response.status_code == 200
                    data = response.json()
                    # אמור להחזיר את המשתמש הנכון ולא את האחר
                    assert data['username'] == sessions_data[i][1]

    def test_session_cookie_security_attributes(self):
        """בדיקת תכונות אבטחה של session cookies"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post(f"{BASE_URL}/auth", data=login_data)

        # בדיקת תכונות הcookie
        session_cookie = None
        for cookie in session.cookies:
            if cookie.name == 'session':
                session_cookie = cookie
                break

        assert session_cookie is not None

        # בדיקת domain
        assert session_cookie.domain == 'localhost' or session_cookie.domain == '.localhost'

        # בדיקת path
        assert session_cookie.path == '/'

        # בדיקת HttpOnly (אם נתמך)
        # הבדיקה תלויה ביישום של Flask

    def test_invalid_session_handling(self):
        """בדיקת טיפול בsession לא תקין"""
        session = requests.Session()

        # יצירת cookie לא תקין
        session.cookies.set('session', 'invalid_session_data', domain='localhost')

        # בקשה עם session לא תקין
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 401

        # בקשה ל-API עם session לא תקין
        response = session.get(f"{BASE_URL}/api/question")
        assert response.status_code == 200
        data = response.json()
        assert 'error' in data

    def test_session_after_password_change(self):
        """בדיקת session לאחר שינוי סיסמה (סימולציה)"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # בדיקה שמחובר
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 200

        # סימולציה של שינוי סיסמה על ידי התחברות חדשה
        # (במערכת אמיתית היה צריך endpoint לשינוי סיסמה)
        new_session = requests.Session()
        login_data_new = {'username': 'admin', 'password': 'admin123'}  # אותה סיסמה
        new_session.post(f"{BASE_URL}/auth", data=login_data_new)

        # בדיקה שהsession הישן עדיין עובד
        # (במערכת מאובטחת יותר, sessions קיימים היו מתבטלים)
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 200

    def test_concurrent_session_operations(self):
        """בדיקת פעולות session במקביל"""
        import threading
        results = []

        def login_and_verify():
            try:
                session = requests.Session()
                login_data = {'username': 'demo', 'password': 'demo456'}
                response = session.post(f"{BASE_URL}/auth", data=login_data)

                if response.status_code in [200, 302]:
                    verify_response = session.get(f"{BASE_URL}/verify")
                    results.append(verify_response.status_code == 200)
                else:
                    results.append(False)
            except Exception as e:
                print(f"Error in thread: {e}")
                results.append(False)

        # יצירת threads מרובים
        threads = []
        for i in range(5):
            thread = threading.Thread(target=login_and_verify)
            threads.append(thread)
            thread.start()

        # חכיה לסיום
        for thread in threads:
            thread.join()

        # בדיקה שכל הsessions נוצרו בהצלחה
        assert len(results) == 5
        assert all(results), f"Some sessions failed: {results}"

    def test_session_data_integrity(self):
        """בדיקת שלמות נתוני session"""
        session = requests.Session()

        # התחברות
        login_data = {'username': 'user1', 'password': 'pass123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # בדיקות מרובות שהנתונים עקביים
        for i in range(20):
            response = session.get(f"{BASE_URL}/verify")
            assert response.status_code == 200
            data = response.json()

            # הנתונים צריכים להיות עקביים בכל בקשה
            assert data['authenticated'] is True
            assert data['username'] == 'user1'
            assert 'username' in data

            time.sleep(0.05)

    def test_session_with_different_browsers(self):
        """סימולציה של משתמש עם browsers שונים"""
        # סימולציה של Chrome
        chrome_session = requests.Session()
        chrome_session.headers.update({'User-Agent': 'Mozilla/5.0 (Chrome)'})

        # סימולציה של Firefox
        firefox_session = requests.Session()
        firefox_session.headers.update({'User-Agent': 'Mozilla/5.0 (Firefox)'})

        # התחברות מ-Chrome
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = chrome_session.post(f"{BASE_URL}/auth", data=login_data)
        assert response.status_code in [200, 302]

        # התחברות מ-Firefox (אותו משתמש)
        response = firefox_session.post(f"{BASE_URL}/auth", data=login_data)
        assert response.status_code in [200, 302]

        # בדיקה ששני הsessions עובדים
        chrome_response = chrome_session.get(f"{BASE_URL}/verify")
        firefox_response = firefox_session.get(f"{BASE_URL}/verify")

        assert chrome_response.status_code == 200
        assert firefox_response.status_code == 200

        chrome_data = chrome_response.json()
        firefox_data = firefox_response.json()

        assert chrome_data['username'] == 'admin'
        assert firefox_data['username'] == 'admin'

    def test_session_without_permanent_flag(self):
        """בדיקת session ללא permanent flag"""
        # הטסט הזה בודק שהsession נוצר גם אם לא מסומן כpermanent
        # (בהתבסס על הקוד, sessions מסומנים כpermanent)

        session = requests.Session()
        login_data = {'username': 'demo', 'password': 'demo456'}
        response = session.post(f"{BASE_URL}/auth", data=login_data)
        assert response.status_code in [200, 302]

        # בדיקה שהsession עובד
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 200
        data = response.json()
        assert data['authenticated'] is True

if __name__ == "__main__":
    print("🍪 מריץ טסטי session management...")
    pytest.main([__file__, "-v", "--tb=short"])