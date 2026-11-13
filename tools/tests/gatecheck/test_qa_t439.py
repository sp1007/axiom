#!/usr/bin/env python3
"""QA (T439) boundary tests for tools/gatecheck.py check table: the seams the T439 fix touches.

Python 3 standard library only.
"""

import contextlib
import importlib.util
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import test_gatecheck as tg
from test_gatecheck import GATECHECK, base_repo, milestone


def load_gatecheck():
    spec = importlib.util.spec_from_file_location("gatecheck_qa_t439", str(GATECHECK))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CheckTableTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="gatecheck-qa-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_only_internal_checks_lack_a_command(self):
        # Guards the T439 root cause: a self-test must not assume some check is "without a command".
        mod = load_gatecheck()
        without = sorted(n for n, c in mod.CHECK_COMMANDS.items() if c is None)
        self.assertEqual(without, sorted(mod.INTERNAL_CHECKS))

    def test_every_check_command_script_exists_in_the_repository(self):
        mod = load_gatecheck()
        root = GATECHECK.parent.parent
        if not (root / "spec").is_dir():
            self.skipTest("not run inside the repository")
        for name, cmd in mod.CHECK_COMMANDS.items():
            if cmd is None:
                continue
            script = cmd[1] if cmd[0] in ("python", "bash") else cmd[0]
            with self.subTest(check=name):
                self.assertTrue((root / script).is_file(), script)

    def test_no_command_check_blocks_later_milestones_too(self):
        # R9 + cumulative rule: a no-command check must not let a LATER milestone pass either.
        blocks = [milestone("MS-P1", "T022", None, ["tests/unit/kernel"], checks=["differential"]),
                  milestone("MS-P3", "T022", "MS-P1", ["tests/unit/kernel"], checks=["gatecheck"],
                            introduces=["F-INT", "F-CF"])]
        r = base_repo(self.tmp, blocks=blocks)
        mod = load_gatecheck()
        mod.CHECK_COMMANDS["differential"] = None
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mod.main(["--root", str(r.root), "--gate", "T022"])
        self.assertEqual(rc, 1)
        self.assertEqual(buf.getvalue().strip().splitlines(),
                         ["MS-P1 BLOCKED: check differential has no command yet (AXS-BOOT-050)",
                          "MS-P3 BLOCKED: earlier milestone MS-P1 is blocked"])

    def test_patching_one_module_copy_does_not_leak(self):
        # The T439 test patches a private module copy; a fresh load and the CLI still see the real table.
        mod = load_gatecheck()
        mod.CHECK_COMMANDS["differential"] = None
        self.assertEqual(load_gatecheck().CHECK_COMMANDS["differential"], ["python", "tools/axtest.py", "diff"])
        blocks = [milestone("MS-P1", "T022", None, ["tests/unit/kernel"], checks=["differential"])]
        r = base_repo(self.tmp, blocks=blocks)
        rc, out, err = r.run("--gate", "T022")
        self.assertNotIn("has no command", out)

    def test_determinism_check_runs_ci_sh(self):
        if shutil.which("bash") is None:
            self.skipTest("bash not available")
        blocks = [milestone("MS-P1", "T022", None, ["tests/unit/kernel"], checks=["determinism"])]
        r = base_repo(self.tmp, blocks=blocks)
        r.write("tools/ci.sh", "echo ci ok\nexit 0\n")
        rc, out, err = r.run("--gate", "T022")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out.strip().splitlines(), ["MS-P1 PASS"])
        r.write("tools/ci.sh", "echo nondeterministic\nexit 7\n")
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 1)
        self.assertIn("MS-P1 BLOCKED: check determinism exited 7: nondeterministic", out)


if __name__ == "__main__":
    unittest.main()
