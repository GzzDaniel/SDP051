from robot_hat import PWM, Servo
import time

# Create servo objects
steering = Servo("P0")  # Steering servo on PWM pin 0
esc = Servo("P1")       # ESC on PWM pin 1

def test_steering():
    print("Testing steering...")
    steering.angle(-45)  # Turn left
    time.sleep(1)
    steering.angle(0)    # Center
    time.sleep(1)
    steering.angle(45)   # Turn right
    time.sleep(1)
    steering.angle(0)    # Return to center
    time.sleep(1)

def test_esc():
    print("Testing ESC/motor...")
    print("Arming ESC...")
    esc.angle(0)         # Neutral position (arming the ESC)
    time.sleep(2)
    
    print("Forward slow")
    esc.angle(10)        # Slow forward
    time.sleep(2)
    
    print("Stop")
    esc.angle(0)         # Stop
    time.sleep(2)
    
    print("Reverse slow")
    esc.angle(-10)       # Slow reverse
    time.sleep(2)
    
    print("Stop")
    esc.angle(0)         # Stop
    
# Run the tests
test_steering()
test_esc()