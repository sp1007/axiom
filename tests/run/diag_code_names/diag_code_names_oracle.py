#!/usr/bin/env python3
"""T497a oracle: every diagnostic code renders with its registered name.

1. Bundles the diag modules with diag_code_names_probe.ax.in and runs it (interp + native -O0/-O1): the rendered name of every
   code id equals diag_code_name, no registered id renders as `<unknown>`, the AX_ASYNC_* ids render their own names.
2. Compiles await_outside_async.ax.in with `axiomc check` and requires the human output to contain
   `error[AX_ASYNC_AWAIT_OUTSIDE_ASYNC]` (and no `error[<unknown>]`)."""

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
    "codes mismatch=0 table_disagree=0 async_bad=0 registered_nonzero=true\n"
    "DIAG-CODE-NAMES-PROBE-PASS\n"
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
]


def run_cmd(cmd, cwd, timeout=180):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: diag_code_names_oracle.py <compiler> <build> <tmp> <root>\n")
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

    test_dir = pathlib.Path(root) / "tests" / "run" / "diag_code_names"
    if not test_dir.is_dir():
        test_dir = HERE
    template = test_dir / "diag_code_names_probe.ax.in"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    src = prelude + "\n" + bc.assemble_compiler_modules(MODULES, root=root) + "\n" + template.read_text(encoding="utf-8")
    bundle = tmp_dir / "diag_code_names_probe_bundle.ax"
    bundle.write_text(src, encoding="utf-8", newline="\n")

    p = run_cmd([axiomc, "run", "--interp", str(bundle)], root)
    if p.returncode != 0 or p.stdout.replace("\r\n", "\n") != EXPECTED:
        sys.stderr.write(f"--interp failed ({p.returncode}):\n{p.stdout}\n{p.stderr}\n")
        return 1
    for flag in ("-O0", "-O1"):
        out = tmp_dir / f"diag_code_names_probe_{flag[1:]}{exe}"
        b = run_cmd([axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(out), str(bundle)], root)
        if b.returncode != 0:
            sys.stderr.write(f"build {flag} failed:\n{b.stdout}\n{b.stderr}\n")
            return 1
        r = run_cmd([str(out)], root)
        if r.returncode != 0 or r.stdout.replace("\r\n", "\n") != EXPECTED:
            sys.stderr.write(f"{flag} failed ({r.returncode}):\n{r.stdout}\n{r.stderr}\n")
            return 1

    prog = tmp_dir / "await_outside_async.ax"
    prog.write_text((test_dir / "await_outside_async.ax.in").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    c = run_cmd([axiomc, "check", str(prog)], root)
    text = (c.stdout + c.stderr).replace("\r\n", "\n")
    if c.returncode == 0 or "error[AX_ASYNC_AWAIT_OUTSIDE_ASYNC]" not in text or "error[<unknown>]" in text:
        sys.stderr.write(f"check did not print error[AX_ASYNC_AWAIT_OUTSIDE_ASYNC] ({c.returncode}):\n{text}\n")
        return 1

    sys.stdout.buffer.write(b"DIAG-CODE-NAMES-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
