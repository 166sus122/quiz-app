# 🚀 CI/CD Pipeline - אפליקציית החידות

## 📋 סקירה כללית

Pipeline CI/CD מלא שמבצע בניה, בדיקות ופריסה אוטומטית של אפליקציית החידות ל-Docker Hub ולשרת הייצור.

## 🏗️ ארכיטקטורת ה-Pipeline

### 1. **Test Stage** 🧪
- הפעלת בדיקות Python
- בניית הקונטיינרים מקומית
- הרצת בדיקות אינטגרציה
- אימות שהשירותים עובדים

### 2. **Build & Push Stage** 📦
- בניית 4 Docker images:
  - `dov121212/quiz-app-nginx`
  - `dov121212/quiz-app-auth-service`
  - `dov121212/quiz-app-quiz-app`
  - `dov121212/quiz-app-fail2ban`
- Push ל-Docker Hub עם tags מתאימים
- תמיכה ב-multi-platform (AMD64 + ARM64)

### 3. **Deploy Stage** 🌐
- פריסה אוטומטית לשרת הייצור
- עדכון docker-compose.prod.yml
- גיבוי אוטומטי של קונפיגורציה ישנה
- בדיקת health לאחר פריסה

### 4. **Smoke Tests** ✅
- בדיקות בסיסיות לאחר פריסה
- אימות זמינות האתר
- בדיקת תגובת API

### 5. **Notifications** 📢
- התראות על הצלחה/כישלון
- ניתן להוסיף Slack/Discord/Email

## 🔧 הגדרת Repository Secrets

צריך להגדיר ב-GitHub Repository Settings → Secrets את הערכים הבאים:

| Secret Name | תיאור | דוגמה |
|-------------|--------|--------|
| `DOCKER_USERNAME` | שם משתמש Docker Hub | `dov121212` |
| `DOCKER_PASSWORD` | סיסמה/Token של Docker Hub | `dckr_pat_xxxxx` |
| `SERVER_HOST` | כתובת שרת הייצור | `123.456.789.10` |
| `SERVER_USER` | שם משתמש לשרת | `ubuntu` |
| `SERVER_PASSWORD` | סיסמה לשרת | `your-password` |

### יצירת Docker Hub Token (מומלץ):
1. התחבר ל-Docker Hub
2. Account Settings → Security → New Access Token
3. שמור את הtoken ב-`DOCKER_PASSWORD`

## 🎯 Triggers (מה מפעיל את ה-Pipeline)

| Event | ענפים | פעולה |
|-------|--------|-------|
| `push` | `main`, `develop` | בדיקות + בניה + פריסה (main בלבד) |
| `pull_request` | `main` | בדיקות בלבד |
| `workflow_dispatch` | כל ענף | הפעלה ידנית |

## 📁 מבנה הקבצים

```
quiz-app/
├── .github/workflows/
│   └── ci-cd.yml                 # ה-Pipeline הראשי
├── docker-compose.yml           # סביבת פיתוח
├── docker-compose.prod.yml      # סביבת ייצור
├── scripts/
│   └── deploy-local.sh          # סקריפט פריסה מקומית
└── CI-CD-README.md              # המדריך הזה
```

## 🚀 שימוש בPipeline

### הפעלה אוטומטית:
```bash
# Push לmain - יפעיל pipeline מלא
git add .
git commit -m "Update application"
git push origin main

# Push לdevelop - יפעיל בדיקות ובניה
git push origin develop

# Pull Request - יפעיל בדיקות בלבד
gh pr create --title "Feature update"
```

### הפעלה ידנית:
1. GitHub → Actions → CI/CD Pipeline
2. Run workflow → בחר ענף → Run

## 🧪 בדיקות מקומיות

לפני push, ניתן לבדוק מקומית:

```bash
# הרשאות לסקריפט
chmod +x scripts/deploy-local.sh

# פריסה מקומית מלאה
./scripts/deploy-local.sh deploy

# רק בניה
./scripts/deploy-local.sh build

# רק בדיקות
./scripts/deploy-local.sh test

# צפייה בסטטוס
./scripts/deploy-local.sh status

# ניקוי
./scripts/deploy-local.sh cleanup
```

## 📊 ניטור ו-Logs

### GitHub Actions Logs:
- Actions tab ב-repository
- לחץ על run ספציפי
- בחר job לראות לוגים מפורטים

### שרת הייצור:
```bash
# SSH לשרת
ssh user@your-server

# צפייה בלוגים
cd ~/quiz-app-production
docker-compose -f docker-compose.prod.yml logs -f

# סטטוס שירותים
docker-compose -f docker-compose.prod.yml ps

# בדיקת health
curl http://localhost/login
```

## 🔒 אבטחה

### Docker Hub:
- שימוש ב-Access Tokens במקום סיסמאות
- הגבלת הרשאות token לrepository ספציפי
- סיבוב tokens תקופתי

### שרת הייצור:
- SSH keys מומלצות על פני סיסמאות
- גיבוי אוטומטי של קונפיגורציות
- ניטור גישות והתחברויות

### Secrets Management:
- אל תשמור secrets בקוד
- השתמש ב-GitHub Secrets בלבד
- בדוק שSecrets לא נחשפים בלוגים

## 🛠️ פתרון בעיות נפוצות

### ❌ Build נכשל:
1. בדוק שכל הDockerfiles תקינים
2. וודא שגישה ל-Docker Hub פעילה
3. בדוק שאין syntax errors בקוד

### ❌ Tests נכשלים:
1. הרץ בדיקות מקומית: `./scripts/deploy-local.sh test`
2. בדוק שכל השירותים מתחילים נכון
3. וודא שPortים לא תפוסים

### ❌ Deployment נכשל:
1. בדוק חיבור SSH לשרת
2. וודא שDocker מותקן בשרת
3. בדוק שיש מקום דיסק פנוי
4. בדוק לוגי השרת: `docker-compose logs`

### ❌ שירותים לא עולים:
1. בדוק שPorts לא תפוסים
2. בדוק הרשאות volumes
3. וודא שnetwork מוגדר נכון
4. בדוק משאבי המערכת (RAM/CPU)

## 📈 שיפורים עתידיים

### מומלץ להוסיף:
- [ ] בדיקות אבטחה אוטומטיות
- [ ] Vulnerability scanning של images
- [ ] Performance testing
- [ ] Database migrations
- [ ] Blue-Green deployment
- [ ] Rollback אוטומטי
- [ ] התראות Slack/Discord
- [ ] Monitoring עם Prometheus/Grafana

### סביבות נוספות:
- [ ] Staging environment
- [ ] Load testing environment
- [ ] Development preview branches

## 🔄 Rollback Process

במקרה של בעיה בprod:

```bash
# SSH לשרת
ssh user@your-server
cd ~/quiz-app-production

# חזרה לגרסה קודמת
docker-compose -f docker-compose.prod.yml.backup.YYYYMMDD_HHMMSS up -d

# או יעצור הכל וישחזר מגיבוי
docker-compose -f docker-compose.prod.yml down
cp docker-compose.prod.yml.backup.YYYYMMDD_HHMMSS docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d
```

## 📞 תמיכה

- **Issues**: GitHub Issues
- **Docs**: README.md של הפרויקט
- **Logs**: GitHub Actions logs
- **שרת**: לוגי docker-compose

---

**📝 הערה**: Pipeline זה מותאם לפרויקט אפליקציית החידות. להתאמה לפרויקטים אחרים, יש לעדכן את שמות הservices וההגדרות בהתאם.