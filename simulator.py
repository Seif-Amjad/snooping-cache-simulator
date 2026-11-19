"""Simulate bus-based snooping cache coherence."""

from dataclasses import dataclass
from enum import Enum


class State(Enum):
    """Cache block states across the supported protocols."""

    VALID = "VALID"
    INV = "INV"
    RO = "RO"
    RW = "RW"
    RES = "RES"
    DIRTY = "DIRTY"


@dataclass
class CacheBlock:
    """A cached copy of one memory variable."""

    tag: str
    value: int
    state: State


class MainMemory:
    """Store the shared values visible in main memory."""

    def __init__(self, values):
        self.storage = dict(values)

    def read(self, variable):
        return self.storage[variable]

    def write(self, variable, value):
        self.storage[variable] = value
