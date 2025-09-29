import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_database():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    print("✓ טבלת users נוצרה בהצלחה")
    
    demo_users = [
        ('admin', 'admin123'),
        ('user1', 'pass123'),
        ('demo', 'demo456')
    ]
    
    for username, password in demo_users:
        hashed_password = hash_password(password)
        try:
            cursor.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, hashed_password)
            )
            print(f'✓ נוסף משתמש: {username} / {password}')
        except sqlite3.IntegrityError:
            print(f'⚠ משתמש {username} כבר קיים במסד הנתונים')
    
    conn.commit()
    
    print("\n--- משתמשים במערכת ---")
    cursor.execute('SELECT id, username, created_at FROM users')
    users = cursor.fetchall()
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}, Created: {user[2]}")
    
    conn.close()
    
    print("\n✅ מסד הנתונים users.db נוצר בהצלחה!")
    print("📍 מיקום הקובץ: ./users.db")
    print("\n🔐 פרטי התחברות:")
    print("   admin / admin123")
    print("   user1 / pass123")
    print("   demo / demo456")

if __name__ == '__main__':
    create_database()
