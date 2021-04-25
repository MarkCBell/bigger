""" Utilities used in building example surfaces. """

from itertools import count as naturals
from math import inf
from typing import Any, Callable, Iterable, Optional, Tuple
import re


def integers(minimum: Optional[int] = None, maximum: Optional[int] = None) -> Iterable[int]:
    """ Return an iterable that yields all of the integers. """

    return (x for n in naturals() for x in (n, ~n) if (minimum is None or minimum <= x) and (maximum is None or x <= maximum))


def extract_curve_and_test(curve_names: str, name: str) -> Tuple[str, Callable[[Any], bool]]:
    """ Return a curve and a test to apply for which of it's components to twist. """

    twist_match = re.match(r"(?P<curve>[%s])_(?P<n>-?\d+)$" % (curve_names), name)
    twist_index_match = re.match(r"(?P<curve>[%s])\[ *(?P<n>-?\d+) *\]$" % (curve_names), name)
    twist_slice_match = re.match(r"(?P<curve>[%s])(\[ *(?P<start>-?\d*) *: *(?P<stop>-?\d*) *(: *(?P<step>-?\d*) *)?\])?$" % (curve_names), name)
    twist_expr_match = re.match(r"(?P<curve>[%s])\{(?P<expr>.*)\}$" % (curve_names), name)

    if twist_match is not None:
        parameters = twist_match.groupdict()
        curve = parameters["curve"]
        n = int(parameters["n"])
        test = lambda edge: edge == n
    elif twist_index_match is not None:
        parameters = twist_index_match.groupdict()
        curve = parameters["curve"]
        n = int(parameters["n"])
        test = lambda edge: edge == n
    elif twist_slice_match is not None:
        parameters = twist_slice_match.groupdict()
        curve = parameters["curve"]
        start = int(parameters["start"]) if parameters["start"] else -inf
        stop = int(parameters["stop"]) if parameters["stop"] else inf
        step = int(parameters["step"]) if parameters["step"] else 1
        test = lambda edge: start <= edge < stop and (edge % step == (0 if start == -inf else start % step))
    elif twist_expr_match is not None:
        parameters = twist_expr_match.groupdict()
        curve = parameters["curve"]
        test = lambda n: eval(parameters["expr"], {"n": n, **globals()})  # pylint: disable=eval-used
    else:
        raise ValueError("Unknown mapping class {}".format(name))

    return curve, test
