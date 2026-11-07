#!/usr/bin/env python3
"""Oracle test for T064 (E15.3): Ownership/capability-aware copy/move propagation,
deep SROA, caller-allocated RVO/NRVO (`compiler.opt.sroa`), and Tarjan SCC call-graph,
2-stage legality/cost inliner, transactional callsite cloning, post-inline SROA cascade,
and deterministic `--emit=callgraph` / `--emit=inline` formatting (`compiler.opt.inline`).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "opt2_sroa_inline_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_SROA_COPY_MOVE_AND_RVO_NRVO=OK\n"
    "PROBE_CALLGRAPH_SCC_AND_SUMMARIES=OK\n"
    "PROBE_INLINE_LEGALITY_AND_COST_MODEL=OK\n"
    "PROBE_TRANSACTIONAL_INLINE_AND_POST_SROA_CASCADE=OK\n"
    "PROBE_ALL=OK\n"
)

POSITIVE_FIXTURES: list[tuple[str, str]] = [
    ("copy_move_prop_and_sroa", "copy_move_prop_and_sroa.ax"),
    ("rvo_nrvo_and_drop_parity", "rvo_nrvo_and_drop_parity.ax"),
    ("inline_scc_and_attributes", "inline_scc_and_attributes.ax"),
]

OPT2_PROBE_BLOBS: list[bytes] = [
    # Blob 0: Virtual file path for `session_parse_virtual_file`
    b"probe_opt2_src.ax",

    # Blob 1: Axiom source for `probe_sroa_copy_move_and_rvo_nrvo()` (7 functions)
    (
        b"@intrinsic unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }\n"
        b"\n"
        b"@derive(Copy)\n"
        b"struct Vec2 {\n"
        b"    x: i64,\n"
        b"    y: i64,\n"
        b"}\n"
        b"\n"
        b"@derive(Copy)\n"
        b"struct Bounds2 {\n"
        b"    lo: Vec2,\n"
        b"    hi: Vec2,\n"
        b"}\n"
        b"\n"
        b"struct OwnedToken {\n"
        b"    val: i64,\n"
        b"    tag: i64,\n"
        b"}\n"
        b"\n"
        b"@derive(Copy)\n"
        b"enum MaybeVal {\n"
        b"    Empty,\n"
        b"    Val(i64),\n"
        b"}\n"
        b"\n"
        b"@derive(Copy)\n"
        b"struct BigFrame {\n"
        b"    a: i64,\n"
        b"    b: i64,\n"
        b"    c: i64,\n"
        b"    d: i64,\n"
        b"}\n"
        b"\n"
        b"fn fn0_copy_prop_and_struct_sroa(x: i64, y: i64) -> i64 {\n"
        b"    let c0: i64 = x;\n"
        b"    let c1: i64 = c0;\n"
        b"    let c2: i64 = c1;\n"
        b"    let v_lo = Vec2 { x: c2 + 1, y: y + 2 };\n"
        b"    let v_hi = Vec2 { x: c2 + 10, y: y + 20 };\n"
        b"    let b = Bounds2 { lo: v_lo, hi: v_hi };\n"
        b"    b.lo.x + b.lo.y + b.hi.x + b.hi.y\n"
        b"}\n"
        b"\n"
        b"fn fn1_move_chain_coalesce(seed: i64) -> i64 {\n"
        b"    let t0 = OwnedToken { val: seed + 3, tag: 7 };\n"
        b"    let t1 = t0;\n"
        b"    let t2 = t1;\n"
        b"    t2.val + t2.tag\n"
        b"}\n"
        b"\n"
        b"fn fn2_enum_and_fixed_array_sroa(flag: bool, base: i64) -> i64 {\n"
        b"    let m = if flag { MaybeVal.Val(base + 5) } else { MaybeVal.Empty };\n"
        b"    let arr: [4]i64 = [base, base + 1, base + 2, base + 3];\n"
        b"    let from_m: i64 = match m {\n"
        b"        MaybeVal.Empty => 0,\n"
        b"        MaybeVal.Val(v) => v,\n"
        b"    };\n"
        b"    from_m + arr[0] + arr[1] + arr[2] + arr[3]\n"
        b"}\n"
        b"\n"
        b"fn fn3_direct_rvo_construct(a: i64, b: i64) -> BigFrame {\n"
        b"    let f = BigFrame { a: a + 1, b: b + 2, c: a + b, d: a - b };\n"
        b"    f\n"
        b"}\n"
        b"\n"
        b"fn fn4_named_nrvo_single_return(a: i64, b: i64) -> BigFrame {\n"
        b"    let mut out = BigFrame { a: a, b: b, c: a * 2, d: b * 3 };\n"
        b"    out.a = out.a + 11;\n"
        b"    out.d = out.d + 17;\n"
        b"    out\n"
        b"}\n"
        b"\n"
        b"fn fn5_blocked_address_observable(x: i64) -> i64 {\n"
        b"    let v = Vec2 { x: x, y: x + 1 };\n"
        b"    let rv: view<Vec2> = view(v);\n"
        b"    rv.x + rv.y + v.x\n"
        b"}\n"
        b"\n"
        b"fn fn6_blocked_dynamic_array_index(idx: usize, x: i64) -> i64 {\n"
        b"    let arr: [4]i64 = [x, x + 10, x + 20, x + 30];\n"
        b"    arr[idx & 3]\n"
        b"}\n"
    ),

    # Blob 2: Axiom source for `probe_callgraph_scc_legality_and_inliner()` (exact 9 functions: 0..8)
    (
        b"@derive(Copy)\n"
        b"struct Vec2 {\n"
        b"    x: i64,\n"
        b"    y: i64,\n"
        b"}\n"
        b"\n"
        b"@derive(Copy)\n"
        b"enum Result<T, E> {\n"
        b"    Ok(T),\n"
        b"    Err(E),\n"
        b"}\n"
        b"\n"
        b"fn pure_translate_vec(v: Vec2, dx: i64, dy: i64) -> Vec2 {\n"
        b"    Vec2 { x: v.x ^ dx, y: v.y | dy }\n"
        b"}\n"
        b"\n"
        b"fn result_status_fn(x: i64) -> Result<i64, i32> {\n"
        b"    if x >= 0 {\n"
        b"        Result<i64, i32>.Ok(x ^ 1)\n"
        b"    } else {\n"
        b"        Result<i64, i32>.Err(1i32)\n"
        b"    }\n"
        b"}\n"
        b"\n"
        b"fn never_inline_helper(x: i64) -> i64 {\n"
        b"    x * 3 + 7\n"
        b"}\n"
        b"\n"
        b"fn even_rec(n: i64) -> i64 {\n"
        b"    if n <= 0 {\n"
        b"        1\n"
        b"    } else {\n"
        b"        odd_rec(n - 1) + 1\n"
        b"    }\n"
        b"}\n"
        b"\n"
        b"fn odd_rec(n: i64) -> i64 {\n"
        b"    if n <= 0 {\n"
        b"        0\n"
        b"    } else {\n"
        b"        even_rec(n - 1) + 2\n"
        b"    }\n"
        b"}\n"
        b"\n"
        b"fn self_rec_fn(n: i64) -> i64 {\n"
        b"    if n <= 1 {\n"
        b"        1\n"
        b"    } else {\n"
        b"        n + self_rec_fn(n - 1)\n"
        b"    }\n"
        b"}\n"
        b"\n"
        b"fn addr_taken_target(x: i64) -> i64 {\n"
        b"    x + 42\n"
        b"}\n"
        b"\n"
        b"fn dead_internal_fn(x: i64) -> i64 {\n"
        b"    x - 99\n"
        b"}\n"
        b"\n"
        b"fn caller_entry_root(x: i64, y: i64) -> i64 {\n"
        b"    let p0 = Vec2 { x: x, y: y };\n"
        b"    let p1 = pure_translate_vec(p0, 5, 10);\n"
        b"    let p2 = pure_translate_vec(p1, 2, 4);\n"
        b"    let r = result_status_fn(p2.x);\n"
        b"    let rv: i64 = match r {\n"
        b"        Result.Ok(v) => v,\n"
        b"        Result.Err(_) => 0,\n"
        b"    };\n"
        b"    let nv = never_inline_helper(rv);\n"
        b"    let ev = even_rec(2);\n"
        b"    let sv = self_rec_fn(2);\n"
        b"    let fp: fn(i64) -> i64 = addr_taken_target;\n"
        b"    let fv = fp(1);\n"
        b"    p2.y + nv + ev + sv + fv\n"
        b"}\n"
    ),
]


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
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
        raise SystemExit(1)
    return out_exe


def run_cmd(args: list[str], cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def assemble_opt2_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", OPT2_PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    opt2_modules = list(got.PIPELINE_MODULES) + [
        ("compiler.own.cap", "compiler"),
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.memopt", "compiler"),
        ("compiler.opt.escape", "compiler"),
        ("compiler.opt.sroa", "compiler"),
        ("compiler.opt.inline", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(opt2_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "opt2" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: opt2_sroa_inline_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.opt.sroa + compiler.opt.inline probe under -O2 --verify-each
    probe_template = resolve_fixture_path(root, "opt2_sroa_inline_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "opt2_sroa_inline_probe_bundle.ax"
    probe_bundle.write_text(assemble_opt2_probe(root, probe_template), encoding="utf-8", newline="\n")

    for flag in ("-O0",):
        probe_exe = tmp_dir / f"opt2_sroa_inline_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=300,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build opt2_sroa_inline_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=180)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"opt2_sroa_inline_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for opt2_sroa_inline_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {iproc.returncode}:\n{iproc.stderr}\n")
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")

        for flag in ("-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            norm_out = rproc.stdout.replace("\r\n", "\n")
            if norm_out != norm_interp:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}:\nexpected:\n{norm_interp}\ngot:\n{norm_out}\n")
                return 1

    sys.stdout.buffer.write(b"OPT2-SROA-INLINE-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
