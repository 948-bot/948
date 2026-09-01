"""
XAUUSD AI DERIV BOT
Database Journaling Module
"""
import sqlite3
import os
from datetime import datetime

DB_NAME = "database/trading_journal.db"

def init_db():
    """
    Inisialisasi tabel database SQLite untuk mencatat riwayat sinyal.
    """
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action TEXT,
            entry REAL,
            tp REAL,
            sl REAL,
            confidence INTEGER,
            reasoning TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_signal_to_db(signal_data: dict, ai_evaluation: dict):
    """
    Menyimpan catatan sinyal dan evaluasi AI ke database.
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO signals (timestamp, action, entry, tp, sl, confidence, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            now,
            ai_evaluation.get("action", "WAIT"),
            signal_data.get("entry", 0.0),
            signal_data.get("tp", 0.0),
            signal_data.get("sl", 0.0),
            ai_evaluation.get("confidence", 0),
            ai_evaluation.get("reasoning", "")
        ))
        
        conn.commit()
        conn.close()
        print("✅ Riwayat sinyal berhasil dicatat ke database journal.")
    except Exception as e:
        print(f"⚠️ Gagal mencatat ke database: {e}")
