import pigpio
import time
import signal
import sys
import atexit

ESC_PIN = 18  # Hardware PWM pin (GPIO18)
FREQUENCY = 50  # 50Hz

class ESCController:
    def __init__(self, pin):
        self.pi = pigpio.pi()
        self.pi.set_mode(pin, pigpio.OUTPUT)
        self.pi.set_PWM_frequency(pin, FREQUENCY)
        self.pi.set_PWM_range(pin, 20000)  # 20ms period for 50Hz
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def set_throttle(self, duty_cycle):
        """Set throttle using pulse width in microseconds."""
        pulse_width = int(duty_cycle * 200)  # Convert % to microseconds (e.g., 5% = 1000µs)
        self.pi.set_servo_pulsewidth(ESC_PIN, pulse_width)
        print(f"Pulse Width: {pulse_width}µs")

    def arm(self):
        """Arming sequence with correct signal order."""
        print("\nArming ESC...")
        self.set_throttle(10)  # 2000µs (max)
        time.sleep(2)
        self.set_throttle(5)   # 1000µs (min)
        time.sleep(2)
        print("ESC armed")

    def cleanup(self, *args):
        print("\nStopping motor...")
        self.set_throttle(0)  # Stop signal
        self.pi.stop()
        sys.exit(0)

def main():
    esc = ESCController(ESC_PIN)
    esc.arm()
    try:
        while True:
            esc.set_throttle(7.5)  # Neutral/stop
            time.sleep(3)
    finally:
        esc.cleanup()

if __name__ == "__main__":
    main()