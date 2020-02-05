# -*- coding: utf-8 -*-

"""Test code for the built-in SQLite-based persistor."""


import pytest
from cb_binary_analysis.config.model import Config
from cb_binary_analysis.state.manager import StateManager


@pytest.fixture
def local_config():
    """
    Configuration for all the test cases in this module.
    """
    return Config.load("""
    id: cb-binary-analysis
    version: 0.0.1
    database:
      _provider: cb_binary_analysis.state.builtin.Persistor
      location: ":memory:"
    """)


def test_file_state_create_and_alter(local_config):
    manager = StateManager(local_config)
    cookie = manager.set_file_state("ABCDEFGH", {"file_size": 2000000, "file_name": "blort.exe",
                                                 "os_type": "WINDOWS", "engine_name": "default"})
    state1 = manager.lookup("ABCDEFGH")
    assert state1["persist_id"] == cookie
    assert state1["file_size"] == 2000000
    assert state1["file_name"] == "blort.exe"
    assert state1["file_hash"] == "ABCDEFGH"
    assert state1["os_type"] == "WINDOWS"
    assert state1["engine_name"] == "default"
    assert "time_sent" not in state1
    assert "time_returned" not in state1
    assert "time_published" not in state1
    cookie2 = manager.set_file_state("ABCDEFGH", {"time_sent": "2020-02-01T04:00:00",
                                                  "time_returned": "2020-02-01T04:05:00"}, cookie)
    assert cookie2 == cookie
    state2 = manager.lookup("ABCDEFGH")
    assert state2["persist_id"] == cookie
    assert state2["file_size"] == 2000000
    assert state2["file_name"] == "blort.exe"
    assert state2["file_hash"] == "ABCDEFGH"
    assert state2["os_type"] == "WINDOWS"
    assert state2["engine_name"] == "default"
    assert state2["time_sent"] == "2020-02-01T04:00:00"
    assert state2["time_returned"] == "2020-02-01T04:05:00"
    assert "time_published" not in state2


def test_file_state_newest_selected(local_config):
    manager = StateManager(local_config)
    cookie1 = manager.set_file_state("ABCDEFGH", {"file_size": 2000000, "file_name": "blort.exe",
                                                  "os_type": "WINDOWS", "engine_name": "default",
                                                  "time_sent": "2020-01-15T12:00:00",
                                                  "time_returned": "2020-01-15T12:05:00",
                                                  "time_published": "2020-01-15T12:05:01"})
    manager.set_file_state("ABCDEFGH", {"file_size": 2000000, "file_name": "blort.exe",
                                        "os_type": "WINDOWS", "engine_name": "another",
                                        "time_sent": "2020-01-14T12:00:00",
                                        "time_returned": "2020-01-14T12:05:00",
                                        "time_published": "2020-01-14T12:05:01"})
    state = manager.lookup("ABCDEFGH")
    assert state["persist_id"] == cookie1
    assert state["engine_name"] == "default"
    assert state["time_sent"] == "2020-01-15T12:00:00"
    assert state["time_returned"] == "2020-01-15T12:05:00"
    assert state["time_published"] == "2020-01-15T12:05:01"


def test_file_state_multi_engine(local_config):
    manager = StateManager(local_config)
    cookie1 = manager.set_file_state("ABCDEFGH", {"file_size": 2000000, "file_name": "blort.exe",
                                                  "os_type": "WINDOWS", "engine_name": "default",
                                                  "time_sent": "2020-01-15T12:00:00",
                                                  "time_returned": "2020-01-15T12:05:00",
                                                  "time_published": "2020-01-15T12:05:01"})
    cookie2 = manager.set_file_state("ABCDEFGH", {"file_size": 2000000, "file_name": "blort.exe",
                                                  "os_type": "WINDOWS", "engine_name": "another",
                                                  "time_sent": "2020-01-14T12:00:00",
                                                  "time_returned": "2020-01-14T12:05:00",
                                                  "time_published": "2020-01-14T12:05:01"})
    state = manager.lookup("ABCDEFGH", "default")
    assert state["persist_id"] == cookie1
    assert state["engine_name"] == "default"
    assert state["time_sent"] == "2020-01-15T12:00:00"
    assert state["time_returned"] == "2020-01-15T12:05:00"
    assert state["time_published"] == "2020-01-15T12:05:01"
    state = manager.lookup("ABCDEFGH", "another")
    assert state["persist_id"] == cookie2
    assert state["engine_name"] == "another"
    assert state["time_sent"] == "2020-01-14T12:00:00"
    assert state["time_returned"] == "2020-01-14T12:05:00"
    assert state["time_published"] == "2020-01-14T12:05:01"


def test_file_state_not_found(local_config):
    manager = StateManager(local_config)
    state = manager.lookup("QRSTUVWXYZ")
    assert state is None


def test_file_state_prune(local_config):
    manager = StateManager(local_config)
    cookie1 = manager.set_file_state("ABCDEFGH", {"file_size": 2000000, "file_name": "blort.exe",
                                                  "os_type": "WINDOWS", "engine_name": "default",
                                                  "time_sent": "2020-01-15T12:00:00",
                                                  "time_returned": "2020-01-15T12:05:00",
                                                  "time_published": "2020-01-15T12:05:01"})
    manager.set_file_state("EFGHIJKM", {"file_size": 2000000, "file_name": "foobar.exe",
                                        "os_type": "WINDOWS", "engine_name": "default",
                                        "time_sent": "2020-01-10T12:00:00",
                                        "time_returned": "2020-01-10T12:05:00",
                                        "time_published": "2020-01-10T12:05:01"})
    manager.prune("2020-01-12T00:00:00")
    state = manager.lookup("EFGHIJKM")
    assert state is None
    state = manager.lookup("ABCDEFGH")
    assert state["persist_id"] == cookie1
    assert state["file_name"] == "blort.exe"
