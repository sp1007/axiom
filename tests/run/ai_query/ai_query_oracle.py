#!/usr/bin/env python3
"""Oracle and direct `std.meta_effects` + `compiler.ai_query` +
`compiler.driver.query_cmd` probe runner for T814 (E19.4 AI-agent semantic fact
graph exporter, layout/container/std effect metadata inspector & `.axmeta`
separation; `SPEC-103`, `SPEC-24`, `REQ-TOOL-004`, `REQ-TOOL-180..182`,
`REQ-TOOL-185..187`, `REQ-TOOL-190`, `INV-DIAG-010`).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "ai_query_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[layout_and_protocol] domain_ok=true human_ok=true json_ok=true wasm_ok=true\n"
    "probe[queries_and_gates] queries_ok=true axmeta_ok=true patch_gate_ok=true pe_strip_ok=true\n"
    "AI-QUERY-PROBE-OK\n"
)

POSITIVE_FIXTURES = [
    (
        "layout_and_container_meta",
        "layout_and_container_meta.ax",
        "LAYOUT-AND-CONTAINER-META-OK\n",
    ),
    (
        "semantic_fact_graph_and_effects",
        "semantic_fact_graph_and_effects.ax",
        "SEMANTIC-FACT-GRAPH-AND-EFFECTS-OK\n",
    ),
    (
        "ai_patch_gate_and_axmeta_strip",
        "ai_patch_gate_and_axmeta_strip.ax",
        "AI-PATCH-GATE-AND-AXMETA-STRIP-OK\n",
    ),
]

AI_QUERY_BUNDLE_MODULES = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.diag.json", "compiler"),
    ("compiler.query.db", "compiler"),
    ("compiler.diag.ux2", "compiler"),
    ("compiler.ai_query", "compiler"),
    ("compiler.driver.query_cmd", "compiler"),
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


def assemble_ai_query_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    meta_effects_path = pathlib.Path(root) / "std" / "meta_effects" / "mod.ax"
    if not meta_effects_path.is_file():
        meta_effects_path = REPO_ROOT / "std" / "meta_effects" / "mod.ax"
    meta_effects_src = meta_effects_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    modules_src = bc.assemble_compiler_modules(AI_QUERY_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + meta_effects_src + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "ai_query" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: ai_query_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.ai_query + compiler.driver.query_cmd + std.meta_effects probe
    probe_template = resolve_fixture_path(root, "ai_query_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "ai_query_probe_bundle.ax"
    probe_bundle.write_text(assemble_ai_query_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(f"ai_query_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if norm_interp_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for ai_query_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp_probe}\n"
        )
        return 1

    for opt_label, opt_flags in (
        ("O0", ["-O0"]),
        ("O1", ["-O1"]),
        ("O2", ["-O2", "--verify-each"]),
    ):
        probe_exe = tmp_dir / f"ai_query_probe_{opt_label}{exe_ext}"
        bproc = run_cmd([axiomc, "build", str(probe_bundle), *opt_flags, "-o", str(probe_exe)], root, timeout=180)
        if bproc.returncode != 0:
            sys.stderr.write(f"ai_query_probe build -{opt_label} failed ({bproc.returncode}):\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(f"ai_query_probe run -{opt_label} failed ({rproc.returncode}):\n{rproc.stdout}\n{rproc.stderr}\n")
            return 1
        norm_native = rproc.stdout.replace("\r\n", "\n")
        if norm_native != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"native -{opt_label} stdout mismatch for ai_query_probe:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
            )
            return 1

    # 2. Run standalone fixtures across --interp, -O0, -O1, -O2 --verify-each and verify production PE stripping
    for name, filename, expected_stdout in POSITIVE_FIXTURES:
        src = resolve_fixture_path(root, filename)
        ip = run_cmd([axiomc, "run", "--interp", str(src)], root, timeout=120)
        if ip.returncode != 0 or ip.stdout.replace("\r\n", "\n") != expected_stdout:
            sys.stderr.write(f"fixture {name} --interp failed:\n{ip.stdout}\n{ip.stderr}\n")
            return 1
        for opt_label, opt_flags in (("O0", ["-O0"]), ("O1", ["-O1"]), ("O2", ["-O2", "--verify-each"])):
            exe = tmp_dir / f"{name}_{opt_label}{exe_ext}"
            bp = run_cmd([axiomc, "build", str(src), *opt_flags, "-o", str(exe)], root, timeout=120)
            if bp.returncode != 0:
                sys.stderr.write(f"fixture {name} build -{opt_label} failed:\n{bp.stdout}\n{bp.stderr}\n")
                return 1
            rp = run_cmd([str(exe)], root, timeout=120)
            if rp.returncode != 0 or rp.stdout.replace("\r\n", "\n") != expected_stdout:
                sys.stderr.write(f"fixture {name} run -{opt_label} failed:\n{rp.stdout}\n{rp.stderr}\n")
                return 1
            if name == "layout_and_container_meta":
                raw_pe = exe.read_bytes()
                for forbidden in (b"AXMETA01", b"AXMI0001", b"AXLTO001", b"AXMIR001", b"AXDB0001"):
                    if forbidden in raw_pe:
                        sys.stderr.write(f"Production PE {exe} leaked metadata magic {forbidden!r}\n")
                        return 1

    sys.stdout.buffer.write(b"AI-QUERY-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
