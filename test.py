from flask import Flask, render_template_string, jsonify, request
from gpiozero import PWMOutputDevice
from gpiozero.pins.rpigpio import RPiGPIOFactory
import time
import signal
import sys

# Initialize Flask app
app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Motor Control</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
        }
        .control-panel {
            margin: 20px;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 10px;
        }
        .button {
            padding: 15px 30px;
            margin: 10px;
            font-size: 18px;
            cursor: pointer;
            border: none;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        .forward {
            background-color: #4CAF50;
            color: white;
        }
        .stop {
            background-color: #f44336;
            color: white;
        }
        .backward {
            background-color: #2196F3;
            color: white;
        }
        .speed-control {
            margin: 20px;
        }
        .speed-slider {
            width: 80%;
            max-width: 400px;
        }
        .status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>Motor Control Interface</h1>
    
    <div class="control-panel">
        <div class="speed-control">
            <h3>Speed Control</h3>
            <input type="range" id="speedSlider" class="speed-slider" min="0" max="100" value="20">
            <p>Speed: <span id="speedValue">20</span>%</p>
        </div>
        
        <div class="buttons">
            <button class="button forward" onclick="controlMotor('forward')">Forward</button>
            <button class="button stop" onclick="controlMotor('stop')">STOP</button>
            <button class="button backward" onclick="controlMotor('backward')">Backward</button>
        </div>
        
        <div class="status" id="statusMessage"></div>
    </div>

    <script>
        const speedSlider = document.getElementById('speedSlider');
        const speedValue = document.getElementById('speedValue');
        const statusMessage = document.getElementById('statusMessage');
        
        speedSlider.oninput = function() {
            speedValue.textContent = this.value;
        }
        
        function controlMotor(action) {
            const speed = speedSlider.value;
            fetch(`/motor/${action}?speed=${speed}`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    statusMessage.textContent = data.message;
                    statusMessage.style.backgroundColor = data.success ? '#dff0d8' : '#f2dede';
                })
                .catch(error => {
                    statusMessage.textContent = 'Error controlling motor';
                    statusMessage.style.backgroundColor = '#f2dede';
                });
        }
    </script>
</body>
</html>
"""

class BrushlessMotor:
    def __init__(self, pin=26, freq=50):
        self.pin = pin
        self.freq = freq
        self.motor = None
        self.pin_factory = RPiGPIOFactory()
        
    def initialize(self):
        """Initialize the motor with proper startup sequence"""
        print("\nInitializing ESC...")
        try:
            self.motor = PWMOutputDevice(self.pin, frequency=self.freq, pin_factory=self.pin_factory)
            
            # Start with zero throttle
            self.motor.value = 0
            time.sleep(2)  # Wait for ESC to recognize idle signal
            
            # Give a small initial pulse to show it's working
            print("Testing motor...")
            self.motor.value = 0.055  # Very slight movement
            time.sleep(1)
            self.motor.value = 0
            time.sleep(1)
            
            print("ESC initialization complete")
            return True
            
        except Exception as e:
            print(f"Error initializing ESC: {str(e)}")
            return False
    
    def set_speed(self, speed):
        """Set motor speed (-1 to 1)"""
        if self.motor:
            # Convert speed to PWM range (0.05 to 0.10)
            # Limit speed to -1 to 1 range
            speed = max(-1, min(1, speed))
            
            # Scale the speed to a smaller range for safety
            pwm_value = 0.05 + (abs(speed) * 0.03)  # This will give us max of 0.08
            
            # Direction is handled by the ESC configuration
            self.motor.value = pwm_value
            print(f"Setting PWM value to: {pwm_value}")
    
    def stop(self):
        """Stop the motor"""
        if self.motor:
            self.motor.value = 0
    
    def cleanup(self):
        """Cleanup GPIO and stop motor"""
        if self.motor:
            print("\nStopping motor...")
            self.motor.value = 0
            time.sleep(0.5)
            self.motor.close()
        print("Cleanup complete")

# Initialize motor
motor = BrushlessMotor()
if not motor.initialize():
    print("Failed to initialize motor")
    sys.exit(1)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/motor/<action>', methods=['POST'])
def control_motor(action):
    try:
        speed = float(request.args.get('speed', 20)) / 100.0  # Convert percentage to decimal
        
        if action == 'forward':
            motor.set_speed(speed)
            message = f"Moving forward at {speed*100:.0f}% speed"
        elif action == 'backward':
            motor.set_speed(-speed)
            message = f"Moving backward at {speed*100:.0f}% speed"
        elif action == 'stop':
            motor.stop()
            message = "Motor stopped"
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})
            
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    try:
        # Run the web server
        print("Starting web server...")
        print("Access the motor control interface at: http://YOUR_PI_IP:5000")
        app.run(host='0.0.0.0', port=5000)
    finally:
        motor.cleanup()