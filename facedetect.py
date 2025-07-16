import cv2
import numpy as np
import json
import os
import time
import threading
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity
import mediapipe as mp

# ======== Configuration ========
FACE_DB = "users.json"
BLINK_THRESHOLD = 0.21
CONSEC_FRAMES_BLINK = 3
FACE_MATCH_THRESHOLD = 0.65
LOGOUT_TIMER = 10  # seconds
BLINK_PROMPT_TIMER = 10  # seconds
CHECK_INTERVAL = 5  # seconds
HAND_GESTURE_TIME = 5  # seconds

# Mediapipe initialization
mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# ======== Helper Functions ========
def get_face_embedding(frame):
    try:
        result = DeepFace.represent(img_path=frame, model_name='Facenet', detector_backend='ssd')
        if result and result[0]['face_confidence'] > 0.85:
            return result[0]['embedding']
        return None
    except:
        return None

def face_similarity(embed1, embed2):
    return cosine_similarity([embed1], [embed2])[0][0]

# ======== Core Classes ========
class FaceAuthenticator:
    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.7)
        self.hands_detector = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        
    def get_eye_aspect_ratio(self, landmarks, eye_indices, frame_shape):
        h, w = frame_shape[:2]
        eye_points = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_indices]
        
        # Calculate vertical distances
        vert1 = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
        vert2 = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
        
        # Calculate horizontal distance
        horiz = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
        
        return (vert1 + vert2) / (2.0 * horiz) if horiz != 0 else 0.0

class AuthSystem:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.current_user = None
        self.last_check = time.time()
        self.last_blink = time.time()
        self.logout_timer = None
        self.blink_prompt_active = False
        self.security_active = True
        self.authenticator = FaceAuthenticator()
        self.hand_verified = False
        self.hand_verification_time = time.time()
        self.blink_counter = 0
        
        # Start security thread
        self.security_thread = threading.Thread(target=self.security_monitor)
        self.security_thread.start()

    def security_monitor(self):
        while self.security_active:
            if self.current_user:
                current_time = time.time()
                
                # Face check every 5 seconds
                if current_time - self.last_check >= CHECK_INTERVAL:
                    self.last_check = current_time
                    if not self.verify_current_user():
                        if not self.logout_timer:
                            self.logout_timer = current_time
                        elif current_time - self.logout_timer >= LOGOUT_TIMER:
                            self.handle_logout("User changed!")
                    else:
                        self.logout_timer = None
                
                # Blink check
                if current_time - self.last_blink >= BLINK_PROMPT_TIMER:
                    if not self.blink_prompt_active:
                        print("\n⚠️ Blink within 5 seconds!")
                        self.blink_prompt_active = True
                        self.prompt_start = current_time
                    elif current_time - self.prompt_start >= 5:
                        self.handle_logout("No blink detected!")
                
                # Hand gesture check
                if current_time - self.hand_verification_time >= HAND_GESTURE_TIME:
                    self.hand_verified = False
                
            time.sleep(1)

    def verify_current_user(self):
        ret, frame = self.cap.read()
        if not ret: return False
        
        cv2.imwrite("temp_current.jpg", frame)
        current_embed = get_face_embedding("temp_current.jpg")
        if not current_embed: return False
        
        with open(FACE_DB, 'r') as f:
            known_users = json.load(f)
            user_embed = known_users.get(self.current_user)
            if not user_embed: return False
            
            similarity = face_similarity(current_embed, user_embed)
            return similarity >= FACE_MATCH_THRESHOLD

    def handle_logout(self, reason):
        print(f"\n⚠️ {reason} Logging out...")
        self.current_user = None
        self.blink_prompt_active = False
        self.logout_timer = None
        self.hand_verified = False

    def signup(self):
        print("\n=== Signup Process ===")
    
        if not os.path.exists(FACE_DB):
            with open(FACE_DB, 'w') as f:
                json.dump({}, f)

        while True:
            username = input("Enter username: ").strip()
            with open(FACE_DB, "r") as f:
                users = json.load(f)
            if username in users:
                print("Username exists! Try again.")
            else:
                break

        print("Press 's' to capture face...")
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read from camera.")
                continue
            cv2.imshow("Signup - Press 's'", frame)
            if cv2.waitKey(1) & 0xFF == ord('s'):
                cv2.imwrite("temp_signup.jpg", frame)
                embedding = get_face_embedding("temp_signup.jpg")
                if embedding:
                    with open(FACE_DB, "r") as f:
                        users = json.load(f)
                    users[username] = embedding
                    with open(FACE_DB, "w") as f:
                        json.dump(users, f)
                    print("✅ Signup successful!")
                    break
                else:
                    print("❌ No face detected! Try again.")
        cv2.destroyAllWindows()


    def login(self):
        print("\n=== Login Process ===")

        if not os.path.exists(FACE_DB) or os.path.getsize(FACE_DB) == 0:
            print("No users found. Please signup first.")
            return False

        with open(FACE_DB, "r") as f:
            known_users = json.load(f)

        print("Press 'l' to capture face...")
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read from camera.")
                continue
            cv2.imshow("Login - Press 'l'", frame)
            if cv2.waitKey(1) & 0xFF == ord('l'):
                cv2.imwrite("temp_login.jpg", frame)
                login_embed = get_face_embedding("temp_login.jpg")
                if login_embed:
                    break
                else:
                    print("❌ No face detected! Try again.")
        cv2.destroyAllWindows()

        for user, embed in known_users.items():
            if face_similarity(login_embed, embed) >= FACE_MATCH_THRESHOLD:
                self.current_user = user
                self.last_blink = time.time()
                print(f"✅ Welcome {user}!")
                return True

        print("❌ Login failed! Face not recognized.")
        return False


    def continuous_auth(self):
        self.last_blink = time.time()
        self.hand_verification_time = time.time()
        
        while self.current_user:
            ret, frame = self.cap.read()
            if not ret: continue
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process face and hands
            face_results = self.authenticator.face_mesh.process(rgb_frame)
            hand_results = self.authenticator.hands_detector.process(rgb_frame)
            
            # Blink detection
            if face_results.multi_face_landmarks:
                landmarks = face_results.multi_face_landmarks[0].landmark
                
                left_ear = self.authenticator.get_eye_aspect_ratio(
                    landmarks, self.authenticator.LEFT_EYE, frame.shape)
                right_ear = self.authenticator.get_eye_aspect_ratio(
                    landmarks, self.authenticator.RIGHT_EYE, frame.shape)
                avg_ear = (left_ear + right_ear) / 2
                
                if avg_ear < BLINK_THRESHOLD:
                    self.blink_counter += 1
                else:
                    if self.blink_counter >= CONSEC_FRAMES_BLINK:
                        self.last_blink = time.time()
                        self.blink_prompt_active = False
                    self.blink_counter = 0

            # Hand gesture detection
            if hand_results.multi_hand_landmarks:
                self.hand_verified = True
                self.hand_verification_time = time.time()
                for hand_landmarks in hand_results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Display status
            cv2.putText(frame, f"User: {self.current_user}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Blink timer: {int(time.time() - self.last_blink)}s", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, "Hand verified" if self.hand_verified else "Show hand gesture",
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if self.hand_verified else (0, 0, 255), 2)
            
            cv2.imshow("Security Monitor", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.handle_logout("Manual logout")
                break

        cv2.destroyAllWindows()

# ======== Main Execution ========
if __name__ == "__main__":
    system = AuthSystem()
    
    try:
        while True:
            print("\n1. Signup\n2. Login\n3. Exit")
            choice = input("Choose option: ").strip()
            
            if choice == '1':
                system.signup()
            elif choice == '2':
                if system.login():
                    print(f"\n✅ Welcome {system.current_user}!")
                    system.continuous_auth()
                else:
                    print("\n❌ Login failed!")
            elif choice == '3':
                break
            else:
                print("Invalid choice!")
    finally:
        system.security_active = False
        system.cap.release()
        cv2.destroyAllWindows()
        if system.security_thread.is_alive():
            system.security_thread.join()
