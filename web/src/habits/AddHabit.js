import React, { useState } from 'react';

const AddHabit = () => {
    const [name, setName] = useState('');

    const handleSubmit = (event) => {
        event.preventDefault();
        // Logic to add the habit
        console.log('Adding Habit:', name);
        setName('');
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Enter a new habit"
            />
            <button type="submit">Add Habit</button>
        </form>
    );
}

export default AddHabit;
