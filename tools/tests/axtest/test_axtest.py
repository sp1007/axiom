"""Self-tests of tools/axtest.py (T005).

Every test builds a scratch repository root (tests/ tree), runs the real runner as a subprocess with
the stub compiler `stubcc.py` (see its docstring for the `//@` behaviour lines) and checks the states,
messages, summary line and exit status. Python 3 standard library only.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
AXTEST = HERE.parent.parent / "axtest.py"
STUB = HERE / "stubcc.py"

sys.path.insert(0, str(AXTEST.parent))
import axtest  # noqa: E402  (the module under test, for the pure-function checks)

GREETING = "Xin chào thế giới"
GREETING_ESC = "Xin chào thế giới\\n"


class Case(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="axtest-self-"))
        # the root path contains a space on purpose (the real repository path does too)
        self.root = self.base / "root with space"
        self.tests = self.root / "tests"
        self.tests.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    # -- helpers ----------------------------------------------------------------------------

    def put(self, rel, content):
        p = self.tests / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        data = content if isinstance(content, bytes) else content.encode("utf-8")
        p.write_bytes(data)
        return p

    def run_axtest(self, *args, env=None, compiler=None, json_mode=True, exe_suffix=".py"):
        cmd = [sys.executable, str(AXTEST), "--root", str(self.root),
               "--compiler", str(compiler or STUB), "--exe-suffix", exe_suffix]
        if json_mode:
            cmd.append("--json")
        cmd += list(args)
        full_env = dict(os.environ)
        for k in ("STUB_FEATURES", "STUB_NO_FEATURES_CMD", "STUB_FEATURES_CRASH"):
            full_env.pop(k, None)
        full_env.update(env or {})
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=full_env)
        self.proc = p
        res = {}
        doc = None
        if json_mode and p.stdout.strip():
            doc = json.loads(p.stdout.decode("utf-8"))
            for r in doc["results"]:
                key = r["id"] + ((" [%s]" % r["mode"]) if r["mode"] else "")
                res[key] = (r["state"], r["message"])
        self.doc = doc
        self.rc = p.returncode
        self.total = p.stderr.decode("utf-8").strip().splitlines()[-1] if json_mode and p.stderr.strip() else \
            p.stdout.decode("utf-8").strip().splitlines()[-1] if p.stdout.strip() else ""
        return res

    def state(self, res, key):
        self.assertIn(key, res, "missing result %r in %r" % (key, sorted(res)))
        return res[key][0]


def hdr(*lines):
    return "\n".join("// " + l for l in lines) + "\n"


# ----------------------------------------------------------------------------------------------
# Pure functions
# ----------------------------------------------------------------------------------------------

class PureTests(unittest.TestCase):
    def test_greeting_bytes(self):
        exp = axtest.decode_escapes(GREETING_ESC)
        self.assertEqual(len(exp), 23)
        self.assertEqual(exp, GREETING.encode("utf-8") + b"\n")
        self.assertEqual(len(GREETING.encode("utf-8")), 22)
        self.assertEqual(exp, b"Xin ch\xc3\xa0o th\xe1\xba\xbf gi\xe1\xbb\x9bi\n")

    def test_escapes(self):
        self.assertEqual(axtest.decode_escapes("a\\tb\\r\\n\\0\\\\"), b"a\tb\r\n\x00\\")
        self.assertEqual(axtest.decode_escapes("\\xff\\xfe"), b"\xff\xfe")
        self.assertEqual(axtest.decode_escapes("\\u{1F600}\\u{e0}"), "\U0001F600à".encode("utf-8"))
        for bad in ("\\q", "\\x1", "\\xzz", "\\u{D800}", "\\u{110000}", "\\u1234", "abc\\"):
            with self.assertRaises(ValueError, msg=bad):
                axtest.decode_escapes(bad)

    def test_ice_banner_pattern(self):
        m = axtest.ICE_BANNER_RE.search
        self.assertTrue(m(b"internal compiler error: x\n"))
        self.assertTrue(m(b"error: internal compiler error: x\n"))
        self.assertTrue(m(b"Error: Internal Compiler Error\n"))
        self.assertTrue(m(b"some output\ninternal compiler error at y\n"))
        self.assertFalse(m(b"the program printed an internal compiler error\n"))   # not at line start
        self.assertFalse(m(b"warning: internal compiler error\n"))
        self.assertFalse(m(b"exit code 3\n"))
        self.assertFalse(m(b""))

    def test_byte_diff_has_hex(self):
        msg = axtest.byte_diff(b"ab\n", b"ab\r\n", "stdout")
        self.assertIn("differs at byte 2", msg)
        self.assertIn("0a", msg)
        self.assertIn("0d 0a", msg)

    def test_native_path_converts_msys_paths_on_windows(self):
        if os.name == "nt":
            self.assertEqual(axtest.native_path("/d/projects/a b/axiom0.exe"), "D:/projects/a b/axiom0.exe")
            self.assertEqual(axtest.native_path("/c"), "C:/")
            self.assertEqual(axtest.native_path("build/axiom0.exe"), "build/axiom0.exe")
            self.assertEqual(axtest.native_path("D:\\x\\y.exe"), "D:\\x\\y.exe")
            self.assertEqual(axtest.native_path("/dev/null"), "/dev/null")
        else:
            self.assertEqual(axtest.native_path("/d/x"), "/d/x")

    def test_crash_status(self):
        self.assertTrue(axtest.is_crash_status(0xC0000005))
        self.assertTrue(axtest.is_crash_status(-11))
        self.assertFalse(axtest.is_crash_status(3))
        self.assertFalse(axtest.is_crash_status(0))
        self.assertFalse(axtest.is_crash_status(None))

    def test_annotation_parsing(self):
        errs = []
        src = (b"fn f() {\n"
               b"    a  //~ ERROR AX_A\n"
               b"    b\n"
               b"    //~^ WARN AX_B\n"
               b"    c  //~? ERROR AX_C\n"
               b"    d //~^^ ERROR AX_D\n")
        got = axtest.collect_annotations(src, None, errs)
        self.assertEqual(errs, [])
        self.assertEqual(got, [(None, "error", "AX_A", 2), (None, "warning", "AX_B", 3),
                               (None, "error", "AX_C", None), (None, "error", "AX_D", 4)])
        errs = []
        axtest.collect_annotations(b"x //~ ERR AX_A\n", None, errs)
        self.assertEqual(len(errs), 1)


# ----------------------------------------------------------------------------------------------
# Kind run
# ----------------------------------------------------------------------------------------------

class RunTests(Case):
    def test_greeting_exact_both_modes(self):
        self.put("run/greet.ax", hdr("test: run", "stdout: " + GREETING_ESC) + "//@ out " + GREETING_ESC + "\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/greet.ax [interp]"), "PASS")
        self.assertEqual(self.state(res, "run/greet.ax [native]"), "PASS")
        self.assertEqual(self.total, "TOTAL 2 PASS 2 FAIL 0 SKIP 0 XFAIL 0")
        self.assertEqual(self.rc, 0)

    def test_crlf_variant_fails_with_hex(self):
        self.put("run/crlf.ax", hdr("test: run", "stdout: " + GREETING_ESC) +
                 "//@ out Xin chào thế giới\\r\\n\n")
        res = self.run_axtest()
        for mode in ("interp", "native"):
            st, msg = res["run/crlf.ax [%s]" % mode]
            self.assertEqual(st, "FAIL")
            self.assertIn("differs at byte 22", msg)
            self.assertIn("0d 0a", msg)
        self.assertEqual(self.rc, 1)
        self.assertEqual(self.total, "TOTAL 2 PASS 0 FAIL 2 SKIP 0 XFAIL 0")

    def test_one_wrong_utf8_byte_fails(self):
        # a-grave is c3 a0; the program writes c3 a1 (a-acute)
        self.put("run/bad.ax", hdr("test: run", "stdout: " + GREETING_ESC) +
                 "//@ out Xin ch\\xc3\\xa1o th\\xe1\\xba\\xbf gi\\xe1\\xbb\\x9bi\\n\n")
        res = self.run_axtest()
        st, msg = res["run/bad.ax [interp]"]
        self.assertEqual(st, "FAIL")
        self.assertIn("differs at byte 7", msg)
        self.assertEqual(self.state(res, "run/bad.ax [native]"), "FAIL")

    def test_args_env_stdin_reach_the_program(self):
        self.put("run/io.ax",
                 hdr("test: run", "args: xin chào 'a b'", "env: AX_T=giá trị", "stdin: dữ liệu\\n",
                     "stdout: args=xin|chào|a b\\nAX_T=giá trị\\ndữ liệu\\n") +
                 "//@ echo-args\n//@ echo-env AX_T\n//@ echo-stdin\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/io.ax [interp]"), "PASS", res)
        self.assertEqual(self.state(res, "run/io.ax [native]"), "PASS", res)

    def test_flags_target_std_root_reach_the_compiler(self):
        self.put("run/fl.ax", hdr("test: run", "flags: -Zx -Zy", "target: x86_64-windows",
                                  "stdout: flags=--std-root mystd --target x86_64-windows -Zx -Zy\\n") +
                 "//@ echo-flags\n")
        res = self.run_axtest("--std-root", "mystd")
        self.assertEqual(self.state(res, "run/fl.ax [interp]"), "PASS", res)
        self.assertEqual(self.state(res, "run/fl.ax [native]"), "PASS", res)

    def test_default_std_root_only_when_directory_exists(self):
        self.put("run/s.ax", hdr("test: run", "stdout: flags=\\n") + "//@ echo-flags\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/s.ax [interp]"), "PASS", res)
        (self.root / "std").mkdir()
        self.put("run/s.ax", hdr("test: run", "stdout: flags=--std-root std\\n") + "//@ echo-flags\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/s.ax [interp]"), "PASS", res)
        self.assertEqual(self.state(res, "run/s.ax [native]"), "PASS", res)

    def test_exit_code_and_stderr_directives(self):
        self.put("run/e.ax", hdr("test: run", "exit: 42", "stderr: panic: lỗi\\n", "stdout-contains: ok") +
                 "//@ out all ok here\n//@ err panic: lỗi\\n\n//@ exit 42\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/e.ax [interp]"), "PASS", res)
        self.assertEqual(self.state(res, "run/e.ax [native]"), "PASS", res)
        self.put("run/e2.ax", hdr("test: run", "stderr-contains: absent text") + "//@ err something else\n")
        res = self.run_axtest("e2")
        self.assertEqual(self.state(res, "run/e2.ax [interp]"), "FAIL")

    def test_wrong_exit_code_fails(self):
        self.put("run/w.ax", hdr("test: run", "exit: 1") + "//@ exit 2\n")
        res = self.run_axtest()
        st, msg = res["run/w.ax [interp]"]
        self.assertEqual(st, "FAIL")
        self.assertIn("exit code 2, expected 1", msg)

    def test_compile_failure_in_run_test_is_fail(self):
        self.put("run/cf.ax", hdr("test: run") + "//@ compile-exit 1\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/cf.ax [native]"), "FAIL")
        self.assertIn("build failed", res["run/cf.ax [native]"][1])
        self.assertEqual(self.state(res, "run/cf.ax [interp]"), "FAIL")

    def test_modes_directive_restricts(self):
        self.put("run/m.ax", hdr("test: run", "modes: interp") + "\n")
        res = self.run_axtest()
        self.assertEqual(sorted(res), ["run/m.ax [interp]"])

    def test_native_after_skips_native_only(self):
        self.put("run/na.ax", hdr("test: run", "native-after: T033", "stdout: mode=interp\\n") +
                 "//@ echo-mode\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/na.ax [interp]"), "PASS")
        st, msg = res["run/na.ax [native]"]
        self.assertEqual(st, "SKIP")
        self.assertEqual(msg, "native after T033")
        self.assertEqual(self.rc, 0)
        self.assertEqual(self.total, "TOTAL 2 PASS 1 FAIL 0 SKIP 1 XFAIL 0")

    def test_list_directive_native_after(self):
        self.put("run/a.ax", hdr("test: run", "native-after: T033") + "\n")
        self.put("run/b.ax", hdr("test: run", "native-after: T037") + "\n")
        self.put("run/c.ax", hdr("test: run") + "\n")
        out = self.run_axtest("--list-directive", "native-after:T033", json_mode=False)
        self.assertEqual(self.proc.stdout.decode().split(), ["run/a.ax"])
        self.run_axtest("--list-directive", "native-after", json_mode=False)
        self.assertEqual(self.proc.stdout.decode().split(), ["run/a.ax", "run/b.ax"])

    def test_invalid_native_after_is_fail(self):
        self.put("run/x.ax", hdr("test: run", "native-after: soon") + "\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/x.ax [directives]"), "FAIL")

    def test_skip_unless_missing_tool(self):
        self.put("run/t.ax", hdr("test: run", "skip-unless: tool definitely-missing-tool") + "\n")
        res = self.run_axtest()
        for mode in ("interp", "native"):
            st, msg = res["run/t.ax [%s]" % mode]
            self.assertEqual(st, "SKIP")
            self.assertIn("definitely-missing-tool", msg)
        self.assertEqual(self.rc, 0)

    def test_skip_unless_tool_present_and_feature(self):
        self.put("run/t.ax", hdr("test: run", "skip-unless: tool python", "modes: interp") + "\n")
        if shutil.which("python") is None:
            self.skipTest("no python on PATH")
        self.assertEqual(self.state(self.run_axtest(), "run/t.ax [interp]"), "PASS")
        self.put("run/f.ax", hdr("test: run", "skip-unless: feature native", "modes: interp") + "\n")
        res = self.run_axtest("run/f", env={"STUB_FEATURES": "interp"})
        self.assertEqual(self.state(res, "run/f.ax [interp]"), "SKIP")

    def test_requires_and_exclude_requires(self):
        self.put("run/r.ax", hdr("test: run", "requires: axiom0-internal", "modes: interp") + "\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/r.ax [interp]"), "PASS")
        res = self.run_axtest("--exclude-requires", "axiom0-internal")
        st, msg = res["run/r.ax [interp]"]
        self.assertEqual(st, "SKIP")
        self.assertIn("axiom0-internal", msg)
        res = self.run_axtest("--exclude-requires", "something-else")
        self.assertEqual(self.state(res, "run/r.ax [interp]"), "PASS")

    def test_no_features_command_skips_run_modes(self):
        self.put("run/n.ax", hdr("test: run") + "\n")
        for env in ({"STUB_NO_FEATURES_CMD": "1"}, {"STUB_FEATURES_CRASH": "1"}, {"STUB_FEATURES": ""}):
            res = self.run_axtest(env=env)
            for mode in ("interp", "native"):
                st, msg = res["run/n.ax [%s]" % mode]
                self.assertEqual(st, "SKIP", env)
                self.assertIn("mode unavailable", msg)
            self.assertEqual(self.rc, 0)

    def test_missing_compiler_skips_run_modes_and_fails_ui(self):
        self.put("run/n.ax", hdr("test: run") + "\n")
        self.put("ui/u.ax", hdr("test: ui") + "\n")
        res = self.run_axtest(compiler=self.root / "no-such-compiler.exe")
        self.assertEqual(self.state(res, "run/n.ax [interp]"), "SKIP")
        self.assertEqual(self.state(res, "ui/u.ax"), "FAIL")
        self.assertEqual(self.rc, 1)

    def test_opt_feature_adds_native_o1(self):
        self.put("run/o.ax", hdr("test: run", "stdout: opt\\n") + "//@ out-if -O1 opt\\n\n")
        res = self.run_axtest(env={"STUB_FEATURES": "interp,native,opt"})
        self.assertEqual(self.state(res, "run/o.ax [native-O1]"), "PASS")
        self.assertEqual(self.state(res, "run/o.ax [native]"), "FAIL")   # -O0 does not print it
        res = self.run_axtest()
        self.assertNotIn("run/o.ax [native-O1]", res)


# ----------------------------------------------------------------------------------------------
# States: xfail / crash / timeout
# ----------------------------------------------------------------------------------------------

class StateTests(Case):
    def test_xfail_failing_is_xfail_passing_is_xpass(self):
        self.put("run/xf.ax", hdr("test: run", "xfail: T123 spec gap", "exit: 1", "modes: interp") + "//@ exit 2\n")
        res = self.run_axtest()
        st, msg = res["run/xf.ax [interp]"]
        self.assertEqual(st, "XFAIL")
        self.assertIn("T123", msg)
        self.assertEqual(self.rc, 0)
        self.assertEqual(self.total, "TOTAL 1 PASS 0 FAIL 0 SKIP 0 XFAIL 1")
        self.put("run/xf.ax", hdr("test: run", "xfail: T123 spec gap", "exit: 2", "modes: interp") + "//@ exit 2\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/xf.ax [interp]"), "XPASS")
        self.assertEqual(self.rc, 1)
        self.assertEqual(self.total, "TOTAL 1 PASS 0 FAIL 1 SKIP 0 XFAIL 0")
        self.assertEqual(self.doc["counts"]["xpass"], 1)

    def test_xfail_needs_task_and_reason(self):
        self.put("run/xf.ax", hdr("test: run", "xfail: T123") + "\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/xf.ax [directives]"), "FAIL")
        self.put("run/xf.ax", hdr("test: run", "xfail: because") + "\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/xf.ax [directives]"), "FAIL")

    def test_xfail_does_not_hide_a_crash(self):
        self.put("run/xc.ax", hdr("test: run", "xfail: T123 gap", "modes: interp") + "//@ crash\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/xc.ax [interp]"), "CRASH")

    def test_crash_by_ice_banner_exit_3(self):
        self.put("run/c.ax", hdr("test: run") + "//@ ice\n")
        res = self.run_axtest()
        for mode in ("interp", "native"):
            st, msg = res["run/c.ax [%s]" % mode]
            self.assertEqual(st, "CRASH", msg)
            self.assertIn("internal compiler error", msg)
        self.assertEqual(self.rc, 1)
        self.assertEqual(self.doc["counts"]["crash"], 2)
        self.assertEqual(self.total, "TOTAL 2 PASS 0 FAIL 2 SKIP 0 XFAIL 0")

    def test_crash_by_banner_with_other_exit_code(self):
        # AXS-SEM-082: detected by the banner, not by exit code 3 alone
        self.put("run/c1.ax", hdr("test: run") + "//@ ice\n//@ compile-exit 1\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/c1.ax [interp]"), "CRASH")
        self.assertEqual(self.state(res, "run/c1.ax [native]"), "CRASH")

    def test_program_exit_3_without_banner_is_not_a_crash(self):
        self.put("run/p3.ax", hdr("test: run", "exit: 3") + "//@ exit 3\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/p3.ax [interp]"), "PASS")
        self.assertEqual(self.state(res, "run/p3.ax [native]"), "PASS")
        # and when it is not expected, it is a plain FAIL
        self.put("run/p3.ax", hdr("test: run") + "//@ exit 3\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/p3.ax [interp]"), "FAIL")
        self.assertEqual(self.state(res, "run/p3.ax [native]"), "FAIL")

    def test_banner_only_counts_on_compiler_stderr_lines_start(self):
        self.put("run/b.ax", hdr("test: run", "stderr: the internal compiler error is a phrase\\n") +
                 "//@ err the internal compiler error is a phrase\\n\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/b.ax [interp]"), "PASS")

    def test_program_crash_status_is_crash(self):
        self.put("run/pc.ax", hdr("test: run") + "//@ crash\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/pc.ax [interp]"), "CRASH")
        self.assertEqual(self.state(res, "run/pc.ax [native]"), "CRASH")

    def test_timeout(self):
        self.put("run/to.ax", hdr("test: run", "timeout: 1") + "//@ sleep 8\n")
        t0 = time.time()
        res = self.run_axtest("--timeout-scale", "0.3")
        self.assertLess(time.time() - t0, 6)
        self.assertEqual(self.state(res, "run/to.ax [interp]"), "TIMEOUT")
        self.assertEqual(self.state(res, "run/to.ax [native]"), "TIMEOUT")
        self.assertEqual(self.rc, 1)
        self.assertEqual(self.doc["counts"]["timeout"], 2)
        self.assertEqual(self.total, "TOTAL 2 PASS 0 FAIL 2 SKIP 0 XFAIL 0")

    def test_interp_limit_exit_124_with_diagnostic_is_timeout(self):
        self.put("run/lim.ax", hdr("test: run") + "//@ limit\n")
        res = self.run_axtest()
        st, msg = res["run/lim.ax [interp]"]
        self.assertEqual(st, "TIMEOUT", msg)
        self.assertIn("limit", msg)
        self.assertEqual(self.state(res, "run/lim.ax [native]"), "PASS")   # native has no step limit
        self.assertEqual(self.rc, 1)

    def test_exit_124_without_limit_diagnostic_is_plain_fail(self):
        self.put("run/e124.ax", hdr("test: run", "modes: interp") + "//@ exit 124\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/e124.ax [interp]"), "FAIL")

    def test_limit_test_that_expects_124_passes(self):
        self.put("run/lim2.ax", hdr("test: run", "exit: 124", "modes: interp", "stderr-contains: AX_DRIVER_INTERP_") +
                 "//@ limit\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/lim2.ax [interp]"), "PASS")


# ----------------------------------------------------------------------------------------------
# Kind ui
# ----------------------------------------------------------------------------------------------

class UiTests(Case):
    def test_ui_pass_with_error_warning_and_caret(self):
        # lines: 1 header, 2-3 stub diagnostics, 4 fn, 5 return (annotated), 6 let (caret target), 7 caret
        self.put("ui/ok.ax", hdr("test: ui") +
                 "//@ diag AX_TYPE_MISMATCH error 5\n//@ diag AX_UNUSED warning 6\n"
                 "fn main() -> i32 {\n"
                 "    return true          //~ ERROR AX_TYPE_MISMATCH\n"
                 "    let x = 1\n"
                 "    //~^ WARN AX_UNUSED\n"
                 "}\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "ui/ok.ax"), "PASS", res)
        self.assertEqual(self.rc, 0)

    def test_ui_no_diagnostics_expected_and_none_produced(self):
        self.put("ui/clean.ax", hdr("test: ui") + "fn main() -> i32 { return 0 }\n")
        self.assertEqual(self.state(self.run_axtest(), "ui/clean.ax"), "PASS")

    def test_ui_unexpected_diagnostic_fails(self):
        self.put("ui/u.ax", hdr("test: ui") + "//@ diag AX_X error 3\nfn main() {}\n")
        res = self.run_axtest()
        st, msg = res["ui/u.ax"]
        self.assertEqual(st, "FAIL")
        self.assertIn("unexpected diagnostics: ERROR AX_X at line 3", msg)

    def test_ui_missing_diagnostic_fails(self):
        self.put("ui/m.ax", hdr("test: ui") + "fn main() {}  //~ ERROR AX_NOPE\n")
        res = self.run_axtest()
        st, msg = res["ui/m.ax"]
        self.assertEqual(st, "FAIL")
        self.assertIn("missing diagnostics: ERROR AX_NOPE at line 2", msg)

    def test_ui_wrong_line_and_wrong_severity_fail(self):
        self.put("ui/l.ax", hdr("test: ui") + "//@ diag AX_X error 3\nfn main() {}\n//~ ERROR AX_X\n")
        self.assertEqual(self.state(self.run_axtest(), "ui/l.ax"), "FAIL")
        self.put("ui/l.ax", hdr("test: ui") + "//@ diag AX_X warning 3\nfn main() {} //~ ERROR AX_X\n")
        self.assertEqual(self.state(self.run_axtest(), "ui/l.ax"), "FAIL")

    def test_ui_diagnostic_without_position(self):
        self.put("ui/np.ax", hdr("test: ui") + "//@ diag-noprimary AX_LINK_X error\n//~? ERROR AX_LINK_X\n")
        self.assertEqual(self.state(self.run_axtest(), "ui/np.ax"), "PASS")
        self.put("ui/np.ax", hdr("test: ui") + "//@ diag-noprimary AX_LINK_X error\n")
        self.assertEqual(self.state(self.run_axtest(), "ui/np.ax"), "FAIL")

    def test_ui_malformed_annotation_is_fail(self):
        self.put("ui/bad.ax", hdr("test: ui") + "x  //~ ERR AX_A\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "ui/bad.ax [directives]"), "FAIL")
        self.assertIn("malformed annotation", res["ui/bad.ax [directives]"][1])

    def test_ui_duplicate_diagnostics_are_counted(self):
        self.put("ui/d.ax", hdr("test: ui") + "//@ diag AX_X error 4\n//@ diag AX_X error 4\nx //~ ERROR AX_X\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "ui/d.ax"), "FAIL")   # two produced, one annotated

    def test_ui_ice_is_crash(self):
        self.put("ui/ice.ax", hdr("test: ui") + "//@ ice\n")
        self.assertEqual(self.state(self.run_axtest(), "ui/ice.ax"), "CRASH")


# ----------------------------------------------------------------------------------------------
# Kind golden
# ----------------------------------------------------------------------------------------------

class GoldenTests(Case):
    def test_golden_siblings_by_extension(self):
        self.put("lex/a.ax", hdr("test: golden") + "//@ emit tokens TOK1\\n\n//@ emit ast AST1\\n\n//@ emit zzz Z\\n\n")
        self.put("lex/a.tokens", "TOK1\n")
        self.put("lex/a.ast", "AST1\n")
        self.put("lex/a.zzz", "Z\n")        # a new emitter name needs no runner edit
        res = self.run_axtest()
        for e in ("tokens", "ast", "zzz"):
            self.assertEqual(self.state(res, "lex/a.ax [%s]" % e), "PASS", res)

    def test_golden_mismatch_and_crlf(self):
        self.put("lex/b.ax", hdr("test: golden") + "//@ emit tokens TOK1\\n\n")
        self.put("lex/b.tokens", b"TOK1\r\n")
        res = self.run_axtest()
        st, msg = res["lex/b.ax [tokens]"]
        self.assertEqual(st, "FAIL")
        self.assertIn("0d 0a", msg)

    def test_golden_without_golden_file_fails(self):
        self.put("lex/c.ax", hdr("test: golden") + "//@ emit tokens T\n")
        self.assertEqual(self.run_axtest()["lex/c.ax"][0], "FAIL")

    def test_bless_updates_and_creates(self):
        self.put("lex/d.ax", hdr("test: golden", "emit: ast") + "//@ emit tokens NEW\\n\n//@ emit ast AST\\n\n")
        self.put("lex/d.tokens", "OLD\n")
        self.put("run/other.ax", hdr("test: run") + "//@ exit 5\n")      # not touched by --bless
        res = self.run_axtest("--bless", "lex/")
        self.assertEqual((self.tests / "lex/d.tokens").read_bytes(), b"NEW\n")
        self.assertEqual((self.tests / "lex/d.ast").read_bytes(), b"AST\n")
        self.assertNotIn("run/other.ax [interp]", res)
        self.assertEqual(self.rc, 0)
        res = self.run_axtest()
        self.assertEqual(self.state(res, "lex/d.ax [tokens]"), "PASS")
        self.assertEqual(self.state(res, "lex/d.ax [ast]"), "PASS")

    def test_golden_inspect_failure_does_not_bless(self):
        self.put("lex/e.ax", hdr("test: golden") + "//@ emit tokens X\n//@ compile-exit 1\n")
        self.put("lex/e.tokens", "KEEP\n")
        self.run_axtest("--bless")
        self.assertEqual((self.tests / "lex/e.tokens").read_bytes(), b"KEEP\n")
        self.assertEqual(self.rc, 1)


# ----------------------------------------------------------------------------------------------
# Kind diff
# ----------------------------------------------------------------------------------------------

class DiffTests(Case):
    def test_diff_agree_and_disagree(self):
        self.put("diff/ok.ax", hdr("test: diff") + "//@ out same\\n\n")
        self.put("diff/bad.ax", hdr("test: diff") + "//@ out same\\n\n//@ out-if -O1 different\\n\n")
        res = self.run_axtest(env={"STUB_FEATURES": "interp,native,opt"})
        self.assertEqual(self.state(res, "diff/ok.ax [diff]"), "PASS", res)
        st, msg = res["diff/bad.ax [diff]"]
        self.assertEqual(st, "FAIL")
        self.assertIn("native-O1", msg)

    def test_diff_without_optimizer_compares_interp_and_o0(self):
        self.put("diff/bad.ax", hdr("test: diff") + "//@ out same\\n\n//@ out-if -O1 different\\n\n")
        res = self.run_axtest()          # no `opt` feature: -O1 variant not run
        self.assertEqual(self.state(res, "diff/bad.ax [diff]"), "PASS")
        self.put("diff/nat.ax", hdr("test: diff") + "//@ out-if native X\\n\n")
        res = self.run_axtest("diff/nat")
        self.assertEqual(self.state(res, "diff/nat.ax [diff]"), "FAIL")

    def test_diff_skipped_with_one_executor(self):
        self.put("diff/one.ax", hdr("test: diff") + "\n")
        res = self.run_axtest(env={"STUB_FEATURES": "interp"})
        self.assertEqual(self.state(res, "diff/one.ax [diff]"), "SKIP")
        self.put("diff/na.ax", hdr("test: diff", "native-after: T033") + "\n")
        res = self.run_axtest("diff/na")
        self.assertEqual(self.state(res, "diff/na.ax [diff]"), "SKIP")


# ----------------------------------------------------------------------------------------------
# Kind exec, projects, discovery
# ----------------------------------------------------------------------------------------------

class ExecProjectTests(Case):
    def test_exec_manifest(self):
        self.put("unit/ver.test", "# comment\ncmd: python {compiler} version\nexit: 0\nstdout: stubcc 0\\n\n")
        self.put("unit/bad.test", "cmd: python {compiler} version\nstdout: nope\\n\n")
        self.put("unit/code.test", "cmd: python {compiler} nosuchcommand\nexit: 2\nstderr-contains: unknown command\n")
        self.put("unit/build.test", "cmd: python {build}/stubcc.py version\nstdout-contains: stubcc\n")
        self.put("unit/tool.test", "skip-unless: tool definitely-missing-tool\ncmd: definitely-missing-tool\n")
        self.put("unit/req.test", "requires: axiom0-internal\ncmd: python {compiler} version\n")
        self.put("unit/tmp.test", "cmd: python {compiler} build -o {tmp}/x.py {test_dir}/ver.test\n")
        res = self.run_axtest("--exclude-requires", "axiom0-internal")
        self.assertEqual(self.state(res, "unit/ver.test"), "PASS", res)
        self.assertEqual(self.state(res, "unit/bad.test"), "FAIL")
        self.assertEqual(self.state(res, "unit/code.test"), "PASS", res)
        self.assertEqual(self.state(res, "unit/build.test"), "PASS", res)
        self.assertEqual(self.state(res, "unit/tool.test"), "SKIP")
        self.assertEqual(self.state(res, "unit/req.test"), "SKIP")
        # {tmp} and {test_dir} expand (the stub exits 1 on this non-source input only if it cannot read it)
        self.assertEqual(self.state(res, "unit/tmp.test"), "PASS", res)   # {tmp} and {test_dir} expand

    def test_exec_manifest_errors(self):
        self.put("unit/nocmd.test", "exit: 0\n")
        self.put("unit/unk.test", "cmd: python {nonsense} x\n")
        self.put("unit/typo.test", "cdm: python x\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "unit/nocmd.test [directives]"), "FAIL")
        self.assertEqual(self.state(res, "unit/unk.test"), "FAIL")
        self.assertIn("unknown placeholder", res["unit/unk.test"][1])
        self.assertEqual(self.state(res, "unit/typo.test [directives]"), "FAIL")

    def test_exec_crash_status(self):
        self.put("unit/crash.test", "cmd: python -c \"import os; os._exit(0xC0000005 - (1 << 32))\"\n" if os.name == "nt" else
                 "cmd: python -c \"import os,signal; os.kill(os.getpid(), signal.SIGSEGV)\"\n")
        self.assertEqual(self.state(self.run_axtest(), "unit/crash.test"), "CRASH")

    def test_project_directory_is_one_test(self):
        p = "modules/proj"
        self.put(p + "/axiom.toml", "[package]\nname = \"proj\"\n")
        self.put(p + "/src/main.ax", hdr("test: run", "stdout: projekt\\n") + "//@ out projekt\\n\n")
        self.put(p + "/src/util.ax", "fn helper() {}\n")           # not discovered separately
        self.put(p + "/tests/inner.ax", hdr("test: run") + "//@ exit 9\n")   # inside a project: ignored
        res = self.run_axtest()
        self.assertEqual(sorted(res), ["modules/proj [interp]", "modules/proj [native]"])
        self.assertEqual(self.state(res, "modules/proj [interp]"), "PASS", res)
        self.assertEqual(self.state(res, "modules/proj [native]"), "PASS", res)

    def test_project_ui_and_missing_main(self):
        self.put("modules/pu/axiom.toml", "")
        self.put("modules/pu/src/main.ax", hdr("test: ui") + "//@ diag AX_X error 3 src/main.ax\nfn main() {} //~ ERROR AX_X\n")
        self.put("modules/pu/src/util.ax", "fn f() {}\n")
        self.put("modules/empty/axiom.toml", "")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "modules/pu"), "PASS", res)
        self.assertEqual(self.state(res, "modules/empty [directives]"), "FAIL")

    def test_discovery_rules(self):
        self.put("run/nodirective.ax", "fn main() {}\n")
        self.put("run/helper.ax", hdr("test: helper") + "fn h() {}\n")
        self.put("run/fixtures/f.ax", "binary-ish\n")
        self.put("run/dup.ax", hdr("test: run", "exit: 1", "exit: 2") + "\n")
        self.put("run/kind.ax", hdr("test: bogus") + "\n")
        self.put("run/note.ax", hdr("test: run", "modes: interp", "Note: not a directive", "a: b") + "\n")
        res = self.run_axtest()
        self.assertEqual(self.state(res, "run/nodirective.ax [directives]"), "FAIL")
        self.assertIn("missing `// test:", res["run/nodirective.ax [directives]"][1])
        self.assertFalse([k for k in res if "helper" in k or "fixtures" in k])
        self.assertEqual(self.state(res, "run/dup.ax [directives]"), "FAIL")
        self.assertEqual(self.state(res, "run/kind.ax [directives]"), "FAIL")
        self.assertEqual(self.state(res, "run/note.ax [interp]"), "PASS")

    def test_filter_and_positional_filter(self):
        self.put("run/aa.ax", hdr("test: run", "modes: interp") + "\n")
        self.put("run/bb.ax", hdr("test: run", "modes: interp") + "\n")
        self.assertEqual(sorted(self.run_axtest("--filter", "aa")), ["run/aa.ax [interp]"])
        self.assertEqual(sorted(self.run_axtest("bb")), ["run/bb.ax [interp]"])
        self.assertEqual(sorted(self.run_axtest("--filter", "aa", "--filter", "bb")),
                         ["run/aa.ax [interp]", "run/bb.ax [interp]"])
        res = self.run_axtest("nothing-matches")
        self.assertEqual(res, {})
        self.assertEqual(self.total, "TOTAL 0 PASS 0 FAIL 0 SKIP 0 XFAIL 0")
        self.assertEqual(self.rc, 0)


# ----------------------------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------------------------

class OutputTests(Case):
    def test_text_output_ends_with_total_line(self):
        self.put("run/a.ax", hdr("test: run", "modes: interp") + "\n")
        self.put("run/b.ax", hdr("test: run", "modes: interp", "exit: 1") + "\n")
        self.put("run/c.ax", hdr("test: run", "modes: interp", "skip-unless: tool definitely-missing-tool") + "\n")
        self.put("run/d.ax", hdr("test: run", "modes: interp", "xfail: T9 gap", "exit: 1") + "\n")
        self.run_axtest(json_mode=False)
        lines = self.proc.stdout.decode("utf-8").splitlines()
        self.assertEqual(lines[-1], "TOTAL 4 PASS 1 FAIL 1 SKIP 1 XFAIL 1")
        self.assertTrue(any(l.startswith("FAIL") and "run/b.ax" in l for l in lines))
        self.assertFalse(any("run/a.ax" in l for l in lines))     # quiet: passes are not listed
        self.assertEqual(self.rc, 1)
        self.run_axtest("--verbose", json_mode=False)
        out = self.proc.stdout.decode("utf-8")
        self.assertIn("PASS    run/a.ax [interp]", out)
        self.assertIn("SKIP    run/c.ax [interp]: tool definitely-missing-tool not found", out)

    def test_json_document(self):
        self.put("run/a.ax", hdr("test: run", "modes: interp") + "\n")
        self.run_axtest()
        self.assertEqual(self.doc["schema"], 1)
        self.assertEqual(self.doc["features"], ["interp", "native"])
        self.assertEqual(self.doc["results"][0]["state"], "PASS")
        self.assertEqual(self.doc["total_line"], self.total)
        self.assertEqual(self.doc["counts"]["total"], 1)

    def test_deterministic_across_job_counts(self):
        for i in range(6):
            self.put("run/t%d.ax" % i, hdr("test: run", "stdout: %d\\n" % i) + "//@ out %d\\n\n" % i)
        self.put("run/zbad.ax", hdr("test: run", "exit: 1") + "\n")
        a = self.run_axtest("-j", "1")
        b = self.run_axtest("-j", "6")
        self.assertEqual(a, b)
        self.assertEqual([r["id"] + r["mode"] for r in self.doc["results"]],
                         sorted(r["id"] + r["mode"] for r in self.doc["results"]))

    def test_list(self):
        self.put("run/a.ax", hdr("test: run") + "\n")
        self.run_axtest("--list", json_mode=False)
        self.assertEqual(self.proc.stdout.decode().split("\n")[:2], ["run/a.ax [interp]", "run/a.ax [native]"])

    def test_cleanup_of_temp_dirs(self):
        before = set(os.listdir(tempfile.gettempdir()))
        self.put("run/a.ax", hdr("test: run") + "\n")
        self.run_axtest()
        leaked = [d for d in set(os.listdir(tempfile.gettempdir())) - before if d.startswith("axtest-") and
                  not d.startswith("axtest-self-")]
        self.assertEqual(leaked, [])


if __name__ == "__main__":
    unittest.main()
