"""
init_db.py — Run this ONCE before starting main.py
Creates (or resets) car_counts.db with the correct schema.
"""

import sqlite3
import os

DB_PATH = "car_counts.db"

def init_db():
    if os.path.exists(DB_PATH):
        answer = input(f"'{DB_PATH}' already exists. Reset it? (y/n): ").strip().lower()
        if answer != 'y':
            print("Keeping existing database. Exiting.")
            return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop old tables if resetting
    cursor.execute("DROP TABLE IF EXISTS car_events")
    cursor.execute("DROP TABLE IF EXISTS summary")

    # ── car_events: one row per crossing event ──────────────
    cursor.execute("""
        CREATE TABLE car_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id  INTEGER  NOT NULL,
            direction TEXT     NOT NULL,   -- 'right' or 'left'
            class     TEXT     NOT NULL,   -- 'car', 'truck', 'bus', 'motorcycle'
            timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ── summary: running totals ──────────────────────────────
    cursor.execute("""
        CREATE TABLE summary (
            id          INTEGER PRIMARY KEY,
            total_right INTEGER DEFAULT 0,
            total_left  INTEGER DEFAULT 0,
            updated_at  DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    """)
    cursor.execute("INSERT INTO summary (id, total_right, total_left) VALUES (1, 0, 0)")

    conn.commit()
    conn.close()

    print(f"[OK] Database created: {DB_PATH}")
    print("     Tables: car_events, summary")
    print("     Ready to run main.py")


if __name__ == "__main__":
    init_db()