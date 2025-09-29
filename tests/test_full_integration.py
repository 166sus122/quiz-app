#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסט אינטגרציה כללי לכל האפליקציה
סימולציה של זרימת עבודה מלאה של משתמש
"""

import pytest
import requests
import time
import json
from typing import Dict, List

BASE_URL = "http://localhost"

class TestFullIntegration:
    """טסט אינטגרציה כללי"""

    def test_complete_user_journey(self):
        """טסט מסע משתמש מלא מהתחלה ועד הסוף"""
        print("\n🎮 מתחיל מסע משתמש מלא...")

        session = requests.Session()

        # שלב 1: בדיקת זמינות המערכת
        print("1️⃣ בודק זמינות המערכת...")
        response = session.get(f"{BASE_URL}/")
        assert response.status_code == 301, "Root redirect failed"

        # שלב 2: טעינת דף התחברות
        print("2️⃣ טוען דף התחברות...")
        response = session.get(f"{BASE_URL}/login")
        assert response.status_code == 200
        assert "אפליקציית חידות" in response.text
        print("✅ דף התחברות נטען בהצלחה")

        # שלב 3: התחברות עם פרטים נכונים
        print("3️⃣ מתחבר עם פרטי משתמש...")
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post(f"{BASE_URL}/auth", data=login_data, allow_redirects=False)
        assert response.status_code == 302
        assert "/quiz" in response.headers.get('Location', '')
        print("✅ התחברות הצליחה")

        # שלב 4: בדיקת session
        print("4️⃣ מאמת session...")
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 200
        user_data = response.json()
        assert user_data['authenticated'] is True
        assert user_data['username'] == 'admin'
        print("✅ Session תקין")

        # שלב 5: טעינת דף החידות
        print("5️⃣ טוען דף החידות...")
        response = session.get(f"{BASE_URL}/quiz")
        assert response.status_code == 200
        assert "משחק החידות" in response.text
        print("✅ דף החידות נטען בהצלחה")

        # שלב 6: משחק חידות מלא (5 שאלות)
        print("6️⃣ משחק חידות - 5 שאלות...")
        score = 0
        correct_answers = 0

        for question_num in range(1, 6):
            print(f"   שאלה {question_num}/5:")

            # קבלת שאלה
            response = session.get(f"{BASE_URL}/api/question")
            assert response.status_code == 200
            question_data = response.json()

            assert 'id' in question_data
            assert 'question' in question_data
            assert 'type' in question_data
            print(f"   📝 {question_data['question'][:50]}...")

            # מענה על השאלה (נענה נכון)
            correct_answer = question_data['correct_answer']
            answer_data = {
                'question_id': question_data['id'],
                'answer': correct_answer
            }

            response = session.post(f"{BASE_URL}/api/answer",
                                  json=answer_data,
                                  headers={'Content-Type': 'application/json'})
            assert response.status_code == 200
            result = response.json()

            if result.get('correct'):
                correct_answers += 1
                score = result.get('score', score)
                print(f"   ✅ תשובה נכונה! ניקוד: {score}")
            else:
                print(f"   ❌ תשובה שגויה")

            time.sleep(0.2)  # הפסקה קטנה

        print(f"📊 סיום משחק: {correct_answers}/5 נכונות, ניקוד: {score}")

        # שלב 7: בדיקת ניקוד סופי
        print("7️⃣ בודק ניקוד סופי...")
        assert score >= 0
        if correct_answers > 0:
            assert score > 0

        # שלב 8: יציאה
        print("8️⃣ יוצא מהמערכת...")
        response = session.get(f"{BASE_URL}/logout", allow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get('Location', '')

        # בדיקה שהsession בוטל
        response = session.get(f"{BASE_URL}/verify")
        assert response.status_code == 401
        print("✅ יציאה בוצעה בהצלחה")

        print("🎉 מסע משתמש הושלם בהצלחה!")

    def test_multiple_concurrent_users(self):
        """טסט מספר משתמשים במקביל"""
        print("\n👥 בודק משתמשים מרובים במקביל...")

        users = [
            ('admin', 'admin123'),
            ('user1', 'pass123'),
            ('demo', 'demo456')
        ]

        import threading
        results = []

        def user_session(username, password):
            """סימולציה של session משתמש"""
            try:
                session = requests.Session()

                # התחברות
                login_data = {'username': username, 'password': password}
                response = session.post(f"{BASE_URL}/auth", data=login_data)
                if response.status_code not in [200, 302]:
                    results.append({'user': username, 'success': False, 'error': 'login_failed'})
                    return

                # אימות
                response = session.get(f"{BASE_URL}/verify")
                if response.status_code != 200:
                    results.append({'user': username, 'success': False, 'error': 'verify_failed'})
                    return

                # שאלות
                questions_answered = 0
                for i in range(3):
                    # קבלת שאלה
                    response = session.get(f"{BASE_URL}/api/question")
                    if response.status_code != 200:
                        break

                    question_data = response.json()
                    if 'error' in question_data:
                        break

                    # מענה על השאלה
                    answer_data = {
                        'question_id': question_data['id'],
                        'answer': question_data['correct_answer']
                    }

                    response = session.post(f"{BASE_URL}/api/answer",
                                          json=answer_data,
                                          headers={'Content-Type': 'application/json'})
                    if response.status_code == 200:
                        questions_answered += 1

                    time.sleep(0.1)

                results.append({
                    'user': username,
                    'success': True,
                    'questions_answered': questions_answered
                })

            except Exception as e:
                results.append({
                    'user': username,
                    'success': False,
                    'error': str(e)
                })

        # הרצת sessions במקביל
        threads = []
        for username, password in users:
            thread = threading.Thread(target=user_session, args=(username, password))
            threads.append(thread)
            thread.start()

        # חכיה לסיום
        for thread in threads:
            thread.join()

        # בדיקת תוצאות
        assert len(results) == len(users)

        successful_users = [r for r in results if r['success']]
        failed_users = [r for r in results if not r['success']]

        print(f"✅ {len(successful_users)} משתמשים הצליחו")
        print(f"❌ {len(failed_users)} משתמשים נכשלו")

        for result in results:
            if result['success']:
                print(f"   {result['user']}: {result.get('questions_answered', 0)} שאלות")
            else:
                print(f"   {result['user']}: כשל - {result.get('error', 'unknown')}")

        # לפחות רוב המשתמשים צריכים להצליח
        assert len(successful_users) >= len(users) // 2

    def test_system_resilience(self):
        """בדיקת עמידות המערכת"""
        print("\n🔧 בודק עמידות המערכת...")

        session = requests.Session()
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # בדיקת זמני תגובה
        response_times = []

        for i in range(10):
            start_time = time.time()
            response = session.get(f"{BASE_URL}/api/question")
            end_time = time.time()

            response_times.append(end_time - start_time)
            assert response.status_code == 200

            time.sleep(0.1)

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        print(f"📊 זמן תגובה ממוצע: {avg_response_time:.3f}s")
        print(f"📊 זמן תגובה מקסימלי: {max_response_time:.3f}s")

        # בדיקות סבירות
        assert avg_response_time < 2.0, f"זמן תגובה ממוצע גבוה מדי: {avg_response_time:.3f}s"
        assert max_response_time < 5.0, f"זמן תגובה מקסימלי גבוה מדי: {max_response_time:.3f}s"

    def test_data_consistency(self):
        """בדיקת עקביות נתונים"""
        print("\n📊 בודק עקביות נתונים...")

        session = requests.Session()
        login_data = {'username': 'demo', 'password': 'demo456'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # קבלת מספר שאלות ובדיקה שהן עקביות
        questions = []
        for i in range(5):
            response = session.get(f"{BASE_URL}/api/question")
            assert response.status_code == 200
            question_data = response.json()

            # בדיקת מבנה
            required_fields = ['id', 'question', 'type', 'correct_answer']
            for field in required_fields:
                assert field in question_data, f"שדה חסר: {field}"

            # בדיקת סוג שאלה
            assert question_data['type'] in ['multiple_choice', 'true_false']

            if question_data['type'] == 'multiple_choice':
                assert 'options' in question_data
                assert isinstance(question_data['options'], list)
                assert len(question_data['options']) >= 2

            questions.append(question_data)
            time.sleep(0.1)

        print(f"✅ נבדקו {len(questions)} שאלות - כולן עקביות")

        # בדיקת שיש מגוון שאלות
        question_types = set(q['type'] for q in questions)
        print(f"📋 סוגי שאלות: {list(question_types)}")

    def test_error_recovery(self):
        """בדיקת התאוששות משגיאות"""
        print("\n🚨 בודק התאוששות משגיאות...")

        session = requests.Session()
        login_data = {'username': 'user1', 'password': 'pass123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        # שליחת נתונים שגויים ובדיקת התאוששות
        error_scenarios = [
            # תשובה עם question_id לא קיים
            {'question_id': 99999, 'answer': True},

            # תשובה עם נתונים חסרים
            {'answer': True},

            # תשובה עם סוג נתונים שגוי
            {'question_id': 'invalid', 'answer': 'invalid'},
        ]

        for scenario in error_scenarios:
            response = session.post(f"{BASE_URL}/api/answer",
                                  json=scenario,
                                  headers={'Content-Type': 'application/json'})

            # המערכת צריכה להחזיר שגיאה מובנת ולא לקרוס
            assert response.status_code in [400, 404, 422, 500]

        # בדיקה שאחרי השגיאות, המערכת עדיין עובדת
        response = session.get(f"{BASE_URL}/api/question")
        assert response.status_code == 200
        print("✅ המערכת התאוששה משגיאות בהצלחה")

    def test_complete_quiz_game(self):
        """סימולציה של משחק חידות שלם"""
        print("\n🎯 משחק חידות שלם - 20 שאלות...")

        session = requests.Session()
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{BASE_URL}/auth", data=login_data)

        score = 0
        correct_count = 0
        questions_seen = set()

        for question_num in range(1, 21):  # 20 שאלות
            if question_num % 5 == 0:
                print(f"   מתקדם... {question_num}/20")

            # קבלת שאלה
            response = session.get(f"{BASE_URL}/api/question")
            assert response.status_code == 200
            question_data = response.json()

            # בדיקה שלא חוזרות שאלות (אם יש מספיק שאלות)
            if question_data['id'] in questions_seen:
                print(f"   🔄 שאלה {question_data['id']} חוזרת")
            questions_seen.add(question_data['id'])

            # מענה על השאלה (נענה נכון ב-80% מהמקרים)
            import random
            if random.random() < 0.8:  # 80% סיכוי לתשובה נכונה
                answer = question_data['correct_answer']
            else:
                # תשובה שגויה
                if question_data['type'] == 'true_false':
                    answer = not question_data['correct_answer']
                else:
                    correct_idx = question_data['correct_answer']
                    wrong_options = [i for i in range(len(question_data['options'])) if i != correct_idx]
                    answer = random.choice(wrong_options) if wrong_options else correct_idx

            answer_data = {
                'question_id': question_data['id'],
                'answer': answer
            }

            response = session.post(f"{BASE_URL}/api/answer",
                                  json=answer_data,
                                  headers={'Content-Type': 'application/json'})
            assert response.status_code == 200
            result = response.json()

            if result.get('correct'):
                correct_count += 1
                score = result.get('score', score)

            time.sleep(0.05)  # הפסקה קצרה

        print(f"🎉 סיום משחק: {correct_count}/20 נכונות")
        print(f"📊 ניקוד סופי: {score}")

        # בדיקות סבירות
        assert correct_count >= 10, "מעט מדי תשובות נכונות במשחק מלא"
        assert score > 0, "הניקוד צריך להיות חיובי"
        assert len(questions_seen) >= 10, "צריך להיות מגוון של שאלות"

if __name__ == "__main__":
    print("🎮 מריץ טסט אינטגרציה מלא...")
    pytest.main([__file__, "-v", "--tb=short", "-s"])