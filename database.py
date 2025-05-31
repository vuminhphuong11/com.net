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
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender) REFERENCES users(username)
        )
    ''') 
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            filename TEXT NOT NULL,
            filetype TEXT,
            filesize INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender) REFERENCES users(username)
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

def save_file_metadata(sender, filename, filetype, filesize, timestamp=None):
    if timestamp is None:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO files (sender, filename, filetype, filesize, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (sender, filename, filetype, filesize, timestamp))
    conn.commit()
    conn.close()

def get_file_history(limit=50):
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        SELECT sender, filename, filetype, filesize, timestamp 
        FROM files 
        ORDER BY id DESC 
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows[::-1]

create_tables()