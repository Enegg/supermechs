from collections import abc

from .exceptions import Catch, DataPath, DataTypeError, DataValueError
from .stats import to_transform_stages
from .typedefs import AnyItemDict
from .utils import assert_keys

from supermechs.abc.item import ItemID
from supermechs.abc.item_pack import PackKey
from supermechs.enums.item import Element, Type
from supermechs.enums.stats import Stat, Tier
from supermechs.item import ItemData, Tags
from supermechs.stats import TransformStage
from supermechs.utils import contains_any_of

_VALID_TAGS: abc.Set[str] = Tags.__annotations__.keys()


def to_tags(
    tags: abc.Iterable[str],
    start_stage: TransformStage,
    *,
    at: DataPath = (),
) -> Tags:
    catch = Catch()
    literal_tags = set[str]()

    for i, tag in enumerate(tags):
        if not isinstance(tag, str):
            catch.add(DataTypeError(type(tag), str, at=(*at, i)))

        elif tag not in _VALID_TAGS:
            msg = f"{tag!r} is not a valid tag"
            catch.add(DataValueError(msg, at=(*at, i)))

        else:
            literal_tags.add(tag)

    catch.checkpoint("Problems while parsing item tags:")

    if "legacy" in literal_tags:
        if start_stage.tier is Tier.MYTHICAL:
            literal_tags.add("premium")

    elif start_stage.tier >= Tier.LEGENDARY:
        literal_tags.add("premium")

    if contains_any_of(start_stage.stats, Stat.advance, Stat.retreat):
        literal_tags.add("require_jump")

    return Tags.from_keywords(literal_tags)


def to_item_data(data: AnyItemDict, pack_key: PackKey, *, at: DataPath = ()) -> ItemData:
    """Construct ItemData from its serialized form.

    Parameters
    ----------
    data: Mapping of serialized data.
    pack_key: The key of a pack this item comes from.
    """
    catch = Catch()
    with catch:
        id, name, type_, element = assert_keys(
            tuple[ItemID, str, Type, Element], data, "id", "name", "type", "element", at=at
        )
    with catch:
        start_stage = to_transform_stages(data, at=at)
        tags = to_tags(data.get("tags", ()), start_stage, at=at)
    catch.checkpoint("Problems while parsing item data:")
    return ItemData(
        id=id,
        pack_key=pack_key,
        name=name,
        type=type_,
        element=element,
        tags=tags,
        start_stage=start_stage,
    )
