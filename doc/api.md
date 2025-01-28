## API

### Endpoints

- GET /habits - List all habits
- POST /habits - Create a new habit. Payload: { name: string, recurrence: string }
- PUT /habits/:id - Update a habit. Payload: { name: string, recurrence: string }
- DELETE /habits/:id - Delete a habit

- GET /habits/due?date=YYYY-MM-DD - Get list of habits due on the specified date
- PUT /habits/check/:id - Mark a habit log as completed

### Habit Logs
Habit logs are created from habits. At the start of each day, the API will check if any habits are due and create a log for each habit. These logs should then be 
