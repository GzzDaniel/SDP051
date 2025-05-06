// UI elements
const statusDisplay = document.getElementById('statusDisplay');
const countdown = document.getElementById('countdown');
const throttleValue = document.getElementById('throttleValue');
const steeringValue = document.getElementById('steeringValue');
const debugInfo = document.getElementById('debugInfo');

// Control areas and indicators
const throttleArea = document.getElementById('throttleArea');
const steeringArea = document.getElementById('steeringArea');
const throttleIndicator = document.getElementById('throttleIndicator');
const steeringIndicator = document.getElementById('steeringIndicator');
const joystick = document.getElementById('joystick');
const joystickIndicator = document.getElementById('joystickIndicator');

// Tabs and control methods
const tabs = document.querySelectorAll('.tab');
const controlMethods = document.querySelectorAll('.control-method');

// Control state
let hasControl = false;
let countdownInterval;
let throttlePercent = 0;
let steeringPercent = 0;
let activeMethod = 'bars';

let prevT = 0;
let prevS = 0;

// Touch tracking for the bars method
// Store touch data with identifier, element and position
let activeTouches = [];

// Touch tracking for the joystick method
let joystickTracking = false;
let joystickTouchId = null;


// Logging helper function
function log(message) {
    console.log(message);
    debugInfo.innerHTML = message + '<br>' + debugInfo.innerHTML;
    if (debugInfo.innerHTML.split('<br>').length > 10) {
        debugInfo.innerHTML = debugInfo.innerHTML.split('<br>').slice(0, 10).join('<br>');
    }
}


statusDisplay.textContent = `Connecting `;

// Create new socket with explicit transport preferences
const socket = io("https://sdp051car.com", {
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    timeout: 10000,
    // Try polling first as websocket is failing
    //transports: ['polling', 'websocket']
});

// Connection events
socket.on('connect', () => {
    log(`Connected! SocketID: ${socket.id}`);
    statusDisplay.textContent = 'Connected. Waiting for turn...';
    statusDisplay.style.backgroundColor = '#d0ffd0';
    
    // Request to be added to the control queue
    socket.emit('userRequestAdd', { message: 'request control' });
});

socket.on('controlOff', () => {
    endControl();
});


socket.on('connect_error', (error) => {
    log(`Connection error: ${error.message}`);
    statusDisplay.textContent = `Connection error: ${error.message}`;
    statusDisplay.style.backgroundColor = '#ffd0d0';
});

socket.on('reconnect_attempt', (attemptNumber) => {
    log(`Reconnection attempt #${attemptNumber}`);
});

socket.on('disconnect', (reason) => {
    log(`Disconnected: ${reason}`);
    statusDisplay.textContent = `Disconnected: ${reason}`;
    statusDisplay.style.backgroundColor = '#ffddaa';
    
    if (hasControl) {
        endControl();
    }
});

// Control events
socket.on('timestart', (timeAllowed) => {
    log(`Control granted! Time: ${timeAllowed}s`);
    hasControl = true;
    statusDisplay.textContent = 'You have control!';
    statusDisplay.style.backgroundColor = '#d0ffd0';
    
    // Start timer
    let timeLeft = timeAllowed;
    countdown.textContent = timeLeft;
    
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    
    countdownInterval = setInterval(() => {
        timeLeft--;
        countdown.textContent = timeLeft;
        socket.emit('timeleft', { message: timeLeft });
        
        if (timeLeft <= 0) {
            endControl();
        }
    }, 1000);
});


// Tab switching
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        // Reset controls
        resetControls();
        sendControlCommand(0, 0);
        
        // Set active tab
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Set active method
        activeMethod = tab.dataset.method;
        controlMethods.forEach(method => {
            method.classList.remove('active');
        });
        document.getElementById(`${activeMethod}Method`).classList.add('active');
    });
});

function endControl() {
    // Stop the car
    sendControlCommand(0, 0);

    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
    
    // Reset controls
    resetControls();
    hasControl = false;
    
    // Update UI
    statusDisplay.textContent = 'Your turn ended. Waiting...';
    statusDisplay.style.backgroundColor = '#e0e0e0';
    countdown.textContent = 'wait';
    
    // Notify server

    socket.emit('timeover', { message: 'control ended' });
    
}

function resetControls() {
    // Reset all indicators
    throttleIndicator.style.top = '50%';
    steeringIndicator.style.left = '50%';
    joystickIndicator.style.transform = 'translate(-50%, -50%)';
    
    // Reset control values
    throttlePercent = 0;
    steeringPercent = 0;
    
    // Reset touch tracking
    activeTouches = [];
    joystickTracking = false;
    joystickTouchId = null;
    
    // Update displays
    throttleValue.textContent = '0%';
    steeringValue.textContent = '0%';
}

// Function to send control commands
function sendControlCommand(throttleVal, steeringVal) {
    if (!hasControl) return;

    let roundedT = Math.round(throttleVal / 5) * 5
    let roundedS = Math.round(steeringVal / 5) * 5

    if ( (roundedT == prevT) && (roundedS == prevS)) return;

    prevT = roundedT;
    prevS = roundedS;
   
    // Send command to server with percentage values
    socket.emit('controlData', {t: roundedT, s: roundedS});
}

// Find touch in active touches array
function findTouchIndex(id) {
    for (let i = 0; i < activeTouches.length; i++) {
        if (activeTouches[i].id === id) {
            return i;
        }
    }
    return -1;
}

// ===== BARS CONTROL FUNCTIONS =====

// Update throttle control
function updateThrottle(clientY) {
    if (!hasControl || activeMethod !== 'bars') return;
    
    const rect = throttleArea.getBoundingClientRect();
    const areaHeight = rect.height;
    const areaCenter = rect.top + areaHeight / 2;
    
    // Calculate distance from center (negative is up/forward, positive is down/backward)
    let distanceFromCenter = clientY - areaCenter;
    
    // Limit to boundaries
    const maxDistance = areaHeight / 2 -20;
    distanceFromCenter = Math.max(-maxDistance, Math.min(maxDistance, distanceFromCenter));
    
    // Calculate percent (-100 to 100)
    throttlePercent = -Math.round((distanceFromCenter / maxDistance) * 100);
    
    // Position indicator
    const newTop = 50 + (distanceFromCenter / maxDistance) * 50;
    throttleIndicator.style.top = `${newTop}%`;
    
    // Update display
    throttleValue.textContent = `${throttlePercent}%`;
    
    // Send command
    // TODO send control command only if it is different
    sendControlCommand(throttlePercent, steeringPercent);
}

// Update steering control
function updateSteering(clientX) {
    if (!hasControl || activeMethod !== 'bars') return;
    
    const rect = steeringArea.getBoundingClientRect();
    const areaWidth = rect.width;
    const areaCenter = rect.left + areaWidth / 2;
    
    // Calculate distance from center (negative is left, positive is right)
    let distanceFromCenter = clientX - areaCenter;
    
    // Limit to boundaries
    const maxDistance = areaWidth / 2 - 20;
    distanceFromCenter = Math.max(-maxDistance, Math.min(maxDistance, distanceFromCenter));
    
    // Calculate percent (-100 to 100)
    steeringPercent = Math.round((distanceFromCenter / maxDistance) * 100);
    
    // Position indicator
    const newLeft = 50 + (distanceFromCenter / maxDistance) * 50;
    steeringIndicator.style.left = `${newLeft}%`;
    
    // Update display
    steeringValue.textContent = `${steeringPercent}%`;
    
    

    // Send command
    // TODO send control command only if it is different
    sendControlCommand(throttlePercent, steeringPercent);
}

// ===== JOYSTICK CONTROL FUNCTION =====

// Update joystick control
function updateJoystick(clientX, clientY) {
    if (!hasControl || activeMethod !== 'joystick') return;
    
    const rect = joystick.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    // Calculate distance from center
    let deltaX = clientX - centerX;
    let deltaY = clientY - centerY;
    
    // Limit to circular boundary
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    const maxDistance = rect.width / 2 - 25; // Joystick radius minus handle radius
    
    if (distance > maxDistance) {
        const angle = Math.atan2(deltaY, deltaX);
        deltaX = Math.cos(angle) * maxDistance;
        deltaY = Math.sin(angle) * maxDistance;
    }
    
    // Position joystick indicator
    joystickIndicator.style.transform = `translate(calc(-50% + ${deltaX}px), calc(-50% + ${deltaY}px))`;
    
    // Calculate control percentages (-100 to 100)
    steeringPercent = Math.round((deltaX / maxDistance) * 100);
    throttlePercent = -Math.round((deltaY / maxDistance) * 100);
    
    // Update displays
    throttleValue.textContent = `${throttlePercent}%`;
    steeringValue.textContent = `${steeringPercent}%`;
    
    // Send command
    sendControlCommand(throttlePercent, steeringPercent);
}

// ===== TOUCH EVENT HANDLERS =====

// Throttle area touch start
throttleArea.addEventListener('touchstart', (e) => {
    if (!hasControl || activeMethod !== 'bars') return;
    e.preventDefault();
    
    // Get the touch
    const touch = e.changedTouches[0];
    
    // Add to active touches
    activeTouches.push({
        id: touch.identifier,
        element: 'throttle',
        initialY: touch.clientY
    });
    
    // Update control
    updateThrottle(touch.clientY);
}, { passive: false });

// Steering area touch start
steeringArea.addEventListener('touchstart', (e) => {
    if (!hasControl || activeMethod !== 'bars') return;
    e.preventDefault();
    
    // Get the touch
    const touch = e.changedTouches[0];
    
    // Add to active touches
    activeTouches.push({
        id: touch.identifier,
        element: 'steering',
        initialX: touch.clientX
    });
    
    // Update control
    updateSteering(touch.clientX);
}, { passive: false });

// Joystick touch start
joystick.addEventListener('touchstart', (e) => {
    if (!hasControl || activeMethod !== 'joystick') return;
    e.preventDefault();
    
    // Only track first touch on joystick
    if (!joystickTracking) {
        const touch = e.changedTouches[0];
        joystickTracking = true;
        joystickTouchId = touch.identifier;
        updateJoystick(touch.clientX, touch.clientY);
    }
}, { passive: false });

// Touch move handler for all controls
document.addEventListener('touchmove', (e) => {
    if (!hasControl) return;
    e.preventDefault();
    
    // Process each changed touch
    for (let i = 0; i < e.changedTouches.length; i++) {
        const touch = e.changedTouches[i];
        
        // Handle bars control touches
        if (activeMethod === 'bars') {
            const touchIndex = findTouchIndex(touch.identifier);
            
            if (touchIndex !== -1) {
                const touchData = activeTouches[touchIndex];
                
                if (touchData.element === 'throttle') {
                    updateThrottle(touch.clientY);
                } else if (touchData.element === 'steering') {
                    updateSteering(touch.clientX);
                }
            }
        }
        // Handle joystick control touch
        else if (activeMethod === 'joystick' && joystickTracking && touch.identifier === joystickTouchId) {
            updateJoystick(touch.clientX, touch.clientY);
        }
    }
}, { passive: false });

// Touch end/cancel handling
document.addEventListener('touchend', (e) => {
    // Check each ended touch
    for (let i = 0; i < e.changedTouches.length; i++) {
        const touch = e.changedTouches[i];
        
        if (activeMethod === 'bars') {
            const touchIndex = findTouchIndex(touch.identifier);
            
            if (touchIndex !== -1) {
                const touchData = activeTouches[touchIndex];
                
                // Reset the appropriate control
                if (touchData.element === 'throttle') {
                    throttleIndicator.style.top = '50%';
                    throttlePercent = 0;
                    throttleValue.textContent = '0%';
                } else if (touchData.element === 'steering') {
                    steeringIndicator.style.left = '50%';
                    steeringPercent = 0;
                    steeringValue.textContent = '0%';
                }
                
                // Remove the touch
                activeTouches.splice(touchIndex, 1);
                
                // Send command with updated values
                sendControlCommand(throttlePercent, steeringPercent);
            }
        }
        else if (activeMethod === 'joystick' && touch.identifier === joystickTouchId) {
            joystickTracking = false;
            joystickTouchId = null;
            joystickIndicator.style.transform = 'translate(-50%, -50%)';
            throttlePercent = 0;
            steeringPercent = 0;
            throttleValue.textContent = '0%';
            steeringValue.textContent = '0%';
            
            sendControlCommand(0, 0);
        }
    }
});

document.addEventListener('touchcancel', (e) => {
    // Similar to touchend but for canceled touches
    for (let i = 0; i < e.changedTouches.length; i++) {
        const touch = e.changedTouches[i];
        
        if (activeMethod === 'bars') {
            const touchIndex = findTouchIndex(touch.identifier);
            
            if (touchIndex !== -1) {
                const touchData = activeTouches[touchIndex];
                
                // Reset the appropriate control
                if (touchData.element === 'throttle') {
                    throttleIndicator.style.top = '50%';
                    throttlePercent = 0;
                    throttleValue.textContent = '0%';
                } else if (touchData.element === 'steering') {
                    steeringIndicator.style.left = '50%';
                    steeringPercent = 0;
                    steeringValue.textContent = '0%';
                }
                
                // Remove the touch
                activeTouches.splice(touchIndex, 1);
            }
        }
        else if (activeMethod === 'joystick' && touch.identifier === joystickTouchId) {
            joystickTracking = false;
            joystickTouchId = null;
            joystickIndicator.style.transform = 'translate(-50%, -50%)';
            throttlePercent = 0;
            steeringPercent = 0;
            throttleValue.textContent = '0%';
            steeringValue.textContent = '0%';
        }
    }
    
    // Send command with updated values
    if (hasControl) {
        sendControlCommand(throttlePercent, steeringPercent);
    }
});

// ===== MOUSE EVENT HANDLERS (for desktop testing) =====
let mouseThrottleActive = false;
let mouseSteeringActive = false;
let mouseJoystickActive = false;

throttleArea.addEventListener('mousedown', (e) => {
    if (!hasControl || activeMethod !== 'bars') return;
    mouseThrottleActive = true;
    updateThrottle(e.clientY);
});

steeringArea.addEventListener('mousedown', (e) => {
    if (!hasControl || activeMethod !== 'bars') return;
    mouseSteeringActive = true;
    updateSteering(e.clientX);
});

joystick.addEventListener('mousedown', (e) => {
    if (!hasControl || activeMethod !== 'joystick') return;
    mouseJoystickActive = true;
    updateJoystick(e.clientX, e.clientY);
});

document.addEventListener('mousemove', (e) => {
    if (!hasControl) return;
    
    if (activeMethod === 'bars') {
        if (mouseThrottleActive) {
            updateThrottle(e.clientY);
        }
        
        if (mouseSteeringActive) {
            updateSteering(e.clientX);
        }
    }
    else if (activeMethod === 'joystick' && mouseJoystickActive) {
        updateJoystick(e.clientX, e.clientY);
    }
});

document.addEventListener('mouseup', () => {
    if (mouseThrottleActive) {
        mouseThrottleActive = false;
        throttleIndicator.style.top = '50%';
        throttlePercent = 0;
        throttleValue.textContent = '0%';
    }
    
    if (mouseSteeringActive) {
        mouseSteeringActive = false;
        steeringIndicator.style.left = '50%';
        steeringPercent = 0;
        steeringValue.textContent = '0%';
    }
    
    if (mouseJoystickActive) {
        mouseJoystickActive = false;
        joystickIndicator.style.transform = 'translate(-50%, -50%)';
        throttlePercent = 0;
        steeringPercent = 0;
        throttleValue.textContent = '0%';
        steeringValue.textContent = '0%';
    }
    
    if (hasControl) {
        sendControlCommand(throttlePercent, steeringPercent);
    }
});



// Keyboard controls
document.addEventListener('keydown', (e) => {
    if (!hasControl || e.repeat) return;
    
    switch(e.key) {
        case 'ArrowUp':
            throttlePercent = 80;
            break;
        case 'ArrowDown':
            throttlePercent = -80;
            break;
        case 'ArrowLeft':
            steeringPercent = -80;
            break;
        case 'ArrowRight':
            steeringPercent = 80;
            break;
        case ' ': // Spacebar for stop
            resetControls();
            break;
        default:
            return;
    }
    
    // Update displays
    throttleValue.textContent = `${throttlePercent}%`;
    steeringValue.textContent = `${steeringPercent}%`;
    
    // Update indicators based on active method
    if (activeMethod === 'bars') {
        if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            throttleIndicator.style.top = (throttlePercent >= 0) ? '0%' : '100%';
        }
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            steeringIndicator.style.left = (steeringPercent >= 0) ? '100%' : '0%';
        }
    }
    else if (activeMethod === 'joystick') {
        const maxPos = 25; // px from center
        let deltaX = 0, deltaY = 0;
        
        if (e.key === 'ArrowUp') deltaY = -maxPos;
        else if (e.key === 'ArrowDown') deltaY = maxPos;
        
        if (e.key === 'ArrowLeft') deltaX = -maxPos;
        else if (e.key === 'ArrowRight') deltaX = maxPos;
        
        joystickIndicator.style.transform = `translate(calc(-50% + ${deltaX}px), calc(-50% + ${deltaY}px))`;
    }
    
    sendControlCommand(throttlePercent, steeringPercent);
});

document.addEventListener('keyup', (e) => {
    if (!hasControl) return;
    
    switch(e.key) {
        case 'ArrowUp':
        case 'ArrowDown':
            throttlePercent = 0;
            if (activeMethod === 'bars') {
                throttleIndicator.style.top = '50%';
            }
            break;
        case 'ArrowLeft':
        case 'ArrowRight':
            steeringPercent = 0;
            if (activeMethod === 'bars') {
                steeringIndicator.style.left = '50%';
            }
            break;
        default:
            return;
    }
    
    if (activeMethod === 'joystick' && (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
        joystickIndicator.style.transform = 'translate(-50%, -50%)';
    }
    
    // Update displays
    throttleValue.textContent = `${throttlePercent}%`;
    steeringValue.textContent = `${steeringPercent}%`;
    
    sendControlCommand(throttlePercent, steeringPercent);
});

// Handle visibility and page unload
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden' && hasControl) {
        sendControlCommand(0, 0);
        resetControls();
    }
});

window.addEventListener('beforeunload', function() {
    if (hasControl) {
        socket.emit('message', { throttle: 'stop', turn: 'none' });
    }
});


