"""Gate (QA) additional self-tests of tools/axtest.py, written by the T005 gate reviewer.

Edge and seam cases the engineer's suite did not cover: CRLF test headers (Windows checkout without
.gitattributes), concatenation of repeated `stdout:` lines without implied newline, the oracle-UB exit
code 125 as an ordinary exit code (SPEC-03 AXS-SEM-082/092), a crashing native program whose expected
exit code does not match the crash status, and `{compiler}` substitution plus `--exclude-requires` in
an exec manifest. Python 3 standard library only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_axtest import Case, hdr, STUB  # noqa: E402


class GateEdgeTests(Case):
    def test_crlf_header_lines_do_not_leak_carriage_returns(self):
        # only the header (parsed by the runner) uses CRLF; the stub splits its `//@` lines on LF
        src = hdr("test: run", "exit: 2", "stdout: ab\\n").replace("\n", "\r\n") + "//@ out ab\\n\n//@ exit 2\n"
        self.put("run/crlfhdr.ax", src.encode("utf-8"))
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/crlfhdr.ax [interp]"), "PASS", res)
        self.assertEqual(self.state(res, "run/crlfhdr.ax [native]"), "PASS", res)

    def test_repeated_stdout_lines_concatenate_without_implied_newline(self):
        self.put("run/cat.ax", hdr("test: run", "modes: interp", "stdout: a", "stdout: b\\n") + "//@ out ab\\n\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/cat.ax [interp]"), "PASS", res)
        # "a\nb\n" must not match "a" + "b\n"
        self.put("run/cat.ax", hdr("test: run", "modes: interp", "stdout: a", "stdout: b\\n") + "//@ out a\\nb\\n\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/cat.ax [interp]"), "FAIL", res)

    def test_exit_125_oracle_ub_is_an_ordinary_exit_code(self):
        body = "//@ err error[AX_UNSAFE_INTERP_UB]: use after free\\n\n//@ exit 125\n"
        self.put("run/ub.ax", hdr("test: run", "modes: interp", "exit: 125") + body)
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/ub.ax [interp]"), "PASS", res)
        self.put("run/ub.ax", hdr("test: run", "modes: interp") + body)
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/ub.ax [interp]"), "FAIL", res)   # not TIMEOUT, not CRASH

    def test_native_crash_with_other_expected_exit_is_crash_not_fail(self):
        self.put("run/nc.ax", hdr("test: run", "exit: 3", "modes: native") + "//@ crash\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/nc.ax [native]"), "CRASH", res)
        self.assertEqual(self.doc["counts"]["crash"], 1)
        self.assertEqual(self.rc, 1)

    def test_exec_manifest_compiler_placeholder_and_exclude_requires(self):
        self.put("unit/ver.test", "# version of the compiler under test\n"
                                  "cmd: {compiler} version\n"
                                  "exit: 0\n"
                                  "stdout: stubcc 0\\n\n"
                                  "requires: axiom0-internal\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "unit/ver.test"), "PASS", res)
        res = self.run_axtest("--exclude-requires", "axiom0-internal")
        st, msg = res["unit/ver.test"]
        self.assertEqual(st, "SKIP")
        self.assertIn("axiom0-internal", msg)
        self.assertEqual(self.rc, 0)


if __name__ == "__main__":
    import unittest
    unittest.main()
