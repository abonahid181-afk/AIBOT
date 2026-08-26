from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-super-secret-key-change-this'

# ----------------- ডেটাবেস সেটআপ -----------------
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deployments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  bot_name TEXT,
                  bot_username TEXT,
                  telegram_key TEXT,
                  gemini_key TEXT,
                  render_key TEXT,
                  status TEXT DEFAULT 'active',
                  deployed_at TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

@app.route('/')
def index():
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        return render_template('index.html', logged_in=True, user=user)
    return render_template('index.html', logged_in=False)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if get_user(username):
        return jsonify({'success': False, 'msg': 'ইউজারনাম আগে থেকেই আছে!'})
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
              (username, hash_password(password), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'msg': 'রেজিস্ট্রেশন সফল! লগইন করুন।'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = get_user(username)
    if user and user[2] == hash_password(password):
        session['user_id'] = user[0]
        session['username'] = user[1]
        return jsonify({'success': True, 'msg': 'লগইন সফল!'})
    return jsonify({'success': False, 'msg': 'ভুল ইউজারনেম বা পাসওয়ার্ড!'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/deploy', methods=['POST'])
def deploy():
    if 'user_id' not in session:
        return jsonify({'success': False, 'msg': 'প্লিজ লগইন করুন!'})
    data = request.get_json()
    bot_name = data.get('name')
    bot_username = data.get('username')
    telegram_key = data.get('telegram_key')
    gemini_key = data.get('gemini_key')
    render_key = data.get('render_key')
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("""INSERT INTO deployments 
                 (user_id, bot_name, bot_username, telegram_key, gemini_key, render_key, status, deployed_at) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (session['user_id'], bot_name, bot_username, telegram_key, gemini_key, render_key, 'active', datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'msg': f'🎉 {bot_name} বট ফ্রিতে সফলভাবে ডিপ্লয় হয়েছে!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
