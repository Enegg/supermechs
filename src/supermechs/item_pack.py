from __future__ import annotations

import logging
import typing as t

from attrs import define, field
from attrs.validators import max_len
from typing_extensions import Self

from .core import abbreviate_names
from .models.item_base import ItemBase
from .typedefs import ID, AnyItemDict, AnyItemPack, Name
from .user_input import StringLimits, sanitize_string

__all__ = ("ItemPack", "extract_info", "extract_key")

LOGGER = logging.getLogger(__name__)


class PackConfig(t.NamedTuple):
    version: str
    key: str
    name: str
    description: str


# TODO: use match case and/or custom exception for input validation
def extract_key(pack: AnyItemPack, /) -> str:
    """Extract the key of an item pack.

    Raises
    ------
    TypeError on unknown version.
    """
    if "version" not in pack or pack["version"] == "1":
        key = pack["config"]["key"]

    elif pack["version"] in ("2", "3"):
        key = pack["key"]

    else:
        raise TypeError(f"Unknown pack version: {pack['version']!r:.20}")

    if not isinstance(key, str):
        raise TypeError(f"{key!r} is not a string")

    return key


def extract_info(pack: AnyItemPack, /) -> PackConfig:
    """Extract version, key, name and description of the pack.

    Raises
    ------
    TypeError on unknown version.
    """
    if "version" not in pack or pack["version"] == "1":
        metadata = pack["config"]
        version = "1"

    elif pack["version"] in ("2", "3"):
        metadata = pack
        version = pack["version"]

    else:
        raise TypeError(f"Unknown pack version: {pack['version']!r:.20}")

    try:
        name = sanitize_string(metadata["name"])

    except KeyError:
        name = "<no name>"

    try:
        description = sanitize_string(metadata["description"], StringLimits.description)

    except KeyError:
        description = "<no description>"

    return PackConfig(version, metadata["key"], name, description)


@define
class ItemPack:
    """Object representing an item pack."""

    key: str = field(validator=max_len(StringLimits.name))
    name: str = field(default="<no name>", validator=max_len(StringLimits.name))
    description: str = field(
        default="<no description>", validator=max_len(StringLimits.description)
    )
    # personal packs
    extends: str | None = field(default=None)
    custom: bool = False

    # Item ID to Item
    items: dict[ID, ItemBase] = field(
        factory=dict, init=False, repr=lambda items: f"{{<{len(items)} items>}}"
    )
    # Item name to item ID
    names_to_ids: dict[Name, ID] = field(factory=dict, init=False, repr=False)
    # Abbrev to a set of names the abbrev matches
    name_abbrevs: dict[str, set[Name]] = field(factory=dict, init=False, repr=False)

    def __contains__(self, value: Name | ID | ItemBase) -> bool:
        if isinstance(value, Name):
            return value in self.names_to_ids

        if isinstance(value, ID):
            return value in self.items

        if isinstance(value, ItemBase):
            return value.pack_key == self.key and value.id in self.items

        return NotImplemented

    def load(self, items: t.Iterable[AnyItemDict], /) -> None:
        """Load pack items from data."""

        for item_dict in items:
            item = ItemBase.from_json(item_dict, self.key, self.custom)
            self.items[item.id] = item
            self.names_to_ids[item.name] = item.id

        self.name_abbrevs |= abbreviate_names(self.names_to_ids)

    def get_item_by_name(self, name: Name) -> ItemBase:
        try:
            id = self.names_to_ids[name]
            return self.items[id]

        except KeyError as err:
            err.args = (f"No item named {name!r} in the pack",)
            raise

    def get_item_by_id(self, item_id: ID) -> ItemBase:
        try:
            return self.items[item_id]

        except KeyError as err:
            err.args = (f"No item with id {item_id} in the pack",)
            raise

    def iter_item_names(self) -> t.Iterator[Name]:
        return iter(self.names_to_ids)

    @classmethod
    def from_json(cls, data: AnyItemPack, /, custom: bool = False) -> Self:
        pack_info = extract_info(data)
        self = cls(
            key=pack_info.key,
            name=pack_info.name,
            description=pack_info.description,
            custom=custom,
        )
        self.load(data["items"])
        return self
