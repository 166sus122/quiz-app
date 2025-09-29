#!/bin/bash

# יצירת תיקיות נדרשות
mkdir -p /var/run/fail2ban
mkdir -p /var/log/fail2ban

# הפעלת rsyslog (לניהול לוגים)
rsyslogd -n &

# יצירת קבצי לוג אם לא קיימים
touch /var/log/nginx/access.log
touch /var/log/nginx/error.log

# המתנה לוודא שהקבצים קיימים
sleep 2

# ניקוי fail2ban קודם
echo "Cleaning up any existing Fail2Ban processes..."
pkill -f fail2ban > /dev/null 2>&1 || true
rm -f /var/run/fail2ban/fail2ban.sock
rm -f /var/run/fail2ban/fail2ban.pid

# הפעלת fail2ban ברקע
echo "Starting Fail2Ban server..."
fail2ban-server -b -s /var/run/fail2ban/fail2ban.sock -p /var/run/fail2ban/fail2ban.pid

# המתנה לאתחול
sleep 3

# בדיקת סטטוס
echo "Checking Fail2Ban status..."
if fail2ban-client ping 2>/dev/null; then
    echo "✅ Fail2Ban is running successfully!"
    fail2ban-client status
else
    echo "❌ Fail2Ban failed to start"
    exit 1
fi

echo "🔒 Fail2Ban is monitoring nginx logs for brute force attacks..."

# שמירה על הcontainer פעיל עם מוניטורינג
while true; do
    sleep 30

    # בדיקה שfail2ban עדיין פעיל
    if ! fail2ban-client ping > /dev/null 2>&1; then
        echo "⚠️  Fail2Ban stopped, attempting restart..."

        # ניקוי וריסטארט
        pkill -f fail2ban > /dev/null 2>&1 || true
        rm -f /var/run/fail2ban/fail2ban.sock
        rm -f /var/run/fail2ban/fail2ban.pid

        # הפעלה מחדש
        fail2ban-server -b -s /var/run/fail2ban/fail2ban.sock -p /var/run/fail2ban/fail2ban.pid
        sleep 3

        if fail2ban-client ping > /dev/null 2>&1; then
            echo "✅ Fail2Ban restarted successfully"
        else
            echo "❌ Failed to restart Fail2Ban"
        fi
    else
        echo "🔒 Fail2Ban is running normally"
    fi
done