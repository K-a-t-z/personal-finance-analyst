from datetime import datetime, date


def parse_date(value: str) -> date:
    """
    Parse a date string in the format "Sat, 24 Jun 2025".
    
    Args:
        value: Date string to parse (e.g., "Sat, 24 Jun 2025")
        
    Returns:
        datetime.date object
        
    Raises:
        ValueError: If the date string cannot be parsed in the expected format
    """
    if not isinstance(value, str):
        raise ValueError(f"Expected string, got {type(value).__name__}")
    
    # Strip whitespace
    value = value.strip()
    
    if not value:
        raise ValueError("Empty date string cannot be parsed")
    
    try:
        # Parse using the expected format: "%a, %d %b %Y"
        # Example: "Sat, 24 Jun 2025"
        dt = datetime.strptime(value, "%a, %d %b %Y")
        return dt.date()
    except ValueError as e:
        raise ValueError(
            f"Failed to parse date '{value}'. Expected format: 'Day, DD Mon YYYY' "
            f"(e.g., 'Sat, 24 Jun 2025'). Original error: {str(e)}"
        ) from e
