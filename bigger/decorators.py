""" A module for decorators. """

from functools import wraps
import inspect
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def memoize(function: F) -> F:
    """A decorator that memoizes a function."""

    @wraps(function)
    def inner(*args: Any, **kwargs: Any) -> Any:

        inputs = inspect.getcallargs(function, *args, **kwargs)  # pylint: disable=deprecated-method
        # We test whether function is a method by looking for a `self` argument. If not we store the cache in the function itself.
        self = inputs.pop("self", function)

        if not hasattr(self, "_cache"):
            self._cache = dict()
        key = (function.__name__, frozenset(inputs.items()))
        if key not in self._cache:
            try:
                self._cache[key] = function(*args, **kwargs)
            except Exception as error:  # pylint: disable=broad-except
                if isinstance(error, KeyboardInterrupt):
                    raise
                self._cache[key] = error

        result = self._cache[key]
        if isinstance(result, Exception):
            raise result
        else:
            return result

    return cast(F, inner)
