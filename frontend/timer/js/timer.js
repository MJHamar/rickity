$(document).ready(function() {
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
                `)
                .click(function(e) {
                    // Prevent navigation if delete button was clicked
                    if ($(e.target).hasClass('delete-button')) {
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

    // Create a new timer
    async function createTimer(name, duration) {
        try {
            const response = await fetch(`${API_URL}/timer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    duration: duration
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
        } catch (error) {
            console.error('Error creating timer:', error);
            alert('Failed to create timer. Please try again.');
        }
    }

    // Handle form submission for creating a new timer
    $('#timer-form').submit(function(e) {
        e.preventDefault();
        
        const name = $('#timer-name').val().trim();
        const durationStr = $('#timer-duration').val().trim();
        
        if (!name || !durationStr) {
            alert('Please enter both name and duration');
            return;
        }
        
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
        
        if (isNaN(duration) || duration <= 0) {
            alert('Please enter a valid duration in seconds or HH:MM:SS format');
            return;
        }
        
        createTimer(name, duration);
    });

    // Initial load
    fetchTimers();
}); 