from flask import Flask, request, render_template_string, render_template, session, redirect, url_for
from flask_socketio import SocketIO, emit
from time import time

app = Flask(__name__)
app.secret_key = "SDP051secretkey"

socketio = SocketIO(app)

# Variable to store the word
stored_word = None
num = 0

adminsids = []
def notifyAdminsRow(row):
    for sid in adminsids:
        emit("adminResponseRow", row, to=sid)
        
def notifyAdminsTable(queue):
    for sid in adminsids:
        emit("adminResponseQueue", queue, to=sid)


# ____________________ ROUTES ________________________
@app.route('/', methods=['GET', 'POST'])
def index():
    # Render the HTML template
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        print("someone tried to access the admin page with: ", username, password)
        
        if username == 'SDP051' and password == 'SDP051051':
            session["can_access_secret"] = True  # Set flag in session
            return redirect(url_for("admin"))
        
        
    return render_template('login.html')


@app.route("/admin")
def admin():
    if not session.get("can_access_secret"):  # Check flag before allowing access
        return redirect(url_for("login"))  # Redirect if accessed directly
    
    session.pop("can_access_secret")  # Remove flag after accessing once
    
    return render_template('admin.html')


# ______________ user queue _______________
class UserQueue:
    '''manages the active users to give sequential control of the car, NOTIFIES users through socket communication'''
    def __init__(self):
        self.queue = []  # each element in queue has sessionid and timeAllowed
        self.idx = None  # index that points to the session id of the host in control of the car
        
    def getCurrentUser(self):
        return self.queue[self.idx]
    
    def getUserIndex(self, sessionID):
        for i in range(len(self.queue)):
            if self.queue[i]["sid"] == sessionID:
                return i
        print("ERROR: no session id found")
        
    def activateCurrentUser(self):
        print("current index: ", self.idx)
        emit('timestart', self.getCurrentUser()["timeAllowed"], to=self.getCurrentUser()["sid"])
        print("notification sent to", self.getCurrentUser()["sid"])
    
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
        self.queue.append({"sid":sessionID, "timeAllowed": 60})  # add to session id and time allowed to queue
    
        if self.idx is None:
            self.idx = len(self.queue)-1
            self.activateCurrentUser()
            
        print("New Client connected:", request.sid) 
        
        notifyAdminsTable(self.queue)
        
    def removeUser(self, sessionID):
        '''usage: sessionID = request.id | removes by their session id, notifies new user if conditions are met'''
        
        if self.idx is None:
            print("server tried to remove from empty list")
            return
         
        removedUser = self.queue[self.idx]["sid"]
        
        #self.queue.remove(sessionID)  # remove user from queue, queue will automatically point to next user properly
        
        del self.queue[self.getUserIndex(sessionID=sessionID)]
        
        print("Client diconnected:", sessionID) 
        
        if len(self.queue) <= 0:  # if list is empty
            self.idx = None     
        elif  self.idx >= len(self.queue):  #queue reached end
            self.idx = 0
            
        if (sessionID == removedUser) and (self.idx is not None):   # activate next user only if removed user was the one in control 
           self.activateCurrentUser()
           
        notifyAdminsTable(self.queue)
        
    def printInfo(self):
        '''prints relevant info in the python terminal'''
        print("INFO active users: ", self.queue)
        if self.idx is not None:
            print("user with control: ", self.queue[self.idx]["sid"])
        else:
            print("user with control: NONE")
    

#_______________ socketio  events_____________________
# When a new client connects
pi_sid = None  #stores raspberry pi session id
userqueue = UserQueue()

@socketio.on("connect")
def handle_connect():
    global pi_sid
    
    #userqueue.addUser(request.sid)
    #userqueue.printInfo()
    #if (request.sid != pi_sid) and (pi_sid is not None):
    #    userqueue.addUser(request.sid)
    #    userqueue.printInfo()
    
@socketio.on("userRequestAdd")
def handle_userRequestAdd(data):
    userqueue.addUser(request.sid)
    userqueue.printInfo()

@socketio.on("adminRequestQueue")
def handle_AdminRequestQueue(data):
    emit("adminResponseQueue", userqueue.queue, to=request.sid)
    adminsids.append(request.sid)
    
@socketio.on('adminRowUpdate')
def handle_queue_update(data, index):
    print("ERROR ERROR")
    
@socketio.on("disconnect")
def handle_disconnect():
    print(request.sid, " disconnected, removing from queue")
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
        userqueue.removeUser(pi_sid)

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    if pi_sid:
        emit('pi_command', data, to=pi_sid)
        
    if data.get("user_agent") != "Pi":
        #throttle, turn = data
        print(data)

@socketio.on('timeleft')
def handle_message(data):
    #print('timeleft:', data)
    timeAllowed = userqueue.getCurrentUser()['timeAllowed']
    notifyAdminsRow({"sid": request.sid, "timeAllowed": timeAllowed, "timeRemaining": data["message"]})


    
if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=4000, debug = True)
    socketio.run(app, host="0.0.0.0", port=4000, debug=True)

