import re
import typing as t

import rtoml

__all__ = (
    "json_decoder",
    "compact_json_encoder",
    "indented_json_encoder",
    "toml_decoder",
    "toml_encoder",
)

DecoderType = t.Callable[[str | bytes], t.Any]
EncoderType = t.Callable[[t.Any], bytes]

json_decoder: DecoderType
compact_json_encoder: EncoderType
indented_json_encoder: EncoderType

try:
    import orjson  # pyright: ignore[reportMissingImports]

except ImportError:
    import json

    json_decoder = json.loads

    def compact_json_encoder(obj: t.Any, /) -> bytes:
        return json.dumps(obj).encode()

    def indented_json_encoder(obj: t.Any, /) -> bytes:
        return json.dumps(obj, indent=2).encode()

else:
    json_decoder = orjson.loads
    compact_json_encoder = orjson.dumps

    _indented_array = re.compile(rb",\n\s+(\d+)")


    def indented_json_encoder(obj: t.Any, /) -> bytes:
        data = orjson.dumps(obj, option=orjson.OPT_INDENT_2)
        data = _indented_array.sub(lambda match: b", " + match[1], data)
        return data


toml_encoder: EncoderType
toml_decoder: DecoderType


def toml_decoder(s: str | bytes, /) -> t.Any:
    return rtoml.loads(s.decode() if isinstance(s, bytes) else s)

def toml_encoder(o: t.Any, /) -> bytes:
    return rtoml.dumps(o).encode()
