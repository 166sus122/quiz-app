#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import requests
import time

class TestBasicFunctionality(unittest.TestCase):
    """
    טסטים בסיסיים לפונקציונליות האפליקציה
    """

    def setUp(self):
        """הכנה לכל טסט"""
        self.base_url = "http://localhost"
        self.wait_for_services()

    def wait_for_services(self, timeout=10):
        """המתנה עד שהשירותים יהיו זמינים"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/login", timeout=5)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        self.fail("השירותים לא זמינים")

    def test_login_page_accessible(self):
        """בדיקה שעמוד ההתחברות נגיש"""
        response = requests.get(f"{self.base_url}/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("התחבר כדי להתחיל לשחק", response.text)
        print("✅ עמוד התחברות נגיש")

    def test_successful_authentication_redirect(self):
        """בדיקה שהתחברות נכונה מחזירה redirect"""
        session = requests.Session()

        auth_data = {
            "username": "admin",
            "password": "admin123"
        }

        response = session.post(
            f"{self.base_url}/auth",
            data=auth_data,
            allow_redirects=False
        )

        # בדיקה שקיבלנו redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get('Location'), '/quiz')
        print("✅ התחברות נכונה מחזירה redirect ל-/quiz")

    def test_failed_authentication_returns_error(self):
        """בדיקה שהתחברות שגויה מחזירה שגיאה"""
        session = requests.Session()

        auth_data = {
            "username": "admin",
            "password": "wrong_password"
        }

        response = session.post(f"{self.base_url}/auth", data=auth_data)

        # בדיקה שקיבלנו שגיאה
        self.assertEqual(response.status_code, 401)
        self.assertIn("שם משתמש או סיסמה שגויים", response.text)
        print("✅ התחברות שגויה מחזירה שגיאה מתאימה")

    def test_empty_credentials_validation(self):
        """בדיקה ששדות ריקים מחזירים שגיאת ולידציה"""
        session = requests.Session()

        auth_data = {
            "username": "",
            "password": ""
        }

        response = session.post(f"{self.base_url}/auth", data=auth_data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("אנא מלא את כל השדות", response.text)
        print("✅ שדות ריקים מחזירים שגיאת ולידציה")

    def test_unauthenticated_api_access_denied(self):
        """בדיקה שגישה ל-API ללא אימות נדחית"""
        # ניסיון גישה לשאלה ללא התחברות
        response = requests.get(f"{self.base_url}/api/question")

        self.assertEqual(response.status_code, 401)

        data = response.json()
        self.assertIn('error', data)
        self.assertIn('לא מאומת', data['error'])
        print("✅ גישה ל-API ללא אימות נדחית")

    def test_quiz_redirect_to_login_when_unauthenticated(self):
        """בדיקה שגישה ל-/quiz ללא אימות מפנה להתחברות"""
        response = requests.get(f"{self.base_url}/quiz", allow_redirects=False)

        if response.status_code == 302:
            # צפוי להיות redirect ל-login
            location = response.headers.get('Location', '')
            self.assertIn('login', location.lower())
            print("✅ גישה ל-/quiz ללא אימות מפנה להתחברות")
        elif response.status_code == 401:
            # גם זה בסדר - סימן שהאימות עובד
            print("✅ גישה ל-/quiz ללא אימות נדחית (401)")
        else:
            self.fail(f"תוצאה לא צפויה: {response.status_code}")

    def test_multiple_users_can_authenticate(self):
        """בדיקה שמספר משתמשים יכולים להתחבר"""
        users = [
            ("admin", "admin123"),
            ("user1", "pass123"),
            ("demo", "demo456")
        ]

        for username, password in users:
            with self.subTest(user=username):
                session = requests.Session()
                auth_data = {"username": username, "password": password}

                response = session.post(
                    f"{self.base_url}/auth",
                    data=auth_data,
                    allow_redirects=False
                )

                self.assertEqual(response.status_code, 302)
                print(f"✅ משתמש {username} יכול להתחבר")

    def test_logout_redirects_to_login(self):
        """בדיקה שיציאה מפנה להתחברות"""
        response = requests.get(f"{self.base_url}/logout", allow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get('Location'), '/login')
        print("✅ יציאה מפנה לעמוד התחברות")

    def test_home_redirects_to_login(self):
        """בדיקה שעמוד הבית מפנה להתחברות"""
        response = requests.get(f"{self.base_url}/", allow_redirects=False)

        self.assertEqual(response.status_code, 301)
        location = response.headers.get('Location', '')
        self.assertTrue(location.endswith('/login'), f"Expected URL ending with /login, got: {location}")
        print("✅ עמוד הבית מפנה להתחברות")

if __name__ == '__main__':
    print("🧪 מריץ טסטים בסיסיים...")
    unittest.main(verbosity=2)