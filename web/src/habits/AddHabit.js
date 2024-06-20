import React, { useState } from 'react';
import { api_url } from '../config';

const AddHabit = () => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [frequency, setFrequency] = useState('');

    const handleSubmit = async (event) => {
        event.preventDefault();

        const habit = {
            name: name,
            description: description,
            create_dt: new Date().toISOString(),
            frequency: frequency
        };

        try {
            const response = await fetch(`${api_url}/habits`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(habit)
            });
            if (response.ok) {
                const data = await response.json();
                console.log('Habit added:', data);
                // Optionally, reset the form or give feedback to the user
                setName('');
                setDescription('');
                setFrequency('');
            } else {
                console.error('Failed to add habit', response.statusText);
            }
        } catch (error) {
            console.error('Error adding habit:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Enter a new habit"
                required
            />
            <input
                type="text"
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Enter a description"
                required
            />
            <select
                value={frequency}
                onChange={e => setFrequency(e.target.value)}
                required
            >
                <option value="" disabled>Select frequency</option>
                <option value="0">Any time</option>
                <option value="1">Hourly</option>
                <option value="2">Daily</option>
                <option value="3">Weekly</option>
            </select>
            <button type="submit">Add Habit</button>
        </form>
    );
}

export default AddHabit;
