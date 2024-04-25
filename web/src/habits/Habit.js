import React from 'react';

const Habit = ({ habit }) => {
    return (
        <div>
            <h3>{habit.name}</h3>
            <p>Status: {habit.completed ? "Completed" : "Pending"}</p>
        </div>
    );
}

export default Habit;
