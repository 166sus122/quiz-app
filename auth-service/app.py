from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from flask.sessions import SecureCookieSessionInterface
import sqlite3
import hashlib
import secrets
from datetime import timedelta
import os

app = Flask(__name__)
# שימוש בsecret key קבוע כדי שכל השירותים יוכלו לקרוא את אותם sessions
app.secret_key = os.getenv('SESSION_SECRET', 'shared-secret-key-between-services-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Custom session interface that doesn't set domain
class NoDomainSessionInterface(SecureCookieSessionInterface):
    def get_cookie_domain(self, app):
        # Return False to explicitly disable domain attribute
        return False

    def save_session(self, app, session, response):
        # Override to ensure domain is not set
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        name = self.get_cookie_name(app)

        if not session:
            if session.modified:
                response.delete_cookie(
                    name,
                    path=path
                )
            return

        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        samesite = self.get_cookie_samesite(app)
        expires = self.get_expiration_time(app, session)
        val = self.get_signing_serializer(app).dumps(dict(session))

        response.set_cookie(
            name,
            val,
            expires=expires,
            httponly=httponly,
            secure=secure,
            path=path,
            samesite=samesite,
            domain=None  # Explicitly set to None to disable domain attribute
        )

app.session_interface = NoDomainSessionInterface()

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