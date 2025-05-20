import sqlite3
import time

DB_NAME = 'chat.db'

def connect_db():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def check_user(username, password):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return False
    return row[0] == password

def save_message(sender, content, timestamp=None):
    if timestamp is None:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    conn = connect_db()
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, content, timestamp) VALUES (?, ?, ?)", (sender, content, timestamp))
    conn.commit()
    conn.close()

def get_recent_messages(limit=100):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT sender, content, timestamp FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows[::-1]

create_tables()