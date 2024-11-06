from collections import Counter
from itertools import chain
from typing import Protocol

from supermechs.abc import ItemElement, Mech

__all__ = ("dominant_element",)


class HasElement(Protocol):
    @property
    def element(self) -> ItemElement: ...


def dominant_element(mech: Mech[HasElement], /, threshold: int = 2) -> ItemElement | None:
    """Guesses the mech type by equipped items.

    threshold: The difference in item count required for either of the two most common elements\
     to be considered over the other.
    """
    items = (mech.torso, mech.legs, mech.hook, mech.drone)
    items = chain(items, mech.side_weapons(), mech.top_weapons())

    elements = Counter(item.element for item in items if item is not None).most_common(2)

    if len(elements) == 0:
        return None

    if len(elements) > 1:  # noqa: SIM102
        if elements[0][1] - elements[1][1] < threshold:
            return None

    return elements[0][0]
