""" A module for decorators. """

import inspect
from typing import Callable, TypeVar, Any

from decorator import decorator

RT = TypeVar("RT")  # return type


@decorator
def memoize(function: Callable[..., RT], *args: Any, **kwargs: Any) -> Callable[..., RT]:
    """ A decorator that memoizes a function. """

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
