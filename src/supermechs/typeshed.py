import typing as t
import typing_extensions as tex

T = tex.TypeVar("T", infer_variance=True)
T2 = tex.TypeVar("T2", infer_variance=True)
KT = tex.TypeVar("KT", bound=t.Hashable, infer_variance=True)
"""Key-type of a mapping."""
VT = tex.TypeVar("VT", infer_variance=True)
"""Value-type of a mapping."""
P = t.ParamSpec("P")

twotuple: t.TypeAlias = tuple[T, T]
"""Tuple of two elements of same type."""
XOrTupleXY: t.TypeAlias = T | tuple[T, T2]
"""Type or tuple of two types."""
Factory: t.TypeAlias = t.Callable[[], T]
"""0-argument callable returning an object of given type."""
LiteralURL: t.TypeAlias = str
"""String representing a URL."""

Name: t.TypeAlias = str
"""String representing item name."""
ID: t.TypeAlias = int
"""Positive integer representing an item's ID."""
