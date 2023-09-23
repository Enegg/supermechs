import typing as t


class ComparisonContext(t.NamedTuple):
    show_damage_average:   bool = False  # calculate average
    show_damage_spread:    bool = False  # calculate damage divergence
    show_damage_potential: bool = False  # damage + energy damage etc, * uses
    show_buff_difference:  bool = False  # whether to display how much has a value changed
    split_damage_values:   bool = False  # whether to split ValueRanges to two entries
