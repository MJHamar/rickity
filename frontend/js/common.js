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

// Format HHmmss string to HH:mm:ss display format
function formatHhmmss(hhmmss) {
    if (!hhmmss || typeof hhmmss !== 'string' || hhmmss.length !== 6) {
        return '00:00:00';
    }
    
    const hours = hhmmss.substring(0, 2);
    const minutes = hhmmss.substring(2, 4);
    const seconds = hhmmss.substring(4, 6);
    
    return `${hours}:${minutes}:${seconds}`;
}

// Convert seconds to HHmmss format
function secondsToHhmmss(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${String(hours).padStart(2, '0')}${String(minutes).padStart(2, '0')}${String(secs).padStart(2, '0')}`;
}

// Convert HHmmss to seconds
function hhmmssToSeconds(hhmmss) {
    if (!hhmmss || typeof hhmmss !== 'string' || hhmmss.length !== 6) {
        return 0;
    }
    
    const hours = parseInt(hhmmss.substring(0, 2), 10);
    const minutes = parseInt(hhmmss.substring(2, 4), 10);
    const seconds = parseInt(hhmmss.substring(4, 6), 10);
    
    return hours * 3600 + minutes * 60 + seconds;
}

/**
 * Production-ready cache busting for JavaScript files
 * Uses a fixed version number that should be updated with each deployment
 * @param {string} jsFilePath - Path to the JavaScript file
 * @returns {string} Path with cache busting query parameter
 */
function getVersionedJsPath(jsFilePath) {
    // In production, use a fixed version number that changes only when files are updated
    // This version should be updated during deployment or release process
    const APP_VERSION = '1.0.0';
    return `${jsFilePath}?v=${APP_VERSION}`;
}
