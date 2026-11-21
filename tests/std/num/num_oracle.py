#!/usr/bin/env python3
"""Oracle for the T454 integer library tests (tests/std/num/*.test).

The driver of the compiler only auto-loads a few std modules, so a program that uses the real std sources has to be
a package that contains them (the arena_drop test of T160 does the same).  This script stages

    <tmp>/<name>_<leg>/axiom.toml
    <tmp>/<name>_<leg>/src/main.ax          the program tests/std/num/prog/<name>.ax
    <tmp>/<name>_<leg>/src/<file>.ax        every file named in the program's `// std: a/b.ax c/d.ax` header,
                                            copied live from <std_root> (so the test always runs the shipped code)

and runs it three ways: `run --interp`, `build` + execute at -O0 and `build -O1` + execute.  All three legs must
agree on exit code and stdout.

Modes (first argument):
  run     the program must exit 0 in every leg; the common stdout is printed
  panic   the program must exit 101 in every leg; prints `PANIC 101 <stdout of the leg>`
  reject  `check` must fail with the diagnostic code given as the last argument; prints `REJECTED <code>`

usage: num_oracle.py <run|panic|reject> <compiler> <std_root> <tmp_dir> <program.ax> [<diagnostic code>]
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TIMEOUT = 1400


def stage(program: Path, std_root: Path, tmp_dir: Path, leg: str) -> Path:
    name = program.stem
    staged = tmp_dir / ("%s_%s" % (name, leg))
    if staged.exists():
        shutil.rmtree(staged)
    (staged / "src").mkdir(parents=True)
    (staged / "axiom.toml").write_text('[package]\nname = "%s"\nversion = "0.1.0"\nedition = "2026"\n' % name, newline="\n")
    text = program.read_bytes().replace(b"\r\n", b"\n")
    (staged / "src" / "main.ax").write_bytes(text)
    m = re.search(rb"^// std:(.*)$", text, re.M)
    files = m.group(1).decode().split() if m else []
    for rel in files:
        src = std_root / rel
        if not src.is_file():
            sys.stderr.write("FAIL: missing std source %s\n" % src)
            sys.exit(1)
        shutil.copyfile(src, staged / "src" / (Path(rel).name))
    return staged


def run(cmd, label):
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        sys.stderr.write("FAIL [%s]: timeout\ncmd: %s\n" % (label, " ".join(cmd)))
        sys.exit(1)
    return proc


def describe(proc):
    return "exit=%d\nstdout:\n%s\nstderr:\n%s" % (proc.returncode, proc.stdout.decode("utf-8", "replace")[:2000],
                                                   proc.stderr.decode("utf-8", "replace")[:4000])


def legs(compiler: Path, std_root: Path, tmp_dir: Path, program: Path):
    """Yield (label, completed process) for the three legs."""
    exe_ext = ".exe" if os.name == "nt" else ""
    staged = stage(program, std_root, tmp_dir, "interp")
    yield "run --interp", run([str(compiler), "run", "--interp", "--std-root", str(std_root), str(staged)], "run --interp")
    for flag, label in (([], "-O0"), (["-O1"], "-O1")):
        staged = stage(program, std_root, tmp_dir, label.strip("-"))
        exe = tmp_dir / ("%s_%s%s" % (program.stem, label.strip("-"), exe_ext))
        build = run([str(compiler), "build"] + flag + ["--std-root", str(std_root), str(staged), "-o", str(exe)], "build " + label)
        if build.returncode != 0:
            yield "build " + label, build
            continue
        yield "exec " + label, run([str(exe)], "exec " + label)


def main(argv):
    if len(argv) < 5 or (argv[0] == "reject" and len(argv) < 6):
        sys.stderr.write(__doc__)
        return 2
    mode = argv[0]
    compiler = Path(argv[1]).resolve()
    std_root = Path(argv[2]).resolve()
    tmp_dir = Path(argv[3]).resolve()
    program = Path(argv[4]).resolve()
    tmp_dir.mkdir(parents=True, exist_ok=True)

    if mode == "reject":
        code = argv[5]
        staged = stage(program, std_root, tmp_dir, "reject")
        proc = run([str(compiler), "check", "--std-root", str(std_root), str(staged)], "check")
        err = proc.stderr.decode("utf-8", "replace") + proc.stdout.decode("utf-8", "replace")
        if proc.returncode != 1 or code not in err:
            sys.stderr.write("FAIL: expected `check` to fail with %s\n%s\n" % (code, describe(proc)))
            return 1
        sys.stdout.buffer.write(("REJECTED %s\n" % code).encode())
        sys.stdout.buffer.flush()
        return 0

    want = 0 if mode == "run" else 101
    results = []
    for label, proc in legs(compiler, std_root, tmp_dir, program):
        if proc.returncode != want:
            sys.stderr.write("FAIL [%s]: expected exit %d\n%s\n" % (label, want, describe(proc)))
            return 1
        results.append((label, proc.stdout.replace(b"\r\n", b"\n")))
    base_label, base = results[0]
    for label, out in results[1:]:
        if out != base:
            sys.stderr.write("FAIL: stdout of %s differs from %s\n--- %s ---\n%s--- %s ---\n%s" % (
                label, base_label, base_label, base.decode("utf-8", "replace"), label, out.decode("utf-8", "replace")))
            return 1
    if len(results) != 3:
        sys.stderr.write("FAIL: expected 3 legs, got %d\n" % len(results))
        return 1
    if mode == "panic":
        sys.stdout.buffer.write(b"PANIC 101 ")
    sys.stdout.buffer.write(base)
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
