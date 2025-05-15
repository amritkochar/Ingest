# src/utils/time_utils.py
from datetime import datetime, timezone

def utc_now() -> datetime:
    """Return a timezone‐aware UTC “now”."""
    return datetime.now(timezone.utc)
