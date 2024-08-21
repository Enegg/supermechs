import sys
from collections import abc
from pathlib import Path

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup

import fileformats
from serial import to_item_data

from .example_item import item

from supermechs.abc.item_pack import PackKey

path = Path() / "tests" / "data" / "item_v3.json"
path2 = Path() / "tests" / "data" / "invalid_item_v3.json"
data = fileformats.json_decoder(path2.read_bytes())


def _unwrap(
    exc: Exception | ExceptionGroup[Exception], add: abc.Callable[[Exception], None]
) -> None:
    if isinstance(exc, ExceptionGroup):
        for exc2 in exc.exceptions: # type: ignore
            _unwrap(exc2, add) # type: ignore

    else:
        add(exc)


def unwrap(exc: Exception) -> None:
    issues: list[Exception] = []
    _unwrap(exc, issues.append)
    print("\n".join(map(str, issues)))


try:
    item_data = to_item_data(data, PackKey("@Eneg"), at=["items", item.id])

except Exception as exc:
    unwrap(exc)

else:
    print(item_data == item)
