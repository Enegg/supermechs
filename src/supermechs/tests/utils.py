from supermechs.utils import _is_pascal, acronym_of

strings: list[tuple[str, bool]] = [
    ("FooBar", True),
    ("fooBar", False),
    ("Foo Bar", False),
    ("FB", False),
    ("Foo", True),
    ("FooBAr", False)
]

for string, outcome in strings:
    assert _is_pascal(string) == outcome, f"{string!r} has wrong outcome"


names = [
    ("HeronMark", "hm"),
    ("EMP", None),
    ("Overcharged EMP", "oemp"),
    ("Overcharged Rocket Battery", "orb")
]

for name, outcome in names:
    acronym = acronym_of(name)
    assert acronym == outcome, f"Acronym of {name!r} is not {outcome!r} but {acronym!r}"
