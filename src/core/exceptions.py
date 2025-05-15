class DuplicateRecordError(Exception):
    """Raised when an ingest tries to insert a record that already exists."""


class AdapterError(Exception):
    """Generic adapter failure (e.g. HTTP error, parse error)."""
