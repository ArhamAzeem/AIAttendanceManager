import os
from datetime import datetime, timedelta

import numpy as np
from PIL import Image

from db import DatabaseManager

os.makedirs("dataset", exist_ok=True)

db_manager = DatabaseManager()


def _write_placeholder_faces(student_id, student_name, count=40):
    """Synthetic grayscale faces so AI Training can run without a webcam."""
    student_dir = f"dataset/{student_id}_{student_name}"
    os.makedirs(student_dir, exist_ok=True)
    seed = abs(hash(student_id)) % (2**32)
    rng = np.random.default_rng(seed)
    base = rng.integers(50, 200, size=(128, 128), dtype=np.uint8)
    for i in range(count):
        noise = rng.integers(-12, 13, size=(128, 128), dtype=np.int16)
        img = np.clip(base.astype(np.int16) + noise + (i % 8), 0, 255).astype(np.uint8)
        Image.fromarray(img, mode="L").save(f"{student_dir}/{i + 1}.jpg")


def register_student_without_camera(student_id, student_name):
    success, message = db_manager.register_student(student_id, student_name)
    if not success:
        return False, message
    _write_placeholder_faces(student_id, student_name)
    return True, "Student saved in MongoDB without a camera. Placeholder images added for training."


def seed_demo_class():
    """Three students + multi-day attendance so every dashboard page has data."""
    if db_manager.get_all_students():
        return False, "Students already exist. Demo data was not added."

    names = ["Ali Khan", "Sara Ahmed", "Hassan Raza"]
    created_ids = []
    for name in names:
        student_id = db_manager.generate_student_id()
        success, message = register_student_without_camera(student_id, name)
        if not success:
            return False, message
        created_ids.append(student_id)

    today = datetime.now().date()
    day_minus_2 = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    day_minus_1 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    db_manager.add_attendance_record(created_ids[0], day_minus_2, "08:12:00", "14:05:00")
    db_manager.add_attendance_record(created_ids[1], day_minus_2, "08:18:00", "14:01:00")
    db_manager.add_attendance_record(created_ids[2], day_minus_2, "08:22:00", "13:58:00")

    db_manager.add_attendance_record(created_ids[0], day_minus_1, "08:10:00", "14:02:00")
    db_manager.add_attendance_record(created_ids[1], day_minus_1, "08:25:00", "-")

    db_manager.add_attendance_record(created_ids[0], today_str, "08:15:00", "-")

    return True, "Demo class loaded: 3 students, placeholder faces, and sample attendance."
