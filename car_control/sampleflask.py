from flask import Flask, request, render_template_string, render_template
from flask_socketio import SocketIO, emit
from time import time

app = Flask(__name__)
socketio = SocketIO(app)

# Variable to store the word
stored_word = None
num = 0


@app.route('/', methods=['GET', 'POST'])
def index():
    # Render the HTML template
    return render_template('index.html')

# ______________ user queue _______________
class UserQueue:
    '''manages the active users to give sequential control of the car, NOTIFIES users through socket communication'''
    def __init__(self):
        self.queue = []  # 
        self.idx = None  # index that points to the session id of the host in control of the car
        
    def activateCurrentUser(self):
        print("current index: ", self.idx)
        emit('timestart', to=self.queue[self.idx])
        print("notification sent to", self.queue[self.idx])
        self.printInfo()
    
    def nextUser(self):
        '''goes to the next user and notifies them'''
        self.idx += 1
        if self.idx >= len(self.queue):
            # loop back to the start of the queue
            print("index went back to start of queue")
            self.idx = 0
            
        self.activateCurrentUser()
            
    def addUser(self, sessionID):
        '''usage: sessionID = request.id | Adds user's session id to the queue, notifies them if conditions are met'''
        self.queue.append(sessionID)  # add to session id to queue
    
        if self.idx is None:
            self.idx = len(self.queue)-1
            self.activateCurrentUser()
            
        print("New Client connected:", request.sid) 
        
    def removeUser(self, sessionID):
        '''usage: sessionID = request.id | removes by their session id, notifies new user if conditions are met'''
        self.queue.remove(sessionID)  # remove user from queue, queue will automatically point to next user properly
        print("Client diconnected:", sessionID) 
        
        if len(self.queue) <= 0:  # if list is empty
            self.idx = None            
        else:
            self.activateCurrentUser()
        
    def printInfo(self):
        '''prints relevant info in the python terminal'''
        print("active users: ", self.queue)
        if self.idx is not None:
            print("user with control: ", self.queue[self.idx])
        else:
            print("user with control: NONE")
    

#_______________ socketio  events_____________________
# When a new client connects
pi_sid = None  #stores raspberry pi session id

userqueue = UserQueue()

@socketio.on("connect")
def handle_connect():
    global pi_sid
    userqueue.addUser(request.sid)
    userqueue.printInfo()
    
    
# TODO if user with active controller disconnected, go to next preson in queue
@socketio.on("disconnect")
def handle_disconnect():
    userqueue.removeUser(request.sid)
    userqueue.printInfo()
    
    
# clients will notify server when their turn is over
@socketio.on("timeover")
def handle_timeover(data):
    print("time ended for: ", request.sid)
    userqueue.nextUser()

@socketio.on("identify")
def handle_identify(data):
    global pi_sid
    if data.get("user_agent") == "Pi":
        pi_sid = request.sid
        print("Pi connected:", pi_sid)

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    if pi_sid:
        emit('pi_command', data, to=pi_sid)
        
    if data.get("user_agent") != "Pi":
        throttle, turn = data
        print(data["throttle"], data["turn"])

    
if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=4000, debug = True)
    socketio.run(app, host="0.0.0.0", port=4000, debug=True)

