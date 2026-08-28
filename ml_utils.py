import os
import cv2
import numpy as np
import pickle
import time
from datetime import datetime

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.layers import (
    Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import GlobalAveragePooling2D, Input, Concatenate
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from db import DatabaseManager

db_manager = DatabaseManager()

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


def train_model():
    checkpoint_path = "models/attendance_model.h5"

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

    faces = np.array(faces).reshape(-1, 128, 128, 1).astype("float32")

    le = LabelEncoder()
    labels_encoded = le.fit_transform(labels)
    labels_categorical = to_categorical(labels_encoded)

    # Save label encoder
    os.makedirs("models", exist_ok=True)
    with open("models/label_encoder.pkl", "wb") as f:
        pickle.dump(le, f)

    x_train, x_test, y_train, y_test = train_test_split(
        faces, labels_categorical, test_size=0.2, random_state=42, stratify=labels_encoded
    )

    num_classes = len(le.classes_)

    # === Data Augmentation ===
    datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        brightness_range=[0.7, 1.3],
        zoom_range=0.15,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    val_datagen = ImageDataGenerator(rescale=1./255)

    
    inputs = Input(shape=(128, 128, 1))
    x = Concatenate()([inputs, inputs, inputs])  # 1-channel grayscale -> 3-channel, model input only

    base_model = MobileNetV2(input_shape=(128, 128, 3), include_top=False, weights='imagenet')
    base_model.trainable = True
    for layer in base_model.layers[:-20]:  # keep most layers frozen, unfreeze last ~20
        layer.trainable = False 

    x = base_model(x)
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.5)(x)
    outputs = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs, outputs)
    model.compile(optimizer=Adam(learning_rate=1e-5), loss='categorical_crossentropy', metrics=['accuracy'])

    # === Save only the best epoch, stop early if no improvement ===
    callbacks = [
        ModelCheckpoint(
            checkpoint_path,
            monitor='val_accuracy',
            save_best_only=True,
            mode='max',
            verbose=1
        ),
        EarlyStopping(
            monitor='val_accuracy',
            patience=8,
            restore_best_weights=True,
            mode='max'
        )
    ]

    print("Training started... This may take a few minutes.")
    history = model.fit(
        datagen.flow(x_train, y_train, batch_size=32),
        epochs=25,
        validation_data=val_datagen.flow(x_test, y_test, batch_size=32, shuffle=False),
        steps_per_epoch=len(x_train) // 32,
        callbacks=callbacks,
        verbose=1
    )

    # model.save() removed — ModelCheckpoint already wrote the best-val_accuracy weights to checkpoint_path
    final_acc = max(history.history['val_accuracy'])
    return True, f"Model trained successfully. Best validation accuracy: {final_acc:.2%}"


def recognize_faces_and_mark_attendance():
    if not os.path.exists("models/attendance_model.h5") or not os.path.exists("models/label_encoder.pkl"):
        return False, "Model not trained yet. Please train the model first."

    model = load_model("models/attendance_model.h5")
    with open("models/label_encoder.pkl", "rb") as f:
        le = pickle.load(f)

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        return False, "Could not open webcam."

    window_name = 'Smart Attendance System'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    consecutive_recognitions = 0
    logged_msg = ""
    for folder in os.listdir("dataset"):
        path = f"dataset/{folder}"
        if os.path.isdir(path):
            print(folder, len(os.listdir(path)))

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
            for cls, prob in zip(le.classes_, predictions[0]):
                print(f"{cls}: {prob:.3f}")
            max_prob = np.max(predictions)
            predicted_class = np.argmax(predictions)

            if max_prob > 0.8:
                student_id = le.inverse_transform([predicted_class])[0]
                student_data = db_manager.get_student_by_id(student_id)
                name = student_data["name"] if student_data else "Unknown"

                logged_msg = db_manager.mark_attendance(student_id)
                consecutive_recognitions += 1

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"Verified: {name}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                cv2.rectangle(frame, (0, 0), (width, 40), (0, 255, 0), -1)
                cv2.putText(frame, "ACCESS GRANTED - LOGGING TIME", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            else:
                consecutive_recognitions = 0
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

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

    