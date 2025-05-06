import socket
import time

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality, JpegEncoder
from picamera2.outputs import FileOutput

picam2 = Picamera2()
video_config = picam2.create_video_configuration({"size": (720, 720)})
picam2.configure(video_config)
#encoder = H264Encoder(1000000)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    
    sock.connect(("", 5000))
    stream = sock.makefile("wb")
    picam2.start_recording(JpegEncoder(), FileOutput(stream), quality=Quality.VERY_LOW)

    while True:
        try:
            pass
        except KeyboardInterrupt:
            picam2.stop_recording()


