from config import DB_PATH
import sqlite3

def init_db():
    # 캐시용 테이블 초기화 (없으면 생성)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # message를 키로 하는 단순한 캐시 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cache (
        message TEXT PRIMARY KEY,
        response TEXT
    )
    """)
    conn.commit()
    conn.close()

def get_cached_response(message: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT response FROM cache WHERE message = ?", (message,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def save_cached_response(message: str, response: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # 이미 키가 존재하면 REPLACE 가능, 아니면 INSERT
    cur.execute("REPLACE INTO cache (message, response) VALUES (?, ?)", (message, response))
    conn.commit()
    conn.close()