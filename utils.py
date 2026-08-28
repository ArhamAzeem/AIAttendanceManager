import cv2
import os
import numpy as np
from db import DatabaseManager
import time

os.makedirs("dataset", exist_ok=True)
os.makedirs("models", exist_ok=True)

db_manager = DatabaseManager()

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

def check_duplicate_face(cam, face_cascade, num_checks=25, threshold=0.85, margin=0.25, window_name=None):
    """
    Improved duplicate face checker with:
    - More frames (25)
    - Higher confidence threshold
    - Stricter voting (70% agreement required)
    - Face size filter
    - Better feedback
    """
    if not os.path.exists("models/attendance_model.h5") or not os.path.exists("models/label_encoder.pkl"):
        return False, None, None

    from keras.models import load_model
    import pickle

    model = load_model("models/attendance_model.h5")
    with open("models/label_encoder.pkl", "rb") as f:
        le = pickle.load(f)

    checks_done = 0
    match_counts = {}          # student_id → number of votes
    confidence_sum = {}        # student_id → sum of confidences (for better decision)

    while checks_done < num_checks:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        # --- Visual feedback ---
        display_frame = frame.copy()
        cv2.putText(display_frame, f"Verifying identity... ({checks_done}/{num_checks})", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        if window_name:
            cv2.imshow(window_name, display_frame)
            cv2.waitKey(1)

        for (x, y, w, h) in faces:
            # Reject faces that are too small (poor quality)
            if w < 100 or h < 100:
                continue

            face_img = gray[y:y+h, x:x+w]
            face_img_resized = cv2.resize(face_img, (128, 128))
            face_img_reshaped = face_img_resized.reshape(1, 128, 128, 1) / 255.0

            predictions = model.predict(face_img_reshaped, verbose=0)[0]
            sorted_probs = np.sort(predictions)[::-1]

            top_prob = sorted_probs[0]
            second_prob = sorted_probs[1] if len(sorted_probs) > 1 else 0.0
            confidence_gap = top_prob - second_prob

            predicted_class = np.argmax(predictions)

            # Require both high confidence AND clear gap from second place
            if top_prob > threshold and confidence_gap > margin:
                student_id = le.inverse_transform([predicted_class])[0]
                
                match_counts[student_id] = match_counts.get(student_id, 0) + 1
                confidence_sum[student_id] = confidence_sum.get(student_id, 0.0) + top_prob

            checks_done += 1
            break   # only process the first good face per frame

        cv2.waitKey(1)

    if not match_counts:
        return False, None, None

    # Pick the student with the most votes
    best_match = max(match_counts, key=match_counts.get)
    votes = match_counts[best_match]
    avg_confidence = confidence_sum[best_match] / votes

    # Require strong majority (70%) AND good average confidence
    if votes >= (num_checks * 0.7) and avg_confidence >= 0.80:
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

    is_dup, dup_id, dup_name = check_duplicate_face(cam, face_cascade, window_name=window_name)
    if is_dup:
        cam.release()
        cv2.destroyAllWindows()
        return False, f"This face is already registered as {dup_name} (ID: {dup_id}). Duplicate registration blocked."

    count = 0
    while count < 100:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (128, 128))
            cv2.imwrite(f"{student_dir}/{count}.jpg", face_img)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, f"Scanning: {count}%", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            height, width, _ = frame.shape
            cv2.rectangle(frame, (0, height - 30), (width, height), (0, 0, 0), -1)
            cv2.rectangle(frame, (0, height - 30), (int(width * (count / 100.0)), height), (0, 255, 0), -1)
            cv2.putText(frame, "Processing Face Data...", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            time.sleep(0.02)

        cv2.imshow(window_name, frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    
    time.sleep(0.5)

    if count >= 100:
        success, message = db_manager.register_student(student_id, student_name)

        if success:
            return True, "Successfully captured 100 images and registered student."
        else:
            return False, f"Images captured, but database registration failed: {message}"
    else:
        return False, "Capture cancelled or failed before reaching 100 images."
