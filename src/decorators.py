"""Shared decorators for automation components."""

from functools import wraps
from collections.abc import Callable
from typing import Any


def requires_driver(function: Callable[..., Any]) -> Callable[..., Any]:
    """Require an initialized WebDriver before entering an automation method."""

    @wraps(function)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not getattr(self, "driver", None):
            raise RuntimeError("WebDriver is not initialized.")
        return function(self, *args, **kwargs)

    return wrapper
