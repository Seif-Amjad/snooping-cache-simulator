"""Simulate bus-based snooping cache coherence."""

import re
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


class Protocol(Enum):
    """Protocol names accepted in input files."""

    WRITE_INVALIDATE_WRITE_THROUGH = "WRITE_INVALIDATE_WRITE_THROUGH"
    WRITE_INVALIDATE_WRITE_BACK = "WRITE_INVALIDATE_WRITE_BACK"
    WRITE_ONCE = "WRITE_ONCE"


@dataclass(frozen=True)
class Operation:
    """One processor action on one variable."""

    processor: str
    action: str
    variable: str
    value: int = None


@dataclass
class SimulationInput:
    """Validated initial configuration and operation sequence."""

    protocol: Protocol
    memory: dict
    processors: list
    operations: list


IDENTIFIER = r"[A-Za-z_][A-Za-z_0-9]*"
INTEGER = r"[+-]?[0-9]+"
ASSIGNMENT = re.compile(rf"({IDENTIFIER})\s*=\s*({INTEGER})")
OPERATION = re.compile(
    rf"({IDENTIFIER})\s*:\s*(Read|Write|Replace)\s*"
    rf"\(\s*({IDENTIFIER})\s*(?:,\s*({INTEGER})\s*)?\)"
)


def load_input(lines):
    """Parse configuration and operations from an iterable of input lines."""
    entries = []
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if line and not line.startswith("#"):
            entries.append((number, line))

    headers = {}
    for index, key in enumerate(("PROTOCOL", "MEMORY", "PROCESSORS")):
        if index >= len(entries):
            raise ValueError(f"missing {key} header")
        number, line = entries[index]
        name, separator, value = line.partition(":")
        if not separator or name.strip() != key:
            raise ValueError(f"line {number}: expected {key}: header")
        headers[key] = number, value.strip()

    number, name = headers["PROTOCOL"]
    try:
        protocol = Protocol(name)
    except ValueError:
        raise ValueError(f"line {number}: unknown protocol {name!r}") from None

    number, value = headers["MEMORY"]
    assignments = value.split(",") if value else []
    if not 1 <= len(assignments) <= 3:
        raise ValueError(f"line {number}: expected 1 to 3 memory variables")
    memory = {}
    for assignment in assignments:
        match = ASSIGNMENT.fullmatch(assignment.strip())
        if not match:
            raise ValueError(f"line {number}: malformed memory assignment {assignment!r}")
        variable, integer = match.groups()
        if variable in memory:
            raise ValueError(f"line {number}: duplicate memory variable {variable}")
        memory[variable] = int(integer)

    number, value = headers["PROCESSORS"]
    processors = [name.strip() for name in value.split(",")] if value else []
    if not 1 <= len(processors) <= 3:
        raise ValueError(f"line {number}: expected 1 to 3 processors")
    if any(not re.fullmatch(IDENTIFIER, name) for name in processors):
        raise ValueError(f"line {number}: malformed processor name")
    if len(set(processors)) != len(processors):
        raise ValueError(f"line {number}: duplicate processor name")

    operations = []
    for number, line in entries[3:]:
        match = OPERATION.fullmatch(line)
        if not match:
            raise ValueError(f"line {number}: malformed operation {line!r}")
        processor, action, variable, integer = match.groups()
        if (action == "Write") != (integer is not None):
            raise ValueError(f"line {number}: wrong number of arguments for {action}")
        if processor not in processors:
            raise ValueError(f"line {number}: unknown processor {processor}")
        if variable not in memory:
            raise ValueError(f"line {number}: unknown variable {variable}")
        operations.append(Operation(processor, action, variable, int(integer) if integer else None))
    return SimulationInput(protocol, memory, processors, operations)
