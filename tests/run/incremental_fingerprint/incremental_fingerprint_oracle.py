#!/usr/bin/env python3
"""Live incremental fingerprint & red-green oracle for `compiler/incremental/fingerprint/mod.ax` (T757 / E18.2).

1. Bundles `compiler/incremental/fingerprint/mod.ax` (with `compiler/query/db/mod.ax`)
   and `tests/run/incremental_fingerprint/incremental_fingerprint_probe.ax.in` and
   executes the direct `IncrementalEngine` probe in `--interp` and native
   `-O0`, `-O1`, and `-O2 --verify-each` modes, verifying byte-exact
   `--emit=fingerprints` and `--emit=incremental-stats` output across a 6-revision
   red-green pipeline.
2. Runs differential `.ax` tests in `tests/run/incremental_fingerprint/` across
   `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "incremental_fingerprint_probe.ax.in"

INCREMENTAL_FINGERPRINT_BUNDLE_MODULES = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.query.db", "compiler"),
    ("compiler.incremental.fingerprint", "compiler"),
]

POSITIVE_FIXTURES = [
    ("comment_whitespace_insensitivity", "comment_whitespace_insensitivity.ax", "7\n1\n0\n"),
    ("private_body_firewall_red_green", "private_body_firewall_red_green.ax", "0\n0\n0\n1\n0\n0\n"),
    ("signature_abi_invalidation", "signature_abi_invalidation.ax", "1\n0\n1\n"),
]

EXPECTED_ITEM_PREFIXES = [
    "item core_pkg::app.run_app ",
    "item core_pkg::math_lib.Packet ",
    "item core_pkg::math_lib.compute ",
    "item core_pkg::math_lib.fast_add ",
    "item core_pkg::math_lib.secret_helper ",
    "item core_pkg::math_lib.SCALE ",
    "item core_pkg::util.helper_util ",
]

EXPECTED_STATS_LINES = [
    "incremental_stats revision=R6 queries_total=37 queries_green_reused=22 queries_recomputed=15 queries_backdated=0 modules_typechecked=2 cgu_reused=1 cgu_rebuilt=2",
    "node parse_module(core_pkg::app) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node parse_module(core_pkg::math_lib) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=SOURCE_CHANGED",
    "node parse_module(core_pkg::util) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node resolve_module(core_pkg::app) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=API_CHANGED",
    "node resolve_module(core_pkg::math_lib) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node resolve_module(core_pkg::util) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node module_interface(core_pkg::app) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=ABI_CHANGED",
    "node module_interface(core_pkg::math_lib) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=API_CHANGED",
    "node module_interface(core_pkg::util) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node item_signature(core_pkg::app.run_app) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node item_signature(core_pkg::math_lib.Packet) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=SOURCE_CHANGED",
    "node item_signature(core_pkg::math_lib.compute) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=SOURCE_CHANGED",
    "node item_signature(core_pkg::math_lib.fast_add) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node item_signature(core_pkg::math_lib.secret_helper) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node item_signature(core_pkg::math_lib.SCALE) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node item_signature(core_pkg::util.helper_util) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node item_abi(core_pkg::app.run_app) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=ABI_CHANGED",
    "node item_abi(core_pkg::math_lib.Packet) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=SOURCE_CHANGED",
    "node item_abi(core_pkg::math_lib.compute) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=SOURCE_CHANGED",
    "node item_abi(core_pkg::math_lib.fast_add) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node item_abi(core_pkg::math_lib.secret_helper) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node item_abi(core_pkg::math_lib.SCALE) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node item_abi(core_pkg::util.helper_util) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node const_eval(core_pkg::math_lib.SCALE) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node typeck_body(core_pkg::app.run_app) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=API_CHANGED",
    "node typeck_body(core_pkg::math_lib.compute) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=API_CHANGED",
    "node typeck_body(core_pkg::math_lib.fast_add) color=Green verified_at=R6 changed_at=R4 backdated=false miss_reason=NONE",
    "node typeck_body(core_pkg::math_lib.secret_helper) color=Green verified_at=R6 changed_at=R3 backdated=false miss_reason=NONE",
    "node typeck_body(core_pkg::util.helper_util) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node mir_body(core_pkg::app.run_app) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=BODY_CHANGED",
    "node mir_body(core_pkg::math_lib.compute) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=BODY_CHANGED",
    "node mir_body(core_pkg::math_lib.fast_add) color=Green verified_at=R6 changed_at=R4 backdated=false miss_reason=NONE",
    "node mir_body(core_pkg::math_lib.secret_helper) color=Green verified_at=R6 changed_at=R3 backdated=false miss_reason=NONE",
    "node mir_body(core_pkg::util.helper_util) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
    "node codegen_unit(core_pkg::app) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=ABI_CHANGED",
    "node codegen_unit(core_pkg::math_lib) color=Red verified_at=R6 changed_at=R6 backdated=false miss_reason=ABI_CHANGED",
    "node codegen_unit(core_pkg::util) color=Green verified_at=R6 changed_at=R1 backdated=false miss_reason=NONE",
]

ITEM_LINE_RE = re.compile(
    r"^item (\S+) ast=([0-9a-f]{32}) api=([0-9a-f]{32}) abi=([0-9a-f]{32}) body=([0-9a-f]{32}) cgu=([0-9a-f]{32})$"
)


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    exe = ".exe" if os.name == "nt" else ""
    for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
        cand = os.path.join(build_dir, name)
        if os.path.isfile(cand):
            return cand
    return compiler


def run_cmd(cmd: list[str], cwd: str, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def assemble_incremental_fingerprint_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    modules_src = bc.assemble_compiler_modules(INCREMENTAL_FINGERPRINT_BUNDLE_MODULES, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "incremental_fingerprint" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def validate_probe_stdout(stdout_text: str, mode_label: str) -> bool:
    lines = stdout_text.replace("\r\n", "\n").strip().splitlines()
    expected_total = 1 + len(EXPECTED_ITEM_PREFIXES) + len(EXPECTED_STATS_LINES)
    if len(lines) != expected_total:
        sys.stderr.write(
            f"FAIL [{mode_label}]: line count mismatch ({len(lines)} vs {expected_total})\n"
            f"Actual:\n{stdout_text}\n"
        )
        return False

    if lines[0] != "fingerprints revision=R6 items=7":
        sys.stderr.write(f"FAIL [{mode_label}]: unexpected header line: {lines[0]!r}\n")
        return False

    for i, expected_prefix in enumerate(EXPECTED_ITEM_PREFIXES):
        line = lines[1 + i]
        if not line.startswith(expected_prefix):
            sys.stderr.write(
                f"FAIL [{mode_label}]: item line {i} prefix mismatch:\n"
                f"  expected prefix: {expected_prefix!r}\n"
                f"  actual line:     {line!r}\n"
            )
            return False
        m = ITEM_LINE_RE.match(line)
        if not m:
            sys.stderr.write(f"FAIL [{mode_label}]: malformed item fingerprint line: {line!r}\n")
            return False
        ast_fp, api_fp, abi_fp, body_fp, cgu_fp = m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)
        for tier_name, hex_val in (("ast", ast_fp), ("api", api_fp), ("abi", abi_fp), ("body", body_fp), ("cgu", cgu_fp)):
            if hex_val == "0" * 32:
                sys.stderr.write(f"FAIL [{mode_label}]: zero {tier_name} fingerprint in {line!r}\n")
                return False
        if "::val#0::" in line:
            tier_set = {ast_fp, api_fp, abi_fp, body_fp, cgu_fp}
            if len(tier_set) != 5:
                sys.stderr.write(f"FAIL [{mode_label}]: domain collision across tiers in {line!r}\n")
                return False

    stats_lines = lines[1 + len(EXPECTED_ITEM_PREFIXES) :]
    if stats_lines != EXPECTED_STATS_LINES:
        sys.stderr.write(
            f"FAIL [{mode_label}]: incremental_stats mismatch:\n"
            f"--- Expected ---\n" + "\n".join(EXPECTED_STATS_LINES) + "\n"
            f"--- Actual ---\n" + "\n".join(stats_lines) + "\n"
        )
        return False
    return True


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: incremental_fingerprint_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.incremental.fingerprint probe under --interp, -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "incremental_fingerprint_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "incremental_fingerprint_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_incremental_fingerprint_probe(root, probe_template),
        encoding="utf-8",
        newline="\n",
    )

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"incremental_fingerprint_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if not validate_probe_stdout(norm_interp_probe, "--interp"):
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"incremental_fingerprint_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(
                f"build incremental_fingerprint_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n"
            )
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"incremental_fingerprint_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if not validate_probe_stdout(norm_probe, flag):
            return 1
        if norm_probe != norm_interp_probe:
            sys.stderr.write(
                f"stdout mismatch for incremental_fingerprint_probe under {flag}:\nexpected:\n{norm_interp_probe}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, exp_out in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        f_interp = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if f_interp.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {f_interp.returncode}:\n{f_interp.stderr}\n")
            return 1
        if f_interp.stdout.replace("\r\n", "\n") != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under --interp\n")
            return 1

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            if rproc.stdout.replace("\r\n", "\n") != exp_out:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}\n")
                return 1

    sys.stdout.buffer.write(b"INCREMENTAL-FINGERPRINT-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
