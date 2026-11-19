import unittest

from simulator import Cache, MainMemory, SharedBus, State


class BusTests(unittest.TestCase):
    def setUp(self):
        self.requester, self.peer, self.other = (Cache(name) for name in ("P", "Q", "R"))
        self.memory = MainMemory({"X": 5})
        self.bus = SharedBus((self.requester, self.peer, self.other), self.memory)

    def test_invalidation_only_touches_peer_copies(self):
        self.requester.write("X", 5, State.VALID)
        self.peer.write("X", 5, State.VALID)
        self.bus.broadcast_invalidate(self.requester, "X")
        self.assertIs(self.requester.read("X").state, State.VALID)
        self.assertIsNone(self.peer.read("X"))
        self.assertIs(self.peer.blocks["X"].state, State.INV)
        self.assertNotIn("X", self.other.blocks)

    def test_broadcast_read_from_memory_and_owner(self):
        self.assertEqual(self.bus.broadcast_read(self.requester, "X"), 5)
        block = self.peer.write("X", 20, State.RW)
        self.assertEqual(self.bus.broadcast_read(self.requester, "X", State.RW, State.RO), 20)
        self.assertEqual(self.memory.read("X"), 20)
        self.assertIs(block.state, State.RO)
