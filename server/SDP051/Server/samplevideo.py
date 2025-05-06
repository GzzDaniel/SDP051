import cv2
import socket
import pickle
import numpy as np

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('', 5000))

while True:
    x = s.recv(1024)
    
    data = pickle.loads(data)
    
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    cv2.imshow("IMG SERVER", img)
    
    if (cv2.waitKey(5) & 0xFF == 27):
        break
    
cv2.destroyAllWindows()
