""" A module for decorators. """

from functools import wraps
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def finite(function: F) -> F:
    """A decorator that only allows its method to be called on finitely supported laminations."""

    @wraps(function)
    def inner(*args: Any, **kwargs: Any) -> Any:

        self = args[0]
        if not self.is_finitely_supported():
            raise ValueError(f"{function.__name__} requires the lamination be finitely supported")

        return function(*args, **kwargs)

    return cast(F, inner)
