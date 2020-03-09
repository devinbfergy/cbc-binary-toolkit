"""Test code for the persistence state manager."""

import uuid

from dateutil.parser import parse
from cbc_binary_toolkit.state.manager import BasePersistor, BasePersistorFactory


class MockPersistor(BasePersistor):
    """Mock Persistor"""

    def __init__(self):
        """Constructor"""
        self.db = dict()

    def get_file_state(self, binary_hash, engine=None):
        """Mock get file state"""
        return self.db.get(binary_hash, None)

    def set_file_state(self, binary_hash, attrs, rowid=None):
        """Mock set file state"""
        self.db[binary_hash] = attrs
        self.db[binary_hash]["file_hash"] = binary_hash
        return uuid.uuid4()

    def get_unfinished_states(self, engine):
        """Mock get_unfinished_states"""
        unfinished = []
        for key in self.db.keys():
            if self.db[key]["engine_name"] == engine and self.db[key].get("time_returned", None) is None:
                unfinished.append(self.db[key])
        return unfinished

    def prune(self, timestamp):
        """Mock prune"""
        prune_time = parse(timestamp)
        for key in self.db.keys():
            if parse(self.db[key]["time_sent"]) < prune_time:
                del self.db[key]


class MockPersistorFactory(BasePersistorFactory):
    """Mock Persistor Factory"""
    def create_persistor(self, config):
        """Mock create persistor"""
        return MockPersistor()
