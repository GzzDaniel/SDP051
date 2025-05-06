// Initialize socket connection
const socket = io();
let queueData = [];

// UI elements
const serverStatusEl = document.getElementById('serverStatus');
const carStatusEl = document.getElementById('carStatus');
const activeUsersEl = document.getElementById('activeUsers');
const currentUserEl = document.getElementById('currentUser');
const logContainerEl = document.getElementById('logContainer');
const refreshBtn = document.getElementById('refreshBtn');
const nextUserBtn = document.getElementById('nextUserBtn');
const emergencyStopBtn = document.getElementById('emergencyStopBtn');
const defaultTimeInput = document.getElementById('defaultTimeInput');
const setDefaultTimeBtn = document.getElementById('setDefaultTimeBtn');

// Initialize Tabulator table
const table = new Tabulator("#user-queue-table", {
    data: queueData,
    layout: "fitColumns",
    pagination: false,
    height: "100%",
    index: "sid",
    columns: [
        { title: "Index", field: "Index", formatter: function(cell) {
            const index = cell.getRow().getPosition() -1;
            return index;
        }, width: 100 },
        { title: "Session ID", field: "sid", headerFilter: "input" },
        { title: "Time Allowed (seconds)", field: "timeAllowed", editor: "number", editorParams: {
            min: 10,
            max: 3000,
            step: 5
        }},
        { title: "Time Remaining", field: "timeRemaining", formatter: function(cell) {
            const value = cell.getValue();
            if (value === undefined || value === null) return "N/A";
            return value + "s";
        }},
        { title: "Status", field: "status", formatter: function(cell) {
            const row = cell.getRow();
            const rowIndex = row.getPosition()-1;
            
            if (queueData.current_index !== undefined && rowIndex === queueData.current_index) {
                return "<span style='color:green;font-weight:bold;'>Active</span>";
            } else if (queueData.current_index !== undefined && rowIndex < queueData.current_index) {
                return "<span style='color:gray;'>Waiting</span>";
            } else {
                return "<span style='color:blue;'>In Queue</span>";
            }
        }},
        { 
            title: "Actions", 
            formatter: function(cell) {
                return "<button class='action-btn remove-btn'>Remove</button>";
            },
            cellClick: function(e, cell) {
                if (e.target.classList.contains('remove-btn')) {
                    const row = cell.getRow();
                    const rowData = row.getData();

                    //REMOVE BUTTON 
                    socket.emit('adminRemoveUser', { sid: rowData.sid });
                    addLogEntry(`Removed user ${rowData.sid} from queue`);
                    
                }
            },
            width: 100,
            hozAlign: "center"
        }
    ],
    rowFormatter: function(row) {
        const data = row.getData();
        const rowIndex = row.getPosition()-1;
        
        if (queueData.current_index !== undefined && rowIndex === queueData.current_index) {
            row.getElement().style.backgroundColor = "#d4edda";
        }
    },
    cellEdited: function(cell) {
        const row = cell.getRow();
        const rowData = row.getData();
        
        // Send updated row data to server
        socket.emit('adminUpdateUser', rowData);
        addLogEntry(`Updated user ${rowData.sid}: Time allowed set to ${rowData.timeAllowed}s`);
    }
});

// Socket connection handlers
socket.on('connect', () => {
    serverStatusEl.textContent = 'Connected';
    serverStatusEl.style.color = '#27ae60';
    
    // Request admin access
    socket.emit('adminRequestQueue', { message: 'admin initialization' });
    
    addLogEntry('Connected to server');
});

socket.on('connect_error', (error) => {
    serverStatusEl.textContent = 'Error';
    serverStatusEl.style.color = '#e74c3c';
    
    addLogEntry(`Connection error: ${error.message}`);
});

socket.on('disconnect', () => {
    serverStatusEl.textContent = 'Disconnected';
    serverStatusEl.style.color = '#e67e22';
    
    addLogEntry('Disconnected from server');
});

// Car status updates
socket.on('piStatus', (data) => {
    carStatusEl.textContent = data.connected ? 'Connected' : 'Disconnected';
    carStatusEl.style.color = data.connected ? '#27ae60' : '#e74c3c';
    
    if (data.connected) {
        addLogEntry('RC Car connected to server');
    } else {
        addLogEntry('RC Car disconnected from server');
    }
});

// Queue updates
socket.on('adminResponseQueue', (data) => {
    // Update queue data
    queueData = data;
    console.log(data);
    // Convert the data for Tabulator
    const tableData = data.queue.map((user, index) => {
        return {
            ...user,
            position: index
        };
    });
    
    // Update table
    table.replaceData(tableData);
    
    // Update status info
    activeUsersEl.textContent = data.queue.length;
    
    const currentUserIndex = data.current_index;
    if (currentUserIndex !== undefined && currentUserIndex !== null && data.queue.length > 0) {
        const shortened = data.queue[currentUserIndex].sid.substring(0, 8) + '...';
        currentUserEl.textContent = shortened;
    } else {
        currentUserEl.textContent = 'None';
    }
    
    addLogEntry(`Queue updated: ${data.queue.length} users`);
});

// Row updates
socket.on('adminResponseRow', (row) => {
    // Find the user in the local data
    const userIndex = queueData.queue.findIndex(user => user.sid === row.sid);
    console.log(userIndex);
    if (userIndex !== -1) {
        // Update the user data
        //queueData.queue[userIndex] = {...queueData.queue[userIndex], ...row};
        
        // Update the table
        //console.log(row);
        table.updateData([{sid: row.sid, timeRemaining: row.timeRemaining}]);
    }
});

// Admin notifications from server
socket.on('adminNotification', (data) => {
    addLogEntry(data.message);
});

// _________________ BUTTONS ______________________
// REFRESH BUTTON
refreshBtn.addEventListener('click', () => {
    socket.emit('adminRequestQueue', { message: 'refresh request' });
    addLogEntry('Manual queue refresh requested');
});

// NEXT USER BUTTON
nextUserBtn.addEventListener('click', () => {
    socket.emit('adminForceNext', { message: 'force next user' });
    addLogEntry('Skipped to next user in queue');
});

// EMERGENCY STOP BuTTON
emergencyStopBtn.addEventListener('click', () => {
    if (confirm('EMERGENCY STOP: Are you sure you want to stop all car motors?')) {
        socket.emit('adminEmergencyStop', { message: 'emergency stop' });
        addLogEntry('EMERGENCY STOP triggered');
    }
});

// DEFAULT TIME BUTTON
setDefaultTimeBtn.addEventListener('click', () => {
    const defaultTime = parseInt(defaultTimeInput.value);
    if (defaultTime >= 10 && defaultTime <= 300) {
        socket.emit('adminSetDefaultTime', { time: defaultTime });
        addLogEntry(`Default time set to ${defaultTime} seconds`);
    } else {
        alert('Default time must be between 10 and 300 seconds');
    }
});

// Helper function to add log entries
function addLogEntry(message) {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'log-time';
    timeSpan.textContent = timeStr;
    
    logEntry.appendChild(timeSpan);
    logEntry.appendChild(document.createTextNode(message));
    
    logContainerEl.appendChild(logEntry);
    logContainerEl.scrollTop = logContainerEl.scrollHeight;
    
    // Limit log entries to prevent memory issues
    if (logContainerEl.children.length > 100) {
        logContainerEl.removeChild(logContainerEl.children[0]);
    }
}

// Initialize with a log entry
addLogEntry('Admin panel initialized');