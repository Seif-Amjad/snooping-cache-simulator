import unittest

from simulator import CoherenceSimulator, load_input


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
