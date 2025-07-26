#Face-Liveness-Auth

This project is a real-time biometric security system using:
- Face recognition (with DeepFace)
- Blink detection (using Mediapipe)
- Hand gesture verification

It monitors user presence and ensures the logged-in user is the real user.

## ✨ Features
- Face-based signup & login
- Live blink detection to avoid spoofing
- Hand gesture verification
- Auto logout if face changes or no blink detected
- Uses threading to monitor security continuously

## 📦 Dependencies
- OpenCV
- Numpy
- DeepFace
- Mediapipe
- scikit-learn

Install with:
```bash
pip install opencv-python numpy deepface mediapipe scikit-learn
