#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
סקריפט הרצת כל הטסטים עבור אפליקציית החידות
"""

import unittest
import sys
import os

# הוספת הנתיב של התיקיה הראשית
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """הרצת כל הטסטים"""

    print("🧪 מתחיל להריץ את כל הטסטים לאפליקציית החידות")
    print("=" * 60)

    # יצירת test loader
    loader = unittest.TestLoader()

    # חיפוש כל הטסטים בתיקיה
    test_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(test_dir, pattern='test_*.py')

    # הרצת הטסטים
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("📊 סיכום תוצאות הטסטים:")
    print(f"✅ טסטים שעברו: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ טסטים שנכשלו: {len(result.failures)}")
    print(f"🚫 שגיאות: {len(result.errors)}")

    if result.failures:
        print("\n🔍 פירוט כשלונות:")
        for test, traceback in result.failures:
            print(f"❌ {test}: {traceback}")

    if result.errors:
        print("\n🔍 פירוט שגיאות:")
        for test, traceback in result.errors:
            print(f"🚫 {test}: {traceback}")

    # החזרת קוד יציאה
    return 0 if result.wasSuccessful() else 1

def run_specific_test(test_name):
    """הרצת טסט ספציפי"""

    print(f"🧪 מריץ טסט ספציפי: {test_name}")
    print("=" * 60)

    # יצירת test suite עבור טסט ספציפי
    suite = unittest.TestSuite()

    try:
        if test_name == "auth":
            from test_auth import TestAuthentication
            suite.addTest(unittest.makeSuite(TestAuthentication))
        elif test_name == "api":
            from test_api import TestQuizAPI
            suite.addTest(unittest.makeSuite(TestQuizAPI))
        elif test_name == "basic":
            from test_basic import TestBasicFunctionality
            suite.addTest(unittest.makeSuite(TestBasicFunctionality))
        elif test_name == "security":
            from test_security import TestSecurityFeatures
            suite.addTest(unittest.makeSuite(TestSecurityFeatures))
        elif test_name == "nginx":
            print("🌐 מריץ טסטי nginx integration עם pytest...")
            os.system("python3 test_nginx_integration.py")
            return 0
        elif test_name == "advanced_api":
            print("🚀 מריץ טסטי API מתקדמים עם pytest...")
            os.system("python3 test_advanced_api.py")
            return 0
        elif test_name == "sessions":
            print("🍪 מריץ טסטי session management עם pytest...")
            os.system("python3 test_session_management.py")
            return 0
        elif test_name == "advanced_security":
            print("🛡️ מריץ טסטי אבטחה מתקדמים עם pytest...")
            os.system("python3 test_advanced_security.py")
            return 0
        elif test_name == "integration":
            print("🎮 מריץ טסט אינטגרציה מלא עם pytest...")
            os.system("python3 test_full_integration.py")
            return 0
        else:
            print(f"❌ טסט לא מוכר: {test_name}")
            print("טסטים זמינים:")
            print("  בסיסיים: auth, api, basic, security")
            print("  מתקדמים: nginx, advanced_api, sessions, advanced_security, integration")
            return 1

        # הרצת הטסט
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        return 0 if result.wasSuccessful() else 1

    except ImportError as e:
        print(f"❌ שגיאה בייבוא הטסט: {e}")
        return 1

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # הרצת טסט ספציפי
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        # הרצת כל הטסטים
        exit_code = run_all_tests()

    sys.exit(exit_code)