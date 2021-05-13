""" A module for decorators. """

from functools import wraps
import inspect
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def memoize(function: F) -> F:
    """A decorator that memoizes a function."""

    @wraps(function)
    def inner(*args: Any, **kwargs: Any) -> Any:
        sig = inspect.signature(function)

        inputs = sig.bind(*args, **kwargs)
        inputs.apply_defaults()

        self = inputs.arguments.pop("self", function)  # We test whether function is a method by looking for a `self` argument. If not we store the cache in the function itself.
        kwd_key = next((name for name, parameter in sig.parameters.items() if parameter.kind == inspect.Parameter.VAR_KEYWORD), "")
        kwds = inputs.arguments.pop(kwd_key, dict())  # We grab any **kwargs parameter in the function.

        if not hasattr(self, "_cache"):
            self._cache = dict()

        try:
            key = (function.__name__, frozenset(inputs.arguments.items()), frozenset(kwds.items()))
        except TypeError:  # inputs are not hashable.
            return function(*args, **kwargs)

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


def finite(function: F) -> F:
    """A decorator that only allows its method to be called on finitely supported laminations."""

    @wraps(function)
    def inner(*args: Any, **kwargs: Any) -> Any:

        inputs = inspect.getcallargs(function, *args, **kwargs)  # pylint: disable=deprecated-method
        self = inputs.pop("self", function)

        if not self.is_finitely_supported():
            raise ValueError(f"{function.__name__} requires the lamination be finitely supported")

        return function(*args, **kwargs)

    return cast(F, inner)
