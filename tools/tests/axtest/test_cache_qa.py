"""QA regression tests for the T437a gate (round 0 findings). Python 3 standard library only.

F1  the superset tree digest must see every file the compiler can load: a project test loads every `*.ax` under its
    directory, including dot-prefixed files/directories and `__pycache__/` (false cache HIT otherwise).
F2  every target of tools/affected_map.txt must be tracked by git (an untracked directory of another task's work
    makes `--affected` fail with exit 2 in every snapshot that lacks it).
F3  ADR-0041 S4: OS timer bindings are never cached (host clock intrinsic `monotonic_ns`, FFI `GetTickCount64`,
    `QueryPerformanceCounter`, `GetSystemTime*`).
F4  `--affected` std rule: a change inside an `impl` block derives the implemented type's name (git's hunk header
    is the `impl ... {` line, which is not a `pub` item).
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import axtest_cache  # noqa: E402
import axtest_affected  # noqa: E402


class TreeDigestSeesCompilerInputs(unittest.TestCase):
    def check_added(self, rel):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "src").mkdir()
            (base / "src" / "main.ax").write_bytes(b"fn main() {}\n")
            before = axtest_cache.Hasher().tree(base)
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"fn broken( {\n")
            after = axtest_cache.Hasher().tree(base)
            self.assertNotEqual(before, after, "tree digest ignores %s, which the compiler loads" % rel)

    def test_dot_file(self):
        self.check_added("src/.evil.ax")

    def test_dot_directory(self):
        self.check_added("src/.hidden/x.ax")

    def test_pycache_directory(self):
        self.check_added("src/__pycache__/x.ax")


class AffectedMapTargetsTracked(unittest.TestCase):
    def test_targets_are_tracked(self):
        rows, problems = axtest_affected.read_map(ROOT)
        self.assertFalse(problems, problems)
        r = subprocess.run(["git", "ls-files", "tests"], cwd=str(ROOT), stdout=subprocess.PIPE)
        if r.returncode != 0:
            self.skipTest("not a git checkout")
        tracked = r.stdout.decode("utf-8").splitlines()
        missing = []
        for mod, targets in sorted(rows.items()):
            for t in targets:
                t = t.rstrip("/")
                if not any(f == t or f.startswith(t + "/") for f in tracked):
                    missing.append("%s -> %s" % (mod, t))
        self.assertEqual(missing, [], "map targets not tracked by git")


class TimerBindingsNeverCached(unittest.TestCase):
    def reason(self, src):
        return axtest_cache.StdIndex(None).nondet_reason([src])

    def test_host_monotonic_clock(self):
        self.assertIsNotNone(self.reason("use std.core.host.monotonic_ns;\nfn main() { let t = monotonic_ns(); }\n"))

    def test_ffi_tick_count(self):
        self.assertIsNotNone(self.reason('extern "C" {\n    fn GetTickCount64() -> u64;\n}\n'))

    def test_ffi_performance_counter(self):
        self.assertIsNotNone(self.reason('extern "C" {\n    fn QueryPerformanceCounter(p: *mut i64) -> i32;\n}\n'))


class ImplBodyChangeNamesType(unittest.TestCase):
    def test_impl_hunk_header(self):
        diff = ("--- a/std/core/prelude.ax\n+++ b/std/core/prelude.ax\n"
                "@@ -42,7 +42,7 @@ impl<T> Atomic<T> {\n-        loop {}\n+        loop {} // changed\n")
        self.assertIn("Atomic", axtest_affected.public_names(diff, None))

    def test_trait_impl_hunk_header(self):
        diff = ("--- a/std/x.ax\n+++ b/std/x.ax\n"
                "@@ -10,7 +10,7 @@ impl Future for Sleep {\n-    a\n+    b\n")
        self.assertIn("Sleep", axtest_affected.public_names(diff, None))


class ThreadBindingsNeverCached(unittest.TestCase):
    """Round 1 F5: ADR-0041 S4 also names OS *thread* bindings (std/sys/windows/thread.ax, FFI)."""

    def reason(self, src):
        return axtest_cache.StdIndex(ROOT / "std").nondet_reason([src])

    def test_ffi_current_thread_id(self):
        self.assertIsNotNone(self.reason('extern "system" {\n    fn GetCurrentThreadId() -> u32;\n}\n'))

    def test_ffi_create_thread(self):
        self.assertIsNotNone(self.reason('extern "system" {\n    fn CreateThread(a: usize) -> usize;\n}\n'))

    def test_std_sys_thread_module(self):
        self.assertIsNotNone(self.reason("use std.sys.windows.thread.Sleep\nfn main() { Sleep(1); }\n"))


class ContextLineDeclarationNamed(unittest.TestCase):
    """Round 1 F6: when the changed line is the first body line of an item, git's hunk header names the
    PREVIOUS item and the item's own declaration is a context line of the hunk."""

    def test_pub_fn_declared_in_context_line(self):
        file_text = ("pub fn compiler_fence(order: u32) {}\n\n"
                     "pub fn spin_loop_hint() {}\n\n"
                     "pub fn is_lock_free<T>() -> bool {\n    let s = 8;\n    s <= 8\n}\n")
        diff = ("--- a/std/core/prelude.ax\n+++ b/std/core/prelude.ax\n"
                "@@ -3,7 +3,7 @@ pub fn compiler_fence(order: u32) {}\n"
                " pub fn spin_loop_hint() {}\n \n pub fn is_lock_free<T>() -> bool {\n"
                "-    let s = 8;\n+    let s = 8; // changed\n     s <= 8\n }\n")
        self.assertIn("is_lock_free", axtest_affected.derive_names(diff, file_text)[0])

    def test_impl_declared_in_context_line(self):
        file_text = ("pub struct Other {}\n\npub struct Sleep {}\n\nimpl Future for Sleep {\n"
                     "    fn poll(self) -> u32 {\n        1\n    }\n}\n")
        diff = ("--- a/std/x.ax\n+++ b/std/x.ax\n"
                "@@ -3,6 +3,6 @@ pub struct Other {}\n"
                " pub struct Sleep {}\n \n impl Future for Sleep {\n-    fn poll(self) -> u32 {\n"
                "+    fn poll(self) -> u32 { // changed\n         1\n     }\n")
        self.assertIn("Sleep", axtest_affected.derive_names(diff, file_text)[0])


if __name__ == "__main__":
    unittest.main()
