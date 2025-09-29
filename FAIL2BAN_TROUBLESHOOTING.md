# מדריך פתרון בעיות Fail2Ban - אפליקציית החידות

## 📖 רקע כללי

Fail2Ban הוא כלי אבטחה שמנטר קבצי לוג ובאופן אוטומטי חוסם כתובות IP שמבצעות פעילות חשודה (כמו ניסיונות התחברות כושלים רצופים). באפליקציית החידות שלנו, Fail2Ban אמור לנטר את לוגי nginx ולחסום IP שמנסים התקפות brute force על endpoint ההתחברות.

## 🚨 הבעיות העיקריות שהתגלו

### 1. **בעיית הפרדת השירותים**
**הבעיה:** במתכונת המקורית, nginx ו-Fail2Ban היו באותו קונטיינר, מה שגרם ל:
- קרשי המערכת בזמן הפעלה
- תלויות מורכבות בין השירותים
- קושי בדיבוג ובניטור

**הפתרון:** הפרדנו את השירותים:
```yaml
# docker-compose.yml
nginx:
  build:
    context: ./nginx
  volumes:
    - nginx_logs:/var/log/nginx

fail2ban:
  build:
    context: ./fail2ban
  privileged: true
  volumes:
    - nginx_logs:/var/log/nginx:ro  # גישת קריאה בלבד
```

### 2. **בעיית גישה לקבצי הלוג**
**הבעיה:** Fail2Ban לא הצליח לקרוא את קבצי הלוג של nginx כי:
- nginx יצר symbolic links במקום קבצים אמיתיים
- הרשאות לא היו מוגדרות נכון
- volumes לא היו משותפים

**הפתרון:** שינינו את אופן יצירת הלוגים ב-nginx:

```bash
# nginx/start-nginx.sh
#!/bin/sh

# יצירת קבצי לוג אמיתיים במקום symbolic links
rm -f /var/log/nginx/access.log /var/log/nginx/error.log
touch /var/log/nginx/access.log /var/log/nginx/error.log
chown nginx:nginx /var/log/nginx/*.log

# הפעלת nginx
exec nginx -g 'daemon off;'
```

### 3. **בעיות הרשאות קונטיינר**
**הבעיה:** Fail2Ban לא הצליח לבצע פעולות iptables כי:
- לא היו הרשאות מתאימות לקונטיינר
- חסרו capabilities נדרשים

**הפתרון:** הוספנו הרשאות privileged ו-capabilities:

```yaml
fail2ban:
  privileged: true
  cap_add:
    - NET_ADMIN
    - NET_RAW
    - SYS_ADMIN
```

### 4. **בעיות ניהול תהליכים**
**הבעיה:** Fail2Ban השאיר תהליכים מתים וקבצי PID שגרמו לכשלים בהפעלה מחדש.

**הפתרון:** יצרנו סקריפט הפעלה מקיף:

```bash
# fail2ban/start-fail2ban.sh
#!/bin/bash

echo "Cleaning up any existing Fail2Ban processes..."
pkill -f fail2ban-server || true
rm -f /run/fail2ban/fail2ban.sock /run/fail2ban/fail2ban.pid

echo "Starting Fail2Ban server..."
fail2ban-server -xf -s /run/fail2ban/fail2ban.sock -p /run/fail2ban/fail2ban.pid &
sleep 3

# ווידוא שהשרת פעיל
if fail2ban-client -s /run/fail2ban/fail2ban.sock ping | grep -q "pong"; then
    echo "✅ Fail2Ban is running successfully!"
    fail2ban-client -s /run/fail2ban/fail2ban.sock status
else
    echo "❌ Failed to start Fail2Ban properly"
    exit 1
fi

# לולאת ניטור
while true; do
    if ! fail2ban-client -s /run/fail2ban/fail2ban.sock ping >/dev/null 2>&1; then
        echo "⚠️  Fail2Ban server stopped, restarting..."
        pkill -f fail2ban-server || true
        sleep 2
        fail2ban-server -xf -s /run/fail2ban/fail2ban.sock -p /run/fail2ban/fail2ban.pid &
        sleep 3
    else
        echo "🔒 Fail2Ban is running normally"
    fi
    sleep 30
done
```

### 5. **בעיית קונפיגורציה של jail**
**הבעיה:** ההגדרות לא היו מותאמות נכון לסביבת הפיתוח.

**הפתרון:** התאמנו את jail.local:

```ini
# fail2ban/jail.local
[DEFAULT]
# זמן חסימה - 5 דקות (קצר לסביבת פיתוח)
bantime = 300

# חלון זמן לספירת ניסיונות - 2 דקות
findtime = 120

# מספר ניסיונות כושלים לפני חסימה
maxretry = 3

# פעולת חסימה
banaction = iptables-multiport

# רשימה לבנה של IP שלא לחסום (כולל gateway של Docker)
ignoreip = 127.0.0.1/8 ::1 172.19.0.1

[nginx-auth]
enabled = true
port = http,https
filter = nginx-auth
logpath = /var/log/nginx/access.log
maxretry = 3
findtime = 120
bantime = 300
```

### 6. **בעיית חסימת המפתח עצמו**
**הבעיה:** Fail2Ban חסם את IP של המפתח עצמו במהלך הבדיקות.

**זיהוי הבעיה:**
```bash
docker exec quiz-fail2ban fail2ban-client status nginx-auth
# Status for the jail: nginx-auth
# |- Currently banned: 1
# `- Banned IP list: 172.19.0.1
```

**הפתרון:**
```bash
# ביטול חסימה
docker exec quiz-fail2ban fail2ban-client set nginx-auth unbanip 172.19.0.1

# הוספה לרשימה הלבנה
ignoreip = 127.0.0.1/8 ::1 172.19.0.1
```

### 7. **בעיית שיתוף Session בין השירותים**
**הבעיה הקריטית ביותר:** למרות שFail2Ban עבד, המשתמשים לא הצליחו להתחבר בגלל:
- auth-service יצר secret key רנדומלי
- quiz-app השתמש בsecret key קבוע
- Flask לא הצליח לפענח sessions בין השירותים

**תסמינים:**
- ההתחברות הצליחה (302 redirect)
- דף החידות נטען
- API calls החזירו 401 Unauthorized

**הפתרון הסופי:**
```python
# auth-service/app.py וגם quiz-app/app.py
app.secret_key = 'shared-secret-key-between-services-change-in-production'
```

## 🔧 פקודות דיבוג שימושיות

### בדיקת סטטוס Fail2Ban:
```bash
# סטטוס כללי
docker exec quiz-fail2ban fail2ban-client status

# סטטוס jail ספציפי
docker exec quiz-fail2ban fail2ban-client status nginx-auth

# רשימת IP חסומים
docker exec quiz-fail2ban fail2ban-client get nginx-auth banip

# ביטול חסימת IP
docker exec quiz-fail2ban fail2ban-client set nginx-auth unbanip <IP>
```

### בדיקת לוגים:
```bash
# לוגי nginx
docker exec quiz-nginx tail -f /var/log/nginx/access.log

# לוגי fail2ban
docker-compose logs -f fail2ban

# לוגי auth service
docker-compose logs -f auth-service
```

### בדיקת iptables:
```bash
# כללי iptables
docker exec quiz-fail2ban iptables -L -n

# כללים ספציפיים לfail2ban
docker exec quiz-fail2ban iptables -L f2b-nginx-auth -n
```

## 🧪 בדיקות פונקציונליות

### בדיקת זרימת התחברות:
```bash
# התחברות תקינה
curl -c /tmp/test.txt -X POST -d "username=admin&password=admin123" http://localhost/auth

# בדיקת session
curl -b /tmp/test.txt http://localhost/verify

# בדיקת API
curl -b /tmp/test.txt http://localhost/api/question
```

### בדיקת fail2ban:
```bash
# ניסיונות כושלים רצופים
for i in {1..5}; do
  curl -X POST -d "username=hacker&password=wrong$i" http://localhost/auth
  sleep 1
done

# בדיקה שIP נחסם
docker exec quiz-fail2ban fail2ban-client status nginx-auth
```

## 📝 לקחים נלמדים

### 1. **חשיבות הפרדת שירותים**
- כל שירות בקונטיינר נפרד
- volumes משותפים לשיתוף נתונים
- הגדרות רשת נכונות

### 2. **ניהול הרשאות בקונטיינרים**
- privileged mode לפעולות מערכת
- capabilities ספציפיים במקום privileged מלא
- volumes עם הרשאות קריאה/כתיבה מתאימות

### 3. **ניהול logs**
- קבצים אמיתיים במקום symbolic links
- הרשאות נכונות
- volumes משותפים

### 4. **Secret management**
- שיתוף secret keys בין microservices
- מניעת randomization בסביבת פיתוח
- תיעוד מפורש של dependencies

### 5. **ניטור ודיבוג**
- לוגים מפורטים
- פקודות בדיקה
- תהליכי restart מוגדרים היטב

## 🚀 המלצות לייצור

### אבטחה:
- השתמש בsecret keys חזקים ומוצפנים
- הגדר bantime ארוך יותר (24 שעות)
- הוסף ניטור והתראות על חסימות

### ביצועים:
- השתמש בlog rotation
- הגדר resource limits לקונטיינרים
- הוסף health checks

### תחזוקה:
- סקריפטים לניקוי logs
- בקרת גרסאות לקונפיגורציות
- backup של הגדרות fail2ban

## 🔗 קישורים שימושיים

- [תיעוד Fail2Ban](https://www.fail2ban.org/wiki/index.php/Main_Page)
- [Docker networking](https://docs.docker.com/network/)
- [Flask session management](https://flask.palletsprojects.com/en/2.3.x/quickstart/#sessions)
- [Nginx reverse proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)

---

**סיכום:** הבעיות היו מורכבות ורב-שכבתיות, החל מבעיות תשתית (הרשאות, לוגים) ועד לבעיות אפליקטיביות (session sharing). הפתרון דרש גישה שיטתית ובדיקה שלב אחר שלב של כל רכיב במערכת.