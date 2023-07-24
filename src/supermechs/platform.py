import typing as t

__all__ = ("json_decoder", "json_encoder", "json_indented_encoder")

JSONDecoder = t.Callable[[str | bytes], t.Any]
JSONEncoder = t.Callable[[t.Any], bytes]

json_decoder: JSONDecoder
json_encoder: JSONEncoder
json_indented_encoder: JSONEncoder

try:
    import orjson  # pyright: ignore[reportMissingImports]

except ImportError:
    import json

    json_decoder = json.loads

    def json_encoder(obj: t.Any, /) -> bytes:
        return json.dumps(obj).encode()

    def json_indented_encoder(obj: t.Any, /) -> bytes:
        return json.dumps(obj, indent=2).encode()

else:
    json_decoder = orjson.loads
    json_encoder = orjson.dumps

    def json_indented_encoder(obj: t.Any, /) -> bytes:
        return orjson.dumps(obj, option=orjson.OPT_INDENT_2)
