supermechs
==========
<p allign="center">
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" /></a>
  <a><img src="https://img.shields.io/github/commit-activity/w/Enegg/supermechs.svg?style=flat-square" alt="Commit activity" /></a>
</p>
This library provides a foundation for modeling the behavior & mechanics of the SuperMechs game.

Installing
----------
**Python 3.10 or higher is required.**

To install the library, you can run the following command:
```sh
python -m pip install git+https://github.com/Enegg/supermechs.git
```
`python` should be replaced with your python executable.

There's currently no PyPI release available.

Versioning
----------
The library is in its alpha stage. The API is immature and may substantially change as development progresses.


Quick example
-------------
```py
import requests  # pip install requests
from supermechs.ext.deserializers import to_item_pack

with requests.get("https://raw.githubusercontent.com/Enegg/Item-packs/master/items.json") as resp:
    resp.raise_for_status()
    pack = to_item_pack(resp.json())

print(pack.data)
# do stuff with pack
```
