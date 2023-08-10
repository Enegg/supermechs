import typing as t

__all__ = ("json_decoder", "compact_json_encoder", "indented_json_encoder")

JSONDecoder = t.Callable[[str | bytes], t.Any]
JSONEncoder = t.Callable[[t.Any], bytes]

json_decoder: JSONDecoder
compact_json_encoder: JSONEncoder
indented_json_encoder: JSONEncoder

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
