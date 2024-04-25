import React from 'react';
import Habit from './Habit';

const HabitList = () => {
    const habits = [
        { id: 1, name: "Read 20 pages of a book", completed: false },
        { id: 2, name: "Walk 5000 steps", completed: true }
    ];

    return (
        <div>
            {habits.map(habit => (
                <Habit key={habit.id} habit={habit} />
            ))}
        </div>
    );
}

export default HabitList;
