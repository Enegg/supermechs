from collections.abc import Callable
from pathlib import Path

from exceptiongroup import ExceptionGroup

from .example_item import item

from supermechs.abc.item_pack import PackKey

from supermechs.ext.deserializers import to_item_data
from supermechs.ext.platform import json_decoder

path = Path() / "tests" / "data" / "item_v3.json"
path2 = Path() / "tests" / "data" / "invalid_item_v3.json"
data = json_decoder(path2.read_bytes())


def _unwrap(exc: Exception | ExceptionGroup[Exception], add: Callable[[Exception], None]):
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
