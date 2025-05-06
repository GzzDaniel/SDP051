from flask import Flask, request, render_template, session, redirect, url_for
from flask_socketio import SocketIO, emit
import time

# Initialize Flask app
app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = "SDP051secretkey"
socketio = SocketIO(app)


# User queue management
class UserQueue:
    def __init__(self):
        self.queue = []  # Each element has 'sid', 'timeAllowed', and 'timeRemaining'
        self.current_index = None  # Index of the user with control
        self.default_time = 90  # Default time allowance in seconds
        
    def get_current_user(self):
        """Get the user currently in control. {'timeAllowed' = , 'sid' = }"""
        if self.current_index is None or len(self.queue) == 0:
            return None
        return self.queue[self.current_index]
    
    def activate_current_user(self):
        """Send activation signal to the current user"""
        if self.current_index is None or len(self.queue) == 0:
            return
            
        current_user = self.get_current_user()
        print(f"Activating user: {current_user['sid']}, time allowed: {current_user['timeAllowed']}s")
        emit('timestart', current_user['timeAllowed'], to=current_user['sid'])
    
    def next_user(self):
        """Move to the next user in the queue"""
        if len(self.queue) == 0:
            self.current_index = None
            return

        if len(self.queue) == 1:
            # only one user
            self.current_index = 0
        else:
            self.current_index += 1
            
        if self.current_index >= len(self.queue):
            # reset index position
            self.current_index = 0
            
        self.activate_current_user()
        notify_admins_queue()
            
    def add_user(self, session_id, time_allowed=None):
        """Add a user to the queue"""
        if time_allowed is None:
            time_allowed = self.default_time
            
        user = {
            "sid": session_id, 
            "timeAllowed": time_allowed, 
            "timeRemaining": time_allowed
        }
        self.queue.append(user)
        
        if self.current_index is None:
            self.current_index = len(self.queue) - 1
            self.activate_current_user()
            
        print(f"New client added to queue: {session_id}")
        notify_admins_queue()
        return user
        
    def remove_user(self, session_id):
        """Remove a user from the queue"""
        
        if self.current_index is None or len(self.queue) == 0:
            return
            
        # Check if the user being removed is the active one
        was_active = False
        if self.current_index < len(self.queue) and self.queue[self.current_index]['sid'] == session_id:
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
            self.current_index = None
        elif was_active:
            #deactivate current user
            emit('controlOff', 'ack', to=session_id)
            # If the active user was removed, move to the next user
            if user_index >= len(self.queue):
                self.current_index = 0
            else:
                self.current_index = user_index
                
            if self.current_index is not None and len(self.queue) > 0:
                self.activate_current_user()
        elif user_index < self.current_index:
            # If a user before the active user was removed, adjust index
            self.current_index -= 1
            
        print(f"Client removed from queue: {session_id}")
        notify_admins_queue()
        
    def update_user(self, session_id, time_allowed=None):
        """Update a user's properties"""
        for i, user in enumerate(self.queue):
            if user['sid'] == session_id:
                if time_allowed is not None:
                    user['timeAllowed'] = time_allowed
                return True
        return False
    
    def set_default_time(self, time_seconds):
        """Set the default time allowance for new users"""
        if time_seconds >= 10 and time_seconds <= 300:
            self.default_time = time_seconds
            for userdata in self.queue:
                userdata['timeAllowed'] = time_seconds
                if userdata['timeRemaining'] > time_seconds:
                    userdata['timeRemaining'] = time_seconds
                    self.activate_current_user()
            return True
        return False

# Initialize global variables
user_queue = UserQueue()
admin_sids = []  # List of Socket.IO session IDs for admin users
pi_sid = None    # Socket.IO session ID for the Raspberry Pi

# ====================== ROUTES ======================
@app.route('/')
def index():
    """Serve the main controller page"""
    return render_template('index.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle admin login"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        print(f"Login attempt: {username}")
        
        if username == 'SDP051' and password == 'SDP051051':
            session["can_access_admin"] = True
            return redirect(url_for("admin"))
        
    return render_template('login.html')

@app.route("/admin")
def admin():
    """Serve the admin control panel"""
    if not session.get("can_access_admin"):
        return redirect(url_for("login"))
    
    session.pop("can_access_admin")
    return render_template('admin.html')

# ====================== ADMIN NOTIFICATION FUNCTIONS ======================
def notify_admins_queue():
    """Send the current queue to all admin clients"""
    queue_data = {
        "queue": user_queue.queue,
        "current_index": user_queue.current_index
    }
    for sid in admin_sids:
        emit("adminResponseQueue", queue_data, to=sid)

def notify_admins_row(row):
    """Send updated row data to all admin clients"""
    for sid in admin_sids:
        emit("adminResponseRow", row, to=sid)

def notify_admins(message):
    """Send a notification message to all admin clients"""
    for sid in admin_sids:
        emit("adminNotification", {"message": message, "timestamp": time.time()}, to=sid)

def notify_pi_status():
    """Send Raspberry Pi connection status to all admin clients"""
    status = {"connected": pi_sid is not None}
    for sid in admin_sids:
        emit("piStatus", status, to=sid)

# ====================== SOCKET.IO EVENTS ======================
@socketio.on("connect")
def handle_connect():
    """Handle new client connections"""
    print(f"Client connected: {request.sid}")

@socketio.on("userRequestAdd")
def handle_user_request_add(data):
    """Handle request to add user to the control queue"""
    user = user_queue.add_user(request.sid)
    print(f"User {request.sid} added to queue")

@socketio.on("identify")
def handle_identify(data):
    """Identify special clients (Raspberry Pi)"""
    global pi_sid
    if data.get("user_agent") == "Pi":
        pi_sid = request.sid
        print(f"Pi connected: {pi_sid}")
        notify_pi_status()
        notify_admins("Raspberry Pi connected to server")


# ______________ ADMIN PANEL EVENTS ______________
@socketio.on("adminRequestQueue")
def handle_admin_request_queue(data):
    """Handle admin request for queue data"""
    if request.sid not in admin_sids:
        admin_sids.append(request.sid)
    
    queue_data = {
        "queue": user_queue.queue,
        "current_index": user_queue.current_index
    }
    emit("adminResponseQueue", queue_data, to=request.sid)
    notify_pi_status()

@socketio.on("adminUpdateUser")
def handle_admin_update_user(data):
    """Handle admin request to update a user's settings"""
    if 'sid' in data and 'timeAllowed' in data:
        sid = data['sid']
        time_allowed = int(data['timeAllowed'])
        
        if user_queue.update_user(sid, time_allowed):
            print(f"Admin updated user {sid}: time allowed = {time_allowed}")
            notify_admins(f"Updated time allowed for user {sid} to {time_allowed}s")
            notify_admins_queue()

@socketio.on("adminRemoveUser")
def handle_admin_remove_user(data):
    """Handle admin request to remove a user from the queue"""
    if 'sid' in data:
        sid = data['sid']
        user_queue.remove_user(sid)
        print(f"Admin removed user {sid} from queue")
        notify_admins(f"Removed user {sid} from queue")

@socketio.on("adminForceNext")
def handle_admin_force_next(data):
    """Handle admin request to force next user"""
    #deactivate current user
    emit('controlOff', 'ack', to=user_queue.get_current_user()['sid'])
    print("Admin forced next user")
    notify_admins("Skipped to next user")

@socketio.on("adminEmergencyStop")
def handle_admin_emergency_stop(data):
    """Handle admin emergency stop command"""
    if pi_sid:
        emergency_cmd = {
            "throttle": "stop",
            "turn": "none",
            "throttle_percent": 0,
            "turn_percent": 0,
            "emergency": True
        }
        emit('pi_command', emergency_cmd, to=pi_sid)
        print("EMERGENCY STOP triggered by admin")
        notify_admins("EMERGENCY STOP command sent to Raspberry Pi")
    else:
        notify_admins("EMERGENCY STOP failed - No Raspberry Pi connected")

@socketio.on("adminSetDefaultTime")
def handle_admin_set_default_time(data):
    """Handle admin request to set default time"""
    time_seconds = int(data['time'])
    if user_queue.set_default_time(time_seconds):
        print(f"Admin set default time to {time_seconds}s")
        notify_admins(f"Default time set to {time_seconds} seconds effect in server")
#___________________________________________________________________________


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    global pi_sid
    
    # Check if this is the Pi disconnecting
    if request.sid == pi_sid:
        pi_sid = None
        print("Pi disconnected")
        notify_pi_status()
        notify_admins("Raspberry Pi disconnected from server")
    else:
        # Handle regular user disconnect
        user_queue.remove_user(request.sid)
        
        # Also remove from admin list if applicable
        if request.sid in admin_sids:
            admin_sids.remove(request.sid)
        
        print(f"Client disconnected: {request.sid}")

@socketio.on("timeover")
def handle_timeover(data):
    """Handle user's control time ending"""
    print(f"Time ended for user: {request.sid}")
    current_user = user_queue.get_current_user()
    
    # Only allow the current active user to trigger next user
    if current_user and current_user['sid'] == request.sid:
        user_queue.next_user()

@socketio.on("timeleft")
def handle_timeleft(data):
    """Handle update on user's remaining time"""
    time_remaining = data.get("message", 0)
    
    current_user = user_queue.get_current_user()
    if current_user and current_user['sid'] == request.sid:
        current_user['timeRemaining'] = time_remaining
        notify_admins_row(current_user)

@socketio.on("controlData")
def handle_message(data):
    """Handle control messages from users"""
    global pi_sid
    
    if not pi_sid:
        print("Received control command but no Pi is connected")
        print("INFO: ", data)
        return
    
    # Only process commands from the current active user
    current_user = user_queue.get_current_user()
    if current_user and current_user['sid'] == request.sid:
        # Forward the command to the Pi
        emit('pi_command', data, to=pi_sid)
        print(f"Forwarded command to Pi: {data}")
    else:
        # Ignore commands from non-active users
        print(f"Ignored command from non-active user: {request.sid}")



if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=4000, debug=True)
   