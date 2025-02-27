const API_URL = 'http://34.118.115.23:2233';

// Utility functions used across both pages
const formatDate = (date) => {
    return date.toISOString().split('T')[0];
};

const addLogDuration = async (logId, durationType, goalAmount) => {
    let amount = '1'; // Default for count type
    
    if (durationType === 'minutes') {
        const minutes = prompt(`Enter minutes (goal: ${goalAmount}):`);
        if (!minutes || isNaN(minutes)) return false;
        amount = minutes;
    }

    try {
        const response = await fetch(
            `${API_URL}/habits/logs/${logId}/durations?amount=${amount}`,
            { method: 'POST' }
        );
        return response.ok;
    } catch (error) {
        console.error('Error adding duration:', error);
        return false;
    }
};

const removeLogDuration = async (durationId) => {
    try {
        const response = await fetch(
            `${API_URL}/habits/logs/durations/${durationId}`,
            { method: 'DELETE' }
        );
        return response.ok;
    } catch (error) {
        console.error('Error removing duration:', error);
        return false;
    }
}; 