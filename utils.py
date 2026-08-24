import cv2
import os
import numpy as np
from db import DatabaseManager
import time

os.makedirs("dataset", exist_ok=True)
os.makedirs("models", exist_ok=True)

db_manager = DatabaseManager()

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

def capture_images(student_id, student_name):
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        return False, "Error: Could not open webcam."

    student_dir = f"dataset/{student_id}_{student_name}"
    os.makedirs(student_dir, exist_ok=True)

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

            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, f"Scanning: {count}%", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            # Draw a nice progress bar at the bottom of the screen
            height, width, _ = frame.shape
            cv2.rectangle(frame, (0, height - 30), (width, height), (0, 0, 0), -1) # Background bar
            cv2.rectangle(frame, (0, height - 30), (int(width * (count / 100.0)), height), (0, 255, 0), -1) # Progress
            cv2.putText(frame, "Processing Face Data...", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            time.sleep(0.02) # Faster sleep for smoother rendering

        cv2.imshow('Registration - Processing Face Data', frame)
        
        # Proper waitKey to keep window responsive and allow quitting
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    
    # Add a slight delay to ensure window closes before Streamlit continues
    time.sleep(0.5)

    if count >= 100:
        db_manager.register_student(student_id, student_name)
        return True, "Successfully captured 100 images and registered student."
    else:
        return False, "Capture cancelled or failed before reaching 100 images."
