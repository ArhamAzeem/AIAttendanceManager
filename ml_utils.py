import os
import cv2
import numpy as np
import pickle
# pyrefly: ignore [missing-import]
from keras.models import Sequential, load_model
# pyrefly: ignore [missing-import]
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
# pyrefly: ignore [missing-import]
from keras.utils import to_categorical
# pyrefly: ignore [missing-import]
from sklearn.model_selection import train_test_split
# pyrefly: ignore [missing-import]
from sklearn.preprocessing import LabelEncoder
from db import DatabaseManager
import time
from datetime import datetime

db_manager = DatabaseManager()

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

def train_model():
    """Reads dataset, trains a CNN model, and saves it."""
    dataset_path = "dataset"
    if not os.path.exists(dataset_path) or len(os.listdir(dataset_path)) == 0:
        return False, "Dataset is empty. Please register students first."

    faces = []
    labels = []

    for student_folder in os.listdir(dataset_path):
        folder_path = os.path.join(dataset_path, student_folder)
        if not os.path.isdir(folder_path):
            continue

        student_id = student_folder.split('_')[0]

        for image_name in os.listdir(folder_path):
            image_path = os.path.join(folder_path, image_name)
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                img = cv2.resize(img, (128, 128))
                faces.append(img)
                labels.append(student_id)

    if len(faces) == 0:
        return False, "No images found in dataset."

    faces = np.array(faces).reshape(-1, 128, 128, 1)
    faces = faces / 255.0

    le = LabelEncoder()
    labels_encoded = le.fit_transform(labels)
    labels_categorical = to_categorical(labels_encoded)

    with open("models/label_encoder.pkl", "wb") as f:
        pickle.dump(le, f)

    x_train, x_test, y_train, y_test = train_test_split(faces, labels_categorical, test_size=0.2, random_state=42)

    num_classes = len(le.classes_)

    model = Sequential([
        Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 1)),
        MaxPooling2D(2, 2),
        Conv2D(64, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(num_classes, activation='softmax')
    ])

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    model.fit(x_train, y_train, epochs=10, validation_data=(x_test, y_test), batch_size=32, verbose=1)

    model.save("models/attendance_model.h5")

    return True, "Model trained and saved successfully."

def recognize_faces_and_mark_attendance():
    if not os.path.exists("models/attendance_model.h5") or not os.path.exists("models/label_encoder.pkl"):
        return False, "Model not trained yet. Please train the model first."

    model = load_model("models/attendance_model.h5")
    with open("models/label_encoder.pkl", "rb") as f:
        le = pickle.load(f)

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        return False, "Could not open webcam."

    consecutive_recognitions = 0
    logged_msg = ""
    
    while consecutive_recognitions < 5:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        height, width, _ = frame.shape
        cv2.putText(frame, "AI Scanning for Faces...", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_img_resized = cv2.resize(face_img, (128, 128))
            face_img_reshaped = face_img_resized.reshape(1, 128, 128, 1) / 255.0

            predictions = model.predict(face_img_reshaped, verbose=0)
            max_prob = np.max(predictions)
            predicted_class = np.argmax(predictions)

            if max_prob > 0.8:
                student_id = le.inverse_transform([predicted_class])[0]
                student_data = db_manager.get_student_by_id(student_id)
                name = student_data["name"] if student_data else "Unknown"

                # Mark Attendance
                logged_msg = db_manager.mark_attendance(student_id)
                consecutive_recognitions += 1

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"Verified: {name}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Draw success banner
                cv2.rectangle(frame, (0, 0), (width, 40), (0, 255, 0), -1)
                cv2.putText(frame, "ACCESS GRANTED - LOGGING TIME", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            else:
                consecutive_recognitions = 0
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow('Smart Attendance System', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    time.sleep(0.5)
    
    if logged_msg:
        return True, logged_msg
    else:
        return False, "Session ended without logging attendance."
