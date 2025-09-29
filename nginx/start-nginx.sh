#!/bin/sh

# יצירת קבצי לוג אמיתיים
rm -f /var/log/nginx/access.log /var/log/nginx/error.log
touch /var/log/nginx/access.log /var/log/nginx/error.log
chown nginx:nginx /var/log/nginx/*.log

# הפעלת nginx בדמון off
exec nginx -g 'daemon off;'