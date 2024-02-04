from supermechs.typeshed import PackKey

from supermechs.ext.deserializers import to_item_data
from supermechs.ext.deserializers.typedefs.packs import ItemDictVer3
from supermechs.ext.platform import json_decoder

with open("data/example_item_v2.json") as file:  # noqa: PTH123
    data: ItemDictVer3 = json_decoder(file.read())

item = to_item_data(data, PackKey("@darkstare"))
