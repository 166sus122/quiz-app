from flask import Flask, request, render_template, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import secrets
from datetime import timedelta

app = Flask(__name__)
# שימוש בsecret key קבוע כדי שכל השירותים יוכלו לקרוא את אותם sessions
app.secret_key = 'shared-secret-key-between-services-change-in-production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_DOMAIN'] = 'localhost'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

DB_PATH = 'users.db'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    hashed_pass = hash_password(password)
    cursor.execute('SELECT username FROM users WHERE username = ? AND password = ?', 
                   (username, hashed_pass))
    user = cursor.fetchone()
    conn.close()
    
    return user is not None

@app.route('/login', methods=['GET'])
def login_page():
    if 'username' in session:
        return redirect('/quiz')
    return render_template('login.html', error=None)

@app.route('/auth', methods=['POST'])
def authenticate():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        return render_template('login.html', error='אנא מלא את כל השדות'), 400
    
    if verify_user(username, password):
        session.permanent = True
        session['username'] = username
        return redirect('/quiz')
    else:
        return render_template('login.html', error='שם משתמש או סיסמה שגויים'), 401

@app.route('/verify', methods=['GET'])
def verify_session():
    if 'username' in session:
        return jsonify({'authenticated': True, 'username': session['username']}), 200
    return jsonify({'authenticated': False}), 401

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)