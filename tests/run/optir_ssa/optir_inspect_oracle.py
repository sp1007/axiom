#!/usr/bin/env python3
"""End-to-end oracle for `inspect --emit=optir` and `inspect --emit=memssa` (T601 / E15.1)."""

import os
import subprocess
import sys


def get_axiomc(compiler, build_dir, tmp_dir, root):
    base = os.path.basename(compiler).lower()
    if base.startswith("axiomc"):
        return compiler
    for cand in ("axiomc2.exe", "axiomc1.exe", "axiomc.exe", "axiomc2", "axiomc1", "axiomc"):
        p = os.path.join(build_dir, cand)
        if os.path.isfile(p):
            return p
    sys.path.insert(0, os.path.join(root, "tests", "selfhost", "obj_link_driver"))
    import gen_obj_link_driver_tests as gen  # noqa: E402

    bundle_ax = os.path.join(tmp_dir, "axiomc_bundle.ax")
    with open(bundle_ax, "wb") as f:
        f.write(gen.axiomc_bundle_text().encode("utf-8"))
    out_exe = os.path.join(tmp_dir, "axiomc.exe" if os.name == "nt" else "axiomc")
    cmd = [compiler, "build", "--stack-reserve=67108864", "-o", out_exe, bundle_ax]
    r = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if r.returncode != 0:
        sys.stderr.write("failed to build axiomc:\n" + r.stderr.decode("utf-8", "replace"))
        sys.exit(1)
    return out_exe


def run_cmd(exe, args, root):
    return subprocess.run([exe] + args, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)


def assert_contains(text, needles, label):
    for n in needles:
        if n not in text:
            sys.stderr.write("FAIL %s: missing %r in:\n%s\n" % (label, n, text))
            sys.exit(1)


def main():
    if len(sys.argv) < 5:
        sys.stderr.write("usage: optir_inspect_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2
    compiler, build_dir, tmp_dir, root = sys.argv[1:5]
    axiomc = get_axiomc(compiler, build_dir, tmp_dir, root)

    ax_file = "tests/run/optir_ssa/diamond_loop_sroa.ax"
    ax_edges = "tests/run/optir_ssa/nested_cfg_memssa_sroa_edges.ax"
    mir_ok = "tests/run/optir_ssa/fixtures/verified_sample.mir"
    mir_bad = "tests/run/optir_ssa/fixtures/unverified_bad.mir"

    # 1. inspect --emit=optir on .ax source (and determinism check)
    r1 = run_cmd(axiomc, ["inspect", "--emit=optir", "--verify-each", ax_file], root)
    r1b = run_cmd(axiomc, ["inspect", "--emit=optir", "--verify-each", ax_file], root)
    if r1.returncode != 0 or r1.stdout != r1b.stdout:
        sys.stderr.write("FAIL ax optir: rc=%d stderr=%s\n" % (r1.returncode, r1.stderr.decode("utf-8", "replace")))
        return 1
    out1 = r1.stdout.decode("utf-8", "replace")
    assert_contains(out1, ["optir_body", "idom: bb0", "df: [", "phi(", "proof #"], "ax --emit=optir")

    # 2. inspect --emit=memssa on .ax source (and determinism check)
    r2 = run_cmd(axiomc, ["inspect", "--emit=memssa", "--verify-each", ax_file], root)
    r2b = run_cmd(axiomc, ["inspect", "--emit=memssa", "--verify-each", ax_file], root)
    if r2.returncode != 0 or r2.stdout != r2b.stdout:
        sys.stderr.write("FAIL ax memssa: rc=%d stderr=%s\n" % (r2.returncode, r2.stderr.decode("utf-8", "replace")))
        return 1
    out2 = r2.stdout.decode("utf-8", "replace")
    assert_contains(out2, ["memssa_body", "mem0 = LiveOnEntry", "MemoryDef(", "MemoryUse("], "ax --emit=memssa")

    # 2b. QA boundary check: nested CFG + AliasInfo/RangeInfo certainty proofs + MemorySSA
    r1e = run_cmd(axiomc, ["inspect", "--emit=optir", "--verify-each", ax_edges], root)
    r1eb = run_cmd(axiomc, ["inspect", "--emit=optir", "--verify-each", ax_edges], root)
    if r1e.returncode != 0 or r1e.stdout != r1eb.stdout:
        sys.stderr.write("FAIL ax_edges optir: rc=%d stderr=%s\n" % (r1e.returncode, r1e.stderr.decode("utf-8", "replace")))
        return 1
    out1e = r1e.stdout.decode("utf-8", "replace")
    assert_contains(
        out1e,
        [
            "optir_body",
            "[memory]",
            "MemoryPhi(",
            "idom: bb0",
            "df: [",
            "phi(",
            "prop=NoAlias certainty=Proven analysis=AliasInfo",
            "prop=NonZero certainty=Proven analysis=RangeInfo",
        ],
        "ax_edges --emit=optir",
    )

    r2e = run_cmd(axiomc, ["inspect", "--emit=memssa", "--verify-each", ax_edges], root)
    r2eb = run_cmd(axiomc, ["inspect", "--emit=memssa", "--verify-each", ax_edges], root)
    if r2e.returncode != 0 or r2e.stdout != r2eb.stdout:
        sys.stderr.write("FAIL ax_edges memssa: rc=%d stderr=%s\n" % (r2e.returncode, r2e.stderr.decode("utf-8", "replace")))
        return 1
    out2e = r2e.stdout.decode("utf-8", "replace")
    assert_contains(out2e, ["memssa_body", "mem0 = LiveOnEntry", "MemoryPhi(", "MemoryDef(", "MemoryUse("], "ax_edges --emit=memssa")

    # 3. inspect --emit=optir on verified .mir input
    r3 = run_cmd(axiomc, ["inspect", "--emit=optir", "--verify-each", mir_ok], root)
    if r3.returncode != 0:
        sys.stderr.write("FAIL mir optir: rc=%d stderr=%s\n" % (r3.returncode, r3.stderr.decode("utf-8", "replace")))
        return 1
    out3 = r3.stdout.decode("utf-8", "replace")
    assert_contains(
        out3,
        [
            "optir_body",
            "local _4: type#1 [sroa]",
            "local _7: type#8 [memory]",
            "idom: bb0",
            "df: [bb3]",
            "phi(",
            "proof #",
        ],
        "mir --emit=optir",
    )

    # 4. inspect --emit=memssa on verified .mir input
    r4 = run_cmd(axiomc, ["inspect", "--emit=memssa", "--verify-each", mir_ok], root)
    if r4.returncode != 0:
        sys.stderr.write("FAIL mir memssa: rc=%d stderr=%s\n" % (r4.returncode, r4.stderr.decode("utf-8", "replace")))
        return 1
    out4 = r4.stdout.decode("utf-8", "replace")
    assert_contains(
        out4,
        [
            "memssa_body",
            "mem0 = LiveOnEntry",
            "MemoryPhi(",
            "MemoryDef(",
            "MemoryUse(mem3) [clobber: mem2, region: _7]",
        ],
        "mir --emit=memssa",
    )

    # 5. Negative test: unverified .mir must be rejected before OptIR / MemorySSA lowering
    r5 = run_cmd(axiomc, ["inspect", "--emit=optir", mir_bad], root)
    r6 = run_cmd(axiomc, ["inspect", "--emit=memssa", mir_bad], root)
    if r5.returncode != 1 or len(r5.stdout) != 0 or r6.returncode != 1 or len(r6.stdout) != 0:
        sys.stderr.write("FAIL negative unverified mir: r5=%d r6=%d\n" % (r5.returncode, r6.returncode))
        return 1

    sys.stdout.buffer.write(b"OPTIR-INSPECT-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
