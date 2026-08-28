import os
import cv2
import numpy as np
import pickle
from db import DatabaseManager
import time
from datetime import datetime
import json
from insightface.app import FaceAnalysis

db_manager = DatabaseManager()

# Load config
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        DISTANCE_THRESHOLD = config.get("distance_threshold", 1.0)
except FileNotFoundError:
    DISTANCE_THRESHOLD = 1.0

_face_app = None

def get_face_app():
    global _face_app
    if _face_app is None:
        _face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_app

def update_embeddings():
    dataset_path = "dataset"
    if not os.path.exists(dataset_path) or len(os.listdir(dataset_path)) == 0:
        return False, "Dataset is empty. Please register students first."

    app = get_face_app()

    known_encodings = []
    known_student_ids = []
    known_names = []

    for student_folder in os.listdir(dataset_path):
        folder_path = os.path.join(dataset_path, student_folder)
        if not os.path.isdir(folder_path):
            continue

        parts = student_folder.split('_')
        student_id = parts[0]
        student_name = parts[1] if len(parts) > 1 else "Unknown"
        
        student_encodings = []
        
        image_files = os.listdir(folder_path)
        for image_name in image_files[:20]:
            image_path = os.path.join(folder_path, image_name)
            img = cv2.imread(image_path)
            if img is None: continue
            
            # Pad the 128x128 cropped face so insightface detector can find it
            if img.shape[0] < 300 or img.shape[1] < 300:
                pad_y = (640 - img.shape[0]) // 2
                pad_x = (640 - img.shape[1]) // 2
                img = cv2.copyMakeBorder(img, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=[0, 0, 0])
            
            faces = app.get(img)
            
            if len(faces) > 0:
                student_encodings.append(faces[0].embedding)
                
        if len(student_encodings) > 0:
            avg_encoding = np.mean(student_encodings, axis=0)
            avg_encoding = avg_encoding / np.linalg.norm(avg_encoding)
            known_encodings.append(avg_encoding)
            known_student_ids.append(student_id)
            known_names.append(student_name)
            
    if len(known_encodings) == 0:
        return False, "No valid faces found in dataset to generate embeddings."
        
    data = {
        "encodings": known_encodings,
        "student_ids": known_student_ids,
        "names": known_names
    }
    
    with open("models/embeddings.pkl", "wb") as f:
        pickle.dump(data, f)
        
    return True, "Embeddings generated and saved successfully."

def recognize_faces_and_mark_attendance():
    if not os.path.exists("models/embeddings.pkl"):
        return False, "Embeddings not found. Please update embeddings first."
        
    with open("models/embeddings.pkl", "rb") as f:
        data = pickle.load(f)
        
    known_encodings = np.array(data["encodings"])
    known_student_ids = data["student_ids"]
    known_names = data["names"]
    
    app = get_face_app()
        
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        return False, "Could not open webcam."
        
    window_name = 'Smart Attendance System'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    consecutive_recognitions = 0
    logged_msg = ""
    
    while consecutive_recognitions < 5:
        ret, frame = cam.read()
        if not ret:
            break
            
        height, width, _ = frame.shape
        cv2.putText(frame, "AI Scanning for Faces...", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        faces = app.get(frame)
        
        for face in faces:
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            encoding = face.embedding
            encoding = encoding / np.linalg.norm(encoding)
            
            name = "Unknown"
            student_id = None
            color = (0, 0, 255)
            
            distances = np.linalg.norm(known_encodings - encoding, axis=1)
            
            if len(distances) > 0:
                best_match_index = np.argmin(distances)
                if distances[best_match_index] < DISTANCE_THRESHOLD:
                    student_id = known_student_ids[best_match_index]
                    name = known_names[best_match_index]
                    color = (0, 255, 0)
                        
            if student_id is not None:
                logged_msg = db_manager.mark_attendance(student_id)
                consecutive_recognitions += 1
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"Verified: {name}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                
                cv2.rectangle(frame, (0, 0), (width, 40), (0, 255, 0), -1)
                cv2.putText(frame, "ACCESS GRANTED - LOGGING TIME", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            else:
                consecutive_recognitions = 0
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, "Unknown Face", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow(window_name, frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    time.sleep(0.5)
    
    if logged_msg:
        return True, logged_msg
    else:
        return False, "Session ended without logging attendance."
