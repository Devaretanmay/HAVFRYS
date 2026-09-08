"""Unit tests for Volf CI Integration."""

import unittest
from volf.ci.runner import VolfCIRunner, run_ci_step


class TestCIIntegration(unittest.TestCase):

    def test_ci_runner_executes_simple_command(self):
        runner = VolfCIRunner(workdir=".", block_network=True, sandbox=False)
        res = runner.run_step("echo 'Hello CI Volf'")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["returncode"], 0)
        self.assertIn("Hello CI Volf", res["stdout"])

    def test_ci_runner_captures_failure_exit_code(self):
        runner = VolfCIRunner(workdir=".", block_network=True, sandbox=False)
        res = runner.run_step("exit 42")
        self.assertEqual(res["returncode"], 42)

    def test_ci_runner_helper_function(self):
        code = run_ci_step("echo 'Testing helper'", block_network=True, sandbox=False)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
