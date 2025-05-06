import socketio
import time
import base64
import cv2
from picamera2 import Picamera2

sio = socketio.Client()

def connect():
    while True:
        try:
            sio.connect("http://32.219.174.238:5000/")
            print("Connected to server!")
            break
        except Exception as e:
            print("Connection failed. Retrying in 3 seconds...")
            time.sleep(3)

connect()

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
picam2.start()

while True:
    frame = picam2.capture_array()
    _, buffer = cv2.imencode('.jpg', frame)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    if sio.connected:
        try:
            sio.emit('video_frame', jpg_as_text)
        except Exception as e:
            print("Lost connection. Reconnecting...")
            connect()
    time.sleep(0.05)
