$(document).ready(function() {
    let availableSounds = [];
    let currentAudio = null;

    // Check if an audio format is supported by the browser
    function isAudioFormatSupported(mimeType) {
        const audio = document.createElement('audio');
        return audio.canPlayType(mimeType) !== '';
    }

    // Check if AIFF format is supported
    const isAiffSupported = isAudioFormatSupported('audio/aiff');
    console.log('Browser supports AIFF format:', isAiffSupported);

    // Check browser audio format support
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

    // Log browser audio support on page load
    document.addEventListener('DOMContentLoaded', () => {
        getBestSupportedFormat();
    });

    // Fetch all sounds from the API
    async function fetchSounds() {
        try {
            const response = await fetch(`${API_URL}/timer/sounds`);
            if (!response.ok) {
                throw new Error('Failed to fetch sounds');
            }
            availableSounds = await response.json();
            populateSoundDropdowns();
        } catch (error) {
            console.error('Error fetching sounds:', error);
            // Continue without sounds
            availableSounds = [];
        }
    }

    // Populate sound dropdowns with available sounds
    function populateSoundDropdowns() {
        const soundDropdowns = $('#timer-sound, #edit-timer-sound');
        
        // Clear existing options except the first one (No Sound)
        soundDropdowns.find('option:not(:first)').remove();
        
        // Add sound options
        availableSounds.forEach(sound => {
            soundDropdowns.append(`<option value="${sound.id}">${sound.name}</option>`);
        });
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
            
            // If browser doesn't support AIFF, request conversion
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
                
                // Try with conversion as a last resort if it's an AIFF file
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
        }
    }

    // Fetch and display all available timers
    async function fetchTimers() {
        try {
            const response = await fetch(`${API_URL}/timer`);
            if (!response.ok) {
                throw new Error('Failed to fetch timers');
            }
            const timers = await response.json();
            displayTimers(timers);
        } catch (error) {
            console.error('Error fetching timers:', error);
            $('#timer-list').html('<p>Error loading timers. Please try again later.</p>');
        }
    }

    // Display timers in the UI
    function displayTimers(timers) {
        const timerList = $('#timer-list');
        timerList.empty();

        if (timers.length === 0) {
            timerList.html('<p>No timers available. Create one below!</p>');
            return;
        }

        timers.forEach(timer => {
            const timerCard = $('<div>')
                .addClass('timer-card relative')
                .html(`
                    <span class="delete-button" data-timer-id="${timer.id}">×</span>
                    <h3>${timer.name}</h3>
                    <p>Duration: <span class="timer-duration">${formatTime(timer.duration)}</span></p>
                    <p>Sound: <span class="timer-sound">${getSoundName(timer.sound_id)}</span></p>
                    <button class="edit-button" data-timer-id="${timer.id}">Edit</button>
                `)
                .click(function(e) {
                    // Prevent navigation if delete button or edit button was clicked
                    if ($(e.target).hasClass('delete-button') || $(e.target).hasClass('edit-button')) {
                        return;
                    }
                    // Navigate to timer detail page
                    window.location.href = `timer_detail.html?name=${encodeURIComponent(timer.name)}&id=${timer.id}`;
                });

            timerList.append(timerCard);
        });

        // Add event listeners for delete buttons
        $('.delete-button').click(function(e) {
            e.stopPropagation();
            const timerId = $(this).data('timer-id');
            if (confirm('Are you sure you want to delete this timer?')) {
                deleteTimer(timerId);
            }
        });

        // Add event listeners for edit buttons
        $('.edit-button').click(function(e) {
            e.stopPropagation();
            const timerId = $(this).data('timer-id');
            openEditModal(timerId);
        });
    }

    // Get sound name from sound ID
    function getSoundName(soundId) {
        if (!soundId) return 'None';
        
        const sound = availableSounds.find(s => s.id === soundId);
        return sound ? sound.name : 'Unknown';
    }

    // Open edit modal with timer data
    async function openEditModal(timerId) {
        try {
            const response = await fetch(`${API_URL}/timer/${timerId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch timer details');
            }
            
            const timer = await response.json();
            
            // Populate edit form with timer data
            $('#edit-timer-id').val(timer.id);
            $('#edit-timer-name').val(timer.name);
            
            // Convert duration from seconds to HH:MM:SS format
            $('#edit-timer-duration').val(formatTime(timer.duration));
            
            // Set sound selection
            $('#edit-timer-sound').val(timer.sound_id || '');
            
            // Show modal
            $('#edit-timer-modal').css('display', 'block');
        } catch (error) {
            console.error('Error fetching timer details:', error);
            alert('Failed to load timer details. Please try again.');
        }
    }

    // Delete a timer
    async function deleteTimer(timerId) {
        try {
            const response = await fetch(`${API_URL}/timer/${timerId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete timer');
            }
            
            // Reload timers after deletion
            fetchTimers();
        } catch (error) {
            console.error('Error deleting timer:', error);
            alert('Failed to delete timer. Please try again.');
        }
    }

    // Update a timer
    async function updateTimer(timerId, name, duration, soundId) {
        try {
            const response = await fetch(`${API_URL}/timer/${timerId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    duration: duration,
                    sound_id: soundId || null
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to update timer');
            }
            
            // Reload timers after update
            fetchTimers();
            
            // Close the modal
            $('#edit-timer-modal').css('display', 'none');
        } catch (error) {
            console.error('Error updating timer:', error);
            alert('Failed to update timer. Please try again.');
        }
    }

    // Create a new timer
    async function createTimer(name, duration, soundId) {
        try {
            const response = await fetch(`${API_URL}/timer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    duration: duration,
                    sound_id: soundId || null
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create timer');
            }
            
            // Reload timers after creation
            fetchTimers();
            
            // Clear form
            $('#timer-name').val('');
            $('#timer-duration').val('');
            $('#timer-sound').val('');
        } catch (error) {
            console.error('Error creating timer:', error);
            alert('Failed to create timer. Please try again.');
        }
    }

    // Parse duration string (HH:MM:SS or seconds) to seconds
    function parseDuration(durationStr) {
        if (!durationStr) return 0;
        
        // Convert HH:MM:SS to seconds
        let duration = 0;
        if (durationStr.includes(':')) {
            const parts = durationStr.split(':');
            if (parts.length === 3) {
                duration = (parseInt(parts[0]) * 3600) + (parseInt(parts[1]) * 60) + parseInt(parts[2]);
            } else if (parts.length === 2) {
                duration = (parseInt(parts[0]) * 60) + parseInt(parts[1]);
            }
        } else {
            duration = parseInt(durationStr);
        }
        
        return isNaN(duration) ? 0 : duration;
    }

    // Handle form submission for creating a new timer
    $('#timer-form').submit(function(e) {
        e.preventDefault();
        
        const name = $('#timer-name').val().trim();
        const durationStr = $('#timer-duration').val().trim();
        const soundId = $('#timer-sound').val();
        
        if (!name || !durationStr) {
            alert('Please enter both name and duration');
            return;
        }
        
        const duration = parseDuration(durationStr);
        
        if (duration <= 0) {
            alert('Please enter a valid duration in seconds or HH:MM:SS format');
            return;
        }
        
        createTimer(name, duration, soundId);
    });

    // Handle form submission for editing a timer
    $('#edit-timer-form').submit(function(e) {
        e.preventDefault();
        
        const timerId = $('#edit-timer-id').val();
        const name = $('#edit-timer-name').val().trim();
        const durationStr = $('#edit-timer-duration').val().trim();
        const soundId = $('#edit-timer-sound').val();
        
        if (!timerId || !name || !durationStr) {
            alert('Please enter all required fields');
            return;
        }
        
        const duration = parseDuration(durationStr);
        
        if (duration <= 0) {
            alert('Please enter a valid duration in seconds or HH:MM:SS format');
            return;
        }
        
        updateTimer(timerId, name, duration, soundId);
    });

    // Handle close button for edit modal
    $('.close').click(function() {
        $('#edit-timer-modal').css('display', 'none');
    });

    // Handle clicks outside the modal to close it
    $(window).click(function(e) {
        if ($(e.target).is('#edit-timer-modal')) {
            $('#edit-timer-modal').css('display', 'none');
        }
    });

    // Handle sound preview button clicks
    $('#preview-sound-btn').click(function() {
        const soundId = $('#timer-sound').val();
        playSound(soundId);
    });

    $('#edit-preview-sound-btn').click(function() {
        const soundId = $('#edit-timer-sound').val();
        playSound(soundId);
    });

    // Initial load
    fetchSounds();
    fetchTimers();
}); 