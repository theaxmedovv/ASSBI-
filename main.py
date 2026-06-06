import cv2
import sqlite3
import os
import time
from ultralytics import YOLO
import yt_dlp

# ============================================================
#  CONFIG — edit these values before running
# ============================================================
YOUTUBE_URL   = "https://www.youtube.com/live/M3EYAY2MftI?si=TX_LD4OyFsCUEfLS"
VIDEO_FILE    = "test_video.mp4"      # local video file name
USE_LOCAL     = True                  # True = local file | False = YouTube stream

MODEL_PATH    = "yolo11n.pt"
DB_PATH       = "car_counts.db"
COOKIES_FILE  = "cookies.txt"

# LINE_X is in DISPLAY coordinates (what you see on screen)
LINE_X        = 640

CAR_CLASSES   = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

DISPLAY_W     = 1280
DISPLAY_H     = 720
FRAME_SKIP    = 1
# ============================================================

CLR_LINE  = (0, 255, 255)
CLR_RIGHT = (0, 200, 0)
CLR_LEFT  = (0, 100, 255)
CLR_HUD   = (20, 20, 20)
CLR_WHITE = (255, 255, 255)


# ── Database ───────────────────────────────────────────────
def init_db(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS car_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id  INTEGER NOT NULL,
            direction TEXT    NOT NULL,
            class     TEXT    NOT NULL,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS summary (
            id          INTEGER PRIMARY KEY,
            total_right INTEGER DEFAULT 0,
            total_left  INTEGER DEFAULT 0,
            updated_at  DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("INSERT OR IGNORE INTO summary (id, total_right, total_left) VALUES (1, 0, 0)")
    conn.commit()
    return conn


def log_crossing(conn, track_id, direction, cls_name):
    conn.execute(
        "INSERT INTO car_events (track_id, direction, class) VALUES (?, ?, ?)",
        (track_id, direction, cls_name)
    )
    col = "total_right" if direction == "right" else "total_left"
    conn.execute(f"UPDATE summary SET {col} = {col} + 1, updated_at = datetime('now','localtime') WHERE id = 1")
    conn.commit()


def get_summary(conn):
    row = conn.execute("SELECT total_right, total_left FROM summary WHERE id = 1").fetchone()
    return (row[0], row[1]) if row else (0, 0)


# ── Stream URL ─────────────────────────────────────────────
def get_stream_url(youtube_url, cookies):
    ydl_opts = {
        'format': 'best[height<=480][ext=mp4]/best[height<=480]/best',
        'quiet': True,
        'no_warnings': True,
    }
    if cookies and os.path.exists(cookies):
        ydl_opts['cookiefile'] = cookies
        print(f"[yt-dlp] Using cookies: {cookies}")
    else:
        print("[yt-dlp] No cookies file — trying without auth")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info['url']


# ── HUD ────────────────────────────────────────────────────
def draw_hud(frame, right, left, fps, line_x):
    h, w = frame.shape[:2]

    # Counting line drawn on display frame
    cv2.line(frame, (line_x, 0), (line_x, h), CLR_LINE, 2)
    cv2.putText(frame, "COUNT LINE", (line_x + 5, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, CLR_LINE, 1, cv2.LINE_AA)

    cv2.rectangle(frame, (10, 10), (320, 120), CLR_HUD, -1)
    cv2.rectangle(frame, (10, 10), (320, 120), CLR_LINE, 1)
    cv2.putText(frame, f"RIGHT (->): {right}", (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, CLR_RIGHT, 2, cv2.LINE_AA)
    cv2.putText(frame, f"LEFT  (<-): {left}", (20, 85),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, CLR_LEFT,  2, cv2.LINE_AA)
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 112),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, CLR_WHITE, 1, cv2.LINE_AA)


# ── Main ───────────────────────────────────────────────────
def main():
    print("=" * 55)
    mode = "LOCAL FILE" if USE_LOCAL else "YOUTUBE STREAM"
    print(f"  CAR DIRECTION COUNTER  |  {mode}")
    print("=" * 55)

    conn = init_db(DB_PATH)
    print(f"[DB] Connected -> {DB_PATH}")

    print("[YOLO] Loading model ...")
    model = YOLO(MODEL_PATH)
    print("[YOLO] Ready.")

    prev_centers = {}
    counted_ids  = set()
    right_count, left_count = get_summary(conn)
    print(f"[DB] Previous counts -> RIGHT: {right_count} | LEFT: {left_count}\n")

    while True:
        try:
            # ── Open video source ──────────────────────────
            if USE_LOCAL:
                if not os.path.exists(VIDEO_FILE):
                    print(f"[ERROR] File not found: {VIDEO_FILE}")
                    print(f"        Place '{VIDEO_FILE}' next to main.py and restart.")
                    return
                print(f"[SOURCE] Opening local file: {VIDEO_FILE}")
                cap = cv2.VideoCapture(VIDEO_FILE)
            else:
                print("[SOURCE] Fetching YouTube stream URL ...")
                stream_url = get_stream_url(YOUTUBE_URL, COOKIES_FILE)
                print("[SOURCE] Got URL. Opening capture ...")
                cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                raise RuntimeError("Could not open video source.")

            # Get original frame dimensions once
            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"[SOURCE] Frame size: {orig_w}x{orig_h}")

            # LINE_X is in display coords -> convert to original frame coords
            scale_x     = orig_w / DISPLAY_W
            line_x_orig = int(LINE_X * scale_x)
            print(f"[LINE] Display X={LINE_X} -> Original frame X={line_x_orig}")

            frame_idx   = 0
            fps_timer   = time.time()
            fps_frames  = 0
            display_fps = 0.0

            print("[RUNNING] Press 'q' to quit.\n" + "-" * 55)

            while cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    if USE_LOCAL:
                        print("[INFO] Video ended.")
                    else:
                        print("[WARN] Lost frame — reconnecting ...")
                    break

                frame_idx  += 1
                fps_frames += 1

                elapsed = time.time() - fps_timer
                if elapsed >= 1.0:
                    display_fps = fps_frames / elapsed
                    fps_frames  = 0
                    fps_timer   = time.time()

                # Skipped frames — just show with HUD, no YOLO
                if frame_idx % FRAME_SKIP != 0:
                    display = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))
                    draw_hud(display, right_count, left_count, display_fps, LINE_X)
                    cv2.imshow("Car Counter", display)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        cap.release()
                        cv2.destroyAllWindows()
                        conn.close()
                        return
                    continue

                # ── YOLO on original frame ─────────────────
                results = model.track(
                    frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    classes=list(CAR_CLASSES.keys()),
                    conf=0.25,
                    verbose=False
                )

                if results[0].boxes.id is not None:
                    boxes     = results[0].boxes.xyxy.cpu().numpy()
                    track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                    classes   = results[0].boxes.cls.cpu().numpy().astype(int)
                    confs     = results[0].boxes.conf.cpu().numpy()        # ← ADD THIS

                for box, tid, cid, conf in zip(boxes, track_ids, classes, confs):
                        x1, y1, x2, y2 = map(int, box)
                        cx       = (x1 + x2) / 2
                        cls_name = CAR_CLASSES.get(cid, "vehicle")

                        # Direction detection using ORIGINAL frame coords
                        direction = None
                        if tid in prev_centers and tid not in counted_ids:
                            prev_cx = prev_centers[tid]
                            if prev_cx < line_x_orig <= cx:
                                direction = "right"
                            elif prev_cx > line_x_orig >= cx:
                                direction = "left"

                        if direction:
                            counted_ids.add(tid)
                            log_crossing(conn, int(tid), direction, cls_name)
                            right_count, left_count = get_summary(conn)
                            arrow = "->" if direction == "right" else "<-"
                            print(
                                f"[CROSS] Frame {frame_idx:>6} | "
                                f"ID {tid:>4} | {cls_name:<10} | "
                                f"{arrow}  {direction.upper():<5} | "
                                f"RIGHT: {right_count}  LEFT: {left_count}"
                            )

                        prev_centers[tid] = cx

                        # Draw box on original frame
                        color = CLR_RIGHT if direction == "right" else (
                                CLR_LEFT  if direction == "left"  else (200, 200, 200))
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        label = f"ID:{tid} {cls_name} {conf:.2f}"
                        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                        cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw, y1), color, -1)
                        cv2.putText(frame, label, (x1, y1 - 4),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, CLR_WHITE, 1, cv2.LINE_AA)

                # Resize THEN draw HUD on display frame
                display = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))
                draw_hud(display, right_count, left_count, display_fps, LINE_X)
                cv2.imshow("Car Counter", display)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n[EXIT] User quit.")
                    cap.release()
                    cv2.destroyAllWindows()
                    conn.close()
                    return

            cap.release()

            # If local video ended normally, stop the loop
            if USE_LOCAL:
                print("\n[DONE] Local video finished.")
                print(f"[FINAL] RIGHT: {right_count} | LEFT: {left_count}")
                cv2.destroyAllWindows()
                conn.close()
                return

        except Exception as e:
            print(f"[ERROR] {e}")
            if USE_LOCAL:
                conn.close()
                return
            print(f"[RETRY] Reconnecting in 5s ...")
            time.sleep(5)


if __name__ == "__main__":
    main()