import re
from collections import abc
from typing import Any, Protocol, TypeAlias

__all__ = ("json_decoder", "json_encoder", "set_json_codecs")

DecoderType: TypeAlias = abc.Callable[[str | bytes], Any]


class EncoderType(Protocol):
    def __call__(self, obj: object, /, *, indent: bool = False) -> bytes:
        ...


json_decoder: DecoderType
json_encoder: EncoderType


def set_json_codecs(encoder: EncoderType, decoder: DecoderType) -> None:
    """Override the json (de)coder used by plugins."""
    global json_encoder, json_decoder
    json_encoder, json_decoder = encoder, decoder


_INDENTED_ARRAY = re.compile(rb",\n\s+(\d+)")


def _dedent_arrays(data: bytes, /) -> bytes:
    return _INDENTED_ARRAY.sub(lambda match: b", " + match[1], data)


try:
    import orjson  # pyright: ignore[reportMissingImports]

except ImportError:
    import json

    def _json_dumps(obj: object, /, *, indent: bool = False) -> bytes:
        if not indent:
            return json.dumps(obj).encode()

        data = json.dumps(obj, indent=2).encode()
        return _dedent_arrays(data)

    set_json_codecs(_json_dumps, json.loads)

else:

    def _orjson_dumps(obj: object, /, *, indent: bool = False) -> bytes:
        if not indent:
            return orjson.dumps(obj)

        data = orjson.dumps(obj, option=orjson.OPT_INDENT_2)
        return _dedent_arrays(data)

    set_json_codecs(_orjson_dumps, orjson.loads)
