# 🚗 Car Direction Counter
**YOLO11n + YouTube Live Stream + SQLite Database**

---

## 📁 Project Files

| File | Purpose |
|------|---------|
| `main.py` | Main script — detects & counts cars, logs to DB |
| `init_db.py` | Creates the `car_counts.db` file (run once) |
| `find_line.py` | Visual helper to find the right `LINE_X` value |
| `query_db.py` | Print DB report (test your chatbot queries) |
| `cookies.txt` | Your YouTube cookies (place here) |
| `requirements.txt` | Python dependencies |

---

## ⚙️ Setup (run once)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create the database
python init_db.py

# 3. Find the right counting line position
python find_line.py
# → Use ← → arrow keys, press ENTER when happy
# → Copy the printed LINE_X value into main.py
```

---

## 🚀 Running

```bash
python main.py
```

**Terminal output looks like:**
```
[CROSS] Frame   1523 | ID   12 | car        | ->  RIGHT | RIGHT: 5  LEFT: 2
[CROSS] Frame   1891 | ID   17 | truck      | <-  LEFT  | RIGHT: 5  LEFT: 3
```

**Press `q`** in the video window to quit cleanly.

---

## 🗄️ Database Schema

### `car_events` — one row per crossing
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto primary key |
| track_id | INTEGER | YOLO ByteTrack ID |
| direction | TEXT | `'right'` or `'left'` |
| class | TEXT | `'car'`, `'truck'`, `'bus'`, `'motorcycle'` |
| timestamp | DATETIME | Local time of crossing |

### `summary` — running totals
| Column | Type | Description |
|--------|------|-------------|
| total_right | INTEGER | All-time rightward count |
| total_left | INTEGER | All-time leftward count |
| updated_at | DATETIME | Last update time |

---

## 🤖 Chatbot SQL Queries

Give these to your chatbot so it can answer questions:

```sql
-- How many cars went right in the last 2 hours?
SELECT COUNT(*) FROM car_events
WHERE direction = 'right'
AND timestamp >= datetime('now', 'localtime', '-2 hours');

-- How many cars went left in the last 2 hours?
SELECT COUNT(*) FROM car_events
WHERE direction = 'left'
AND timestamp >= datetime('now', 'localtime', '-2 hours');

-- Total count by direction (all time)
SELECT direction, COUNT(*) FROM car_events GROUP BY direction;

-- Count by vehicle type
SELECT class, direction, COUNT(*) FROM car_events
GROUP BY class, direction;

-- Hourly breakdown
SELECT strftime('%Y-%m-%d %H:00', timestamp) as hour,
       direction, COUNT(*) as count
FROM car_events
GROUP BY hour, direction
ORDER BY hour DESC;
```

---

## 🔧 Config (top of main.py)

```python
LINE_X      = 640    # X pixel where counting line sits
FRAME_SKIP  = 1      # Process every N frames (increase to save CPU)
DISPLAY_W   = 1280   # Window width
DISPLAY_H   = 720    # Window height
```

---

## 🐛 Common Issues

| Problem | Fix |
|---------|-----|
| Stream lag | Increase `FRAME_SKIP` to 2 or 3 |
| "No cookies" warning | Place `cookies.txt` next to `main.py` |
| Low car detection | Lower `conf=0.25` to `conf=0.15` in `main.py` |
| Double-counting | `counted_ids` set prevents this automatically |
| Stream drops | Script auto-reconnects every 5 seconds |