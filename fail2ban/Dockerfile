FROM alpine:latest

# התקנת fail2ban, iptables ו-rsyslog
RUN apk add --no-cache \
    fail2ban \
    iptables \
    rsyslog \
    bash

# יצירת תיקיות ללוגים
RUN mkdir -p /var/log/nginx /var/log/fail2ban

# יצירת תיקייה לתצורות fail2ban
RUN mkdir -p /etc/fail2ban/filter.d /etc/fail2ban/jail.d

# העתקת תצורות fail2ban
COPY jail.local /etc/fail2ban/jail.local
COPY filter.d/nginx-auth.conf /etc/fail2ban/filter.d/nginx-auth.conf

# סקריפט התחלה
COPY start-fail2ban.sh /start-fail2ban.sh
RUN chmod +x /start-fail2ban.sh

CMD ["/start-fail2ban.sh"]