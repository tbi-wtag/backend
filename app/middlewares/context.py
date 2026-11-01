import contextvars
from typing import Any, Dict

request_context: contextvars.ContextVar[Dict[str, Any] | None] = contextvars.ContextVar(
    "request_context", default=None
)

current_user_context: contextvars.ContextVar[Dict[str, Any] | None] = (
    contextvars.ContextVar("current_user_context", default=None)
)
