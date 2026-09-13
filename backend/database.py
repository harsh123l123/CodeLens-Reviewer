import sqlite3
import json
import time
try:
    from .config import DB_PATH
except ImportError:
    from config import DB_PATH

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id TEXT PRIMARY KEY,
        created_at REAL,
        language TEXT,
        title TEXT,
        code TEXT,
        score INTEGER,
        grade TEXT,
        metrics_json TEXT,
        summary TEXT,
        issues_json TEXT,
        improved_code TEXT,
        test_cases_json TEXT,
        is_bookmarked INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

def save_review(review_dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    review_id = review_dict.get("id") or f"rev_{int(time.time()*1000)}"
    created_at = review_dict.get("created_at", time.time())
    language = review_dict.get("language", "plaintext")
    title = review_dict.get("title", f"Review - {language.capitalize()}")
    code = review_dict.get("code", "")
    score = int(review_dict.get("score", 0))
    grade = review_dict.get("grade", "N/A")
    summary = review_dict.get("summary", "")
    metrics_json = json.dumps(review_dict.get("metrics", {}))
    issues_json = json.dumps(review_dict.get("issues", []))
    improved_code = review_dict.get("improved_code", "")
    test_cases_json = json.dumps(review_dict.get("test_cases", []))
    
    cursor.execute("""
        INSERT OR REPLACE INTO reviews 
        (id, created_at, language, title, code, score, grade, metrics_json, summary, issues_json, improved_code, test_cases_json, is_bookmarked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        review_id, created_at, language, title, code, score, grade,
        metrics_json, summary, issues_json, improved_code, test_cases_json
    ))
    conn.commit()
    conn.close()
    return review_id

def get_reviews(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, created_at, language, title, score, grade, summary, is_bookmarked,
               length(code) as code_len, length(issues_json) as issues_len
        FROM reviews
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_review_by_id(review_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["metrics"] = json.loads(data["metrics_json"]) if data["metrics_json"] else {}
    data["issues"] = json.loads(data["issues_json"]) if data["issues_json"] else []
    data["test_cases"] = json.loads(data["test_cases_json"]) if data["test_cases_json"] else []
    return data

def delete_review(review_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def toggle_bookmark(review_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reviews SET is_bookmarked = 1 - is_bookmarked WHERE id = ?", (review_id,))
    conn.commit()
    cursor.execute("SELECT is_bookmarked FROM reviews WHERE id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row else False
