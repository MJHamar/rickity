import React, { useEffect, useState } from 'react';
import Habit from './Habit'; // Import the Habit component

const HabitsList = () => {
    const [habits, setHabits] = useState([]);

    useEffect(() => {
        const fetchHabits = async () => {
            try {
                const response = await fetch('http://127.0.0.1:3140/habits');
                if (response.ok) {
                    const data = await response.json();
                    setHabits(data);
                } else {
                    console.error('Failed to fetch habits', response.statusText);
                }
            } catch (error) {
                console.error('Error fetching habits:', error.message);
            }
        };

        fetchHabits();
    }, []);

    return (
        <div>
            <h1>Habits</h1>
            {habits.length === 0 ? (
                <p>No habits found.</p>
            ) : (
                habits.map(habit => (
                    <Habit key={habit.id} habit={habit} /> // Use the Habit component
                ))
            )}
        </div>
    );
};

export default HabitsList;
