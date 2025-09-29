#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים מתקדמים ל-API של אפליקציית החידות
בודק שאלות, תשובות, ניקוד ואבטחה
"""

import pytest
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost"

class TestAdvancedAPI:
    """טסטים מתקדמים ל-API"""

    @pytest.fixture
    def authenticated_session(self):
        """יצירת session מאומת"""
        session = requests.Session()
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post(f"{BASE_URL}/auth", data=login_data)
        assert response.status_code in [200, 302]
        return session

    @pytest.fixture
    def demo_session(self):
        """יצירת session לmשתמש demo"""
        session = requests.Session()
        login_data = {'username': 'demo', 'password': 'demo456'}
        response = session.post(f"{BASE_URL}/auth", data=login_data)
        assert response.status_code in [200, 302]
        return session

    def test_api_question_structure(self, authenticated_session):
        """בדיקת מבנה תשובת שאלה"""
        response = authenticated_session.get(f"{BASE_URL}/api/question")
        assert response.status_code == 200

        data = response.json()
        required_fields = ['id', 'question', 'type']
        for field in required_fields:
            assert field in data, f"שדה חסר: {field}"

        # בדיקת סוג השאלה
        assert data['type'] in ['multiple_choice', 'true_false']

        if data['type'] == 'multiple_choice':
            assert 'options' in data
            assert isinstance(data['options'], list)
            assert len(data['options']) >= 2

        # בדיקת explanation (אופציונלי)
        if 'explanation' in data:
            assert isinstance(data['explanation'], str)

    def test_multiple_questions_are_different(self, authenticated_session):
        """בדיקה שמתקבלות שאלות שונות"""
        questions = []
        for i in range(10):
            response = authenticated_session.get(f"{BASE_URL}/api/question")
            assert response.status_code == 200
            data = response.json()
            questions.append(data['id'])
            time.sleep(0.1)

        # בדיקה שיש לפחות כמה שאלות שונות
        unique_questions = set(questions)
        assert len(unique_questions) >= 3, "צריכות להיות לפחות 3 שאלות שונות"

    def test_answer_submission_correct(self, authenticated_session):
        """בדיקת שליחת תשובה נכונה"""
        # קבלת שאלה
        response = authenticated_session.get(f"{BASE_URL}/api/question")
        assert response.status_code == 200
        question = response.json()

        # שליחת תשובה נכונה
        answer_data = {
            'question_id': question['id'],
            'answer': question['correct_answer']
        }

        response = authenticated_session.post(f"{BASE_URL}/api/answer",
                                            json=answer_data,
                                            headers={'Content-Type': 'application/json'})

        assert response.status_code == 200
        result = response.json()

        assert 'correct' in result
        assert result['correct'] is True
        assert 'score' in result
        assert isinstance(result['score'], int)
        assert result['score'] > 0

    def test_answer_submission_incorrect(self, authenticated_session):
        """בדיקת שליחת תשובה שגויה"""
        # קבלת שאלה
        response = authenticated_session.get(f"{BASE_URL}/api/question")
        assert response.status_code == 200
        question = response.json()

        # יצירת תשובה שגויה
        if question['type'] == 'true_false':
            wrong_answer = not question['correct_answer']
        else:  # multiple_choice
            # נבחר תשובה שגויה
            correct_idx = question['correct_answer']
            wrong_answer = (correct_idx + 1) % len(question['options'])

        answer_data = {
            'question_id': question['id'],
            'answer': wrong_answer
        }

        response = authenticated_session.post(f"{BASE_URL}/api/answer",
                                            json=answer_data,
                                            headers={'Content-Type': 'application/json'})

        assert response.status_code == 200
        result = response.json()

        assert result['correct'] is False
        # הניקוד לא אמור להשתנות בתשובה שגויה
        assert 'score' in result

    def test_invalid_question_id(self, authenticated_session):
        """בדיקת שליחת תשובה עם ID שאלה לא קיים"""
        answer_data = {
            'question_id': 99999,  # ID לא קיים
            'answer': True
        }

        response = authenticated_session.post(f"{BASE_URL}/api/answer",
                                            json=answer_data,
                                            headers={'Content-Type': 'application/json'})

        # אמור לקבל שגיאה או להתעלם מהתשובה
        assert response.status_code in [400, 404, 200]

    def test_malformed_answer_data(self, authenticated_session):
        """בדיקת נתונים לא תקינים בשליחת תשובה"""
        test_cases = [
            {},  # ריק
            {'question_id': 'not_a_number'},  # ID לא מספר
            {'answer': True},  # חסר question_id
            {'question_id': 1},  # חסר answer
            {'question_id': 1, 'answer': 'invalid_type'},  # סוג תשובה לא תקין
        ]

        for invalid_data in test_cases:
            response = authenticated_session.post(f"{BASE_URL}/api/answer",
                                                json=invalid_data,
                                                headers={'Content-Type': 'application/json'})
            assert response.status_code in [400, 422]

    def test_score_accumulation(self, authenticated_session):
        """בדיקת צבירת ניקוד"""
        initial_score = 0
        current_score = initial_score

        for i in range(5):
            # קבלת שאלה
            response = authenticated_session.get(f"{BASE_URL}/api/question")
            assert response.status_code == 200
            question = response.json()

            # שליחת תשובה נכונה
            answer_data = {
                'question_id': question['id'],
                'answer': question['correct_answer']
            }

            response = authenticated_session.post(f"{BASE_URL}/api/answer",
                                                json=answer_data,
                                                headers={'Content-Type': 'application/json'})

            assert response.status_code == 200
            result = response.json()

            if result['correct']:
                # הניקוד אמור לעלות
                assert result['score'] > current_score
                current_score = result['score']

            time.sleep(0.1)

    def test_concurrent_api_calls(self, authenticated_session):
        """בדיקת קריאות API במקביל"""
        import threading
        results = []

        def make_request():
            response = authenticated_session.get(f"{BASE_URL}/api/question")
            results.append(response.status_code)

        # יצירת threads מרובים
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # חכיה לסיום כל הthreads
        for thread in threads:
            thread.join()

        # בדיקה שכל הבקשות הצליחו
        assert len(results) == 10
        for status_code in results:
            assert status_code == 200

    def test_api_without_authentication(self):
        """בדיקת גישה ל-API ללא אימות"""
        # בקשה ללא session cookies
        response = requests.get(f"{BASE_URL}/api/question")
        assert response.status_code == 200

        data = response.json()
        # אמור לקבל הודעת שגיאה
        assert 'error' in data
        assert data['error'] == 'לא מאומת'
        assert data.get('redirect') == '/login'

        # בקשת תשובה ללא אימות
        answer_data = {'question_id': 1, 'answer': True}
        response = requests.post(f"{BASE_URL}/api/answer",
                               json=answer_data,
                               headers={'Content-Type': 'application/json'})

        data = response.json()
        assert 'error' in data

    def test_session_isolation_between_users(self):
        """בדיקת בידוד sessions בין משתמשים שונים"""
        # יצירת שני sessions למשתמשים שונים
        session1 = requests.Session()
        session2 = requests.Session()

        # התחברות משתמש 1
        login_data1 = {'username': 'admin', 'password': 'admin123'}
        session1.post(f"{BASE_URL}/auth", data=login_data1)

        # התחברות משתמש 2
        login_data2 = {'username': 'demo', 'password': 'demo456'}
        session2.post(f"{BASE_URL}/auth", data=login_data2)

        # בדיקה שכל session מזהה את המשתמש הנכון
        response1 = session1.get(f"{BASE_URL}/verify")
        response2 = session2.get(f"{BASE_URL}/verify")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1['username'] == 'admin'
        assert data2['username'] == 'demo'

        # בדיקה שהניקוד נפרד
        # משתמש 1 עונה על שאלה
        response = session1.get(f"{BASE_URL}/api/question")
        question = response.json()
        answer_data = {'question_id': question['id'], 'answer': question['correct_answer']}
        response = session1.post(f"{BASE_URL}/api/answer", json=answer_data,
                               headers={'Content-Type': 'application/json'})
        user1_score = response.json().get('score', 0)

        # משתמש 2 צריך להתחיל מניקוד 0
        response = session2.get(f"{BASE_URL}/api/question")
        question = response.json()
        answer_data = {'question_id': question['id'], 'answer': question['correct_answer']}
        response = session2.post(f"{BASE_URL}/api/answer", json=answer_data,
                               headers={'Content-Type': 'application/json'})
        user2_score = response.json().get('score', 0)

        # הניקודים יכולים להיות שונים (תלוי באם זה התחלה של המשחק או לא)

    def test_api_rate_limiting_behavior(self, authenticated_session):
        """בדיקת התנהגות עם בקשות מהירות"""
        # שליחת בקשות מהירות רצופות
        response_times = []
        status_codes = []

        for i in range(20):
            start_time = time.time()
            response = authenticated_session.get(f"{BASE_URL}/api/question")
            end_time = time.time()

            response_times.append(end_time - start_time)
            status_codes.append(response.status_code)

        # כל הבקשות אמורות להצליח (אין rate limiting כרגע)
        assert all(code == 200 for code in status_codes)

        # זמני התגובה אמורים להיות סבירים
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 1.0, f"זמן תגובה ממוצע גבוה מדי: {avg_response_time:.2f}s"

    def test_large_payload_handling(self, authenticated_session):
        """בדיקת טיפול ב-payloads גדולים"""
        # יצירת payload גדול
        large_answer_data = {
            'question_id': 1,
            'answer': True,
            'extra_field': 'x' * 10000,  # 10KB של נתונים נוספים
            'metadata': {
                'timestamp': time.time(),
                'user_agent': 'TestClient/1.0',
                'extra_data': ['a'] * 1000
            }
        }

        response = authenticated_session.post(f"{BASE_URL}/api/answer",
                                            json=large_answer_data,
                                            headers={'Content-Type': 'application/json'})

        # הבקשה אמורה להתקבל (גם אם יתעלמו מהשדות הנוספים)
        assert response.status_code in [200, 400, 413]  # 413 = Payload Too Large

if __name__ == "__main__":
    print("🧪 מריץ טסטים מתקדמים ל-API...")
    pytest.main([__file__, "-v", "--tb=short"])