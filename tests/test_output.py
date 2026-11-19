import io
import subprocess
import sys
import unittest
from pathlib import Path

from tests.test_benchmarks import BENCHMARK_1, simulate


class OutputTests(unittest.TestCase):
    def test_trace_alignment_for_supported_sizes(self):
        for processor_count in range(1, 4):
            for variable_count in range(1, 4):
                with self.subTest(processors=processor_count, variables=variable_count):
                    processors = ", ".join(("P", "LongName", "R")[:processor_count])
                    memory = ", ".join(("X=-1234", "Y=6", "Z=0")[:variable_count])
                    simulator = simulate("WRITE_ONCE", f"""MEMORY: {memory}
PROCESSORS: {processors}
P: Read(X)
P: Replace(X)
""")
                    output = io.StringIO()
                    simulator.print_trace_table(output)
                    lines = output.getvalue().splitlines()
                    self.assertEqual(len(lines), 7)
                    self.assertEqual({len(line) for line in lines}, {len(lines[0])})
                    self.assertEqual(lines[0], lines[2])
                    self.assertEqual(lines[0], lines[-1])
                    self.assertEqual(lines[1].count("|"),
                                     1 + variable_count + 2 * processor_count * variable_count)
                    self.assertIn("0      | Initial State", lines[3])
                    self.assertIn("P reads X (Read-Miss)", lines[4])
                    self.assertIn("P replaces X (Replace)", lines[5])
                    self.assertEqual([cell.strip() for cell in lines[5].split("|")][-2:], ["-", "-"])

    def test_cli_reads_stdin_and_reports_bad_input(self):
        script = Path(__file__).resolve().parents[1] / "simulator.py"
        command = [sys.executable, "-B", str(script)]
        completed = subprocess.run(command, input=f"PROTOCOL: WRITE_ONCE\n{BENCHMARK_1}",
                                   text=True, capture_output=True, check=True)
        self.assertIn("Q reads X (Read-Miss)", completed.stdout)
        failed = subprocess.run(command, input="invalid\n", text=True, capture_output=True)
        self.assertEqual(failed.returncode, 2)
        self.assertIn("line 1: expected PROTOCOL", failed.stderr)
