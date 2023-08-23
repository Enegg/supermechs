import sys
import typing as t

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

    def indented_json_encoder(obj: t.Any, /) -> bytes:
        return orjson.dumps(obj, option=orjson.OPT_INDENT_2)


toml_encoder: EncoderType
toml_decoder: DecoderType

if sys.version_info >= (3, 11):
    import tomlib

else:
    import rtoml

    def toml_decoder(s: str | bytes, /) -> t.Any:
        return rtoml.loads(s.decode() if isinstance(s, bytes) else s)

    def toml_encoder(o: t.Any, /) -> bytes:
        return rtoml.dumps(o).encode()
