from flask import Flask, render_template_string
from flask_socketio import SocketIO
import base64

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Camera Stream</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <h1>Pi Camera Live Stream</h1>
    <img id="stream" width="640" height="480"/>
    <script>
        const socket = io();
        const img = document.getElementById("stream");

        socket.on('video_frame', (data) => {
            img.src = 'data:image/jpeg;base64,' + data;
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('video_frame')
def handle_video_frame(data):
    socketio.emit('video_frame', data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug= True)
