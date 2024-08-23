import re
from collections import abc
from typing import Any, Protocol, TypeAlias

__all__ = ("dumps", "loads", "set_codecs")

Loads: TypeAlias = abc.Callable[[str | bytes], Any]


class Dumps(Protocol):
    def __call__(self, obj: object, /, *, indent: bool = False) -> bytes: ...


loads: Loads
dumps: Dumps


def set_codecs(encoder: Dumps, decoder: Loads) -> None:
    """Override dumps/loads used by plugins."""
    global dumps, loads
    dumps, loads = encoder, decoder


_INDENTED_ARRAY = re.compile(rb",\n\s+(\d+)")


def _dedent_arrays(data: bytes, /) -> bytes:
    return _INDENTED_ARRAY.sub(lambda match: b", " + match[1], data)


try:
    import orjson

except ImportError:
    import json

    def _json_dumps(obj: object, /, *, indent: bool = False) -> bytes:
        if not indent:
            return json.dumps(obj).encode()

        data = json.dumps(obj, indent=2).encode()
        return _dedent_arrays(data)

    set_codecs(_json_dumps, json.loads)

else:

    def _orjson_dumps(obj: object, /, *, indent: bool = False) -> bytes:
        if not indent:
            return orjson.dumps(obj)

        data = orjson.dumps(obj, option=orjson.OPT_INDENT_2)
        return _dedent_arrays(data)

    set_codecs(_orjson_dumps, orjson.loads)
