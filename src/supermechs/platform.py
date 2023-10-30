import re
import typing as t

__all__ = ("json_decoder", "json_encoder", "set_json_encoder", "set_json_decoder")

DecoderType = t.Callable[[str | bytes], t.Any]


class EncoderType(t.Protocol):
    def __call__(self, obj: t.Any, /, indent: bool = False) -> bytes:
        ...


json_decoder: DecoderType
json_encoder: EncoderType

_in_use: None | str = None


def set_json_encoder(func: EncoderType, /) -> None:
    """Override the json encoder the plugin will use.

    Notice
    ------
    This has to be called prior to any imports from the plugin depending on the encoder.
    """
    if _in_use is not None:
        msg = f"Encoder in use by {_in_use}"
        raise RuntimeWarning(msg)

    global json_encoder  # noqa: PLW0603
    json_encoder = func


def set_json_decoder(func: DecoderType, /) -> None:
    """Override the json decoder the plugin will use.

    Notice
    ------
    This has to be called prior to any imports from the plugin depending on the decoder.
    """
    if _in_use is not None:
        msg = f"Decoder in use by {_in_use}"
        raise RuntimeWarning(msg)

    global json_decoder  # noqa: PLW0603
    json_decoder = func


def _set_in_use(module: str, /) -> None:  # pyright: ignore[reportUnusedFunction]
    global _in_use  # noqa: PLW0603

    if _in_use is None:
        _in_use = module


try:
    import orjson  # pyright: ignore[reportMissingImports]

except ImportError:
    import json

    def _json_dumps(obj: t.Any, /, indent: bool = False) -> bytes:
        return json.dumps(obj, indent=2 if indent else None).encode()

    set_json_decoder(json.loads)
    set_json_encoder(_json_dumps)

else:
    _indented_array = re.compile(rb",\n\s+(\d+)")

    def _json_dumps(obj: t.Any, /, indent: bool = False) -> bytes:
        if not indent:
            return orjson.dumps(obj)

        data = orjson.dumps(obj, option=orjson.OPT_INDENT_2)
        data = _indented_array.sub(lambda match: b", " + match[1], data)
        return data

    set_json_decoder(orjson.loads)
    set_json_encoder(_json_dumps)
