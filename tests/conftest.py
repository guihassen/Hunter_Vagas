import copy
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def base_config():
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return copy.deepcopy(config)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Collectors sleep() between requests to be polite; skip it in tests."""
    import time

    monkeypatch.setattr(time, "sleep", lambda *_args, **_kwargs: None)
