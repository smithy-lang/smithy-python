from datetime import datetime, timezone


def ensure_utc(value: datetime) -> datetime:
    """Ensures that the given datetime is a UTC timezone-aware datetime.

    If the datetime isn't timzezone-aware, its timezone is set to UTC. If it is
    aware, it's replaced with the equivalent datetime under UTC.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    else:
        return value.astimezone(timezone.utc)
