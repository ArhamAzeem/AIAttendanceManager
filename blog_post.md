# Building a Smart Attendance System with Facial Recognition

Traditional attendance tracking in classrooms is often slow and prone to errors. To solve this, I built the "AI Attendance Manager," a system that uses facial recognition to automatically log when students enter and leave a classroom. This project was developed as part of the AI and Machine Learning Mania competition.

Here is a breakdown of how the system was built and how it works.

## The Problem
The goal was to create an automated system to replace manual attendance marking. It needed to:
1. Capture video from a webcam.
2. Detect faces in real-time.
3. Process those faces for a neural network.
4. Train a Convolutional Neural Network (CNN) to recognize registered students.
5. Log attendance (In-Time and Out-Time) into a database.

## Technology Stack
- **Frontend:** Streamlit (Python) for the user interface.
- **Computer Vision:** OpenCV for webcam feed and face detection using Haar Cascades.
- **Machine Learning:** Keras with TensorFlow backend to build and train the CNN.
- **Database:** MongoDB to store student profiles and attendance records.

## Step 1: Data Collection
To train a facial recognition model, you first need data. I created a script using OpenCV that opens the webcam and detects faces using a Haar Cascade classifier (`haarcascade_frontalface_default.xml`). 

When a new student is registered, the system isolates their face from the video feed, converts it to grayscale, and resizes it to 128x128 pixels. It automatically captures 100 frames of the student's face to create a diverse dataset for that specific person. These images are saved locally in a `dataset/<student_id>_<student_name>/` directory.

## Step 2: Building and Training the CNN
Once the images are collected, they are used to train a custom Convolutional Neural Network (CNN). Facial recognition is treated as an image classification problem where the model learns the unique features of each student's face.

The CNN architecture includes:
- **Input Layer:** Takes the 128x128 grayscale images.
- **Convolutional Layers:** Two layers with 32 and 64 filters to extract facial features like edges and shapes.
- **Max Pooling Layers:** To reduce the spatial dimensions and computational load.
- **Dense Layers:** A fully connected layer with 128 neurons, followed by a Dropout layer to prevent overfitting.
- **Output Layer:** A Softmax layer that classifies the face into one of the registered student IDs.

The model is compiled using the Adam optimizer and trained over 10 epochs. After training, the model is saved as an `.h5` file.

## Step 3: Real-Time Face Recognition
During an attendance session, the system continuously reads frames from the webcam. It runs the same pre-processing steps used during training (detect face, convert to grayscale, resize). 

The processed face is passed to the trained CNN's `predict()` function. If the model is confident in its prediction (above a certain threshold), it identifies the student.

## Step 4: Logging Attendance
To track how long a student stays in class, I used MongoDB to implement a simple logic flow:
- **In-Time:** When the system first recognizes a student on a given day, it creates a new record in the database and logs the current time as their `in_time`.
- **Out-Time:** If the system recognizes the same student again later that day, it updates their `out_time`. Since the camera is always running, the last time a student is seen before the session ends becomes their final `out_time`.

## Step 5: The Interface
I used Streamlit to build a simple dashboard. The app has a sidebar with four main sections:
1. **Dashboard:** A view of the MongoDB database showing attendance logs, filterable by date.
2. **Register Student:** An interface to input a student's ID and name, which starts the 100-image capture process.
3. **Train Model:** A button to trigger the CNN training on the newly collected dataset.
4. **Take Attendance:** A screen that opens the webcam and starts the live recognition and logging process.

## Conclusion
This project demonstrates how combining computer vision, deep learning, and a simple web framework can solve a real administrative problem. By automating attendance, the system saves time and prevents manual errors or proxy attendance.
