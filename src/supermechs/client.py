from __future__ import annotations

import logging

from .item_pack import ItemPack
from .rendering import PackRenderer
from .state import SMState
from .typedefs import AnyItemPack
from .utils import MISSING

__all__ = ("SMClient",)

LOGGER = logging.getLogger(__name__)

# TODO: "Client" doesn't really make sense. All we need is the State to store objects.
# Also, graphics related stuff should have their own store.

class SMClient:
    """Represents the SuperMechs app."""

    default_pack: ItemPack
    default_renderer: PackRenderer

    def __init__(self) -> None:
        self.state = SMState()
        self.default_pack = MISSING

    async def set_default_item_pack(self, pack_data: AnyItemPack, /) -> None:
        """Set a pack as the default one."""
        # honestly, this should not store the renderer
        self.default_pack = self.state.store_item_pack(pack_data, False)
        self.default_renderer = self.state.store_pack_renderer(pack_data)
        await self.default_renderer.load(pack_data)

    def get_default_renderer(self) -> PackRenderer:
        return self.state.get_pack_renderer(self.default_pack.key)
