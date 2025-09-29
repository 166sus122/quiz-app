FROM python:3.11-slim

WORKDIR /app

# התקנת תלויות
RUN pip install --no-cache-dir flask requests

# העתקת קבצי האפליקציה
COPY app.py .
COPY templates/ templates/
COPY questions.json .

EXPOSE 5002

CMD ["python", "app.py"]