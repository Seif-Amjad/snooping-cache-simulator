"""Simulate bus-based snooping cache coherence."""

import argparse
import re
import sys
from collections import Counter
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


class Cache:
    """Store a private copy of each cached variable."""

    def __init__(self, processor_id):
        self.processor_id = processor_id
        self.blocks = {}

    def read(self, variable):
        block = self.blocks.get(variable)
        if block is not None and block.state is not State.INV:
            return block
        return None

    def write(self, variable, value, state):
        block = CacheBlock(variable, value, state)
        self.blocks[variable] = block
        return block

    def replace(self, variable):
        return self.blocks.pop(variable, None)

    def snoop(self, variable, new_state=None):
        block = self.read(variable)
        if block is not None and new_state is not None:
            block.state = new_state
        return block


class SharedBus:
    """Send transactions to all peer caches and access main memory."""

    def __init__(self, caches, memory):
        self.caches = list(caches)
        self.memory = memory
        self.invalidations = 0
        self.write_backs = 0
        self.write_throughs = 0

    def peers(self, requester):
        return (cache for cache in self.caches if cache is not requester)

    def broadcast_read(self, requester, variable, owner_state=None, shared_state=None,
                       *, reserved_state=None):
        owner = None
        for cache in self.peers(requester):
            block = cache.snoop(variable)
            if block is not None and block.state is owner_state:
                owner = block
            elif block is not None and block.state is reserved_state:
                block.state = shared_state
        if owner is None:
            return self.memory.read(variable)
        # Flush the old owner's value before the requester can overwrite it.
        self.write_back_to_memory(variable, owner.value)
        if shared_state is not None:
            owner.state = shared_state
        return owner.value

    def broadcast_invalidate(self, requester, variable):
        self.invalidations += 1
        for cache in self.peers(requester):
            cache.snoop(variable, State.INV)

    def write_back_to_memory(self, variable, value):
        self.write_backs += 1
        self.memory.write(variable, value)

    def write_through_to_memory(self, variable, value):
        self.write_throughs += 1
        self.memory.write(variable, value)


@dataclass
class TraceRow:
    """Values and states captured after one operation."""

    event: str
    memory: dict
    caches: dict


class CoherenceSimulator:
    """Execute operations under the selected coherence protocol."""

    def __init__(self, config):
        self.protocol = config.protocol
        self.operations = config.operations
        self.memory = MainMemory(config.memory)
        self.caches = {name: Cache(name) for name in config.processors}
        self.bus = SharedBus(self.caches.values(), self.memory)
        self.access_counts = Counter()
        self.trace = [self.snapshot("Initial State")]

    def snapshot(self, event):
        return TraceRow(event, dict(self.memory.storage), {
            name: {tag: (block.value, block.state) for tag, block in cache.blocks.items()}
            for name, cache in self.caches.items()
        })

    def step(self, operation):
        cache = self.caches[operation.processor]
        variable = operation.variable
        block = cache.read(variable)
        hit = block is not None
        if operation.action == "Read":
            event = f"reads {variable} (Read-{'Hit' if hit else 'Miss'})"
        elif operation.action == "Write":
            verb = "updates" if hit else "writes"
            event = f"{verb} {variable} (W-{'Hit' if hit else 'Miss'})"
        else:
            event = f"replaces {variable} (Replace)"

        handlers = {
            Protocol.WRITE_INVALIDATE_WRITE_THROUGH: self.write_through,
            Protocol.WRITE_INVALIDATE_WRITE_BACK: self.write_back,
            Protocol.WRITE_ONCE: self.write_once,
        }
        handlers[self.protocol](cache, operation, block)
        if operation.action in ("Read", "Write"):
            self.access_counts[operation.action, hit] += 1
        row = self.snapshot(f"{operation.processor} {event}")
        self.trace.append(row)
        return row

    def run_all(self):
        for operation in self.operations[len(self.trace) - 1:]:
            self.step(operation)
        return self.trace

    def write_through(self, cache, operation, block):
        variable = operation.variable
        if operation.action == "Replace":
            cache.replace(variable)
        elif operation.action == "Read":
            if block is None:
                value = self.bus.broadcast_read(cache, variable)
                cache.write(variable, value, State.VALID)
        else:
            if block is None:
                self.bus.broadcast_read(cache, variable)
            self.bus.broadcast_invalidate(cache, variable)
            self.bus.write_through_to_memory(variable, operation.value)
            cache.write(variable, operation.value, State.VALID)

    def replace(self, cache, variable, dirty_state):
        block = cache.replace(variable)
        if block is not None and block.state is dirty_state:
            self.bus.write_back_to_memory(variable, block.value)

    def write_back(self, cache, operation, block):
        variable = operation.variable
        if operation.action == "Replace":
            self.replace(cache, variable, State.RW)
        elif operation.action == "Read":
            if block is None:
                value = self.bus.broadcast_read(cache, variable, State.RW, State.RO)
                cache.write(variable, value, State.RO)
        else:
            if block is None:
                self.bus.broadcast_read(cache, variable, State.RW)
            if block is None or block.state is State.RO:
                self.bus.broadcast_invalidate(cache, variable)
            cache.write(variable, operation.value, State.RW)

    def write_once(self, cache, operation, block):
        variable = operation.variable
        if operation.action == "Replace":
            self.replace(cache, variable, State.DIRTY)
        elif operation.action == "Read":
            if block is None:
                # A peer read breaks the reservation without flushing a clean copy.
                value = self.bus.broadcast_read(
                    cache, variable, State.DIRTY, State.VALID, reserved_state=State.RES
                )
                cache.write(variable, value, State.VALID)
        else:
            if block is None:
                # The assignment's write-miss rule flushes the old owner, not the new write.
                self.bus.broadcast_read(cache, variable, State.DIRTY)
                self.bus.broadcast_invalidate(cache, variable)
                state = State.DIRTY
            elif block.state is State.VALID:
                self.bus.broadcast_invalidate(cache, variable)
                self.bus.write_through_to_memory(variable, operation.value)
                state = State.RES
            else:
                state = State.DIRTY
            cache.write(variable, operation.value, state)

    def print_trace_table(self, output=None):
        """Print an aligned table of all snapshots, including step zero."""
        variables = tuple(self.memory.storage)
        header = ["Serial", "Event", *(f"Mem({tag})" for tag in variables)]
        for processor in self.caches:
            for tag in variables:
                header.extend((f"{processor} Val({tag})", f"{processor} State({tag})"))

        rows = [header]
        for serial, row in enumerate(self.trace):
            cells = [str(serial), row.event, *(str(row.memory[tag]) for tag in variables)]
            for cache in row.caches.values():
                for tag in variables:
                    block = cache.get(tag)
                    cells.extend((str(block[0]), block[1].value) if block else ("-", "-"))
            rows.append(cells)

        widths = [max(map(len, column)) for column in zip(*rows)]
        table = [" | ".join(cell.ljust(width) for cell, width in zip(row, widths))
                 for row in rows]
        rule = "=" * len(table[0])
        print(rule, table[0], rule, *table[1:], rule, sep="\n", file=output)

    def print_summary(self, output=None):
        """Print final values and the transaction counts."""
        final = self.trace[-1]
        print("\nFinal Summary", file=output)
        memory = ", ".join(f"{tag}={value}" for tag, value in final.memory.items())
        print(f"Memory: {memory}", file=output)
        for processor, cache in final.caches.items():
            copies = []
            for tag in final.memory:
                block = cache.get(tag)
                copies.append(f"{tag}={block[0]} ({block[1].value})" if block else f"{tag}=- (-)")
            print(f"{processor}: {', '.join(copies)}", file=output)
        for action in ("Read", "Write"):
            print(f"{action}-Hits: {self.access_counts[action, True]}", file=output)
            print(f"{action}-Misses: {self.access_counts[action, False]}", file=output)
        print(f"Bus invalidation commands: {self.bus.invalidations}", file=output)
        print(f"Memory write-backs: {self.bus.write_backs}", file=output)
        print(f"Memory write-throughs: {self.bus.write_throughs}", file=output)


def main(argv=None):
    """Run the simulator with a file or standard input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="input file (default: stdin)")
    arguments = parser.parse_args(argv)
    try:
        if arguments.input is None:
            config = load_input(sys.stdin)
        else:
            with open(arguments.input, encoding="utf-8-sig") as input_file:
                config = load_input(input_file)
    except (ValueError, OSError) as error:
        parser.exit(2, f"error: {error}\n")

    simulator = CoherenceSimulator(config)
    simulator.run_all()
    simulator.print_trace_table()
    simulator.print_summary()


if __name__ == "__main__":
    main()
