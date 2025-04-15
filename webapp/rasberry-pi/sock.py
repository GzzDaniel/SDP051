import socketio

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to Flask server")
    sio.emit("identify", {"user_agent": "Pi"})

@sio.event
def disconnect():
    print("Disconnected from Flask server")

@sio.event
def pi_command(data):
    print(f"Received command: {data}")
    
    if data == "UP pressed":
        print("Moving forward")
    elif data == "DOWN pressed":
        print("Moving backward")
    elif data == "LEFT pressed":
        print("Turning left")
    elif data == "RIGHT pressed":
        print("Turning right")
    elif data == "UP released" or data == "DOWN released" or data == "LEFT released" or data == "RIGHT released":
        print("Stopping")

try:
    sio.connect('http://32.219.174.238:4000')
except Exception as e:
    print(f"Failed to connect to Flask server: {e}")

sio.wait()