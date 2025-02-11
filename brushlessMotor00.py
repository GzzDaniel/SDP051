from gpiozero import PWMOutputDevice
import time

PIN = 17

motor = PWMOutputDevice(PIN, frequency=50)

def set_motor_speed(duty_cycle):
    motor.value = duty_cycle / 1000
    print(f"Set Motor speed to {duty_cycle}%")

try:
    while True:  # Main loop to keep repeating
        # Decrease from 100 to 50
        for i in range(100, 50, -1):
            set_motor_speed(i)
            time.sleep(.2)
        
        # Increase from 50 to 100
        for i in range(50, 100, +1):
            set_motor_speed(i)
            time.sleep(.2)
        
        # Optional: Add a small pause at the end of each cycle
        time.sleep(1)

except KeyboardInterrupt:
    pass
finally:
    motor.value = 0
    print("GPIO cleaned up.")