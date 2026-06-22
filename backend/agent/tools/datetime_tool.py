from datetime import datetime


def tell_time_date() -> str:
    """Return the current date and time."""
    return datetime.now().strftime("It is %A, %B %d %Y, %H:%M")
