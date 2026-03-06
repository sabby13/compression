import cv2
import os

video_path = "input.mp4"
output_dir = "frames"

os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(video_path)

fps = cap.get(cv2.CAP_PROP_FPS)
print("FPS:", fps)

frame_count = 0
max_frames = 300

while cap.isOpened() and frame_count < max_frames:
    ret, frame = cap.read()
    if not ret:
        break

    frame_filename = os.path.join(output_dir, f"frame_{frame_count:03d}.jpg")
    cv2.imwrite(frame_filename, frame)

    frame_count += 1
    timestamp = frame_count / fps

cap.release()
print(f"Extracted {frame_count} frames")