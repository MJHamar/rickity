import React from 'react';
import HabitList from './habits/HabitList';
import AddHabit from './habits/AddHabit';

function App() {
  return (
    <div className="App">
      <h1>Habit Tracker</h1>
      <AddHabit />
      <HabitList />
    </div>
  );
}

export default App;