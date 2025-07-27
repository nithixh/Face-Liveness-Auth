#Face-Liveness-Auth

A real-time biometric security system that ensures continuous user verification using:

- 🧠 Face recognition (DeepFace or OpenCV)
- 👁️ Blink detection (MediaPipe)
- ✋ Hand-raise gesture detection

This project supports two modes:
- `standalone_code/`: raw detection scripts for face and hand tracking
- `anti-cheat-quiz-demo/`: a Flask-based anti-cheat quiz app with webcam liveness checks

---

## 📂 Project Structure
Face-Liveness-Auth/
├── anti-cheat-quiz-demo/ # Flask web app
│ ├── static/ # JS, CSS
│ ├── templates/ # HTML templates
│ └── app.py # Main web app script
│
├── standalone_code/ # Standalone liveness detection logic
│ └── facedetect.py # Face + hand tracking
│
├── requirements.txt # Python dependencies
└── README.md # You're here :)

---

## 🚀 Demo Features (anti-cheat-quiz-demo)

- 🔐 User signup/login
- ✍️ Take a quiz after logging in
- 🖐️ Webcam-based hand-raise detection
- ⛔ Auto logout if hand isn’t detected
- 🧠 Simple session validation using `users.json`

---

## 🛠️ Tech Stack

- **Flask** – Web app framework
- **MediaPipe** – Hand detection
- **OpenCV** – Webcam access
- **Jinja2** – Dynamic templating
- **HTML/CSS/JS** – Frontend

## 🧪 Example Usage

- Register a new user on `/signup`
- Login to start the quiz
- During quiz, the system will ask you to raise your hand
- If no hand is detected, you'll be logged out as a possible cheater

---

## 📌 Notes

- This is a **work-in-progress demo**
- You can extend it with:
- Face recognition login
- Blink detection (add to `standalone_code/`)
- Full admin dashboard

---

### 🚧 Status: Work in Progress

> This is **not a fully completed application**. Some features are under development and may not work as intended. Planned features include better spoof detection, live video monitoring, and advanced exam control mechanisms.

---

## 📬 Author

Made with ❤️ by [nithixh](https://github.com/nithixh)

---



