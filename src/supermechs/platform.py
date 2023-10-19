import re
import typing as t

import rtoml

__all__ = ("json_decoder", "json_encoder", "toml_decoder", "toml_encoder")

DecoderType = t.Callable[[str | bytes], t.Any]
EncoderType = t.Callable[[t.Any], bytes]

json_decoder: DecoderType

try:
    import orjson  # pyright: ignore[reportMissingImports]

except ImportError:
    import json

    json_decoder = json.loads

    def json_encoder(obj: t.Any, /, indent: bool = False) -> bytes:
        return json.dumps(obj, indent=2 if indent else None).encode()

else:
    json_decoder = orjson.loads

    _indented_array = re.compile(rb",\n\s+(\d+)")

    def json_encoder(obj: t.Any, /, indent: bool = False) -> bytes:
        if not indent:
            return orjson.dumps(obj)

        data = orjson.dumps(obj, option=orjson.OPT_INDENT_2)
        data = _indented_array.sub(lambda match: b", " + match[1], data)
        return data


toml_encoder: EncoderType
toml_decoder: DecoderType


def toml_decoder(s: str | bytes, /) -> t.Any:
    return rtoml.loads(s.decode() if isinstance(s, bytes) else s)


def toml_encoder(o: t.Any, /) -> bytes:
    return rtoml.dumps(o).encode()
