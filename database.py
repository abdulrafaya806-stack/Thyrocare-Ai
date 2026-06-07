import sqlite3

def init_db():
    conn = sqlite3.connect('thyroid_records.db')
    cursor = conn.cursor()
    # SQLite mein AUTOINCREMENT standard tareeqa ye hai:
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
    conn.commit()
    conn.close()

def insert_patient(age, gender, tsh, t3, tt4, t4u, fti, prediction, confidence):
    conn = sqlite3.connect('thyroid_records.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO patients (age, gender, tsh, t3, tt4, t4u, fti, prediction, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (age, gender, tsh, t3, tt4, t4u, fti, prediction, confidence))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect('thyroid_records.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patients ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows