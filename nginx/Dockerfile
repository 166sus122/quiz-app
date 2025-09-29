FROM nginx:alpine

# יצירת תיקיות ללוגים
RUN mkdir -p /var/log/nginx

# העתקת קובץ תצורה של nginx וסקריפט התחלה
COPY nginx.conf /etc/nginx/nginx.conf
COPY start-nginx.sh /start-nginx.sh

# הגדרת הרשאות לסקריפט
RUN chmod +x /start-nginx.sh

EXPOSE 80

CMD ["/start-nginx.sh"]