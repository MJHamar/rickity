const API_URL = 'http://34.118.115.23:2233';

// Utility functions used across both pages
const formatDate = (date) => {
    return date.toISOString().split('T')[0];
};

const toggleHabitLog = async (logId, completed) => {
    const endpoint = completed ? 'uncheck' : 'check';
    try {
        const response = await fetch(`${API_URL}/habits/${endpoint}/${logId}`, {
            method: 'PUT'
        });
        if (!response.ok) throw new Error('Failed to toggle habit');
        return true;
    } catch (error) {
        console.error('Error toggling habit:', error);
        return false;
    }
}; 