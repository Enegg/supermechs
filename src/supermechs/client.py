from __future__ import annotations

import logging

from .item_pack import ItemPack
from .rendering import PackRenderer

__all__ = ("SMClient",)

LOGGER = logging.getLogger(__name__)

# TODO: "Client" doesn't really make sense. All we need is the State to store objects.
# Also, graphics related stuff should have their own store.

class SMClient:
    """Represents the SuperMechs app."""

    default_pack: ItemPack
    default_renderer: PackRenderer
