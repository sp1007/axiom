#!/usr/bin/env python3
"""axtest_cache - the sound incremental per-test result cache of tools/axtest.py (T437a, ADR-0041 §4).

A cache entry lets a later run report a PASS without executing the test. The soundness conditions S1-S8 of
ADR-0041 §4 are implemented here; the runner (tools/axtest.py) only decides which test groups are looked up
and hands the results back for storing.

Layout of `<cache-dir>` (default: `<main checkout>/_workspaces/artifacts/axtest-cache/`, git-ignored):

    entries/<pk[:2]>/<prekey>/<fullkey>.json   one file per entry (S7), written atomically (temp + rename)
    deps-index/<sha256(test id)[:2]>/<sha256(test id)>.json   newest exact dependency list per test id
                                                (used by `--affected` rule 1)
    probe.json        `--dep-file` support per compiler binary hash (S2 probe)
    durations.json    per-id/per-mode durations in ms (longest-first scheduling, `--smoke --check`)

Key (S1). `prekey = sha256(canonical(pre-material))`, where the pre-material holds everything that is known
before the run: schema version, sha256 of the compiler binary, sha256 of every runner module
(`tools/axtest*.py`), test id, test kind and the labels (modes) of the cached entries, the features the
compiler advertises, the behaviour-changing runner options (`--std-root`, `--timeout-scale`, `--exe-suffix`,
`--exclude-requires`), the environment the runner passes (`AXIOM_STD` and every `AXIOM*`/`AX_*` variable), the
argv determinants (input argument, flags, program args), the test file bytes (a project test: its whole tree),
every expectation file (golden siblings, `stdout-file:`), the host platform tag and the dependency source.
`fullkey = sha256(canonical(prekey, dependency list with the sha256 of every dependency))`. The dependency list
is either the compiler-reported list (`dep_source: exact`, `--dep-file`, S2) or the sound superset
(`dep_source: superset`): the test directory tree, the input file's directory tree when the input lies
outside it, the whole std root, every `cache-inputs:` path, and the presence/bytes of `axiom.toml` in every
ancestor directory of the test up to the repository root. An exact list is extended by the name listing of
every directory that holds a dependency (a file created next to a loaded module can change module
resolution) and by the same `axiom.toml` markers.

Lookup: the candidates under `entries/<prekey>/` are re-validated by recomputing the full key from the
current bytes of the dependencies recorded in each candidate; a candidate whose recomputed key differs is a
miss (it may still be valid for another checkout and is left for LRU pruning). An unreadable or
inconsistent file is a miss and is deleted (S7).

Assumption A1 (recorded in the T437a report): a test result does not depend on the absolute path of the
checkout (the root path is not part of the key, so snapshots share entries). The verification sample (S6)
is the guard against violations.

Python 3 standard library only.
"""

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

SCHEMA = 1
MAX_CANDIDATES = 8
DEFAULT_MAX_BYTES = 1 << 30           # LRU bound of the entries/ tree (1 GiB)
NONDET_STD_DIRS = ("thread", "sync", "async", "time")   # S4: scheduling and timing are not inputs
NONDET_SOURCE_RE = re.compile(r"\bstd\.(?:thread|sync|async|time)\b|\basync\b|\bawait\b|\bspawn\b")
STD_REF_RE = re.compile(r"\bstd(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
TREE_SKIP = {".git"}
# S4, OS thread/sync/timer/clock/environment/randomness/process bindings (T437a QA F3, F5).
#
# Deny by default, derived structurally from the sources (no list of "bad" names): a *leaf binding* is a function
# whose behaviour the program text does not define --
#   * a function declared inside an `extern "<abi>" { ... }` block, or a body-less `extern "<abi>" fn X(...);`
#     (OS / C FFI, e.g. `CreateThread`, `GetTickCount64`, `Sleep`);
#   * an `@intrinsic` function (compiler/host intrinsics, e.g. `monotonic_ns`, `size_of`);
#   * a host provider `__ax_host_<name>` (defined in std/sys/**, bound to intrinsic `<name>` by the compiler),
#     and any mention of `__ax_host_<name>` (normalised to `<name>`).
# A leaf binding is deterministic only when its name is in DETERMINISTIC_BINDINGS below (a positive list of
# memory/layout, heap, process-exit, console/file output, file-system and argument bindings whose results depend
# only on the program and the files the test controls). Every other leaf binding -- whatever its name, including
# any binding added later -- is nondeterministic (threads, sync/futex, sleep/wait, clocks/counters,
# environment, process ids, module paths/handles, randomness, dynamic loading...). A test is never cached when
#   1. its own sources declare a leaf binding that is not on the list (FFI, `@intrinsic`, `__ax_host_*`), or
#      mention a nondeterministic leaf binding declared anywhere in std (or `__ax_host_<nondet>`), or import one;
#   2. a std file it reaches (transitively, through `std.a.b` module references) *uses* a nondeterministic leaf
#      binding: mentions it other than in its own declaration (call, `use` re-export, alias, function value);
#   3. (exact dependency lists) a reported dependency lies under std/{thread,sync,async,time} or is a std file
#      that uses a nondeterministic leaf binding (rule 2 applied to the loaded file itself).
# The old word filter (`nondet_name`) is kept as an extra net for imported names.
DETERMINISTIC_BINDINGS = frozenset({
    # layout / memory / object intrinsics (values depend only on the program)
    "size_of", "align_of", "needs_drop", "address_of", "address_of_mut", "ptr_copy", "ptr_copy_nonoverlapping",
    "ptr_write_bytes", "drop_in_place", "forget", "transmute", "zeroed", "uninit", "type_name", "type_id",
    "unreachable", "abort", "panic", "assert", "debug_assert", "null", "null_mut", "is_null", "ptr_add",
    "ptr_sub", "ptr_offset",
    # heap (the program's own allocations)
    "heap_alloc", "heap_free", "heap_realloc", "allocate", "deallocate", "reallocate",
    "HeapAlloc", "HeapFree", "HeapReAlloc", "GetProcessHeap", "LocalFree",
    # console / standard streams output and process exit
    "stdio", "write", "print", "print_int", "exit", "ExitProcess", "GetStdHandle", "WriteFile", "WriteConsoleW",
    "GetConsoleMode",
    # files and directories the test itself creates/reads (contents are inputs of the test)
    "open", "read", "close", "file_size", "remove", "mkdir", "metadata", "dir_open", "dir_next", "dir_close",
    "CreateFileW", "ReadFile", "SetFilePointer", "GetFileSizeEx", "DeleteFileW", "CreateDirectoryW",
    "RemoveDirectoryW", "DeleteFileA", "CreateFileA", "FindFirstFileW", "FindNextFileW", "FindClose", "GetFileAttributesExW", "CloseHandle",
    "GetLastError",
    # command-line arguments (fixed by the test's directives)
    "args_count", "arg", "GetCommandLineW", "CommandLineToArgvW",
    # pure C library functions used by FFI tests
    "strlen", "strcmp", "strncmp", "memcpy", "memmove", "memset", "memcmp", "abs", "labs", "llabs", "lstrlenW",
    "lstrlenA", "MultiByteToWideChar", "WideCharToMultiByte",
})
HOST_PROVIDER_PREFIX = "__ax_host_"
IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
COMMENT_RE = re.compile(r'"(?:\\.|[^"\\\n])*"|//[^\n]*|/\*.*?\*/', re.S)
EXTERN_BLOCK_RE = re.compile(r'\bextern\s+"[^"\n]*"\s*\{')
EXTERN_FN_RE = re.compile(r'\bextern\s+"[^"\n]*"\s+fn\s+(' + IDENT + r')\s*(?:<[^>{;]*>)?\s*\([^){;]*\)[^{;]*;')
INTRINSIC_FN_RE = re.compile(r"@intrinsic\b(?:\s*\([^)]*\))?(?:\s+@" + IDENT + r"(?:\s*\([^)]*\))?)*\s+"
                             r"(?:pub(?:\s*\([^)]*\))?\s+)?(?:(?:unsafe|const|async|extern\s+\"[^\"\n]*\")\s+)*"
                             r"fn\s+(" + IDENT + r")")
HOST_NAME_RE = re.compile(r"(?<![A-Za-z0-9_])" + HOST_PROVIDER_PREFIX + r"([A-Za-z0-9_]+)")
FN_NAME_RE = re.compile(r"\bfn\s+(" + IDENT + r")")
NONDET_WORDS = {"time", "times", "clock", "tick", "ticks", "counter", "monotonic", "env", "environment",
                "getenv", "random", "rand", "pid", "perf", "performance", "timeout", "timed", "rdtsc",
                "thread", "sleep", "wait", "futex", "yield", "spawn", "join"}
NAME_WORD_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+")
USE_LAST_RE = re.compile(r"\buse\s+[A-Za-z_][A-Za-z0-9_.]*\.([A-Za-z_][A-Za-z0-9_]*)")


def nondet_name(name):
    """A name about time/clock/environment/randomness/process id/threads, judged by its words
    (`GetTickCount64` -> get tick count 64, `env_get`, `GetCurrentThreadId`), so that e.g.
    `capability_grant_check_runtime` does not match. Only an extra net; the sound rule is deny-by-default."""
    words = [w.lower() for w in NAME_WORD_RE.findall(name)]
    return any(w in NONDET_WORDS for w in words) or "processid" in "".join(words)


def binding_key(name):
    """`__ax_host_monotonic_ns` -> `monotonic_ns` (a host provider implements the intrinsic of that name)."""
    return name[len(HOST_PROVIDER_PREFIX):] if name.startswith(HOST_PROVIDER_PREFIX) else name


# pure integer/pointer arithmetic intrinsics, one per primitive type (`wrapping_add_u64`, `count_ones_u8`, ...)
DETERMINISTIC_BINDING_RE = re.compile(
    r"(?:(?:wrapping|checked|saturating|overflowing|unchecked|exact)_(?:add|sub|mul|neg|div|rem|shl|shr|abs|pow)"
    r"|rotate_left|rotate_right|count_ones|count_zeros|leading_zeros|trailing_zeros|leading_ones|trailing_ones"
    r"|swap_bytes|reverse_bits|bswap|ctpop|ctlz|cttz|to_le|to_be|from_le|from_be)"
    r"(?:_(?:[iu](?:8|16|32|64|128|size)|f32|f64))?")


def binding_is_deterministic(name):
    k = binding_key(name)
    return k in DETERMINISTIC_BINDINGS or bool(DETERMINISTIC_BINDING_RE.fullmatch(k))


def strip_comments(text):
    """Source text without comments (string literals kept: `extern "system"` needs them); newlines kept."""
    def sub(m):
        s = m.group(0)
        if s.startswith('"'):
            return s
        return "\n" * s.count("\n") or " "
    return COMMENT_RE.sub(sub, text)


def _block_end(code, open_pos):
    """Index just after the `}` matching the `{` at open_pos (string literals skipped), or len(code)."""
    depth = 0
    i = open_pos
    n = len(code)
    while i < n:
        ch = code[i]
        if ch == '"':
            i += 1
            while i < n and code[i] != '"':
                i += 2 if code[i] == "\\" else 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def leaf_bindings(text):
    """{name: kind} of every leaf binding a source file declares (see the S4 comment): extern-block functions,
    body-less `extern "abi" fn`, `@intrinsic` functions and `__ax_host_*` providers (names as written)."""
    code = strip_comments(text)
    out = {}
    for m in EXTERN_BLOCK_RE.finditer(code):
        end = _block_end(code, m.end() - 1)
        for n in FN_NAME_RE.findall(code[m.end():end]):
            out.setdefault(n, "extern")
    for n in EXTERN_FN_RE.findall(code):
        out.setdefault(n, "extern")
    for n in INTRINSIC_FN_RE.findall(code):
        out.setdefault(n, "intrinsic")
    for n in FN_NAME_RE.findall(code):
        if n.startswith(HOST_PROVIDER_PREFIX):
            out.setdefault(n, "host-provider")
    return out


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def posix_rel(path, root):
    """`path` relative to `root` with forward slashes, or the absolute posix path when outside."""
    p = Path(path)
    try:
        return p.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def platform_tag():
    return "%s|%s|%s" % (platform.system(), platform.version(), platform.machine())


def git(root, *args):
    try:
        r = subprocess.run(["git", *args], cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def main_checkout(root):
    """The main working tree of the repository that `root` belongs to (a snapshot is a git worktree);
    `root` itself when it is not a git checkout."""
    common = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common:
        p = Path(common.strip())
        if p.name == ".git" and p.parent.is_dir():
            return p.parent
    return Path(root)


def default_cache_dir(root):
    return main_checkout(root) / "_workspaces" / "artifacts" / "axtest-cache"


# ----------------------------------------------------------------------------------------------
# Hashing with an in-process memo (one run; keyed by path, size and mtime)
# ----------------------------------------------------------------------------------------------

class Hasher:
    def __init__(self):
        self._files = {}
        self._lock = threading.Lock()

    def file(self, path):
        """sha256 of a file, or None when it does not exist / is not a file."""
        p = str(path)
        try:
            st = os.stat(p)
        except OSError:
            return None
        if not os.path.isfile(p):
            return None
        sig = (st.st_size, st.st_mtime_ns)
        with self._lock:
            got = self._files.get(p)
        if got is not None and got[0] == sig:
            return got[1]
        h = hashlib.sha256()
        try:
            with open(p, "rb") as f:
                while True:
                    b = f.read(1 << 20)
                    if not b:
                        break
                    h.update(b)
        except OSError:
            return None
        d = h.hexdigest()
        with self._lock:
            self._files[p] = (sig, d)
        return d

    def tree(self, path):
        """Digest of a directory tree: sorted relative paths with their sha256. Every file counts, dot-files,
        dot-directories and `__pycache__/` included (the compiler loads every `*.ax` of a project directory,
        whatever its name; T437a QA F1). Only a `.git` directory and Python byte-code (`*.pyc`, written by test
        generators while tests run, never read by the compiler) are skipped. A missing directory digests to
        `absent`."""
        base = Path(path)
        if not base.is_dir():
            return "absent"
        lines = []
        for dirpath, dirnames, filenames in os.walk(str(base)):
            dirnames[:] = sorted(d for d in dirnames if d not in TREE_SKIP)
            for fn in sorted(filenames):
                if fn.endswith(".pyc"):
                    continue
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, str(base)).replace("\\", "/")
                lines.append("%s\0%s\n" % (rel, self.file(fp) or "unreadable"))
        lines.sort()
        return sha256_bytes("".join(lines).encode("utf-8"))

    def dirlist(self, path):
        """Digest of the names in one directory (not recursive)."""
        p = Path(path)
        if not p.is_dir():
            return "absent"
        try:
            names = sorted(os.listdir(str(p)))
        except OSError:
            return "unreadable"
        return sha256_bytes("\n".join(names).encode("utf-8"))


# ----------------------------------------------------------------------------------------------
# Small file helpers
# ----------------------------------------------------------------------------------------------

def atomic_write_json(path, obj):
    """Write JSON atomically (temp file in the same directory + os.replace). Returns True on success."""
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    tmp = path.parent / (".tmp-%s-%s" % (os.getpid(), uuid.uuid4().hex))
    data = (json.dumps(obj, sort_keys=True, indent=0, ensure_ascii=True) + "\n").encode("utf-8")
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        for attempt in range(5):
            try:
                os.replace(str(tmp), str(path))
                return True
            except PermissionError:
                time.sleep(0.05 * (attempt + 1))   # Windows: a reader holds the target open
        return False
    except OSError:
        return False
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def read_json(path):
    try:
        with open(path, "rb") as f:
            return json.loads(f.read().decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def parse_dep_file(path):
    """`path sha256` per line (S2). Returns a list of (path, sha) or None when unreadable/malformed."""
    try:
        with open(path, "rb") as f:
            text = f.read().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(.*\S)\s+([0-9a-fA-F]{64})$", line)
        if not m:
            return None
        out.append((m.group(1), m.group(2).lower()))
    return out


# ----------------------------------------------------------------------------------------------
# Durations (per id / per mode, ms) for longest-first scheduling and the smoke bound
# ----------------------------------------------------------------------------------------------

def load_durations(cache_dir):
    d = read_json(Path(cache_dir) / "durations.json") if cache_dir else None
    if not isinstance(d, dict) or not isinstance(d.get("ids"), dict):
        return {}
    return d["ids"]


def save_durations(cache_dir, updates):
    """Merge {id: {label: ms}} into durations.json (re-read just before the atomic write)."""
    if not cache_dir or not updates:
        return
    cur = load_durations(cache_dir)
    for tid, labels in updates.items():
        slot = cur.setdefault(tid, {})
        for label, ms in labels.items():
            slot[label] = int(ms)
    atomic_write_json(Path(cache_dir) / "durations.json", {"schema": 1, "ids": cur})


def id_duration_ms(durations, tid):
    """Total recorded ms of all modes of an id, or None when unknown."""
    v = durations.get(tid)
    if not v:
        return None
    return sum(int(x) for x in v.values())


# ----------------------------------------------------------------------------------------------
# The cache
# ----------------------------------------------------------------------------------------------

class Producer:
    """Where entries of this run come from (S5)."""

    def __init__(self, root, compiler):
        self.root = Path(root)
        self.snapshot = None
        self.base = None
        self.changeset = None
        self.origin = "local"
        head = git(root, "rev-parse", "HEAD")
        if head:
            self.base = head.strip()
            self.changeset = changeset_digest(root)
        name = self.root.resolve().name
        comp_in_snapshot = any(part.startswith("build-snap-") for part in Path(compiler).resolve().parts)
        if name.startswith("build-snap-") and self.base and comp_in_snapshot:
            self.snapshot = name
            self.origin = "snapshot"
        elif name.startswith("build-snap-"):
            self.snapshot = name

    def as_dict(self):
        return {"origin": self.origin, "snapshot": self.snapshot, "base": self.base,
                "changeset": self.changeset}


def changed_paths(root):
    """Paths changed in the working tree of `root` relative to HEAD (tracked diff + untracked)."""
    out = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if out is None:
        return None
    paths = []
    parts = out.split("\0")
    i = 0
    while i < len(parts):
        rec = parts[i]
        i += 1
        if len(rec) < 4:
            continue
        st, p = rec[:2], rec[3:]
        paths.append(p)
        if st[0] in "RC":
            i += 1   # the source path of a rename/copy follows
    return sorted(set(paths))


def changeset_digest(root, hasher=None):
    hasher = hasher or Hasher()
    paths = changed_paths(root)
    if paths is None:
        return None
    lines = ["%s %s" % (p, hasher.file(Path(root) / p) or "deleted") for p in paths]
    return sha256_bytes("\n".join(lines).encode("utf-8"))


class Cache:
    """One run's view of the cache. Thread-safe for lookups and stores from the runner's worker threads."""

    def __init__(self, cache_dir, root, compiler, runner_files, read=True, write=True, gate=False,
                 max_bytes=DEFAULT_MAX_BYTES, log=None):
        self.dir = Path(cache_dir)
        self.root = Path(root).resolve()
        self.compiler = Path(compiler)
        self.read = read
        self.write = write
        self.gate = gate
        self.max_bytes = max_bytes
        self.hasher = Hasher()
        self.lock = threading.Lock()
        self.log = log or (lambda msg: None)
        self.stored = 0
        self.store_skipped = {}            # reason -> count
        self.rejected = {}                 # reason -> count (gate provenance etc.)
        self.deleted_corrupt = 0
        self._ancestor_memo = {}
        self.compiler_sha = self.hasher.file(self.compiler) or "missing"
        self.runner_sha = {}
        for f in sorted(runner_files):
            self.runner_sha[Path(f).name] = self.hasher.file(f) or "missing"
        self.producer = Producer(self.root, self.compiler)
        self.head = self.producer.base
        self.platform = platform_tag()
        self._dep_mode = None
        self._tree_memo = {}

    # -- S2 probe -------------------------------------------------------------------------------

    def dep_mode(self, compiler_cmd_fn, std_args):
        """`exact` when the compiler under test honours `--dep-file=<path>` (probed once per binary and
        recorded in probe.json by binary hash), else `superset`."""
        if self._dep_mode is not None:
            return self._dep_mode
        probe_path = self.dir / "probe.json"
        doc = read_json(probe_path) or {}
        known = doc.get(self.compiler_sha) if isinstance(doc, dict) else None
        if known in ("exact", "superset"):
            self._dep_mode = known
            return known
        mode = "superset"
        tmpdir = self.dir / ("probe-" + uuid.uuid4().hex)
        try:
            tmpdir.mkdir(parents=True, exist_ok=True)
            src = tmpdir / "probe.ax"
            src.write_bytes(b"// dep-file probe\nfn main() -> i32 {\n    0\n}\n")
            dep = tmpdir / "deps.txt"
            cmd = compiler_cmd_fn("check", "--dep-file=" + str(dep), *std_args, str(src))
            try:
                subprocess.run(cmd, cwd=str(self.root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               stdin=subprocess.DEVNULL, timeout=120)
            except (OSError, subprocess.TimeoutExpired):
                pass
            if dep.is_file() and parse_dep_file(dep) is not None:
                mode = "exact"
        except OSError:
            pass
        finally:
            for p in sorted(tmpdir.rglob("*"), reverse=True) if tmpdir.exists() else []:
                try:
                    p.unlink() if p.is_file() else p.rmdir()
                except OSError:
                    pass
            try:
                tmpdir.rmdir()
            except OSError:
                pass
        doc = read_json(probe_path) or {}
        if not isinstance(doc, dict):
            doc = {}
        doc[self.compiler_sha] = mode
        atomic_write_json(probe_path, doc)
        self._dep_mode = mode
        return mode

    # -- key material ---------------------------------------------------------------------------

    def rel(self, p):
        return posix_rel(p, self.root)

    def abs(self, rel):
        p = Path(rel)
        return p if p.is_absolute() else self.root / p

    def ancestor_toml_deps(self, start_dir):
        deps = []
        d = Path(start_dir).resolve()
        while True:
            try:
                d.relative_to(self.root)
            except ValueError:
                break
            deps.append(["file?", self.rel(d / "axiom.toml")])
            if d == self.root:
                break
            d = d.parent
        return deps

    def dep_digest(self, kind, rel, memo=False):
        p = self.abs(rel)
        if kind == "tree":
            if memo:
                # before the run (lookup/prepare phase) a tree is walked once per run; the after-run check of
                # S2 always walks again (memo=False)
                with self.lock:
                    got = self._tree_memo.get(str(p))
                if got is None:
                    got = self.hasher.tree(p)
                    with self.lock:
                        self._tree_memo[str(p)] = got
                return got
            return self.hasher.tree(p)
        if kind == "dirlist":
            return self.hasher.dirlist(p)
        if kind in ("file", "file?"):
            return self.hasher.file(p) or "absent"
        return "unknown-kind"

    def with_digests(self, deps, memo=False):
        """[[kind, rel], ...] -> sorted unique [[kind, rel, digest], ...]."""
        uniq = sorted({(k, r) for k, r in deps})
        return [[k, r, self.dep_digest(k, r, memo)] for k, r in uniq]

    @staticmethod
    def full_key(prekey, deps_with_digests):
        return sha256_bytes(canonical({"prekey": prekey, "deps": deps_with_digests}).encode("utf-8"))

    # -- lookup ---------------------------------------------------------------------------------

    def _entry_dir(self, prekey):
        return self.dir / "entries" / prekey[:2] / prekey

    def _record_sha(self, rec):
        body = {k: v for k, v in rec.items() if k != "record_sha256"}
        return sha256_bytes(canonical(body).encode("utf-8"))

    def is_ancestor(self, base):
        if not base or not self.head:
            return False
        if base == self.head:
            return True
        with self.lock:
            if base in self._ancestor_memo:
                return self._ancestor_memo[base]
        try:
            r = subprocess.run(["git", "merge-base", "--is-ancestor", base, self.head], cwd=str(self.root),
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
            ok = r.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok = False
        with self.lock:
            self._ancestor_memo[base] = ok
        return ok

    def _reject(self, reason):
        with self.lock:
            self.rejected[reason] = self.rejected.get(reason, 0) + 1

    def lookup(self, prekey, pre):
        """The valid record for `prekey`, or None. Corrupt files are deleted."""
        if not self.read:
            return None
        d = self._entry_dir(prekey)
        try:
            files = [d / n for n in os.listdir(str(d)) if n.endswith(".json") and not n.startswith(".")]
        except OSError:
            return None
        try:
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        except OSError:
            pass
        for f in files[:MAX_CANDIDATES]:
            rec = read_json(f)
            ok = (isinstance(rec, dict) and rec.get("schema") == SCHEMA and rec.get("prekey") == prekey
                  and isinstance(rec.get("deps"), list) and isinstance(rec.get("results"), dict)
                  and rec.get("record_sha256") == self._record_sha(rec)
                  and f.stem == rec.get("key") and rec.get("pre") == pre)
            if ok:
                for r in rec["results"].values():
                    if not isinstance(r, dict) or r.get("state") != "PASS":
                        ok = False
            if not ok:
                self._delete(f)
                with self.lock:
                    self.deleted_corrupt += 1
                continue
            try:
                deps = [[str(k), str(r)] for k, r, _d in rec["deps"]]
            except (TypeError, ValueError):
                self._delete(f)
                continue
            if self.full_key(prekey, self.with_digests(deps, memo=True)) != rec["key"]:
                continue        # inputs changed since; not corrupt
            if self.gate:
                prod = rec.get("producer") or {}
                if prod.get("origin") != "snapshot":
                    self._reject("origin-local")
                    continue
                if not self.is_ancestor(prod.get("base")):
                    self._reject("base-not-ancestor")
                    continue
            try:
                os.utime(str(f), None)          # LRU: a hit is a use
            except OSError:
                pass
            return rec
        return None

    def _delete(self, f):
        try:
            os.remove(str(f))
        except OSError:
            pass

    def delete_record(self, rec):
        if rec and rec.get("prekey") and rec.get("key"):
            self._delete(self._entry_dir(rec["prekey"]) / (rec["key"] + ".json"))

    # -- store ----------------------------------------------------------------------------------

    def skip_store(self, reason):
        with self.lock:
            self.store_skipped[reason] = self.store_skipped.get(reason, 0) + 1

    def store(self, test_id, prekey, pre, deps_before, deps_after, results, dep_source, exact_paths=None):
        """Store a PASS record (S3) if the dependency digests did not change during the run (S2)."""
        if not self.write:
            return False
        if deps_before != deps_after:
            self.skip_store("inputs changed during the run")
            return False
        for r in results.values():
            if r.get("state") != "PASS":
                self.skip_store("not PASS")
                return False
        key = self.full_key(prekey, deps_after)
        rec = {
            "schema": SCHEMA,
            "key": key,
            "prekey": prekey,
            "pre": pre,
            "test": test_id,
            "deps": deps_after,
            "dep_source": dep_source,
            "results": results,
            "producer": self.producer.as_dict(),
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        rec["record_sha256"] = self._record_sha(rec)
        ok = atomic_write_json(self._entry_dir(prekey) / (key + ".json"), rec)
        if ok:
            with self.lock:
                self.stored += 1
            if dep_source == "exact" and exact_paths is not None:
                hid = sha256_bytes(test_id.encode("utf-8"))
                atomic_write_json(self.dir / "deps-index" / hid[:2] / (hid + ".json"),
                                  {"id": test_id, "deps": sorted(set(exact_paths)),
                                   "compiler": self.compiler_sha, "created": rec["created"]})
        return ok

    # -- LRU pruning (S7) -----------------------------------------------------------------------

    def prune(self):
        base = self.dir / "entries"
        if not base.is_dir():
            return 0
        files = []
        total = 0
        for dirpath, _dirs, names in os.walk(str(base)):
            for n in names:
                p = os.path.join(dirpath, n)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                if n.startswith(".tmp-") and time.time() - st.st_mtime > 3600:
                    self._delete(p)
                    continue
                files.append((st.st_mtime, st.st_size, p))
                total += st.st_size
        if total <= self.max_bytes:
            return 0
        files.sort()
        removed = 0
        target = int(self.max_bytes * 0.8)
        for _mt, size, p in files:
            if total <= target:
                break
            self._delete(p)
            total -= size
            removed += 1
        return removed


def load_exact_deps_index(cache_dir):
    """{test id: [dep paths]} from deps-index/ (newest exact dependency list per id)."""
    out = {}
    base = Path(cache_dir) / "deps-index"
    if not base.is_dir():
        return out
    for dirpath, _dirs, names in os.walk(str(base)):
        for n in names:
            if not n.endswith(".json") or n.startswith("."):
                continue
            doc = read_json(os.path.join(dirpath, n))
            if isinstance(doc, dict) and isinstance(doc.get("id"), str) and isinstance(doc.get("deps"), list):
                out[doc["id"]] = [str(x) for x in doc["deps"]]
    return out


# ----------------------------------------------------------------------------------------------
# S4 helpers (superset mode): a conservative nondeterminism filter over the test's own sources plus the
# std modules they reference (transitively, textually)
# ----------------------------------------------------------------------------------------------

class StdIndex:
    def __init__(self, std_root):
        self.std_root = Path(std_root) if std_root else None
        self._refs = {}
        self._lock = threading.Lock()

    def module_files(self, modpath):
        """Files that may hold std module `std.a.b` or one of its prefixes (items: `std.a.b.Item`)."""
        if self.std_root is None:
            return []
        parts = modpath.split(".")[1:]
        out = []
        while parts:
            base = self.std_root.joinpath(*parts)
            for cand in (base.with_suffix(".ax"), base / "mod.ax"):
                if cand.is_file():
                    out.append(cand)
            if base.is_dir():
                out.append(base)          # a directory module: all its files
            if out:
                return out
            parts = parts[:-1]
        return out

    def refs_of(self, path):
        p = str(path)
        with self._lock:
            if p in self._refs:
                return self._refs[p]
        found = set()
        files = [Path(p)] if os.path.isfile(p) else (sorted(Path(p).rglob("*.ax")) if os.path.isdir(p) else [])
        for f in files:
            try:
                text = f.read_bytes().decode("utf-8", "replace")
            except OSError:
                continue
            found.update(STD_REF_RE.findall(text))
        res = sorted(found)
        with self._lock:
            self._refs[p] = res
        return res

    def binding_names(self):
        """Every nondeterministic leaf binding declared anywhere under the std root (deny by default: a leaf
        binding not in DETERMINISTIC_BINDINGS), as written (`Sleep`, `monotonic_ns`, `__ax_host_thread_spawn`)."""
        with self._lock:
            cached = getattr(self, "_bindings", None)
        if cached is not None:
            return cached
        names = set()
        if self.std_root is not None and self.std_root.is_dir():
            for f in sorted(self.std_root.rglob("*.ax")):
                try:
                    text = f.read_bytes().decode("utf-8", "replace")
                except OSError:
                    continue
                for n in leaf_bindings(text):
                    if not binding_is_deterministic(n):
                        names.add(n)
        res = frozenset(names)
        with self._lock:
            self._bindings = res
        return res

    def _name_rx(self):
        names = self.binding_names()
        if not names:
            return None
        rx = getattr(self, "_name_rx_c", None)
        if rx is None:
            rx = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(re.escape(n) for n in sorted(names, key=len,
                                                                                            reverse=True))
                            + r")(?![A-Za-z0-9_])")
            self._name_rx_c = rx
        return rx

    def text_uses_binding(self, text):
        """The nondeterministic leaf binding a source text *uses* -- mentions other than in its own `fn NAME`
        declaration (call, `use`/`pub use` re-export, alias, function value) -- or a mention of a host provider
        `__ax_host_<name>` of a nondeterministic intrinsic; None otherwise."""
        code = strip_comments(text)
        rx = self._name_rx()
        if rx is not None:
            for m in rx.finditer(code):
                before = code[max(0, m.start() - 40):m.start()]
                if re.search(r"\bfn\s+$", before):
                    continue                       # its own declaration
                return m.group(1)
        for m in HOST_NAME_RE.finditer(code):
            if not binding_is_deterministic(m.group(1)):
                before = code[max(0, m.start() - 40):m.start()]
                if not re.search(r"\bfn\s+$", before):
                    return HOST_PROVIDER_PREFIX + m.group(1)
        return None

    def file_calls_binding(self, path):
        """The nondeterministic leaf binding a std file (or directory module) uses, or None (memoised)."""
        p = str(path)
        with self._lock:
            memo = self.__dict__.setdefault("_calls", {})
            if p in memo:
                return memo[p]
        found = None
        files = [Path(p)] if os.path.isfile(p) else (sorted(Path(p).rglob("*.ax")) if os.path.isdir(p) else [])
        for f in files:
            try:
                found = self.text_uses_binding(f.read_bytes().decode("utf-8", "replace"))
            except OSError:
                continue
            if found:
                break
        with self._lock:
            memo[p] = found
        return found

    def source_binding(self, text):
        """A nondeterministic leaf binding the test source declares (FFI / `@intrinsic` / host provider not on
        the deterministic list), uses (one declared in std) or imports."""
        for n, kind in sorted(leaf_bindings(text).items()):
            if not binding_is_deterministic(n):
                return "declares %s binding `%s` (not classified deterministic)" % (kind, n)
        u = self.text_uses_binding(text)
        if u:
            return "uses host binding `%s`" % u
        for n in USE_LAST_RE.findall(strip_comments(text)):
            if nondet_name(n):
                return "imports `%s`" % n
        return None

    def nondet_reason(self, source_texts):
        """A reason string when the sources (or the std modules they reach) involve threads, sync, async,
        time, or an OS timer/clock/environment/randomness/process-id binding; None otherwise."""
        seen_files = set()
        todo = []
        for text in source_texts:
            m = NONDET_SOURCE_RE.search(text)
            if m:
                return "source mentions `%s`" % m.group(0)
            b = self.source_binding(text)
            if b:
                return b
            todo.extend(STD_REF_RE.findall(text))
        seen_mods = set()
        while todo:
            mod = todo.pop()
            if mod in seen_mods:
                continue
            seen_mods.add(mod)
            parts = mod.split(".")
            if len(parts) > 1 and parts[1] in NONDET_STD_DIRS:
                return "reaches std.%s" % parts[1]
            for f in self.module_files(mod):
                key = str(f)
                if key in seen_files:
                    continue
                seen_files.add(key)
                if self.std_root is not None:
                    try:
                        relparts = Path(f).resolve().relative_to(self.std_root.resolve()).parts
                    except ValueError:
                        relparts = ()
                    if relparts and relparts[0] in NONDET_STD_DIRS:
                        return "reaches std/%s" % relparts[0]
                b = self.file_calls_binding(f)
                if b:
                    return "reaches %s, which calls host binding `%s`" % (Path(f).name, b)
                todo.extend(self.refs_of(f))
        return None


def exact_deps_nondet(dep_rels, std_rel, std_index=None, root=None):
    """S4 for an exact dependency list: a dependency under std/{thread,sync,async,time}, or (with std_index and
    root) a loaded std file that uses a nondeterministic leaf binding (OS thread/timer/env/... bindings)."""
    prefix = (std_rel.rstrip("/") + "/") if std_rel else "std/"
    for r in dep_rels:
        if r.startswith(prefix):
            first = r[len(prefix):].split("/", 1)[0]
            if first in NONDET_STD_DIRS:
                return "depends on %s%s" % (prefix, first)
            if std_index is not None and root is not None and r.endswith(".ax"):
                b = std_index.file_calls_binding(Path(root) / r)
                if b:
                    return "depends on %s, which uses host binding `%s`" % (r, b)
    return None


if __name__ == "__main__":
    print("axtest_cache is a library of tools/axtest.py", file=sys.stderr)
    sys.exit(2)
