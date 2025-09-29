from flask import Flask, render_template, jsonify, request, redirect, session
import json
import random
import requests
import os

app = Flask(__name__)
# שימוש באותו secret key כמו ב-auth-service כדי לשתף sessions
app.secret_key = os.getenv('SESSION_SECRET', 'shared-secret-key-between-services-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_PATH'] = '/'

AUTH_SERVICE_URL = 'http://auth-service:5001'
QUESTIONS_FILE = 'questions.json'

@app.after_request
def remove_cookie_domain(response):
    """Remove Domain attribute from session cookie to make it work with both localhost and 127.0.0.1"""
    cookies = response.headers.getlist('Set-Cookie')
    if cookies:
        # Clear all Set-Cookie headers
        del response.headers['Set-Cookie']

        # Add them back with Domain removed
        for cookie in cookies:
            if 'session=' in cookie:
                # Remove all variations of Domain=localhost
                import re
                cookie = re.sub(r'Domain=[^;]+;\s*', '', cookie)
                cookie = re.sub(r';\s*Domain=[^;]+', '', cookie)
            response.headers.add('Set-Cookie', cookie)
    return response

def load_questions():
    with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['questions']

def verify_authentication():
    """בדיקת אימות מול שירות ההתחברות"""
    try:
        # בסביבת Docker, נשתמש בשם השירות
        # בסביבת פיתוח מקומית, אפשר לשנות ל-localhost
        response = requests.get(
            f'{AUTH_SERVICE_URL}/verify',
            cookies=request.cookies,
            timeout=5
        )
        return response.status_code == 200
    except:
        # אם שירות האימות לא זמין, נבדוק session מקומי
        return 'username' in session

@app.route('/')
def index():
    return redirect('/quiz')

@app.route('/quiz')
def quiz_page():
    if not verify_authentication():
        return redirect('http://localhost/login')
    
    if 'score' not in session:
        session['score'] = 0
        session['answered_questions'] = []
    
    return render_template('quiz.html')

@app.route('/api/question', methods=['GET'])
def get_question():
    if not verify_authentication():
        return jsonify({'error': 'לא מאומת', 'redirect': '/login'}), 401
    
    questions = load_questions()
    answered = session.get('answered_questions', [])
    
    # סינון שאלות שכבר נענו
    available_questions = [q for q in questions if q['id'] not in answered]
    
    if not available_questions:
        return jsonify({'error': 'אין יותר שאלות זמינות'}), 404
    
    question = random.choice(available_questions)
    
    # הסרת התשובה הנכונה מהנתונים שנשלחים ללקוח
    question_data = {
        'id': question['id'],
        'type': question['type'],
        'question': question['question'],
        'explanation': question.get('explanation', '')
    }
    
    if question['type'] == 'multiple_choice':
        question_data['options'] = question['options']
        question_data['correct_answer'] = question['correct_answer']
    else:
        question_data['correct_answer'] = question['correct_answer']
    
    return jsonify(question_data)

@app.route('/api/answer', methods=['POST'])
def check_answer():
    if not verify_authentication():
        return jsonify({'error': 'לא מאומת', 'redirect': '/login'}), 401
    
    data = request.get_json()
    question_id = data.get('question_id')
    user_answer = data.get('answer')
    
    questions = load_questions()
    question = next((q for q in questions if q['id'] == question_id), None)
    
    if not question:
        return jsonify({'error': 'שאלה לא נמצאה'}), 404
    
    is_correct = user_answer == question['correct_answer']
    
    # עדכון ניקוד
    if 'score' not in session:
        session['score'] = 0
    
    if 'answered_questions' not in session:
        session['answered_questions'] = []
    
    if is_correct:
        session['score'] += 1
    
    session['answered_questions'].append(question_id)
    session.modified = True
    
    return jsonify({
        'correct': is_correct,
        'score': session['score'],
        'explanation': question.get('explanation', '')
    })

@app.route('/api/score', methods=['GET'])
def get_score():
    if not verify_authentication():
        return jsonify({'error': 'לא מאומת'}), 401
    
    return jsonify({
        'score': session.get('score', 0),
        'answered': len(session.get('answered_questions', []))
    })

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)