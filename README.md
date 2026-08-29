# Campus AI Attendance Manager

Campus AI uses a webcam and InsightFace face embeddings to record student attendance. It includes student enrollment, live check-in/check-out, attendance reports, and irregular-attendance email alerts.

## Requirements

- Python 3.8 or newer
- MongoDB running on `localhost:27017`
- A working webcam

## Install

Open a terminal in this folder and run:

```bash
python -m venv .venv
```

Activate the environment.

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Install the packages:

```bash
pip install -r requirements.txt
```

## Run

Start MongoDB, then run:

```bash
streamlit run app.py
```

Open the URL shown in the terminal, usually `http://localhost:8501`.

The first face scan may take longer while the InsightFace `buffalo_l` model is prepared.

## Use the App

1. Open **Student Directory**.
2. Select **Register New Profile**, enter the student's name, and click **Capture Biometrics**. The app captures 30 face images and updates embeddings automatically.
3. Open **Live Attendance**, click **Activate scanner**, and have the student look at the camera.
4. Check **Overview** for today's presence and attendance activity.
5. Check **Reports** for attendance percentages, trends, irregular students, and CSV export.

Use **AI Training Center** to rebuild embeddings after manually changing files in the `dataset` folder.

## Important Files

- `dataset/` — captured student face images
- `models/embeddings.pkl` — generated face embeddings
- `config.json` — face-match distance threshold; default is `1.0`
- `blog_post.md` — project explanation for submission

## Troubleshooting

- **MongoDB error:** Make sure MongoDB is running on `localhost:27017`.
- **Camera error:** Close other apps using the webcam and check camera permissions.
- **Embeddings not found:** Register a student or click **Update Face Embeddings** in **AI Training Center**.

For biometric data, use consent, restricted access, and demo data when presenting the project.
