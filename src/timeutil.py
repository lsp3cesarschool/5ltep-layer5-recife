"""ISO 8601 helpers: every instant is compared in UTC; a naive timestamp is taken as UTC."""

from datetime import datetime, timezone


def parse(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds") if dt else None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def latest(*values: str | None) -> str | None:
    found = [parse(v) for v in values if v]
    return iso(max(found)) if found else None


def earliest(*values: str | None) -> str | None:
    found = [parse(v) for v in values if v]
    return iso(min(found)) if found else None
