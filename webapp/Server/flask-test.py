from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
import time

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "SDP051secretkey"
socketio = SocketIO(app, cors_allowed_origins='*')

# User queue management
class UserQueue:
    def __init__(self):
        self.queue = []  # Each element has 'sid' and 'timeAllowed'
        self.idx = None  # Index pointing to the user in control
        
    def get_current_user(self):
        if self.idx is None or len(self.queue) == 0:
            return None
        return self.queue[self.idx]
    
    def activate_current_user(self):
        if self.idx is None or len(self.queue) == 0:
            return
            
        current_user = self.get_current_user()
        print(f"Activating user: {current_user['sid']}, time allowed: {current_user['timeAllowed']}s")
        emit('timestart', current_user['timeAllowed'], to=current_user['sid'])
    
    def next_user(self):
        if len(self.queue) == 0:
            self.idx = None
            return
            
        if self.idx is None:
            self.idx = 0
        else:
            self.idx += 1
            
        if self.idx >= len(self.queue):
            self.idx = 0
            
        self.activate_current_user()
            
    def add_user(self, session_id, time_allowed=60):
        user = {"sid": session_id, "timeAllowed": time_allowed, "timeRemaining": time_allowed}
        self.queue.append(user)
        
        if self.idx is None:
            self.idx = len(self.queue) - 1
            self.activate_current_user()
            
        print(f"New client connected: {session_id}")
        self.print_info()
        return user
        
    def remove_user(self, session_id):
        if self.idx is None or len(self.queue) == 0:
            return
            
        # Check if the user being removed is the active one
        was_active = False
        if self.idx < len(self.queue) and self.queue[self.idx]['sid'] == session_id:
            was_active = True
        
        # Find and remove the user
        user_index = -1
        for i, user in enumerate(self.queue):
            if user['sid'] == session_id:
                user_index = i
                break
                
        if user_index == -1:
            return
            
        del self.queue[user_index]
        
        # Update index if necessary
        if len(self.queue) == 0:
            self.idx = None
        elif was_active or self.idx >= len(self.queue):
            self.idx = 0 if len(self.queue) > 0 else None
            if self.idx is not None:
                self.activate_current_user()
        elif user_index < self.idx:
            # If we removed someone before the active user, adjust index
            self.idx -= 1
            
        print(f"Client disconnected: {session_id}")
        self.print_info()
        
    def print_info(self):
        print(f"Queue size: {len(self.queue)}")
        print("Active users:", [user['sid'] for user in self.queue])
        if self.idx is not None and len(self.queue) > 0:
            print(f"User with control: {self.queue[self.idx]['sid']}")
        else:
            print("User with control: NONE")

# Initialize user queue and track admin connections
user_queue = UserQueue()
admin_sids = []
pi_sid = None  # Track the Raspberry Pi connection

# ====================== ROUTES ======================
@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    from flask import session, redirect, url_for
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == 'SDP051' and password == 'SDP051051':
            session["can_access_admin"] = True
            return redirect(url_for("admin"))
        
    return render_template('login.html')

@app.route("/admin")
def admin():
    from flask import session, redirect, url_for
    
    if not session.get("can_access_admin"):
        return redirect(url_for("login"))
    
    session.pop("can_access_admin")
    return render_template('admin.html')

# ====================== SOCKET.IO EVENTS ======================
@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on("userRequestAdd")
def handle_user_request_add(data):
    user = user_queue.add_user(request.sid)
    notify_admins_queue()

@socketio.on("identify")
def handle_identify(data):
    global pi_sid
    if data.get("user_agent") == "Pi":
        pi_sid = request.sid
        print(f"Pi connected: {pi_sid}")
        notify_admins("Pi connected to server")
        # Send immediate stop command to ensure car is in a safe state
        if pi_sid:
            emit('pi_command', {
                'throttle': 'stop',
                'turn': 'none',
                'throttle_percent': 0,
                'turn_percent': 0
            }, to=pi_sid)

@socketio.on("adminRequestQueue")
def handle_admin_request_queue(data):
    admin_sids.append(request.sid)
    queue_data = {
        "queue": user_queue.queue,
        "current_index": user_queue.idx
    }
    emit("adminResponseQueue", queue_data, to=request.sid)

@socketio.on("disconnect")
def handle_disconnect():
    global pi_sid
    
    # Check if this is the Pi disconnecting
    if request.sid == pi_sid:
        pi_sid = None
        print("Pi disconnected")
        notify_admins("Pi disconnected from server")
    else:
        # Handle regular user disconnect
        user_queue.remove_user(request.sid)
        
        # Also remove from admin list if applicable
        if request.sid in admin_sids:
            admin_sids.remove(request.sid)
        
        notify_admins_queue()

@socketio.on("timeover")
def handle_timeover(data):
    print(f"Time ended for: {request.sid}")
    
    # Send stop command to Pi
    if pi_sid:
        emit('pi_command', {
            'throttle': 'stop',
            'turn': 'none',
            'throttle_percent': 0,
            'turn_percent': 0
        }, to=pi_sid)
    
    # Move to next user
    user_queue.next_user()

@socketio.on("timeleft")
def handle_timeleft(data):
    time_remaining = data.get("message", 0)
    
    current_user = user_queue.get_current_user()
    if current_user and current_user['sid'] == request.sid:
        current_user['timeRemaining'] = time_remaining
        notify_admins_row(current_user)

@socketio.on("message")
def handle_message(data):
    global pi_sid
    
    # Process control message
    if isinstance(data, dict):
        throttle = data.get("throttle")
        turn = data.get("turn")
        throttle_percent = data.get("throttle_percent", 0)
        turn_percent = data.get("turn_percent", 0)
        
        # Log the command (with percentage details)
        print(f"Control message - Throttle: {throttle} ({throttle_percent}%), Turn: {turn} ({turn_percent}%)")
        
        # Check if sender is the active user
        current_user = user_queue.get_current_user()
        if current_user and current_user['sid'] == request.sid:
            # Forward the command to the Pi
            if pi_sid:
                # Make sure we send the percentage values along with the direction
                emit('pi_command', {
                    'throttle': throttle,
                    'turn': turn,
                    'throttle_percent': throttle_percent,
                    'turn_percent': turn_percent
                }, to=pi_sid)
            else:
                print("No Pi connected to receive command")
        else:
            # Ignore commands from non-active users
            print(f"Ignoring command from non-active user: {request.sid}")

# Admin operations
@socketio.on("adminSetDefaultTime")
def handle_admin_set_default_time(data):
    default_time = data.get("time", 60)
    # Implementation to change default time
    print(f"Admin set default time to {default_time} seconds")
    notify_admins(f"Default time set to {default_time} seconds")

@socketio.on("adminUpdateUser")
def handle_admin_update_user(data):
    # Update user data in queue
    sid = data.get("sid")
    new_time = data.get("timeAllowed")
    
    for user in user_queue.queue:
        if user["sid"] == sid and new_time:
            user["timeAllowed"] = new_time
            notify_admins_row(user)
            break
    
    notify_admins(f"Updated user {sid} time to {new_time}s")

@socketio.on("adminRemoveUser")
def handle_admin_remove_user(data):
    sid = data.get("sid")
    user_queue.remove_user(sid)
    notify_admins(f"Admin removed user {sid} from queue")

@socketio.on("adminForceNext")
def handle_admin_force_next(data):
    # Send stop command to Pi
    if pi_sid:
        emit('pi_command', {
            'throttle': 'stop',
            'turn': 'none',
            'throttle_percent': 0,
            'turn_percent': 0
        }, to=pi_sid)
    
    # Move to next user
    user_queue.next_user()
    notify_admins("Admin forced next user")

@socketio.on("adminEmergencyStop")
def handle_admin_emergency_stop(data):
    # Emergency stop - send stop command to Pi
    if pi_sid:
        emit('pi_command', {
            'throttle': 'stop',
            'turn': 'none',
            'throttle_percent': 0,
            'turn_percent': 0
        }, to=pi_sid)
        notify_admins("EMERGENCY STOP initiated")
    else:
        notify_admins("EMERGENCY STOP failed - Pi not connected")

# ====================== ADMIN FUNCTIONS ======================
def notify_admins_queue():
    """Send the current queue to all admins"""
    queue_data = {
        "queue": user_queue.queue,
        "current_index": user_queue.idx
    }
    for sid in admin_sids:
        emit("adminResponseQueue", queue_data, to=sid)

def notify_admins_row(row):
    """Send updated row data to all admins"""
    for sid in admin_sids:
        emit("adminResponseRow", row, to=sid)

def notify_admins(message):
    """Send a notification to all admins"""
    for sid in admin_sids:
        emit("adminNotification", {"message": message, "timestamp": time.time()}, to=sid)

# ====================== MAIN ======================
if __name__ == '__main__':
    try:
        # Start server
        print("Starting server on 0.0.0.0:4000")
        socketio.run(app, host="0.0.0.0", port=4000, debug=True)
    except KeyboardInterrupt:
        print("Server shutting down")