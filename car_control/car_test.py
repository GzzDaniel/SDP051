# pi_client.py - Run this on your Raspberry Pi
import socketio
import RPi.GPIO as gpio
import time
import sys

# Configure Socket.IO client
sio = socketio.Client()

# Server URL - Change this to your actual server address
SERVER_URL = "http://32.219.174.238:4000"  # Replace with your server's IP

# Motor control pins
# Left/right pins
LR_PIN1 = 17  # Left
LR_PIN2 = 22  # Right
# Forward/backward pins 
FB_PIN1 = 23  # Forward
FB_PIN2 = 24  # Backward

# Current state tracking
current_speed = 50  # Default starting speed (0-100)

def setup_gpio():
    """Initialize GPIO pins"""
    # Clean up any previous GPIO setup
    gpio.setwarnings(False)
    try:
        gpio.cleanup()
    except:
        pass
    
    # Set GPIO mode
    gpio.setmode(gpio.BCM)
    
    # Setup direction pins
    gpio.setup(LR_PIN1, gpio.OUT)
    gpio.setup(LR_PIN2, gpio.OUT)
    gpio.setup(FB_PIN1, gpio.OUT)
    gpio.setup(FB_PIN2, gpio.OUT)
    
    # Initialize all pins to OFF
    gpio.output(LR_PIN1, False)
    gpio.output(LR_PIN2, False)
    gpio.output(FB_PIN1, False)
    gpio.output(FB_PIN2, False)
    
    print("GPIO initialized and ready for control")

def move_forward():
    """Move the car forward"""
    gpio.output(FB_PIN1, True)
    gpio.output(FB_PIN2, False)
    print("Moving forward")

def move_backward():
    """Move the car backward"""
    gpio.output(FB_PIN1, False)
    gpio.output(FB_PIN2, True)
    print("Moving backward")

def turn_left():
    """Turn the car left"""
    gpio.output(LR_PIN1, True)
    gpio.output(LR_PIN2, False)
    print("Turning left")

def turn_right():
    """Turn the car right"""
    gpio.output(LR_PIN1, False)
    gpio.output(LR_PIN2, True)
    print("Turning right")

def stop_forward_backward():
    """Stop forward/backward movement"""
    gpio.output(FB_PIN1, False)
    gpio.output(FB_PIN2, False)
    print("Stopped forward/backward")

def stop_turning():
    """Stop turning"""
    gpio.output(LR_PIN1, False)
    gpio.output(LR_PIN2, False)
    print("Stopped turning")

def cleanup_gpio():
    """Clean up GPIO resources"""
    try:
        gpio.cleanup()
        print("GPIO cleaned up")
    except Exception as e:
        print(f"Error during GPIO cleanup: {e}")

# Socket.IO event handlers
@sio.event
def connect():
    print("Connected to Flask server")
    sio.emit("identify", {"user_agent": "Pi"})
    # Setup GPIO after connection
    setup_gpio()

@sio.event
def disconnect():
    print("Disconnected from Flask server")
    cleanup_gpio()

@sio.event
def pi_command(data):
    print(f"Received command: {data}")
    
    # Handle string commands (legacy format)
    if isinstance(data, str):
        if data == "UP pressed":
            move_forward()
        elif data == "DOWN pressed":
            move_backward()
        elif data == "LEFT pressed":
            turn_left()
        elif data == "RIGHT pressed":
            turn_right()
        elif data == "UP released" or data == "DOWN released":
            stop_forward_backward()
        elif data == "LEFT released" or data == "RIGHT released":
            stop_turning()
    
    # Handle dictionary commands (new format)
    elif isinstance(data, dict):
        throttle = data.get("throttle")
        turn = data.get("turn")
        
        # Process forward/backward movement
        if throttle == "forward":
            move_forward()
        elif throttle == "backward":
            move_backward()
        elif throttle == "stop":
            stop_forward_backward()
        
        # Process turning
        if turn == "left":
            turn_left()
        elif turn == "right":
            turn_right()
        elif turn == "none":
            stop_turning()

# Main program
if __name__ == "__main__":
    try:
        print(f"Connecting to Flask server at {SERVER_URL}...")
        sio.connect(SERVER_URL)
        sio.wait()
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cleanup_gpio()