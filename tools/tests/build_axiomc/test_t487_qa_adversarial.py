"""T487 QA gate adversarial self-tests (axiom-architect, round 0).

Cases the implementation self-tests did not cover:
- A poisoned seed (a "trusting trust" compiler whose descendants all carry a marker) reaches its own fixed point
  (B == C) and passes the cheap stage-0 smoke guard, so seeded mode alone accepts it; `--trust-root` must reject it
  because the full-chain c2 differs from the seeded B. This is the reason the trust root stays in sweeps/phase gates.
- An explicit seed whose bytes no longer match its `.inputs.json` manifest is a seed miss (full chain), never used.
- A seed that cannot compile the new source fails loudly (no silent pass, no stale compiler reported as built).

Fake stage driver only (no real compiler runs); Python 3 standard library only.
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(HERE))
import bootstrap  # noqa: E402
from test_build_axiomc import Fixture, write  # noqa: E402

POISON = b"POISON-LINEAGE"


class T487QaAdversarial(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix="t487qa_")
        self.addCleanup(self._td.cleanup)
        self.fx = Fixture(self._td.name)
        self.cache_dir = Path(self._td.name) / "compiler-cache"

    def poisoned_stage_build(self, stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                             opt_level, time_passes, cwd, env):
        res = self.fx.fake_run_stage_build(stage_label, compiler_path, bundle_path, output_path, std_root,
                                           stack_reserve, opt_level, time_passes, cwd, env)
        try:
            with open(compiler_path, "rb") as f:
                producer = f.read()
        except OSError:
            producer = b""
        if POISON in producer:
            # the poisoned compiler reproduces itself into everything it compiles
            with open(output_path, "ab") as f:
                f.write(b"|" + POISON)
            res["sha256"] = bootstrap.sha256_file(output_path)
            res["size_bytes"] = os.path.getsize(output_path)
        return res

    def run_main(self, argv, driver):
        buf, err = io.StringIO(), io.StringIO()
        self.fx.calls = []
        with mock.patch.object(bootstrap, "run_stage_build", driver), \
                mock.patch.object(bootstrap, "load_bundle_text", self.fx.fake_load_bundle_text), \
                contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = bootstrap.main(argv)
        return rc, buf.getvalue(), err.getvalue()

    def base_argv(self, build):
        return ["--root", str(self.fx.root), "--stage0", str(self.fx.stage0), "--build-dir", str(build),
                "--out", str(build / "axiomc1.exe"), "--std-root", str(self.fx.root / "std"),
                "--cache-dir", str(self.cache_dir)]

    def test_poisoned_seed_passes_seeded_mode_but_trust_root_rejects_it(self):
        seed = Path(self._td.name) / "poisoned_seed.exe"
        write(seed, "S23|" + POISON.decode() + "\n")

        # Seeded mode alone: B == C holds (the poison is self-reproducing) and the stage-0 smoke guard passes.
        build_s = Path(self._td.name) / "build_seeded"
        rc_s, out_s, err_s = self.run_main(self.base_argv(build_s) + ["--seed", str(seed)], self.poisoned_stage_build)
        self.assertEqual(rc_s, 0, out_s + err_s)
        self.assertIn("[seeded B==C]", out_s)
        b_bytes = (build_s / "dir_stage2_O1" / "axiomc2.exe").read_bytes()
        self.assertIn(POISON, b_bytes)

        # Trust root (full chain + c2 == B) must reject the poisoned seed at O1 and never report TRUST-ROOT OK.
        build_t = Path(self._td.name) / "build_trust"
        rc_t, out_t, err_t = self.run_main(
            self.base_argv(build_t) + ["--trust-root", "--stage2-opt", "both", "--seed", str(seed)],
            self.poisoned_stage_build,
        )
        self.assertEqual(rc_t, 1, out_t + err_t)
        self.assertIn("FAIL trust-root mismatch (O1)", err_t)
        self.assertNotIn("TRUST-ROOT (O1) OK", out_t)
        c2_bytes = (build_t / "dir_stage2_O1" / "axiomc2.exe").read_bytes()
        self.assertNotIn(POISON, c2_bytes)

        # The same trust-root run with a clean seed passes at both levels (control).
        clean = Path(self._td.name) / "clean_seed.exe"
        write(clean, "S23|clean\n")
        build_c = Path(self._td.name) / "build_trust_clean"
        rc_c, out_c, err_c = self.run_main(
            self.base_argv(build_c) + ["--trust-root", "--stage2-opt", "both", "--seed", str(clean)],
            self.poisoned_stage_build,
        )
        self.assertEqual(rc_c, 0, out_c + err_c)
        self.assertIn("TRUST-ROOT (O1) OK", out_c)
        self.assertIn("TRUST-ROOT (O0) OK", out_c)

    def test_explicit_seed_not_matching_its_manifest_is_a_miss(self):
        # Produce a real cached seed with a manifest, then tamper with the seed bytes.
        rc0, out0, err0 = self.run_main(self.base_argv(self.fx.build) + ["--full-chain", "--stage", "3"],
                                        self.fx.fake_run_stage_build)
        self.assertEqual(rc0, 0, out0 + err0)
        cached = sorted(self.cache_dir.glob("axiomc2_O1_*.exe"))
        self.assertEqual(len(cached), 1, out0)
        with open(cached[0], "ab") as f:
            f.write(b"|tampered")
        build2 = Path(self._td.name) / "build2"
        rc, out, err = self.run_main(self.base_argv(build2) + ["--seed", str(cached[0])], self.fx.fake_run_stage_build)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("SEED: miss (explicit seed does not match its manifest", out)
        self.assertEqual(self.fx.calls, ["stage1:default", "stage2:O1", "stage3:O1"])
        self.assertNotIn("seedA:O1", self.fx.calls)

    def test_seed_that_cannot_compile_new_source_fails_loudly(self):
        seed = Path(self._td.name) / "old_seed.exe"
        write(seed, "S23|too-old\n")

        def seed_rejects(stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                         opt_level, time_passes, cwd, env):
            if stage_label.startswith("seedA"):
                self.fx.calls.append("seedA:" + opt_level)
                return {"stage": stage_label, "opt": opt_level, "rc": 1, "stdout": "",
                        "stderr": "error[AX_PARSE]: seed does not know this syntax\n", "wall_s": 0.0,
                        "size_bytes": 0, "sha256": "", "peak_ws_mb": 0.0, "peak_commit_mb": 0.0, "cmd": []}
            return self.fx.fake_run_stage_build(stage_label, compiler_path, bundle_path, output_path, std_root,
                                                stack_reserve, opt_level, time_passes, cwd, env)

        rc, out, err = self.run_main(self.base_argv(self.fx.build) + ["--seed", str(seed)], seed_rejects)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("FAIL seeded A (O1, seed -> A) rc=1", err)
        self.assertNotIn("FIXED-POINT (O1) OK", out)
        self.assertFalse((self.fx.build / "dir_stage2_O1" / "axiomc2.exe").exists())
        self.assertFalse((self.fx.build / "axiomc2.exe.inputs.json").exists())

    def test_trust_root_auto_seed_does_not_self_seed_and_catches_poisoned_cache(self):
        # 1. With an empty cache, --trust-root (without --seed) must NOT store c2 first and then seed from itself.
        empty_cache = Path(self._td.name) / "empty-trust-cache"
        build_empty = Path(self._td.name) / "build_trust_empty"
        rc_e, out_e, err_e = self.run_main(
            ["--root", str(self.fx.root), "--stage0", str(self.fx.stage0), "--build-dir", str(build_empty),
             "--out", str(build_empty / "axiomc1.exe"), "--std-root", str(self.fx.root / "std"),
             "--trust-root", "--stage2-opt", "O1", "--cache-dir", str(empty_cache)],
            self.fx.fake_run_stage_build,
        )
        self.assertEqual(rc_e, 0, out_e + err_e)
        self.assertIn("TRUST-ROOT SEED: none", out_e, "empty cache must not self-seed from just-built c2:\n" + out_e)
        self.assertNotIn("TRUST-ROOT (O1) OK", out_e)

        # 2. Populate cache with a poisoned seed (from an earlier seeded gate on v1), then edit source to v2 and run
        # `--trust-root --stage2-opt both --cache-dir <cache>` WITHOUT explicit `--seed` (the documented §4 command).
        poison_seed = Path(self._td.name) / "poison_seed_v0.exe"
        write(poison_seed, "S23|" + POISON.decode() + "\n")
        build_s = Path(self._td.name) / "build_poison_cache_fill"
        rc_s, out_s, err_s = self.run_main(
            self.base_argv(build_s) + ["--seed", str(poison_seed)],
            self.poisoned_stage_build,
        )
        self.assertEqual(rc_s, 0, out_s + err_s)
        self.assertEqual(len(list(self.cache_dir.glob("axiomc2_O1_*.exe"))), 1)

        write(self.fx.root / "compiler" / "a.ax", "module compiler.a\nfn a() -> i32 { 123 }\n")
        build_tr = Path(self._td.name) / "build_trust_auto"
        rc_tr, out_tr, err_tr = self.run_main(
            self.base_argv(build_tr) + ["--trust-root", "--stage2-opt", "both"],
            self.poisoned_stage_build,
        )
        self.assertEqual(rc_tr, 1, "trust-root --seed auto must reject poisoned cached seed:\n" + out_tr + err_tr)
        self.assertIn("FAIL trust-root mismatch (O1)", err_tr)

    def test_seeded_b_not_equal_c_does_not_pass_on_rerun_with_reuse_existing(self):
        seed = Path(self._td.name) / "seed_nondet.exe"
        write(seed, "S23|seed\n")
        counter = {"n": 0}

        def nondet_build(stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                         opt_level, time_passes, cwd, env):
            res = self.fx.fake_run_stage_build(stage_label, compiler_path, bundle_path, output_path, std_root,
                                               stack_reserve, opt_level, time_passes, cwd, env)
            if not stage_label.startswith("stage1"):
                counter["n"] += 1
                with open(output_path, "ab") as f:
                    f.write(("|nondet=%d" % counter["n"]).encode("utf-8"))
                res["sha256"] = bootstrap.sha256_file(output_path)
                res["size_bytes"] = os.path.getsize(output_path)
            return res

        # Matches build_axiomc.py's invocation (`--stage 2 --stage2-opt O1 --seed ... --reuse-existing`).
        argv = self.base_argv(self.fx.build) + ["--stage", "2", "--stage2-opt", "O1", "--seed", str(seed),
                                                "--reuse-existing"]
        rc1, out1, err1 = self.run_main(argv, nondet_build)
        self.assertEqual(rc1, 1, out1 + err1)
        self.assertIn("FAIL seeded fixed-point mismatch (O1)", err1)

        rc2, out2, err2 = self.run_main(argv, nondet_build)
        self.assertEqual(rc2, 1, "rerun after B != C must not falsely reuse unverified B and exit 0:\n" + out2 + err2)
        self.assertIn("FAIL seeded fixed-point mismatch (O1)", err2)

    def test_stage0_smoke_failure_does_not_poison_cache_or_pass_on_rerun(self):
        seed = Path(self._td.name) / "seed_smoke.exe"
        write(seed, "S23|seed\n")

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

        argv = self.base_argv(self.fx.build) + ["--stage", "2", "--stage2-opt", "O1", "--seed", str(seed),
                                                "--reuse-existing"]
        rc1, out1, err1 = self.run_main(argv, smoke_diverge)
        self.assertEqual(rc1, 1, out1 + err1)
        self.assertIn("FAIL stage0-guard: smoke .exe mismatch", err1)
        cached = list(self.cache_dir.glob("*.exe")) if self.cache_dir.is_dir() else []
        self.assertEqual(cached, [], "stage0-guard failure must not publish B into compiler-cache")

        rc2, out2, err2 = self.run_main(argv, smoke_diverge)
        self.assertEqual(rc2, 1, "rerun after stage0-guard failure must still fail:\n" + out2 + err2)

    def test_fixedpoint_oracle_accepts_space_separated_timeout_scale(self):
        fp_dir = TOOLS.parent / "tests" / "selfhost" / "fixedpoint"
        if str(fp_dir) not in sys.path:
            sys.path.insert(0, str(fp_dir))
        import fixedpoint_oracle

        # Passing the documented `--timeout-scale 6` form must not be rejected as a 4th positional arg (rc=2).
        buf, err = io.StringIO(), io.StringIO()
        with mock.patch.object(bootstrap, "verify_no_external_tools_on_path", return_value=(False, "fake-gcc")), \
                contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = fixedpoint_oracle.main(
                [str(self.fx.stage0), str(self.fx.build), str(self.fx.root), "--timeout-scale", "6"]
            )
        self.assertNotEqual(rc, 2, "CLI rejected documented `--timeout-scale N` with usage error:\n" + err.getvalue())
        self.assertEqual(rc, 1, buf.getvalue() + err.getvalue())


if __name__ == "__main__":
    unittest.main()
