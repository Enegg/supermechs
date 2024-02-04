from supermechs.api import ItemPack, Mech, PackData
from supermechs.rendering import get_mech_graphics
from supermechs.typeshed import PackKey

mech = Mech(name="Test build")
pack = ItemPack(data=PackData(PackKey("@Default")), items={}, sprites={})

graphics = get_mech_graphics(mech, pack.get_sprite)
