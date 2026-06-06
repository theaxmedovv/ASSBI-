"""
find_line.py — Helper to find the correct LINE_X value for your stream.

Run this first, then update LINE_X in main.py.

Controls:
  LEFT / RIGHT arrow keys  →  move the line
  +  /  -                  →  move line faster / slower
  ENTER                    →  print the current X value and exit
  q                        →  quit
"""

import cv2
import yt_dlp
import os

VIDEO_FILE   = "test_video.mp4"
USE_LOCAL    = True
YOUTUBE_URL  = "https://www.youtube.com/live/M3EYAY2MftI?si=TX_LD4OyFsCUEfLS"
COOKIES_FILE = "cookies.txt"
DISPLAY_W    = 1280
DISPLAY_H    = 720


def get_stream_url():
    ydl_opts = {'format': 'best[height<=480][ext=mp4]/best[height<=480]/best', 'quiet': True}
    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(YOUTUBE_URL, download=False)
        return info['url']


def main():
    if USE_LOCAL:
        print(f"Opening local file: {VIDEO_FILE}")
        cap = cv2.VideoCapture(VIDEO_FILE)
    else:
        print("Fetching stream ...")
        cap = cv2.VideoCapture(get_stream_url(), cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("ERROR: could not open stream.")
        return

    # Start line in the middle
    ok, frame = cap.read()
    if not ok:
        print("ERROR: no frame received.")
        return

    h, w = frame.shape[:2]
    line_x = 640
    step   = 5

    print(f"Frame size: {w}x{h}")
    print("Use ← → to move line, ENTER to confirm, q to quit.\n")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        display = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))

        # Scale line_x for display
        scale    = DISPLAY_W / w
        disp_x   = int(line_x * scale)

        cv2.line(display, (disp_x, 0), (disp_x, DISPLAY_H), (0, 255, 255), 2)
        cv2.putText(display, f"LINE_X = {line_x}  (step={step})",
                    (disp_x + 5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(display, "ENTER = confirm  |  +/- = change step  |  q = quit",
                    (10, DISPLAY_H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Line Finder — use arrow keys", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == 13:  # ENTER
            print(f"\n✅  Set  LINE_X = {line_x}  in main.py")
            break
        elif key == 2:   # LEFT arrow
            line_x = max(0, line_x - step)
        elif key == 3:   # RIGHT arrow
            line_x = min(w, line_x + step)
        elif key == ord('+'):
            step = min(50, step + 5)
        elif key == ord('-'):
            step = max(1, step - 1)

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nCopy this line into main.py:\n  LINE_X = {line_x}")


if __name__ == "__main__":
    main()