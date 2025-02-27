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
                
                const durations = habitLog?.latest_log?.durations || [];
                const sum = durations.reduce((acc, d) => acc + parseInt(d.amount), 0);
                const goal = parseInt(habit.duration?.amount) || 1;
                const completed = sum >= goal;
                
                const cell = $('<td>', {
                    class: `habit-cell ${completed ? 'completed' : 'uncompleted'}`,
                    'data-log-id': habitLog?.latest_log?.id,
                    'data-completed': completed,
                    'data-duration-type': habit.duration?.type,
                    'data-goal-amount': goal
                }).html(`
                    <div class="progress-container">
                        <span class="progress-text">${sum}/${goal}</span>
                        ${durations.map(d => `
                            <div class="duration-entry" data-duration-id="${d.id}">
                                ${d.amount}
                                <button class="remove-duration">×</button>
                            </div>
                        `).join('')}
                    </div>
                    <button class="add-duration">+</button>
                `);
                
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
        const durationType = cell.data('duration-type');
        const goalAmount = cell.data('goal-amount');

        if (logId && await addLogDuration(logId, durationType, goalAmount)) {
            location.reload();
        }
    });

    // Event delegation for add duration clicks
    $('#habits-table').on('click', '.add-duration', async function(e) {
        e.stopPropagation();
        const cell = $(this).closest('.habit-cell');
        const logId = cell.data('log-id');
        const durationType = cell.data('duration-type');
        const goalAmount = cell.data('goal-amount');
        
        if (await addLogDuration(logId, durationType, goalAmount)) {
            location.reload();
        }
    });

    // Event delegation for remove duration clicks
    $('#habits-table').on('click', '.remove-duration', async function(e) {
        e.stopPropagation();
        const durationId = $(this).closest('.duration-entry').data('duration-id');
        if (await removeLogDuration(durationId)) {
            location.reload();
        }
    });

    // Initial load
    const habits = await fetchHabits();
    populateHeaders(habits);
    await populateTable(habits);
}); 