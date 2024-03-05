from collections import abc

import pytest

from supermechs.abc.item_pack import PackKey
from supermechs.enums.item import Element, Type

from supermechs.ext.deserializers import to_item_data
from supermechs.ext.deserializers.exceptions import (
    DataError,
    DataErrorGroup,
    DataErrorType,
    DataKeyError,
    DataTypeError,
    DataValueError,
)
from supermechs.ext.deserializers.typedefs import AnyItemDict


def test_item_dict_parsing(item_dict: tuple[AnyItemDict, PackKey]):
    to_item_data(item_dict[0], item_dict[1])


def flatten_exc_group(exceptions: abc.Iterable[DataErrorType], /) -> abc.Iterator[DataError]:
    for exc in exceptions:
        if isinstance(exc, DataError):
            yield exc

        else:
            yield from flatten_exc_group(exc.exceptions)


class TestInvalidItem:
    @pytest.fixture(scope="class")
    def errors(self, invalid_item: AnyItemDict):
        with pytest.raises(DataErrorGroup) as exc_info:
            to_item_data(invalid_item, PackKey("@Eneg"))

        assert exc_info.type is DataErrorGroup
        errors = list(flatten_exc_group(exc_info.value.exceptions))
        assert len(errors) == 8
        return errors

    def test_item_type(self, errors: list[DataError]):
        assert isinstance(errors[0], DataTypeError)
        assert errors[0].received == "SIDE_WEAP"
        assert errors[0].expected == Type
        assert errors[0].at == ("type",)
        # assert errors[0] == DataTypeError("SIDE_WEAP", Type, at=("type",))

    def test_element(self, errors: list[DataError]):
        assert errors[1] == DataTypeError("EXPLOSIV", Element, at=("element",))

    def test_expDmg(self, errors: list[DataError]):
        assert errors[2] == DataTypeError(list, list, at=("legendary", "expDmg"))

    def test_range(self, errors: list[DataError]):
        assert errors[3] == DataTypeError(list, list, at=("legendary", "range"))

    def test_heaCost(self, errors: list[DataError]):
        assert errors[4] == DataTypeError(str, int, at=("legendary", "heaCost"))