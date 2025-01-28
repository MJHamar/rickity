from datetime import timedelta, datetime, time
import re

def end_of_day(dt: datetime) -> datetime:
    """Convert a datetime to the end of that day (23:59:59)"""
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def parse_recurrence(recurrence: str) -> timedelta:
    """Convert a recurrence string to a timedelta object.
    
    Accepts formats like:
    - "7" or "7 days"
    - "day" or "1 day"
    - "month" or "1 month"
    - "week" or "1 week"
    - "2 months"
    """
    # First try to parse as an integer (days)
    try:
        days = int(recurrence)
        return timedelta(days=days)
    except ValueError:
        pass

    # Handle single unit strings (day, week, month)
    unit_mapping = {
        'day': 1,
        'week': 7,
        'month': 30.44  # approximate
    }
    
    recurrence = recurrence.lower().strip()
    if recurrence in unit_mapping:
        return timedelta(days=unit_mapping[recurrence])

    # Parse string format with numbers
    pattern = r"^(\d+)?\s*(day|days|week|weeks|month|months)$"
    match = re.match(pattern, recurrence)
    
    if not match:
        raise ValueError(
            "Invalid recurrence format. Valid formats: '7', '7 days', 'day', '1 day', 'week', '2 weeks', 'month', '2 months'"
        )
    
    amount = int(match.group(1) or 1)  # Default to 1 if no number specified
    unit = match.group(2).rstrip('s')  # Remove 's' to match unit_mapping
    
    days = amount * unit_mapping[unit]
    return timedelta(days=round(days)) 