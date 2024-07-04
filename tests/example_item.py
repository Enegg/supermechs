from serial.stat_providers import InterpolatedStats, StaticStats

from supermechs.abc.item import ItemID
from supermechs.enums.item import ElementEnum, TagEnum, TypeEnum
from supermechs.enums.stats import StatEnum, TierEnum
from supermechs.item import ItemData
from supermechs.stats import TransformStage

item = ItemData(
    id=ItemID("187@Eneg"),
    name="Overcharged Rocket Battery",
    type=TypeEnum.SIDE_WEAPON,
    element=ElementEnum.EXPLOSIVE,
    tags={TagEnum.premium, TagEnum.require_jump},
    stages=[
        TransformStage(
            tier=TierEnum.LEGENDARY,
            stats=InterpolatedStats(
                {
                    StatEnum.weight: 63,
                    StatEnum.explosive_damage: 103,
                    StatEnum.explosive_damage_addon: 181,
                    StatEnum.heat_damage: 56,
                    StatEnum.explosive_resistance_damage: 9,
                    StatEnum.range: 3,
                    StatEnum.range_addon: 6,
                    StatEnum.push: 1,
                    StatEnum.retreat: 1,
                    StatEnum.uses: 3,
                    StatEnum.backfire: 123,
                    StatEnum.heat_generation: 47,
                },
                {
                    StatEnum.explosive_damage: 138,
                    StatEnum.explosive_damage_addon: 243,
                    StatEnum.heat_damage: 75,
                },
                39,
            ),
            level_progression=[],
        ),
        TransformStage(
            tier=TierEnum.MYTHICAL,
            stats=InterpolatedStats(
                {
                    StatEnum.weight: 63,
                    StatEnum.explosive_damage: 154,
                    StatEnum.explosive_damage_addon: 276,
                    StatEnum.heat_damage: 81,
                    StatEnum.explosive_resistance_damage: 14,
                    StatEnum.range: 3,
                    StatEnum.range_addon: 6,
                    StatEnum.push: 1,
                    StatEnum.retreat: 1,
                    StatEnum.uses: 3,
                    StatEnum.backfire: 180,
                    StatEnum.heat_generation: 75,
                },
                {
                    StatEnum.explosive_damage: 202,
                    StatEnum.explosive_damage_addon: 362,
                    StatEnum.heat_damage: 106,
                },
                49,
            ),
            level_progression=[],
        ),
        TransformStage(
            tier=TierEnum.DIVINE,
            stats=StaticStats(
                {
                    StatEnum.weight: 63,
                    StatEnum.explosive_damage: 213,
                    StatEnum.explosive_damage_addon: 382,
                    StatEnum.heat_damage: 112,
                    StatEnum.explosive_resistance_damage: 14,
                    StatEnum.range: 3,
                    StatEnum.range_addon: 6,
                    StatEnum.push: 1,
                    StatEnum.retreat: 1,
                    StatEnum.uses: 3,
                    StatEnum.backfire: 180,
                    StatEnum.heat_generation: 75,
                }
            ),
            level_progression=[],
        ),
    ],
)
