from flask import Flask, render_template, request, redirect, url_for, session
import random
import json
import base64
import os
from datetime import datetime
import numpy as np
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity
import tempfile

app = Flask(__name__)
app.secret_key = 'demo_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4 MB limit

USERS_DB = 'users.json'

QUESTIONS = [
    {"q": "What is 2 + 2?", "a": "4", "options": ["3", "4", "5", "6"]},
    {"q": "Capital of France?", "a": "Paris", "options": ["Berlin", "London", "Paris", "Rome"]},
    {"q": "Largest planet?", "a": "Jupiter", "options": ["Mars", "Jupiter", "Earth", "Venus"]},
    {"q": "Who wrote Hamlet?", "a": "Shakespeare", "options": ["Dickens", "Shakespeare", "Hemingway", "Austen"]},
    {"q": "5 x 6 = ?", "a": "30", "options": ["30", "36", "35", "25"]},
    {"q": "Fastest land animal?", "a": "Cheetah", "options": ["Lion", "Tiger", "Cheetah", "Horse"]},
    {"q": "H2O is?", "a": "Water", "options": ["Oxygen", "Hydrogen", "Water", "Salt"]},
    {"q": "Square root of 16?", "a": "4", "options": ["2", "4", "8", "16"]},
    {"q": "Sun rises in the?", "a": "East", "options": ["West", "North", "East", "South"]},
    {"q": "Color of the sky?", "a": "Blue", "options": ["Green", "Blue", "Red", "Yellow"]}
]

@app.route('/')
def index():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    # Create a list of (index, question) pairs
    indexed_questions = list(enumerate(QUESTIONS))

    return render_template('quiz.html', questions=indexed_questions, username=session['username'])

@app.route('/submit', methods=['POST'])
def submit():
    if not session.get('username'):
        return redirect(url_for('login'))
    answers = [request.form.get(f'q{i}') for i in range(10)]
    score = sum(1 for i, ans in enumerate(answers) if ans == QUESTIONS[i]["a"])
    return render_template('result.html', score=score, username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return render_template('logout.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        face_image = request.form['face_image']
        if not username or not face_image:
            return render_template('signup.html', error='Username and face required')
        # Load users
        if os.path.exists(USERS_DB):
            try:
                with open(USERS_DB, 'r') as f:
                    users = json.load(f)
            except Exception:
                users = {}
        else:
            users = {}
        if username in users:
            return render_template('signup.html', error='Username already exists')
        # Decode and save image temporarily
        try:
            img_data = base64.b64decode(face_image.split(',')[1])
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_img:
                temp_img.write(img_data)
                temp_img_path = temp_img.name
            # Get embedding
            embedding_objs = DeepFace.represent(img_path=temp_img_path, model_name='Facenet')
            if not embedding_objs or (isinstance(embedding_objs, list) and not embedding_objs[0].get("embedding")):
                os.remove(temp_img_path)
                return render_template('signup.html', error='Face not detected. Please try again with a clear face image.')
            if isinstance(embedding_objs, list):
                embedding = embedding_objs[0]["embedding"]
            else:
                embedding = embedding_objs["embedding"]
            users[username] = embedding
            with open(USERS_DB, 'w') as f:
                json.dump(users, f)
            os.remove(temp_img_path)
            return redirect(url_for('login'))
        except Exception as e:
            return render_template('signup.html', error=f'Face embedding failed: {str(e)}')
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        face_image = request.form['face_image']
        if not username or not face_image:
            error = 'Username and face required'
        else:
            # Load users
            if os.path.exists(USERS_DB):
                with open(USERS_DB, 'r') as f:
                    users = json.load(f)
            else:
                users = {}
            if username not in users:
                error = 'User does not exist'
            else:
                try:
                    img_data = base64.b64decode(face_image.split(',')[1])
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_img:
                        temp_img.write(img_data)
                        temp_img_path = temp_img.name
                    embedding_objs = DeepFace.represent(img_path=temp_img_path, model_name='Facenet')
                    if isinstance(embedding_objs, list):
                        embedding = embedding_objs[0]["embedding"]
                    else:
                        embedding = embedding_objs["embedding"]
                    stored_embedding = np.array(users[username]).reshape(1, -1)
                    input_embedding = np.array(embedding).reshape(1, -1)
                    similarity = cosine_similarity(stored_embedding, input_embedding)[0][0]
                    os.remove(temp_img_path)
                    if similarity > 0.45:  # Threshold, tune as needed
                        session['username'] = username
                        return redirect(url_for('index'))
                    else:
                        error = f'Face does not match (similarity={similarity:.2f}). Try again.'
                except Exception as e:
                    error = f'Face recognition failed: {str(e)}'
    return render_template('login.html', error=error)


if __name__ == '__main__':
    app.run(debug=True)
