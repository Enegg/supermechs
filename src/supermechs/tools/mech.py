from supermechs.enums.item import Element, Type
from supermechs.mech import Mech

__all__ = ("dominant_element",)


def dominant_element(mech: Mech, /, threshold: int = 2) -> Element | None:
    """Guesses the mech type by equipped items.

    threshold: the difference in item count required for either of the two most common elements\
     to be considered over the other.
    """
    from collections import Counter

    elements = Counter(
        item.element for item in mech.iter_items("body", "weapons", Type.HOOK) if item is not None
    ).most_common(2)
    # return None when there are no elements
    # or the difference between the two most common is indecisive
    if len(elements) == 0 or (len(elements) > 1 and elements[0][1] - elements[1][1] < threshold):
        return None

    # otherwise just return the most common one
    return elements[0][0]
