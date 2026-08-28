import cv2
import os
import numpy as np
from db import DatabaseManager
import time
from ml_utils import get_face_app, update_embeddings
import pickle

os.makedirs("dataset", exist_ok=True)
os.makedirs("models", exist_ok=True)

db_manager = DatabaseManager()

def check_duplicate_face(cam, num_checks=15, threshold=1.0, window_name=None):
    if not os.path.exists("models/embeddings.pkl"):
        return False, None, None

    with open("models/embeddings.pkl", "rb") as f:
        data = pickle.load(f)
        
    known_encodings = np.array(data["encodings"])
    known_student_ids = data["student_ids"]
    known_names = data["names"]
    
    app = get_face_app()

    checks_done = 0
    match_counts = {}

    while checks_done < num_checks:
        ret, frame = cam.read()
        if not ret:
            break

        display_frame = frame.copy()
        cv2.putText(display_frame, "Verifying identity...", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        if window_name:
            cv2.imshow(window_name, display_frame)
            cv2.waitKey(1)

        faces = app.get(frame)

        for face in faces:
            encoding = face.embedding
            encoding = encoding / np.linalg.norm(encoding)
            
            distances = np.linalg.norm(known_encodings - encoding, axis=1)
                
            if len(distances) > 0:
                best_match_index = np.argmin(distances)
                if distances[best_match_index] < threshold:
                    student_id = known_student_ids[best_match_index]
                    match_counts[student_id] = match_counts.get(student_id, 0) + 1

            checks_done += 1

        cv2.waitKey(1)

    if not match_counts:
        return False, None, None

    best_match = max(match_counts, key=match_counts.get)
    votes = match_counts[best_match]

    if votes >= (num_checks * 0.5):
        student_data = db_manager.get_student_by_id(best_match)
        name = student_data["name"] if student_data else "Unknown"
        return True, best_match, name

    return False, None, None

def capture_images(student_id, student_name):
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        return False, "Error: Could not open webcam."

    student_dir = f"dataset/{student_id}_{student_name}"
    os.makedirs(student_dir, exist_ok=True)

    window_name = 'Registration - Processing Face Data'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    for _ in range(10):
        cam.read()

    is_dup, dup_id, dup_name = check_duplicate_face(cam, window_name=window_name)
    if is_dup:
        cam.release()
        cv2.destroyAllWindows()
        return False, f"This face is already registered as {dup_name} (ID: {dup_id}). Duplicate registration blocked."

    app = get_face_app()

    count = 0
    # Capture 30 images
    while count < 30:
        ret, frame = cam.read()
        if not ret:
            break
            
        faces = app.get(frame)

        for face in faces:
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            count += 1
            
            # Ensure coordinates are within frame bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)

            if x2 > x1 and y2 > y1:
                face_img = frame[y1:y2, x1:x2]
                face_img = cv2.resize(face_img, (128, 128))
                cv2.imwrite(f"{student_dir}/{count}.jpg", face_img)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            percentage = int((count / 30.0) * 100)
            cv2.putText(frame, f"Scanning: {percentage}%", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            height, width, _ = frame.shape
            cv2.rectangle(frame, (0, height - 30), (width, height), (0, 0, 0), -1)
            cv2.rectangle(frame, (0, height - 30), (int(width * (count / 30.0)), height), (0, 255, 0), -1)
            cv2.putText(frame, "Processing Face Data...", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            time.sleep(0.02)

        cv2.imshow(window_name, frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    
    time.sleep(0.5)

    if count >= 30:
        success, message = db_manager.register_student(student_id, student_name)

        if success:
            update_embeddings()
            return True, "Successfully captured images, registered student, and updated embeddings."
        else:
            return False, f"Images captured, but database registration failed: {message}"
    else:
        return False, "Capture cancelled or failed before reaching required images."
