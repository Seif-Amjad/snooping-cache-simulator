import unittest

from simulator import Protocol, State
from tests.test_benchmarks import simulate


class EdgeCaseTests(unittest.TestCase):
    def test_replace_absent_then_read_after_replace(self):
        for protocol in Protocol:
            with self.subTest(protocol=protocol):
                simulator = simulate(protocol.value, """MEMORY: X=-1
PROCESSORS: P
P: Replace(X)
P: Write(X, 0)
P: Replace(X)
P: Read(X)
""")
                self.assertEqual(simulator.trace[1].caches, {"P": {}})
                self.assertEqual(simulator.trace[1].memory, {"X": -1})
                self.assertEqual(simulator.trace[3].caches, {"P": {}})
                self.assertEqual(simulator.trace[3].memory, {"X": 0})
                self.assertEqual(simulator.trace[4].event, "P reads X (Read-Miss)")
                self.assertEqual(simulator.trace[4].caches["P"]["X"][0], 0)
                self.assertEqual(sum(simulator.access_counts.values()), 2)
                self.assertEqual(simulator.bus.invalidations, 1)

    def test_three_variables_remain_independent_when_writing_an_invalid_copy(self):
        for protocol in Protocol:
            with self.subTest(protocol=protocol):
                simulator = simulate(protocol.value, """MEMORY: X=1, Y=2, Z=3
PROCESSORS: P, Q, R
P: Read(X)
Q: Read(X)
R: Read(Y)
R: Read(Z)
P: Write(X, 10)
Q: Write(X, 20)
""")
                prior, final = simulator.trace[-2:]
                self.assertEqual(prior.caches["Q"]["X"], (1, State.INV))
                self.assertEqual(final.event, "Q writes X (W-Miss)")
                self.assertEqual(final.caches["Q"]["X"][0], 20)
                self.assertEqual(final.caches["P"]["X"], (10, State.INV))
                self.assertEqual(final.caches["R"], prior.caches["R"])
                self.assertEqual((final.memory["Y"], final.memory["Z"]), (2, 3))
