# ORIGINALLY THOUGHT OF MAKING A DEKSTOP APP 
# BUT THAT WOULD CAUSE THE ISSUE OF DISTRIBUTING OUR TOOL 
# SO FOR NOW WE ARE GOING FOR A WEBAPP




import os
import cv2
import json
import base64
import threading
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static")

UPLOAD_FOLDER = "uploads"
FRAMES_FOLDER = "static/frames"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)

# Store job status
jobs = {}

def extract_frames(job_id, video_path, max_frames=300):
    try:
        jobs[job_id]["status"] = "processing"
        
        # Clean up previous frames
        frames_dir = os.path.join(FRAMES_FOLDER, job_id)
        os.makedirs(frames_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        jobs[job_id]["fps"] = round(fps, 2)
        jobs[job_id]["total_video_frames"] = total_video_frames
        jobs[job_id]["duration"] = round(total_video_frames / fps, 2) if fps > 0 else 0

        frame_count = 0
        saved_frames = []

        while cap.isOpened() and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            frame_filename = f"frame_{frame_count:03d}.jpg"
            frame_path = os.path.join(frames_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            saved_frames.append(f"/static/frames/{job_id}/{frame_filename}")

            frame_count += 1
            jobs[job_id]["extracted"] = frame_count
            timestamp = frame_count / fps if fps > 0 else 0

        cap.release()
        jobs[job_id]["status"] = "done"
        jobs[job_id]["frames"] = saved_frames
        jobs[job_id]["extracted"] = frame_count

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["video"]
    if not file.filename.endswith(".mp4"):
        return jsonify({"error": "Only .mp4 files supported"}), 400

    import uuid
    job_id = str(uuid.uuid4())[:8]
    filename = secure_filename(file.filename)
    video_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")
    file.save(video_path)

    max_frames = int(request.form.get("max_frames", 300))
    jobs[job_id] = {"status": "queued", "extracted": 0, "frames": []}

    thread = threading.Thread(target=extract_frames, args=(job_id, video_path, max_frames))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

