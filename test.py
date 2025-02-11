import RPi.GPIO as GPIO
import time
import signal
import sys
import atexit

# Constants
ESC_PIN = 18  # Changed to hardware PWM pin
FREQUENCY = 50  # 50Hz for standard RC signals

class ESCController:
    def __init__(self, pin):
        # Reset GPIO
        GPIO.cleanup()
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        
        # Create PWM on hardware PWM pin
        self.pwm = GPIO.PWM(pin, FREQUENCY)
        self.pwm.start(0)
        self.running = True
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.cleanup)

    def set_throttle(self, duty_cycle):
        """Set throttle with PWM duty cycle"""
        if not self.running:
            return
            
        try:
            self.pwm.ChangeDutyCycle(duty_cycle)
            print(f"Duty Cycle: {duty_cycle:.1f}%")
        except Exception as e:
            print(f"PWM Error: {str(e)}")

    def arm(self):
        """ESC arming sequence"""
        print("\nArming ESC...")
        print("Setting zero")
        self.set_throttle(0)
        time.sleep(2)
        
        print("Sending calibration signal")
        self.set_throttle(10)
        time.sleep(2)
        
        print("Back to zero")
        self.set_throttle(0)
        time.sleep(2)
        
        print("ESC armed")

    def cleanup(self, *args):
        """Safe shutdown"""
        if self.running:
            print("\nStopping motor...")
            self.running = False
            try:
                self.set_throttle(0)
                time.sleep(0.5)
                self.pwm.stop()
                GPIO.cleanup()
                print("Cleanup completed")
            except:
                GPIO.cleanup()
            finally:
                sys.exit(0)

def main():
    print("\nHardware PWM ESC Control")
    print("----------------------")
    print("Using hardware PWM pin (GPIO18)")
    input("Press Enter when ready...")

    esc = ESCController(ESC_PIN)
    
    try:
        # Initial arming
        esc.arm()
        
        print("\nStarting test sequence")
        print("Press Ctrl+C to stop")
        
        while True:
            # Test different duty cycles
            duty_cycles = [0, 5, 7.5, 10]
            for dc in duty_cycles:
                print(f"\nTesting {dc}% duty cycle")
                esc.set_throttle(dc)
                time.sleep(3)  # Hold each test for 3 seconds
                
            # Return to zero
            esc.set_throttle(0)
            time.sleep(2)
            
            # Ask to continue
            response = input("\nContinue testing? (y/n): ")
            if response.lower() != 'y':
                break

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
    finally:
        esc.cleanup()

if __name__ == "__main__":
    main()
    