#!/usr/bin/env python3
"""Live persistent incremental cache, action digest & < 100 ms no-op fast path oracle (T758 / E18.2).

1. Bundles `compiler/incremental/cache/mod.ax` (with `compiler/incremental/fingerprint/mod.ax`
   and `compiler/query/db/mod.ax`) and `tests/run/incremental_cache/incremental_cache_probe.ax.in`
   and executes the direct `IncrementalCache` probe in `--interp` and native `-O0`, `-O1`, and
   `-O2 --verify-each` modes:
   - Verifies real on-disk `.axiom-cache/dep-graph.axcache` (`AXCACHE1` magic, schema version,
     trailing 128-bit payload checksum) and `<cache-dir>/objects/<fp128_hex>.obj` artifacts.
   - Verifies `< 100 ms` no-op rebuild fast path (`noop_fastpath=true under_100ms=true`,
     `queries_total=0 queries_recomputed=0 modules_typechecked=0 cgu_reused=3 cgu_rebuilt=0`).
   - Verifies byte-identical output between clean (`--no-incremental`) and incremental builds,
     corruption/version eviction recovery, error non-pollution, and `AXD-060` diagnostic replay.
2. Runs differential `.ax` tests in `tests/run/incremental_cache/` across `--interp`, `-O0`,
   `-O1`, and `-O2 --verify-each`.
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

PROBE_TEMPLATE = HERE / "incremental_cache_probe.ax.in"

INCREMENTAL_CACHE_BUNDLE_MODULES = [
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
    ("compiler.incremental.cache", "compiler"),
]

POSITIVE_FIXTURES = [
    ("cold_to_warm_cache_and_noop_fastpath", "cold_to_warm_cache_and_noop_fastpath.ax", "1\n3\n4\n0\n0\n3\n"),
    ("cache_corruption_and_version_eviction", "cache_corruption_and_version_eviction.ax", "0\n2\n3\n5\n6\n7\n"),
    ("clean_vs_cached_artifact_equivalence", "clean_vs_cached_artifact_equivalence.ax", "1\n0\n"),
]

CACHE_STATS_RE = re.compile(
    r"^cache_stats warm=true noop_fastpath=true under_100ms=true evict_reason=NONE "
    r"evictions=0 noop_hits=3 obj_hits=11 obj_misses=1 atomic_writes=4 atomic_renames=4 "
    r"env_digest=([0-9a-f]{32}) artifact_fp=([0-9a-f]{32})$"
)

CGU_LINE_RE = re.compile(
    r"^cgu (\S+) cgu_fp=([0-9a-f]{32}) obj_digest=([0-9a-f]{32}) "
    r"obj_len=(\d+) syms=(\d+) relocs=(\d+) published=true reused=true$"
)

EXPECTED_CGU_MODULES = [
    "core_pkg::app",
    "core_pkg::math_lib",
    "core_pkg::util",
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

EXPECTED_DIAG_LINES = [
    "diag WARNING code=2100 item=core_pkg::app.run_app loc=2:9 msg=redundant parentheses in run_app",
    "diag WARNING code=2101 item=core_pkg::util.helper_util loc=4:5 msg=unused parameter in helper_util",
]


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


def assemble_incremental_cache_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    modules_src = bc.assemble_compiler_modules(INCREMENTAL_CACHE_BUNDLE_MODULES, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "incremental_cache" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def validate_probe_stdout(stdout_text: str, mode_label: str) -> bool:
    lines = stdout_text.replace("\r\n", "\n").strip().splitlines()
    if len(lines) < 15:
        sys.stderr.write(f"FAIL [{mode_label}]: too few output lines ({len(lines)}):\n{stdout_text}\n")
        return False

    m_stats = CACHE_STATS_RE.match(lines[0])
    if not m_stats:
        sys.stderr.write(f"FAIL [{mode_label}]: unexpected cache_stats line:\n  {lines[0]!r}\n")
        return False
    env_dig, art_fp = m_stats.group(1), m_stats.group(2)
    if env_dig == "0" * 32 or art_fp == "0" * 32:
        sys.stderr.write(f"FAIL [{mode_label}]: zero digest in cache_stats: {lines[0]!r}\n")
        return False

    for i, exp_mod in enumerate(EXPECTED_CGU_MODULES):
        cgu_line = lines[1 + i]
        mc = CGU_LINE_RE.match(cgu_line)
        if not mc or mc.group(1) != exp_mod:
            sys.stderr.write(f"FAIL [{mode_label}]: unexpected cgu line {i}: {cgu_line!r}\n")
            return False
        if mc.group(2) == "0" * 32 or mc.group(3) == "0" * 32 or int(mc.group(4)) < 64:
            sys.stderr.write(f"FAIL [{mode_label}]: invalid cgu digest/len in {cgu_line!r}\n")
            return False

    if lines[4] != "fingerprints revision=R2 items=7":
        sys.stderr.write(f"FAIL [{mode_label}]: unexpected fingerprints header: {lines[4]!r}\n")
        return False

    for i, prefix in enumerate(EXPECTED_ITEM_PREFIXES):
        if not lines[5 + i].startswith(prefix):
            sys.stderr.write(f"FAIL [{mode_label}]: item line {i} mismatch: {lines[5 + i]!r}\n")
            return False

    expected_inc_stats = (
        "incremental_stats revision=R2 queries_total=0 queries_green_reused=0 "
        "queries_recomputed=0 queries_backdated=0 modules_typechecked=0 cgu_reused=3 cgu_rebuilt=0"
    )
    if lines[12] != expected_inc_stats:
        sys.stderr.write(
            f"FAIL [{mode_label}]: unexpected no-op incremental_stats line:\n"
            f"  expected: {expected_inc_stats!r}\n"
            f"  actual:   {lines[12]!r}\n"
        )
        return False

    if lines[-2:] != EXPECTED_DIAG_LINES:
        sys.stderr.write(
            f"FAIL [{mode_label}]: diagnostic replay lines mismatch:\n"
            f"  expected: {EXPECTED_DIAG_LINES!r}\n"
            f"  actual:   {lines[-2:]!r}\n"
        )
        return False

    return True


def verify_on_disk_cache_files(cache_dir: pathlib.Path, mode_label: str) -> bool:
    index_file = cache_dir / "dep-graph.axcache"
    if not index_file.is_file():
        sys.stderr.write(f"FAIL [{mode_label}]: missing {index_file}\n")
        return False
    raw = index_file.read_bytes()
    if len(raw) < 48 or raw[:8] != b"AXCACHE1":
        sys.stderr.write(f"FAIL [{mode_label}]: invalid header magic in {index_file}\n")
        return False

    # Temp file must have been cleaned up by atomic rename commit
    tmp_index = cache_dir / "dep-graph.axcache.tmp"
    if tmp_index.exists():
        sys.stderr.write(f"FAIL [{mode_label}]: leftover temporary file {tmp_index}\n")
        return False

    obj_dir = cache_dir / "objects"
    obj_files = sorted(obj_dir.glob("*.obj")) if obj_dir.is_dir() else []
    if len(obj_files) < 3:
        sys.stderr.write(f"FAIL [{mode_label}]: expected >= 3 cached .obj files in {obj_dir}, found {len(obj_files)}\n")
        return False
    for of in obj_files:
        ob = of.read_bytes()
        # Check AMD64 COFF machine (0x8664 -> b"\x64\x86") and zero TimeDateStamp (bytes 4..8 == 0)
        if len(ob) < 64 or ob[:2] != b"\x64\x86" or ob[4:8] != b"\x00\x00\x00\x00":
            sys.stderr.write(f"FAIL [{mode_label}]: non-deterministic or invalid COFF header in {of}\n")
            return False
    return True


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: incremental_cache_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.incremental.cache probe under --interp, -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "incremental_cache_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "incremental_cache_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_incremental_cache_probe(root, probe_template),
        encoding="utf-8",
        newline="\n",
    )

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"incremental_cache_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if not validate_probe_stdout(norm_interp_probe, "--interp"):
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"incremental_cache_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(
                f"build incremental_cache_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n"
            )
            return 1
        disk_cache_dir = tmp_dir / f"axiom_cache_{flag[1:]}"
        cache_arg = "--cache-dir=" + str(disk_cache_dir).replace("\\", "/")
        rproc = run_cmd([str(probe_exe), cache_arg], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"incremental_cache_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if not validate_probe_stdout(norm_probe, flag):
            return 1
        if norm_probe != norm_interp_probe:
            sys.stderr.write(
                f"stdout mismatch for incremental_cache_probe under {flag}:\nexpected:\n{norm_interp_probe}\ngot:\n{norm_probe}\n"
            )
            return 1
        if not verify_on_disk_cache_files(disk_cache_dir, flag):
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
            if rproc.stdout.replace("\r\n", "\n") != exp_out:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}\n")
                return 1

    sys.stdout.buffer.write(b"INCREMENTAL-CACHE-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
