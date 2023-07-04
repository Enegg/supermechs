import typing as t

SafeStr = t.NewType("SafeStr", str)
SafeInt = t.NewType("SafeInt", int)


class StringLimits:
    """Namespace for length limits of various kinds of strings."""

    name: t.Final[int] = 32
    description: t.Final[int] = 100


def sanitize_string(
    string: str, /, max_length: int = StringLimits.name, *, strict: bool = False
) -> SafeStr:
    """"""

    if strict:
        if len(string) > max_length:
            raise ValueError("String too long")

        if any(not char.isascii() for char in string):
            raise ValueError("Non-ascii characters found")

    chars = (char if char.isascii() else "_" for char in string)

    return SafeStr("".join(chars)[:max_length])
