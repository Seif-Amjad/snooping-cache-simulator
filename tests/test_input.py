import unittest

from simulator import Operation, Protocol, load_input


class InputTests(unittest.TestCase):
    def test_valid_input(self):
        config = load_input("""
            # Example
            PROTOCOL: WRITE_ONCE
            MEMORY: X=-5, Z=+80
            PROCESSORS: P, Q
            P: Read(X)
            Q: Write(Z, -12)
            P: Replace(X)
        """.splitlines())
        self.assertIs(config.protocol, Protocol.WRITE_ONCE)
        self.assertEqual(config.memory, {"X": -5, "Z": 80})
        self.assertEqual(config.processors, ["P", "Q"])
        self.assertEqual(config.operations, [
            Operation("P", "Read", "X"),
            Operation("Q", "Write", "Z", -12),
            Operation("P", "Replace", "X"),
        ])

    def test_invalid_input(self):
        valid = "PROTOCOL: WRITE_ONCE\nMEMORY: X=5\nPROCESSORS: P\nP: Read(X)"
        cases = (
            ("WRITE_ONCE", "OTHER", "unknown protocol"),
            ("MEMORY:", "DATA:", "expected MEMORY"),
            ("X=5", "X=5, Y=2, Z=3, W=4", "1 to 3 memory variables"),
            ("X=5", "X=5, X=6", "duplicate memory variable"),
            ("X=5", "X=", "malformed memory assignment"),
            ("PROCESSORS: P", "PROCESSORS: P, Q, R, S", "1 to 3 processors"),
            ("PROCESSORS: P", "PROCESSORS: P, P", "duplicate processor"),
            ("P: Read(X)", "Q: Read(X)", "unknown processor"),
            ("Read(X)", "Read(Y)", "unknown variable"),
            ("Read(X)", "Read[X]", "malformed operation"),
            ("Read(X)", "Read(X, 2)", "wrong number of arguments"),
            ("Read(X)", "Write(X)", "wrong number of arguments"),
        )
        for original, replacement, message in cases:
            with self.subTest(replacement=replacement):
                with self.assertRaisesRegex(ValueError, message):
                    load_input(valid.replace(original, replacement).splitlines())
