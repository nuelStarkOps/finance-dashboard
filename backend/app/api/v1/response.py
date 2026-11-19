"""Standard response envelope helper."""

from typing import Any

from pydantic import BaseModel


def ok(data: Any = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the standard success envelope."""
    body: dict[str, Any] = {"success": True}
    if data is not None:
        body["data"] = data
    if meta is not None:
        body["meta"] = meta
    return body


class Message(BaseModel):
    """A simple message payload."""

    message: str
