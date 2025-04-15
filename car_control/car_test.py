import socketio
import RPi.GPIO as gpio
import time

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

# PWM settings
PWM_FREQ = 100  # PWM frequency in Hz
fb_pwm = None
lr_pwm = None

# Current state tracking
current_fb_speed = 0  # -100 to 100
current_lr_speed = 0  # -100 to 100

def setup_gpio():
    """Initialize GPIO pins with PWM support"""
    global fb_pwm, lr_pwm
    
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
    
    # Setup PWM on all pins
    fb_pwm = [gpio.PWM(FB_PIN1, PWM_FREQ), gpio.PWM(FB_PIN2, PWM_FREQ)]
    lr_pwm = [gpio.PWM(LR_PIN1, PWM_FREQ), gpio.PWM(LR_PIN2, PWM_FREQ)]
    
    # Start PWM with 0% duty cycle (stopped)
    for pwm in fb_pwm + lr_pwm:
        pwm.start(0)
    
    print("GPIO initialized with PWM and ready for control")

def set_forward_backward(speed_percent):
    """
    Set forward/backward movement with speed control
    speed_percent: -100 to 100, negative for backward, positive for forward
    """
    global current_fb_speed
    
    # Ensure PWM is available
    if fb_pwm is None:
        return
    
    # Limit to valid range
    speed_percent = max(-100, min(100, speed_percent))
    current_fb_speed = speed_percent
    
    abs_speed = abs(speed_percent)
    
    # Map 0-100 to PWM duty cycle (adjust this range as needed for your motors)
    # For some motors, lower values might not move the motor, so we add a minimum
    if abs_speed > 0:
        duty_cycle = 20 + (abs_speed * 0.8)  # Scale 0-100 to 20-100
    else:
        duty_cycle = 0
    
    # Set direction based on sign and apply PWM
    if speed_percent > 0:  # Forward
        fb_pwm[0].ChangeDutyCycle(duty_cycle)  # FB_PIN1
        fb_pwm[1].ChangeDutyCycle(0)           # FB_PIN2
        print(f"Moving forward at {duty_cycle}% duty cycle")
    elif speed_percent < 0:  # Backward
        fb_pwm[0].ChangeDutyCycle(0)           # FB_PIN1
        fb_pwm[1].ChangeDutyCycle(duty_cycle)  # FB_PIN2
        print(f"Moving backward at {duty_cycle}% duty cycle")
    else:  # Stop
        fb_pwm[0].ChangeDutyCycle(0)
        fb_pwm[1].ChangeDutyCycle(0)
        print("Stopped forward/backward movement")

def set_left_right(speed_percent):
    """
    Set left/right turning with speed control
    speed_percent: -100 to 100, negative for left, positive for right
    """
    global current_lr_speed
    
    # Ensure PWM is available
    if lr_pwm is None:
        return
    
    # Limit to valid range
    speed_percent = max(-100, min(100, speed_percent))
    current_lr_speed = speed_percent
    
    abs_speed = abs(speed_percent)
    
    # Map 0-100 to PWM duty cycle (adjust this range as needed for your motors)
    # For some motors, lower values might not move the motor, so we add a minimum
    if abs_speed > 0:
        duty_cycle = 20 + (abs_speed * 0.8)  # Scale 0-100 to 20-100
    else:
        duty_cycle = 0
    
    # Set direction based on sign and apply PWM
    if speed_percent > 0:  # Right
        lr_pwm[0].ChangeDutyCycle(0)           # LR_PIN1
        lr_pwm[1].ChangeDutyCycle(duty_cycle)  # LR_PIN2
        print(f"Turning right at {duty_cycle}% duty cycle")
    elif speed_percent < 0:  # Left
        lr_pwm[0].ChangeDutyCycle(duty_cycle)  # LR_PIN1
        lr_pwm[1].ChangeDutyCycle(0)           # LR_PIN2
        print(f"Turning left at {duty_cycle}% duty cycle")
    else:  # Stop turning
        lr_pwm[0].ChangeDutyCycle(0)
        lr_pwm[1].ChangeDutyCycle(0)
        print("Stopped turning")

def cleanup_gpio():
    """Clean up GPIO resources"""
    global fb_pwm, lr_pwm
    
    try:
        # Stop PWM
        if fb_pwm:
            for pwm in fb_pwm:
                pwm.stop()
        if lr_pwm:
            for pwm in lr_pwm:
                pwm.stop()
        
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
    
    # Handle dictionary commands
    if isinstance(data, dict):
        throttle = data.get("throttle")
        turn = data.get("turn")
        throttle_percent = data.get("throttle_percent", 0)
        turn_percent = data.get("turn_percent", 0)
        
        # Calculate actual speed values (-100 to 100)
        fb_speed = throttle_percent if throttle == "forward" else -throttle_percent if throttle == "backward" else 0
        lr_speed = turn_percent if turn == "right" else -turn_percent if turn == "left" else 0
        
        # Apply speed control
        set_forward_backward(fb_speed)
        set_left_right(lr_speed)
    
    # Handle legacy string commands (for backward compatibility)
    elif isinstance(data, str):
        if data == "UP pressed":
            set_forward_backward(100)
        elif data == "DOWN pressed":
            set_forward_backward(-100)
        elif data == "LEFT pressed":
            set_left_right(-100)
        elif data == "RIGHT pressed":
            set_left_right(100)
        elif data == "UP released" or data == "DOWN released":
            set_forward_backward(0)
        elif data == "LEFT released" or data == "RIGHT released":
            set_left_right(0)

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