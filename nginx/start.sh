#!/bin/bash

# הפעלת rsyslog (לניהול לוגים)
rsyslogd

# יצירת קובץ לוג אם לא קיים
touch /var/log/nginx/access.log
touch /var/log/nginx/error.log

# הפעלת fail2ban
echo "Starting Fail2Ban..."
fail2ban-server -xf start > /dev/null 2>&1 &

# המתנה קצרה לאתחול fail2ban
sleep 2

# הצגת סטטוס fail2ban
echo "Fail2Ban status:"
fail2ban-client status

# הפעלת nginx בחזית (foreground)
echo "Starting Nginx..."
nginx -g 'daemon off;'