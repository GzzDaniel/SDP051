// Socket connection
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
});