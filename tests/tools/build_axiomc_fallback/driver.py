#!/usr/bin/env python3
"""Scenario driver of the T423f tests: `build_axiomc.py` falls back to the full chain when the seed cannot compile.

Usage: driver.py <scenario>. Prints `OK <scenario>` and exits 0 when every assertion held, otherwise prints the
failed expectation plus the captured build output on stderr and exits 1.

No real compiler runs. `bootstrap.run_stage_build` is replaced by a fake stage driver (output bytes depend only on
what a real stage output depends on, so the stage-2 == stage-3 fixed point holds; stage "seedA_*" or a named stage
can be made to fail with a compile error), `bootstrap.load_bundle_text` concatenates the fixture's compiler/*.ax,
`build_axiomc.ensure_stage0` returns a stub axiom0 and `subprocess.run` (the final `version` smoke) is a fake. Every
scenario runs in a temporary directory in milliseconds. Python 3 standard library only.
"""

import contextlib
import hashlib
import io
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[3] / "tools"
sys.path.insert(0, str(TOOLS))
import bootstrap  # noqa: E402
import build_axiomc  # noqa: E402

NOTICE = "bootstrap: seeded A failed, falling back to full chain"
A_FAIL = "bootstrap: FAIL seeded A"
OLD = 1_000_000_000


class Failure(Exception):
    pass


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


class World:
    def __init__(self, tmp):
        self.tmp = Path(tmp)
        self.root = self.tmp / "root"
        self.cache = self.tmp / "compiler-cache"
        self.fail_stage = None  # label prefix (str or tuple) of the stages that fail with a compile error
        self.calls = []
        self.log = []
        write(self.root / "compiler" / "a.ax", "module compiler.a\nfn a() {}\n")
        write(self.root / "compiler" / "sub" / "b.ax", "module compiler.sub.b\nfn b() {}\n")
        write(self.root / "std" / "core" / "x.ax", "module std.core.x\nfn x() {}\n")
        write(self.root / "std" / "axiom.toml", "name = \"std\"\n")
        write(self.root / "stage0.bin", "axiom0 v1\n")

    # -- fakes ---------------------------------------------------------------------------------------------------
    def run_stage_build(self, stage_label, compiler_path, bundle_path, output_path, std_root, stack_reserve,
                        opt_level, time_passes, cwd, env):
        self.calls.append(stage_label.split("_")[0] + ":" + opt_level)
        if self.fail_stage and stage_label.startswith(self.fail_stage):
            res = bootstrap.make_cached_result("stage1_fake", opt_level, str(self.root / "stage0.bin"), cwd)
            res.update(rc=1, stderr="error[AX_FAKE]: unknown host intrinsic `host.fiber_new` (fake seed)", output="",
                       size_bytes=0, sha256="")
            return res
        with open(bundle_path, "rb") as f:
            bundle = f.read()
        std = bootstrap.files_digest(bootstrap.hash_tree(std_root, "std", (".ax", ".toml")))
        lineage = "S1" if stage_label.startswith("stage1") else "S23"
        payload = "%s|%s|%s|%s|%s" % (lineage, hashlib.sha256(bundle).hexdigest(), std, opt_level, stack_reserve)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(payload.encode("utf-8"))
        res = bootstrap.make_cached_result(stage_label, opt_level, output_path, cwd)
        res["cmd"] = ["(fake)", compiler_path]
        return res

    def load_bundle_text(self, root):
        parts = []
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, "compiler")):
            dirnames.sort()
            for fn in sorted(f for f in filenames if f.endswith(".ax")):
                with open(os.path.join(dirpath, fn), "rb") as f:
                    parts.append(f.read().decode("utf-8"))
        return "\n".join(parts)

    def build(self, name, *extra, fail_stage=None):
        """Run build_axiomc.main into build dir `name`; returns (rc, stdout, stderr, calls)."""
        self.fail_stage = fail_stage
        self.calls = []
        out_dir = self.tmp / name
        argv = ["--out", str(out_dir), "--root", str(self.root), "--cache-dir", str(self.cache)] + list(extra)

        class Done:
            returncode = 0
            stdout = b""
            stderr = b""

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(build_axiomc, "ensure_stage0", lambda *a, **k: str(self.root / "stage0.bin")), \
                mock.patch.object(build_axiomc.subprocess, "run", lambda *a, **k: Done()), \
                mock.patch.object(bootstrap, "run_stage_build", self.run_stage_build), \
                mock.patch.object(bootstrap, "load_bundle_text", self.load_bundle_text), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = build_axiomc.main(argv)
        self.log.append("--- build %s %s -> rc=%s\n%s\n[stderr]\n%s" % (name, " ".join(extra), rc, out.getvalue(), err.getvalue()))
        return rc, out.getvalue(), err.getvalue(), list(self.calls)

    def cached(self):
        return sorted(p.name for p in self.cache.glob("axiomc2_O1_*.exe"))

    def seed_from_v1_then_edit_sources(self):
        """Populate the compiler cache from the v1 sources, then change a source (the 'new task change set')."""
        rc, out, err, calls = self.build("build_v1", "--seed", "auto")
        expect(rc == 0, "v1 priming build failed: rc=%s" % rc)
        expect(calls == ["stage1:default", "stage2:O1"], "v1 priming calls: %s" % calls)
        expect(len(self.cached()) == 1, "v1 build must populate the cache: %s" % self.cached())
        a = self.root / "compiler" / "a.ax"
        write(a, "module compiler.a\nfn a() -> i32 { 42 }\n")
        os.utime(str(a), (OLD, OLD))
        return next(self.cache.glob("axiomc2_O1_*.exe"))


def expect(cond, msg):
    if not cond:
        raise Failure(msg)


# -- scenarios -----------------------------------------------------------------------------------------------------
def s_auto_seed_fails(w):
    """Default (auto) seed that cannot compile the new sources: fallback runs the full chain and reports it."""
    w.seed_from_v1_then_edit_sources()
    rc, out, err, calls = w.build("build_v2", fail_stage="seedA")
    expect(rc == 0, "fallback build must succeed, rc=%s" % rc)
    expect(out.count(NOTICE) == 1, "fallback notice must be printed exactly once, got %d" % out.count(NOTICE))
    expect(A_FAIL in err, "the original seeded A failure stays visible on stderr")
    expect("SEED: hit" in out, "the seed was used first")
    # stage1 is reused by the rerun; the full chain then builds c2 (build_axiomc builds --stage 2)
    expect(calls == ["stage1:default", "seedA:O1", "stage2:O1"], "calls: %s" % calls)
    expect("BUILD-AXIOMC OK" in out, "build must finish OK")
    expect(len(w.cached()) == 2, "the full-chain compiler becomes the new cached seed: %s" % w.cached())
    # the new cached seed is the next build's seed: a third build is seeded again with no fallback
    write(w.root / "compiler" / "sub" / "b.ax", "module compiler.sub.b\nfn b() -> i32 { 7 }\n")
    rc3, out3, err3, calls3 = w.build("build_v3")
    expect(rc3 == 0 and NOTICE not in out3, "third build works without fallback: rc=%s" % rc3)
    expect("seedA:O1" in calls3, "third build is seeded again: %s" % calls3)


def s_auto_literal_seed_fails(w):
    """A literal `--seed auto` is the same policy as the default: it falls back too."""
    w.seed_from_v1_then_edit_sources()
    rc, out, err, calls = w.build("build_v2", "--seed", "auto", fail_stage="seedA")
    expect(rc == 0, "rc=%s" % rc)
    expect(out.count(NOTICE) == 1, "notice count %d" % out.count(NOTICE))
    expect(calls == ["stage1:default", "seedA:O1", "stage2:O1"], "calls: %s" % calls)


def s_explicit_seed_fails(w):
    """An explicit --seed <path> that cannot compile the new sources keeps failing hard, no fallback."""
    seed = w.seed_from_v1_then_edit_sources()
    rc, out, err, calls = w.build("build_v2", "--seed", str(seed), fail_stage="seedA")
    expect(rc != 0, "explicit seed failure must exit non-zero, rc=%s" % rc)
    expect(A_FAIL in err, "seeded A failure reported on stderr")
    expect(NOTICE not in out and NOTICE not in err, "no fallback notice for an explicit seed")
    expect(calls == ["stage1:default", "seedA:O1"], "no full chain after an explicit seed failure: %s" % calls)
    expect("BUILD-AXIOMC OK" not in out, "no success line")
    expect(len(w.cached()) == 1, "cache untouched: %s" % w.cached())


def s_seed_works(w):
    """A seed that compiles the new sources: seeded A/B/C, no fallback."""
    w.seed_from_v1_then_edit_sources()
    rc, out, err, calls = w.build("build_v2")
    expect(rc == 0, "rc=%s" % rc)
    expect(NOTICE not in out and NOTICE not in err, "no fallback notice when the seed works")
    expect(A_FAIL not in err, "no failure output")
    expect(calls == ["stage1:default", "seedA:O1", "stage2:O1", "stage3:O1"], "calls: %s" % calls)
    expect("[seeded B==C]" in out, "seeded fixed point reported")


def s_later_seeded_stage_failure_is_not_retried(w):
    """Only seeded A falls back: A ok but B (A -> B) failing is a real failure and stays one."""
    w.seed_from_v1_then_edit_sources()
    rc, out, err, calls = w.build("build_v2", fail_stage="stage2_seedA_to_B")
    expect(rc != 0, "seeded B failure must exit non-zero, rc=%s" % rc)
    expect("bootstrap: FAIL seeded B" in err, "seeded B failure reported: %s" % err)
    expect(NOTICE not in out and NOTICE not in err, "no fallback notice for a B failure")
    expect(calls == ["stage1:default", "seedA:O1", "stage2:O1"], "no full chain after a B failure: %s" % calls)


def s_stage1_failure_is_not_a_seed_failure(w):
    """A stage-1 (axiom0 -> axiomc1) failure happens before any seed is used: no fallback, non-zero exit."""
    w.seed_from_v1_then_edit_sources()
    rc, out, err, calls = w.build("build_v2", fail_stage="stage1")
    expect(rc != 0, "rc=%s" % rc)
    expect("bootstrap: FAIL stage1" in err, "stage-1 failure reported: %s" % err)
    expect(NOTICE not in out and NOTICE not in err, "a stage-1 failure is not a seeded A failure")
    expect(calls == ["stage1:default"], "calls: %s" % calls)


def s_fallback_then_chain_stage_fails(w):
    """Seeded A fails, the full chain's stage 2 fails too: one notice, non-zero exit, both failures on stderr."""
    w.seed_from_v1_then_edit_sources()
    rc, out, err, calls = w.build("build_v2", fail_stage=("seedA", "stage2_axiomc1"))
    expect(rc != 0, "rc=%s" % rc)
    expect(out.count(NOTICE) == 1, "one notice")
    expect(A_FAIL in err and "bootstrap: FAIL stage2" in err, "both failures on stderr: %s" % err)
    expect(calls == ["stage1:default", "seedA:O1", "stage2:O1"], "calls: %s" % calls)
    expect("BUILD-AXIOMC OK" not in out, "no success line")
    expect(len(w.cached()) == 1, "a failed chain publishes no seed: %s" % w.cached())


def s_full_chain_never_falls_back(w):
    """--full-chain is not seeded at all: no seed lookup, no notice."""
    w.seed_from_v1_then_edit_sources()
    rc, out, err, calls = w.build("build_v2", "--full-chain", fail_stage="seedA")
    expect(rc == 0, "rc=%s" % rc)
    expect(NOTICE not in out and "SEED:" not in out, "no seeded mode, no notice")
    expect(calls == ["stage1:default", "stage2:O1"], "calls: %s" % calls)


def s_force_never_seeds_or_falls_back(w):
    """--force disables seeded mode (QA T423f adversarial): no seed lookup, no seeded A, no notice."""
    w.seed_from_v1_then_edit_sources()
    rc, out, err, calls = w.build("build_v2", "--force", fail_stage="seedA")
    expect(rc == 0, "rc=%s" % rc)
    expect(NOTICE not in out and NOTICE not in err and "SEED:" not in out, "no seeded mode, no notice")
    expect(calls == ["stage1:default", "stage2:O1"], "calls: %s" % calls)


SCENARIOS = {
    "force_never_seeds_or_falls_back": s_force_never_seeds_or_falls_back,
    "auto_seed_fails": s_auto_seed_fails,
    "auto_literal_seed_fails": s_auto_literal_seed_fails,
    "explicit_seed_fails": s_explicit_seed_fails,
    "seed_works": s_seed_works,
    "later_seeded_stage_failure_is_not_retried": s_later_seeded_stage_failure_is_not_retried,
    "stage1_failure_is_not_a_seed_failure": s_stage1_failure_is_not_a_seed_failure,
    "fallback_then_chain_stage_fails": s_fallback_then_chain_stage_fails,
    "full_chain_never_falls_back": s_full_chain_never_falls_back,
}


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(newline="\n")
        except Exception:
            pass
    if len(argv) != 2 or argv[1] not in SCENARIOS:
        print("usage: driver.py <%s>" % "|".join(sorted(SCENARIOS)), file=sys.stderr)
        return 2
    name = argv[1]
    with tempfile.TemporaryDirectory(prefix="t423f_") as tmp:
        w = World(tmp)
        try:
            SCENARIOS[name](w)
        except Failure as exc:
            print("FAIL %s: %s" % (name, exc), file=sys.stderr)
            print("\n".join(w.log), file=sys.stderr)
            return 1
    sys.stdout.write("OK %s\n" % name)  # LF on every platform (the manifest compares exact bytes)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
