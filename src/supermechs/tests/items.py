from supermechs.ext.deserializers.models import to_item_data
from supermechs.ext.deserializers.typedefs.packs import ItemDictVer3
from supermechs.platform import json_decoder

with open("data/example_item_v2.json") as file:
    data: ItemDictVer3 = json_decoder(file.read())

item = to_item_data(data, "@darkstare", False)
