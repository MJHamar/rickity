$(document).ready(async function() {
    const DAYS_TO_SHOW = 7;

    async function fetchHabits() {
        try {
            const response = await fetch(`${API_URL}/habits`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching habits:', error);
            return [];
        }
    }

    async function fetchHabitsForDate(date) {
        try {
            const response = await fetch(`${API_URL}/habits/due?date=${formatDate(date)}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching habits for date:', error);
            return [];
        }
    }

    function populateHeaders(habits) {
        const headerRow = $('#habit-headers');
        habits.forEach(habit => {
            headerRow.append(`<th>${habit.name}</th>`);
        });
    }

    async function populateTable(habits) {
        console.log('Starting populateTable with habits:', habits);
        const tbody = $('#habits-body');
        tbody.empty();

        for (let i = 0; i < DAYS_TO_SHOW; i++) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            console.log(`Processing date: ${formatDate(date)}`);
            
            const habitLogs = await fetchHabitsForDate(date);
            console.log('Fetched habit logs:', habitLogs);
            
            const row = $('<tr>');
            row.append(`<td>${formatDate(date)}</td>`);

            habits.forEach(habit => {
                console.log(`Processing habit: ${habit.name} (${habit.id})`);
                const habitLog = habitLogs.find(log => log.habit.id === habit.id);
                console.log('Found habit log:', habitLog);
                
                const completed = habitLog?.latest_log?.completed || false;
                const logId = habitLog?.latest_log?.id;
                console.log(`Status - completed: ${completed}, logId: ${logId}`);
                
                const cell = $('<td>', {
                    class: `habit-cell ${completed ? 'completed' : 'uncompleted'}`,
                    'data-log-id': logId,
                    'data-completed': completed
                });
                
                row.append(cell);
            });

            tbody.append(row);
        }
        console.log('Finished populating table');
    }

    // Event delegation for habit cell clicks
    $('#habits-table').on('click', '.habit-cell', async function() {
        const cell = $(this);
        const logId = cell.data('log-id');
        const completed = cell.data('completed');

        if (logId && await toggleHabitLog(logId, completed)) {
            cell.toggleClass('completed uncompleted');
            cell.data('completed', !completed);
        }
    });

    // Initial load
    const habits = await fetchHabits();
    populateHeaders(habits);
    await populateTable(habits);
}); 