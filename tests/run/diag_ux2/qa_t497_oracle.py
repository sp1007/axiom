#!/usr/bin/env python3
"""QA oracle for T497: bundles the diag modules with qa_t497_probe.ax.in and runs it (interp + native -O0/-O1).

The probe cross-checks code 169 (AX_TYPE_INDEX_NOT_INT) in compiler.diag.code, compiler.diag.format and
compiler.diag.explain, plus a name sweep over every code id (format.ax vs code.ax)."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

EXPECTED = (
    "t497[code] id_ok=true name_ok=true msg_ok=true sweep_ok=true\n"
    "t497[explain] entry_ok=true count_ok=true cli_ok=true\n"
    "QA-T497-CODE-PROBE-PASS\n"
)

MODULES = [
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
    ("compiler.diag.explain", "compiler"),
    ("compiler.driver.explain_cmd", "compiler"),
]


def run_cmd(cmd, cwd, timeout=180):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: qa_t497_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2
    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir = pathlib.Path(os.path.abspath(sys.argv[3]))
    root = os.path.abspath(sys.argv[4])
    exe = ".exe" if os.name == "nt" else ""
    axiomc = compiler
    for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
        cand = os.path.join(build_dir, name)
        if os.path.isfile(cand):
            axiomc = cand
            break
    tmp_dir.mkdir(parents=True, exist_ok=True)

    template = pathlib.Path(root) / "tests" / "run" / "diag_ux2" / "qa_t497_probe.ax.in"
    if not template.is_file():
        template = HERE / "qa_t497_probe.ax.in"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    src = prelude + "\n" + bc.assemble_compiler_modules(MODULES, root=root) + "\n" + template.read_text(encoding="utf-8")
    bundle = tmp_dir / "qa_t497_probe_bundle.ax"
    bundle.write_text(src, encoding="utf-8", newline="\n")

    p = run_cmd([axiomc, "run", "--interp", str(bundle)], root)
    if p.returncode != 0 or p.stdout.replace("\r\n", "\n") != EXPECTED:
        sys.stderr.write(f"--interp failed ({p.returncode}):\n{p.stdout}\n{p.stderr}\n")
        return 1
    for flag in ("-O0", "-O1"):
        out = tmp_dir / f"qa_t497_probe_{flag[1:]}{exe}"
        b = run_cmd([axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(out), str(bundle)], root)
        if b.returncode != 0:
            sys.stderr.write(f"build {flag} failed:\n{b.stdout}\n{b.stderr}\n")
            return 1
        r = run_cmd([str(out)], root)
        if r.returncode != 0 or r.stdout.replace("\r\n", "\n") != EXPECTED:
            sys.stderr.write(f"{flag} failed ({r.returncode}):\n{r.stdout}\n{r.stderr}\n")
            return 1
    sys.stdout.buffer.write(b"QA-T497-CODE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
