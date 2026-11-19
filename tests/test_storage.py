import unittest

from simulator import CacheBlock, MainMemory, State


class StorageTests(unittest.TestCase):
    def test_block_keeps_value_when_invalidated(self):
        block = CacheBlock("X", 5, State.VALID)
        block.state = State.INV
        self.assertEqual((block.tag, block.value, block.state), ("X", 5, State.INV))

    def test_memory_copies_initial_values(self):
        initial = {"X": 5}
        memory = MainMemory(initial)
        self.assertEqual(memory.read("X"), 5)
        memory.write("X", 10)
        self.assertEqual(memory.read("X"), 10)
        self.assertEqual(initial, {"X": 5})
