# 🚗 ASSBI - Automated Traffic Counter

**Real-time vehicle detection and directional counting from YouTube Live streams**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![YOLOv11](https://img.shields.io/badge/YOLO-v11n-green)](https://github.com/ultralytics/ultralytics)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue)](https://www.sqlite.org/)

## Overview

ASSBI is an intelligent traffic monitoring system that:

- 🎯 **Detects vehicles** using YOLOv11n with real-time tracking (ByteTrack)
- 📺 **Streams from YouTube** live feeds for continuous monitoring
- 📊 **Counts directional traffic** (left/right) with automatic line detection
- 💾 **Logs to SQLite** for historical analysis and reporting
- 🤖 **Provides SQL queries** for chatbot integration

Perfect for traffic analysis, road safety studies, or automated traffic management systems.

---

## ✨ Features

- **Real-time Detection**: Process video frames at configurable intervals
- **Directional Counting**: Automatic detection of vehicle direction crossing a virtual line
- **Multi-class Support**: Detects cars, trucks, buses, motorcycles, and more
- **Smart Deduplication**: Prevents double-counting using ByteTrack IDs
- **Persistent Storage**: SQLite database for long-term analysis
- **Auto-reconnection**: Handles stream interruptions gracefully
- **Easy Calibration**: Visual helper tool to set the counting line position
- **Query Ready**: Pre-built SQL queries for common traffic metrics

---

## 📋 Prerequisites

- Python 3.8 or higher
- YouTube cookies file for stream access (optional, but recommended)
- Webcam or YouTube Live stream URL
- ~2GB free disk space for model weights and database

---

## 📁 Project Structure

| File               | Purpose                                                               |
| ------------------ | --------------------------------------------------------------------- |
| `main.py`          | Main application — detects, tracks, counts vehicles, logs to database |
| `init_db.py`       | Database initialization (run once to create database schema)          |
| `find_line.py`     | Interactive tool to calibrate the counting line position              |
| `query_db.py`      | Database query utility for generating traffic reports                 |
| `cookies.txt`      | YouTube session cookies (optional, for authenticated access)          |
| `requirements.txt` | Python package dependencies                                           |
| `train/`           | Directory for training-related utilities                              |
| `captures/`        | Directory for saving frame captures                                   |

---

## 🚀 Quick Start

### 1. Installation

Clone the repository and install dependencies:

```bash
cd ASSBI
pip install -r requirements.txt
```

**Optional**: Place your YouTube cookies in `cookies.txt` for better access:

```bash
# Copy your browser cookies into cookies.txt
# Format: Netscape HTTP Cookie File format or simple key=value pairs
```

### 2. Initialize Database

Create the SQLite database schema (run once):

```bash
python init_db.py
```

This creates `car_counts.db` with the following tables:

- `car_events`: Individual vehicle crossing records
- `summary`: Aggregate traffic statistics

### 3. Calibrate Counting Line

Run the line finder to determine the optimal X-axis position for counting:

```bash
python find_line.py
```

**Instructions**:

- Use `←` and `→` arrow keys to adjust the vertical line position
- Press `ENTER` when satisfied with the position
- Copy the printed `LINE_X` value
- Update `LINE_X` in `main.py` with this value

### 4. Run the Counter

Start monitoring traffic:

```bash
python main.py
```

**Controls**:

- Press `q` to quit gracefully
- Press `s` to save the current frame

---

## 📊 Output & Monitoring

### Live Console Output

```
[CROSS] Frame   1523 | ID   12 | car        | ->  RIGHT | RIGHT: 5  LEFT: 2
[CROSS] Frame   1891 | ID   17 | truck      | <-  LEFT  | RIGHT: 5  LEFT: 3
[CROSS] Frame   2105 | ID   23 | bus        | ->  RIGHT | RIGHT: 6  LEFT: 3
```

**Output fields**:

- `Frame`: Current frame number
- `ID`: Unique ByteTrack identifier
- `car/truck/bus/...`: Detected vehicle class
- `->`: Direction of movement (→ right, ← left)
- `RIGHT/LEFT`: Running count for each direction

### Database Query Tool

Generate comprehensive traffic reports:

```bash
python query_db.py
```

Displays:

- Total vehicles by direction
- Vehicle type breakdown
- Hourly traffic trends
- Peak traffic times
- Detection statistics

---

## ⚙️ Configuration

Edit the configuration section at the top of `main.py`:

```python
# ===== CORE SETTINGS =====
LINE_X = 640              # X-coordinate of the counting line (pixels)
FRAME_SKIP = 1            # Process every Nth frame (1 = every frame, 2 = every 2nd, etc.)
CONF = 0.25               # YOLO confidence threshold (0.0-1.0)
IOU = 0.45                # YOLO IOU threshold for NMS

# ===== DISPLAY SETTINGS =====
DISPLAY_W = 1280          # Video window width
DISPLAY_H = 720           # Video window height
SHOW_CONF = True          # Display confidence scores on detections

# ===== STREAM SETTINGS =====
STREAM_URL = "youtube_url_here"  # YouTube Live stream URL or local video path
RECONNECT_INTERVAL = 5    # Seconds between reconnection attempts
```

### Configuration Tips

| Setting       | Purpose                   | Recommendation                                                   |
| ------------- | ------------------------- | ---------------------------------------------------------------- |
| `LINE_X`      | Position of counting line | Use `find_line.py` to calibrate                                  |
| `FRAME_SKIP`  | Process every N frames    | Increase to 2-3 for lower CPU usage                              |
| `CONF`        | Detection confidence      | Lower (0.15-0.2) for better coverage, higher (0.4+) for accuracy |
| `IOU`         | Non-Maximum Suppression   | 0.45 is balanced; increase for fewer overlaps                    |
| `DISPLAY_W/H` | Window resolution         | Match your stream aspect ratio for best results                  |

---

## 🗄️ Database Schema

### `car_events` Table

Records every vehicle crossing event.

| Column       | Type                | Description                                                       |
| ------------ | ------------------- | ----------------------------------------------------------------- |
| `id`         | INTEGER PRIMARY KEY | Auto-incrementing event ID                                        |
| `track_id`   | INTEGER             | YOLO ByteTrack unique ID                                          |
| `direction`  | TEXT                | `'right'` or `'left'`                                             |
| `class`      | TEXT                | Vehicle class (`'car'`, `'truck'`, `'bus'`, `'motorcycle'`, etc.) |
| `confidence` | REAL                | Detection confidence score (0.0-1.0)                              |
| `timestamp`  | DATETIME            | Local timestamp of crossing                                       |

### `summary` Table

Real-time aggregate statistics.

| Column           | Type     | Description                      |
| ---------------- | -------- | -------------------------------- |
| `total_right`    | INTEGER  | Cumulative right-direction count |
| `total_left`     | INTEGER  | Cumulative left-direction count  |
| `total_vehicles` | INTEGER  | Total detections                 |
| `updated_at`     | DATETIME | Last database update time        |

---

## 🤖 Chatbot Integration

Integrate with your chatbot using these pre-built SQL queries:

### Last 2 Hours Traffic

```sql
-- Rightbound vehicles (last 2 hours)
SELECT COUNT(*) as count FROM car_events
WHERE direction = 'right'
AND timestamp >= datetime('now', 'localtime', '-2 hours');

-- Leftbound vehicles (last 2 hours)
SELECT COUNT(*) as count FROM car_events
WHERE direction = 'left'
AND timestamp >= datetime('now', 'localtime', '-2 hours');
```

### Traffic by Vehicle Type

```sql
SELECT class, direction, COUNT(*) as count
FROM car_events
WHERE timestamp >= datetime('now', 'localtime', '-24 hours')
GROUP BY class, direction
ORDER BY count DESC;
```

### Hourly Breakdown

```sql
SELECT
  strftime('%Y-%m-%d %H:00', timestamp) as hour,
  direction,
  COUNT(*) as count
FROM car_events
GROUP BY hour, direction
ORDER BY hour DESC
LIMIT 24;
```

### Peak Traffic Hour

```sql
SELECT
  strftime('%H:00', timestamp) as hour,
  COUNT(*) as total_vehicles
FROM car_events
GROUP BY hour
ORDER BY total_vehicles DESC
LIMIT 5;
```

### Daily Report

```sql
SELECT
  DATE(timestamp) as date,
  SUM(CASE WHEN direction = 'right' THEN 1 ELSE 0 END) as rightbound,
  SUM(CASE WHEN direction = 'left' THEN 1 ELSE 0 END) as leftbound,
  COUNT(*) as total
FROM car_events
GROUP BY date
ORDER BY date DESC;
```

---

## 🐛 Troubleshooting

| Problem                          | Cause                           | Solution                                                  |
| -------------------------------- | ------------------------------- | --------------------------------------------------------- |
| **Stream lag/slow processing**   | Frame rate too high             | Increase `FRAME_SKIP` to 2-3, reduce `DISPLAY_W/H`        |
| **Low vehicle detection**        | Confidence threshold too high   | Lower `CONF` from 0.25 to 0.15-0.20                       |
| **Double counting**              | Vehicle tracked as multiple IDs | This is handled automatically; check `LINE_X` calibration |
| **YouTube stream fails**         | Missing or expired cookies      | Update `cookies.txt` with fresh session cookies           |
| **Frequent disconnections**      | Network issues                  | Increase `RECONNECT_INTERVAL`, check internet stability   |
| **High CPU/GPU usage**           | Processing too many frames      | Increase `FRAME_SKIP` or reduce detection confidence      |
| **Wrong counting line position** | Manual configuration error      | Run `find_line.py` again to recalibrate                   |
| **Database locked**              | Multiple processes accessing DB | Ensure only one instance of `main.py` is running          |

---

## 📈 Performance Benchmarks

| Metric       | Value       | Notes                                |
| ------------ | ----------- | ------------------------------------ |
| FPS          | 20-30       | Depends on `FRAME_SKIP` and hardware |
| Model Size   | 46 MB       | YOLOv11n is lightweight              |
| Memory Usage | 800-1200 MB | GPU: 1-2 GB if available             |
| CPU Usage    | 40-60%      | Single-threaded processing           |

---

## 🔄 Workflow Example

1. **First Time Setup** (5 minutes):

   ```bash
   pip install -r requirements.txt
   python init_db.py
   python find_line.py  # Calibrate and note LINE_X value
   # Edit main.py: set LINE_X = <your_value>
   ```

2. **Daily Monitoring**:

   ```bash
   python main.py  # Run and let it monitor traffic
   ```

3. **Generate Reports**:

   ```bash
   python query_db.py  # View daily/hourly statistics
   ```

4. **Analyze Data**:
   - Query the SQLite database with custom SQL
   - Export results for analysis
   - Feed metrics to your chatbot or dashboard

---

## 🛠️ Advanced Usage

### Custom Detection Classes

Modify the class filter in `main.py` to track specific vehicle types:

```python
TRACKED_CLASSES = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
```

### Batch Processing

Process recorded videos instead of live streams:

```bash
# In main.py, set STREAM_URL to a local file path
STREAM_URL = "traffic_video.mp4"
```

### Export Data

Export traffic data to CSV or JSON:

```bash
sqlite3 car_counts.db "SELECT * FROM car_events" | sed 's/\(.*\)/\1/' > traffic_report.csv
```

---

## 📝 License

This project is provided as-is. Please ensure compliance with YouTube's Terms of Service and local laws regarding traffic monitoring.

---

## 🤝 Contributing

Found a bug or have a feature request?

- Test your issue thoroughly
- Provide detailed reproduction steps
- Include configuration settings and error messages

---

## 📧 Support

For issues or questions:

1. Check the **Troubleshooting** section
2. Review database schema and SQL queries
3. Verify configuration settings in `main.py`

---

## 🎯 Roadmap

Future improvements planned:

- [ ] Web dashboard for live monitoring
- [ ] Email/SMS alerts for traffic anomalies
- [ ] Multi-line counting support
- [ ] Vehicle speed estimation
- [ ] Heat map generation
- [ ] Model fine-tuning on custom datasets

---

**Last Updated**: 2026-06-07 | **Version**: 1.1

