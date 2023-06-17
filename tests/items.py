import orjson

from supermechs.api import InvItem, Item
from supermechs.typedefs import ItemDictVer3

with open("tests/example_item_v2.json") as file:
    data: ItemDictVer3 = orjson.loads(file.read())

item = Item.from_json(data, "@darkstare", False)
inv_item = InvItem.from_item(item, maxed=True)
