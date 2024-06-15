import React, { useEffect, useState } from 'react';
import './Habit.css';

const Habit = ({ habit }) => {
    const [checkDetails, setCheckDetails] = useState(null);

    useEffect(() => {
        const fetchCheckDetails = async () => {
            try {
                const response = await fetch(`http://127.0.0.1:3140/habits/${habit.id}/check`);
                if (response.ok) {
                    const data = await response.json();
                    setCheckDetails(data);
                } else {
                    console.error('Failed to fetch check details', response.statusText);
                }
            } catch (error) {
                console.error('Error fetching check details:', error.message);
            }
        };

        fetchCheckDetails();
    }, [habit.id]);
    console.log(checkDetails);

    const lastCheckTime = checkDetails && checkDetails.check_dt.length > 0
        ? new Date(checkDetails.check_dt[checkDetails.check_dt.length - 1] * 1000).toUTCString()
        : 'Never';
    // if lastCheckTime is not Never and the last check was within the repetition interval, set isDue to false
    // otherwise, set isDue to true
    const checkInterval = habit.frequency === "1" ? 60 * 60 * 1000 : habit.frequency === "2" ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000;
    const isDue = lastCheckTime !== 'Never' && Date.now() - new Date(checkDetails.check_dt[checkDetails.check_dt.length - 1] * 1000) < checkInterval;
    const divStyle = {
        backgroundColor: isDue ? 'lightgreen' : 'lightcoral'
    };

    const handleCheck = async (event) => {
        // make an API call to localhost:3140/habits/:id/check with POST method
        // if the response is successful, update the checkDetails state
        // otherwise, log the error
        event.preventDefault();

        try {
            const response = await fetch(`http://127.0.0.1:3140/habits/${habit.id}/check`, {
                method: 'POST'
            });
            if (response.ok) {
                const data = await response.json();
                setCheckDetails(data);
            } else {
                console.error('Failed to check habit', response.statusText);
            }
        }
        catch (error) {
            console.error('Error checking habit:', error.message);
        }
    };

    return (
        <div className="habit" style={divStyle} onClick={handleCheck}>
            <h2>{habit.name}</h2>
        </div>
    );
};

export default Habit;
