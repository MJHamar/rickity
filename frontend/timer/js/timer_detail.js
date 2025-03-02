$(document).ready(function() {
    // Get timer ID and name from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const timerId = urlParams.get('id');
    const timerName = urlParams.get('name');
    
    // WebSocket connection
    let socket = null;
    let timerState = {
        timer_state: "000000",
        timer_status: 'stopped'
    };
    let previousStatus = 'stopped';
    let timerUpdateTimeout = null;
    
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
    
    // Parse HHmmss format to display as HH:mm:ss
    function parseTimerFormat(hhmmss) {
        if (!hhmmss || typeof hhmmss !== 'string' || hhmmss.length !== 6) {
            return { hours: '00', minutes: '00', seconds: '00' };
        }
        
        return {
            hours: hhmmss.substring(0, 2),
            minutes: hhmmss.substring(2, 4),
            seconds: hhmmss.substring(4, 6)
        };
    }
    
    // Convert display format (HH:mm:ss) to internal format (HHmmss)
    function getTimerValue() {
        const hours = $('#hours').text().padStart(2, '0');
        const minutes = $('#minutes').text().padStart(2, '0');
        const seconds = $('#seconds').text().padStart(2, '0');
        
        return hours + minutes + seconds;
    }
    
    // Make timer segments editable or non-editable based on timer status
    function updateTimerEditability() {
        const isEditable = timerState.timer_status !== 'rolling';
        
        $('.time-segment').each(function() {
            if (isEditable) {
                $(this).addClass('editable').attr('contenteditable', 'true');
            } else {
                $(this).removeClass('editable').removeAttr('contenteditable');
            }
        });
    }
    
    // Update timer display
    function updateTimerDisplay() {
        // Parse timer state (HHmmss format)
        const timeComponents = parseTimerFormat(timerState.timer_state);
        
        // Update time segments
        $('#hours').text(timeComponents.hours);
        $('#minutes').text(timeComponents.minutes);
        $('#seconds').text(timeComponents.seconds);
        
        // Update timer editability
        updateTimerEditability();
        
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

    // Parse WebSocket message
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
    
    // Send set timer command with debounce
    function sendTimerUpdate() {
        // Clear any existing timeout
        if (timerUpdateTimeout) {
            clearTimeout(timerUpdateTimeout);
        }
        
        // Set a new timeout - only send after 300ms of no changes
        timerUpdateTimeout = setTimeout(function() {
            const timerValue = getTimerValue();
            
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ set: timerValue }));
                console.log('Sending timer update:', timerValue);
            } else {
                console.error('WebSocket not connected');
                alert('Connection lost. Trying to reconnect...');
                initializeWebSocket();
            }
        }, 300);
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
    
    // Handle timer value changes
    $(document).on('focus', '.time-segment', function() {
        // Select all text when focused
        const range = document.createRange();
        range.selectNodeContents(this);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    });
    
    $(document).on('input', '.time-segment', function() {
        const type = $(this).data('type');
        let value = $(this).text().replace(/\D/g, ''); // Remove non-digits
        
        // Apply limits based on segment type
        if (type === 'hours') {
            // No specific limit for hours, but keep it 2 digits
            if (value.length > 2) value = value.substring(0, 2);
        } else if (type === 'minutes' || type === 'seconds') {
            // Limit to 0-59
            if (value.length > 2) value = value.substring(0, 2);
            if (parseInt(value) > 59) value = '59';
        }
        
        // Update the segment text
        $(this).text(value.padStart(2, '0'));
        
        // Trigger update after change
        sendTimerUpdate();
    });
    
    // Handle paste to strip formatting and non-numeric characters
    $(document).on('paste', '.time-segment', function(e) {
        e.preventDefault();
        const clipboardData = e.originalEvent.clipboardData || window.clipboardData;
        const pastedText = clipboardData.getData('text');
        const numericText = pastedText.replace(/\D/g, '');
        document.execCommand('insertText', false, numericText);
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