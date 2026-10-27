import contextvars
from typing import Any, Dict

request_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "request_context", default = {}
)

current_user_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "current_user_context", default = {}
)

