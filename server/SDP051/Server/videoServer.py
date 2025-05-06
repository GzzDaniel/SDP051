
from flask import Flask, Response
import socket
import threading

# =^._.^= UDP + Flask MJPEG Server nya~!
app = Flask(__name__)

# Settings
UDP_IP = "0.0.0.0"
UDP_PORT = 5000
HTTP_PORT = 3000
latest_frame = b""  # Holds the latest JPEG frame nya~


def udp_receiver():
    global latest_frame
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"🐾 Listening for MJPEG on UDP {UDP_IP}:{UDP_PORT} nya~!")

    while True:
        data, _ = sock.recvfrom(65536)
        # Only accept full JPEG frames nya~! (^･ω･^=)
        if data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9'):
            latest_frame = data

# 🍙 MJPEG streaming route!
@app.route("/")
def video_feed():
    def generate():
        while True:
            if latest_frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" +
                       latest_frame + b"\r\n")
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>NyaaCam MJPEG~!</title></head>
    <body style="text-align:center; background:#111;">
        <h1 style="color:white;">Live MJPEG Stream</h1>
        <img src="/video" width="640" height="480" 
             style="border:5px solid pink; border-radius:12px;">
    </body>
    </html>
    """

if __name__ == "__main__":
    #threading.Thread(target=udp_receiver, daemon=True).start()
    print(f"server ready at http://localhost:{HTTP_PORT}")
    app.run(host="0.0.0.0", port=HTTP_PORT, debug=True)
