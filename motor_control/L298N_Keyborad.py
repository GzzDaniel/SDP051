import RPi.GPIO as gpio
import time
import curses

def init():
    gpio.setmode(gpio.BCM)
    # left right motors
    gpio.setup(17, gpio.OUT)
    gpio.setup(22, gpio.OUT)
    # forward backward motors
    gpio.setup(23, gpio.OUT)
    gpio.setup(24, gpio.OUT)

def move(fb_direction, lr_direction, duration=0.1):
    """
    Move the robot with combined forward/backward and left/right control
    fb_direction: 1 for forward, -1 for backward, 0 for stop
    lr_direction: 1 for right, -1 for left, 0 for straight
    duration: how long to run the motors
    """
    # No need to reinitialize GPIO for every move as it causes stuttering
    # Only initialize once at the start of the program
    
    # Forward/backward control
    if fb_direction == 1:  # Forward
        gpio.output(23, True)
        gpio.output(24, False)
    elif fb_direction == -1:  # Backward
        gpio.output(23, False)
        gpio.output(24, True)
    else:  # Stop forward/backward
        gpio.output(23, False)
        gpio.output(24, False)
    
    # Left/right control
    if lr_direction == 1:  # Right
        gpio.output(17, False)
        gpio.output(22, True)
    elif lr_direction == -1:  # Left
        gpio.output(17, True)
        gpio.output(22, False)
    else:  # Straight
        gpio.output(17, False)
        gpio.output(22, False)
    
    if duration > 0:
        time.sleep(duration)
    # Don't cleanup here to maintain continuous control

def stop_all():
    """Stop all motors and clean up GPIO"""
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(24, False)
    gpio.cleanup()

def main(stdscr):
    # Set up curses
    stdscr.clear()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)
    curses.noecho()
    
    stdscr.addstr(0, 0, "Robot Keyboard Control")
    stdscr.addstr(1, 0, "Use arrow keys to drive")
    stdscr.addstr(2, 0, "Release keys to stop")
    stdscr.addstr(3, 0, "Press 'q' to quit")
    stdscr.addstr(5, 0, "Current status: Stopped")
    stdscr.refresh()
    
    current_status = "Stopped"
    
    # Initialize GPIO once at the beginning
    init()
    
    try:
        while True:
            # Get keyboard input
            key = stdscr.getch()
            
            fb_direction = 0
            lr_direction = 0
            
            if key == curses.KEY_UP:
                fb_direction = 1
                current_status = "Moving Forward"
            elif key == curses.KEY_DOWN:
                fb_direction = -1
                current_status = "Moving Backward"
            elif key == curses.KEY_LEFT:
                lr_direction = -1
                current_status = "Turning Left"
            elif key == curses.KEY_RIGHT:
                lr_direction = 1
                current_status = "Turning Right"
            elif key == ord('q'):
                break
            
            if key != -1:  # A key was pressed
                move(fb_direction, lr_direction, 0.1)
                stdscr.addstr(5, 0, f"Current status: {current_status}")
                stdscr.refresh()
            else:  # No key is pressed, stop the robot
                move(0, 0, 0.1)  # Stop all motors
                if current_status != "Stopped":
                    current_status = "Stopped"
                    stdscr.addstr(5, 0, f"Current status: {current_status}")
                    stdscr.refresh()
            
            time.sleep(0.05)  # Small delay to reduce CPU usage
    
    finally:
        stop_all()

if __name__ == "__main__":
    try:
        # Initialize curses and start the control loop
        curses.wrapper(main)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Make sure GPIO is cleaned up even if there's an error
        gpio.cleanup()
        print("Program ended. GPIO cleaned up.")