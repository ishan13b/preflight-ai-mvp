"""Helpers shared across architecture reviewers."""


def is_none_value(value: str) -> bool:
    """Return True when a field represents an unset / missing capability."""
    normalized = value.strip().lower()
    return normalized in {"none", "null", "n/a", "na", "-"}
