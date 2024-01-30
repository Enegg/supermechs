class SMException(Exception):
    """Base class for library exceptions."""


class OutOfRangeError(SMException):
    """Value X = {number} out of range {min} <= X <= {max}"""

    def __init__(self, number: float, lower: float, upper: float, /) -> None:
        assert self.__doc__ is not None
        super().__init__(self.__doc__.format(number=number, min=lower, max=upper))


class NegativeValueError(OutOfRangeError):
    """Value cannot be negative, got {number}"""

    def __init__(self, number: float, /) -> None:
        super().__init__(number, 0, 0)


class IDLookupError(SMException):
    """Unknown item ID: {ID}"""

    def __init__(self, id: int, /) -> None:
        assert self.__doc__ is not None
        super().__init__(self.__doc__.format(id=id))


class PackKeyError(SMException):
    """Unknown pack key: {key}"""

    def __init__(self, key: str, /) -> None:
        assert self.__doc__ is not None
        super().__init__(self.__doc__.format(key=key))


class MaxPowerError(SMException):
    """Item at maximum power"""

    def __init__(self, arg: object = __doc__, *args: object) -> None:
        super().__init__(arg, *args)


class MaxTierError(SMException):
    """Attempted to transform an item at its maximum tier."""

    def __init__(self, /) -> None:
        super().__init__("Maximum item tier already reached")
