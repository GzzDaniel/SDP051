import RPi.GPIO as GPIO          
from time import sleep

# GPIO Pin Configuration
in1 = 24
in2 = 23
en = 25
temp1 = 1  # Direction flag (1 for forward, 0 for backward)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(en, GPIO.OUT)
GPIO.output(in1, GPIO.LOW)
GPIO.output(in2, GPIO.LOW)

# Setup PWM
p = GPIO.PWM(en, 1000)  # 1000 Hz frequency
p.start(25)  # Start with 25% duty cycle

# Print instructions
print("\n")
print("L298N Brushless Motor Control")
print("----------------------------")
print("The default speed & direction of motor is LOW & Forward.....")
print("Commands:")
print("r - run (in last direction)  s - stop")
print("f - forward                  b - backward")
print("l - low speed (25%)          m - medium speed (50%)          h - high speed (100%)")
print("1-9 - set speed (10-90%)     0 - maximum speed (100%)")
print("e - exit")
print("\n")    

try:
    while True:
        x = input("Enter command: ")
        
        if x == 'r':
            print("Running motor...")
            if temp1 == 1:
                GPIO.output(in1, GPIO.HIGH)
                GPIO.output(in2, GPIO.LOW)
                print("Direction: Forward")
            else:
                GPIO.output(in1, GPIO.LOW)
                GPIO.output(in2, GPIO.HIGH)
                print("Direction: Backward")

        elif x == 's':
            print("Stopping motor...")
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.LOW)

        elif x == 'f':
            print("Setting direction: Forward")
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
            temp1 = 1

        elif x == 'b':
            print("Setting direction: Backward")
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.HIGH)
            temp1 = 0

        elif x == 'l':
            print("Setting speed: Low (25%)")
            p.ChangeDutyCycle(25)

        elif x == 'm':
            print("Setting speed: Medium (50%)")
            p.ChangeDutyCycle(50)

        elif x == 'h':
            print("Setting speed: High (100%)")
            p.ChangeDutyCycle(100)
            
        # New feature: direct speed setting with number keys
        elif x.isdigit():
            speed = int(x) * 10
            if x == '0':
                speed = 100
            print(f"Setting speed: {speed}%")
            p.ChangeDutyCycle(speed)
        
        elif x == 'e':
            print("Exiting program...")
            break
        
        else:
            print("Invalid command. Please use one of the following:")
            print("r, s, f, b, l, m, h, 0-9, e")

except KeyboardInterrupt:
    print("\nProgram stopped by user")
    
finally:
    p.stop()  # Stop PWM
    GPIO.cleanup()  # Clean up GPIO
    print("GPIO cleaned up. Program ended.")