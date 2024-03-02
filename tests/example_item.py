from supermechs.abc.item import ItemID
from supermechs.abc.item_pack import PackKey
from supermechs.enums.item import Element, Type
from supermechs.enums.stats import Stat, Tier
from supermechs.item import ItemData, Tags
from supermechs.stats import TransformStage

from supermechs.ext.deserializers.stat_providers import InterpolatedStats, StaticStats

item = ItemData(
    id=ItemID(187),
    pack_key=PackKey("@Eneg"),
    name="Overcharged Rocket Battery",
    type=Type.SIDE_WEAPON,
    element=Element.EXPLOSIVE,
    tags=Tags(premium=True, require_jump=True),
    start_stage=TransformStage(
        tier=Tier.LEGENDARY,
        stats=InterpolatedStats(
            {
                Stat.weight: 63,
                Stat.explosive_damage: 103,
                Stat.explosive_damage_addon: 181,
                Stat.heat_damage: 56,
                Stat.explosive_resistance_damage: 9,
                Stat.range: 3,
                Stat.range_addon: 6,
                Stat.push: 1,
                Stat.retreat: 1,
                Stat.uses: 3,
                Stat.backfire: 123,
                Stat.heat_generation: 47,
            },
            {
                Stat.explosive_damage: 138,
                Stat.explosive_damage_addon: 243,
                Stat.heat_damage: 75,
            },
            39,
        ),
        level_progression=[],
        next=TransformStage(
            tier=Tier.MYTHICAL,
            stats=InterpolatedStats(
                {
                    Stat.weight: 63,
                    Stat.explosive_damage: 154,
                    Stat.explosive_damage_addon: 276,
                    Stat.heat_damage: 81,
                    Stat.explosive_resistance_damage: 14,
                    Stat.range: 3,
                    Stat.range_addon: 6,
                    Stat.push: 1,
                    Stat.retreat: 1,
                    Stat.uses: 3,
                    Stat.backfire: 180,
                    Stat.heat_generation: 75,
                },
                {
                    Stat.explosive_damage: 202,
                    Stat.explosive_damage_addon: 362,
                    Stat.heat_damage: 106,
                },
                49,
            ),
            level_progression=[],
            next=TransformStage(
                tier=Tier.DIVINE,
                stats=StaticStats(
                    {
                        Stat.weight: 63,
                        Stat.explosive_damage: 213,
                        Stat.explosive_damage_addon: 382,
                        Stat.heat_damage: 112,
                        Stat.explosive_resistance_damage: 14,
                        Stat.range: 3,
                        Stat.range_addon: 6,
                        Stat.push: 1,
                        Stat.retreat: 1,
                        Stat.uses: 3,
                        Stat.backfire: 180,
                        Stat.heat_generation: 75,
                    }
                ),
                level_progression=[],
            ),
        ),
    ),
)
