from collections import abc
from typing import TypeAlias
from typing_extensions import ParamSpec, TypeVar

T = TypeVar("T", infer_variance=True)
T2 = TypeVar("T2", infer_variance=True)
KT = TypeVar("KT", bound=abc.Hashable, infer_variance=True)
"""Key-type of a mapping."""
VT = TypeVar("VT", infer_variance=True)
"""Value-type of a mapping."""
P = ParamSpec("P")

twotuple: TypeAlias = tuple[T, T]
"""Tuple of two elements of same type."""
XOrTupleXY: TypeAlias = T | tuple[T, T2]
"""Type or tuple of two types."""
Factory: TypeAlias = abc.Callable[[], T]
"""0-argument callable returning an object of given type."""
LiteralURL: TypeAlias = str
"""String representing a URL."""

Name: TypeAlias = str
"""String representing item name."""
ID: TypeAlias = int
"""Positive integer representing an item's ID."""
