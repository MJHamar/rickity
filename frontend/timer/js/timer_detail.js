$(document).ready(function() {
    // Get timer ID and name from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const timerId = urlParams.get('id');
    const timerName = urlParams.get('name');
    
    // WebSocket connection
    let socket = null;
    let timerState = {
        timer_state: "000000",
        timer_status: 'stopped',
        sound_id: null
    };
    let previousStatus = 'stopped';
    let timerUpdateTimeout = null;
    let availableSounds = [];
    let currentAudio = null;
    
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
    
    // Show or hide sound selector based on timer status
    function updateSoundSelectorVisibility() {
        if (timerState.timer_status === 'stopped' || timerState.timer_status === 'finished') {
            $('#sound-selector').show();
        } else {
            $('#sound-selector').hide();
        }
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
        
        // Update sound selector visibility
        updateSoundSelectorVisibility();
        
        // Update selected sound
        if (timerState.sound_id) {
            $('#timer-sound').val(timerState.sound_id);
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
            
            // Check if we need to play a sound
            if (parsedMessage.play_sound && parsedMessage.sound_id) {
                playSound(parsedMessage.sound_id);
            }
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
    
    // Check if an audio format is supported by the browser
    function isAudioFormatSupported(mimeType) {
        const audio = document.createElement('audio');
        return audio.canPlayType(mimeType) !== '';
    }

    // Check if AIFF format is supported
    const isAiffSupported = isAudioFormatSupported('audio/aiff');
    console.log('Browser supports AIFF format:', isAiffSupported);

    // Get the best supported format
    function getBestSupportedFormat() {
        const formats = {
            mp3: isAudioFormatSupported('audio/mpeg'),
            wav: isAudioFormatSupported('audio/wav'),
            ogg: isAudioFormatSupported('audio/ogg'),
            aiff: isAudioFormatSupported('audio/aiff')
        };
        
        console.log('Browser audio format support:', formats);
        
        // Return the first supported format in order of preference
        if (formats.mp3) return 'mp3';
        if (formats.wav) return 'wav';
        if (formats.ogg) return 'ogg';
        if (formats.aiff) return 'aiff';
        
        // Fallback to MP3 if nothing is explicitly supported
        return 'mp3';
    }

    // Play a sound
    async function playSound(soundId) {
        if (!soundId) return;
        
        // Stop any currently playing sound
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
        
        try {
            console.log(`Attempting to play sound with ID: ${soundId}`);
            
            // Determine if we need format conversion based on browser support
            let requestUrl = `${API_URL}/timer/sounds/${soundId}`;
            const browserSupport = {
                aiff: isAudioFormatSupported('audio/aiff'),
                mp3: isAudioFormatSupported('audio/mpeg'),
                wav: isAudioFormatSupported('audio/wav')
            };
            
            // If this might be an AIFF file and browser doesn't support AIFF, request conversion
            if (!browserSupport.aiff && browserSupport.mp3) {
                // First make a HEAD request to check if it's an AIFF file
                try {
                    const response = await fetch(requestUrl, { method: 'HEAD' });
                    const contentType = response.headers.get('content-type');
                    
                    if (contentType && contentType.includes('audio/aiff')) {
                        console.log('AIFF file detected and browser does not support AIFF. Requesting MP3 conversion.');
                        requestUrl += '?convert_format=mp3';
                    }
                } catch (error) {
                    console.error('Error checking file type:', error);
                }
            }
            
            console.log(`Sound URL: ${requestUrl}`);
            
            // Create a new audio element
            currentAudio = new Audio();
            
            // Set up error handling before setting the source
            currentAudio.addEventListener('error', (e) => {
                console.error('Audio error event:', e);
                if (currentAudio.error) {
                    console.error('Audio error code:', currentAudio.error.code);
                    console.error('Audio error message:', currentAudio.error.message);
                }
            });
            
            // Wait for the audio to be loaded before playing
            currentAudio.addEventListener('canplaythrough', () => {
                console.log('Audio can play through - ready to play');
            });
            
            // AIFF Fallback: If we detect this is an AIFF file and the browser doesn't support it,
            // we'll try to alert the user but continue playback attempt anyway
            const fileExtMatch = requestUrl.match(/\.(wav|mp3|ogg|aiff)$/i);
            const fileExt = fileExtMatch ? fileExtMatch[1].toLowerCase() : '';
            
            if (fileExt === 'aiff' && !isAiffSupported) {
                console.warn('AIFF format not well supported in this browser. Playback may fail or using conversion.');
            }
            
            // Set source and try to play the audio
            currentAudio.src = requestUrl;
            
            // Try to play the audio
            await currentAudio.play();
            console.log('Audio playback started successfully');
        } catch (error) {
            console.error('Error playing sound:', error);
            console.error('Error name:', error.name);
            console.error('Error message:', error.message);
            
            // Show a more user-friendly error message
            if (error.name === 'NotSupportedError') {
                console.log('The audio format is not supported by your browser.');
                
                // If this is an AIFF file, try with conversion as a last resort
                if (requestUrl.includes('audio/aiff') || requestUrl.toLowerCase().endsWith('.aiff')) {
                    const conversionUrl = requestUrl.includes('?') 
                        ? `${requestUrl}&convert_format=mp3` 
                        : `${requestUrl}?convert_format=mp3`;
                        
                    console.log('Trying again with conversion to MP3:', conversionUrl);
                    try {
                        currentAudio = new Audio(conversionUrl);
                        await currentAudio.play();
                        console.log('Playback with conversion successful');
                        return;
                    } catch (convError) {
                        console.error('Conversion attempt also failed:', convError);
                        alert('Your browser does not support AIFF audio files. Please use Safari or convert the sound to MP3 or WAV format.');
                    }
                } else {
                    alert('This audio format is not supported by your browser. Please try a different sound or use a different browser.');
                }
            } else if (error.name === 'NotAllowedError') {
                console.log('The browser blocked autoplay. User interaction might be required first');
            }
            
            // Make an explicit fetch request to check if the file is accessible
            fetch(requestUrl)
                .then(response => {
                    console.log('Fetch response status:', response.status);
                    console.log('Fetch response headers:', Array.from(response.headers.entries()));
                    if (!response.ok) {
                        console.error(`File fetch failed with status: ${response.status}`);
                    } else {
                        console.log('File exists and is accessible');
                        // Check content type
                        const contentType = response.headers.get('content-type');
                        console.log('Content-Type:', contentType);
                        
                        // If it's an AIFF file, suggest conversion
                        if (contentType && contentType.includes('audio/aiff')) {
                            console.log('This is an AIFF file. Using conversion parameter might help.');
                        }
                    }
                })
                .catch(fetchError => {
                    console.error('Failed to fetch the sound file:', fetchError);
                });
        }
    }
    
    // Fetch all sounds from the API
    async function fetchSounds() {
        try {
            const response = await fetch(`${API_URL}/timer/sounds`);
            if (!response.ok) {
                throw new Error('Failed to fetch sounds');
            }
            availableSounds = await response.json();
            populateSoundDropdown();
        } catch (error) {
            console.error('Error fetching sounds:', error);
            // Continue without sounds
            availableSounds = [];
        }
    }
    
    // Populate sound dropdown with available sounds
    function populateSoundDropdown() {
        const soundDropdown = $('#timer-sound');
        
        // Clear existing options except the first one (No Sound)
        soundDropdown.find('option:not(:first)').remove();
        
        // Add sound options
        availableSounds.forEach(sound => {
            soundDropdown.append(`<option value="${sound.id}">${sound.name}</option>`);
        });
        
        // Set the current sound if available
        if (timerState.sound_id) {
            soundDropdown.val(timerState.sound_id);
        }
    }
    
    // Update timer sound
    async function updateTimerSound(soundId) {
        try {
            const response = await fetch(`${API_URL}/timer/${timerId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: timerName,
                    duration: hhmmssToSeconds(timerState.timer_state),
                    sound_id: soundId || null
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to update timer sound');
            }
            
            // Update local state
            timerState.sound_id = soundId;
            
            // Show success message
            alert('Sound saved successfully!');
        } catch (error) {
            console.error('Error updating timer sound:', error);
            alert('Failed to update timer sound. Please try again.');
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
    
    // Handle timer segment editing
    $('.time-segment').on('focus', function() {
        // Select all text when focusing
        const range = document.createRange();
        range.selectNodeContents(this);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    }).on('input', function() {
        const type = $(this).data('type');
        let value = $(this).text().replace(/\D/g, ''); // Remove non-digits
        
        // Enforce limits based on segment type
        if (type === 'hours') {
            // No specific limit for hours
        } else if (type === 'minutes' || type === 'seconds') {
            if (parseInt(value) > 59) value = '59';
        }
        
        // Update display and pad to 2 digits
        $(this).text(value.padStart(2, '0'));
        
        // Send timer update to server
        sendTimerUpdate();
    }).on('blur', function() {
        // Ensure display format is correct on blur
        const value = $(this).text().trim() || '0';
        $(this).text(value.padStart(2, '0'));
    }).on('keydown', function(e) {
        // Handle keydown events (Enter and Escape)
        if (e.key === 'Enter' || e.key === 'Escape') {
            e.preventDefault();
            $(this).blur();
        }
    });
    
    // Handle sound preview button
    $('#preview-sound-btn').click(function() {
        const soundId = $('#timer-sound').val();
        playSound(soundId);
    });
    
    // Handle save sound button
    $('#save-sound-btn').click(function() {
        const soundId = $('#timer-sound').val();
        updateTimerSound(soundId);
    });
    
    // Initialize timer
    function init() {
        updateTimerInfo();
        fetchSounds();
        initializeWebSocket();
        
        // Register event for page unload to cleanly close WebSocket
        window.isLeavingPage = false;
        window.addEventListener('beforeunload', function() {
            window.isLeavingPage = true;
            if (socket) {
                socket.close();
            }
        });
    }
    
    // Start initialization
    init();
}); 