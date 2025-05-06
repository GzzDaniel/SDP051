import RPi.GPIO as gpio
import time

"""
forward/backward are pin 16 18 (physical) 
purple -> red
grey -> black

left/right are pin 17 22
white -> red
black -> black

"""

def init():
    gpio.setmode(gpio.BCM)
    # left right
    gpio.setup(17, gpio.OUT)
    gpio.setup(22, gpio.OUT)
    # forward backward
    gpio.setup(23, gpio.OUT)
    gpio.setup(24, gpio.OUT)

def forward(sec):
    init()
    gpio.output(23, True)
    gpio.output(24, False)
    time.sleep(sec)
    gpio.cleanup()

def backward(sec):
    init()
    gpio.output(23, False)
    gpio.output(24, True)
    time.sleep(sec)
    gpio.cleanup()

def left(sec):
    init()
    gpio.output(17, True)
    gpio.output(22, False)
    time.sleep(sec)
    gpio.cleanup()

def right(sec):
    init()
    gpio.output(17, False)
    gpio.output(22, True)
    time.sleep(sec)
    gpio.cleanup()

# Main test sequence
seconds = 2
turn_time = 0.5

print("left")
left(turn_time)
time.sleep(1)

print("right")
right(turn_time)
time.sleep(1)

print("forward")
forward(seconds)
time.sleep(1)

print("backward")
backward(seconds)
time.sleep(1)

