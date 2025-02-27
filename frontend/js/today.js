$(document).ready(async function() {
    async function fetchTodayHabits() {
        try {
            const response = await fetch(`${API_URL}/habits/due/today`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching today\'s habits:', error);
            return [];
        }
    }

    function renderHabitsList(habits) {
        const habitsList = $('#habits-list');
        habitsList.empty();

        habits.forEach(habit => {
            const durations = habit.latest_log?.durations || [];
            const sum = durations.reduce((acc, d) => acc + parseInt(d.amount), 0);
            const duration = habit.habit.duration;
            const goal = parseInt(duration.amount) || 1;
            const completed = sum >= goal;

            const habitItemHtml = `
                <div class="habit-main">
                    <span class="status-icon">${completed ? '✓' : '×'}</span>
                    <span class="habit-name">${habit.habit.name} (${sum}/${goal})</span>
                </div>
                <div class="durations-list">
                    ${durations.map(d => `
                        <div class="duration-entry" data-duration-id="${d.id}">
                            ${d.amount}
                            <button class="remove-duration">×</button>
                        </div>
                    `).join('')}
                    <button class="add-duration">+ Add</button>
                </div>
            `;
            
            const habitItem = $('<div>', {
                class: `habit-item ${completed ? 'completed' : 'uncompleted'}`,
                'data-log-id': habit.latest_log?.id,
                'data-duration-type': duration.type,
                'data-goal-amount': goal
            }).html(habitItemHtml);
            
            habitsList.append(habitItem);
        });
    }

    // Event delegation for habit item clicks
    $('#habits-list').on('click', '.habit-item', async function() {
        const item = $(this);
        const logId = item.data('log-id');
        const durationType = item.data('duration-type');
        const goalAmount = item.data('goal-amount');

        if (logId && await addLogDuration(logId, durationType, goalAmount)) {
            location.reload(); // Refresh to show updated values
        }
    });

    // Add click handlers
    $('#habits-list').on('click', '.add-duration', async function(e) {
        e.stopPropagation();
        const item = $(this).closest('.habit-item');
        const logId = item.data('log-id');
        const durationType = item.data('duration-type');
        const goalAmount = item.data('goal-amount');
        
        if (await addLogDuration(logId, durationType, goalAmount)) {
            location.reload();
        }
    });

    $('#habits-list').on('click', '.remove-duration', async function(e) {
        e.stopPropagation();
        const durationId = $(this).closest('.duration-entry').data('duration-id');
        if (await removeLogDuration(durationId)) {
            location.reload();
        }
    });

    // Initial load
    const habits = await fetchTodayHabits();
    renderHabitsList(habits);
}); 