import unittest

from simulator import CoherenceSimulator, State, load_input


BENCHMARK_1 = """MEMORY: X=5
PROCESSORS: P, Q
P: Read(X)
Q: Read(X)
Q: Write(X, 10)
Q: Read(X)
Q: Write(X, 15)
P: Write(X, 20)
Q: Read(X)
"""


def simulate(protocol, benchmark):
    config = load_input(f"PROTOCOL: {protocol}\n{benchmark}".splitlines())
    simulator = CoherenceSimulator(config)
    simulator.run_all()
    return simulator


class BenchmarkTests(unittest.TestCase):
    def assert_benchmark_1(self, protocol, expected):
        simulator = simulate(protocol, BENCHMARK_1)
        actual = []
        for row in simulator.trace:
            copies = []
            for cache in row.caches.values():
                block = cache.get("X")
                copies.append(f"{block[0]} {block[1].value}" if block else "-")
            actual.append((row.memory["X"], *copies))
        self.assertEqual(actual, [(5, "-", "-"), *expected])

    def test_benchmark_1_write_through(self):
        self.assert_benchmark_1("WRITE_INVALIDATE_WRITE_THROUGH", [
            (5, "5 VALID", "-"),
            (5, "5 VALID", "5 VALID"),
            (10, "5 INV", "10 VALID"),
            (10, "5 INV", "10 VALID"),
            (15, "5 INV", "15 VALID"),
            (20, "20 VALID", "15 INV"),
            (20, "20 VALID", "20 VALID"),
        ])

    def test_benchmark_1_write_back(self):
        self.assert_benchmark_1("WRITE_INVALIDATE_WRITE_BACK", [
            (5, "5 RO", "-"),
            (5, "5 RO", "5 RO"),
            (5, "5 INV", "10 RW"),
            (5, "5 INV", "10 RW"),
            (5, "5 INV", "15 RW"),
            (15, "20 RW", "15 INV"),
            (20, "20 RO", "20 RO"),
        ])

    def test_write_back_replace_flushes_owner(self):
        simulator = simulate("WRITE_INVALIDATE_WRITE_BACK", """MEMORY: X=5
PROCESSORS: P
P: Read(X)
P: Write(X, 9)
P: Replace(X)
""")
        self.assertEqual(simulator.trace[-2].memory, {"X": 5})
        self.assertEqual(simulator.trace[-1].memory, {"X": 9})
        self.assertEqual(simulator.trace[-1].caches, {"P": {}})

    def test_benchmark_1_write_once(self):
        self.assert_benchmark_1("WRITE_ONCE", [
            (5, "5 VALID", "-"),
            (5, "5 VALID", "5 VALID"),
            (10, "5 INV", "10 RES"),
            (10, "5 INV", "10 RES"),
            (10, "5 INV", "15 DIRTY"),
            (15, "20 DIRTY", "15 INV"),
            (20, "20 VALID", "20 VALID"),
        ])

    def test_write_once_peer_read_breaks_reservation(self):
        simulator = simulate("WRITE_ONCE", """MEMORY: X=5
PROCESSORS: P, Q
P: Read(X)
P: Write(X, 8)
Q: Read(X)
P: Write(X, 9)
""")
        self.assertEqual(simulator.trace[-2].caches, {
            "P": {"X": (8, State.VALID)}, "Q": {"X": (8, State.VALID)},
        })
        self.assertEqual(simulator.trace[-1].memory, {"X": 9})
        self.assertEqual(simulator.trace[-1].caches["Q"]["X"], (8, State.INV))

    def test_write_once_replace_flushes_dirty_copy(self):
        simulator = simulate("WRITE_ONCE", """MEMORY: X=5
PROCESSORS: P
P: Read(X)
P: Write(X, 8)
P: Write(X, 9)
P: Replace(X)
""")
        self.assertEqual(simulator.trace[-2].memory, {"X": 8})
        self.assertEqual(simulator.trace[-1].memory, {"X": 9})
        self.assertEqual(simulator.trace[-1].caches, {"P": {}})
