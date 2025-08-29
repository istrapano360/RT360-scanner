
import cv2
import time
import serial
from pathlib import Path
from threading import Thread, Lock, Event
from flask import Flask, render_template, Response, redirect, url_for, request
from Picam_preset_scanner import get_camera, take_picture, capture_both_formats

# Postavke, Status i frame spremnici
base_path = Path.home() / "Pictures" / "RT360_Capture"
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
scan_cancel_event = Event()
scan_in_progress = False
current_scan_step = 0
total_scan_steps = 64
streaming = False
output_frame_0 = None
output_frame_1 = None

app = Flask(__name__)

# Lockovi za svaku kameru
frame_lock_0 = Lock()
frame_lock_1 = Lock()
camera_lock_0 = Lock()
camera_lock_1 = Lock()
focus_lock_0 = Lock()
focus_lock_1 = Lock()

# Zoom razine po kameri
zoom_levels = [1.0, 1.0]    # index 0 za cam0, index 1 za cam1
ZOOM_STEP = 0.3
ZOOM_MIN = 0.5
ZOOM_MAX = 10.0
focus_values = [2.0, 2.0]   # Pocetne vrijednosti fokusa za cam0 i cam1
FOCUS_MIN = 0.0             # Beskonasno (infinity)
FOCUS_MAX = 10.0            # Maksimalni bliski fokus
FOCUS_STEP = 0.1            # Korak za slider

# Funkcija za dohvat kamere
def preview_worker(cam_id):
    global output_frame_0, output_frame_1, streaming
    lock = camera_lock_0 if cam_id == 0 else camera_lock_1
    if not lock.acquire(timeout=5):
        print(f"[PREVIEW] Camera {cam_id} bussy.")
        return
    try:
        cam = get_camera(cam_id)
        cam.configure(cam.create_video_configuration(main={"size": (640, 480)}))
        cam.start()
        print(f"[PREVIEW] Camera {cam_id} initialized.")
        while streaming:
            raw = cam.capture_array()
            raw = cv2.cvtColor(raw, cv2.COLOR_RGB2BGR)
            h, w, _ = raw.shape
            zoom = zoom_levels[cam_id]
            zoom_w = int(w / zoom)
            zoom_h = int(h / zoom)
            x1 = (w - zoom_w) // 2
            y1 = (h - zoom_h) // 2
            cropped = raw[y1:y1+zoom_h, x1:x1+zoom_w]
            frame = cv2.resize(cropped, (w, h))
            encoded = cv2.imencode('.jpg', frame)[1].tobytes()
            if cam_id == 0:
                with frame_lock_0:
                    output_frame_0 = encoded
            else:
                with frame_lock_1:
                    output_frame_1 = encoded
            time.sleep(0.03)
        cam.stop()
        print(f"[PREVIEW] Camera {cam_id} stoped.")

    except Exception as e:
        print(f"[PREVIEW] Camera error {cam_id}: {e}")

    finally:
        lock.release()

# Ruta za pokretanje preview-a
@app.route("/start_preview")
def start_preview():
    global streaming
    if not streaming:
        streaming = True
        Thread(target=preview_worker, args=(0,), daemon=True).start()
        Thread(target=preview_worker, args=(1,), daemon=True).start()
    return redirect(url_for("index"))

# Ruta za zaustavljanje preview-a
@app.route("/stop_preview")
def stop_preview():
    global streaming
    streaming = False
    return redirect(url_for("index"))

# Ruta za dohvat video feed-a
@app.route("/video_feed/<int:cam_id>")
def video_feed(cam_id):
    def generate():
        while streaming:
            if cam_id == 0:
                with frame_lock_0:
                    frame = output_frame_0
            else:
                with frame_lock_1:
                    frame = output_frame_1
            if frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            time.sleep(0.03)
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

# Ruta za glavni pregled
@app.route("/")
def index():
    return render_template("index.html", 
                        FOCUS_MIN=FOCUS_MIN,
                        FOCUS_MAX=FOCUS_MAX,
                        FOCUS_STEP=FOCUS_STEP,
                        preview_active=streaming,
                        focus_values=focus_values,
                        active_folder=current_scan_folder.name,
                        scan_in_progress=scan_in_progress,
                        current_scan_step=current_scan_step,
                        total_scan_steps=total_scan_steps)

# Ruta za dohvat trenutne vrijednosti fokusa                  
@app.route("/zoom/<int:cam_id>/<action>")
def zoom(cam_id, action):
    global zoom_levels
    if cam_id not in [0, 1]:
        return "Invalid camera ID", 400
    current = zoom_levels[cam_id]
    if action == "in":
        zoom_levels[cam_id] = min(current + ZOOM_STEP, ZOOM_MAX)
    elif action == "out":
        zoom_levels[cam_id] = max(current - ZOOM_STEP, ZOOM_MIN)
    elif action == "reset":
        zoom_levels[cam_id] = 1.0
    else:
        return "Invalid zoom action", 400
    print(f"[ZOOM] Cam {cam_id}: {zoom_levels[cam_id]}")
    return redirect(url_for("index"))

# Ruta za snimanje slike    
@app.route("/take_picture")
def take_picture_route():
    global streaming, current_scan_folder
    was_streaming = streaming
    streaming = False
    time.sleep(0.5)
    print("[CAPTURING] Calling capture_both_formats()...")
    capture_both_formats(current_scan_folder)
    print("[CAPTURING] Done.")
    if was_streaming:
        Thread(target=preview_worker, args=(0,), daemon=True).start()
        Thread(target=preview_worker, args=(1,), daemon=True).start()
        streaming = True
    return redirect(url_for("index"))
    
# Ruta za autofokus po kameri
@app.route("/autofocus/<int:cam_id>")
def autofocus(cam_id):
    if cam_id not in [0, 1]:
        return "Invalid camera ID", 400
    lock = focus_lock_0 if cam_id == 0 else focus_lock_1
    if not lock.acquire(timeout=2):
        return f"Focus camera {cam_id} bussy", 503
    try:
        cam = get_camera(cam_id)
        cam.autofocus_cycle()
        print(f"[FOCUS] Autofocus camera {cam_id} successfully started.")
        return "", 204  # No Content (successfuly done)
    except Exception as e:
        print(f"[FOCUS] Camera error {cam_id}: {str(e)}")
        return "Error", 500
    finally:
        lock.release()

# Ruta za rucni fokus po kameri
@app.route("/set_focus/<int:cam_id>", methods=["POST"])
def set_focus(cam_id):
    if cam_id not in [0, 1]:
        return "Invalid camera ID", 400
    try:
        value = float(request.form.get("value"))
        value = max(FOCUS_MIN, min(value, FOCUS_MAX))
        lock = focus_lock_0 if cam_id == 0 else focus_lock_1
        if not lock.acquire(timeout=2):
            return "Focus bussy", 503
        cam = get_camera(cam_id)
        cam.set_controls({"AfMode": 0, "LensPosition": value})
        print(f"[FOCUS] CAmera {cam_id} Focus set on {value}")
        return "", 204
    except Exception as e:
        print(f"[FOCUS] Camera error {cam_id}: {str(e)}")
        return "Error", 500
    finally:
        lock.release()

# Ruta za postavljanje postavki kamere
@app.route("/start_scan")
def start_scan():
    Thread(target=scan_64, daemon=True).start()
    return redirect(url_for("index"))

# Ruta za otkazivanje skeniranja
@app.route("/cancel_scan")
def cancel_scan():
    scan_cancel_event.set()
    return redirect(url_for("index"))

# Ruta za dohvat statusa skeniranja
@app.route("/scan_status")
def scan_status():
    global scan_in_progress, current_scan_step, total_scan_steps
    return {
        "scan_in_progress": scan_in_progress,
        "current_scan_step": current_scan_step,
        "total_scan_steps": total_scan_steps
    }

#Start scan   
def scan_64():
    global streaming, current_scan_folder
    global scan_in_progress, current_scan_step, total_scan_steps
    scan_in_progress = True
    current_scan_step = 0
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
    except Exception as e:
        print(f"[SCAN] Can't open serial port: {e}")
        scan_in_progress = False
        return
    was_streaming = streaming
    if streaming:
        print("[SCAN] Pause preview.")
        streaming = False
        time.sleep(0.5)
    scan_cancel_event.clear()
    for i in range(total_scan_steps):
        current_scan_step = i + 1
        if scan_cancel_event.is_set():
            print("[SCAN] Interupted by user.")
            break
        print(f"[SCAN] [{i+1}/{total_scan_steps}]  sending STEP to Arduino...")
        ser.write(b"STEP\n")
        t0 = time.time()
        while True:
            if scan_cancel_event.is_set():
                print("[SCAN]  Interupted while waiting.")
                ser.close()
                scan_in_progress = False
                return
            if ser.in_waiting:
                response = ser.readline().decode().strip()
                if response == "DONE":
                    print("[SCAN]  Arduino done.")
                    break
            elif time.time() - t0 > 10:
                print("[SCAN]  Timeout Arduino response.")
                ser.close()
                scan_in_progress = False
                return
            time.sleep(0.01)
        print(f"[SCAN]  Capturing {i+1}...")
        capture_both_formats(current_scan_folder)
    ser.close()
    print("[SCAN]  Scan done.")
    scan_in_progress = False
    current_scan_step = 0
    if was_streaming:
        print("[SCAN]  Restoring preview...")
        streaming = True
        Thread(target=preview_worker, args=(0,), daemon=True).start()
        Thread(target=preview_worker, args=(1,), daemon=True).start()

# Funkcija za dohvat sljedeceg foldera za skeniranje
def get_next_scan_folder():
    i = 1
    while True:
        folder = base_path / f"Scan{i:03d}"
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            return folder
        i += 1

# Ruta za kreiranje novog foldera         
@app.route("/new_folder")
def new_folder():
    global current_scan_folder
    current_scan_folder = get_next_scan_folder()
    print(f"[FOLDER] New activ folder: {current_scan_folder}")
    return redirect(url_for("index"))

# Funkcija za pronalazak najnovijeg foldera skeniranja     
def find_latest_scan_folder():
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path / "Scan001"
    
    max_num = 0
    latest_folder = base_path / "Scan001"  # default fallback
    
    for folder in base_path.iterdir():
        if folder.is_dir() and folder.name.startswith("Scan"):
            try:
                # Extract number from folder name (handles "Scan006" -> 6)
                num = int(folder.name[4:])  # Changed from [3:] to [4:] to handle "Scan" prefix correctly
                if num > max_num:
                    max_num = num
                    latest_folder = folder
            except ValueError:
                continue
    return latest_folder

# Inicijalizacija trenutnog foldera skeniranja
# Make sure to call this after the base_path is set
# This will ensure that the latest scan folder is found at startup     
current_scan_folder = find_latest_scan_folder()           

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
