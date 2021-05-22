""" A module for decorators. """

from functools import wraps
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def memoize(is_method: bool = True) -> Callable[[F], F]:
    """Return a decorator that memoizes a function or method."""

    def helper(function: F) -> F:
        @wraps(function)
        def inner(*args: Any, **kwargs: Any) -> Any:
            self = args[0] if is_method else function  # Where to store the cache.
            arguments = args[1:] if is_method else args  # Don't include self in the key.

            if not hasattr(self, "_cache"):
                self._cache = dict()

            try:
                key = (function.__name__, arguments, frozenset(kwargs.items()))
            except TypeError:  # inputs are not hashable.
                return function(*args, **kwargs)

            if key not in self._cache:
                try:
                    self._cache[key] = function(*args, **kwargs)
                except Exception as error:  # pylint: disable=broad-except
                    self._cache[key] = error

            result = self._cache[key]

            if isinstance(result, Exception):
                raise result
            else:
                return result

        return cast(F, inner)

    return helper


def finite(function: F) -> F:
    """A decorator that only allows its method to be called on finitely supported laminations."""

    @wraps(function)
    def inner(*args: Any, **kwargs: Any) -> Any:

        self = args[0]
        if not self.is_finitely_supported():
            raise ValueError(f"{function.__name__} requires the lamination be finitely supported")

        return function(*args, **kwargs)

    return cast(F, inner)
