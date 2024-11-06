from collections import abc
from typing import Final

import attrs

from supermechs.enums import StatName
from supermechs.utils import default

__all__ = ("BuildRules",)


@attrs.frozen
class BuildRules:
    @default
    @staticmethod
    def default() -> "BuildRules":
        return BuildRules()

    safe_weight: Final[int] = 1000
    """The maximum weight of a mech before overload."""
    overload: Final[int] = 10
    """The maximum extra weight allowed over the max weight."""
    hp_overload_penalty: Final[int] = 15
    """The ratio at which hit points are reduced for each kg of overload."""
    exclusive_stats: Final[abc.Set[str]] = {
        StatName.physical_resistance,
        StatName.explosive_resistance,
        StatName.electric_resistance,
    }
    """A set of stats which can occur at most once among all modules of a mech."""

    @property
    def max_weight(self) -> int:
        """The absolute maximum weight of a mech before it is overweight."""
        return self.safe_weight + self.overload
