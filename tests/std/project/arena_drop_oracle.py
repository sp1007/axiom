#!/usr/bin/env python3
"""T160 oracle for the `tests/std/project/arena_drop` project test.

Stages `tests/std/project/arena_drop` into `{tmp}` along with the live
`{std_root}/core/arena/arena.ax` module (`module std.core.arena.arena`)
because `ax_project_discover` currently only auto-loads `option.ax`,
`result.ax`, `prelude.ax`, and `host.ax` from `--std-root`.

Modes:
  - `interp`: runs `{compiler} run --interp --std-root {std_root} <pkg>`
    and emits its stdout for `axtest.py` comparison against `src/main.ax`.
  - `native`: runs `{compiler} run --interp` (`run` leg) and
    `{compiler} build` + execute at `-O0` and `-O1` (`native` legs),
    verifies all legs exit `0` with identical stdout, and emits the stdout
    for `axtest.py` comparison against `arena_drop.test`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_checked(cmd: list[str], label: str) -> bytes:
    proc = subprocess.run(cmd, capture_output=True, timeout=60)
    if proc.returncode != 0:
        sys.stderr.write(
            f"FAIL [{label}]: exit={proc.returncode}\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout.decode('utf-8', 'replace')}\n"
            f"stderr:\n{proc.stderr.decode('utf-8', 'replace')}\n"
        )
        sys.exit(1)
    return proc.stdout.replace(b"\r\n", b"\n")


def stage_project(pkg_src: Path, std_root: Path, tmp_dir: Path, mode: str) -> Path:
    staged = tmp_dir / f"arena_drop_{mode}"
    if staged.exists():
        shutil.rmtree(staged)
    shutil.copytree(pkg_src, staged)
    arena_src = std_root / "core" / "arena" / "arena.ax"
    if not arena_src.is_file():
        sys.stderr.write(f"FAIL: missing std arena source at {arena_src}\n")
        sys.exit(1)
    shutil.copyfile(arena_src, staged / "src" / "arena.ax")
    return staged


def main() -> int:
    if len(sys.argv) != 6:
        sys.stderr.write(
            "usage: arena_drop_oracle.py <interp|native> <compiler> <pkg_dir> <std_root> <tmp_dir>\n"
        )
        return 2

    mode = sys.argv[1]
    compiler = Path(sys.argv[2]).resolve()
    pkg_dir = Path(sys.argv[3]).resolve()
    std_root = Path(sys.argv[4]).resolve()
    tmp_dir = Path(sys.argv[5]).resolve()

    staged = stage_project(pkg_dir, std_root, tmp_dir, mode)

    if mode == "interp":
        out_interp = run_checked(
            [str(compiler), "run", "--interp", "--std-root", str(std_root), str(staged)],
            "run --interp",
        )
        sys.stdout.buffer.write(out_interp)
        sys.stdout.buffer.flush()
        return 0

    if mode == "native":
        out_interp = run_checked(
            [str(compiler), "run", "--interp", "--std-root", str(std_root), str(staged)],
            "run --interp",
        )

        exe_ext = ".exe" if os.name == "nt" else ""
        exe_o0 = tmp_dir / f"arena_drop_o0{exe_ext}"
        exe_o1 = tmp_dir / f"arena_drop_o1{exe_ext}"

        run_checked(
            [str(compiler), "build", "--std-root", str(std_root), str(staged), "-o", str(exe_o0)],
            "build -O0",
        )
        out_exec_o0 = run_checked([str(exe_o0)], "exec -O0")

        run_checked(
            [str(compiler), "build", "-O1", "--std-root", str(std_root), str(staged), "-o", str(exe_o1)],
            "build -O1",
        )
        out_exec_o1 = run_checked([str(exe_o1)], "exec -O1")

        outputs = {
            "run --interp": out_interp,
            "build+exec -O0": out_exec_o0,
            "build+exec -O1": out_exec_o1,
        }
        baseline = out_exec_o0
        for label, out in outputs.items():
            if out != baseline:
                sys.stderr.write(
                    f"FAIL: output mismatch between build+exec -O0 and {label}:\n"
                    f"--- build+exec -O0 ---\n{baseline.decode('utf-8', 'replace')}"
                    f"--- {label} ---\n{out.decode('utf-8', 'replace')}"
                )
                return 1

        sys.stdout.buffer.write(baseline)
        sys.stdout.buffer.flush()
        return 0

    sys.stderr.write(f"FAIL: unknown mode {mode!r}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
