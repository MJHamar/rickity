$(document).ready(function() {
    // Get timer ID and name from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const timerId = urlParams.get('id');
    const timerName = urlParams.get('name');
    
    // WebSocket connection
    let socket = null;
    let timerState = {
        timer_state: 0,
        timer_status: 'stopped'
    };
    let previousStatus = 'stopped';
    
    // Update UI with timer information
    function updateTimerInfo() {
        $('#timer-name').text(timerName);
    }
    
    // Create fireworks animation
    function createFireworks() {
        const fireworksContainer = $('<div class="fireworks"></div>');
        $('.timer-display').append(fireworksContainer);

        // Create 50 firework particles with random colors and positions
        for (let i = 0; i < 50; i++) {
            const xPos = Math.random() * 200 - 100; // Random x position (-100 to 100)
            const yPos = Math.random() * 200 - 100; // Random y position (-100 to 100)
            
            // Random color - festive colors
            const colors = [
                '#FF5252', // Red
                '#FFEB3B', // Yellow
                '#4CAF50', // Green
                '#2196F3', // Blue
                '#E040FB'  // Purple
            ];
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            const firework = $('<div class="firework"></div>');
            firework.css({
                'background-color': color,
                '--x': xPos + 'px',
                '--y': yPos + 'px',
                'left': '50%',
                'top': '50%'
            });
            
            fireworksContainer.append(firework);
        }
        
        // Remove fireworks after animation completes
        setTimeout(() => {
            fireworksContainer.remove();
        }, 1500);
    }
    
    // Update timer display
    function updateTimerDisplay() {
        // Update time display
        $('#timer-time').text(formatTime(timerState.timer_state));
        
        // Update status text and class
        const statusElement = $('#timer-status');
        statusElement.removeClass('status-rolling status-paused status-stopped status-finished');
        
        let statusText = '';
        let statusClass = '';
        const timerDisplayElement = $('.timer-display');
        
        // If status changed to 'finished' from another status, create fireworks
        if (timerState.timer_status === 'finished' && previousStatus !== 'finished') {
            createFireworks();
        }
        
        // Save current status for next comparison
        previousStatus = timerState.timer_status;
        
        switch(timerState.timer_status) {
            case 'rolling':
                statusText = 'Running';
                statusClass = 'status-rolling';
                timerDisplayElement.css('background-color', 'var(--pastel-running)');
                break;
            case 'paused':
                statusText = 'Paused';
                statusClass = 'status-paused';
                timerDisplayElement.css('background-color', 'var(--pastel-paused)');
                break;
            case 'stopped':
                statusText = 'Stopped';
                statusClass = 'status-stopped';
                timerDisplayElement.css('background-color', 'var(--pastel-stopped)');
                break;
            case 'finished':
                statusText = 'Finished!';
                statusClass = 'status-finished';
                timerDisplayElement.css('background-color', 'var(--pastel-finished)');
                break;
            default:
                statusText = timerState.timer_status;
                timerDisplayElement.css('background-color', 'var(--pastel-running)');
        }
        
        statusElement.text(statusText).addClass(statusClass);
        
        // Update button text based on timer status
        if (timerState.timer_status === 'rolling') {
            $('#toggle-button').text('Pause');
        } else if (timerState.timer_status === 'paused') {
            $('#toggle-button').text('Resume');
        } else {
            $('#toggle-button').text('Start');
        }
    }

    // Parse WebSocket message format "{'timer_state': <timer_state> 'timer_status': <timer_status>}" (used by timer module)
    function parseTimerMessage(message) {
        const parsedMessage = JSON.parse(message);
        return parsedMessage;
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
            const parsedMessage = parseTimerMessage(event.data);
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
        if (timerState.timer_status === 'rolling') {
            sendCommand('pause');
        } else if (timerState.timer_status === 'paused') {
            sendCommand('resume');
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