import typing as t

from attrs import define

from supermechs.api import AnyStatsMapping

Entry = t.Sequence[t.Any]


@define
class StatsGroup:
    """Merges a set of mappings and allows for operations on them."""

    size: t.Final[int]
    """The number of side to side entries to compare."""
    key_order: t.Final[t.MutableSequence[str]]
    """The order in which final keys should appear."""
    entries: t.Final[t.MutableMapping[str, Entry]]
    """Current set of entries."""

    def __init__(self, *stat_mappings: AnyStatsMapping, key_order: t.Sequence[str]) -> None:
        if len(stat_mappings) < 2:
            raise ValueError("Need at least two mappings to compare")

        self.size = len(stat_mappings)
        self.key_order = sorted(
            set[str]().union(*map(AnyStatsMapping.keys, stat_mappings)), key=key_order.index
        )
        self.entries = {
            key: tuple(mapping.get(key) for mapping in stat_mappings) for key in self.key_order
        }

    def __str__(self) -> str:
        return "\n".join(f"{key}: {', '.join(value)}" for key, value in self)

    def __iter__(self) -> t.Iterator[tuple[str, Entry]]:
        for key in self.key_order:
            yield key, self.entries[key]

    def insert_entry(self, key: str, index: int, entry: Entry) -> None:
        """Insert given key: entry pair at given index."""
        self.key_order.insert(index, key)
        self.entries[key] = entry

    def insert_after(self, key: str, after: str, entry: Entry) -> int:
        """Insert 'key' after another key. Returns the index it inserted at."""
        index = self.key_order.index(after) + 1
        self.insert_entry(key, index, entry)
        return index

    def remove_entry(self, key: str) -> Entry:
        """Remove and return an existing entry."""
        self.key_order.remove(key)
        return self.entries.pop(key)
