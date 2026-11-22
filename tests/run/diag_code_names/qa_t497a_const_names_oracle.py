#!/usr/bin/env python3
"""T497a QA oracle: the rendered name of every code id 0..=300 equals the name of the `pub const AX_*: u32 = N;` constant of
compiler/diag/code.ax (and `<unknown>` where no constant exists), in interp, native -O0 and native -O1 (byte-identical stdout).
The constants are a source independent of the two name tables, so a drifting or deleted table branch is caught; the sentinel
AX_DIAG_CODE_COUNT is not a code. Also the `--json` output for an `.await` outside async carries the same name."""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

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
]
MAXID = 300


def run_cmd(cmd, cwd, timeout=240):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: qa_t497a_const_names_oracle.py <compiler> <build> <tmp> <root>\n")
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

    code_src = pathlib.Path(root, "compiler", "diag", "code.ax").read_text(encoding="utf-8")
    consts = {}
    for name, num in re.findall(r"pub const (AX_[A-Z0-9_]+): u32 = (\d+)u32;", code_src):
        if name != "AX_DIAG_CODE_COUNT":
            consts[int(num)] = name
    if len(consts) < 150 or max(consts) < 169:
        sys.stderr.write(f"oracle: implausible constant table ({len(consts)} entries, max {max(consts) if consts else None})\n")
        return 1
    expected = "".join(f"{i} {consts.get(i, '<unknown>')}\n" for i in range(MAXID + 1))

    test_dir = pathlib.Path(root) / "tests" / "run" / "diag_code_names"
    if not test_dir.is_dir():
        test_dir = HERE
    template = test_dir / "qa_t497a_const_names_probe.ax.in"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    src = prelude + "\n" + bc.assemble_compiler_modules(MODULES, root=root) + "\n" + template.read_text(encoding="utf-8")
    bundle = tmp_dir / "qa_t497a_const_names_bundle.ax"
    bundle.write_text(src, encoding="utf-8", newline="\n")

    def check(label, p):
        got = p.stdout.replace("\r\n", "\n")
        if p.returncode != 0 or got != expected:
            exp_l, got_l = expected.splitlines(), got.splitlines()
            diffs = [(a, b) for a, b in zip(exp_l, got_l) if a != b][:5]
            sys.stderr.write(f"{label} failed (exit {p.returncode}, {len(got_l)} lines vs {len(exp_l)}): first diffs {diffs}\n{p.stderr[-800:]}\n")
            return False
        return True

    if not check("--interp", run_cmd([axiomc, "run", "--interp", str(bundle)], root)):
        return 1
    for flag in ("-O0", "-O1"):
        out = tmp_dir / f"qa_t497a_const_names_{flag[1:]}{exe}"
        b = run_cmd([axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(out), str(bundle)], root)
        if b.returncode != 0:
            sys.stderr.write(f"build {flag} failed:\n{b.stdout}\n{b.stderr}\n")
            return 1
        if not check(flag, run_cmd([str(out)], root)):
            return 1

    # JSON diagnostics: the same registered name, never `<unknown>`
    prog = tmp_dir / "await_outside_async.ax"
    prog.write_text((test_dir / "await_outside_async.ax.in").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    c = run_cmd([axiomc, "check", "--json", str(prog)], root)
    try:
        doc = json.loads((c.stdout.strip() or c.stderr.strip()))
        codes = [d["code"] for d in doc["diagnostics"]]
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"check --json output is not the expected JSON ({e}):\n{c.stdout}\n{c.stderr}\n")
        return 1
    if c.returncode == 0 or codes != ["AX_ASYNC_AWAIT_OUTSIDE_ASYNC"]:
        sys.stderr.write(f"check --json codes {codes} (exit {c.returncode})\n")
        return 1

    sys.stdout.buffer.write(b"QA-T497A-CONST-NAMES-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
