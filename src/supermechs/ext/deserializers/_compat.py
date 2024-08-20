# pyright: reportImportCycles=false
import sys
import typing

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup

if typing.TYPE_CHECKING:
    from .exceptions import DataErrorType

DataErrorGroup: typing.Final[type[ExceptionGroup["DataErrorType"]]] = ExceptionGroup
"""\
When capturing `ExceptionGroup`s into a variable:
>>> try:
...    ...
... except ExceptionGroup as exc:
...    ...

The type of `exc` will be reported as `ExceptionGroup[Unknown]`, as it is generic.
This causes (false positive) errors down the line. Meanwhile, parametrized generic exceptions
cannot be used in the `except` statement (they result in a `TypeError`).

This leads to a problem of always having to specify the type of `exc` beforehand
as `exc: ExceptionGroup[...]`, which is inconvenient.

This typealias is introduced as an alternative solution - it is a bare `ExceptionGroup` at runtime,
but the type checker sees it as parametrized.

Because of how on per module basis pyright gives precedence to the assigned type
rather than the variable annotation, this typealias is placed in a separate module.
"""
