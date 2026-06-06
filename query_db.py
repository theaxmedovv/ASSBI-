"""
query_db.py — Standalone DB query helper
Run this any time to inspect counts. 
Also shows the exact SQL queries your chatbot should use.
"""

import sqlite3
from datetime import datetime

DB_PATH = "car_counts.db"


def connect():
    return sqlite3.connect(DB_PATH)


# ── Queries ────────────────────────────────────────────────

def total_counts():
    conn = connect()
    row = conn.execute("SELECT total_right, total_left FROM summary WHERE id=1").fetchone()
    conn.close()
    return {"right": row[0], "left": row[1]} if row else {}


def counts_last_n_hours(hours: float):
    conn = connect()
    rows = conn.execute("""
        SELECT direction, COUNT(*) as cnt
        FROM car_events
        WHERE timestamp >= datetime('now', 'localtime', ? )
        GROUP BY direction
    """, (f"-{hours} hours",)).fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def counts_by_class():
    conn = connect()
    rows = conn.execute("""
        SELECT class, direction, COUNT(*) as cnt
        FROM car_events
        GROUP BY class, direction
        ORDER BY class, direction
    """).fetchall()
    conn.close()
    return rows


def recent_events(limit: int = 20):
    conn = connect()
    rows = conn.execute("""
        SELECT id, track_id, direction, class, timestamp
        FROM car_events
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def counts_per_hour():
    conn = connect()
    rows = conn.execute("""
        SELECT strftime('%Y-%m-%d %H:00', timestamp) as hour,
               direction,
               COUNT(*) as cnt
        FROM car_events
        GROUP BY hour, direction
        ORDER BY hour DESC
        LIMIT 48
    """).fetchall()
    conn.close()
    return rows


# ── Pretty print ───────────────────────────────────────────

def print_report():
    print("\n" + "=" * 55)
    print("  CAR COUNTER — DATABASE REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    totals = total_counts()
    print(f"\n📊 TOTAL COUNTS (all time)")
    print(f"   → RIGHT : {totals.get('right', 0)}")
    print(f"   ← LEFT  : {totals.get('left',  0)}")
    print(f"   TOTAL   : {totals.get('right',0) + totals.get('left',0)}")

    for h in [1, 2, 6, 24]:
        counts = counts_last_n_hours(h)
        r = counts.get('right', 0)
        l = counts.get('left', 0)
        print(f"\n⏱  LAST {h:2d} HOUR(S)")
        print(f"   → RIGHT : {r}")
        print(f"   ← LEFT  : {l}")
        print(f"   TOTAL   : {r + l}")

    print(f"\n🚗 COUNTS BY VEHICLE CLASS")
    rows = counts_by_class()
    if rows:
        for cls, direction, cnt in rows:
            arrow = "->" if direction == "right" else "<-"
            print(f"   {cls:<12} {arrow} {direction:<6} : {cnt}")
    else:
        print("   (no data yet)")

    print(f"\n📋 LAST 10 EVENTS")
    events = recent_events(10)
    if events:
        print(f"   {'ID':<5} {'TrackID':<8} {'DIR':<6} {'CLASS':<12} {'TIMESTAMP'}")
        print("   " + "-" * 52)
        for eid, tid, direction, cls, ts in events:
            arrow = "->" if direction == "right" else "<-"
            print(f"   {eid:<5} {tid:<8} {arrow:<6} {cls:<12} {ts}")
    else:
        print("   (no events yet)")

    print(f"\n📅 HOURLY BREAKDOWN (last 24h)")
    hourly = counts_per_hour()
    if hourly:
        seen_hours = {}
        for hour, direction, cnt in hourly:
            if hour not in seen_hours:
                seen_hours[hour] = {'right': 0, 'left': 0}
            seen_hours[hour][direction] = cnt
        for hour, d in list(seen_hours.items())[:24]:
            print(f"   {hour}  → {d.get('right',0):>4}  ← {d.get('left',0):>4}")
    else:
        print("   (no data yet)")

    print("=" * 55 + "\n")


if __name__ == "__main__":
    print_report()