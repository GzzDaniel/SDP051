from twisted.web import server, resource, static
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource

class MJPEGStream(Resource):
    isLeaf = True

    def __init__(self):
        self.frame = b''
        Resource.__init__(self)

    def render_GET(self, request):
        request.setHeader('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self._send_frame(request)
        return server.NOT_DONE_YET

    def _send_frame(self, request):
        request.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + self.frame + b"\r\n")
        reactor.callLater(0.04, self._send_frame, request)  # ~25fps

    def update_frame(self, new_frame):
        self.frame = new_frame

stream = MJPEGStream()

class Upload(Resource):
    isLeaf = True
    def render_POST(self, request):
        stream.update_frame(request.content.read())
        return b"OK"

root = Resource()
root.putChild(b"", static.File("templates"))
root.putChild(b"stream.mjpg", stream)
root.putChild(b"upload", Upload())

site = Site(root)
reactor.listenTCP(8080, site)
print("MJPEG server running at http://100.120.244.69:8080")
reactor.run()
