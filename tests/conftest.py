from pathlib import Path

import pytest
import requests

from supermechs.ext.platform import json_decoder

BASE_PATH = Path() / "tests" / "data"


@pytest.fixture(scope="session")
def item_pack():
    with requests.get(
        "https://raw.githubusercontent.com/Enegg/Item-packs/master/items.json"
    ) as resp:
        resp.raise_for_status()
        yield json_decoder(resp.content)


@pytest.fixture(params=[("item_v1.json", "@Darkstare"), ("item_v3.json", "@Eneg")])
def item_dict(request: pytest.FixtureRequest):
    name, pack_key = request.param
    return json_decoder((BASE_PATH / name).read_bytes()), pack_key


@pytest.fixture(scope="module")
def invalid_item():
    return json_decoder((BASE_PATH / "invalid_item_v3.json").read_bytes())
