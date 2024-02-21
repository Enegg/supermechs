from supermechs.abc.item_pack import PackKey
from supermechs.api import ItemPack, Mech, PackData
from supermechs.graphics.api import get_mech_gfx

mech = Mech(name="Test build")
pack = ItemPack(data=PackData(PackKey("@Default")), items={}, sprites={})

graphics = get_mech_gfx(mech, pack.get_sprite)
