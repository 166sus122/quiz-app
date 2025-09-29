FROM python:3.11-slim

WORKDIR /app

# התקנת תלויות
RUN pip install --no-cache-dir flask flask-session

# העתקת קבצי האפליקציה
COPY app.py .
COPY templates/ templates/
COPY users.db .

EXPOSE 5001

CMD ["python", "app.py"]