from gpiozero import PWMOutputDevice
from gpiozero.pins.rpigpio import RPiGPIOFactory  # Add explicit pin factory
import time
import signal
import sys

class BrushlessMotor:
    def __init__(self, pin=18, freq=50):
        self.pin = pin
        self.freq = freq
        self.motor = None
        self.running = False
        self.pin_factory = RPiGPIOFactory()  # Use RPi.GPIO explicitly
        
        # Signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def initialize(self):
        """Initialize the motor with proper startup sequence"""
        print("\nInitializing ESC...")
        try:
            self.motor = PWMOutputDevice(self.pin, frequency=self.freq, pin_factory=self.pin_factory)
            
            # Start with zero throttle
            self.motor.value = 0
            time.sleep(2)  # Wait for ESC to recognize idle signal
            
            print("ESC initialization complete")
            return True
            
        except Exception as e:
            print(f"Error initializing ESC: {str(e)}")
            return False
    
    def set_throttle(self, throttle_percent):
        """
        Set throttle value (0-100%)
        Converts throttle percentage to proper PWM value
        """
        if not self.motor:
            print("Motor not initialized!")
            return
            
        # Convert 0-100% to proper PWM value (0.05 - 0.10)
        # 0.05 is typically minimum throttle, 0.10 is maximum
        pwm_value = 0.05 + (throttle_percent / 100.0 * 0.05)
        
        # Clamp values for safety
        pwm_value = max(0.05, min(0.10, pwm_value))
        
        self.motor.value = pwm_value
        print(f"Throttle set to {throttle_percent}% (PWM: {pwm_value:.3f})")
    
    def run_continuous(self, initial_throttle=30):
        """Run the motor continuously with user control"""
        if not self.initialize():
            return
        
        self.running = True
        print("\nMotor Control Started")
        print("Commands:")
        print("+ : Increase throttle by 5%")
        print("- : Decrease throttle by 5%")
        print("q : Quit")
        
        current_throttle = initial_throttle
        self.set_throttle(current_throttle)
        
        while self.running:
            try:
                cmd = input("> ")
                
                if cmd.lower() == 'q':
                    break
                elif cmd == '+':
                    current_throttle = min(100, current_throttle + 5)
                    self.set_throttle(current_throttle)
                elif cmd == '-':
                    current_throttle = max(0, current_throttle - 5)
                    self.set_throttle(current_throttle)
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                break
                
        self.cleanup()
    
    def cleanup(self):
        """Cleanup GPIO and stop motor"""
        if self.motor:
            print("\nStopping motor...")
            self.motor.value = 0
            time.sleep(0.5)
            self.motor.close()
        print("Cleanup complete")
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\nShutdown signal received")
        self.running = False

if __name__ == "__main__":
    motor = BrushlessMotor()
    motor.run_continuous()