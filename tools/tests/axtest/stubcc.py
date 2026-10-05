#!/usr/bin/env python3
"""Stub compiler for the axtest self-tests.

It imitates just enough of the axiom0 command line (`--features`, `check --json`, `inspect --emit=`,
`run --interp`, `build -o`) and takes its behaviour from `//@` lines in the source file, so that every
runner directive, kind and state can be proven without the real compiler:

    //@ out TEXT          write TEXT (escapes: \\n \\r \\xHH \\u{..}) to stdout
    //@ err TEXT          write TEXT to stderr
    //@ out-if COND TEXT  like out, only when COND holds: `interp`, `native`, or a compiler flag
    //@ exit N            program exit code (default 0)
    //@ sleep S           sleep S seconds
    //@ echo-args         stdout: args=a|b|c
    //@ echo-env NAME     stdout: NAME=value (or NAME=<unset>)
    //@ echo-stdin        copy stdin to stdout
    //@ echo-flags        stdout: flags=... (flags the compiler received, without the input path)
    //@ echo-mode         stdout: mode=interp or mode=native
    //@ echo-cwd-name     stdout: the name of the directory the program runs in
    //@ limit             (interp) print AX_DRIVER_INTERP_STEP_LIMIT on stderr and exit 124
    //@ crash             die with an access-violation style status
    //@ diag CODE SEV LINE [FILE]   a diagnostic for `check --json` (SEV: error|warning)
    //@ ice               print the internal-compiler-error banner (compiler step)
    //@ compile-exit N    exit code of the compiler step (default 0; with `ice` default 3)
    //@ emit EXT TEXT     stdout of `inspect --emit=EXT`

Environment: STUB_FEATURES (comma list, default `interp,native`), STUB_NO_FEATURES_CMD=1 (behave like a
compiler that has no --features command: usage error, exit 2), STUB_FEATURES_CRASH=1.
"""

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def decode(text):
    out = bytearray()
    i = 0
    while i < len(text):
        c = text[i]
        if c != "\\":
            out += c.encode("utf-8")
            i += 1
            continue
        e = text[i + 1]
        if e == "n":
            out += b"\n"; i += 2
        elif e == "r":
            out += b"\r"; i += 2
        elif e == "\\":
            out += b"\\"; i += 2
        elif e == "x":
            out.append(int(text[i + 2:i + 4], 16)); i += 4
        elif e == "u":
            m = re.match(r"\{([0-9a-fA-F]+)\}", text[i + 2:])
            out += chr(int(m.group(1), 16)).encode("utf-8"); i += 2 + m.end()
        else:
            raise ValueError("stub: bad escape")
    return bytes(out)


def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    result = []
    for line in data.decode("utf-8", "replace").split("\n"):
        m = re.search(r"//@ (\S+)(?: (.*))?$", line)
        if m:
            result.append((m.group(1), m.group(2) or ""))
    return result


def w(stream, data):
    stream.buffer.write(data)
    stream.buffer.flush()


def die_crash():
    if os.name == "nt":
        os._exit(0xC0000005 - (1 << 32))
    import signal
    os.kill(os.getpid(), signal.SIGSEGV)


def banner():
    w(sys.stderr, b"internal compiler error: stub invariant failed at stub.c:1\n")


def run_program(src, flags, mode, args=None, input_path=None):
    """Execute the behaviour described by the `//@` lines (both for interp and native)."""
    args = list(args or [])
    code = 0
    ops = read_lines(src)
    for op, rest in ops:
        if op == "out":
            w(sys.stdout, decode(rest))
        elif op == "err":
            w(sys.stderr, decode(rest))
        elif op == "out-if":
            cond, _, text = rest.partition(" ")
            if cond == mode or cond in flags:
                w(sys.stdout, decode(text))
        elif op == "exit":
            code = int(rest)
        elif op == "sleep":
            time.sleep(float(rest))
        elif op == "echo-args":
            w(sys.stdout, ("args=" + "|".join(args) + "\n").encode("utf-8"))
        elif op == "echo-env":
            w(sys.stdout, ("%s=%s\n" % (rest, os.environ.get(rest, "<unset>"))).encode("utf-8"))
        elif op == "echo-stdin":
            w(sys.stdout, sys.stdin.buffer.read())
        elif op == "echo-flags":
            w(sys.stdout, ("flags=" + " ".join(flags) + "\n").encode("utf-8"))
        elif op == "echo-mode":
            w(sys.stdout, ("mode=" + mode + "\n").encode("utf-8"))
        elif op == "echo-cwd-name":
            w(sys.stdout, (os.path.basename(os.getcwd()) + "\n").encode("utf-8"))
        elif op == "limit" and mode == "interp":
            w(sys.stderr, b"error[AX_DRIVER_INTERP_STEP_LIMIT]: step limit reached\n")
            return 124
        elif op == "crash":
            die_crash()
    return code


def compile_phase(src):
    """Compiler-step behaviour. Returns an exit code to stop with, or None to continue."""
    ops = read_lines(src)
    has_ice = any(op == "ice" for op, _ in ops)
    if has_ice:
        banner()
    for op, rest in ops:
        if op == "compile-exit":
            return int(rest)
    return 3 if has_ice else None


def split_args(argv):
    """Returns (flags, input path, output path, program args)."""
    flags = []
    out = None
    inp = None
    prog_args = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--":
            prog_args = argv[i + 1:]
            break
        if a == "-o":
            out = argv[i + 1]; i += 2
            continue
        if a in ("--std-root", "--target"):
            flags += [a, argv[i + 1]]; i += 2
            continue
        if a.startswith("-"):
            flags.append(a); i += 1
            continue
        inp = a; i += 1
    return flags, inp, out, prog_args


def src_of(inp):
    """A project directory (axiom.toml) is described by its src/main.ax."""
    if inp is not None and os.path.isdir(inp):
        return os.path.join(inp, "src", "main.ax")
    return inp


def main(argv):
    if not argv:
        sys.stderr.write("usage: stubcc <command>\n")
        return 2
    cmd = argv[0]
    if cmd == "--features":
        if os.environ.get("STUB_NO_FEATURES_CMD"):
            sys.stderr.write("stubcc: unknown command '--features'\n")
            return 2
        if os.environ.get("STUB_FEATURES_CRASH"):
            die_crash()
        feats = os.environ.get("STUB_FEATURES", "interp,native")
        for f in feats.split(","):
            if f:
                w(sys.stdout, (f + "\n").encode())
        return 0
    if cmd == "version":
        w(sys.stdout, b"stubcc 0\n")
        return 0
    rest = argv[1:]
    if cmd == "check":
        flags, inp, _o, _a = split_args(rest)
        inp = src_of(inp)
        rc = compile_phase(inp)
        diags = []
        for op, text in read_lines(inp):
            if op == "diag":
                parts = text.split()
                code, sev, line = parts[0], parts[1], int(parts[2])
                f = parts[3] if len(parts) > 3 else inp
                diags.append({"id": len(diags), "code": code, "severity": sev, "message": "stub",
                              "primary": {"file": f, "start": 0, "end": 1, "line": line, "col": 1,
                                          "end_line": line, "end_col": 2},
                              "labels": [], "notes": [], "helps": [], "fixes": [], "data": {}})
            elif op == "diag-noprimary":
                code, sev = text.split()
                diags.append({"id": len(diags), "code": code, "severity": sev, "message": "stub",
                              "primary": None, "labels": [], "notes": [], "helps": [], "fixes": [], "data": {}})
        errors = sum(1 for d in diags if d["severity"] == "error")
        doc = {"schema": 1, "tool": "axiom0", "diagnostics": diags, "errors": errors,
               "warnings": len(diags) - errors}
        w(sys.stderr, (json.dumps(doc) + "\n").encode("utf-8"))
        if rc is not None:
            return rc
        return 1 if errors else 0
    if cmd == "inspect":
        ext = None
        files = []
        for a in rest:
            if a.startswith("--emit="):
                ext = a[len("--emit="):]
            elif not a.startswith("-"):
                files.append(a)
        inp = src_of(files[-1])
        rc = compile_phase(inp)
        if rc is not None:
            return rc
        for op, text in read_lines(inp):
            if op == "emit":
                e, _, body = text.partition(" ")
                if e == ext:
                    w(sys.stdout, decode(body))
                    return 0
        sys.stderr.write("stubcc: unknown emitter '%s'\n" % ext)
        return 2
    if cmd == "run":
        flags, inp, _o, prog_args = split_args(rest)
        inp = src_of(inp)
        if "--interp" not in flags:
            sys.stderr.write("stubcc: only run --interp is supported\n")
            return 2
        flags = [f for f in flags if f != "--interp"]
        rc = compile_phase(inp)
        if rc is not None:
            return rc
        return run_program(inp, flags, "interp", prog_args)
    if cmd == "build":
        flags, inp, out, _a = split_args(rest)
        inp = src_of(inp)
        rc = compile_phase(inp)
        if rc is not None:
            return rc
        if out is None:
            sys.stderr.write("stubcc: build needs -o\n")
            return 2
        here = os.path.dirname(os.path.abspath(__file__))
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("import sys\nsys.path.insert(0, %r)\nimport stubcc\n"
                    "sys.exit(stubcc.run_program(%r, %r, 'native', sys.argv[1:]))\n"
                    % (here, os.path.abspath(inp), flags))
        return 0
    sys.stderr.write("stubcc: unknown command '%s'\n" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
