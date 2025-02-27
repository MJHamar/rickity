const API_URL = 'http://34.118.115.23:2233';

/**
 * Utility functions used across multiple modules
 */

// Format a date object to YYYY-MM-DD string (used by habits module)
const formatDate = (date) => {
    return date.toISOString().split('T')[0];
};

// Format seconds to HH:mm:ss (used by timer module)
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

// Parse WebSocket message format "<timer_state> <timer_status>" (used by timer module)
function parseTimerMessage(message) {
    const parts = message.trim().split(' ');
    return {
        state: parseInt(parts[0], 10),
        status: parts[1]
    };
} 