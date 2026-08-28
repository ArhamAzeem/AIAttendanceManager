import os
import urllib.request

def download_file(url, save_path):
    if not os.path.exists(save_path):
        print(f"Downloading {os.path.basename(save_path)}...")
        urllib.request.urlretrieve(url, save_path)
        print("Download complete.")
    else:
        print(f"{os.path.basename(save_path)} already exists.")

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    
    # OpenCV DNN face detection model
    prototxt_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
    caffemodel_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel"
    
    download_file(prototxt_url, "models/deploy.prototxt")
    download_file(caffemodel_url, "models/res10_300x300_ssd_iter_140000.caffemodel")
    
    print("OpenCV DNN models setup successfully.")
