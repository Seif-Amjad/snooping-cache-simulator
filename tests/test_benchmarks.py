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

BENCHMARK_2 = """MEMORY: X=10, Z=80
PROCESSORS: P1, P2, P3
P1: Read(X)
P2: Read(X)
P3: Read(X)
P1: Write(X, 35)
P1: Read(Z)
P2: Read(X)
P3: Write(X, 15)
P1: Write(Z, 81)
"""


def simulate(protocol, benchmark):
    config = load_input(f"PROTOCOL: {protocol}\n{benchmark}".splitlines())
    simulator = CoherenceSimulator(config)
    simulator.run_all()
    return simulator


class BenchmarkTests(unittest.TestCase):
    def assert_variable_trace(self, simulator, variable, expected):
        actual = []
        for row in simulator.trace:
            copies = []
            for cache in row.caches.values():
                block = cache.get(variable)
                copies.append(f"{block[0]} {block[1].value}" if block else "-")
            actual.append((row.memory[variable], *copies))
        self.assertEqual(actual, expected)

    def assert_benchmark_1(self, protocol, expected):
        self.assert_variable_trace(simulate(protocol, BENCHMARK_1), "X", [(5, "-", "-"), *expected])

    def assert_benchmark_2(self, protocol, x_trace, z_read, z_write, transfers):
        simulator = simulate(protocol, BENCHMARK_2)
        self.assert_variable_trace(simulator, "X", [(10, "-", "-", "-"), *x_trace])
        self.assert_variable_trace(simulator, "Z", [
            *((80, "-", "-", "-"),) * 5,
            *((80, z_read, "-", "-"),) * 3,
            (*z_write, "-", "-"),
        ])
        counts = simulator.access_counts
        self.assertEqual([counts["Read", True], counts["Read", False],
                          counts["Write", True], counts["Write", False]], [0, 5, 2, 1])
        bus = simulator.bus
        self.assertEqual((bus.invalidations, bus.write_backs, bus.write_throughs), transfers)

    def test_benchmark_2_write_through(self):
        self.assert_benchmark_2("WRITE_INVALIDATE_WRITE_THROUGH", [
            (10, "10 VALID", "-", "-"),
            (10, "10 VALID", "10 VALID", "-"),
            (10, "10 VALID", "10 VALID", "10 VALID"),
            (35, "35 VALID", "10 INV", "10 INV"),
            (35, "35 VALID", "10 INV", "10 INV"),
            (35, "35 VALID", "35 VALID", "10 INV"),
            (15, "35 INV", "35 INV", "15 VALID"),
            (15, "35 INV", "35 INV", "15 VALID"),
        ], "80 VALID", (81, "81 VALID"), (3, 0, 3))

    def test_benchmark_2_write_back(self):
        self.assert_benchmark_2("WRITE_INVALIDATE_WRITE_BACK", [
            (10, "10 RO", "-", "-"),
            (10, "10 RO", "10 RO", "-"),
            (10, "10 RO", "10 RO", "10 RO"),
            (10, "35 RW", "10 INV", "10 INV"),
            (10, "35 RW", "10 INV", "10 INV"),
            (35, "35 RO", "35 RO", "10 INV"),
            (35, "35 INV", "35 INV", "15 RW"),
            (35, "35 INV", "35 INV", "15 RW"),
        ], "80 RO", (80, "81 RW"), (3, 1, 0))

    def test_benchmark_2_write_once(self):
        self.assert_benchmark_2("WRITE_ONCE", [
            (10, "10 VALID", "-", "-"),
            (10, "10 VALID", "10 VALID", "-"),
            (10, "10 VALID", "10 VALID", "10 VALID"),
            (35, "35 RES", "10 INV", "10 INV"),
            (35, "35 RES", "10 INV", "10 INV"),
            (35, "35 VALID", "35 VALID", "10 INV"),
            (35, "35 INV", "35 INV", "15 DIRTY"),
            (35, "35 INV", "35 INV", "15 DIRTY"),
        ], "80 VALID", (81, "81 RES"), (3, 0, 2))

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
