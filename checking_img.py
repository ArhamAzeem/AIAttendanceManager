import os, cv2
for f in sorted(os.listdir("dataset/STU-008_wisam 2.0"))[:5]:
    img = cv2.imread(f"dataset/STU-008_wisam 2.0/{f}")
    print(f, img.shape if img is not None else "FAILED TO READ")

for folder in os.listdir("dataset"):
    path = f"dataset/{folder}"
    if os.path.isdir(path):
        print(folder, len(os.listdir(path)))