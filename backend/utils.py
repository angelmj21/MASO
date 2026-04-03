from datetime import datetime, timezone


def ts() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(category: str, message: str) -> str:
    """Format a timestamped log entry: [timestamp] [Category] message"""
    return f"[{ts()}] [{category}] {message}"


def syslog(message: str) -> str:
    return log("System", message)


def seclog(message: str) -> str:
    return log("Security", message)
