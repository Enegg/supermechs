from collections import abc
from typing import Any, Protocol, TypeAlias

__all__ = ("json_decoder", "json_encoder", "set_json_encoder", "set_json_decoder")

DecoderType: TypeAlias = abc.Callable[[str | bytes], Any]


class EncoderType(Protocol):
    def __call__(self, obj: Any, /, indent: bool = False) -> bytes:
        ...


json_decoder: DecoderType
json_encoder: EncoderType


def set_json_encoder(func: EncoderType, /) -> None:
    """Override the json encoder used by plugins."""

    global json_encoder  # noqa: PLW0603
    json_encoder = func


def set_json_decoder(func: DecoderType, /) -> None:
    """Override the json decoder used by plugins."""

    global json_decoder  # noqa: PLW0603
    json_decoder = func


try:
    import orjson  # pyright: ignore[reportMissingImports]

except ImportError:
    import json

    def _json_dumps(obj: Any, /, indent: bool = False) -> bytes:
        return json.dumps(obj, indent=2 if indent else None).encode()

    set_json_decoder(json.loads)
    set_json_encoder(_json_dumps)

else:
    import re

    _indented_array = re.compile(rb",\n\s+(\d+)")

    def _json_dumps(obj: Any, /, indent: bool = False) -> bytes:
        if not indent:
            return orjson.dumps(obj)

        data = orjson.dumps(obj, option=orjson.OPT_INDENT_2)
        data = _indented_array.sub(lambda match: b", " + match[1], data)
        return data

    set_json_decoder(orjson.loads)
    set_json_encoder(_json_dumps)
