$(document).ready(function() {
    // Get timer ID and name from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const timerId = urlParams.get('id');
    const timerName = urlParams.get('name');
    
    // WebSocket connection
    let socket = null;
    let timerState = {
        state: 0,
        status: 'stopped'
    };
    
    // Update UI with timer information
    function updateTimerInfo() {
        $('#timer-name').text(timerName);
    }
    
    // Update timer display
    function updateTimerDisplay() {
        console.log('timerState', timerState);
        console.log('timerState.timer_state', timerState['timer_state']);
        console.log('timerState.timer_status', timerState['timer_status']);
        // Update time display
        $('#timer-time').text(formatTime(timerState['timer_state']));
        
        // Update status text and class
        const statusElement = $('#timer-status');
        statusElement.removeClass('status-rolling status-paused status-stopped');
        
        let statusText = '';
        let statusClass = '';
        
        switch(timerState['timer_status']) {
            case 'rolling':
                statusText = 'Running';
                statusClass = 'status-rolling';
                break;
            case 'paused':
                statusText = 'Paused';
                statusClass = 'status-paused';
                break;
            case 'stopped':
                statusText = 'Stopped';
                statusClass = 'status-stopped';
                break;
            default:
                statusText = timerState['timer_status'];
        }
        
        statusElement.text(statusText).addClass(statusClass);
        
        // Update button text based on timer status
        if (timerState['timer_status'] === 'rolling') {
            $('#toggle-button').text('Pause');
        } else {
            $('#toggle-button').text('Continue');
        }
    }

    // Parse WebSocket message format "<timer_state> <timer_status>" (used by timer module)
    function parseTimerMessage(message) {
        const parts = message.trim().split(' ');
        return {
            state: parseInt(parts[0], 10),
            status: parts[1]
        };
    } 
    
    // Initialize WebSocket connection
    function initializeWebSocket() {
        // Close any existing socket
        if (socket) {
            socket.close();
        }
        
        // Create new WebSocket connection
        socket = new WebSocket(`ws://${API_URL.replace('http://', '')}/timer/ws/${timerId}`);
        
        // Handle socket open event
        socket.onopen = function() {
            console.log('WebSocket connection established');
        };
        
        // Handle incoming messages
        socket.onmessage = function(event) {
            console.log('Message received:', event.data);
            const parsedMessage = event.data;
            timerState = parsedMessage;
            updateTimerDisplay();
        };
        
        // Handle socket error
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
            $('#timer-status').text('Connection Error').addClass('status-stopped');
        };
        
        // Handle socket close
        socket.onclose = function() {
            console.log('WebSocket connection closed');
            setTimeout(function() {
                // Attempt to reconnect after 3 seconds
                if (!window.isLeavingPage) {
                    initializeWebSocket();
                }
            }, 3000);
        };
    }
    
    // Send command to WebSocket
    function sendCommand(action) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: action }));
        } else {
            console.error('WebSocket not connected');
            alert('Connection lost. Trying to reconnect...');
            initializeWebSocket();
        }
    }
    
    // Handle toggle button click (pause/continue)
    $('#toggle-button').click(function() {
        if (timerState['timer_status'] === 'rolling') {
            sendCommand('pause');
        } else {
            sendCommand('start');
        }
    });
    
    // Handle reset button click
    $('#reset-button').click(function() {
        sendCommand('stop');
    });
    
    // Set a flag when leaving the page to prevent reconnect attempts
    $(window).on('beforeunload', function() {
        window.isLeavingPage = true;
        if (socket) {
            socket.close();
        }
    });
    
    // Initialize the page
    updateTimerInfo();
    initializeWebSocket();
}); 