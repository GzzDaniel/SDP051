from flask import Flask, request, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from time import time
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow connections from any origin

# Directory for static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# Ensure directories exist
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Create the HTML file in the templates directory
with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RC Car Controller</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.4.1/socket.io.min.js"></script>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="container">
        <h1>RC Car Controller</h1>
        
        <div id="statusDisplay" class="status">
            Connecting to server...
        </div>
        
        <div id="timer" class="timer">
            Waiting for control...
        </div>
        
        <div class="controls-layout">
            <div class="slider-container">
                <span class="slider-label">Forward/Backward</span>
                <input type="range" id="throttleSlider" class="slider vertical-slider" min="-100" max="100" value="0" orient="vertical">
                <div id="throttleValue">0%</div>
            </div>
            
            <div class="slider-container">
                <span class="slider-label">Left/Right</span>
                <input type="range" id="steeringSlider" class="slider" min="-100" max="100" value="0">
                <div id="steeringValue">0%</div>
            </div>
        </div>
        
        <!-- Video stream (uncomment and update IP if available) -->
        <!-- <div class="video-container">
            <img src="http://YOUR_PI_IP:8000/stream.mjpg" class="video-stream" alt="Video Stream">
        </div> -->
    </div>
    <script src="/static/controller.js"></script>
</body>
</html>''')

# Create the CSS file in the static directory
with open(os.path.join(static_dir, 'styles.css'), 'w') as f:
    f.write('''body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: #f5f5f5;
}

.container {
    width: 100%;
    max-width: 500px;
    background-color: #fff;
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

h1 {
    text-align: center;
    color: #333;
}

.status {
    text-align: center;
    margin: 10px 0;
    padding: 8px;
    background-color: #e0e0e0;
    border-radius: 5px;
}

.control-section {
    margin: 20px 0;
}

.slider-container {
    margin: 40px 0;
    text-align: center;
}

.slider-label {
    display: block;
    margin-bottom: 10px;
    font-weight: bold;
}

.slider {
    width: 90%;
    margin: 10px auto;
    display: block;
}

.vertical-slider {
    height: 200px;
    writing-mode: bt-lr; /* IE */
    -webkit-appearance: slider-vertical; /* WebKit */
    width: 60px;
}

.controls-layout {
    display: flex;
    justify-content: space-around;
    margin-top: 40px;
}

.timer {
    margin: 20px 0;
    text-align: center;
    font-size: 1.2em;
    font-weight: bold;
}

.video-container {
    width: 100%;
    margin-top: 20px;
    text-align: center;
}

.video-stream {
    max-width: 100%;
    border-radius: 10px;
}''')

# Create the JavaScript file in the static directory
with open(os.path.join(static_dir, 'controller.js'), 'w') as f:
    f.write('''// Socket connection
const socket = io();
const statusDisplay = document.getElementById('statusDisplay');
const timer = document.getElementById('timer');
const throttleSlider = document.getElementById('throttleSlider');
const steeringSlider = document.getElementById('steeringSlider');
const throttleValue = document.getElementById('throttleValue');
const steeringValue = document.getElementById('steeringValue');

let hasControl = false;
let countdownInterval;

// Connect to server
socket.on("connect", () => {
    statusDisplay.textContent = "Connected to server";
    statusDisplay.style.backgroundColor = "#d0ffd0";
});

socket.on("connect_error", (error) => {
    statusDisplay.textContent = "Connection error: " + error.message;
    statusDisplay.style.backgroundColor = "#ffd0d0";
});

socket.on("timestart", () => {
    hasControl = true;
    statusDisplay.textContent = "You have control!";
    statusDisplay.style.backgroundColor = "#d0ffd0";
    
    let timeLeft = 20; // seconds
    timer.textContent = `Time left: ${timeLeft} seconds`;
    
    // Enable controls
    throttleSlider.disabled = false;
    steeringSlider.disabled = false;
    
    countdownInterval = setInterval(() => {
        timeLeft--;
        timer.textContent = `Time left: ${timeLeft} seconds`;
        
        if (timeLeft <= 0) {
            hasControl = false;
            clearInterval(countdownInterval);
            timer.textContent = "Time's up! Waiting for next turn...";
            
            // Disable controls and reset sliders
            throttleSlider.disabled = true;
            steeringSlider.disabled = true;
            throttleSlider.value = 0;
            steeringSlider.value = 0;
            throttleValue.textContent = "0%";
            steeringValue.textContent = "0%";
            
            // Send stop command
            sendControlCommand(0, 0);
            
            // Notify server
            socket.emit("timeover", { message: "ack" });
        }
    }, 1000);
});

// Initially disable sliders until user gets control
throttleSlider.disabled = true;
steeringSlider.disabled = true;

// Function to send control commands
function sendControlCommand(throttleVal, steeringVal) {
    if (!hasControl) return;
    
    // Convert slider values to control commands
    let throttle, turn;
    
    // Throttle logic (vertical slider)
    if (throttleVal > 0) {
        throttle = "forward";
    } else if (throttleVal < 0) {
        throttle = "backward";
    } else {
        throttle = "stop";
    }
    
    // Steering logic (horizontal slider)
    if (steeringVal > 0) {
        turn = "right";
    } else if (steeringVal < 0) {
        turn = "left";
    } else {
        turn = "none";
    }
    
    // Send as an object with percentage values for gradual control
    socket.emit("message", {
        throttle,
        turn,
        throttle_percent: Math.abs(throttleVal),
        turn_percent: Math.abs(steeringVal)
    });
    
    console.log(`Sending: throttle=${throttle} (${throttleVal}%), turn=${turn} (${steeringVal}%)`);
}

// Throttle slider listener
throttleSlider.addEventListener("input", function() {
    const value = parseInt(this.value);
    throttleValue.textContent = `${value}%`;
    sendControlCommand(value, parseInt(steeringSlider.value));
});

// Steering slider listener
steeringSlider.addEventListener("input", function() {
    const value = parseInt(this.value);
    steeringValue.textContent = `${value}%`;
    sendControlCommand(parseInt(throttleSlider.value), value);
});

// Auto-center steering when released
steeringSlider.addEventListener("mouseup", function() {
    this.value = 0;
    steeringValue.textContent = "0%";
    sendControlCommand(parseInt(throttleSlider.value), 0);
});

// Handle keyboard arrows as alternative controls
document.addEventListener("keydown", function(event) {
    if (!hasControl || event.repeat) return;
    
    switch(event.key) {
        case "ArrowUp":
            throttleSlider.value = 100;
            throttleValue.textContent = "100%";
            break;
        case "ArrowDown":
            throttleSlider.value = -100;
            throttleValue.textContent = "-100%";
            break;
        case "ArrowLeft":
            steeringSlider.value = -100;
            steeringValue.textContent = "-100%";
            break;
        case "ArrowRight":
            steeringSlider.value = 100;
            steeringValue.textContent = "100%";
            break;
    }
    
    sendControlCommand(parseInt(throttleSlider.value), parseInt(steeringSlider.value));
});

document.addEventListener("keyup", function(event) {
    if (!hasControl) return;
    
    switch(event.key) {
        case "ArrowUp":
        case "ArrowDown":
            throttleSlider.value = 0;
            throttleValue.textContent = "0%";
            break;
        case "ArrowLeft":
        case "ArrowRight":
            steeringSlider.value = 0;
            steeringValue.textContent = "0%";
            break;
    }
    
    sendControlCommand(parseInt(throttleSlider.value), parseInt(steeringSlider.value));
});''')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(static_dir, path)

# ______________ user queue _______________
class UserQueue:
    '''manages the active users to give sequential control of the car, NOTIFIES users through socket communication'''
    def __init__(self):
        self.queue = []  
        self.idx = None  # index that points to the session id of the host in control of the car
        
    def activateCurrentUser(self):
        print("current index: ", self.idx)
        emit('timestart', to=self.queue[self.idx])
        print("notification sent to", self.queue[self.idx])
        self.printInfo()
    
    def nextUser(self):
        '''goes to the next user and notifies them'''
        self.idx += 1
        if self.idx >= len(self.queue):
            # loop back to the start of the queue
            print("index went back to start of queue")
            self.idx = 0
            
        self.activateCurrentUser()
            
    def addUser(self, sessionID):
        '''usage: sessionID = request.id | Adds user's session id to the queue, notifies them if conditions are met'''
        self.queue.append(sessionID)  # add to session id to queue
    
        if self.idx is None:
            self.idx = len(self.queue)-1
            self.activateCurrentUser()
            
        print("New Client connected:", request.sid) 
        
    def removeUser(self, sessionID):
        '''usage: sessionID = request.id | removes by their session id, notifies new user if conditions are met'''
        if sessionID not in self.queue:
            return
            
        # Check if the current user is being removed
        current_user_idx = self.queue.index(sessionID)
        is_current_user = (self.idx == current_user_idx)
        
        # Remove user from queue
        self.queue.remove(sessionID)
        print("Client disconnected:", sessionID)
        
        if len(self.queue) <= 0:  # if list is empty
            self.idx = None
            return
            
        # Adjust the index if necessary
        if is_current_user:
            # If the current user disconnected, move to next user
            if self.idx >= len(self.queue):
                self.idx = 0
            self.activateCurrentUser()
        elif current_user_idx < self.idx:
            # If a user before the current user disconnected, adjust index
            self.idx -= 1
        
    def printInfo(self):
        '''prints relevant info in the python terminal'''
        print("active users: ", self.queue)
        if self.idx is not None and self.queue:
            print("user with control: ", self.queue[self.idx])
        else:
            print("user with control: NONE")
    

#_______________ socketio events_____________________
# When a new client connects
pi_sid = None  # stores raspberry pi session id

userqueue = UserQueue()

@socketio.on("connect")
def handle_connect():
    global pi_sid
    userqueue.addUser(request.sid)
    userqueue.printInfo()
    
@socketio.on("disconnect")
def handle_disconnect():
    userqueue.removeUser(request.sid)
    userqueue.printInfo()
    
# clients will notify server when their turn is over
@socketio.on("timeover")
def handle_timeover(data):
    print("time ended for: ", request.sid)
    userqueue.nextUser()

@socketio.on("identify")
def handle_identify(data):
    global pi_sid
    if data.get("user_agent") == "Pi":
        pi_sid = request.sid
        print("Pi connected:", pi_sid)

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    if pi_sid:
        emit('pi_command', data, to=pi_sid)
    
if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=4000, debug=True)