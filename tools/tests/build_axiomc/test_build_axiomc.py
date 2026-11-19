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


if __name__ == "__main__":
    unittest.main()
