import pytest

from api.tests import *  # noqa: F401, F403


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("RABBITMQ_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "test")
    monkeypatch.setenv("DB_PASSWORD", "test")

    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    import main
    main._config_cache.clear()
