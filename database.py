import sqlite3
import os
import shutil

DB_NAME = 'thyroid_records.db'

def get_db_connection():
    # Agar code Vercel (Linux) par chal raha hai toh /tmp folder use karega
    if os.environ.get('VERCEL') or os.name != 'nt':
        db_path = os.path.join('/tmp', DB_NAME)
        
        # Agar /tmp ke andar file pehle se majood nahi hai toh project directory se copy kar lega
        if not os.path.exists(db_path) and os.path.exists(DB_NAME):
            try:
                shutil.copy(DB_NAME, db_path)
            except Exception as e:
                print(f"Database copy warning: {e}")
    else:
        # Local system (Windows) par wahi regular path chalega
        db_path = DB_NAME

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Patients Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER,
            gender TEXT,
            tsh REAL,
            t3 REAL,
            tt4 REAL,
            t4u REAL,
            fti REAL,
            prediction TEXT,
            confidence REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Users Table for Authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            auth_provider TEXT DEFAULT 'local',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_patient(age, gender, tsh, t3, tt4, t4u, fti, prediction, confidence):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO patients (age, gender, tsh, t3, tt4, t4u, fti, prediction, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (age, gender, tsh, t3, tt4, t4u, fti, prediction, confidence))
    conn.commit()
    conn.close()

def get_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patients ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

# User Authentication Helpers
def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(name, email, password_hash, auth_provider='local'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, auth_provider)
            VALUES (?, ?, ?, ?)
        ''', (name, email, password_hash, auth_provider))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        user_id = None
    finally:
        conn.close()
    return user_id