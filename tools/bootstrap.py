#!/usr/bin/env python3
"""Bootstrap driver for the self-hosted Axiom compiler (T086 / T087; SPEC-00 §6, SPEC-20 §4/§6).

Python 3 standard library only. Assembles the multi-module `axiomc` bundle using the canonical
module order from `tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py` (`axiomc_bundle_text()`)
and drives:
  - Stage 1: `axiom0` -> `axiomc1.exe`
  - Stage 2: `axiomc1` -> `axiomc2.exe` (in directory A: `<build_dir>/dir_stage2_<opt>`)
  - Stage 3: `axiomc2` -> `axiomc3.exe` (in directory B: `<build_dir>/dir_stage3_<opt>`,
             verifying byte-identical SHA-256 fixed point in two distinct directories)

Supports checking the fixed point at `-O1`, `-O0`, or both (`--check-both-opt` / `--stage2-opt both`).
All builds pass `--stack-reserve 67108864` (64 MB per ADR-0003) and `--std-root <std>`, and run
with `SOURCE_DATE_EPOCH=0` and host C/binutils toolchains (`gcc`, `clang`, `ld`, `as`, `link`, `cl`, `lld`)
removed from `PATH` (INV-BOOT-003, ABOOT-74/75).
"""

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STACK_RESERVE = 67108864  # 64 MB per ADR-0003

# Budget limits per SPEC-20 §6.2 / ADR-0005 §7:
STAGE1_MAX_WALL_S = 120.0       # < 2 minutes
STAGE1_MAX_PEAK_MB = 2048.0     # < 2.0 GB
STAGE2_MAX_WALL_S = 600.0       # < 10 minutes
STAGE2_MAX_PEAK_MB = 4096.0     # < 4.0 GB
STAGE3_MAX_WALL_S = 600.0       # < 10 minutes
STAGE3_MAX_PEAK_MB = 4096.0     # < 4.0 GB


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def query_peak_memory_bytes(handle_int):
    """Return (peak_working_set_bytes, peak_commit_bytes) for a Win32 process handle."""
    if os.name != "nt" or not handle_int:
        return (0, 0)
    pmc = PROCESS_MEMORY_COUNTERS()
    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    ok = 0
    try:
        fn = getattr(ctypes.windll.kernel32, "K32GetProcessMemoryInfo", None)
        if fn is None:
            fn = ctypes.windll.psapi.GetProcessMemoryInfo
        fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
        fn.restype = wintypes.BOOL
        ok = fn(wintypes.HANDLE(handle_int), ctypes.byref(pmc), pmc.cb)
    except Exception:
        ok = 0
    if not ok:
        return (0, 0)
    return (int(pmc.PeakWorkingSetSize), int(pmc.PeakPagefileUsage))


def load_bundle_text(root):
    obj_link_dir = os.path.join(root, "tests", "selfhost", "obj_link_driver")
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    for p in (obj_link_dir, selfhost_dir):
        if p not in sys.path:
            sys.path.insert(0, p)
    import gen_obj_link_driver_tests as gen
    return gen.axiomc_bundle_text()


def clean_bootstrap_env():
    """Return a clean environment with SOURCE_DATE_EPOCH=0 and no gcc/ld/as/clang/link on PATH."""
    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = "0"
    for k in ("AXIOM_STD",):
        env.pop(k, None)
    raw_path = env.get("PATH", "")
    kept = []
    forbidden_tools = (
        "gcc.exe",
        "ld.exe",
        "as.exe",
        "clang.exe",
        "link.exe",
        "cl.exe",
        "lld.exe",
        "lld-link.exe",
        "gcc",
        "ld",
        "as",
        "clang",
    )
    for entry in raw_path.split(os.pathsep):
        e = entry.strip().strip('"')
        if not e:
            continue
        has_toolchain = False
        for tool in forbidden_tools:
            if os.path.isfile(os.path.join(e, tool)):
                has_toolchain = True
                break
        if not has_toolchain:
            kept.append(entry)
    env["PATH"] = os.pathsep.join(kept)
    return env


def verify_no_external_tools_on_path(env):
    """Verify that gcc, ld, as, clang, link are absent from env['PATH'] (INV-BOOT-003)."""
    raw_path = env.get("PATH", "")
    forbidden = ("gcc.exe", "ld.exe", "as.exe", "clang.exe", "link.exe")
    for entry in raw_path.split(os.pathsep):
        e = entry.strip().strip('"')
        if not e:
            continue
        for tool in forbidden:
            full = os.path.join(e, tool)
            if os.path.isfile(full):
                return False, full
    return True, None


def parse_time_passes(stdout_text):
    """Extract ordered (pass_name, seconds) pairs from `--time-passes` output."""
    passes = []
    for line in stdout_text.splitlines():
        s = line.strip()
        if s.startswith("time: "):
            parts = s[6:].strip().split()
            if len(parts) >= 2 and parts[1].endswith("s"):
                try:
                    secs = float(parts[1][:-1])
                    passes.append((parts[0], secs))
                except ValueError:
                    pass
    return passes


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def files_byte_identical(path_a, path_b):
    if not os.path.isfile(path_a) or not os.path.isfile(path_b):
        return False
    if os.path.getsize(path_a) != os.path.getsize(path_b):
        return False
    with open(path_a, "rb") as fa, open(path_b, "rb") as fb:
        while True:
            ca = fa.read(65536)
            cb = fb.read(65536)
            if ca != cb:
                return False
            if not ca:
                return True


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------------------------------------------
# Input manifests (T444c, REQ-BLD-028). A stage binary `<bin>` is reused only when `<bin>.inputs.json` records
# exactly the inputs of the build that is about to run; file mtimes are never consulted.
#
# Manifest layout (schema 1, JSON, sorted keys, LF):
#   schema, kind ("axiom0" | "stage1" | "stage2" | "stage3"),
#   producer_sha256   sha256 of the compiler binary that produced <bin> ("" for axiom0),
#   bundle_sha256     sha256 of the bundle text that was compiled ("" for axiom0),
#   flags             {"opt": ..., "stack_reserve": ...} for stages; {"cc": ..., "build_type": ...} for axiom0,
#   sources_sha256    sha256 over the sorted lines "<relative path> <sha256>" of every hashed source file,
#   inputs_hash       sha256 of the canonical JSON of the five fields above (this is the reuse key),
#   files             {relative path: sha256} behind sources_sha256 (kept to explain a rebuild),
#   output_sha256 / output_size   of <bin> itself (a binary replaced behind the manifest is never reused).
# Hashed sources of a stage: compiler/**/*.ax, std/**/*.ax and std/**/*.toml (std is keyed by content under the
# fixed prefix "std/"; the std root's absolute path is deliberately NOT an input because the output does not
# depend on it, INV-DET-004). Stage 0: every file under bootstrap/axiom0 except build outputs (see hash_tree).
# ---------------------------------------------------------------------------------------------------------------

MANIFEST_SCHEMA = 1
MANIFEST_SUFFIX = ".inputs.json"
_SKIP_DIR_NAMES = ("cmakefiles", ".cache", ".git", "__pycache__")
_BUILD_TREE_MARKERS = ("CMakeCache.txt", "build.ninja")
_SKIP_FILE_SUFFIXES = (".exe", ".obj", ".o", ".pyc", ".pdb", ".ilk", ".lib", ".a", ".log")


def manifest_path(binary):
    return binary + MANIFEST_SUFFIX


def hash_tree(base, rel_prefix, suffixes=None):
    """Return {"<rel_prefix>/<path under base>": sha256} for the files under `base` (sorted walk).

    `suffixes` (tuple) keeps only files with one of those extensions; None keeps every file except build outputs
    (CMake build trees, i.e. directories holding CMakeCache.txt or build.ninja, plus CMakeFiles/.cache/.git/
    __pycache__ directories, and *.exe/*.obj/*.o/*.pyc/... files). Source directories named build* are kept.
    """
    out = {}
    if not os.path.isdir(base):
        return out
    for dirpath, dirnames, filenames in os.walk(base):
        if suffixes is None:
            dirnames[:] = sorted(
                d for d in dirnames
                if d.lower() not in _SKIP_DIR_NAMES
                and not any(os.path.isfile(os.path.join(dirpath, d, m)) for m in _BUILD_TREE_MARKERS)
            )
        else:
            dirnames[:] = sorted(dirnames)
        for fn in sorted(filenames):
            if suffixes is not None:
                if not fn.endswith(suffixes):
                    continue
            elif fn.lower().endswith(_SKIP_FILE_SUFFIXES):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, base).replace(os.sep, "/")
            try:
                out[rel_prefix + "/" + rel] = sha256_file(full)
            except OSError:
                pass
    return out


def collect_source_hashes(root, std_root):
    """Hashes of every compiler/std source a stage build can observe (see the manifest layout above)."""
    files = {}
    files.update(hash_tree(os.path.join(root, "compiler"), "compiler", (".ax",)))
    files.update(hash_tree(std_root, "std", (".ax", ".toml")))
    return files


def files_digest(files):
    lines = ["%s %s" % (k, files[k]) for k in sorted(files)]
    return sha256_bytes("\n".join(lines).encode("utf-8"))


def _canonical_json(obj):
    import json
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def make_inputs(kind, files, producer_sha256="", bundle_sha256="", flags=None):
    """Expected-inputs record of a build (the manifest minus the output fields); `inputs_hash` is the reuse key."""
    rec = {
        "schema": MANIFEST_SCHEMA,
        "kind": kind,
        "producer_sha256": producer_sha256,
        "bundle_sha256": bundle_sha256,
        "flags": dict(flags or {}),
        "sources_sha256": files_digest(files),
    }
    rec["inputs_hash"] = sha256_bytes(_canonical_json(rec).encode("utf-8"))
    rec["files"] = dict(files)
    return rec


def _explain_difference(old, new):
    parts = []
    if old.get("producer_sha256") != new.get("producer_sha256"):
        parts.append("producing compiler changed")
    if old.get("bundle_sha256") != new.get("bundle_sha256"):
        parts.append("bundle text changed")
    if old.get("flags") != new.get("flags"):
        parts.append("flags changed (%s -> %s)" % (_canonical_json(old.get("flags")), _canonical_json(new.get("flags"))))
    if old.get("sources_sha256") != new.get("sources_sha256"):
        of, nf = old.get("files") or {}, new.get("files") or {}
        changed = sorted(k for k in set(of) | set(nf) if of.get(k) != nf.get(k))
        shown = ", ".join(changed[:3]) + (" (+%d more)" % (len(changed) - 3) if len(changed) > 3 else "")
        parts.append("sources changed: %s" % (shown or "?"))
    return "; ".join(parts) or "inputs changed"


def reuse_blocker(binary, expected):
    """None when `binary` may be reused for the build described by `expected`; otherwise the reason it may not."""
    import json
    if not os.path.isfile(binary):
        return "no previous binary"
    try:
        if os.path.getsize(binary) == 0:
            return "previous binary is empty"
    except OSError:
        return "previous binary unreadable"
    mp = manifest_path(binary)
    if not os.path.isfile(mp):
        return "no input manifest next to the previous binary"
    try:
        with open(mp, "r", encoding="utf-8") as f:
            old = json.load(f)
    except (OSError, ValueError):
        return "input manifest unreadable"
    if not isinstance(old, dict) or old.get("schema") != MANIFEST_SCHEMA:
        return "input manifest schema changed"
    if old.get("inputs_hash") != expected["inputs_hash"]:
        return _explain_difference(old, expected)
    try:
        if os.path.getsize(binary) != old.get("output_size") or sha256_file(binary) != old.get("output_sha256"):
            return "binary does not match its manifest (replaced or damaged)"
    except OSError:
        return "previous binary unreadable"
    return None


def write_manifest(binary, expected, output_sha256=None):
    """Write `<binary>.inputs.json` (atomic replace, LF) for a binary just produced from `expected`."""
    rec = dict(expected)
    rec["output_sha256"] = output_sha256 or sha256_file(binary)
    rec["output_size"] = os.path.getsize(binary)
    mp = manifest_path(binary)
    tmp = mp + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(_canonical_json(rec) + "\n")
    os.replace(tmp, mp)


def drop_manifest(binary):
    try:
        os.remove(manifest_path(binary))
    except OSError:
        pass


def find_reusable(candidates, expected):
    """First candidate binary whose manifest matches `expected`: (path, None); else (None, reason of the first
    candidate that exists, or "no previous binary")."""
    first_reason = None
    for cand in candidates:
        if not cand:
            continue
        why = reuse_blocker(cand, expected)
        if why is None:
            return cand, None
        if first_reason is None and os.path.isfile(cand):
            first_reason = why
    return None, first_reason or "no previous binary"


def run_stage_build(
    stage_label,
    compiler_path,
    bundle_path,
    output_path,
    std_root,
    stack_reserve,
    opt_level,
    time_passes,
    cwd,
    env,
):
    cmd = [
        compiler_path,
        "build",
        bundle_path,
        "-o",
        output_path,
        "--stack-reserve",
        str(stack_reserve),
        "--std-root",
        std_root,
    ]
    if opt_level == "O1":
        cmd.append("-O1")
    elif opt_level == "O0":
        cmd.append("-O0")
    if time_passes:
        cmd.append("--time-passes")

    if os.path.isfile(output_path):
        try:
            os.remove(output_path)
        except OSError:
            pass

    t0 = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out_bytes, err_bytes = proc.communicate()
    wall_s = time.perf_counter() - t0
    peak_ws, peak_commit = query_peak_memory_bytes(int(proc._handle) if hasattr(proc, "_handle") else 0)
    rc = proc.returncode

    out_text = out_bytes.decode("utf-8", "replace").replace("\r\n", "\n")
    err_text = err_bytes.decode("utf-8", "replace").replace("\r\n", "\n")
    passes = parse_time_passes(out_text) if time_passes else []
    peak_rss_mb = max(peak_ws, peak_commit) / (1024.0 * 1024.0)
    peak_ws_mb = peak_ws / (1024.0 * 1024.0)
    peak_commit_mb = peak_commit / (1024.0 * 1024.0)

    return {
        "stage": stage_label,
        "opt": opt_level,
        "cmd": cmd,
        "cwd": cwd,
        "rc": rc,
        "stdout": out_text,
        "stderr": err_text,
        "wall_s": wall_s,
        "peak_ws_bytes": peak_ws,
        "peak_commit_bytes": peak_commit,
        "peak_ws_mb": peak_ws_mb,
        "peak_commit_mb": peak_commit_mb,
        "peak_mb": peak_rss_mb,
        "passes": passes,
        "output": output_path,
        "size_bytes": os.path.getsize(output_path) if os.path.isfile(output_path) else 0,
        "sha256": sha256_file(output_path) if os.path.isfile(output_path) else "",
    }


def make_cached_result(stage_label, opt_level, binary_path, cwd):
    return {
        "stage": stage_label,
        "opt": opt_level,
        "cmd": ["(cached)", binary_path],
        "cwd": cwd,
        "rc": 0,
        "stdout": "",
        "stderr": "",
        "wall_s": 0.0,
        "peak_ws_bytes": 0,
        "peak_commit_bytes": 0,
        "peak_ws_mb": 0.0,
        "peak_commit_mb": 0.0,
        "peak_mb": 0.0,
        "passes": [],
        "output": binary_path,
        "size_bytes": os.path.getsize(binary_path),
        "sha256": sha256_file(binary_path),
    }


def write_perf_csv(csv_path, stage_results):
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    lines = ["stage,opt,pass,seconds,milliseconds,peak_ws_mb,peak_commit_mb,binary_bytes,sha256"]
    for res in stage_results:
        st = res["stage"]
        opt = res.get("opt", "default")
        ws_mb = "%.2f" % res["peak_ws_mb"]
        cm_mb = "%.2f" % res["peak_commit_mb"]
        sz = str(res["size_bytes"])
        digest = res["sha256"]
        for pname, secs in res["passes"]:
            ms = int(round(secs * 1000.0))
            lines.append(
                "%s,%s,%s,%.6f,%d,%s,%s,%s,%s"
                % (st, opt, pname, secs, ms, ws_mb, cm_mb, sz, digest)
            )
        total_ms = int(round(res["wall_s"] * 1000.0))
        lines.append(
            "%s,%s,wall_total,%.6f,%d,%s,%s,%s,%s"
            % (st, opt, res["wall_s"], total_ms, ws_mb, cm_mb, sz, digest)
        )
    with open(csv_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def find_default_stage0(root):
    candidates = [
        os.path.join(root, "build", "axiom0.exe"),
        os.path.join(root, "build", "axiom0"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return candidates[0]


def safe_copy_binary(src, dst):
    """Copy `src` to `dst` unless they are already the same path or byte-identical on disk."""
    if os.path.abspath(src) == os.path.abspath(dst):
        return
    if files_byte_identical(src, dst):
        return
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    shutil.copy2(src, dst)


# ---------------------------------------------------------------------------------------------------------------
# Seeded fast bootstrap & content-addressed compiler cache (T487, REQ-BLD-028, REQ-TST-072).
# ---------------------------------------------------------------------------------------------------------------

STAGE0_SMOKE_SET = (
    "tests/run/str/hello.ax",
    "tests/run/basic/001-return.ax",
    "tests/run/basic/002-arithmetic.ax",
    "tests/conformance/p5/0114_prog_a_hello.ax",
    "tests/conformance/p7/0017_generic_001_identity.ax",
    "tests/opt/const_fold_run.ax",
)

INLINE_GREETING_SMOKE = (
    "// test: run\n"
    "// stdout: Xin chào thế giới\\n\n"
    "fn main() {\n"
    '    print("Xin chào thế giới\\n");\n'
    "}\n"
)

_REAL_RUN_STAGE_BUILD = run_stage_build


def main_checkout_root(root):
    """Return the main checkout root for a git worktree/snapshot, or `abspath(root)` if not a git checkout."""
    root_abs = os.path.abspath(root)
    if not os.path.exists(os.path.join(root_abs, ".git")):
        return root_abs
    try:
        r = subprocess.run(
            ["git", "-C", root_abs, "rev-parse", "--path-format=absolute", "--git-common-dir"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        if r.returncode == 0:
            common = r.stdout.decode("utf-8", "replace").strip()
            if common and os.path.basename(common) == ".git":
                parent = os.path.dirname(common)
                if os.path.isdir(parent):
                    return os.path.abspath(parent)
    except Exception:
        pass
    return root_abs


def default_compiler_cache_dir(root):
    return os.path.join(main_checkout_root(root), "_workspaces", "artifacts", "compiler-cache")


def seed_cache_inputs(source_files, bundle_sha, flags):
    """T444c input manifest for a cached Stage-2 seed compiler (keyed by sources, bundle, and flags)."""
    return make_inputs("stage2", source_files, "", bundle_sha, flags)


def store_compiler_cache(cache_dir, binary_path, source_files, bundle_sha, flags, output_sha256=None):
    """Store a verified Stage-2 compiler in `cache_dir` keyed by its T444c input manifest."""
    if not cache_dir or not os.path.isfile(binary_path):
        return None
    os.makedirs(cache_dir, exist_ok=True)
    exp = seed_cache_inputs(source_files, bundle_sha, flags)
    opt = (flags or {}).get("opt", "O1")
    cached_bin = os.path.join(cache_dir, "axiomc2_%s_%s.exe" % (opt, exp["inputs_hash"][:16]))
    out_sha = output_sha256 or sha256_file(binary_path)
    if not files_byte_identical(binary_path, cached_bin):
        tmp_bin = cached_bin + ".%d.tmp" % os.getpid()
        shutil.copy2(binary_path, tmp_bin)
        os.replace(tmp_bin, cached_bin)
    write_manifest(cached_bin, exp, out_sha)
    return cached_bin


def collect_head_source_hashes(root, current_source_files):
    """Compute the base commit (HEAD) source hashes from `current_source_files` + git HEAD diffs, or None."""
    root_abs = os.path.abspath(root)
    if not os.path.exists(os.path.join(root_abs, ".git")):
        return None
    try:
        r = subprocess.run(
            ["git", "-C", root_abs, "status", "--porcelain", "-z", "--", "compiler", "std"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        if r.returncode != 0:
            return None
        entries = [e for e in r.stdout.decode("utf-8", "replace").split("\0") if e]
        if not entries:
            return dict(current_source_files)
        head_files = dict(current_source_files)
        i = 0
        while i < len(entries):
            e = entries[i]
            i += 1
            if len(e) < 4:
                continue
            status = e[:2]
            rel = e[3:].replace("\\", "/")
            paths = [rel]
            if "R" in status or "C" in status:
                if i < len(entries):
                    paths.append(entries[i].replace("\\", "/"))
                    i += 1
            for p in paths:
                head_files.pop(p, None)
                if "?" in status:
                    continue
                if p.startswith("compiler/") and not p.endswith(".ax"):
                    continue
                if p.startswith("std/") and not p.endswith((".ax", ".toml")):
                    continue
                show = subprocess.run(
                    ["git", "-C", root_abs, "cat-file", "blob", "HEAD:" + p],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                )
                if show.returncode == 0:
                    head_files[p] = sha256_bytes(show.stdout)
        return head_files
    except Exception:
        return None


def _valid_cached_stage2_manifest(cand, stack_reserve=None):
    """Return the parsed manifest dict when `cand` is a valid Stage-2 binary matching its `.inputs.json`, else None."""
    import json
    if not os.path.isfile(cand):
        return None
    mp = manifest_path(cand)
    if not os.path.isfile(mp):
        return None
    try:
        with open(mp, "r", encoding="utf-8") as f:
            old = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(old, dict) or old.get("schema") != MANIFEST_SCHEMA or old.get("kind") != "stage2":
        return None
    if stack_reserve is not None and (old.get("flags") or {}).get("stack_reserve") != stack_reserve:
        return None
    exp = make_inputs(
        old.get("kind", "stage2"),
        old.get("files") or {},
        old.get("producer_sha256", ""),
        old.get("bundle_sha256", ""),
        old.get("flags") or {},
    )
    if reuse_blocker(cand, exp) is not None:
        return None
    return old


def resolve_seed_compiler(
    seed_arg,
    cache_dir,
    root,
    source_files,
    bundle_sha,
    stack_reserve,
    preferred_opt="O1",
):
    """Resolve the Stage-2 seed compiler binary from explicit `--seed <path>` or `cache_dir`.

    Returns `(seed_path, reason)` on hit, or `(None, miss_reason)` on miss.
    """
    if not seed_arg or seed_arg.lower() == "none":
        return None, "seeded mode not requested"

    if seed_arg != "auto":
        p = os.path.abspath(seed_arg)
        if not os.path.isfile(p):
            return None, "explicit seed not found at %s" % p
        try:
            if os.path.getsize(p) == 0:
                return None, "explicit seed is empty at %s" % p
        except OSError:
            return None, "explicit seed unreadable at %s" % p
        mp = manifest_path(p)
        if os.path.isfile(mp):
            import json
            try:
                with open(mp, "r", encoding="utf-8") as f:
                    old = json.load(f)
                if not isinstance(old, dict) or old.get("schema") != MANIFEST_SCHEMA:
                    return None, "explicit seed manifest schema mismatch at %s" % mp
                if os.path.getsize(p) != old.get("output_size") or sha256_file(p) != old.get("output_sha256"):
                    return None, "explicit seed does not match its manifest at %s" % p
            except (OSError, ValueError):
                return None, "explicit seed manifest unreadable at %s" % mp
        return p, "explicit --seed %s" % p

    eff_cache = os.path.abspath(cache_dir) if cache_dir else default_compiler_cache_dir(root)
    if not os.path.isdir(eff_cache):
        return None, "compiler cache directory not found at %s" % eff_cache

    opts_order = []
    for o in ("O1", preferred_opt, "O0"):
        if o in ("O1", "O0") and o not in opts_order:
            opts_order.append(o)

    # 1. Exact current-source input manifest match in cache_dir
    for opt in opts_order:
        exp = seed_cache_inputs(source_files, bundle_sha, {"opt": opt, "stack_reserve": stack_reserve})
        cand = os.path.join(eff_cache, "axiomc2_%s_%s.exe" % (opt, exp["inputs_hash"][:16]))
        if reuse_blocker(cand, exp) is None:
            return cand, "cache hit (exact inputs %s)" % exp["inputs_hash"][:16]

    # Collect all valid manifest-verified stage-2 binaries in eff_cache
    valid_entries = []
    try:
        names = sorted(os.listdir(eff_cache))
    except OSError:
        names = []
    for fn in names:
        if not fn.endswith(".exe"):
            continue
        cand = os.path.join(eff_cache, fn)
        m = _valid_cached_stage2_manifest(cand, stack_reserve=stack_reserve)
        if m is not None:
            try:
                mt = os.path.getmtime(cand)
            except OSError:
                mt = 0.0
            valid_entries.append((cand, m, mt))

    if not valid_entries:
        return None, "no valid cached stage2 compiler in %s" % eff_cache

    # 2. Match against base commit (HEAD) sources_sha256 when inside a git checkout
    head_files = collect_head_source_hashes(root, source_files)
    if head_files is not None:
        head_sources_sha = files_digest(head_files)
        head_matches = [e for e in valid_entries if e[1].get("sources_sha256") == head_sources_sha]
        if head_matches:
            head_matches.sort(
                key=lambda e: ((e[1].get("flags") or {}).get("opt") == "O1", e[2], e[0]),
                reverse=True,
            )
            best_cand, best_m, _mt = head_matches[0]
            return best_cand, "cache hit (HEAD base commit inputs %s)" % best_m["inputs_hash"][:16]

    # 3. Newest manifest-verified stage-2 compiler in cache_dir (preferring O1)
    valid_entries.sort(
        key=lambda e: ((e[1].get("flags") or {}).get("opt") == "O1", e[2], e[0]),
        reverse=True,
    )
    best_cand, best_m, _mt = valid_entries[0]
    return best_cand, "cache hit (cached stage2 inputs %s)" % best_m["inputs_hash"][:16]


def run_smoke_build(compiler_path, src_path, out_exe, std_root, opt_level, cwd, env):
    """Compile one smoke source `src_path` to `out_exe` using `compiler_path`."""
    if os.path.isfile(out_exe):
        try:
            os.remove(out_exe)
        except OSError:
            pass
    if run_stage_build is not _REAL_RUN_STAGE_BUILD:
        # Fake stage driver active in unit tests: check for synthetic stage-0 smoke failure markers
        try:
            with open(compiler_path, "rb") as f:
                comp_bytes = f.read()
        except OSError:
            return 1, "", "cannot read compiler binary"
        if b"STAGE0_SMOKE_FAIL" in comp_bytes:
            return 1, "", "synthetic stage0 smoke compile error"
        with open(src_path, "rb") as f:
            src_bytes = f.read()
        tag = b"DIVERGENT:" if b"STAGE0_SMOKE_DIVERGE" in comp_bytes else b"SMOKE_EXE:"
        os.makedirs(os.path.dirname(os.path.abspath(out_exe)), exist_ok=True)
        with open(out_exe, "wb") as f:
            f.write(tag + hashlib.sha256(src_bytes).hexdigest().encode("utf-8") + b"|" + opt_level.encode("utf-8"))
        return 0, "", ""

    cmd = [compiler_path, "build", src_path, "-o", out_exe, "--std-root", std_root]
    if opt_level == "O1":
        cmd.append("-O1")
    elif opt_level == "O0":
        cmd.append("-O0")
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out_b, err_b = proc.communicate()
    return (
        proc.returncode,
        out_b.decode("utf-8", "replace").replace("\r\n", "\n"),
        err_b.decode("utf-8", "replace").replace("\r\n", "\n"),
    )


def run_stage0_smoke_guard(axiomc1, compiler_b, root, std_root, opt_level, env):
    """Verify that `axiomc1` and `compiler_b` (`B`) compile the fixed smoke set (incl. 'Xin chào thế giới')
    to byte-identical `.exe` binaries (T487 Scope 3, ADR-0043)."""
    eff_opt = "O1" if opt_level in ("O1", "default") else "O0"
    smoke_sources = []
    for rel in STAGE0_SMOKE_SET:
        p = os.path.join(root, *rel.split("/"))
        if os.path.isfile(p):
            smoke_sources.append((rel, p))

    with tempfile.TemporaryDirectory(prefix="axiom_s0_guard_") as td:
        if not smoke_sources:
            inline_p = os.path.join(td, "greeting_smoke.ax")
            with open(inline_p, "wb") as f:
                f.write(INLINE_GREETING_SMOKE.encode("utf-8"))
            smoke_sources.append(("inline:greeting_smoke.ax", inline_p))

        dir_c1 = os.path.join(td, "dir_c1")
        dir_b = os.path.join(td, "dir_b")
        os.makedirs(dir_c1, exist_ok=True)
        os.makedirs(dir_b, exist_ok=True)

        for idx, (label, src_path) in enumerate(smoke_sources):
            exe_c1 = os.path.join(dir_c1, "smoke_%d.exe" % idx)
            exe_b = os.path.join(dir_b, "smoke_%d.exe" % idx)
            rc1, _o1, err1 = run_smoke_build(axiomc1, src_path, exe_c1, std_root, eff_opt, dir_c1, env)
            if rc1 != 0 or not os.path.isfile(exe_c1):
                print(
                    "bootstrap: FAIL stage0-guard: axiomc1 failed to compile smoke program %s (rc=%d)\n%s"
                    % (label, rc1, err1[:1000]),
                    file=sys.stderr,
                )
                return False
            rc2, _o2, err2 = run_smoke_build(compiler_b, src_path, exe_b, std_root, eff_opt, dir_b, env)
            if rc2 != 0 or not os.path.isfile(exe_b):
                print(
                    "bootstrap: FAIL stage0-guard: seeded B failed to compile smoke program %s (rc=%d)\n%s"
                    % (label, rc2, err2[:1000]),
                    file=sys.stderr,
                )
                return False
            if not files_byte_identical(exe_c1, exe_b):
                h1 = sha256_file(exe_c1)
                h2 = sha256_file(exe_b)
                print(
                    "bootstrap: FAIL stage0-guard: smoke .exe mismatch on %s (%s): sha256(axiomc1)=%s != sha256(B)=%s"
                    % (label, eff_opt, h1, h2),
                    file=sys.stderr,
                )
                return False

    print(
        "STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on %d smoke program(s) (%s, incl. Xin chào thế giới)"
        % (len(smoke_sources), eff_opt)
    )
    return True


def _seeded_stage0_guard_verified(base_dir, opt_level, axiomc1_sha256):
    """Return True iff `dir_seed_A_<opt>/axiomc_A.exe.inputs.json` records a passing stage0-smoke guard
    for `axiomc1_sha256` (T487 F2)."""
    import json
    a_out = os.path.join(base_dir, "dir_seed_A_%s" % opt_level, "axiomc_A.exe")
    mp_a = manifest_path(a_out)
    if not os.path.isfile(mp_a):
        return False
    try:
        with open(mp_a, "r", encoding="utf-8") as f:
            old_a = json.load(f)
    except (OSError, ValueError):
        return False
    return isinstance(old_a, dict) and old_a.get("stage0_guard_axiomc1_sha256") == axiomc1_sha256


def _publish_seeded_opt(pub, source_files, bundle_sha, cache_dir, stage0_guard_c1_sha=None):
    """Publish verified seeded outputs (A/B/C manifests, top-level copies, and compiler-cache entry).
    Called ONLY after BOTH `B == C` fixed-point and `run_stage0_smoke_guard` succeed (T487 F2)."""
    exp_a = dict(pub["exp_a"])
    if stage0_guard_c1_sha:
        exp_a["stage0_guard_axiomc1_sha256"] = stage0_guard_c1_sha
    write_manifest(pub["a_out"], exp_a, pub["sha_a"])

    s2_copies = pub["s2_copies"]
    for c in s2_copies[1:]:
        safe_copy_binary(pub["s2_out_in_dir"], c)
    for c in s2_copies:
        write_manifest(c, pub["exp_b"], pub["sha_b"])

    s3_copies = pub["s3_copies"]
    for c in s3_copies[1:]:
        safe_copy_binary(pub["s3_out_in_dir"], c)
    for c in s3_copies:
        write_manifest(c, pub["exp_c"], pub["sha_c"])

    if cache_dir:
        store_compiler_cache(cache_dir, pub["s2_out_in_dir"], source_files, bundle_sha, pub["flags"], pub["sha_b"])


def _drop_seeded_pub_manifests(pending_pubs):
    for pub in pending_pubs:
        for c in [pub["a_out"]] + pub["s2_copies"] + pub["s3_copies"]:
            drop_manifest(c)


def run_seeded_for_opt(
    opt_level,
    seed_compiler,
    bundle_bytes,
    std_root,
    stack_reserve,
    base_dir,
    time_passes,
    env,
    reuse_existing=False,
    source_files=None,
    cache_dir=None,
    publish_queue=None,
):
    """Seeded fast bootstrap for `opt_level` (T487 Scope 2):
      A = seed(new source)   in dir_seed_A_<opt>/axiomc_A.exe
      B = A(new source)      in dir_stage2_<opt>/axiomc2.exe (and dir_seed_B_<opt>/axiomc_B.exe)
      C = B(new source)      in dir_stage3_<opt>/axiomc3.exe
    Requires `B == C` byte-identical in distinct directories; `B` is the compiler under test.
    Copies, manifests, and compiler-cache entries are NOT published until `B == C` succeeds (and when
    `publish_queue` is supplied, deferred until the caller also verifies `run_stage0_smoke_guard`, T487 F2).
    """
    dir_a = os.path.abspath(os.path.join(base_dir, "dir_seed_A_%s" % opt_level))
    dir_sb = os.path.abspath(os.path.join(base_dir, "dir_seed_B_%s" % opt_level))
    dir_s2 = os.path.abspath(os.path.join(base_dir, "dir_stage2_%s" % opt_level))
    dir_s3 = os.path.abspath(os.path.join(base_dir, "dir_stage3_%s" % opt_level))
    if len({dir_a, dir_s2, dir_s3}) != 3:
        raise RuntimeError("seed A, stage2 (B), and stage3 (C) directories must be distinct")
    for d in (dir_a, dir_sb, dir_s2, dir_s3):
        os.makedirs(d, exist_ok=True)

    bundle_a = os.path.join(dir_a, "axiomc_bundle.ax")
    bundle_s2 = os.path.join(dir_s2, "axiomc_bundle.ax")
    bundle_s3 = os.path.join(dir_s3, "axiomc_bundle.ax")
    for bp in (bundle_a, bundle_s2, bundle_s3):
        with open(bp, "wb") as f:
            f.write(bundle_bytes)

    a_out = os.path.join(dir_a, "axiomc_A.exe")
    sb_out = os.path.join(dir_sb, "axiomc_B.exe")
    s2_out_in_dir = os.path.join(dir_s2, "axiomc2.exe")
    s3_out_in_dir = os.path.join(dir_s3, "axiomc3.exe")
    top_s2_opt = os.path.join(base_dir, "axiomc2_%s.exe" % opt_level)
    top_s3_opt = os.path.join(base_dir, "axiomc3_%s.exe" % opt_level)
    top_s2_default = os.path.join(base_dir, "axiomc2.exe")
    top_s3_default = os.path.join(base_dir, "axiomc3.exe")

    source_files = source_files if source_files is not None else {}
    flags = {"opt": opt_level, "stack_reserve": stack_reserve}
    bundle_sha = sha256_bytes(bundle_bytes)
    seed_sha = sha256_file(seed_compiler)

    s2_copies = [s2_out_in_dir, sb_out, top_s2_opt]
    if opt_level == "O1":
        s2_copies += [top_s2_default, os.path.join(base_dir, "axiomc.exe")]
    s3_copies = [s3_out_in_dir, top_s3_opt] + ([top_s3_default] if opt_level == "O1" else [])
    all_manifests = [a_out] + s2_copies + s3_copies

    results = []

    # Step 1: A = seed(new source)
    exp_a = make_inputs("seed_a", source_files, seed_sha, bundle_sha, flags)
    reused_a, why_a = (None, "reuse not requested")
    if reuse_existing:
        reused_a, why_a = find_reusable([a_out], exp_a)
        if reused_a is None:
            seeded_s2, _seeded_exp2 = _find_reusable_seeded_stage2(
                base_dir,
                opt_level,
                [s2_out_in_dir, sb_out, top_s2_opt, top_s2_default if opt_level == "O1" else ""],
                source_files,
                bundle_sha,
                flags,
            )
            if seeded_s2 is not None:
                import json
                with open(manifest_path(a_out), "r", encoding="utf-8") as f:
                    old_a = json.load(f)
                exp_a = make_inputs("seed_a", source_files, old_a.get("producer_sha256", ""), bundle_sha, flags)
                reused_a = a_out
    if reused_a is not None:
        r_a = make_cached_result("seedA_seed_to_A_%s" % opt_level, opt_level, a_out, dir_a)
        print("REUSED %s (inputs %s)" % (a_out, exp_a["inputs_hash"][:16]))
    else:
        drop_manifest(a_out)
        r_a = run_stage_build(
            "seedA_seed_to_A_%s" % opt_level,
            seed_compiler,
            bundle_a,
            a_out,
            std_root,
            stack_reserve,
            opt_level,
            time_passes,
            dir_a,
            env,
        )
        if r_a["rc"] == 0 and os.path.isfile(a_out):
            print("REBUILT %s (%s)" % (a_out, why_a))
    results.append(r_a)
    if r_a["rc"] != 0 or not os.path.isfile(a_out):
        for c in all_manifests:
            drop_manifest(c)
        print(
            "bootstrap: FAIL seeded A (%s, seed -> A) rc=%d\n%s"
            % (opt_level, r_a["rc"], r_a["stderr"][:2000]),
            file=sys.stderr,
        )
        return False, results
    print(
        "SEED-A (%s) OK: %s [dir=%s] (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
        % (opt_level, a_out, dir_a, r_a["size_bytes"], r_a["sha256"][:16], r_a["wall_s"], r_a["peak_ws_mb"], r_a["peak_commit_mb"])
    )

    # Step 2: B = A(new source)
    exp_b = make_inputs("stage2", source_files, r_a["sha256"], bundle_sha, flags)
    reused_b, why_b = (None, "reuse not requested")
    if reuse_existing:
        reused_b, why_b = find_reusable(
            [s2_out_in_dir, sb_out, top_s2_opt, top_s2_default if opt_level == "O1" else ""],
            exp_b,
        )
    if reused_b is not None:
        safe_copy_binary(reused_b, s2_out_in_dir)
        r_b = make_cached_result("stage2_seedA_to_B_%s" % opt_level, opt_level, s2_out_in_dir, dir_s2)
        print("REUSED %s (inputs %s)" % (s2_out_in_dir, exp_b["inputs_hash"][:16]))
    else:
        for c in s2_copies:
            drop_manifest(c)
        r_b = run_stage_build(
            "stage2_seedA_to_B_%s" % opt_level,
            a_out,
            bundle_s2,
            s2_out_in_dir,
            std_root,
            stack_reserve,
            opt_level,
            time_passes,
            dir_s2,
            env,
        )
        if r_b["rc"] == 0 and os.path.isfile(s2_out_in_dir):
            print("REBUILT %s (%s)" % (s2_out_in_dir, why_b))
    results.append(r_b)
    if r_b["rc"] != 0 or not os.path.isfile(s2_out_in_dir):
        for c in all_manifests:
            drop_manifest(c)
        print(
            "bootstrap: FAIL seeded B (%s, A -> B) rc=%d\n%s"
            % (opt_level, r_b["rc"], r_b["stderr"][:2000]),
            file=sys.stderr,
        )
        return False, results

    print(
        "STAGE2 (%s) OK: %s [dir=%s] (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
        % (
            opt_level,
            s2_out_in_dir,
            dir_s2,
            r_b["size_bytes"],
            r_b["sha256"][:16],
            r_b["wall_s"],
            r_b["peak_ws_mb"],
            r_b["peak_commit_mb"],
        )
    )

    # Step 3: C = B(new source)
    exp_c = make_inputs("stage3", source_files, r_b["sha256"], bundle_sha, flags)
    reused_c, why_c = (None, "reuse not requested")
    if reuse_existing:
        reused_c, why_c = find_reusable(
            [s3_out_in_dir, top_s3_opt, top_s3_default if opt_level == "O1" else ""],
            exp_c,
        )
    if reused_c is not None:
        safe_copy_binary(reused_c, s3_out_in_dir)
        r_c = make_cached_result("stage3_seedB_to_C_%s" % opt_level, opt_level, s3_out_in_dir, dir_s3)
        print("REUSED %s (inputs %s)" % (s3_out_in_dir, exp_c["inputs_hash"][:16]))
    else:
        for c in s3_copies:
            drop_manifest(c)
        r_c = run_stage_build(
            "stage3_seedB_to_C_%s" % opt_level,
            s2_out_in_dir,
            bundle_s3,
            s3_out_in_dir,
            std_root,
            stack_reserve,
            opt_level,
            time_passes,
            dir_s3,
            env,
        )
        if r_c["rc"] == 0 and os.path.isfile(s3_out_in_dir):
            print("REBUILT %s (%s)" % (s3_out_in_dir, why_c))
    results.append(r_c)
    if r_c["rc"] != 0 or not os.path.isfile(s3_out_in_dir):
        for c in all_manifests:
            drop_manifest(c)
        print(
            "bootstrap: FAIL seeded C (%s, B -> C) rc=%d\n%s"
            % (opt_level, r_c["rc"], r_c["stderr"][:2000]),
            file=sys.stderr,
        )
        return False, results

    print(
        "STAGE3 (%s) OK: %s [dir=%s] (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
        % (
            opt_level,
            s3_out_in_dir,
            dir_s3,
            r_c["size_bytes"],
            r_c["sha256"][:16],
            r_c["wall_s"],
            r_c["peak_ws_mb"],
            r_c["peak_commit_mb"],
        )
    )

    if r_b["sha256"] != r_c["sha256"] or not files_byte_identical(s2_out_in_dir, s3_out_in_dir):
        for c in all_manifests:
            drop_manifest(c)
        print(
            "bootstrap: FAIL seeded fixed-point mismatch (%s): sha256(B)=%s != sha256(C)=%s"
            % (opt_level, r_b["sha256"], r_c["sha256"]),
            file=sys.stderr,
        )
        return False, results

    print(
        "FIXED-POINT (%s) OK: sha256(axiomc2_%s) == sha256(axiomc3_%s) == %s (%d bytes, built in %s and %s) [seeded B==C]"
        % (opt_level, opt_level, opt_level, r_c["sha256"], r_c["size_bytes"], dir_s2, dir_s3)
    )

    pub = {
        "opt_level": opt_level,
        "a_out": a_out,
        "exp_a": exp_a,
        "sha_a": r_a["sha256"],
        "s2_out_in_dir": s2_out_in_dir,
        "s2_copies": s2_copies,
        "exp_b": exp_b,
        "sha_b": r_b["sha256"],
        "s3_out_in_dir": s3_out_in_dir,
        "s3_copies": s3_copies,
        "exp_c": exp_c,
        "sha_c": r_c["sha256"],
        "flags": flags,
    }
    if publish_queue is not None:
        publish_queue.append(pub)
    else:
        _publish_seeded_opt(pub, source_files, bundle_sha, cache_dir)

    return True, results


def _find_reusable_seeded_stage2(base_dir, opt_level, candidates, source_files, bundle_sha, flags):
    """When `reuse_existing` is active and `dir_seed_A_<opt>/axiomc_A.exe` in `base_dir` was built for the exact
    same `(source_files, bundle_sha, flags)`, accept a Stage-2 binary produced by that `A` only when a matching
    Stage-3 binary (`B == C` fixed point) is also verified on disk (T487 F2)."""
    import json
    a_out = os.path.join(base_dir, "dir_seed_A_%s" % opt_level, "axiomc_A.exe")
    mp_a = manifest_path(a_out)
    if not os.path.isfile(a_out) or not os.path.isfile(mp_a):
        return None, None
    try:
        with open(mp_a, "r", encoding="utf-8") as f:
            old_a = json.load(f)
    except (OSError, ValueError):
        return None, None
    if not isinstance(old_a, dict) or old_a.get("schema") != MANIFEST_SCHEMA:
        return None, None
    exp_a = make_inputs("seed_a", source_files, old_a.get("producer_sha256", ""), bundle_sha, flags)
    if reuse_blocker(a_out, exp_a) is not None:
        return None, None
    exp_b = make_inputs("stage2", source_files, sha256_file(a_out), bundle_sha, flags)
    reused, _why = find_reusable(candidates, exp_b)
    if reused is None:
        return None, None
    s2_sha = sha256_file(reused)
    s3_cands = [
        os.path.join(base_dir, "dir_stage3_%s" % opt_level, "axiomc3.exe"),
        os.path.join(base_dir, "axiomc3_%s.exe" % opt_level),
        os.path.join(base_dir, "axiomc3.exe") if opt_level == "O1" else "",
    ]
    exp_c = make_inputs("stage3", source_files, s2_sha, bundle_sha, flags)
    reused_s3, _why_s3 = find_reusable(s3_cands, exp_c)
    if reused_s3 is None or sha256_file(reused_s3) != s2_sha or not files_byte_identical(reused, reused_s3):
        return None, None
    return reused, exp_b


def run_stage2_and_stage3_for_opt(
    opt_level,
    axiomc1,
    bundle_bytes,
    std_root,
    stack_reserve,
    base_dir,
    max_stage,
    time_passes,
    env,
    reuse_existing=False,
    source_files=None,
    allow_seeded_reuse=True,
    cache_dir=None,
):
    """Run Stage-2 in dir_stage2_<opt> and (if max_stage >= 3) Stage-3 in dir_stage3_<opt>.

    With `reuse_existing`, a previous binary is reused only when its `<bin>.inputs.json` manifest matches the
    inputs of this build exactly (see "Input manifests" above); `source_files` is `collect_source_hashes(...)`.

    Stage-2 and Stage-3 always execute in two distinct directories (`dir_stage2 != dir_stage3`)
    with identical flags (INV-DET-004, SPEC-00 MS-P10b, SPEC-20 §6.3).
    """
    dir_s2 = os.path.abspath(os.path.join(base_dir, "dir_stage2_%s" % opt_level))
    dir_s3 = os.path.abspath(os.path.join(base_dir, "dir_stage3_%s" % opt_level))
    if dir_s2 == dir_s3:
        raise RuntimeError("stage2 and stage3 directories must be distinct")
    os.makedirs(dir_s2, exist_ok=True)
    os.makedirs(dir_s3, exist_ok=True)

    bundle_s2 = os.path.join(dir_s2, "axiomc_bundle.ax")
    bundle_s3 = os.path.join(dir_s3, "axiomc_bundle.ax")
    with open(bundle_s2, "wb") as f:
        f.write(bundle_bytes)
    with open(bundle_s3, "wb") as f:
        f.write(bundle_bytes)

    s2_out_in_dir = os.path.join(dir_s2, "axiomc2.exe")
    s3_out_in_dir = os.path.join(dir_s3, "axiomc3.exe")
    top_s2_opt = os.path.join(base_dir, "axiomc2_%s.exe" % opt_level)
    top_s3_opt = os.path.join(base_dir, "axiomc3_%s.exe" % opt_level)
    top_s2_default = os.path.join(base_dir, "axiomc2.exe")
    top_s3_default = os.path.join(base_dir, "axiomc3.exe")

    results = []

    source_files = source_files if source_files is not None else {}
    flags = {"opt": opt_level, "stack_reserve": stack_reserve}
    bundle_sha = sha256_bytes(bundle_bytes)
    s2_copies = [s2_out_in_dir, top_s2_opt]
    if opt_level == "O1":
        s2_copies += [top_s2_default, os.path.join(base_dir, "axiomc.exe")]

    # Stage 2 reuse: exact input-manifest match (producer axiomc1, or valid seeded A when allow_seeded_reuse=True).
    s2_cands = [s2_out_in_dir, top_s2_opt, top_s2_default if opt_level == "O1" else ""]
    exp2 = make_inputs("stage2", source_files, sha256_file(axiomc1), bundle_sha, flags)
    reused_s2 = None
    why2 = "reuse not requested"
    if reuse_existing:
        reused_s2, why2 = find_reusable(s2_cands, exp2)
        if reused_s2 is None and allow_seeded_reuse:
            seeded_s2, seeded_exp2 = _find_reusable_seeded_stage2(
                base_dir, opt_level, s2_cands, source_files, bundle_sha, flags
            )
            if seeded_s2 is not None:
                reused_s2 = seeded_s2
                exp2 = seeded_exp2

    if reused_s2 is not None:
        safe_copy_binary(reused_s2, s2_out_in_dir)
        r2 = make_cached_result("stage2_axiomc1_to_axiomc2_%s" % opt_level, opt_level, s2_out_in_dir, dir_s2)
        print("REUSED %s (inputs %s)" % (s2_out_in_dir, exp2["inputs_hash"][:16]))
    else:
        for c in s2_copies:
            drop_manifest(c)
        r2 = run_stage_build(
            "stage2_axiomc1_to_axiomc2_%s" % opt_level,
            axiomc1,
            bundle_s2,
            s2_out_in_dir,
            std_root,
            stack_reserve,
            opt_level,
            time_passes,
            dir_s2,
            env,
        )
        if r2["rc"] == 0 and os.path.isfile(s2_out_in_dir):
            print("REBUILT %s (%s)" % (s2_out_in_dir, why2))
    results.append(r2)
    if r2["rc"] != 0 or not os.path.isfile(s2_out_in_dir):
        print(
            "bootstrap: FAIL stage2 (%s, axiomc1 -> axiomc2) rc=%d\n%s"
            % (opt_level, r2["rc"], r2["stderr"][:2000]),
            file=sys.stderr,
        )
        return False, results

    if max_stage < 3:
        for c in s2_copies[1:]:
            safe_copy_binary(s2_out_in_dir, c)
        for c in s2_copies:
            write_manifest(c, exp2, r2["sha256"])

        if cache_dir:
            store_compiler_cache(cache_dir, s2_out_in_dir, source_files, bundle_sha, flags, r2["sha256"])

    print(
        "STAGE2 (%s) OK: %s [dir=%s] (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
        % (
            opt_level,
            s2_out_in_dir,
            dir_s2,
            r2["size_bytes"],
            r2["sha256"][:16],
            r2["wall_s"],
            r2["peak_ws_mb"],
            r2["peak_commit_mb"],
        )
    )

    if max_stage >= 3:
        s3_copies = [s3_out_in_dir, top_s3_opt] + ([top_s3_default] if opt_level == "O1" else [])
        exp3 = make_inputs("stage3", source_files, r2["sha256"], bundle_sha, flags)
        reused_s3 = None
        why3 = "reuse not requested"
        if reuse_existing:
            reused_s3, why3 = find_reusable([s3_out_in_dir, top_s3_opt, top_s3_default if opt_level == "O1" else ""], exp3)

        if reused_s3 is not None:
            safe_copy_binary(reused_s3, s3_out_in_dir)
            r3 = make_cached_result("stage3_axiomc2_to_axiomc3_%s" % opt_level, opt_level, s3_out_in_dir, dir_s3)
            print("REUSED %s (inputs %s)" % (s3_out_in_dir, exp3["inputs_hash"][:16]))
        else:
            for c in s3_copies:
                drop_manifest(c)
            r3 = run_stage_build(
                "stage3_axiomc2_to_axiomc3_%s" % opt_level,
                s2_out_in_dir,
                bundle_s3,
                s3_out_in_dir,
                std_root,
                stack_reserve,
                opt_level,
                time_passes,
                dir_s3,
                env,
            )
            if r3["rc"] == 0 and os.path.isfile(s3_out_in_dir):
                print("REBUILT %s (%s)" % (s3_out_in_dir, why3))
        results.append(r3)
        if r3["rc"] != 0 or not os.path.isfile(s3_out_in_dir):
            for c in s2_copies + s3_copies:
                drop_manifest(c)
            print(
                "bootstrap: FAIL stage3 (%s, axiomc2 -> axiomc3) rc=%d\n%s"
                % (opt_level, r3["rc"], r3["stderr"][:2000]),
                file=sys.stderr,
            )
            return False, results

        print(
            "STAGE3 (%s) OK: %s [dir=%s] (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
            % (
                opt_level,
                s3_out_in_dir,
                dir_s3,
                r3["size_bytes"],
                r3["sha256"][:16],
                r3["wall_s"],
                r3["peak_ws_mb"],
                r3["peak_commit_mb"],
            )
        )
        if r2["sha256"] != r3["sha256"] or not files_byte_identical(s2_out_in_dir, s3_out_in_dir):
            for c in s2_copies + s3_copies:
                drop_manifest(c)
            print(
                "bootstrap: FAIL fixed-point mismatch (%s): sha256(axiomc2)=%s != sha256(axiomc3)=%s"
                % (opt_level, r2["sha256"], r3["sha256"]),
                file=sys.stderr,
            )
            return False, results

        for c in s2_copies[1:]:
            safe_copy_binary(s2_out_in_dir, c)
        for c in s2_copies:
            write_manifest(c, exp2, r2["sha256"])
        for c in s3_copies[1:]:
            safe_copy_binary(s3_out_in_dir, c)
        for c in s3_copies:
            write_manifest(c, exp3, r3["sha256"])
        if cache_dir:
            store_compiler_cache(cache_dir, s2_out_in_dir, source_files, bundle_sha, flags, r2["sha256"])

        print(
            "FIXED-POINT (%s) OK: sha256(axiomc2_%s) == sha256(axiomc3_%s) == %s (%d bytes, built in %s and %s)"
            % (opt_level, opt_level, opt_level, r3["sha256"], r3["size_bytes"], dir_s2, dir_s3)
        )

    return True, results


def verify_trust_root_c2_equals_seeded_b(
    opt_level,
    seed_compiler,
    bundle_bytes,
    std_root,
    stack_reserve,
    base_dir,
    time_passes,
    env,
    reuse_existing=False,
    source_files=None,
):
    """Build or reuse `A = seed(new source)` and `B = A(new source)` in `dir_seed_A_<opt>` / `dir_seed_B_<opt>`
    and verify `c2 == B` byte-identical against `dir_stage2_<opt>/axiomc2.exe` (T487 Scope 4)."""
    c2_bin = os.path.join(base_dir, "dir_stage2_%s" % opt_level, "axiomc2.exe")
    if not os.path.isfile(c2_bin):
        print("bootstrap: FAIL trust-root: missing full-chain stage2 binary at %s" % c2_bin, file=sys.stderr)
        return False, []

    dir_a = os.path.abspath(os.path.join(base_dir, "dir_seed_A_%s" % opt_level))
    dir_sb = os.path.abspath(os.path.join(base_dir, "dir_seed_B_%s" % opt_level))
    os.makedirs(dir_a, exist_ok=True)
    os.makedirs(dir_sb, exist_ok=True)
    bundle_a = os.path.join(dir_a, "axiomc_bundle.ax")
    bundle_sb = os.path.join(dir_sb, "axiomc_bundle.ax")
    with open(bundle_a, "wb") as f:
        f.write(bundle_bytes)
    with open(bundle_sb, "wb") as f:
        f.write(bundle_bytes)

    a_out = os.path.join(dir_a, "axiomc_A.exe")
    sb_out = os.path.join(dir_sb, "axiomc_B.exe")
    source_files = source_files if source_files is not None else {}
    flags = {"opt": opt_level, "stack_reserve": stack_reserve}
    bundle_sha = sha256_bytes(bundle_bytes)
    seed_sha = sha256_file(seed_compiler)
    results = []

    exp_a = make_inputs("seed_a", source_files, seed_sha, bundle_sha, flags)
    reused_a, why_a = (None, "reuse not requested")
    if reuse_existing:
        reused_a, why_a = find_reusable([a_out], exp_a)
    if reused_a is not None:
        r_a = make_cached_result("seedA_seed_to_A_%s" % opt_level, opt_level, a_out, dir_a)
        print("REUSED %s (inputs %s)" % (a_out, exp_a["inputs_hash"][:16]))
    else:
        drop_manifest(a_out)
        r_a = run_stage_build(
            "seedA_seed_to_A_%s" % opt_level,
            seed_compiler,
            bundle_a,
            a_out,
            std_root,
            stack_reserve,
            opt_level,
            time_passes,
            dir_a,
            env,
        )
        if r_a["rc"] == 0 and os.path.isfile(a_out):
            write_manifest(a_out, exp_a, r_a["sha256"])
            print("REBUILT %s (%s)" % (a_out, why_a))
    results.append(r_a)
    if r_a["rc"] != 0 or not os.path.isfile(a_out):
        print("bootstrap: FAIL trust-root A (%s, seed -> A) rc=%d" % (opt_level, r_a["rc"]), file=sys.stderr)
        return False, results

    exp_b = make_inputs("stage2", source_files, r_a["sha256"], bundle_sha, flags)
    reused_b, why_b = (None, "reuse not requested")
    if reuse_existing:
        reused_b, why_b = find_reusable([sb_out], exp_b)
    if reused_b is not None:
        r_b = make_cached_result("seedB_A_to_B_%s" % opt_level, opt_level, sb_out, dir_sb)
        print("REUSED %s (inputs %s)" % (sb_out, exp_b["inputs_hash"][:16]))
    else:
        drop_manifest(sb_out)
        r_b = run_stage_build(
            "seedB_A_to_B_%s" % opt_level,
            a_out,
            bundle_sb,
            sb_out,
            std_root,
            stack_reserve,
            opt_level,
            time_passes,
            dir_sb,
            env,
        )
        if r_b["rc"] == 0 and os.path.isfile(sb_out):
            write_manifest(sb_out, exp_b, r_b["sha256"])
            print("REBUILT %s (%s)" % (sb_out, why_b))
    results.append(r_b)
    if r_b["rc"] != 0 or not os.path.isfile(sb_out):
        print("bootstrap: FAIL trust-root B (%s, A -> B) rc=%d" % (opt_level, r_b["rc"]), file=sys.stderr)
        return False, results

    h_c2 = sha256_file(c2_bin)
    h_b = r_b["sha256"]
    if h_c2 != h_b or not files_byte_identical(c2_bin, sb_out):
        drop_manifest(a_out)
        drop_manifest(sb_out)
        print(
            "bootstrap: FAIL trust-root mismatch (%s): sha256(c2)=%s != sha256(seeded B)=%s"
            % (opt_level, h_c2, h_b),
            file=sys.stderr,
        )
        return False, results

    print("TRUST-ROOT (%s) OK: sha256(c2_%s) == sha256(B_%s) == %s" % (opt_level, opt_level, opt_level, h_c2))
    return True, results


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Bootstrap the self-hosted Axiom compiler (axiomc).")
    ap.add_argument("--root", default=ROOT, help="Repository root directory")
    ap.add_argument("--stage0", default=None, help="Path to Stage-0 compiler (axiom0.exe)")
    ap.add_argument("--build-dir", default=None, help="Output build directory (default: dirname of --stage0)")
    ap.add_argument("--out", default=None, help="Explicit output path for Stage-1 binary (axiomc1.exe)")
    ap.add_argument("--bundle-out", default=None, help="Path to write assembled axiomc_bundle.ax")
    ap.add_argument("--std-root", default=None, help="Path to std library root (default: <root>/std)")
    ap.add_argument("--stack-reserve", type=int, default=DEFAULT_STACK_RESERVE, help="PE stack reserve in bytes")
    ap.add_argument("--stage", type=int, choices=(1, 2, 3), default=None, help="Highest bootstrap stage to build (1, 2, or 3)")
    ap.add_argument("--opt", choices=("default", "O0", "O1"), default="default", help="Optimization flag for Stage-1 build")
    ap.add_argument(
        "--stage2-opt",
        choices=("default", "O0", "O1", "both"),
        default="O1",
        help="Optimization flag for Stage-2/3 self-compile (O0, O1, or both)",
    )
    ap.add_argument(
        "--check-both-opt",
        "--verify-fixed-point",
        dest="check_both_opt",
        action="store_true",
        help="Verify Stage-2 == Stage-3 fixed point in distinct directories at both -O0 and -O1",
    )
    ap.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse an existing stage binary when its <bin>.inputs.json manifest matches this build's inputs exactly "
        "(content hashes of compiler/ and std/ sources, bundle text, producing compiler, flags); never by mtime",
    )
    ap.add_argument(
        "--seed",
        default=None,
        help="Seed Stage-2 compiler path for seeded fast bootstrap (A=seed(src), B=A(src), C=B(src), B==C), "
        "or 'auto' to look up in --cache-dir; missing seed falls back to the full chain automatically (T487)",
    )
    ap.add_argument(
        "--cache-dir",
        default=None,
        help="Content-addressed Stage-2 compiler cache directory (default: <main_checkout>/_workspaces/artifacts/compiler-cache)",
    )
    ap.add_argument(
        "--full-chain",
        action="store_true",
        help="Force the full axiom0 -> c1 -> c2 (-> c3) chain, disabling seeded mode",
    )
    ap.add_argument(
        "--trust-root",
        action="store_true",
        help="Run the full axiom0 -> c1 -> c2 -> c3 trust-root chain and, when a seed is available, verify c2 == B byte-identical",
    )
    ap.add_argument(
        "--no-stage0-smoke",
        action="store_true",
        help="Skip the stage-0 smoke-set .exe byte-parity guard between axiomc1 and seeded B",
    )
    ap.add_argument("--time-passes", action="store_true", help="Pass --time-passes and report per-pass timings")
    ap.add_argument("--perf-csv", default=None, help="Write self-host timing and memory CSV to this path")
    ap.add_argument("--check-budget", action="store_true", help="Enforce SPEC-20 §6.2 wall-time and RAM budgets")
    args = ap.parse_args(argv)

    if args.check_both_opt or args.trust_root:
        max_stage = 3
        if args.check_both_opt or (args.trust_root and args.stage2_opt == "both"):
            opt_levels = ["O1", "O0"]
        elif args.stage2_opt == "default":
            opt_levels = ["O0"]
        else:
            opt_levels = [args.stage2_opt]
    else:
        if args.stage is not None:
            max_stage = args.stage
        elif args.seed is not None:
            max_stage = 3
        elif args.out is not None:
            max_stage = 1
        else:
            max_stage = 3
        if args.stage2_opt == "both":
            opt_levels = ["O1", "O0"]
        elif args.stage2_opt == "default":
            opt_levels = ["O0"]
        else:
            opt_levels = [args.stage2_opt]

    root = os.path.abspath(args.root)
    stage0 = os.path.abspath(args.stage0) if args.stage0 else find_default_stage0(root)
    if not os.path.isfile(stage0):
        print("bootstrap: error: stage0 compiler not found at %s" % stage0, file=sys.stderr)
        return 2

    build_dir = os.path.abspath(args.build_dir) if args.build_dir else (
        os.path.dirname(os.path.abspath(args.out)) if args.out else os.path.dirname(stage0)
    )
    os.makedirs(build_dir, exist_ok=True)

    std_root = os.path.abspath(args.std_root) if args.std_root else os.path.join(root, "std")
    if not os.path.isdir(std_root):
        print("bootstrap: error: std root not found at %s" % std_root, file=sys.stderr)
        return 2

    env = clean_bootstrap_env()
    ok_env, bad_tool = verify_no_external_tools_on_path(env)
    if not ok_env:
        print("bootstrap: error: external tool still on PATH: %s" % bad_tool, file=sys.stderr)
        return 1

    axiomc1 = os.path.abspath(args.out) if args.out else os.path.join(build_dir, "axiomc1.exe")
    base_dir = os.path.dirname(axiomc1)

    bundle_text = load_bundle_text(root)
    bundle_bytes = bundle_text.encode("utf-8")
    bundle_sha = sha256_bytes(bundle_bytes)
    t_hash = time.perf_counter()
    source_files = collect_source_hashes(root, std_root)
    print("INPUTS: %d source files hashed in %.2fs (sources %s)" % (len(source_files), time.perf_counter() - t_hash, files_digest(source_files)[:16]))

    eff_cache_dir = None
    if args.cache_dir is not None:
        eff_cache_dir = os.path.abspath(args.cache_dir) if args.cache_dir else None
    elif args.seed is not None or args.trust_root:
        eff_cache_dir = default_compiler_cache_dir(root)

    tmp_ctx = None
    if args.bundle_out:
        bundle_path = os.path.abspath(args.bundle_out)
        os.makedirs(os.path.dirname(bundle_path), exist_ok=True)
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="axiom_bootstrap_")
        bundle_path = os.path.join(tmp_ctx.name, "axiomc_bundle.ax")

    try:
        with open(bundle_path, "wb") as f:
            f.write(bundle_bytes)

        stage_results = []

        # Stage 1: axiom0 -> axiomc1 (kept in both full-chain and seeded modes as the Stage-0 guard, T487 Scope 3)
        exp1 = make_inputs(
            "stage1", source_files, sha256_file(stage0), bundle_sha,
            {"opt": args.opt, "stack_reserve": args.stack_reserve},
        )
        reused_s1, why1 = (None, "reuse not requested")
        if args.reuse_existing:
            reused_s1, why1 = find_reusable([axiomc1], exp1)
        if reused_s1 is not None:
            r1 = make_cached_result("stage1_axiom0_to_axiomc1", args.opt, axiomc1, root)
            print("REUSED %s (inputs %s)" % (axiomc1, exp1["inputs_hash"][:16]))
        else:
            drop_manifest(axiomc1)
            r1 = run_stage_build(
                "stage1_axiom0_to_axiomc1",
                stage0,
                bundle_path,
                axiomc1,
                std_root,
                args.stack_reserve,
                args.opt,
                args.time_passes or bool(args.perf_csv),
                root,
                env,
            )
            if r1["rc"] == 0 and os.path.isfile(axiomc1):
                write_manifest(axiomc1, exp1, r1["sha256"])
                print("REBUILT %s (%s)" % (axiomc1, why1))
        stage_results.append(r1)
        if r1["rc"] != 0 or not os.path.isfile(axiomc1):
            print(
                "bootstrap: FAIL stage1 (axiom0 -> axiomc1) rc=%d\n%s"
                % (r1["rc"], r1["stderr"][:2000]),
                file=sys.stderr,
            )
            return 1
        print(
            "STAGE1 OK: %s (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
            % (axiomc1, r1["size_bytes"], r1["sha256"][:16], r1["wall_s"], r1["peak_ws_mb"], r1["peak_commit_mb"])
        )

        # Stage 2 & Stage 3 across requested optimization levels
        if max_stage >= 2:
            # Check which requested opt_levels already have valid full-chain or verified seeded outputs in base_dir
            reusable_opts = set()
            if args.reuse_existing and not args.trust_root and not args.full_chain:
                for opt_lvl in opt_levels:
                    fl = {"opt": opt_lvl, "stack_reserve": args.stack_reserve}
                    s2_p = os.path.join(base_dir, "dir_stage2_%s" % opt_lvl, "axiomc2.exe")
                    s2_cands = [
                        s2_p,
                        os.path.join(base_dir, "axiomc2_%s.exe" % opt_lvl),
                        os.path.join(base_dir, "axiomc2.exe") if opt_lvl == "O1" else "",
                    ]
                    e2 = make_inputs("stage2", source_files, r1["sha256"], bundle_sha, fl)
                    is_seeded_s2 = False
                    reused_s2, _w2 = find_reusable(s2_cands, e2)
                    if reused_s2 is None:
                        reused_s2, _e2 = _find_reusable_seeded_stage2(
                            base_dir, opt_lvl, s2_cands, source_files, bundle_sha, fl
                        )
                        if reused_s2 is not None:
                            is_seeded_s2 = True
                    if reused_s2 is None:
                        continue
                    if max_stage >= 3 or is_seeded_s2:
                        s3_p = os.path.join(base_dir, "dir_stage3_%s" % opt_lvl, "axiomc3.exe")
                        s3_cands = [
                            s3_p,
                            os.path.join(base_dir, "axiomc3_%s.exe" % opt_lvl),
                            os.path.join(base_dir, "axiomc3.exe") if opt_lvl == "O1" else "",
                        ]
                        s2_sha = sha256_file(reused_s2)
                        e3 = make_inputs("stage3", source_files, s2_sha, bundle_sha, fl)
                        reused_s3, _w3 = find_reusable(s3_cands, e3)
                        if reused_s3 is None:
                            continue
                        if is_seeded_s2 and (
                            sha256_file(reused_s3) != s2_sha or not files_byte_identical(reused_s2, reused_s3)
                        ):
                            continue
                    if is_seeded_s2 and not args.no_stage0_smoke:
                        if not _seeded_stage0_guard_verified(base_dir, opt_lvl, r1["sha256"]):
                            continue
                    reusable_opts.add(opt_lvl)
            all_existing_reusable = len(reusable_opts) == len(opt_levels)

            seed_compiler = None
            if args.seed and not args.full_chain and not args.trust_root and not all_existing_reusable:
                seed_compiler, seed_reason = resolve_seed_compiler(
                    args.seed,
                    eff_cache_dir,
                    root,
                    source_files,
                    bundle_sha,
                    args.stack_reserve,
                    preferred_opt=opt_levels[0],
                )
                if seed_compiler is not None:
                    print("SEED: hit %s (%s, sha256=%s)" % (seed_compiler, seed_reason, sha256_file(seed_compiler)[:16]))
                else:
                    print("SEED: miss (%s); falling back to full chain" % seed_reason)

            if seed_compiler is not None:
                pending_seeded_pubs = []
                for opt_lvl in opt_levels:
                    if opt_lvl in reusable_opts:
                        ok_opt, opt_results = run_stage2_and_stage3_for_opt(
                            opt_lvl,
                            axiomc1,
                            bundle_bytes,
                            std_root,
                            args.stack_reserve,
                            base_dir,
                            max_stage,
                            args.time_passes or bool(args.perf_csv),
                            env,
                            reuse_existing=True,
                            source_files=source_files,
                            allow_seeded_reuse=True,
                            cache_dir=eff_cache_dir,
                        )
                    else:
                        ok_opt, opt_results = run_seeded_for_opt(
                            opt_lvl,
                            seed_compiler,
                            bundle_bytes,
                            std_root,
                            args.stack_reserve,
                            base_dir,
                            args.time_passes or bool(args.perf_csv),
                            env,
                            reuse_existing=args.reuse_existing,
                            source_files=source_files,
                            cache_dir=None,
                            publish_queue=pending_seeded_pubs,
                        )
                    stage_results.extend(opt_results)
                    if not ok_opt:
                        _drop_seeded_pub_manifests(pending_seeded_pubs)
                        return 1
                stage0_guard_c1_sha = None
                if not args.no_stage0_smoke:
                    built_opts = [p["opt_level"] for p in pending_seeded_pubs]
                    if "O1" in built_opts:
                        primary_opt = "O1"
                    elif built_opts:
                        primary_opt = built_opts[0]
                    else:
                        primary_opt = "O1" if "O1" in opt_levels else opt_levels[0]
                    b_bin = os.path.join(base_dir, "dir_stage2_%s" % primary_opt, "axiomc2.exe")
                    if not run_stage0_smoke_guard(axiomc1, b_bin, root, std_root, primary_opt, env):
                        _drop_seeded_pub_manifests(pending_seeded_pubs)
                        return 1
                    stage0_guard_c1_sha = r1["sha256"]
                for pub in pending_seeded_pubs:
                    _publish_seeded_opt(
                        pub, source_files, bundle_sha, eff_cache_dir, stage0_guard_c1_sha=stage0_guard_c1_sha
                    )
            else:
                # T487 F1: resolve any pre-existing trust-root seed BEFORE full-chain builds or writes compiler-cache/
                tr_seed, tr_reason = (None, "")
                if args.trust_root:
                    tr_seed, tr_reason = resolve_seed_compiler(
                        args.seed or "auto",
                        eff_cache_dir,
                        root,
                        source_files,
                        bundle_sha,
                        args.stack_reserve,
                        preferred_opt=opt_levels[0],
                    )
                for opt_lvl in opt_levels:
                    ok_opt, opt_results = run_stage2_and_stage3_for_opt(
                        opt_lvl,
                        axiomc1,
                        bundle_bytes,
                        std_root,
                        args.stack_reserve,
                        base_dir,
                        max_stage,
                        args.time_passes or bool(args.perf_csv),
                        env,
                        reuse_existing=args.reuse_existing,
                        source_files=source_files,
                        allow_seeded_reuse=not (args.full_chain or args.trust_root),
                        cache_dir=None if args.trust_root else eff_cache_dir,
                    )
                    stage_results.extend(opt_results)
                    if not ok_opt:
                        return 1

                if args.trust_root:
                    if tr_seed is not None:
                        print("TRUST-ROOT SEED: %s (%s, sha256=%s)" % (tr_seed, tr_reason, sha256_file(tr_seed)[:16]))
                        for opt_lvl in opt_levels:
                            ok_tr, tr_results = verify_trust_root_c2_equals_seeded_b(
                                opt_lvl,
                                tr_seed,
                                bundle_bytes,
                                std_root,
                                args.stack_reserve,
                                base_dir,
                                args.time_passes or bool(args.perf_csv),
                                env,
                                reuse_existing=args.reuse_existing,
                                source_files=source_files,
                            )
                            stage_results.extend(tr_results)
                            if not ok_tr:
                                return 1
                    else:
                        print("TRUST-ROOT SEED: none (%s); full chain c2 == c3 verified" % tr_reason)
                    if eff_cache_dir:
                        for opt_lvl in opt_levels:
                            c2_bin = os.path.join(base_dir, "dir_stage2_%s" % opt_lvl, "axiomc2.exe")
                            fl = {"opt": opt_lvl, "stack_reserve": args.stack_reserve}
                            store_compiler_cache(eff_cache_dir, c2_bin, source_files, bundle_sha, fl)

        if args.perf_csv:
            write_perf_csv(args.perf_csv, stage_results)
            print("PERF-CSV WRITTEN: %s" % args.perf_csv)

        if args.check_budget:
            if r1["wall_s"] >= STAGE1_MAX_WALL_S:
                print(
                    "bootstrap: FAIL stage1 wall time %.2fs exceeds budget %.2fs"
                    % (r1["wall_s"], STAGE1_MAX_WALL_S),
                    file=sys.stderr,
                )
                return 1
            if r1["peak_ws_mb"] >= STAGE1_MAX_PEAK_MB:
                print(
                    "bootstrap: FAIL stage1 peak memory %.1fMB exceeds budget %.1fMB"
                    % (r1["peak_ws_mb"], STAGE1_MAX_PEAK_MB),
                    file=sys.stderr,
                )
                return 1
            for res in stage_results[1:]:
                if res["wall_s"] >= STAGE2_MAX_WALL_S:
                    print(
                        "bootstrap: FAIL %s wall time %.2fs exceeds budget %.2fs"
                        % (res["stage"], res["wall_s"], STAGE2_MAX_WALL_S),
                        file=sys.stderr,
                    )
                    return 1
                if res["peak_ws_mb"] >= STAGE2_MAX_PEAK_MB:
                    print(
                        "bootstrap: FAIL %s peak memory %.1fMB exceeds budget %.1fMB"
                        % (res["stage"], res["peak_ws_mb"], STAGE2_MAX_PEAK_MB),
                        file=sys.stderr,
                    )
                    return 1

        return 0
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


if __name__ == "__main__":
    sys.exit(main())
