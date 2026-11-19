"""Self-tests of the content-hash reuse of tools/bootstrap.py and tools/build_axiomc.py (T444c, REQ-BLD-028).

No real compiler runs: `bootstrap.run_stage_build` is replaced by a fake stage driver whose output bytes depend only
on what a real stage output depends on (bundle text, std content, flags -- not on the producing compiler, so the
stage-2 == stage-3 fixed point holds), `bootstrap.load_bundle_text` concatenates the fixture's compiler/*.ax, and
`build_axiomc.subprocess.run` is replaced by a fake cmake. Every test runs in a temporary directory in
milliseconds. Python 3 standard library only.
"""

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent.parent
sys.path.insert(0, str(TOOLS))
import bootstrap  # noqa: E402
import build_axiomc  # noqa: E402

OLD = 1_000_000_000  # an mtime older than any binary a test produces


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def backdate(path):
    os.utime(str(path), (OLD, OLD))


class Fixture:
    """A fake repository root with a fake stage driver; `run()` calls bootstrap.main in-process."""

    def __init__(self, tmp):
        self.root = Path(tmp) / "root"
        self.calls = []
        write(self.root / "compiler" / "a.ax", "module compiler.a\nfn a() {}\n")
        write(self.root / "compiler" / "sub" / "b.ax", "module compiler.sub.b\nfn b() {}\n")
        write(self.root / "std" / "core" / "x.ax", "module std.core.x\nfn x() {}\n")
        write(self.root / "std" / "axiom.toml", "name = \"std\"\n")
        write(self.root / "stage0.bin", "axiom0 v1\n")
        self.stage0 = self.root / "stage0.bin"
        self.build = Path(tmp) / "build"

    # -- fake stage driver -------------------------------------------------------------------------------------
    def fake_run_stage_build(self, stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                             opt_level, time_passes, cwd, env):
        self.calls.append(stage_label.split("_")[0] + ":" + opt_level)
        with open(bundle_path, "rb") as f:
            bundle = f.read()
        std = bootstrap.files_digest(bootstrap.hash_tree(std_root, "std", (".ax", ".toml")))
        # stage1 differs from stage2/3 (different compiler lineage); stage2 == stage3 (fixed point)
        lineage = "S1" if stage_label.startswith("stage1") else "S23"
        payload = ("%s|%s|%s|%s|%s" % (lineage, hashlib.sha256(bundle).hexdigest(), std, opt_level, stack_reserve))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(payload.encode("utf-8"))
        res = bootstrap.make_cached_result(stage_label, opt_level, output_path, cwd)
        res["cmd"] = ["(fake)", compiler_path]
        return res

    def fake_load_bundle_text(self, root):
        parts = []
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, "compiler")):
            dirnames.sort()
            for fn in sorted(f for f in filenames if f.endswith(".ax")):
                with open(os.path.join(dirpath, fn), "rb") as f:
                    parts.append(f.read().decode("utf-8"))
        return "\n".join(parts)

    def run(self, *extra, build=None, stage=3, reuse=True):
        build = Path(build) if build else self.build
        argv = ["--root", str(self.root), "--stage0", str(self.stage0), "--build-dir", str(build),
                "--out", str(build / "axiomc1.exe"), "--std-root", str(self.root / "std"),
                "--stage", str(stage), "--stage2-opt", "O1"]
        if reuse:
            argv.append("--reuse-existing")
        argv += list(extra)
        self.calls = []
        buf = io.StringIO()
        err = io.StringIO()
        with mock.patch.object(bootstrap, "run_stage_build", self.fake_run_stage_build), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fake_load_bundle_text), \
                contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = bootstrap.main(argv)
        return rc, buf.getvalue(), err.getvalue()

    def sha(self, name):
        return bootstrap.sha256_file(str(self.build / name))


class BootstrapReuse(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix="t444c_")
        self.addCleanup(self._td.cleanup)
        self.fx = Fixture(self._td.name)

    def first_build(self):
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        return out

    def test_first_build_rebuilds_then_second_reuses(self):
        out = self.first_build()
        self.assertEqual(out.count("REBUILT "), 3, out)
        self.assertIn("(no previous binary)", out)
        before = {n: self.fx.sha(n) for n in ("axiomc1.exe", "axiomc2.exe", "axiomc.exe", "axiomc2_O1.exe")}
        rc, out2, err = self.fx.run()
        self.assertEqual(rc, 0, out2 + err)
        self.assertEqual(self.fx.calls, [], out2)
        self.assertEqual(out2.count("REUSED "), 3, out2)
        self.assertNotIn("REBUILT", out2)
        self.assertIn("FIXED-POINT (O1) OK", out2)
        for n, h in before.items():
            self.assertEqual(self.fx.sha(n), h)

    def test_manifest_content(self):
        self.first_build()
        m = json.loads((self.fx.build / "axiomc2.exe.inputs.json").read_text(encoding="utf-8"))
        self.assertEqual(m["schema"], 1)
        self.assertEqual(m["kind"], "stage2")
        self.assertEqual(m["output_sha256"], self.fx.sha("axiomc2.exe"))
        self.assertEqual(m["producer_sha256"], self.fx.sha("axiomc1.exe"))
        self.assertEqual(m["flags"], {"opt": "O1", "stack_reserve": bootstrap.DEFAULT_STACK_RESERVE})
        self.assertEqual(sorted(m["files"]), ["compiler/a.ax", "compiler/sub/b.ax", "std/axiom.toml", "std/core/x.ax"])
        # every produced copy has the same manifest next to it
        for n in ("axiomc2_O1.exe", "axiomc.exe", "dir_stage2_O1/axiomc2.exe"):
            self.assertTrue((self.fx.build / (n + ".inputs.json")).is_file(), n)

    def test_content_change_with_older_mtime_rebuilds(self):
        self.first_build()
        a = self.fx.root / "compiler" / "a.ax"
        write(a, "module compiler.a\nfn a() { 1 }\n")
        backdate(a)  # older than every binary: the old mtime rule would have reused the stale binaries
        self.assertLess(a.stat().st_mtime, (self.fx.build / "axiomc2.exe").stat().st_mtime)
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        self.assertIn("sources changed: compiler/a.ax", out)
        self.assertIn("bundle text changed", out)
        self.assertEqual(out.count("REBUILT "), 3, out)

    def test_std_change_outside_the_bundle_rebuilds(self):
        self.first_build()
        x = self.fx.root / "std" / "core" / "x.ax"
        write(x, "module std.core.x\nfn x() { 2 }\n")
        backdate(x)
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        self.assertIn("sources changed: std/core/x.ax", out)
        self.assertNotIn("bundle text changed", out)
        # std/axiom.toml is a std input too
        write(self.fx.root / "std" / "axiom.toml", "name = \"std2\"\n")
        rc, out, err = self.fx.run()
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        self.assertIn("std/axiom.toml", out)

    def test_mtime_only_change_reuses(self):
        self.first_build()
        a = self.fx.root / "compiler" / "a.ax"
        os.utime(str(a), None)  # newer mtime, same bytes
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, [])
        self.assertEqual(out.count("REUSED "), 3, out)

    def test_non_ax_files_are_not_inputs(self):
        self.first_build()
        write(self.fx.root / "compiler" / "NOTES.md", "not a source\n")
        write(self.fx.root / "std" / "README.md", "not a source\n")
        rc, out, err = self.fx.run()
        self.assertEqual(self.fx.calls, [])

    def test_flag_change_rebuilds(self):
        self.first_build()
        rc, out, err = self.fx.run("--stack-reserve", "1048576")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls[0], "stage1:default")
        self.assertIn("flags changed", out)
        self.assertIn('"stack_reserve":1048576', out)
        # opt level of stage 1 is a flag too
        rc, out, err = self.fx.run("--opt", "O1", "--stack-reserve", "1048576")
        self.assertEqual(self.fx.calls[0], "stage1:O1")

    def test_stage0_content_change_rebuilds_stage1_only_when_output_differs(self):
        self.first_build()
        write(self.fx.stage0, "axiom0 v2\n")
        backdate(self.fx.stage0)
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        # stage 1 is rebuilt (producer changed); the fake stage-1 output is identical, so stage 2 and 3 key on
        # the content of axiomc1 and are reused
        self.assertEqual(self.fx.calls, ["stage1:default"], out)
        self.assertIn("producing compiler changed", out)
        self.assertEqual(out.count("REUSED "), 2, out)

    def test_binary_replaced_behind_the_manifest_is_rebuilt(self):
        self.first_build()
        for n in ("axiomc2.exe", "axiomc2_O1.exe", "dir_stage2_O1/axiomc2.exe"):
            (self.fx.build / n).write_bytes(b"tampered")
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, ["stage2:O1"], out)
        self.assertIn("does not match its manifest", out)

    def test_missing_manifest_rebuilds(self):
        self.first_build()
        (self.fx.build / "axiomc1.exe.inputs.json").unlink()
        rc, out, err = self.fx.run()
        self.assertEqual(self.fx.calls, ["stage1:default"], out)
        self.assertIn("no input manifest", out)

    def test_corrupt_manifest_rebuilds(self):
        self.first_build()
        (self.fx.build / "axiomc1.exe.inputs.json").write_text("{not json", encoding="utf-8")
        rc, out, err = self.fx.run()
        self.assertEqual(self.fx.calls, ["stage1:default"], out)
        self.assertIn("unreadable", out)

    def test_without_reuse_flag_everything_is_rebuilt(self):
        self.first_build()
        rc, out, err = self.fx.run(reuse=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        self.assertEqual(out.count("(reuse not requested)"), 3, out)
        # ... and the forced build leaves valid manifests behind
        rc, out, err = self.fx.run()
        self.assertEqual(self.fx.calls, [])

    def test_forced_build_is_byte_identical_to_reused_build(self):
        self.first_build()
        before = {n: self.fx.sha(n) for n in ("axiomc1.exe", "axiomc2.exe", "axiomc3.exe")}
        self.fx.run(reuse=False)
        for n, h in before.items():
            self.assertEqual(self.fx.sha(n), h, n)

    def test_manifests_are_path_independent_and_seedable(self):
        """T487: a build directory seeded with another directory's binaries + manifests reuses them."""
        self.first_build()
        other = Path(self._td.name) / "other_build"
        shutil.copytree(str(self.fx.build), str(other))
        # the seeded copy keeps the old mtimes; the content is what counts
        rc, out, err = self.fx.run(build=other)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, [], out)
        self.assertEqual(out.count("REUSED "), 3, out)
        a = (self.fx.build / "axiomc2.exe.inputs.json").read_bytes()
        b = (other / "axiomc2.exe.inputs.json").read_bytes()
        self.assertEqual(a, b)

    def test_failed_stage_leaves_no_manifest(self):
        def failing(*args, **kw):
            res = self.fx.fake_run_stage_build(*args, **kw)
            os.remove(args[3])
            res["rc"] = 1
            return res

        self.fx.calls = []
        argv = ["--root", str(self.fx.root), "--stage0", str(self.fx.stage0), "--build-dir", str(self.fx.build),
                "--out", str(self.fx.build / "axiomc1.exe"), "--std-root", str(self.fx.root / "std"),
                "--stage", "1", "--reuse-existing"]
        with mock.patch.object(bootstrap, "run_stage_build", failing), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = bootstrap.main(argv)
        self.assertEqual(rc, 1)
        self.assertFalse((self.fx.build / "axiomc1.exe.inputs.json").exists())

    def test_hashing_the_real_tree_is_fast(self):
        repo = TOOLS.parent
        if not (repo / "compiler").is_dir() or not (repo / "std").is_dir():
            self.skipTest("no compiler/ and std/ tree")
        t0 = time.perf_counter()
        files = bootstrap.collect_source_hashes(str(repo), str(repo / "std"))
        elapsed = time.perf_counter() - t0
        if elapsed >= 2.0:
            t0 = time.perf_counter()
            files = bootstrap.collect_source_hashes(str(repo), str(repo / "std"))
            elapsed = time.perf_counter() - t0
        print("\nT444c: hashed %d compiler/std source files in %.2fs" % (len(files), elapsed))
        self.assertGreater(len(files), 100)
        self.assertLess(elapsed, 2.0)

    def test_added_and_deleted_source_files_and_truncation_over_three_files(self):
        self.first_build()
        added = self.fx.root / "std" / "core" / "added.ax"
        write(added, "module std.core.added\nfn added() {}\n")
        backdate(added)
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        self.assertIn("sources changed: std/core/added.ax", out)

        added.unlink()
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        self.assertIn("sources changed: std/core/added.ax", out)

        for idx in range(5):
            p = self.fx.root / "std" / "core" / ("extra_%d.ax" % idx)
            write(p, "module std.core.extra_%d\n" % idx)
            backdate(p)
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("sources changed: std/core/extra_0.ax, std/core/extra_1.ax, std/core/extra_2.ax (+2 more)", out)

    def test_empty_binary_schema_change_and_fallback_candidate_reuse(self):
        self.first_build()
        # Removing dir_stage2_O1/axiomc2.exe falls back to top-level axiomc2_O1.exe / axiomc2.exe without rebuilding
        (self.fx.build / "dir_stage2_O1" / "axiomc2.exe").unlink()
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, [], out)
        self.assertEqual(out.count("REUSED "), 3, out)
        self.assertTrue((self.fx.build / "dir_stage2_O1" / "axiomc2.exe").is_file())

        # Truncating all stage-2 candidates to 0 bytes triggers rebuild with "previous binary is empty"
        for n in ("dir_stage2_O1/axiomc2.exe", "axiomc2_O1.exe", "axiomc2.exe"):
            (self.fx.build / n).write_bytes(b"")
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, ["stage2:O1"], out)
        self.assertIn("(previous binary is empty)", out)

        # Unsupported manifest schema version triggers rebuild with "input manifest schema changed"
        mp1 = self.fx.build / "axiomc1.exe.inputs.json"
        m1 = json.loads(mp1.read_text(encoding="utf-8"))
        m1["schema"] = 999
        mp1.write_text(json.dumps(m1), encoding="utf-8")
        rc, out, err = self.fx.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.fx.calls, ["stage1:default"], out)
        self.assertIn("(input manifest schema changed)", out)


class Stage0Reuse(unittest.TestCase):
    """build_axiomc.ensure_stage0 with a fake cmake."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix="t444c0_")
        self.addCleanup(self._td.cleanup)
        self.root = Path(self._td.name) / "snap"
        self.src = self.root / "bootstrap" / "axiom0"
        write(self.src / "CMakeLists.txt", "project(axiom0 C)\n")
        write(self.src / "cmake" / "AxiomTests.cmake", "# t\n")
        write(self.src / "src" / "kernel" / "k.c", "int k;\n")
        write(self.src / "src" / "kernel" / "k.h", "extern int k;\n")
        write(self.src / "src" / "mir" / "build" / "builder.c", "int builder;\n")  # a SOURCE dir named build
        self.out = self.root / "build"
        self.cmds = []

    def fake_run(self, cmd, **kw):
        self.cmds.append(list(cmd))
        if "--build" in cmd:
            payload = b"".join(Path(p).read_bytes() for p in sorted(self.src.rglob("*.[ch]"))
                               if "build" not in p.relative_to(self.src).parts[:1])
            (self.out / "axiom0.exe").write_bytes(b"AX0:" + payload)
        elif "-S" in cmd:
            self.out.mkdir(parents=True, exist_ok=True)
            (self.out / "build.ninja").write_text("# ninja\n", encoding="utf-8")

        class R:
            returncode = 0

        return R()

    def ensure(self, **kw):
        self.cmds = []
        buf = io.StringIO()
        with mock.patch.object(build_axiomc.subprocess, "run", self.fake_run), contextlib.redirect_stdout(buf):
            p = build_axiomc.ensure_stage0(str(self.out), str(self.root), **kw)
        return p, buf.getvalue()

    def builds(self):
        return [c for c in self.cmds if "--build" in c]

    def test_build_then_reuse_then_rebuild_on_source_change(self):
        p, out = self.ensure()
        self.assertEqual(Path(p), self.out / "axiom0.exe")
        self.assertEqual(len(self.builds()), 1)
        self.assertNotIn("--clean-first", self.builds()[0])  # fresh tree: nothing to clean
        self.assertIn("REBUILT ", out)
        self.assertTrue((self.out / "axiom0.exe.inputs.json").is_file())

        p, out = self.ensure()
        self.assertEqual(self.cmds, [])
        self.assertIn("REUSED ", out)

        k = self.src / "src" / "kernel" / "k.c"
        write(k, "int k = 2;\n")
        backdate(k)  # older than axiom0.exe
        p, out = self.ensure()
        self.assertEqual(len(self.builds()), 1)
        self.assertIn("--clean-first", self.builds()[0])  # ninja would trust the old mtime: clean first
        self.assertIn("sources changed: bootstrap/axiom0/src/kernel/k.c", out)
        self.assertIn(b"int k = 2;", (self.out / "axiom0.exe").read_bytes())

        p, out = self.ensure()
        self.assertEqual(self.cmds, [])

    def test_header_cmake_and_nested_build_named_source_dir_are_inputs(self):
        self.ensure()
        for rel, text in (("src/kernel/k.h", "extern long k;\n"), ("cmake/AxiomTests.cmake", "# t2\n"),
                          ("src/mir/build/builder.c", "int builder = 1;\n"), ("CMakeLists.txt", "project(x C)\n")):
            write(self.src / rel, text)
            backdate(self.src / rel)
            p, out = self.ensure()
            self.assertEqual(len(self.builds()), 1, rel)
            self.assertIn("bootstrap/axiom0/" + rel, out)

    def test_build_output_trees_and_binaries_are_not_inputs(self):
        self.ensure()
        # a CMake build tree below the source dir and stray binaries must not trigger a rebuild
        write(self.src / "build" / "CMakeCache.txt", "x\n")
        write(self.src / "build" / "generated" / "g.c", "int g;\n")
        write(self.src / "src" / "kernel" / "k.obj", "obj\n")
        write(self.src / "tmp.exe", "exe\n")
        p, out = self.ensure()
        self.assertEqual(self.cmds, [], out)

    def test_cc_and_build_type_are_inputs(self):
        self.ensure()
        p, out = self.ensure(cc="gcc")
        self.assertEqual(len(self.builds()), 1)
        self.assertIn("flags changed", out)
        p, out = self.ensure(cc="gcc", build_type="Debug")
        self.assertEqual(len(self.builds()), 1)

    def test_existing_binary_without_manifest_is_rebuilt_clean(self):
        self.out.mkdir(parents=True)
        (self.out / "axiom0.exe").write_bytes(b"legacy")
        p, out = self.ensure()
        self.assertEqual(len(self.builds()), 1)
        self.assertIn("--clean-first", self.builds()[0])
        self.assertIn("no input manifest", out)

    def test_explicit_stage0_is_used_as_is(self):
        exe = Path(self._td.name) / "my_axiom0.exe"
        exe.write_bytes(b"x")
        p, out = self.ensure(explicit_stage0=str(exe))
        self.assertEqual(Path(p), exe)
        self.assertEqual(self.cmds, [])

    def test_build_axiomc_main_end_to_end_and_force(self):
        write(self.root / "compiler" / "a.ax", "module compiler.a\nfn a() {}\n")
        write(self.root / "std" / "core" / "x.ax", "module std.core.x\nfn x() {}\n")
        write(self.root / "std" / "axiom.toml", "name = \"std\"\n")
        fx = Fixture(self._td.name)

        def run_main(*extra):
            self.cmds = []
            fx.calls = []
            buf = io.StringIO()
            err = io.StringIO()
            argv = ["--out", str(self.out), "--root", str(self.root)] + list(extra)
            with mock.patch.object(build_axiomc.subprocess, "run", self.fake_run), \
                    mock.patch.object(bootstrap, "run_stage_build", fx.fake_run_stage_build), \
                    mock.patch.object(bootstrap, "load_bundle_text", fx.fake_load_bundle_text), \
                    contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                rc = build_axiomc.main(argv)
            return rc, buf.getvalue(), err.getvalue()

        rc, out, err = run_main()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(len(self.builds()), 1)
        self.assertEqual(fx.calls, ["stage1:default", "stage2:O1"])
        self.assertIn("BUILD-AXIOMC OK:", out)
        self.assertTrue((self.out / "axiomc.exe.inputs.json").is_file())
        self.assertEqual(
            (self.out / "axiomc.exe.inputs.json").read_bytes(),
            (self.out / "axiomc2.exe.inputs.json").read_bytes(),
        )

        # Second call reuses stage 0, stage 1, and stage 2
        rc, out2, err2 = run_main()
        self.assertEqual(rc, 0, out2 + err2)
        self.assertEqual(self.builds(), [])
        self.assertEqual(fx.calls, [])
        self.assertEqual(out2.count("REUSED "), 3, out2)

        # --force reuses stage 0 (unchanged bootstrap/axiom0) and forces stage 1 + stage 2 rebuild
        rc, out3, err3 = run_main("--force")
        self.assertEqual(rc, 0, out3 + err3)
        self.assertEqual(self.builds(), [])
        self.assertEqual(fx.calls, ["stage1:default", "stage2:O1"])
        self.assertEqual(out3.count("(reuse not requested)"), 2, out3)


class SeededBootstrapAndOracleReuse(unittest.TestCase):
    """T487 self-tests: seed hit, seed miss -> full chain, B != C -> failure, stage-0 failure -> failure,
    trust-root c2 == B check, and reuse inside fixedpoint_oracle / axiomc_e2e_oracle."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix="t487_")
        self.addCleanup(self._td.cleanup)
        self.fx = Fixture(self._td.name)
        self.cache_dir = Path(self._td.name) / "compiler-cache"

    def test_seed_miss_falls_back_to_full_chain_and_populates_cache(self):
        # 1. Explicit missing --seed falls back to full chain
        missing_seed = Path(self._td.name) / "nonexistent_seed.exe"
        rc, out, err = self.fx.run("--seed", str(missing_seed), "--cache-dir", str(self.cache_dir))
        self.assertEqual(rc, 0, out + err)
        self.assertIn("SEED: miss (explicit seed not found", out)
        self.assertIn("falling back to full chain", out)
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        cached_exes = list(self.cache_dir.glob("axiomc2_O1_*.exe"))
        self.assertEqual(len(cached_exes), 1)
        self.assertTrue((Path(str(cached_exes[0]) + ".inputs.json")).is_file())

        # 2. Automatic --seed auto with empty cache dir falls back to full chain and populates cache
        empty_cache = Path(self._td.name) / "empty-cache"
        build2 = Path(self._td.name) / "build2"
        rc2, out2, err2 = self.fx.run("--seed", "auto", "--cache-dir", str(empty_cache), build=build2)
        self.assertEqual(rc2, 0, out2 + err2)
        self.assertIn("SEED: miss (", out2)
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        self.assertEqual(len(list(empty_cache.glob("axiomc2_O1_*.exe"))), 1)

    def test_seed_hit_builds_A_B_C_and_matches_full_chain_byte_for_byte(self):
        # Populate the cache from v1 sources (base commit)
        rc, out, err = self.fx.run("--seed", "auto", "--cache-dir", str(self.cache_dir))
        self.assertEqual(rc, 0, out + err)
        base_seed = list(self.cache_dir.glob("axiomc2_O1_*.exe"))[0]

        # Modify compiler/a.ax (new task change set) and backdate its mtime
        a = self.fx.root / "compiler" / "a.ax"
        write(a, "module compiler.a\nfn a() -> i32 { 42 }\n")
        backdate(a)

        # Build v2 via seeded mode (auto from cache_dir) in build_seeded
        build_seeded = Path(self._td.name) / "build_seeded"
        rc_s, out_s, err_s = self.fx.run(
            "--seed", "auto", "--cache-dir", str(self.cache_dir), "--check-both-opt", build=build_seeded
        )
        self.assertEqual(rc_s, 0, out_s + err_s)
        self.assertIn("SEED: hit %s" % str(base_seed), out_s)
        self.assertEqual(
            self.fx.calls,
            ["stage1:default", "seedA:O1", "stage2:O1", "stage3:O1", "seedA:O0", "stage2:O0", "stage3:O0"],
        )
        self.assertIn("FIXED-POINT (O1) OK:", out_s)
        self.assertIn("[seeded B==C]", out_s)
        self.assertIn("FIXED-POINT (O0) OK:", out_s)
        self.assertIn("STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe", out_s)

        # Build v2 via full chain in build_full and compare sha256(B) == sha256(c2) at O1 and O0
        build_full = Path(self._td.name) / "build_full"
        rc_f, out_f, err_f = self.fx.run("--full-chain", "--check-both-opt", build=build_full)
        self.assertEqual(rc_f, 0, out_f + err_f)
        self.assertEqual(
            self.fx.calls,
            ["stage1:default", "stage2:O1", "stage3:O1", "stage2:O0", "stage3:O0"],
        )
        for opt in ("O1", "O0"):
            b_bin = build_seeded / ("dir_stage2_%s" % opt) / "axiomc2.exe"
            c_bin = build_seeded / ("dir_stage3_%s" % opt) / "axiomc3.exe"
            c2_bin = build_full / ("dir_stage2_%s" % opt) / "axiomc2.exe"
            self.assertEqual(bootstrap.sha256_file(str(b_bin)), bootstrap.sha256_file(str(c_bin)))
            self.assertEqual(bootstrap.sha256_file(str(b_bin)), bootstrap.sha256_file(str(c2_bin)))

        # Re-running seeded mode in build_seeded reuses stage1, B (stage2), and C (stage3) with 0 builds
        rc_r, out_r, err_r = self.fx.run(
            "--seed", "auto", "--cache-dir", str(self.cache_dir), "--check-both-opt", build=build_seeded
        )
        self.assertEqual(rc_r, 0, out_r + err_r)
        self.assertEqual(self.fx.calls, [], out_r)
        self.assertEqual(out_r.count("REUSED "), 5, out_r)  # stage1 + (stage2, stage3) x {O1, O0}

        # When O1 was built first (as build_axiomc.py does) and then --check-both-opt runs (as fixedpoint_oracle does),
        # O1 is reused (0 O1 builds) and only O0 is built via seeded mode
        build_o1_then_both = Path(self._td.name) / "build_o1_then_both"
        rc_o1, out_o1, err_o1 = self.fx.run(
            "--seed", "auto", "--cache-dir", str(self.cache_dir), build=build_o1_then_both
        )
        self.assertEqual(rc_o1, 0, out_o1 + err_o1)
        self.assertEqual(self.fx.calls, ["stage1:default", "seedA:O1", "stage2:O1", "stage3:O1"])
        rc_both, out_both, err_both = self.fx.run(
            "--seed", "auto", "--cache-dir", str(self.cache_dir), "--check-both-opt", build=build_o1_then_both
        )
        self.assertEqual(rc_both, 0, out_both + err_both)
        self.assertEqual(self.fx.calls, ["seedA:O0", "stage2:O0", "stage3:O0"], out_both)
        self.assertEqual(out_both.count("REUSED "), 3, out_both)  # stage1 + stage2(O1) + stage3(O1)

    def test_seeded_b_not_equal_c_fails(self):
        # Create a seed binary
        seed_bin = Path(self._td.name) / "seed.exe"
        write(seed_bin, "S23|seed\n")

        counter = {"n": 0}

        def nondet_stage_build(stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                               opt_level, time_passes, cwd, env):
            res = self.fx.fake_run_stage_build(
                stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                opt_level, time_passes, cwd, env
            )
            if not stage_label.startswith("stage1"):
                counter["n"] += 1
                with open(output_path, "ab") as f:
                    f.write(("|nondet=%d" % counter["n"]).encode("utf-8"))
                res["sha256"] = bootstrap.sha256_file(output_path)
                res["size_bytes"] = os.path.getsize(output_path)
            return res

        buf, err = io.StringIO(), io.StringIO()
        argv = [
            "--root", str(self.fx.root),
            "--stage0", str(self.fx.stage0),
            "--build-dir", str(self.fx.build),
            "--out", str(self.fx.build / "axiomc1.exe"),
            "--std-root", str(self.fx.root / "std"),
            "--seed", str(seed_bin),
        ]
        with mock.patch.object(bootstrap, "run_stage_build", nondet_stage_build), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = bootstrap.main(argv)
        self.assertEqual(rc, 1)
        self.assertIn("FAIL seeded fixed-point mismatch (O1): sha256(B)=", err.getvalue())

    def test_stage0_guard_failure_fails_seeded_mode(self):
        seed_bin = Path(self._td.name) / "seed.exe"
        write(seed_bin, "S23|seed\n")

        # Case A: stage1 (axiom0 -> axiomc1) fails to compile the new source
        def stage1_compile_fail(stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                                opt_level, time_passes, cwd, env):
            res = self.fx.fake_run_stage_build(
                stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                opt_level, time_passes, cwd, env
            )
            if stage_label.startswith("stage1"):
                os.remove(output_path)
                res["rc"] = 1
                res["stderr"] = "error[AX_TYPE_NOT_CALLABLE]: synthetic symbol-id overflow in stage0\n"
            return res

        buf, err = io.StringIO(), io.StringIO()
        argv = [
            "--root", str(self.fx.root),
            "--stage0", str(self.fx.stage0),
            "--build-dir", str(self.fx.build),
            "--out", str(self.fx.build / "axiomc1.exe"),
            "--std-root", str(self.fx.root / "std"),
            "--seed", str(seed_bin),
        ]
        with mock.patch.object(bootstrap, "run_stage_build", stage1_compile_fail), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = bootstrap.main(argv)
        self.assertEqual(rc, 1)
        self.assertIn("FAIL stage1 (axiom0 -> axiomc1) rc=1", err.getvalue())
        self.assertIn("synthetic symbol-id overflow", err.getvalue())

        # Case B: stage1 builds axiomc1, but axiomc1 produces divergent .exe bytes on the smoke set vs B
        def stage1_smoke_diverge(stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                                 opt_level, time_passes, cwd, env):
            res = self.fx.fake_run_stage_build(
                stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                opt_level, time_passes, cwd, env
            )
            if stage_label.startswith("stage1"):
                with open(output_path, "ab") as f:
                    f.write(b"|STAGE0_SMOKE_DIVERGE")
                res["sha256"] = bootstrap.sha256_file(output_path)
                res["size_bytes"] = os.path.getsize(output_path)
            return res

        build_b = Path(self._td.name) / "build_smoke_div"
        buf2, err2 = io.StringIO(), io.StringIO()
        argv2 = [
            "--root", str(self.fx.root),
            "--stage0", str(self.fx.stage0),
            "--build-dir", str(build_b),
            "--out", str(build_b / "axiomc1.exe"),
            "--std-root", str(self.fx.root / "std"),
            "--seed", str(seed_bin),
        ]
        with mock.patch.object(bootstrap, "run_stage_build", stage1_smoke_diverge), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                contextlib.redirect_stdout(buf2), contextlib.redirect_stderr(err2):
            rc2 = bootstrap.main(argv2)
        self.assertEqual(rc2, 1)
        self.assertIn("FAIL stage0-guard: smoke .exe mismatch", err2.getvalue())

    def test_trust_root_verifies_c2_equals_seeded_b(self):
        # First populate cache
        rc, out, err = self.fx.run("--seed", "auto", "--cache-dir", str(self.cache_dir))
        self.assertEqual(rc, 0, out + err)

        # Edit source and run --trust-root at both O1 and O0
        write(self.fx.root / "compiler" / "a.ax", "module compiler.a\nfn a() -> i32 { 99 }\n")
        build_tr = Path(self._td.name) / "build_tr"
        rc_tr, out_tr, err_tr = self.fx.run(
            "--trust-root", "--stage2-opt", "both", "--cache-dir", str(self.cache_dir), build=build_tr
        )
        self.assertEqual(rc_tr, 0, out_tr + err_tr)
        self.assertIn("TRUST-ROOT (O1) OK: sha256(c2_O1) == sha256(B_O1)", out_tr)
        self.assertIn("TRUST-ROOT (O0) OK: sha256(c2_O0) == sha256(B_O0)", out_tr)

    def test_reuse_inside_fixedpoint_oracle_and_axiomc_e2e_oracle(self):
        fp_dir = TOOLS.parent / "tests" / "selfhost" / "fixedpoint"
        e2e_dir = TOOLS.parent / "tests" / "selfhost" / "obj_link_driver"
        for p in (str(fp_dir), str(e2e_dir)):
            if p not in sys.path:
                sys.path.insert(0, p)
        import fixedpoint_oracle
        import axiomc_e2e_oracle

        # Prepare stage0 in build dir so fixedpoint_oracle resolves build_dir
        self.fx.build.mkdir(parents=True, exist_ok=True)
        stage0_in_build = self.fx.build / "axiom0.exe"
        shutil.copy2(str(self.fx.stage0), str(stage0_in_build))
        self.fx.stage0 = stage0_in_build
        # Create minimal tools/bootstrap.py and tools/build_axiomc.py markers in fx.root
        write(self.fx.root / "tools" / "bootstrap.py", "# stub\n")
        write(self.fx.root / "tools" / "build_axiomc.py", "# stub\n")

        # 1. Pre-build both O1 and O0 via seeded mode (or full chain) as the gate does
        rc, out, err = self.fx.run("--check-both-opt", "--cache-dir", str(self.cache_dir))
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(
            self.fx.calls,
            ["stage1:default", "stage2:O1", "stage3:O1", "stage2:O0", "stage3:O0"],
        )
        # Write stage0 manifest so build_axiomc.ensure_stage0 reuses axiom0.exe
        s0_exp = build_axiomc.stage0_inputs(str(self.fx.root / "bootstrap" / "axiom0"), "clang", "Release")
        bootstrap.write_manifest(str(stage0_in_build), s0_exp)

        # 2. Run fixedpoint_oracle: must reuse all 5 stage binaries in step 2 and 3 in step 3 with 0 rebuilds
        tmp_fp = Path(self._td.name) / "tmp_fp"
        self.fx.calls = []
        buf_fp, err_fp = io.StringIO(), io.StringIO()
        with mock.patch.object(bootstrap, "run_stage_build", self.fx.fake_run_stage_build), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                mock.patch.object(build_axiomc.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0})()), \
                contextlib.redirect_stdout(buf_fp), contextlib.redirect_stderr(err_fp):
            rc_fp = fixedpoint_oracle.main([str(self.fx.build / "axiomc2.exe"), str(tmp_fp), str(self.fx.root)])
        out_fp = buf_fp.getvalue()
        self.assertEqual(rc_fp, 0, out_fp + err_fp.getvalue())
        self.assertEqual(self.fx.calls, [], out_fp)
        self.assertGreaterEqual(out_fp.count("REUSED "), 5, out_fp)
        self.assertNotIn("REBUILT ", out_fp)
        self.assertIn("FIXEDPOINT-PARITY OK", out_fp)

        # 3. Check axiomc_e2e_oracle manifest-based reuse (ignores mtime, checks manifest)
        with mock.patch.object(bootstrap, "run_stage_build", self.fx.fake_run_stage_build), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text):
            bundle_bytes = self.fx.fake_load_bundle_text(str(self.fx.root)).encode("utf-8")
            cand, ih, why = axiomc_e2e_oracle.resolve_prebuilt_axiomc_with_manifest(
                str(stage0_in_build), str(self.fx.root), bundle_bytes=bundle_bytes
            )
            self.assertIsNotNone(cand)
            self.assertIsNone(why)
            self.assertEqual(Path(cand), self.fx.build / "axiomc1.exe")

            # Backdated source edit invalidates manifest reuse in both axiomc_e2e_oracle and fixedpoint_oracle
            a = self.fx.root / "compiler" / "a.ax"
            write(a, "module compiler.a\nfn a() -> i32 { 7 }\n")
            backdate(a)
            bundle_bytes_v2 = self.fx.fake_load_bundle_text(str(self.fx.root)).encode("utf-8")
            cand2, _ih2, why2 = axiomc_e2e_oracle.resolve_prebuilt_axiomc_with_manifest(
                str(stage0_in_build), str(self.fx.root), bundle_bytes=bundle_bytes_v2
            )
            self.assertIsNone(cand2)
            self.assertIn("sources changed: compiler/a.ax", why2)

        # 4. fixedpoint_oracle rebuilds when source manifest changed
        self.fx.calls = []
        buf_fp2, err_fp2 = io.StringIO(), io.StringIO()
        with mock.patch.object(bootstrap, "run_stage_build", self.fx.fake_run_stage_build), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                mock.patch.object(build_axiomc.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0})()), \
                contextlib.redirect_stdout(buf_fp2), contextlib.redirect_stderr(err_fp2):
            rc_fp2 = fixedpoint_oracle.main([str(self.fx.build / "axiomc2.exe"), str(tmp_fp), str(self.fx.root)])
        out_fp2 = buf_fp2.getvalue()
        self.assertEqual(rc_fp2, 0, out_fp2 + err_fp2.getvalue())
        self.assertNotEqual(self.fx.calls, [])
        self.assertIn("REBUILT ", out_fp2)
        self.assertIn("FIXEDPOINT-PARITY OK", out_fp2)

    def test_fixedpoint_oracle_timeout_derived_from_manifest_and_scale(self):
        fp_dir = TOOLS.parent / "tests" / "selfhost" / "fixedpoint"
        if str(fp_dir) not in sys.path:
            sys.path.insert(0, str(fp_dir))
        import fixedpoint_oracle

        base = fixedpoint_oracle.derive_test_timeout_budget(argv=[], env={})
        self.assertGreaterEqual(base, 3600.0)
        scaled_arg = fixedpoint_oracle.derive_test_timeout_budget(argv=["--timeout-scale", "6"], env={})
        self.assertEqual(scaled_arg, base * 6.0)
        scaled_eq = fixedpoint_oracle.derive_test_timeout_budget(argv=["--timeout-scale=3.5"], env={})
        self.assertEqual(scaled_eq, base * 3.5)
        scaled_env = fixedpoint_oracle.derive_test_timeout_budget(argv=[], env={"AXTEST_TIMEOUT_SCALE": "4"})
        self.assertEqual(scaled_env, base * 4.0)

        # CLI forms: both `--timeout-scale N` and `--timeout-scale=N` pass arg validation; invalid/missing values return 2.
        for valid_extra in (["--timeout-scale", "6"], ["--timeout-scale=6"]):
            buf, err = io.StringIO(), io.StringIO()
            with mock.patch.object(bootstrap, "verify_no_external_tools_on_path", return_value=(False, "fake-gcc")), \
                    contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                rc = fixedpoint_oracle.main(
                    [str(self.fx.stage0), str(self.fx.build), str(self.fx.root)] + valid_extra
                )
            self.assertEqual(rc, 1, valid_extra)
        for bad_extra in (["--timeout-scale"], ["--timeout-scale", "0"], ["--timeout-scale=-2"], ["--unknown-flag"]):
            buf, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                rc = fixedpoint_oracle.main(
                    [str(self.fx.stage0), str(self.fx.build), str(self.fx.root)] + bad_extra
                )
            self.assertEqual(rc, 2, bad_extra)

    def test_trust_root_catches_poisoned_same_commit_cache_entry(self):
        # F1 regression: a poisoned seed cached for the *current* source tree must not be overwritten before verification.
        poison = b"POISON-SAME-COMMIT"
        poison_seed = Path(self._td.name) / "poison_seed.exe"
        write(poison_seed, "S23|" + poison.decode() + "\n")

        def poisoned_driver(stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                            opt_level, time_passes, cwd, env):
            res = self.fx.fake_run_stage_build(stage_label, compiler_path, bundle_path, output_path, std_root,
                                               stack_reserve, opt_level, time_passes, cwd, env)
            if poison in Path(compiler_path).read_bytes():
                with open(output_path, "ab") as f:
                    f.write(b"|" + poison)
                res["sha256"] = bootstrap.sha256_file(output_path)
                res["size_bytes"] = os.path.getsize(output_path)
            return res

        def run_with(argv):
            buf, err = io.StringIO(), io.StringIO()
            with mock.patch.object(bootstrap, "run_stage_build", poisoned_driver), \
                    mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                    contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                rc = bootstrap.main(argv)
            return rc, buf.getvalue(), err.getvalue()

        build_s = Path(self._td.name) / "build_seeded_same"
        rc_s, out_s, err_s = run_with([
            "--root", str(self.fx.root), "--stage0", str(self.fx.stage0), "--build-dir", str(build_s),
            "--out", str(build_s / "axiomc1.exe"), "--std-root", str(self.fx.root / "std"),
            "--cache-dir", str(self.cache_dir), "--seed", str(poison_seed),
        ])
        self.assertEqual(rc_s, 0, out_s + err_s)

        # Now run --trust-root on the *same* source tree without --seed: must catch the poisoned cached entry.
        build_t = Path(self._td.name) / "build_trust_same"
        rc_t, out_t, err_t = run_with([
            "--root", str(self.fx.root), "--stage0", str(self.fx.stage0), "--build-dir", str(build_t),
            "--out", str(build_t / "axiomc1.exe"), "--std-root", str(self.fx.root / "std"),
            "--cache-dir", str(self.cache_dir), "--trust-root", "--stage2-opt", "O1",
        ])
        self.assertEqual(rc_t, 1, out_t + err_t)
        self.assertIn("FAIL trust-root mismatch (O1)", err_t)

    def test_seeded_rerun_without_no_stage0_smoke_still_runs_smoke_guard(self):
        # F2 regression: a build published with --no-stage0-smoke cannot bypass stage0-smoke on a normal --reuse-existing run.
        seed_bin = Path(self._td.name) / "seed_smoke_bypass.exe"
        write(seed_bin, "S23|seed\n")

        def smoke_diverge(stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                          opt_level, time_passes, cwd, env):
            res = self.fx.fake_run_stage_build(stage_label, compiler_path, bundle_path, output_path, std_root,
                                               stack_reserve, opt_level, time_passes, cwd, env)
            if stage_label.startswith("stage1"):
                with open(output_path, "ab") as f:
                    f.write(b"|STAGE0_SMOKE_DIVERGE")
                res["sha256"] = bootstrap.sha256_file(output_path)
                res["size_bytes"] = os.path.getsize(output_path)
            return res

        base_argv = [
            "--root", str(self.fx.root), "--stage0", str(self.fx.stage0), "--build-dir", str(self.fx.build),
            "--out", str(self.fx.build / "axiomc1.exe"), "--std-root", str(self.fx.root / "std"),
            "--cache-dir", str(self.cache_dir), "--stage", "2", "--stage2-opt", "O1",
            "--seed", str(seed_bin), "--reuse-existing",
        ]
        buf1, err1 = io.StringIO(), io.StringIO()
        with mock.patch.object(bootstrap, "run_stage_build", smoke_diverge), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                contextlib.redirect_stdout(buf1), contextlib.redirect_stderr(err1):
            rc1 = bootstrap.main(base_argv + ["--no-stage0-smoke"])
        self.assertEqual(rc1, 0, buf1.getvalue() + err1.getvalue())

        buf2, err2 = io.StringIO(), io.StringIO()
        with mock.patch.object(bootstrap, "run_stage_build", smoke_diverge), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                contextlib.redirect_stdout(buf2), contextlib.redirect_stderr(err2):
            rc2 = bootstrap.main(base_argv)
        self.assertEqual(rc2, 1, buf2.getvalue() + err2.getvalue())
        self.assertIn("FAIL stage0-guard: smoke .exe mismatch", err2.getvalue())


if __name__ == "__main__":
    unittest.main()
