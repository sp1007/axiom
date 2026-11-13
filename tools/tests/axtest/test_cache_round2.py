"""T437a round 2 self-audit of the S4 never-cache classifier (deny by default). Python 3 standard library only.

The classifier must make a test uncacheable whenever it can reach a leaf binding (extern / `@intrinsic` /
`__ax_host_*`) that is not positively classified deterministic -- whatever the binding is called and wherever
it is declared -- and must keep pure tests cacheable.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent.parent
sys.path.insert(0, str(TOOLS))
import axtest_cache  # noqa: E402

HOST = ("module std.core.host\n"
        "@intrinsic\npub fn monotonic_ns() -> u64 {\n    0\n}\n"
        "@intrinsic\npub unsafe fn heap_alloc(size: usize, align: usize) -> *mut u8 {\n    0 as *mut u8\n}\n"
        "@intrinsic pub fn size_of<T>() -> usize { 0 }\n")


class Std:
    def __init__(self, files):
        self.dir = Path(tempfile.mkdtemp(prefix="ax-s4-"))
        self.std = self.dir / "std"
        for rel, text in files.items():
            p = self.std / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        self.index = axtest_cache.StdIndex(self.std)

    def reason(self, src):
        return self.index.nondet_reason([src])

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class DenyByDefault(unittest.TestCase):
    def setUp(self):
        self.s = Std({
            "core/host.ax": HOST,
            # re-export only (no call) of a nondeterministic intrinsic, in a non-sys module, under another name
            "x/clock.ax": "module std.x.clock\npub use std.core.host.monotonic_ns as now\n",
            # an extern declared in a non-sys std module whose name says nothing about time/threads
            "util/rng.ax": ('module std.util.rng\nextern "system" {\n'
                            "    fn BCryptGenRandom(a: usize, b: *mut u8, n: u32, f: u32) -> i32;\n}\n"
                            "pub fn fill(p: *mut u8, n: u32) -> i32 {\n    BCryptGenRandom(0, p, n, 2)\n}\n"),
            # transitive: std.a -> std.b, and std.b calls a nondeterministic extern
            "a.ax": "module std.a\nuse std.b\npub fn go() -> u64 {\n    std.b.cycles()\n}\n",
            "b.ax": ('module std.b\nextern "C" {\n    fn __rdcycle() -> u64;\n}\n'
                     "pub fn cycles() -> u64 {\n    __rdcycle()\n}\n"),
            # pure module using only deterministic bindings
            "pure/mem.ax": ("module std.pure.mem\nuse std.core.host.heap_alloc\n"
                            "pub fn grab() -> *mut u8 {\n    heap_alloc(8, 8)\n}\n"),
            # binding only inside a comment / string: not a binding
            "doc/text.ax": ('module std.doc.text\n// extern "system" { fn Sleep(ms: u32); }\n'
                            'pub fn s() -> str {\n    "Sleep(1) CreateThread"\n}\n'),
        })

    def tearDown(self):
        self.s.close()

    def test_binding_reached_only_through_reexport_alias(self):
        r = self.s.reason("use std.x.clock.now\nfn main() {\n    let t = now();\n}\n")
        self.assertIsNotNone(r)
        self.assertIn("monotonic_ns", r)

    def test_extern_in_non_sys_module_with_neutral_name(self):
        r = self.s.reason("use std.util.rng\nfn main() {\n    std.util.rng.fill(0 as *mut u8, 4);\n}\n")
        self.assertIsNotNone(r)
        self.assertIn("BCryptGenRandom", r)

    def test_transitive_module_chain(self):
        self.assertIsNotNone(self.s.reason("use std.a\nfn main() {\n    std.a.go();\n}\n"))

    def test_unknown_intrinsic_declared_by_test(self):
        # no time/thread word in the name: only deny-by-default catches it
        r = self.s.reason("@intrinsic fn cpu_cycles() -> u64 { 0 }\nfn main() {\n    cpu_cycles();\n}\n")
        self.assertIsNotNone(r)
        self.assertIn("cpu_cycles", r)

    def test_unknown_ffi_body_less_extern_fn(self):
        self.assertIsNotNone(self.s.reason('extern "C" fn rand() -> i32;\nfn main() {\n    rand();\n}\n'))

    def test_host_provider_called_directly(self):
        self.assertIsNotNone(self.s.reason("fn main() {\n    let id = __ax_host_thread_current_id();\n}\n"))
        self.assertIsNone(self.s.reason("fn main() {\n    let p = __ax_host_heap_alloc(8, 8);\n}\n"))

    def test_attribute_test_spawning_through_std_thread(self):
        src = ("use std.thread\n@test\nfn t() {\n    let h = thread.spawn(|| 1);\n    h.join();\n}\n"
               "#[test]\nfn u() {}\n")
        self.assertIsNotNone(self.s.reason(src))

    def test_pure_test_stays_cacheable(self):
        src = ("use std.pure.mem\n@intrinsic fn size_of<T>() -> usize { 0 }\n"
               "@intrinsic fn wrapping_add_u32(a: u32, b: u32) -> u32 { 0 }\n"
               'extern "system" {\n    fn WriteFile(h: usize, p: *const u8, n: u32, w: *mut u32, o: usize) -> i32;\n'
               "    fn GetStdHandle(n: u32) -> usize;\n}\n"
               "fn main() {\n    let p = std.pure.mem.grab();\n    let n = wrapping_add_u32(1, size_of<u8>() as u32);\n}\n")
        self.assertIsNone(self.s.reason(src))

    def test_module_declaring_but_not_using_nondet_intrinsic_is_not_tainted(self):
        # std.core.host declares monotonic_ns: reaching it for heap_alloc only stays cacheable ...
        self.assertIsNone(self.s.reason("use std.core.host.heap_alloc\nfn main() {\n    heap_alloc(1, 1);\n}\n"))
        # ... calling the nondeterministic one through the module path is not
        self.assertIsNotNone(self.s.reason("use std.core.host\nfn main() {\n    std.core.host.monotonic_ns();\n}\n"))

    def test_binding_text_in_comment_or_string_is_not_a_binding(self):
        self.assertIsNone(self.s.reason("use std.doc.text\nfn main() {\n    std.doc.text.s();\n}\n"))

    def test_exact_dependency_on_tainted_std_file(self):
        root = self.s.dir
        nd = axtest_cache.exact_deps_nondet(["std/util/rng.ax", "std/core/host.ax"], "std", self.s.index, root)
        self.assertIsNotNone(nd)
        self.assertIn("rng.ax", nd)
        self.assertIsNone(axtest_cache.exact_deps_nondet(["std/core/host.ax", "std/pure/mem.ax"], "std",
                                                         self.s.index, root))
        self.assertIsNotNone(axtest_cache.exact_deps_nondet(["std/thread/mod.ax"], "std", self.s.index, root))


class RealStdClassification(unittest.TestCase):
    """The checked-in std: every OS thread/sync/timer/env binding is nondeterministic, heap/IO/layout are not."""

    def test_real_std_bindings(self):
        idx = axtest_cache.StdIndex(TOOLS.parent / "std")
        names = idx.binding_names()
        for n in ("CreateThread", "GetCurrentThreadId", "Sleep", "WaitForSingleObject", "WaitOnAddress",
                  "QueryPerformanceCounter", "monotonic_ns", "env_get", "__ax_host_thread_spawn",
                  "__ax_host_futex_wait"):
            self.assertIn(n, names)
        for n in ("heap_alloc", "WriteFile", "HeapAlloc", "size_of", "wrapping_add_u64"):
            self.assertNotIn(n, names)
        self.assertIsNotNone(idx.nondet_reason(["use std.sys.windows.thread\nfn main() {}\n"]))
        self.assertIsNotNone(idx.nondet_reason(["use std.sys.windows.time\nfn main() {}\n"]))
        self.assertIsNone(idx.nondet_reason(["use std.sys.windows.heap\nfn main() {}\n"]))


if __name__ == "__main__":
    unittest.main()
