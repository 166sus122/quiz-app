# טסטים לאפליקציית החידות

תיקיה זו מכילה טסטים אוטומטיים מקיפים לבדיקת פונקציונליות האפליקציה, אבטחה ואינטגרציה.

## קבצי הטסטים:

### `test_auth.py` - טסטי אימות
- ✅ התחברות מוצלחת (admin, user1, demo)
- ❌ התחברות כושלת (סיסמה שגויה, משתמש לא קיים)
- 🔒 בדיקת שדות ריקים
- 🚫 מספר ניסיונות כושלים (Fail2Ban)
- 🔄 התמדת session
- 🚪 פונקציית יציאה

### `test_api.py` - טסטי API
- 📝 קבלת שאלות (מאומת/לא מאומת)
- ✅ שליחת תשובות נכונות
- ❌ שליחת תשובות שגויות
- 📊 בדיקת ניקוד
- 🔍 טיפול בשגיאות
- 🎮 זרימה מלאה של המשחק

### `test_basic.py` - טסטים בסיסיים
- 🌐 נגישות עמודים
- ↩️ redirects נכונים
- 👥 התחברות מספר משתמשים
- 🔐 בקרת גישה לדפים מוגנים
- 🚪 פונקציות logout

### `test_security.py` - טסטי אבטחה
- 🔒 Fail2Ban (חסימת IP לאחר ניסיונות כושלים)
- 💉 הגנה מפני SQL Injection
- 🔗 הגנה מפני XSS
- 🔑 בדיקת הצפנת סיסמאות
- 🍪 אבטחת Session
- 🚦 Rate Limiting

### **טסטים חדשים מתקדמים:**

### `test_nginx_integration.py` - טסטי אינטגרציה עם nginx
- 🔄 ניתוב בקשות דרך nginx reverse proxy
- 🍪 העברת cookies וsessions בין שירותים
- 🌐 בדיקת endpoints שונים (/login, /auth, /verify, /quiz, /api/)
- 👥 sessions מרובים במקביל
- 🚪 זרימת התחברות ויציאה דרך proxy
- 📡 בדיקת headers forwarding

### `test_advanced_api.py` - טסטי API מתקדמים
- 🧪 מבנה ועקביות תשובות API
- 🎯 טיפול בתשובות נכונות ושגויות מתקדם
- 🔢 מעקב אחר ניקוד וצבירה
- 💾 בדיקת שאלות מרובות ושונות
- 🚫 טיפול בנתונים לא תקינים ושגיאות
- ⚡ בקשות מקבילות ומהירות
- 👥 בידוד sessions בין משתמשים

### `test_session_management.py` - טסטי ניהול sessions מתקדמים
- 🍪 יצירה והשמדה של session cookies
- 🔄 התמדת sessions בין בקשות
- 👤 מספר sessions לאותו משתמש
- 🚧 בידוד sessions בין משתמשים שונים
- 🔐 תכונות אבטחה של cookies (domain, path, HttpOnly)
- ❌ טיפול בsessions לא תקינים
- 🌐 sessions עם דפדפנים שונים

### `test_advanced_security.py` - טסטי אבטחה מתקדמים
- 🔨 הגנת brute force מתקדמת
- 💉 בדיקת SQL injection payloads מגוונים
- 🔗 מניעת XSS עם payloads מורכבים
- 🔒 הגנה מפני session hijacking
- 🛡️ בדיקת CSRF protection
- 📁 מניעת directory traversal
- 🚫 ניסיונות עקיפת אימות
- 🔢 Rate limiting של API calls
- 🤝 בקשות מקבילות ואבטחה
- 🕵️ מניעת חשיפת מידע רגיש

### `test_full_integration.py` - טסט אינטגרציה מלא
- 🎮 מסע משתמש מלא מהתחלה ועד הסוף
- 👥 מספר משתמשים במקביל
- 💪 בדיקת עמידות המערכת
- 📊 עקביות נתונים
- 🚨 התאוששות משגיאות
- 🎯 סימולציה של משחק חידות שלם (20 שאלות)

## הרצת הטסטים:

### הרצת כל הטסטים:
```bash
cd quiz-app/tests
python3 run_tests.py
```

### הרצת טסטים ספציפיים:
```bash
# טסטי אימות בלבד
python3 run_tests.py auth

# טסטי API בלבד
python3 run_tests.py api

# טסטים בסיסיים בלבד
python3 run_tests.py basic

# טסטי אבטחה בלבד
python3 run_tests.py security

# טסטים מתקדמים חדשים:
python3 run_tests.py nginx           # nginx integration
python3 run_tests.py advanced_api    # API מתקדם
python3 run_tests.py sessions        # session management
python3 run_tests.py advanced_security  # אבטחה מתקדמת
python3 run_tests.py integration     # טסט אינטגרציה מלא

# טסט ספציפי
python3 -m unittest test_auth.TestAuthentication.test_successful_login_admin
```

### הרצה עם pytest (מומלץ לטסטים החדשים):
```bash
# כל הטסטים החדשים
pytest test_nginx_integration.py -v
pytest test_advanced_api.py -v
pytest test_session_management.py -v
pytest test_advanced_security.py -v -s
pytest test_full_integration.py -v -s

# כל הטסטים
pytest . -v
```

### הרצה ישירה:
```bash
python3 test_auth.py
python3 test_api.py
python3 test_nginx_integration.py
python3 test_advanced_api.py
python3 test_session_management.py
python3 test_advanced_security.py
python3 test_full_integration.py
```

## דרישות:
- האפליקציה צריכה לרוץ על http://localhost
- כל השירותים (nginx, auth-service, quiz-app) צריכים להיות פעילים
- המשתמשים admin/admin123, user1/pass123, demo/demo456 צריכים להיות מוגדרים

## התקנת תלויות:
```bash
pip3 install -r requirements.txt
```

## הערות:
- הטסטים משתמשים ב-requests library לבדיקות HTTP
- כל טסט מתחיל ב-session נקי
- הטסטים בודקים גם תרחישי error וגם happy path
- יש בדיקות לאבטחה ולטיפול בשגיאות