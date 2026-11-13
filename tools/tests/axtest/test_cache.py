"""Self-tests of the axtest result cache, durations/longest-first and --baseline (T437a, ADR-0041 §4).

Every test builds a scratch repository root, runs the real runner as a subprocess with the stub compiler
(`stubcc.py`; `STUB_DEP_FILE=1` makes it honour `--dep-file`) and checks which results were reported from the
cache (`"cached": true` in the JSON document) and what was stored. Python 3 standard library only.
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
TOOLS = HERE.parent.parent
AXTEST = TOOLS / "axtest.py"
STUB = HERE / "stubcc.py"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TOOLS))
import axtest_cache  # noqa: E402
from test_axtest import hdr  # noqa: E402

PASS_RUN = hdr("test: run", "modes: interp", "stdout: ok\\n") + "//@ out ok\\n\n"


def run_git(cwd, *args):
    env = dict(os.environ)
    env.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
                "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"})
    r = subprocess.run(["git", *args], cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if r.returncode != 0:
        raise RuntimeError("git %s: %s" % (args, r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8").strip()


class CacheCase(unittest.TestCase):
    root_name = "root with space"

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="axtest-cache-"))
        self.root = self.base / self.root_name
        self.tests = self.root / "tests"
        self.tests.mkdir(parents=True)
        self.cache = self.base / "cache"
        self.axtest = AXTEST
        self.compiler = STUB

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def put(self, rel, content, under=None):
        p = (under or self.tests) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return p

    def ax(self, *args, env=None, cache=True):
        cmd = [sys.executable, str(self.axtest), "--root", str(self.root), "--compiler", str(self.compiler),
               "--exe-suffix", ".py", "--json"]
        if cache:
            cmd += ["--cache-dir", str(self.cache)]
        cmd += list(args)
        full = dict(os.environ)
        for k in list(full):
            if k.startswith("STUB_") or k.startswith("AXIOM") or k.startswith("AX_"):
                full.pop(k)
        full.update(env or {})
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=full)
        self.rc = p.returncode
        self.err = p.stderr.decode("utf-8", "replace")
        self.doc = json.loads(p.stdout.decode("utf-8")) if p.stdout.strip() else None
        res = {}
        if self.doc:
            for r in self.doc["results"]:
                key = r["id"] + ((" [%s]" % r["mode"]) if r["mode"] else "")
                res[key] = (r["state"], r.get("cached", False))
        return res

    def entries(self):
        base = self.cache / "entries"
        return sorted(p for p in base.rglob("*.json")) if base.is_dir() else []

    def assert_all(self, res, state, cached):
        self.assertTrue(res, self.err)
        for k, v in res.items():
            self.assertEqual(v, (state, cached), "%s: %r\n%s" % (k, v, self.err))


class HitMissTests(CacheCase):
    def test_hit_on_identical_inputs(self):
        self.put("run/a.ax", hdr("test: run", "stdout: ok\\n") + "//@ out ok\\n\n")
        res = self.ax()
        self.assert_all(res, "PASS", False)
        self.assertEqual(len(self.entries()), 1)
        res = self.ax()
        self.assert_all(res, "PASS", True)
        self.assertEqual(self.doc["counts"]["cached"], 2)
        self.assertIn("CACHED 2", self.err)
        self.assertEqual(self.rc, 0)

    def test_text_mode_prints_cached_line_and_keeps_total_last(self):
        self.put("run/a.ax", PASS_RUN)
        self.ax()
        cmd = [sys.executable, str(AXTEST), "--root", str(self.root), "--compiler", str(STUB), "--exe-suffix",
               ".py", "--cache-dir", str(self.cache)]
        out = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()
        self.assertTrue(out[-1].startswith("TOTAL 1 PASS 1 FAIL 0"), out)
        self.assertTrue(any(l.startswith("CACHED 1 ") for l in out), out)

    def test_no_cache_runs_fresh(self):
        self.put("run/a.ax", PASS_RUN)
        self.ax()
        res = self.ax("--no-cache")
        self.assert_all(res, "PASS", False)

    def test_miss_after_one_byte_of_the_test(self):
        p = self.put("run/a.ax", PASS_RUN)
        self.ax()
        p.write_bytes(p.read_bytes() + b" ")
        self.assert_all(self.ax(), "PASS", False)
        self.assert_all(self.ax(), "PASS", True)

    def test_miss_after_expectation_file_golden_and_stdout_file(self):
        self.put("parse/g.ax", hdr("test: golden") + "//@ emit ast AST\\n\n")
        g = self.put("parse/g.ast", "AST\n")
        self.put("run/s.ax", hdr("test: run", "modes: interp", "stdout-file: s.stdout") + "//@ out S\\n\n")
        s = self.put("run/s.stdout", "S\n")
        self.ax()
        self.assert_all(self.ax(), "PASS", True)
        g.write_bytes(b"AST\n ")       # one byte more: the cached PASS must not survive
        res = self.ax()
        self.assertEqual(res["parse/g.ax [ast]"], ("FAIL", False))
        self.assertEqual(res["run/s.ax [interp]"], ("PASS", True))
        g.write_bytes(b"AST\n")
        s.write_bytes(b"T\n")
        res = self.ax()
        self.assertEqual(res["run/s.ax [interp]"], ("FAIL", False))

    def test_miss_after_std_file_superset(self):
        self.put("std/core/x.ax", "module std.core.x\n", under=self.root)
        self.put("run/a.ax", PASS_RUN)
        self.put("run/b.ax", PASS_RUN)
        self.ax()
        self.assert_all(self.ax(), "PASS", True)
        self.put("std/core/x.ax", "module std.core.x\n// one more byte\n", under=self.root)
        res = self.ax()
        self.assert_all(res, "PASS", False)
        self.assertEqual(self.doc["cache"]["dep_source"], "superset")
        # a new file anywhere in the std root is also a change of the superset
        self.ax()
        self.put("std/new/y.ax", "module std.new.y\n", under=self.root)
        self.assert_all(self.ax(), "PASS", False)

    def test_superset_includes_test_directory_tree(self):
        self.put("run/a.ax", PASS_RUN)
        self.ax()
        self.put("run/helper_mod.ax", hdr("test: helper") + "fn helper() {}\n")
        self.assert_all(self.ax(), "PASS", False)

    def test_project_test_sees_dot_files_and_pycache(self):
        # QA F1: the compiler loads every *.ax of a project directory, dot-files and __pycache__ included
        self.put("modules/p/axiom.toml", "[package]\nname = \"p\"\n")
        self.put("modules/p/src/main.ax", PASS_RUN)
        self.ax()
        self.assert_all(self.ax(), "PASS", True)
        for i, rel in enumerate(("modules/p/src/.evil.ax", "modules/p/src/.hidden/x.ax",
                                 "modules/p/src/__pycache__/y.ax")):
            self.put(rel, "fn broken( {\n")
            self.assert_all(self.ax(), "PASS", False)
            self.assert_all(self.ax(), "PASS", True)

    def test_exact_deps_miss_on_dep_and_hit_on_unrelated_std(self):
        env = {"STUB_DEP_FILE": "1"}
        self.put("std/core/used.ax", "module std.core.used\n", under=self.root)
        self.put("std/core/other.ax", "module std.core.other\n", under=self.root)
        self.put("run/a.ax", PASS_RUN + "//@ dep std/core/used.ax\n")
        self.assert_all(self.ax(env=env), "PASS", False)
        self.assertEqual(self.doc["cache"]["dep_source"], "exact")
        rec = json.loads(self.entries()[0].read_text(encoding="utf-8"))
        self.assertEqual(rec["dep_source"], "exact")
        self.assertIn("std/core/used.ax", [d[1] for d in rec["deps"]])
        self.assert_all(self.ax(env=env), "PASS", True)
        # a std file the compiler did not load: still a hit (exact list, not the superset)
        self.put("std/core/other.ax", "module std.core.other\n// changed\n", under=self.root)
        self.assert_all(self.ax(env=env), "PASS", True)
        # one byte of a reported dependency: miss
        self.put("std/core/used.ax", "module std.core.used\n ", under=self.root)
        self.assert_all(self.ax(env=env), "PASS", False)
        self.assert_all(self.ax(env=env), "PASS", True)
        # a new file next to a loaded dependency (module resolution may change): miss
        self.put("std/core/used/mod.ax", "module std.core.used\n", under=self.root)
        self.assert_all(self.ax(env=env), "PASS", False)
        # the exact list is indexed per test id for --affected rule 1
        idx = axtest_cache.load_exact_deps_index(self.cache)
        self.assertIn("std/core/used.ax", idx["run/a.ax"])

    def test_dep_file_probe_is_recorded_per_binary(self):
        self.put("run/a.ax", PASS_RUN)
        self.ax(env={"STUB_DEP_FILE": "1"})
        probe = json.loads((self.cache / "probe.json").read_text(encoding="utf-8"))
        self.assertEqual(list(probe.values()), ["exact"])
        other = self.base / "c2"
        self.cache = other
        self.ax()
        probe = json.loads((other / "probe.json").read_text(encoding="utf-8"))
        self.assertEqual(list(probe.values()), ["superset"])

    def test_miss_after_compiler_binary_change(self):
        comp = self.base / "comp" / "stubcc.py"
        comp.parent.mkdir()
        shutil.copy2(STUB, comp)
        self.compiler = comp
        self.put("run/a.ax", PASS_RUN)
        self.ax()
        self.assert_all(self.ax(), "PASS", True)
        comp.write_bytes(comp.read_bytes() + b"\n# rebuilt\n")
        self.assert_all(self.ax(), "PASS", False)

    def test_miss_after_runner_change(self):
        tools = self.base / "tools"
        tools.mkdir()
        for n in ("axtest.py", "axtest_cache.py", "axtest_affected.py"):
            shutil.copy2(TOOLS / n, tools / n)
        self.axtest = tools / "axtest.py"
        self.put("run/a.ax", PASS_RUN)
        self.ax()
        self.assert_all(self.ax(), "PASS", True)
        p = tools / "axtest_cache.py"
        p.write_bytes(p.read_bytes() + b"\n# runner module edited\n")
        self.assert_all(self.ax(), "PASS", False)
        self.assert_all(self.ax(), "PASS", True)
        p = tools / "axtest.py"
        p.write_bytes(p.read_bytes() + b"\n# runner edited\n")
        self.assert_all(self.ax(), "PASS", False)

    def test_miss_after_option_or_env_change(self):
        self.put("run/a.ax", PASS_RUN)
        self.ax()
        self.assert_all(self.ax("--timeout-scale", "2"), "PASS", False)
        self.assert_all(self.ax("--timeout-scale", "2"), "PASS", True)
        self.assert_all(self.ax(), "PASS", True)
        self.assert_all(self.ax(env={"AXIOM_EXTRA": "1"}), "PASS", False)
        self.assert_all(self.ax(env={"AXIOM_EXTRA": "1"}), "PASS", True)
        self.assert_all(self.ax(env={"AXIOM_EXTRA": "2"}), "PASS", False)
        self.assert_all(self.ax("--exclude-requires", "zz"), "PASS", False)

    def test_miss_after_mode_change(self):
        self.put("run/a.ax", hdr("test: run", "stdout: ok\\n") + "//@ out ok\\n\n")
        self.ax(env={"STUB_FEATURES": "interp"})            # native SKIPs: only [interp] is cached
        res = self.ax(env={"STUB_FEATURES": "interp,native"})
        self.assertEqual(res["run/a.ax [interp]"], ("PASS", False))
        self.assertEqual(res["run/a.ax [native]"], ("PASS", False))
        res = self.ax(env={"STUB_FEATURES": "interp,native"})
        self.assertEqual(res["run/a.ax [native]"], ("PASS", True))
        res = self.ax(env={"STUB_FEATURES": "interp"})
        self.assertEqual(res["run/a.ax [interp]"], ("PASS", True))
        self.assertEqual(res["run/a.ax [native]"][0], "SKIP")


class NeverStoredTests(CacheCase):
    def test_fail_skip_timeout_xfail_never_stored(self):
        self.put("run/fail.ax", hdr("test: run", "modes: interp", "stdout: no\\n") + "//@ out ok\\n\n")
        self.put("run/to.ax", hdr("test: run", "modes: interp", "timeout: 0.5") + "//@ sleep 3\n")
        self.put("run/sk.ax", hdr("test: run", "modes: native", "native-after: T999") + "//@ out ok\\n\n")
        self.put("run/xf.ax", hdr("test: run", "modes: interp", "exit: 1", "xfail: T999 known") + "//@ exit 0\n")
        self.put("run/xp.ax", hdr("test: run", "modes: interp", "xfail: T999 known") + "//@ exit 0\n")
        for _ in range(2):
            res = self.ax()
            self.assertEqual(res["run/fail.ax [interp]"], ("FAIL", False))
            self.assertEqual(res["run/to.ax [interp]"], ("TIMEOUT", False))
            self.assertEqual(res["run/sk.ax [native]"], ("SKIP", False))
            self.assertEqual(res["run/xf.ax [interp]"], ("XFAIL", False))
            self.assertEqual(res["run/xp.ax [interp]"], ("XPASS", False))
        self.assertEqual(self.entries(), [])

    def test_s4_classes_never_cached(self):
        self.put("std/thread/t.ax", "module std.thread.t\n", under=self.root)
        self.put("std/core/wrap.ax", "module std.core.wrap\nuse std.thread.t\n", under=self.root)
        self.put("run/req.ax", hdr("test: run", "modes: interp", "requires: host-x", "stdout: ok\\n") + "//@ out ok\\n\n")
        self.put("run/nc.ax", hdr("test: run", "modes: interp", "nocache: yes", "stdout: ok\\n") + "//@ out ok\\n\n")
        self.put("run/thr.ax", PASS_RUN + "use std.thread.t\n")
        self.put("run/indirect.ax", PASS_RUN + "use std.core.wrap\n")
        self.put("run/asy.ax", PASS_RUN + "async fn f() {}\n")
        self.put("unit/c.test", "cmd: {compiler} version\nstdout: stubcc 0\\n\n")
        self.put("run/ok.ax", PASS_RUN)
        self.ax()
        res = self.ax()
        self.assertEqual(res["run/ok.ax [interp]"], ("PASS", True))
        for k in ("run/req.ax [interp]", "run/nc.ax [interp]", "run/thr.ax [interp]", "run/indirect.ax [interp]",
                  "run/asy.ax [interp]", "unit/c.test"):
            self.assertEqual(res[k], ("PASS", False), k)
        self.assertEqual(len(self.entries()), 1)

    def test_timer_env_bindings_never_cached(self):
        # QA F3: the binding set comes from the std host-binding files, not from a hand list
        self.put("std/core/host.ax", "module std.core.host\n@intrinsic\npub fn monotonic_ns() -> u64 {\n    0\n}\n"
                 "@intrinsic\npub fn heap_size() -> u64 {\n    0\n}\n"
                 "@intrinsic\npub fn heap_alloc(n: usize, a: usize) -> *mut u8 {\n    0 as *mut u8\n}\n", under=self.root)
        self.put("std/sys/windows/rng.ax", 'module std.sys.windows.rng\nextern "system" {\n'
                 "    fn BCryptGenRandom(a: *mut u8, n: u32) -> i32;\n}\n", under=self.root)
        self.put("std/env/env.ax", "module std.env.env\nfn get() -> i64 {\n    env_get(0)\n}\n", under=self.root)
        self.put("std/sys/windows/envb.ax", 'module std.sys.windows.envb\nextern "C" {\n'
                 "    fn env_get(x: i64) -> i64;\n}\n", under=self.root)
        self.put("run/clock.ax", PASS_RUN + "fn f() -> u64 {\n    monotonic_ns()\n}\n")
        self.put("run/rng.ax", PASS_RUN + "fn f() {\n    BCryptGenRandom(p, 4)\n}\n")
        self.put("run/env.ax", PASS_RUN + "use std.env.env\n")
        self.put("run/tick.ax", PASS_RUN + 'extern "C" {\n    fn GetTickCount64() -> u64;\n}\n')
        self.put("run/heap.ax", PASS_RUN + "fn f() -> *mut u8 {\n    heap_alloc(8, 8)\n}\n")
        # round 2 (QA F5), deny by default: an intrinsic not classified deterministic is never cached, whatever
        # its name says
        self.put("run/unknown.ax", PASS_RUN + "fn f() -> u64 {\n    heap_size()\n}\n")
        self.ax()
        res = self.ax()
        for k in ("run/clock.ax", "run/rng.ax", "run/env.ax", "run/tick.ax", "run/unknown.ax"):
            self.assertEqual(res[k + " [interp]"], ("PASS", False), k)
        self.assertEqual(res["run/heap.ax [interp]"], ("PASS", True))    # a classified deterministic binding
        self.assertEqual(self.doc["cache"]["uncacheable"], 5)

    def test_exact_dep_under_std_thread_never_cached(self):
        env = {"STUB_DEP_FILE": "1"}
        self.put("std/time/clock.ax", "module std.time.clock\n", under=self.root)
        self.put("run/a.ax", PASS_RUN + "//@ dep std/time/clock.ax\n")
        self.ax(env=env)
        self.assert_all(self.ax(env=env), "PASS", False)
        self.assertEqual(self.entries(), [])
        self.assertIn("nondeterministic", json.dumps(self.doc["cache"]["store_skipped"]))

    def test_cmd_test_with_cache_inputs_is_cached_and_tracks_inputs(self):
        self.put("unit/c.test", "cmd: {compiler} version\nstdout: stubcc 0\\n\ncache-inputs: data\n")
        self.put("data/in.txt", "1", under=self.root)
        self.ax()
        self.assertEqual(self.ax()["unit/c.test"], ("PASS", True))
        self.put("data/in.txt", "2", under=self.root)
        self.assertEqual(self.ax()["unit/c.test"], ("PASS", False))


class IntegrityTests(CacheCase):
    def test_corrupt_entry_is_a_miss_and_deleted(self):
        self.put("run/a.ax", PASS_RUN)
        self.ax()
        [e] = self.entries()
        e.write_bytes(e.read_bytes()[:-20])            # torn / truncated
        self.assert_all(self.ax(), "PASS", False)
        self.assertIn("CACHE-CORRUPT-DELETED 1", self.err)
        [e2] = self.entries()                          # re-stored by the fresh run, valid again
        self.assertTrue(axtest_cache.read_json(e2))
        # a well-formed record whose content was altered (sha mismatch) is also deleted
        rec = json.loads(e2.read_text(encoding="utf-8"))
        rec["results"]["interp"]["ms"] = 1
        e2.write_text(json.dumps(rec), encoding="utf-8")
        self.assert_all(self.ax(), "PASS", False)
        self.assertIn("CACHE-CORRUPT-DELETED 1", self.err)

    def test_concurrent_writers_never_tear_an_entry(self):
        for i in range(24):
            self.put("run/t%02d.ax" % i, PASS_RUN + "// distinct %d\n" % i)
        cmd = [sys.executable, str(AXTEST), "--root", str(self.root), "--compiler", str(STUB), "--exe-suffix",
               ".py", "--json", "--cache-dir", str(self.cache), "-j", "4"]
        procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(3)]
        for p in procs:
            out, _err = p.communicate()
            self.assertEqual(p.returncode, 0)
        files = self.entries()
        self.assertEqual(len(files), 24)
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            body = {k: v for k, v in rec.items() if k != "record_sha256"}
            self.assertEqual(rec["record_sha256"],
                             axtest_cache.sha256_bytes(axtest_cache.canonical(body).encode("utf-8")))
        leftovers = [p for p in (self.cache / "entries").rglob(".tmp-*")]
        self.assertEqual(leftovers, [])
        self.assert_all(self.ax("-j", "4"), "PASS", True)


class GateTests(CacheCase):
    root_name = "build-snap-T999"

    def setUp(self):
        super().setUp()
        self.compiler = self.root / "build" / "stubcc.py"
        self.compiler.parent.mkdir()
        shutil.copy2(STUB, self.compiler)
        (self.root / ".gitignore").write_text("build/\n", encoding="utf-8")
        run_git(self.root, "init", "-q")
        self.put("run/a.ax", PASS_RUN)
        run_git(self.root, "add", "-A")
        run_git(self.root, "commit", "-q", "-m", "a")

    def test_gate_rejects_local_entries(self):
        local = self.base / "localcomp" / "stubcc.py"     # a compiler outside any snapshot: origin local
        local.parent.mkdir()
        shutil.copy2(STUB, local)
        self.compiler = local
        self.ax()
        self.assert_all(self.ax(), "PASS", True)        # local runs may use local entries
        res = self.ax("--gate")
        self.assert_all(res, "PASS", False)
        self.assertEqual(self.doc["cache"]["rejected"].get("origin-local"), 1)

    def test_gate_uses_snapshot_entries_of_ancestor_base_only(self):
        self.ax()
        rec = json.loads(self.entries()[0].read_text(encoding="utf-8"))
        self.assertEqual(rec["producer"]["origin"], "snapshot")
        self.assertEqual(rec["producer"]["snapshot"], "build-snap-T999")
        self.assertEqual(len(rec["producer"]["base"]), 40)
        # (with fewer than 20 hits the gate's verification sample re-runs every hit, so the hit count is the
        # observable, not the `cached` flag)
        self.ax("--gate")
        self.assertEqual(self.doc["cache"]["hits"], 1)    # HEAD == base
        self.put("other/b.ax", PASS_RUN + "// b\n")       # outside the superset of run/a.ax
        run_git(self.root, "add", "-A")
        run_git(self.root, "commit", "-q", "-m", "b")
        self.ax("--gate", "run/a.ax")
        self.assertEqual(self.doc["cache"]["hits"], 1)    # base is an ancestor of HEAD
        self.assertEqual(self.ax("run/a.ax")["run/a.ax [interp]"], ("PASS", True))
        # a HEAD that does not descend from the producing base: rejected
        run_git(self.root, "checkout", "-q", "--orphan", "other")
        run_git(self.root, "commit", "-q", "-m", "unrelated")
        res = self.ax("--gate", "run/a.ax")
        self.assertEqual(res["run/a.ax [interp]"], ("PASS", False))
        self.assertEqual(self.doc["cache"]["hits"], 0)
        self.assertGreaterEqual(self.doc["cache"]["rejected"].get("base-not-ancestor", 0), 1)

    def test_gate_implies_verification_sample_with_printed_seed(self):
        self.ax()
        self.ax("--gate")
        self.assertRegex(self.err, r"VERIFY-SAMPLE seed=\d+ n=1 of 1 hits")
        self.assertIsNotNone(self.doc["cache"]["sample_seed"])


class VerifySampleTests(CacheCase):
    def test_sample_mismatch_disables_cache_for_the_run(self):
        # the outcome depends on an environment variable that is (deliberately) not part of the key
        self.put("run/env.ax", hdr("test: run", "modes: interp", "stdout: SMOKE_VAR=1\\n") + "//@ echo-env SMOKE_VAR\n")
        for i in range(3):
            self.put("run/ok%d.ax" % i, PASS_RUN + "// %d\n" % i)
        self.ax(env={"SMOKE_VAR": "1"})
        self.assert_all(self.ax(env={"SMOKE_VAR": "1"}), "PASS", True)
        res = self.ax("--verify-sample", "7", env={"SMOKE_VAR": "2"})
        self.assertEqual(res["run/env.ax [interp]"], ("FAIL", False))
        for i in range(3):
            self.assertEqual(res["run/ok%d.ax [interp]" % i], ("PASS", False))
        self.assertIn("VERIFY-SAMPLE seed=7 n=4 of 4 hits", self.err)
        self.assertIn("CACHE-MISMATCH run/env.ax", self.err)
        self.assertEqual(self.doc["cache"]["mismatch"], ["run/env.ax"])
        self.assertEqual(self.rc, 1)

    def test_sample_size_is_max_20_or_5_percent(self):
        for i in range(30):
            self.put("run/t%02d.ax" % i, PASS_RUN + "// %d\n" % i)
        self.ax("-j", "4")
        self.ax("-j", "4", "--verify-sample", "3")
        self.assertIn("VERIFY-SAMPLE seed=3 n=20 of 30 hits", self.err)
        self.assertEqual(self.doc["counts"]["cached"], 10)


class SchedulingTests(CacheCase):
    def test_longest_known_tests_start_first(self):
        log = self.root / "order.log"
        for n in ("a", "b", "c", "d"):
            self.put("run/%s.ax" % n, PASS_RUN + "//@ append order.log %s\n" % n)
        self.cache.mkdir(parents=True)
        (self.cache / "durations.json").write_text(json.dumps({"schema": 1, "ids": {
            "run/a.ax": {"interp": 10}, "run/b.ax": {"interp": 9000}, "run/c.ax": {"interp": 300}}}),
            encoding="utf-8")
        self.ax("-j", "1", "--no-cache")
        # d is unknown: estimated at half the default 1 s step timeout (500 ms)
        self.assertEqual(log.read_text(encoding="utf-8").split(), ["b", "d", "c", "a"])
        dur = json.loads((self.cache / "durations.json").read_text(encoding="utf-8"))["ids"]
        self.assertIn("interp", dur["run/d.ax"])          # recorded after the run
        self.assertLess(dur["run/b.ax"]["interp"], 9000)    # replaced by the measured duration

    def test_hits_keep_the_recorded_duration(self):
        self.put("run/a.ax", hdr("test: run", "modes: interp") + "//@ sleep 0.3\n//@ exit 0\n" +
                 "//@ out x\n")
        self.put("run/a.ax", hdr("test: run", "modes: interp", "stdout: x") + "//@ sleep 0.3\n//@ out x\n")
        self.ax()
        d1 = json.loads((self.cache / "durations.json").read_text(encoding="utf-8"))["ids"]["run/a.ax"]["interp"]
        self.assertGreaterEqual(d1, 250)
        self.assertEqual(self.ax()["run/a.ax [interp]"], ("PASS", True))
        d2 = json.loads((self.cache / "durations.json").read_text(encoding="utf-8"))["ids"]["run/a.ax"]["interp"]
        self.assertEqual(d1, d2)


class BaselineTests(CacheCase):
    def setUp(self):
        super().setUp()
        self.put("run/f1.ax", hdr("test: run", "modes: interp", "exit: 1") + "//@ exit 0\n")
        self.put("run/f2.ax", hdr("test: run", "modes: interp", "exit: 1") + "//@ exit 0\n")
        self.put("run/p.ax", PASS_RUN)
        self.bl = self.base / "baseline.txt"

    def test_subset_is_ok(self):
        self.bl.write_text("# c\nrun/f1.ax   regression:x  T1\nrun/f2.ax regression:x T1\nother/x.ax a:b T2\n",
                           encoding="utf-8")
        self.ax("--baseline", str(self.bl), cache=False)
        self.assertIn("BASELINE OK", self.err)
        self.assertNotIn("NOW PASSING", self.err)
        self.assertEqual(self.rc, 1)                    # exit status unchanged
        self.assertTrue(self.doc["baseline"]["ok"])

    def test_new_failure(self):
        self.bl.write_text("run/f1.ax regression:x T1\n", encoding="utf-8")
        self.ax("--baseline", str(self.bl), cache=False)
        self.assertIn("NEW FAILURES: run/f2.ax", self.err)
        self.assertEqual(self.doc["baseline"]["new_failures"], ["run/f2.ax"])
        self.assertEqual(self.rc, 1)

    def test_now_passing_and_subset_run(self):
        self.bl.write_text("run/f1.ax r:x T1\nrun/f2.ax r:x T1\nrun/p.ax r:x T1\nnot/run.ax r:x T1\n",
                           encoding="utf-8")
        self.ax("--baseline", str(self.bl), "run/p.ax", cache=False)
        self.assertIn("BASELINE OK", self.err)
        self.assertIn("BASELINE NOW PASSING: run/p.ax", self.err)
        self.assertEqual(self.doc["baseline"]["now_passing"], ["run/p.ax"])   # not run ids are not listed
        self.assertEqual(self.rc, 0)


class ExactRuntimeInputTests(CacheCase):
    """T437b round 1 (QA F1): in exact mode the compiler's dependency list says nothing about files the program
    reads at run time. The key must still hold the test directory tree (ADR-0041 S4 addendum), the
    `cache-inputs:` paths and the input's directory; `--affected` rule 2a must select exact entries too."""

    ENV = {"STUB_DEP_FILE": "1"}

    def list_affected(self, *changed):
        cmd = [sys.executable, str(self.axtest), "--root", str(self.root), "--compiler", str(self.compiler),
               "--exe-suffix", ".py", "--cache-dir", str(self.cache), "--list", "--affected"] + list(changed)
        full = {k: v for k, v in os.environ.items()
                if not (k.startswith("STUB_") or k.startswith("AXIOM") or k.startswith("AX_"))}
        full.update(self.ENV)
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=full)
        return p.stdout.decode("utf-8", "replace")

    def three_runs(self, data, key):
        res = self.ax(env=self.ENV)
        self.assertEqual(res[key], ("PASS", False), self.err)
        self.assertEqual(self.doc["cache"]["dep_source"], "exact")
        self.assertEqual(len(self.entries()), 1, self.err)
        self.assertEqual(self.ax(env=self.ENV)[key], ("PASS", True), self.err)
        data.write_bytes(b"v2\n")
        self.assertEqual(self.ax(env=self.ENV)[key], ("FAIL", False), self.err)
        self.assertEqual(self.ax("--no-cache", env=self.ENV)[key], ("FAIL", False))

    def test_runtime_read_of_a_file_in_the_test_directory(self):
        data = self.put("run/rt/data.txt", "v1\n")
        self.put("run/rt/r.ax", hdr("test: run", "modes: interp", "stdout: v1\\n") + "//@ cat tests/run/rt/data.txt\n")
        self.three_runs(data, "run/rt/r.ax [interp]")
        # the stored exact entry keys the directory tree, not only its listing
        rec = json.loads(self.entries()[0].read_text(encoding="utf-8"))
        self.assertIn(["tree", "tests/run/rt"], [d[:2] for d in rec["deps"]])

    def test_runtime_read_in_a_subdirectory_of_the_test_directory(self):
        data = self.put("run/rt/in/deep.txt", "v1\n")
        self.put("run/rt/r.ax", hdr("test: run", "modes: interp", "stdout: v1\\n")
                 + "//@ cat tests/run/rt/in/deep.txt\n")
        self.three_runs(data, "run/rt/r.ax [interp]")

    def test_runtime_read_of_a_declared_cache_input_outside_the_test_directory(self):
        data = self.put("data/in.txt", "v1\n", under=self.root)
        self.put("run/rt/r.ax", hdr("test: run", "modes: interp", "stdout: v1\\n", "cache-inputs: data/in.txt")
                 + "//@ cat data/in.txt\n")
        self.three_runs(data, "run/rt/r.ax [interp]")
        out = self.list_affected("data/in.txt")
        self.assertIn("run/rt/r.ax", out)

    def test_declared_cache_input_directory_selects_on_a_new_file(self):
        self.put("data/in.txt", "v1\n", under=self.root)
        self.put("run/rt/r.ax", hdr("test: run", "modes: interp", "stdout: v1\\n", "cache-inputs: data")
                 + "//@ cat data/in.txt\n")
        self.ax(env=self.ENV)
        self.assertEqual(self.ax(env=self.ENV)["run/rt/r.ax [interp]"], ("PASS", True))
        self.put("data/new.txt", "x", under=self.root)
        self.assertEqual(self.ax(env=self.ENV)["run/rt/r.ax [interp]"], ("PASS", False))
        self.assertIn("run/rt/r.ax", self.list_affected("data/new.txt"))

    def test_affected_rule_2a_selects_an_exact_entry(self):
        self.put("run/rt/data.txt", "v1\n")
        self.put("run/rt/r.ax", hdr("test: run", "modes: interp", "stdout: v1\\n") + "//@ cat tests/run/rt/data.txt\n")
        self.put("run/other/o.ax", PASS_RUN)
        self.ax(env=self.ENV)
        idx = axtest_cache.load_exact_deps_index(self.cache)
        self.assertIn("run/rt/r.ax", idx)                    # an exact entry exists
        self.assertNotIn("tests/run/rt/data.txt", idx["run/rt/r.ax"])
        out = self.list_affected("tests/run/rt/data.txt")
        self.assertIn("run/rt/r.ax", out)
        self.assertNotIn("run/other/o.ax", out)

    def test_nocache_is_never_stored_in_exact_mode(self):
        self.put("run/rt/r.ax", hdr("test: run", "modes: interp", "stdout: ok\\n", "nocache: reads the clock")
                 + "//@ out ok\\n\n")
        self.ax(env=self.ENV)
        self.assertEqual(self.ax(env=self.ENV)["run/rt/r.ax [interp]"], ("PASS", False))
        self.assertEqual(self.entries(), [])

    def test_unrelated_file_outside_the_test_directory_still_hits(self):
        # the gain of the exact mode is kept: a change elsewhere (here: another test directory) is no miss
        self.put("run/rt/r.ax", PASS_RUN)
        self.ax(env=self.ENV)
        self.put("run/other/note.txt", "x")
        self.assertEqual(self.ax(env=self.ENV)["run/rt/r.ax [interp]"], ("PASS", True))


class IdFileTests(CacheCase):
    def test_id_file_selects_exact_ids(self):
        self.put("run/a.ax", PASS_RUN)
        self.put("run/ab.ax", PASS_RUN)
        f = self.base / "ids.txt"
        f.write_text("# ids\nrun/a.ax\nrun/missing.ax\n", encoding="utf-8")
        res = self.ax("--id-file", str(f))
        self.assertEqual(sorted(res), ["run/a.ax [interp]"])
        self.assertIn("UNKNOWN-ID run/missing.ax", self.err)


if __name__ == "__main__":
    unittest.main()
