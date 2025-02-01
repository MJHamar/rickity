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
            const completed = habit.latest_log?.completed || false;
            const habitItem = $('<div>', {
                class: `habit-item ${completed ? 'completed' : 'uncompleted'}`,
                'data-log-id': habit.latest_log?.id,
                'data-completed': completed,
                text: habit.habit.name
            });
            
            habitsList.append(habitItem);
        });
    }

    // Event delegation for habit item clicks
    $('#habits-list').on('click', '.habit-item', async function() {
        const item = $(this);
        const logId = item.data('log-id');
        const completed = item.data('completed');

        if (logId && await toggleHabitLog(logId, completed)) {
            item.toggleClass('completed uncompleted');
            item.data('completed', !completed);
        }
    });

    // Initial load
    const habits = await fetchTodayHabits();
    renderHabitsList(habits);
}); 