from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
import cv2
import requests
from ultralytics import YOLO
from datetime import datetime
import os
import json
from geopy.geocoders import Nominatim
from telegram import Bot
from telegram.error import TelegramError

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['GOOGLE_MAPS_API_KEY'] = 'AIzaSyA4cu1uYO9RyxposmyaAUbpuEwBWJNkqrE'
app.config['TELEGRAM_BOT_TOKEN'] = '7339350903:AAHKHlNHiPr-J0U48IYde1oo7n-VxPjfLm0'
app.config['TELEGRAM_CHAT_ID'] = '1114081526'

# Initialize database
db = SQLAlchemy(app)

# Initialize Telegram bot
bot = Bot(token=app.config['TELEGRAM_BOT_TOKEN'])

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Fire detection model
try:
    model = YOLO("my_trained_model.pt")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

# ESP32-CAM stream
ESP32_STREAM_URL = "http://192.168.75.75:81/stream"

# In-memory fire event history
fire_events = []

# Location coordinates (replace with your actual coordinates)
LOCATION = {
    'latitude': 28.6139,  # Example: New Delhi coordinates
    'longitude': 77.2090
}

def send_telegram_alert():
    try:
        message = f"🔥 FIRE ALERT!\nLocation: https://www.google.com/maps?q={LOCATION['latitude']},{LOCATION['longitude']}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        bot.send_message(chat_id=app.config['TELEGRAM_CHAT_ID'], text=message)
    except TelegramError as e:
        print(f"Error sending Telegram alert: {e}")

def gen_frames():
    try:
        cap = cv2.VideoCapture(ESP32_STREAM_URL)
        if not cap.isOpened():
            print("Error: Could not open video stream")
            return

        fire_detected = False
        last_alert_time = None

        while True:
            success, frame = cap.read()
            if not success:
                print("Error: Could not read frame")
                break

            if model is not None:
                results = model(frame, imgsz=640)[0]
                detected = False

                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = f"{model.names[cls]} {conf:.2f}"

                    if model.names[cls].lower() == "fire":
                        detected = True
                        if not fire_detected:
                            fire_detected = True
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            fire_events.append(timestamp)
                            
                            current_time = datetime.now()
                            if last_alert_time is None or (current_time - last_alert_time).total_seconds() > 300:
                                send_telegram_alert()
                                last_alert_time = current_time

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                if not detected:
                    fire_detected = False

                if fire_detected:
                    cv2.putText(frame, "🔥 FIRE DETECTED!", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    except Exception as e:
        print(f"Error in gen_frames: {e}")
    finally:
        if 'cap' in locals():
            cap.release()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', 
                         fire_events=fire_events,
                         map_api_key=app.config['GOOGLE_MAPS_API_KEY'],
                         latitude=LOCATION['latitude'],
                         longitude=LOCATION['longitude'])

@app.route('/video_feed')
def video_feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera_status')
def camera_status():
    try:
        r = requests.get(ESP32_STREAM_URL, timeout=2)
        if r.status_code == 200:
            return {"status": "online"}
    except:
        pass
    return {"status": "offline"}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
        else:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Signup successful. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
