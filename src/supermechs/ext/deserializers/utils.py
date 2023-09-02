import typing as t
import typing_extensions as tex

from supermechs.typeshed import T


def js_format(string: str, /, **kwargs: t.Any) -> str:
    """Format a JavaScript style string using given keys and values."""
    # XXX: this will do as many passes as there are kwargs, maybe concatenate the pattern?
    import re

    for key, value in kwargs.items():
        string = re.sub(rf"%{re.escape(key)}%", str(value), string)

    return string


class NanMeta(type):
    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, t.Any]) -> tex.Self:
        def func(self: T, __value: int) -> T:
            return self

        for dunder in ("add", "sub", "mul", "truediv", "floordiv", "mod", "pow"):
            namespace[f"__{dunder}__"] = func
            namespace[f"__r{dunder}__"] = func

        return super().__new__(cls, name, bases, namespace)


class Nan(int, metaclass=NanMeta):
    def __str__(self) -> str:
        return "?"

    def __repr__(self) -> str:
        return "NaN"

    def __format__(self, _: str, /) -> str:
        return "?"

    def __eq__(self, _: t.Any) -> bool:
        return False

    def __lt__(self, _: t.Any) -> bool:
        return False

    def __round__(self, ndigits: int = 0, /) -> tex.Self:
        # round() on float("nan") raises ValueError and probably has a good reason to do so,
        # but for my purposes it is essential round() returns this object too
        return self


NaN: t.Final = Nan()
