#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import requests
import json
import time

class TestQuizAPI(unittest.TestCase):
    """
    טסטים לבדיקת API של אפליקציית החידות
    """

    def setUp(self):
        """הכנה לכל טסט"""
        self.base_url = "http://localhost"
        self.session = requests.Session()

        # הכנה - התחברות עם משתמש קיים
        self.authenticate()

    def authenticate(self):
        """התחברות למערכת לפני כל טסט"""
        auth_data = {
            "username": "admin",
            "password": "admin123"
        }

        auth_response = self.session.post(f"{self.base_url}/auth", data=auth_data)
        self.assertEqual(auth_response.status_code, 302, "התחברות נכשלה בהכנה לטסט")

    def test_get_question_authenticated(self):
        """בדיקת קבלת שאלה כשמשתמש מאומת"""

        response = self.session.get(f"{self.base_url}/api/question")

        # בדיקת response code
        self.assertEqual(response.status_code, 200)

        # בדיקת תוכן התשובה
        data = response.json()

        # בדיקת שדות חובה
        required_fields = ['id', 'type', 'question', 'explanation']
        for field in required_fields:
            self.assertIn(field, data, f"שדה {field} חסר בתשובה")

        # בדיקת סוג השאלה
        self.assertIn(data['type'], ['multiple_choice', 'true_false'])

        # בדיקת שדות לפי סוג השאלה
        if data['type'] == 'multiple_choice':
            self.assertIn('options', data)
            self.assertIsInstance(data['options'], list)
            self.assertGreater(len(data['options']), 1)

        self.assertIn('correct_answer', data)

        print(f"✅ קיבלנו שאלה מסוג {data['type']}: {data['question'][:50]}...")

    def test_get_question_unauthenticated(self):
        """בדיקת קבלת שאלה כשמשתמש לא מאומת"""

        # יצירת session חדש ללא אימות
        unauthenticated_session = requests.Session()

        response = unauthenticated_session.get(f"{self.base_url}/api/question")

        # בדיקה שקיבלנו 401 Unauthorized
        self.assertEqual(response.status_code, 401)

        data = response.json()
        self.assertIn('error', data)
        self.assertIn('redirect', data)

        print("✅ טסט גישה לשאלה ללא אימות - עבר")

    def test_submit_correct_answer(self):
        """בדיקת שליחת תשובה נכונה"""

        # קבלת שאלה
        question_response = self.session.get(f"{self.base_url}/api/question")
        question_data = question_response.json()

        # שליחת התשובה הנכונה
        answer_data = {
            "question_id": question_data['id'],
            "answer": question_data['correct_answer']
        }

        answer_response = self.session.post(
            f"{self.base_url}/api/answer",
            json=answer_data
        )

        self.assertEqual(answer_response.status_code, 200)

        result = answer_response.json()
        self.assertIn('correct', result)
        self.assertIn('score', result)
        self.assertIn('explanation', result)

        # בדיקה שהתשובה נכונה
        self.assertTrue(result['correct'])
        self.assertGreaterEqual(result['score'], 1)

        print(f"✅ תשובה נכונה נשלחה בהצלחה. ניקוד: {result['score']}")

    def test_submit_incorrect_answer(self):
        """בדיקת שליחת תשובה שגויה"""

        # קבלת שאלה
        question_response = self.session.get(f"{self.base_url}/api/question")
        question_data = question_response.json()

        # יצירת תשובה שגויה
        if question_data['type'] == 'multiple_choice':
            # למשל, אם התשובה הנכונה היא 0, נשלח 1
            wrong_answer = (question_data['correct_answer'] + 1) % len(question_data['options'])
        else:  # true_false
            # אם התשובה הנכונה true, נשלח false ולהיפך
            wrong_answer = not question_data['correct_answer']

        answer_data = {
            "question_id": question_data['id'],
            "answer": wrong_answer
        }

        answer_response = self.session.post(
            f"{self.base_url}/api/answer",
            json=answer_data
        )

        self.assertEqual(answer_response.status_code, 200)

        result = answer_response.json()

        # בדיקה שהתשובה שגויה
        self.assertFalse(result['correct'])

        print("✅ תשובה שגויה נשלחה בהצלחה")

    def test_submit_answer_unauthenticated(self):
        """בדיקת שליחת תשובה ללא אימות"""

        unauthenticated_session = requests.Session()

        answer_data = {
            "question_id": 1,
            "answer": 0
        }

        response = unauthenticated_session.post(
            f"{self.base_url}/api/answer",
            json=answer_data
        )

        self.assertEqual(response.status_code, 401)

        data = response.json()
        self.assertIn('error', data)

        print("✅ טסט שליחת תשובה ללא אימות - עבר")

    def test_submit_invalid_question_id(self):
        """בדיקת שליחת תשובה עם ID שאלה לא קיים"""

        answer_data = {
            "question_id": 99999,  # ID לא קיים
            "answer": 0
        }

        response = self.session.post(
            f"{self.base_url}/api/answer",
            json=answer_data
        )

        self.assertEqual(response.status_code, 404)

        data = response.json()
        self.assertIn('error', data)
        self.assertIn('שאלה לא נמצאה', data['error'])

        print("✅ טסט ID שאלה לא קיים - עבר")

    def test_get_score(self):
        """בדיקת קבלת ניקוד נוכחי"""

        response = self.session.get(f"{self.base_url}/api/score")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('score', data)
        self.assertIn('answered', data)

        # בדיקה שהערכים הגיוניים
        self.assertIsInstance(data['score'], int)
        self.assertIsInstance(data['answered'], int)
        self.assertGreaterEqual(data['score'], 0)
        self.assertGreaterEqual(data['answered'], 0)

        print(f"✅ ניקוד נוכחי: {data['score']}, שאלות שנענו: {data['answered']}")

    def test_get_score_unauthenticated(self):
        """בדיקת קבלת ניקוד ללא אימות"""

        unauthenticated_session = requests.Session()

        response = unauthenticated_session.get(f"{self.base_url}/api/score")

        self.assertEqual(response.status_code, 401)

        print("✅ טסט קבלת ניקוד ללא אימות - עבר")

    def test_quiz_full_flow(self):
        """בדיקת זרימה מלאה של המשחק"""

        initial_score_response = self.session.get(f"{self.base_url}/api/score")
        initial_score = initial_score_response.json()['score']

        # ענה על 3 שאלות
        for i in range(3):
            # קבל שאלה
            question_response = self.session.get(f"{self.base_url}/api/question")
            self.assertEqual(question_response.status_code, 200)

            question_data = question_response.json()

            # שלח תשובה נכונה
            answer_data = {
                "question_id": question_data['id'],
                "answer": question_data['correct_answer']
            }

            answer_response = self.session.post(
                f"{self.base_url}/api/answer",
                json=answer_data
            )

            self.assertEqual(answer_response.status_code, 200)
            result = answer_response.json()
            self.assertTrue(result['correct'])

        # בדוק שהניקוד עלה
        final_score_response = self.session.get(f"{self.base_url}/api/score")
        final_score = final_score_response.json()['score']

        self.assertGreater(final_score, initial_score)

        print(f"✅ זרימה מלאה: ניקוד עלה מ-{initial_score} ל-{final_score}")

    def test_malformed_json_request(self):
        """בדיקת שליחת JSON לא תקין"""

        # שליחת JSON לא תקין
        response = self.session.post(
            f"{self.base_url}/api/answer",
            data="invalid json",  # לא JSON תקין
            headers={'Content-Type': 'application/json'}
        )

        # בדיקה שהשרת מטפל בזה בצורה נאותה
        self.assertIn(response.status_code, [400, 500])

        print("✅ טסט JSON לא תקין - עבר")

if __name__ == '__main__':
    print("🧪 מתחיל טסטים ל-API...")
    unittest.main(verbosity=2)