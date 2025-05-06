console.log("Starting car control application");

// Connect to the WebSocket server
const socket = io();

// Control variables
let hasControl = false;
let countdownTimer = null;
let throttleValue = 0;
let turningValue = 0;

// Arrow key states
let arrowPressed = {
    up: false,
    down: false,
    right: false, 
    left: false
};

// DOM elements
const throttleSlider = document.getElementById('throttleSlider');
const turningSlider = document.getElementById('turningSlider');
const throttleValueDisplay = document.getElementById('throttleValue');
const turningValueDisplay = document.getElementById('turningValue');
const controlStatus = document.getElementById('controlStatus');
const timerDisplay = document.getElementById('timerDisplay');

// ============= Socket event handlers =============
socket.on("connect", () => {
    console.log("Connected to server");
});

socket.on("connect_error", (error) => {
    console.error("Connection error:", error.message);
    controlStatus.textContent = "Connection error";
    controlStatus.style.color = "red";
});

socket.on("timestart", () => {
    // Server notifies client it's their turn to control
    hasControl = true;
    controlStatus.textContent = "You have control!";
    controlStatus.style.color = "green";
    
    let timeLeft = 20; // seconds
    updateTimerDisplay(timeLeft);
    
    // Clear any existing timer
    if (countdownTimer) {
        clearInterval(countdownTimer);
    }
    
    // Start countdown
    countdownTimer = setInterval(() => {
        timeLeft--;
        updateTimerDisplay(timeLeft);
        
        if (timeLeft <= 0) {
            hasControl = false;
            clearInterval(countdownTimer);
            controlStatus.textContent = "Time's up! Waiting for next turn...";
            controlStatus.style.color = "red";
            
            // Reset sliders to center
            throttleSlider.value = 0;
            turningSlider.value = 0;
            updateSliderDisplays();
            
            // Tell server our time is over
            socket.emit("timeover", { message: "time_complete" });
            
            // Send stop command to ensure car stops
            sendCommand(0, 0);
        }
    }, 1000);
});

// ============= Helper functions =============
function updateTimerDisplay(seconds) {
    timerDisplay.textContent = seconds > 0 ? `${seconds} seconds` : "0 seconds";
}

function updateSliderDisplays() {
    throttleValueDisplay.textContent = throttleSlider.value;
    turningValueDisplay.textContent = turningSlider.value;
}

function sendCommand(throttle, turn) {
    // Only send commands if we have control
    if (!hasControl) return;
    
    // Convert numeric values to command strings for backwards compatibility
    let throttleCmd, turnCmd;
    
    // Throttle command
    if (throttle > 0) {
        throttleCmd = 'forward';
    } else if (throttle < 0) {
        throttleCmd = 'backward';
    } else {
        throttleCmd = 'stop';
    }
    
    // Turn command
    if (turn > 0) {
        turnCmd = 'right';
    } else if (turn < 0) {
        turnCmd = 'left';
    } else {
        turnCmd = 'none';
    }
    
    // Also send the numeric values for advanced control
    socket.emit("message", {
        throttle: throttleCmd,
        turn: turnCmd,
        throttleValue: throttle,
        turnValue: turn
    });
}

// Process keyboard inputs and update sliders accordingly
function processKeyboardInput() {
    // Calculate throttle based on up/down keys
    if (arrowPressed.up && !arrowPressed.down) {
        throttleValue = 100; // Full forward
    } else if (!arrowPressed.up && arrowPressed.down) {
        throttleValue = -100; // Full reverse
    } else {
        throttleValue = 0; // Stop
    }
    
    // Calculate turning based on left/right keys
    if (arrowPressed.left && !arrowPressed.right) {
        turningValue = -100; // Full left
    } else if (!arrowPressed.left && arrowPressed.right) {
        turningValue = 100; // Full right
    } else {
        turningValue = 0; // Straight
    }
    
    // Update sliders to match keyboard input
    throttleSlider.value = throttleValue;
    turningSlider.value = turningValue;
    updateSliderDisplays();
    
    // Send the command
    sendCommand(throttleValue, turningValue);
}

// ============= Event listeners =============
// Throttle slider event
throttleSlider.addEventListener('input', function() {
    if (hasControl) {
        throttleValue = parseInt(this.value);
        throttleValueDisplay.textContent = throttleValue;
        sendCommand(throttleValue, turningValue);
    }
});

// Turning slider event
turningSlider.addEventListener('input', function() {
    if (hasControl) {
        turningValue = parseInt(this.value);
        turningValueDisplay.textContent = turningValue;
        sendCommand(throttleValue, turningValue);
    }
});

// Key down event - for keyboard control
document.addEventListener("keydown", function(event) {
    if (!hasControl || event.repeat) return;
    
    switch(event.key) {
        case "ArrowUp":
            arrowPressed.up = true;
            break;
        case "ArrowDown":
            arrowPressed.down = true;
            break;
        case "ArrowLeft":
            arrowPressed.left = true;
            break;
        case "ArrowRight":
            arrowPressed.right = true;
            break;
    }
    
    processKeyboardInput();
});

// Key up event
document.addEventListener("keyup", function(event) {
    if (!hasControl) return;
    
    switch(event.key) {
        case "ArrowUp":
            arrowPressed.up = false;
            break;
        case "ArrowDown":
            arrowPressed.down = false;
            break;
        case "ArrowLeft":
            arrowPressed.left = false;
            break;
        case "ArrowRight":
            arrowPressed.right = false;
            break;
    }
    
    processKeyboardInput();
});

// Add touch events for mobile support
throttleSlider.addEventListener('touchmove', function(e) {
    e.preventDefault(); // Prevent scrolling while dragging
});

turningSlider.addEventListener('touchmove', function(e) {
    e.preventDefault(); // Prevent scrolling while dragging
});

// Initialize UI elements
updateSliderDisplays();