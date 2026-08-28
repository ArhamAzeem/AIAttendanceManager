import os
import cv2
import numpy as np
import time
import json
from ml_utils import get_face_app

def load_config():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("distance_threshold", 1.0)
    except FileNotFoundError:
        return 1.0

def evaluate_model():
    dataset_path = "dataset"
    if not os.path.exists(dataset_path) or len(os.listdir(dataset_path)) == 0:
        print("Dataset is empty. Cannot evaluate.")
        return

    app = get_face_app()

    DISTANCE_THRESHOLD = load_config()
    print(f"Using distance threshold: {DISTANCE_THRESHOLD}")

    enrollment_encodings = []
    enrollment_ids = []
    
    test_images = [] # list of dicts: {"path": path, "true_id": id}
    
    print("Processing dataset and splitting into enrollment/test sets (80/20)...")
    
    for student_folder in os.listdir(dataset_path):
        folder_path = os.path.join(dataset_path, student_folder)
        if not os.path.isdir(folder_path):
            continue
            
        student_id = student_folder.split('_')[0]
        image_files = os.listdir(folder_path)
        
        if len(image_files) < 5:
            print(f"Skipping {student_id}, not enough images.")
            continue
            
        # Split 80% enrollment, 20% test
        split_idx = int(len(image_files) * 0.8)
        enroll_files = image_files[:split_idx]
        test_files = image_files[split_idx:]
        
        # Calculate average embedding for enrollment
        student_encs = []
        for img_name in enroll_files[:20]: # use at most 20 for speed
            img_path = os.path.join(folder_path, img_name)
            img = cv2.imread(img_path)
            if img is None: continue
            
            # Pad the 128x128 cropped face so insightface detector can find it
            if img.shape[0] < 300 or img.shape[1] < 300:
                pad_y = (640 - img.shape[0]) // 2
                pad_x = (640 - img.shape[1]) // 2
                img = cv2.copyMakeBorder(img, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=[0, 0, 0])
            
            faces = app.get(img)
            
            if len(faces) > 0:
                student_encs.append(faces[0].embedding)
                
        if len(student_encs) > 0:
            avg_enc = np.mean(student_encs, axis=0)
            avg_enc = avg_enc / np.linalg.norm(avg_enc)
            enrollment_encodings.append(avg_enc)
            enrollment_ids.append(student_id)
            
        # Add test images
        for img_name in test_files:
            test_images.append({
                "path": os.path.join(folder_path, img_name),
                "true_id": student_id
            })

    if len(enrollment_encodings) == 0 or len(test_images) == 0:
        print("Not enough data to evaluate.")
        return
        
    print(f"Enrollment embeddings computed for {len(enrollment_ids)} students.")
    print(f"Running evaluation on {len(test_images)} held-out test images...")
    
    correct = 0
    false_positives = 0
    false_negatives = 0
    
    start_time = time.time()
    total_latency = 0
    
    for item in test_images:
        img_path = item["path"]
        true_id = item["true_id"]
        
        t0 = time.time()
        img = cv2.imread(img_path)
        if img is None: continue
        
        # Pad the 128x128 cropped face so insightface detector can find it
        if img.shape[0] < 300 or img.shape[1] < 300:
            pad_y = (640 - img.shape[0]) // 2
            pad_x = (640 - img.shape[1]) // 2
            img = cv2.copyMakeBorder(img, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        
        faces = app.get(img)
        
        if len(faces) == 0:
            false_negatives += 1
            continue
            
        enc = faces[0].embedding
        enc = enc / np.linalg.norm(enc)
        
        distances = np.linalg.norm(enrollment_encodings - enc, axis=1)
        
        predicted_id = "Unknown"
        if len(distances) > 0:
            best_idx = np.argmin(distances)
            if distances[best_idx] < DISTANCE_THRESHOLD:
                predicted_id = enrollment_ids[best_idx]
                
        t1 = time.time()
        total_latency += (t1 - t0)
                
        if predicted_id == true_id:
            correct += 1
        elif predicted_id == "Unknown":
            false_negatives += 1
        else:
            false_positives += 1
            
    avg_latency = (total_latency / len(test_images)) * 1000
    accuracy = correct / len(test_images)
    
    print("\n" + "="*40)
    print("EVALUATION RESULTS")
    print("="*40)
    print(f"Total Test Images: {len(test_images)}")
    print(f"True Positives (Correct): {correct}")
    print(f"False Positives (Wrong Match): {false_positives}")
    print(f"False Negatives (Unknown/No Face): {false_negatives}")
    print("-" * 40)
    print(f"Accuracy: {accuracy*100:.2f}%")
    print(f"Average Latency per Image: {avg_latency:.2f} ms")
    print("="*40)

if __name__ == "__main__":
    evaluate_model()
