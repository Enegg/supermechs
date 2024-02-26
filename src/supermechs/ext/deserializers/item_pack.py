from collections import abc
from typing import TYPE_CHECKING, Any

from .errors import Catch, DataVersionError
from .items import to_item_data
from .typedefs import AnyItemPack
from .utils import assert_key, assert_type

from supermechs.abc.item_pack import PackKey
from supermechs.item_pack import ItemPack, PackData

if TYPE_CHECKING:
    from supermechs.abc.item import ItemID
    from supermechs.item import ItemData


def to_item_pack(data: AnyItemPack, /) -> ItemPack:
    metadata = extract_metadata(data)
    catch = Catch()
    items: dict[ItemID, ItemData] = {}
    key = "items"

    for i, item_data in enumerate(assert_key(abc.Sequence[Any], data, key)):
        with catch:
            item = to_item_data(item_data, metadata.key, at=(key, i))
            items[item.id] = item

    catch.checkpoint("Problems while creating item pack:")
    return ItemPack(data=metadata, items=items, sprites={})


def extract_metadata(pack: AnyItemPack, /) -> PackData:
    """Extracts key, name and description from item pack data."""
    key = "version"
    version = assert_type(str, pack.get(key, "1"), at=(key,))

    if version == "1":
        at = ("config",)
        cfg = assert_key(dict[str, Any], pack, at[0])

    elif version not in ("2", "3"):
        raise DataVersionError(version, "3", at=(key,))

    else:
        at = ()
        cfg = pack

    catch = Catch()
    params: dict[str, str] = {}
    with catch:
        pack_key = PackKey(assert_key(str, cfg, "key", at=at))

    for extra in ("name", "description"):
        if extra in cfg:
            with catch:
                params[extra] = assert_key(str, cfg, extra, at=at)

    catch.checkpoint()
    return PackData(key=pack_key, **params)


def extract_key(pack: AnyItemPack, /) -> PackKey:
    """Extract the key of an item pack."""
    return extract_metadata(pack).key
