#!/usr/bin/env python3
"""axtest - the Axiom test runner (T005).

Discovers tests under <root>/tests, runs the compiler under test and the programs it produces as
binary subprocesses, and compares exit codes and raw output bytes with the expectations written in
the test files. Python 3 standard library only. Full documentation: tests/README.md.

This file is written once: every test kind and directive the later tasks need is already here
(ADR-0005 section 2). Later tasks add test files, never edit the runner.

Exit status: 0 no FAIL, 1 at least one FAIL (XPASS, CRASH and TIMEOUT count as FAIL), 2 usage error.
The last line of the normal output is `TOTAL n PASS p FAIL f SKIP s XFAIL x`
(with --json the JSON document goes to stdout and that line to stderr).
"""

import argparse
import concurrent.futures
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ----------------------------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------------------------

# The internal-compiler-error banner (SPEC-03 AXS-SEM-082). A compiler crash is recognised by a line
# of the compiler's stderr that starts with this text, NOT by exit code 3 alone, because a test
# program may legitimately exit with 3. The exact text is fixed by T009/T016; if it changes, this is
# the only place to edit.
ICE_BANNER_RE = re.compile(rb"^(?:error: )?internal compiler error", re.IGNORECASE | re.MULTILINE)

# Interpreter limit diagnostics (SPEC-03 AXS-SEM-090/091): `run --interp` exits 124 and prints a
# diagnostic whose code starts with this prefix. Such a run is TIMEOUT, not FAIL.
INTERP_LIMIT_EXIT = 124
INTERP_LIMIT_CODE_PREFIX = b"AX_DRIVER_INTERP_"

DEFAULT_TIMEOUT = 10.0
KINDS = ("run", "ui", "golden", "diff", "exec")
MODES = ("interp", "native")
STATES = ("PASS", "FAIL", "SKIP", "XFAIL", "XPASS", "CRASH", "TIMEOUT")
# Sibling extensions of x.ax that are not golden files.
NON_GOLDEN_EXT = {"ax", "test", "md", "txt", "c", "h", "py", "toml", "json", "csv", "bak", "tmp"}
SKIP_DIRS = {"fixtures", "__pycache__"}

TASK_ID_RE = re.compile(r"^T\d+[a-z]?$")
HEADER_DIRECTIVE_RE = re.compile(r"^//[ \t]*([a-z][a-z0-9-]*):[ \t]?(.*)$")
MANIFEST_DIRECTIVE_RE = re.compile(r"^([a-z][a-z0-9-]*):[ \t]?(.*)$")
ANNOTATION_RE = re.compile(r"//~(?P<mark>\^*|\?)[ \t]*(?P<sev>ERROR|WARN)[ \t]+(?P<code>[A-Z][A-Z0-9_]*)")

# directive name -> "single" (at most once) or "multi" (may repeat; see Test.* accessors)
DIRECTIVES = {
    "test": "single",
    "exit": "single",
    "modes": "single",
    "target": "single",
    "timeout": "single",
    "input": "single",
    "cmd": "single",
    "native-after": "single",
    "xfail": "single",
    "stdout-file": "single",
    "stdout": "multi",
    "stderr": "multi",
    "stdout-contains": "multi",
    "stderr-contains": "multi",
    "stdin": "multi",
    "flags": "multi",
    "args": "multi",
    "env": "multi",
    "skip-unless": "multi",
    "requires": "multi",
    "emit": "multi",
}


class Outcome:
    """The result of one test entry: a state and a one-line message."""

    __slots__ = ("state", "msg", "detail")

    def __init__(self, state, msg="", detail=""):
        self.state = state
        self.msg = msg
        self.detail = detail


def passed(msg=""):
    return Outcome("PASS", msg)


def failed(msg, detail=""):
    return Outcome("FAIL", msg, detail)


def skipped(reason):
    return Outcome("SKIP", reason)


# ----------------------------------------------------------------------------------------------
# Byte helpers
# ----------------------------------------------------------------------------------------------

def decode_escapes(text):
    """Decode a directive value (`\\n \\r \\t \\0 \\\\ \\xHH \\u{H..}`) to bytes.

    `\\xHH` is one raw byte (so an invalid UTF-8 sequence can be expressed); every other character
    is encoded as UTF-8. Raises ValueError for an unknown or malformed escape.
    """
    out = bytearray()
    i = 0
    n = len(text)
    simple = {"n": b"\n", "r": b"\r", "t": b"\t", "0": b"\x00", "\\": b"\\", "'": b"'", '"': b'"'}
    while i < n:
        c = text[i]
        if c != "\\":
            out += c.encode("utf-8", "surrogatepass")
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("trailing backslash")
        e = text[i + 1]
        if e in simple:
            out += simple[e]
            i += 2
        elif e == "x":
            h = text[i + 2:i + 4]
            if len(h) != 2 or not re.fullmatch(r"[0-9a-fA-F]{2}", h):
                raise ValueError("bad \\x escape")
            out.append(int(h, 16))
            i += 4
        elif e == "u":
            m = re.match(r"\{([0-9a-fA-F]{1,6})\}", text[i + 2:])
            if not m:
                raise ValueError("bad \\u{...} escape")
            cp = int(m.group(1), 16)
            if cp > 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
                raise ValueError("\\u{...} is not a Unicode scalar value")
            out += chr(cp).encode("utf-8")
            i += 2 + m.end()
        else:
            raise ValueError("unknown escape \\" + e)
    return bytes(out)


def render(data, limit=160):
    """Printable, single-line rendering of bytes for messages."""
    s = data.decode("utf-8", "backslashreplace")
    s = s.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    if len(s) > limit:
        s = s[:limit] + "..."
    return s


def hexs(data):
    return " ".join("%02x" % b for b in data)


def byte_diff(expected, actual, what):
    """Message describing the first difference between two byte strings, with a hex window."""
    n = 0
    m = min(len(expected), len(actual))
    while n < m and expected[n] == actual[n]:
        n += 1
    lo = max(0, n - 6)
    return (
        "%s differs at byte %d (expected %d bytes, got %d bytes)\n"
        "    expected: %s | hex %s\n"
        "    actual:   %s | hex %s"
        % (
            what, n, len(expected), len(actual),
            render(expected[lo:n + 16], 80), hexs(expected[lo:n + 16]),
            render(actual[lo:n + 16], 80), hexs(actual[lo:n + 16]),
        )
    )


def is_crash_status(rc):
    """An exit status that means the process died (signal, access violation, abort)."""
    return rc is not None and (rc < 0 or rc >= 0xC0000000)


# ----------------------------------------------------------------------------------------------
# Subprocess helper
# ----------------------------------------------------------------------------------------------

class Proc:
    __slots__ = ("rc", "out", "err", "timed_out", "spawn_error", "cmd")

    def __init__(self, cmd):
        self.cmd = cmd
        self.rc = None
        self.out = b""
        self.err = b""
        self.timed_out = False
        self.spawn_error = None


def kill_tree(p):
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            import signal
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
    except Exception:
        pass
    try:
        p.kill()
    except Exception:
        pass


def run_proc(cmd, timeout, cwd, stdin=None, env=None):
    """Run cmd with binary pipes. stdin None means no input (closed); bytes are sent."""
    res = Proc(cmd)
    kwargs = dict(stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(cwd), env=env)
    if os.name != "nt":
        kwargs["start_new_session"] = True
    try:
        p = subprocess.Popen(cmd, **kwargs)
    except OSError as e:
        res.spawn_error = str(e)
        return res
    try:
        res.out, res.err = p.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(p)
        res.timed_out = True
        try:
            res.out, res.err = p.communicate(timeout=5)
        except Exception:
            res.out, res.err = b"", b""
    res.rc = p.returncode
    return res


def native_path(text):
    """Windows Python given an MSYS/Git-Bash path (`/d/dir/x.exe`, as `bash tools/ci.sh` passes it)
    converts it to `D:/dir/x.exe`; every other path is returned unchanged."""
    if os.name == "nt":
        m = re.match(r"^/([A-Za-z])(/.*)?$", text)
        if m:
            return "%s:%s" % (m.group(1).upper(), m.group(2) or "/")
    return text


def exe_cmd(path):
    """Command prefix for an executable or a Python script (stub compilers in self-tests)."""
    p = str(path)
    if p.lower().endswith(".py"):
        return [sys.executable, p]
    return [p]


def resolve_exec_tokens(tokens, root):
    """First token of an exec manifest command: python, scripts, extensionless executables."""
    if not tokens:
        return tokens
    first = tokens[0]
    if first in ("python", "python3"):
        return [sys.executable] + tokens[1:]
    if first.lower().endswith(".py"):
        return [sys.executable, first] + tokens[1:]
    if ("/" in first or "\\" in first) and not os.path.isabs(first):
        cand = Path(root) / first
        if cand.exists():
            return [str(cand)] + tokens[1:]
        if Path(str(cand) + ".exe").exists():
            return [str(cand) + ".exe"] + tokens[1:]
    elif os.path.isabs(first) and not os.path.exists(first) and os.path.exists(first + ".exe"):
        return [first + ".exe"] + tokens[1:]
    return tokens


# ----------------------------------------------------------------------------------------------
# Test model and discovery
# ----------------------------------------------------------------------------------------------

class Test:
    def __init__(self, tid, kind, path, input_path):
        self.id = tid                    # display id: path relative to tests/ with forward slashes
        self.kind = kind                 # run | ui | golden | diff | exec | None (when erroneous)
        self.path = path                 # file (.ax / .test) or project directory
        self.input = input_path          # what is passed to the compiler (file or project dir)
        self.dirs = {}                   # name -> list of (lineno, raw value)
        self.errors = []                 # directive problems -> the test FAILs
        self.annotations = []            # ui: (file_rel|None, severity, code, line|None)
        self.golden_exts = []            # golden: extensions to compare/bless
        # parsed values
        self.exit_code = None
        self.timeout = None
        self.modes = None
        self.target = None
        self.xfail = None                # (task, reason)
        self.native_after = None
        self.stdout_file = None
        self.stdout = None
        self.stderr = None
        self.stdout_contains = []
        self.stderr_contains = []
        self.stdin = None
        self.flags = []
        self.args = []
        self.env = {}
        self.skip_unless = []            # (what, name)
        self.requires = []
        self.cmd = None
        self.input_override = None

    def has_directive(self, name, value=None):
        for _ln, raw in self.dirs.get(name, []):
            if value is None or raw.strip() == value:
                return True
        return False


def split_header(data):
    """Leading `//` lines of an .ax file as (lineno, name, raw value) directive candidates."""
    found = []
    for i, line in enumerate(data.split(b"\n"), 1):
        if line.endswith(b"\r"):
            line = line[:-1]
        if not line.startswith(b"//"):
            break
        text = line.decode("utf-8", "replace")
        m = HEADER_DIRECTIVE_RE.match(text)
        if m and m.group(1) in DIRECTIVES:
            found.append((i, m.group(1), m.group(2)))
    return found


def split_manifest(data, errors):
    found = []
    for i, line in enumerate(data.split(b"\n"), 1):
        if line.endswith(b"\r"):
            line = line[:-1]
        text = line.decode("utf-8", "replace")
        if not text.strip() or text.lstrip().startswith("#"):
            continue
        m = MANIFEST_DIRECTIVE_RE.match(text)
        if not m or m.group(1) not in DIRECTIVES:
            errors.append("line %d: not a known `name: value` directive: %s" % (i, text.strip()[:60]))
            continue
        found.append((i, m.group(1), m.group(2)))
    return found


def collect_annotations(data, rel, errors):
    """Inline `//~ ERROR CODE`, `//~^ WARN CODE`, `//~? ERROR CODE` annotations of one source."""
    result = []
    text = data.decode("utf-8", "replace")
    for ln, line in enumerate(text.split("\n"), 1):
        pos = 0
        while True:
            idx = line.find("//~", pos)
            if idx < 0:
                break
            m = ANNOTATION_RE.match(line, idx)
            if not m:
                errors.append("%s line %d: malformed annotation (expected `//~ ERROR CODE`, "
                              "`//~^ WARN CODE` or `//~? ERROR CODE`)" % (rel or "file", ln))
                pos = idx + 3
                continue
            mark = m.group("mark")
            sev = "error" if m.group("sev") == "ERROR" else "warning"
            if mark == "?":
                target = None
            else:
                target = ln - len(mark)
                if target < 1:
                    errors.append("%s line %d: `//~^` points before the first line" % (rel or "file", ln))
                    target = 1
            result.append((rel, sev, m.group("code"), target))
            pos = m.end()
    return result


def parse_directives(test, found):
    """Fill the typed fields of `test` from raw (lineno, name, value) triples."""
    for ln, name, raw in found:
        test.dirs.setdefault(name, []).append((ln, raw))

    def err(ln, msg):
        test.errors.append("line %d: %s" % (ln, msg))

    for name, kind in DIRECTIVES.items():
        occ = test.dirs.get(name, [])
        if kind == "single" and len(occ) > 1:
            err(occ[1][0], "duplicate `%s:` directive" % name)

    def first(name):
        occ = test.dirs.get(name)
        return occ[0] if occ else None

    v = first("test")
    if v:
        k = v[1].strip()
        if k in KINDS or k == "helper":
            test.kind = k
        else:
            err(v[0], "unknown test kind `%s` (expected one of %s)" % (k, ", ".join(KINDS)))
    v = first("exit")
    if v:
        try:
            test.exit_code = int(v[1].strip(), 0)
        except ValueError:
            err(v[0], "`exit:` needs an integer, got `%s`" % v[1].strip())
    v = first("timeout")
    if v:
        try:
            test.timeout = float(v[1].strip())
            if test.timeout <= 0:
                raise ValueError
        except ValueError:
            err(v[0], "`timeout:` needs a positive number of seconds, got `%s`" % v[1].strip())
    v = first("modes")
    if v:
        modes = v[1].split()
        bad = [m for m in modes if m not in MODES]
        if bad or not modes:
            err(v[0], "`modes:` takes `interp` and/or `native`, got `%s`" % v[1].strip())
        else:
            test.modes = modes
    v = first("target")
    if v:
        test.target = v[1].strip() or None
    v = first("input")
    if v:
        test.input_override = v[1].strip()
    v = first("cmd")
    if v:
        test.cmd = v[1]
    v = first("native-after")
    if v:
        t = v[1].strip()
        if TASK_ID_RE.match(t):
            test.native_after = t
        else:
            err(v[0], "`native-after:` needs a task id such as T033, got `%s`" % t)
    v = first("xfail")
    if v:
        m = re.match(r"^(T\d+[a-z]?)[ \t]+(\S.*)$", v[1].strip())
        if m:
            test.xfail = (m.group(1), m.group(2).strip())
        else:
            err(v[0], "`xfail:` needs `<task-id> <reason>`, got `%s`" % v[1].strip())
    v = first("stdout-file")
    if v:
        sf = v[1].strip()
        if sf:
            test.stdout_file = sf
        else:
            err(v[0], "`stdout-file:` needs a path")

    def joined(name):
        occ = test.dirs.get(name)
        if not occ:
            return None
        buf = b""
        for ln, raw in occ:
            try:
                buf += decode_escapes(raw)
            except ValueError as e:
                err(ln, "`%s:` %s" % (name, e))
        return buf

    test.stdout = joined("stdout")
    test.stderr = joined("stderr")
    test.stdin = joined("stdin")
    for name, attr in (("stdout-contains", "stdout_contains"), ("stderr-contains", "stderr_contains")):
        for ln, raw in test.dirs.get(name, []):
            try:
                getattr(test, attr).append(decode_escapes(raw))
            except ValueError as e:
                err(ln, "`%s:` %s" % (name, e))
    for name, attr in (("flags", "flags"), ("args", "args")):
        for ln, raw in test.dirs.get(name, []):
            try:
                getattr(test, attr).extend(shlex.split(raw))
            except ValueError as e:
                err(ln, "`%s:` %s" % (name, e))
    for ln, raw in test.dirs.get("env", []):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", raw.strip())
        if m:
            test.env[m.group(1)] = m.group(2)
        else:
            err(ln, "`env:` needs NAME=value, got `%s`" % raw.strip())
    for ln, raw in test.dirs.get("skip-unless", []):
        m = re.match(r"^(tool|feature)[ \t]+(\S+)$", raw.strip())
        if m:
            test.skip_unless.append((m.group(1), m.group(2)))
        else:
            err(ln, "`skip-unless:` needs `tool <name>` or `feature <name>`, got `%s`" % raw.strip())
    for ln, raw in test.dirs.get("requires", []):
        r = raw.strip()
        if r:
            test.requires.append(r)
        else:
            err(ln, "`requires:` needs a name")
    for ln, raw in test.dirs.get("emit", []):
        for ext in raw.split():
            if re.fullmatch(r"[a-z][a-z0-9_]*", ext) and ext not in NON_GOLDEN_EXT:
                test.golden_exts.append(ext)
            else:
                err(ln, "`emit:` takes emitter names (golden file extensions), got `%s`" % ext)


def read_file(path):
    with open(path, "rb") as f:
        return f.read()


def make_test(tid, path, kind_hint=None):
    """Build the Test for one .ax file, .test manifest or project directory."""
    rel_posix = tid
    if path.is_dir():
        main = path / "src" / "main.ax"
        t = Test(tid, None, path, path)
        if not main.is_file():
            t.errors.append("project directory has no src/main.ax (directives are read from it)")
            return t
        data = read_file(main)
        parse_directives(t, split_header(data))
        if t.input_override:
            t.input = path / t.input_override
        if t.kind == "ui":
            for f in sorted(path.rglob("*.ax")):
                rel = f.relative_to(path).as_posix()
                t.annotations.extend(collect_annotations(read_file(f), rel, t.errors))
        return t
    t = Test(tid, None, path, path)
    data = read_file(path)
    if path.suffix == ".test":
        t.kind = "exec"
        parse_directives(t, split_manifest(data, t.errors))
        if t.kind != "exec":
            t.errors.append("a `.test` manifest is always of kind exec")
            t.kind = "exec"
        if t.cmd is None:
            t.errors.append("manifest has no `cmd:` line")
        return t
    parse_directives(t, split_header(data))
    if t.input_override:
        t.input = path.parent / t.input_override
    if t.kind is None and not t.errors:
        t.errors.append("missing `// test: <kind>` directive "
                        "(use `// test: helper` for a source file that is not a test)")
    if t.kind == "ui":
        t.annotations.extend(collect_annotations(data, None, t.errors))
    if t.kind == "golden":
        for sib in sorted(path.parent.glob(path.stem + ".*")):
            ext = sib.suffix[1:]
            if sib != path and ext and ext not in NON_GOLDEN_EXT and sib.stem == path.stem:
                t.golden_exts.append(ext)
        t.golden_exts = sorted(set(t.golden_exts))
    return t


def discover(tests_dir):
    """All tests under tests_dir, sorted by id. A directory with axiom.toml is one project test."""
    tests = []
    if not tests_dir.is_dir():
        return tests
    for dirpath, dirnames, filenames in os.walk(str(tests_dir)):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        here = Path(dirpath)
        if "axiom.toml" in filenames and here != tests_dir:
            dirnames[:] = []
            tid = here.relative_to(tests_dir).as_posix()
            tests.append(make_test(tid, here))
            continue
        for fn in sorted(filenames):
            if fn.endswith(".ax") or fn.endswith(".test"):
                p = here / fn
                tid = p.relative_to(tests_dir).as_posix()
                t = make_test(tid, p)
                if t.kind == "helper" and not t.errors:
                    continue
                tests.append(t)
    tests.sort(key=lambda t: t.id)
    return tests


# ----------------------------------------------------------------------------------------------
# Execution
# ----------------------------------------------------------------------------------------------

class Observed:
    """What a run variant produced (after compilation succeeded)."""

    def __init__(self, rc, out, err, cmd):
        self.rc = rc
        self.out = out
        self.err = err
        self.cmd = cmd


class Entry:
    """One reported line: a test (or one mode of it) with a callable producing its Outcome."""

    def __init__(self, test, label, run=None, preset=None):
        self.test = test
        self.label = label
        self.run = run
        self.preset = preset

    @property
    def name(self):
        return self.test.id + (" [%s]" % self.label if self.label else "")


class Runner:
    def __init__(self, opts):
        self.root = Path(native_path(opts.root)).resolve()
        self.compiler = self._locate(opts.compiler)
        self.build_dir = self._locate(opts.build_dir) if opts.build_dir else self.compiler.parent
        self.timeout_scale = opts.timeout_scale
        self.exclude_requires = set(opts.exclude_requires or [])
        self.exe_suffix = opts.exe_suffix
        self.std_root_args = self._std_root_args(opts.std_root)
        self._features = None

    # -- configuration helpers --------------------------------------------------------------

    def _locate(self, text):
        """A relative path is taken from the current directory if it exists there, else from the
        root (the default `build/axiom0.exe` is relative to the root)."""
        p = Path(native_path(text))
        if p.is_absolute():
            return p
        if (Path.cwd() / p).exists():
            return (Path.cwd() / p).resolve()
        return self.root / p

    def _std_root_args(self, std_root):
        """`--std-root <dir>` is passed when given explicitly, or when the default `std` exists
        (before std/ exists no compiler could use it, and passing it would only break option
        parsing of a compiler that predates T060)."""
        if std_root is not None:
            return ["--std-root", std_root]
        if (self.root / "std").is_dir():
            return ["--std-root", "std"]
        return []

    def compiler_cmd(self, *args):
        return exe_cmd(self.compiler) + [str(a) for a in args]

    @property
    def features(self):
        """Capability names advertised by `<compiler> --features` (one per line). A missing,
        failing or non-answering compiler advertises nothing: never an error."""
        if self._features is None:
            feats = set()
            try:
                r = run_proc(self.compiler_cmd("--features"), 20, self.root)
                if r.spawn_error is None and not r.timed_out and r.rc == 0:
                    for line in r.out.decode("utf-8", "replace").splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            feats.add(line.split()[0].rstrip(":,"))
            except Exception:
                feats = set()
            self._features = feats
        return self._features

    def step_timeout(self, test):
        t = test.timeout if test.timeout else DEFAULT_TIMEOUT
        return t * self.timeout_scale

    def input_arg(self, test):
        """The path given to the compiler: relative to the root with forward slashes if possible."""
        p = Path(test.input)
        try:
            return p.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(p)

    def common_flags(self, test, extra=()):
        flags = list(self.std_root_args)
        if test.target:
            flags += ["--target", test.target]
        flags += test.flags
        flags += list(extra)
        return flags

    def program_env(self, test):
        env = dict(os.environ)
        if 'AXIOM_STD' not in env and os.path.isdir('std'):
            env['AXIOM_STD'] = 'std'
        if not test.env:
            return env
        env.update(test.env)
        return env


    # -- skip logic common to all kinds -----------------------------------------------------

    def common_skip(self, test):
        for r in test.requires:
            if r in self.exclude_requires:
                return "requires %s (excluded for this compiler)" % r
        for what, name in test.skip_unless:
            if what == "tool" and shutil.which(name) is None:
                return "tool %s not found" % name
            if what == "feature" and name not in self.features:
                return "compiler lacks feature %s" % name
        return None

    # -- entries ----------------------------------------------------------------------------

    def entries_for(self, test, bless=False):
        if test.errors:
            return [Entry(test, "directives",
                          preset=failed("invalid test file: " + "; ".join(test.errors)))]
        if bless and test.kind != "golden" and not (test.kind == "exec" and test.stdout_file is not None):
            return []
        skip = self.common_skip(test)
        kind = test.kind
        if kind == "exec":
            return [Entry(test, "", self._with_skip(skip, lambda: self.run_exec(test, bless=bless)))]
        if kind == "ui":
            return [Entry(test, "", self._with_skip(skip, lambda: self.run_ui(test)))]
        if kind == "golden":
            exts = test.golden_exts
            if not exts:
                return [Entry(test, "", preset=failed(
                    "golden test has no sibling golden file (x.tokens, x.ast, ...) and no `emit:`"))]
            return [Entry(test, e, self._with_skip(skip, lambda e=e: self.run_golden(test, e, bless)))
                    for e in exts]
        if kind == "diff":
            return [Entry(test, "diff", self._with_skip(skip, lambda: self.run_diff(test)))]
        if kind == "run":
            return self.run_entries(test, skip)
        return [Entry(test, "", preset=failed("unknown test kind"))]

    def _with_skip(self, skip, fn):
        if skip:
            return lambda: skipped(skip)
        return fn

    def run_entries(self, test, skip):
        raw_modes = test.modes or list(MODES)
        modes = [m for m in MODES if m in raw_modes]
        variants = []  # (label, mode, extra flags)
        has_opt_flag = any(f.startswith("-O") for f in test.flags)
        for m in modes:
            variants.append((m, m, []))
            if m == "native" and not has_opt_flag and "opt" in self.features:
                variants.append(("native-O1", "native", ["-O1"]))
        ctx = {"interp_obs": None}
        entries = []
        for label, mode, extra in variants:
            if skip:
                run = (lambda s=skip: skipped(s))
            elif mode == "native" and test.native_after:
                run = (lambda t=test.native_after: skipped("native after " + t))
            elif mode not in self.features:
                run = (lambda m=mode: skipped("mode unavailable: " + m))
            elif label == "native-O1" and "native" not in self.features:
                run = (lambda: skipped("mode unavailable: native"))
            else:
                run = (lambda m=mode, x=extra, lbl=label: self.run_program(test, m, x, lbl, ctx))
            entries.append(Entry(test, label, run))
        return entries

    # -- program execution ------------------------------------------------------------------

    def new_tmp(self):
        return Path(tempfile.mkdtemp(prefix="axtest-"))

    def compile_failure(self, test, r, what):
        """Common handling of a compiler step; returns an Outcome for an abnormal step or None."""
        if r.spawn_error:
            return failed("cannot execute %s: %s" % (what, r.spawn_error))
        if ICE_BANNER_RE.search(r.err):
            return Outcome("CRASH", "internal compiler error in %s: %s" % (what, render(r.err, 200)))
        if r.timed_out:
            return Outcome("TIMEOUT", "%s did not finish within %gs" % (what, self.step_timeout(test)))
        if is_crash_status(r.rc):
            return Outcome("CRASH", "%s died with status %s" % (what, r.rc))
        return None

    def exec_variant(self, test, mode, extra, expected_exit):
        """Compile (native) and run one variant. Returns (Outcome, None) for an abnormal result or
        (None, Observed) when the program ran."""
        timeout = self.step_timeout(test)
        flags = self.common_flags(test, extra)
        inp = self.input_arg(test)
        env = self.program_env(test)
        if mode == "interp":
            cmd = self.compiler_cmd("run", "--interp", *flags, inp)
            if test.args:
                cmd += ["--"] + test.args
            r = run_proc(cmd, timeout, self.root, stdin=test.stdin, env=env)
            bad = self.compile_failure(test, r, "`axiom0 run --interp`")
            if bad is None and r.rc == INTERP_LIMIT_EXIT and INTERP_LIMIT_CODE_PREFIX in r.err \
                    and expected_exit != INTERP_LIMIT_EXIT:
                bad = Outcome("TIMEOUT", "interpreter limit reached (exit 124): " + render(r.err, 200))
            if bad is None and is_crash_status(r.rc) and r.rc != expected_exit:
                bad = Outcome("CRASH", "interpreter run died with status %s" % r.rc)
            if bad:
                return bad, None
            return None, Observed(r.rc, r.out, r.err, cmd)
        tmp = self.new_tmp()
        try:
            exe = tmp / ("prog" + self.exe_suffix)
            bcmd = self.compiler_cmd("build", *flags, "-o", str(exe), inp)
            r = run_proc(bcmd, timeout, self.root)
            bad = self.compile_failure(test, r, "`axiom0 build`")
            if bad:
                return bad, None
            if r.rc != 0:
                return failed("build failed (exit %d): %s" % (r.rc, render(r.err, 300))), None
            if not exe.exists():
                return failed("build exited 0 but wrote no executable at the -o path"), None
            cmd = exe_cmd(exe) + test.args
            r = run_proc(cmd, timeout, self.root, stdin=test.stdin, env=env)
            if r.spawn_error:
                return failed("cannot execute the built program: " + r.spawn_error), None
            if r.timed_out:
                return Outcome("TIMEOUT", "program did not finish within %gs" % timeout), None
            if is_crash_status(r.rc) and r.rc != expected_exit:
                return Outcome("CRASH", "program died with status %s" % r.rc), None
            return None, Observed(r.rc, r.out, r.err, cmd)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def judge(self, test, obs, expected_exit):
        """Compare an Observed run with the exit/stdout/stderr expectations of the test."""
        if obs.rc != expected_exit:
            return failed("exit code %s, expected %s; stderr: %s" % (obs.rc, expected_exit, render(obs.err, 300)))
        problems = []
        if test.stdout_file is not None:
            gf = test.path.parent / test.stdout_file
            if not gf.exists():
                problems.append("stdout-file %s does not exist (run with --bless and review it)" % test.stdout_file)
            else:
                exp = gf.read_bytes()
                if exp != obs.out:
                    problems.append(byte_diff(exp, obs.out, "%s output" % test.stdout_file))
        for what, exp, act in (("stdout", test.stdout, obs.out), ("stderr", test.stderr, obs.err)):
            if exp is not None and exp != act:
                problems.append(byte_diff(exp, act, what))
        for what, needles, act in (("stdout", test.stdout_contains, obs.out),
                                   ("stderr", test.stderr_contains, obs.err)):
            for n in needles:
                if n not in act:
                    problems.append("%s does not contain %s (got %s)" % (what, render(n, 80), render(act, 120)))
        if problems:
            return failed(problems[0] if len(problems) == 1 else "%d mismatches" % len(problems),
                          "\n".join(problems))
        return passed()

    def run_program(self, test, mode, extra, label="", ctx=None):
        expected = 0 if test.exit_code is None else test.exit_code
        bad, obs = self.exec_variant(test, mode, extra, expected)
        if bad:
            return bad
        res = self.judge(test, obs, expected)
        if mode == "interp":
            is_limit = (obs.rc == INTERP_LIMIT_EXIT and INTERP_LIMIT_CODE_PREFIX in obs.err)
            if ctx is not None and not is_limit and res.state == "PASS":
                ctx["interp_obs"] = obs
            return res
        if ctx is not None and ctx.get("interp_obs") is not None:
            iobs = ctx["interp_obs"]
            if obs.rc != iobs.rc:
                return failed("interp/native disagree: interp exit %s, %s exit %s; stderr: %s"
                              % (iobs.rc, label or mode, obs.rc, render(obs.err, 300)))
            if obs.out != iobs.out:
                diff = byte_diff(iobs.out, obs.out, "stdout")
                return failed("interp/native disagree: " + diff, diff)
        return res

    def run_diff(self, test):
        variants = []  # (label, mode, extra)
        feats = self.features
        if "interp" in feats:
            variants.append(("interp", "interp", []))
        if "native" in feats and not test.native_after:
            variants.append(("native-O0", "native", ["-O0"]))
            if "opt" in feats:
                variants.append(("native-O1", "native", ["-O1"]))
        if len(variants) < 2:
            return skipped("fewer than two executors available (%s)" %
                           (", ".join(v[0] for v in variants) or "none"))
        expected = 0 if test.exit_code is None else test.exit_code
        observed = []
        for label, mode, extra in variants:
            bad, obs = self.exec_variant(test, mode, extra, expected)
            if bad:
                return Outcome(bad.state, "%s: %s" % (label, bad.msg))
            observed.append((label, obs))
        base_label, base = observed[0]
        for label, obs in observed[1:]:
            if obs.rc != base.rc:
                return failed("%s exit %s but %s exit %s" % (base_label, base.rc, label, obs.rc))
            if obs.out != base.out:
                return failed("stdout of %s and %s disagree" % (base_label, label),
                              byte_diff(base.out, obs.out, "stdout"))
        if test.exit_code is not None or test.stdout is not None or test.stderr is not None \
                or test.stdout_contains or test.stderr_contains:
            return self.judge(test, base, expected)
        return passed()

    # -- ui ---------------------------------------------------------------------------------

    def run_ui(self, test):
        cmd = self.compiler_cmd("check", "--json", *self.common_flags(test), self.input_arg(test))
        r = run_proc(cmd, self.step_timeout(test), self.root, env=self.program_env(test))
        bad = self.compile_failure(test, r, "`axiom0 check`")
        if bad:
            return bad
        doc = parse_diag_json(r.err)
        if doc is None:
            return failed("no schema-1 JSON diagnostics document on stderr (exit %s): %s"
                          % (r.rc, render(r.err, 200)))
        actual = []
        for d in doc.get("diagnostics", []):
            prim = d.get("primary") or {}
            actual.append((prim.get("file"), d.get("severity"), d.get("code"), prim.get("line")))
        unmatched_expected = list(test.annotations)
        unexpected = []
        for afile, sev, code, line in actual:
            found = None
            for i, (efile, esev, ecode, eline) in enumerate(unmatched_expected):
                if esev == sev and ecode == code and (eline is None or eline == line) and \
                        (efile is None or (afile and (afile.replace("\\", "/") == efile
                                                      or afile.replace("\\", "/").endswith("/" + efile)))):
                    found = i
                    break
            if found is None:
                unexpected.append("%s %s at %s" % (sev.upper() if sev else "?", code,
                                                   "line %s" % line if line else "no position"))
            else:
                del unmatched_expected[found]
        missing = ["%s %s at %s" % (sev.upper(), code, "line %s" % line if line else "any position")
                   for (_f, sev, code, line) in unmatched_expected]
        problems = []
        if missing:
            problems.append("missing diagnostics: " + "; ".join(missing))
        if unexpected:
            problems.append("unexpected diagnostics: " + "; ".join(unexpected))
        errors = sum(1 for a in actual if a[1] == "error")
        want_rc = 1 if errors else 0
        if r.rc != want_rc:
            problems.append("exit code %s, expected %s for %d error(s)" % (r.rc, want_rc, errors))
        if problems:
            return failed(" | ".join(problems))
        return passed()

    # -- golden -----------------------------------------------------------------------------

    def run_golden(self, test, ext, bless):
        cmd = self.compiler_cmd("inspect", "--emit=" + ext, *self.common_flags(test), self.input_arg(test))
        r = run_proc(cmd, self.step_timeout(test), self.root, env=self.program_env(test))
        bad = self.compile_failure(test, r, "`axiom0 inspect --emit=%s`" % ext)
        if bad:
            return bad
        expected_exit = 0 if test.exit_code is None else test.exit_code
        if r.rc != expected_exit:
            return failed("inspect exit code %s, expected %s; stderr: %s" % (r.rc, expected_exit, render(r.err, 300)))
        golden = test.path.with_name(test.path.stem + "." + ext)
        if bless:
            old = golden.read_bytes() if golden.exists() else None
            if old == r.out:
                return passed("unchanged")
            golden.write_bytes(r.out)
            return passed("blessed (%s)" % ("new file" if old is None else "updated"))
        if not golden.exists():
            return failed("golden file %s does not exist (run with --bless and review it)" % golden.name)
        exp = golden.read_bytes()
        if exp != r.out:
            return failed(byte_diff(exp, r.out, "%s output" % golden.name),
                          byte_diff(exp, r.out, "%s output" % golden.name))
        return passed()

    # -- exec manifests ---------------------------------------------------------------------

    def run_exec(self, test, bless=False):
        tmp = self.new_tmp()
        try:
            subst = {
                "compiler": self.compiler.as_posix(),
                "build": self.build_dir.as_posix(),
                "root": self.root.as_posix(),
                "test_dir": test.path.parent.as_posix(),
                "tmp": tmp.as_posix(),
                "std_root": (self.root / "std").as_posix(),
            }
            try:
                raw_tokens = shlex.split(test.cmd)
            except ValueError as e:
                return failed("cannot split cmd: %s" % e)
            # placeholders are substituted per token after splitting, so paths with spaces stay whole
            tokens = []
            for tok in raw_tokens:
                for k, v in subst.items():
                    tok = tok.replace("{" + k + "}", v)
                m = re.search(r"\{[a-z_]+\}", tok)
                if m:
                    return failed("unknown placeholder %s in cmd (known: %s)" % (m.group(0), ", ".join(sorted(subst))))
                tokens.append(tok)
            tokens = resolve_exec_tokens(tokens, self.root) + test.args
            r = run_proc(tokens, self.step_timeout(test), self.root, stdin=test.stdin,
                         env=self.program_env(test))
            if r.spawn_error:
                return failed("cannot execute `%s`: %s" % (tokens[0] if tokens else "", r.spawn_error))
            if r.timed_out:
                return Outcome("TIMEOUT", "command did not finish within %gs" % self.step_timeout(test))
            expected = 0 if test.exit_code is None else test.exit_code
            if is_crash_status(r.rc) and r.rc != expected:
                return Outcome("CRASH", "command died with status %s" % r.rc)
            if bless and test.stdout_file is not None:
                if r.rc != expected:
                    return failed("exit code %s, expected %s; stderr: %s" % (r.rc, expected, render(r.err, 300)))
                gf = test.path.parent / test.stdout_file
                old = gf.read_bytes() if gf.exists() else None
                if old == r.out:
                    return passed("unchanged")
                gf.write_bytes(r.out)
                return passed("blessed (%s)" % ("new file" if old is None else "updated"))
            return self.judge(test, Observed(r.rc, r.out, r.err, tokens), expected)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def parse_diag_json(err):
    """The schema-1 diagnostics document (AXD-063): the last stderr line that is a JSON object."""
    for line in reversed(err.split(b"\n")):
        line = line.strip()
        if not line.startswith(b"{"):
            continue
        try:
            doc = json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(doc, dict) and isinstance(doc.get("diagnostics"), list):
            return doc
    return None


def apply_xfail(test, out):
    if test.xfail is None:
        return out
    task, reason = test.xfail
    if out.state == "PASS":
        return Outcome("XPASS", "expected failure (%s: %s) passed; remove the `xfail:` directive" % (task, reason))
    if out.state == "FAIL":
        return Outcome("XFAIL", "%s: %s -- %s" % (task, reason, out.msg.splitlines()[0] if out.msg else ""), out.detail)
    return out


def execute_entry(entry):
    t0 = time.time()
    if entry.preset is not None:
        out = entry.preset
    else:
        try:
            out = apply_xfail(entry.test, entry.run())
        except Exception as e:  # a bug in the runner must not look like a pass
            out = failed("runner error: %s: %s" % (type(e).__name__, e))
    return entry, out, int((time.time() - t0) * 1000)


def execute_group(group):
    return [execute_entry(e) for e in group]


def is_weak_native_evidence(entry, out):
    t = entry.test
    if t.kind != "run" or entry.label not in ("native", "native-O1"):
        return False
    if out.state == "SKIP":
        return False
    if t.exit_code is not None and t.exit_code != 0:
        return False
    if (t.stdout is not None or t.stderr is not None or t.stdout_contains
            or t.stderr_contains or t.stdout_file is not None):
        return False
    return True


# ----------------------------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------------------------

def count(results):
    c = {s: 0 for s in STATES}
    for _e, out, _ms in results:
        c[out.state] += 1
    fail = c["FAIL"] + c["XPASS"] + c["CRASH"] + c["TIMEOUT"]
    total = len(results)
    return c, fail, total


def total_line(results):
    c, fail, total = count(results)
    return "TOTAL %d PASS %d FAIL %d SKIP %d XFAIL %d" % (total, c["PASS"], fail, c["SKIP"], c["XFAIL"])


def build_parser():
    ap = argparse.ArgumentParser(
        prog="axtest.py",
        description="Axiom test runner. Discovers tests/**.ax, tests/**.test and project directories.")
    ap.add_argument("filters", nargs="*", metavar="FILTER",
                    help="run only tests whose id contains any FILTER (same as --filter)")
    ap.add_argument("--filter", action="append", default=[], metavar="TEXT",
                    help="run only tests whose id (path under tests/) contains TEXT; repeatable")
    ap.add_argument("--compiler", default=os.environ.get("AXIOM0") or
                    ("build/axiom0.exe" if os.name == "nt" else "build/axiom0"),
                    help="compiler under test (default build/axiom0.exe or $AXIOM0; a .py file is run with python)")
    ap.add_argument("--build-dir", default=None, help="the {build} placeholder of exec manifests "
                    "(default: the directory of --compiler)")
    ap.add_argument("--std-root", default=None, help="passed to the compiler as --std-root "
                    "(default: `std` when the directory exists)")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent),
                    help="repository root; tests are read from <root>/tests (default: parent of tools/)")
    ap.add_argument("-j", "--jobs", type=int, default=min(8, os.cpu_count() or 1), metavar="N",
                    help="tests run in parallel (default min(8, cpus))")
    ap.add_argument("--timeout-scale", type=float, default=1.0, metavar="N",
                    help="multiply every step timeout by N (default 1)")
    ap.add_argument("--exclude-requires", action="append", default=[], metavar="NAME",
                    help="SKIP tests with `requires: NAME` (e.g. axiom0-internal when testing axiomc)")
    ap.add_argument("--verbose", "-v", action="store_true", help="print every result and failure details")
    ap.add_argument("--json", action="store_true",
                    help="machine-readable results as one JSON document on stdout "
                         "(the TOTAL line goes to stderr)")
    ap.add_argument("--bless", action="store_true",
                    help="rewrite the golden files of the selected golden tests (review the diff!)")
    ap.add_argument("--list", action="store_true", help="list the selected test ids and exit")
    ap.add_argument("--list-directive", metavar="NAME[:VALUE]",
                    help="list files that carry the directive (e.g. native-after:T033) and exit")
    ap.add_argument("--exe-suffix", default=".exe" if os.name == "nt" else "",
                    help=argparse.SUPPRESS)  # self-test hook: stub compilers write .py "executables"
    return ap


def select(tests, filters):
    if not filters:
        return tests
    return [t for t in tests if any(f in t.id for f in filters)]


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass
    ap = build_parser()
    opts = ap.parse_args(argv)
    if opts.jobs < 1 or opts.timeout_scale <= 0:
        ap.error("-j must be >= 1 and --timeout-scale > 0")
    root = Path(native_path(opts.root)).resolve()
    tests = select(discover(root / "tests"), opts.filters + opts.filter)

    if opts.list_directive:
        name, _, value = opts.list_directive.partition(":")
        hits = sorted(t.id for t in tests if t.has_directive(name, value.strip() or None))
        for h in hits:
            print(h)
        return 0

    runner = Runner(opts)
    entry_groups = []
    for t in tests:
        grp = runner.entries_for(t, bless=opts.bless)
        if grp:
            entry_groups.append(grp)
    if opts.list:
        for grp in entry_groups:
            for e in grp:
                print(e.name)
        return 0

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=opts.jobs) as pool:
        for grp_res in pool.map(execute_group, entry_groups):
            results.extend(grp_res)
    results.sort(key=lambda r: (r[0].test.id, r[0].label))

    weak_entries = [e for e, o, _ms in results if is_weak_native_evidence(e, o)]
    line = total_line(results)
    if opts.json:
        counts, fail, total = count(results)
        doc = {
            "schema": 1,
            "tool": "axtest",
            "compiler": runner.compiler.as_posix(),
            "features": sorted(runner.features),
            "results": [
                {"id": e.test.id, "mode": e.label, "state": o.state, "message": o.msg, "ms": ms,
                 "weak_native_evidence": is_weak_native_evidence(e, o)}
                for e, o, ms in results
            ],
            "counts": {"total": total, "pass": counts["PASS"], "fail": fail, "skip": counts["SKIP"],
                       "xfail": counts["XFAIL"], "xpass": counts["XPASS"], "crash": counts["CRASH"],
                       "timeout": counts["TIMEOUT"], "weak_native": len(weak_entries)},
            "total_line": line,
        }
        sys.stdout.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        sys.stdout.flush()
        print(line, file=sys.stderr)
    else:
        for e, o, ms in results:
            interesting = o.state in ("FAIL", "XPASS", "CRASH", "TIMEOUT")
            if not (interesting or opts.verbose):
                continue
            text = "%-7s %s" % (o.state, e.name)
            if o.msg:
                text += ": " + o.msg
            print(text)
            if opts.verbose and o.detail and o.detail != o.msg:
                for ln in o.detail.splitlines():
                    print("        " + ln)
        if opts.verbose:
            for e in weak_entries:
                print("%-7s %s" % ("WEAK", e.name))
        print("WEAK-NATIVE %d" % len(weak_entries))
        print(line)
        sys.stdout.flush()
    _c, fail, _t = count(results)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
