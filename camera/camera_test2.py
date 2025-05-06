import asyncio
import cv2
import numpy as np
from aiohttp import web
from aiortc import RTCPeerConnection, VideoStreamTrack
from aiortc.contrib.media import MediaRelay
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import io
from threading import Condition

# Global frame holder
class FrameOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()
        return len(buf)

frame_output = FrameOutput()

# Start the Pi camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start_recording(JpegEncoder(), FileOutput(frame_output))


# Create aiortc VideoTrack
class CameraVideoTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()

    async def recv(self):
        from av import VideoFrame
        import time

        # Wait for the next frame
        with frame_output.condition:
            frame_output.condition.wait()
            jpeg_data = frame_output.frame

        # Decode JPEG to ndarray
        img_array = np.frombuffer(jpeg_data, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = time.time_ns() // 1000
        video_frame.time_base = fractions.Fraction(1, 1_000_000)
        return video_frame


# WebRTC signaling
pcs = set()
relay = MediaRelay()

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    video_track = CameraVideoTrack()
    pc.addTrack(video_track)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })


# Routes and app
app = web.Application()
app.router.add_post("/offer", offer)

# Run the server
web.run_app(app, port=8080)
