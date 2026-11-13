#!/usr/bin/env python3
"""taskgate - the whole per-task QA gate scope in one command (T437a; `.claude/agents/axiom-qa.md`
"Per-task gate scope"; ADR-0041 §4/§6). Not the phase-gate checker (that is tools/gatecheck.py).

    python tools/taskgate.py --task <ID> [--range <base>..<head> | --changed @file] [--compiler PATH] [-j 2]
                             [--no-cache] [--seed N] [--json-out PATH] [--extra <id> ...]
                             [--baseline FILE] [--cache-dir DIR] [--root DIR]

Runs, deduplicated and in one `axtest.py` invocation with `--gate --baseline <file>`:
  (1) own       the task's own tests: every test under a `tests/...` entry of the task's `paths:` + `--extra`;
  (2) affected  `axtest.py --affected` of the change set (derivation printed), plus the tool self-test
                directories it selects (`tools/tests/X/run_selftests.py`, run separately);
  (3) smoke     `axtest.py --smoke` (tests/smoke.list; seed printed);
  (4) archcheck `tools/archcheck.py`.
The change set defaults to the working-tree changes of the root against its HEAD (inside a QA snapshot
`build-snap-<ID>` that is exactly the task's change set); `--range` or `--changed` override it.

Prints a Markdown block for the QA file (counts per part and per group, affected-set derivation,
CACHED/miss/sample counts and seed, WEAK-NATIVE, NEW/BASELINE failures, tool self-tests, archcheck, wall time)
and writes the same as JSON with `--json-out`.

Exit status: 0 only if archcheck is clean, no failing id lies outside the baseline (tool self-test failures
count as new failures) and no WEAK-NATIVE test is among the task's own or changed tests; otherwise 1;
2 for a usage/environment error. Python 3 standard library only.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import axtest  # noqa: E402
import axtest_affected  # noqa: E402
import axtest_cache  # noqa: E402

FAIL_STATES = ("FAIL", "XPASS", "CRASH", "TIMEOUT")
DERIVATION_LINES_MAX = 400


class GateError(Exception):
    pass


def find_task_file(root, tid):
    for base in (Path(root), axtest_cache.main_checkout(root)):
        tasks = base / "_workspaces" / "tasks"
        for sub in ("doing", "todo", "done", "blocked"):
            d = tasks / sub
            if d.is_dir():
                for p in sorted(d.glob("%s-*.md" % tid)):
                    return p
                p = d / ("%s.md" % tid)
                if p.is_file():
                    return p
    return None


def task_paths(task_file):
    text = task_file.read_bytes().decode("utf-8", "replace")
    m = re.search(r"^paths:\s*\[(.*?)\]\s*$", text, re.M)
    if not m:
        return []
    return [x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()]


def own_test_ids(paths, tests):
    ids = set()
    for p in paths:
        p = p.rstrip("/")
        if not p.startswith("tests/"):
            continue
        rel = p[len("tests/"):]
        for t in tests:
            if t.id == rel or t.id.startswith(rel + "/"):
                ids.add(t.id)
    return ids


def run_cmd(cmd, cwd, timeout=None):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, b"", b"timeout", time.time() - t0
    return p.returncode, p.stdout, p.stderr, time.time() - t0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="taskgate.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--task", required=True, metavar="ID")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--range", metavar="BASE..HEAD", help="change set = git diff BASE HEAD")
    g.add_argument("--changed", metavar="@FILE", help="change set = paths listed in FILE (one per line)")
    ap.add_argument("--compiler", default=None, help="compiler under test (default: axtest's default)")
    ap.add_argument("-j", "--jobs", type=int, default=2)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--seed", type=int, default=None, help="smoke seed (default: hash of the change set)")
    ap.add_argument("--json-out", metavar="PATH")
    ap.add_argument("--extra", nargs="*", default=[], metavar="ID", help="more own test ids")
    ap.add_argument("--baseline", default=None, help="default <root>/_workspaces/baseline-failures.txt")
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--root", default=str(HERE.parent))
    ap.add_argument("--timeout-scale", default=None)
    ap.add_argument("--exclude-requires", action="append", default=[])
    ap.add_argument("--build-dir", default=None, help="the {build} placeholder of exec manifests (axtest --build-dir)")
    ap.add_argument("--exe-suffix", default=None, help=argparse.SUPPRESS)   # self-test hook (stub compiler)
    opts = ap.parse_args(argv)
    t_start = time.time()
    root = Path(axtest.native_path(opts.root)).resolve()
    try:
        summary = gate(opts, root)
    except (GateError, axtest_affected.AffectedError) as e:
        print("taskgate: %s" % e, file=sys.stderr)
        return 2
    summary["wall_s"] = round(time.time() - t_start, 1)
    md = markdown(summary)
    print(md)
    if opts.json_out:
        Path(opts.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(opts.json_out).write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return summary["exit"]


def gate(opts, root):
    tests = axtest.discover(root / "tests")
    tf = find_task_file(root, opts.task)
    if tf is None:
        raise GateError("no task file for %s under _workspaces/tasks/" % opts.task)
    paths = task_paths(tf)
    # change set
    if opts.range:
        change_args = [opts.range]
        change_src = "range %s" % opts.range
    elif opts.changed:
        change_args = [opts.changed if opts.changed.startswith("@") else "@" + opts.changed]
        change_src = "file %s" % opts.changed.lstrip("@")
    else:
        cp = axtest_cache.changed_paths(root)
        if cp is None:
            raise GateError("%s is not a git checkout; pass --range or --changed" % root)
        fd, tmpf = tempfile.mkstemp(prefix="taskgate-changed-", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(cp) + "\n")
        change_args = ["@" + tmpf]
        change_src = "working tree of %s vs HEAD" % root.name
    cache_dir = Path(opts.cache_dir).resolve() if opts.cache_dir else axtest_cache.default_cache_dir(root)
    try:
        aff = axtest_affected.derive(root, change_args, tests, cache_dir)
    finally:
        if change_src.startswith("working tree"):
            try:
                os.remove(change_args[0][1:])
            except OSError:
                pass
    own =own_test_ids(paths, tests) | set(opts.extra)
    unknown_extra = sorted(set(opts.extra) - {t.id for t in tests})
    seed = opts.seed if opts.seed is not None else axtest.change_seed(root, aff.changed)
    smoke = axtest_affected.smoke_select(root, tests, seed)
    parts = {"own": sorted(own), "affected": aff.ids, "smoke": smoke.ids}
    all_ids = sorted(set().union(*[set(v) for v in parts.values()]))
    baseline = Path(opts.baseline) if opts.baseline else root / "_workspaces" / "baseline-failures.txt"
    if not baseline.is_file():
        raise GateError("baseline file %s does not exist" % baseline)

    # (1)-(3): one axtest run
    doc = None
    ax_lines = []
    ax_rc = 0
    ax_wall = 0.0
    if all_ids:
        fd, idf = tempfile.mkstemp(prefix="taskgate-ids-", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(all_ids) + "\n")
        cmd = [sys.executable, str(root / "tools" / "axtest.py"), "--root", str(root), "--id-file", idf,
               "--gate", "--baseline", str(baseline), "--json", "-j", str(opts.jobs)]
        if opts.compiler:
            cmd += ["--compiler", opts.compiler]
        if opts.no_cache:
            cmd.append("--no-cache")
        if opts.cache_dir:
            cmd += ["--cache-dir", str(cache_dir)]
        if opts.timeout_scale:
            cmd += ["--timeout-scale", opts.timeout_scale]
        if opts.build_dir:
            cmd += ["--build-dir", opts.build_dir]
        if opts.exe_suffix is not None:
            cmd += ["--exe-suffix", opts.exe_suffix]
        for r in opts.exclude_requires:
            cmd += ["--exclude-requires", r]
        ax_rc, out, err, ax_wall = run_cmd(cmd, root)
        ax_lines = err.decode("utf-8", "replace").splitlines()
        try:
            doc = json.loads(out.decode("utf-8"))
        except ValueError:
            raise GateError("axtest produced no JSON document (exit %s): %s" % (ax_rc, "\n".join(ax_lines[-20:])))
        os.remove(idf)

    # (2b): tool self-tests selected by the change set. A failing self-test is "known" (does not fail the
    # gate) when its id `tools/tests/<dir>::<unittest id>` is in the baseline file or the same test fails in the
    # HEAD version of tools/ (git archive HEAD tools, run there); otherwise it is a new failure.
    baseline_ids = set(axtest.read_baseline(str(baseline)))
    tools_res = []
    for d in sorted(aff.tools):
        script = root / d / "run_selftests.py"
        if not script.is_file():
            tools_res.append({"dir": d, "state": "SKIP", "detail": "no run_selftests.py", "s": 0})
            continue
        rc, out, err, secs = run_cmd([sys.executable, str(script)], root)
        lines = (out + err).decode("utf-8", "replace").strip().splitlines()
        tail = [l for l in lines if l.startswith("SELFTEST")][-1:] or lines[-1:] or [""]
        res = {"dir": d, "state": "PASS" if rc == 0 else "FAIL", "detail": tail[0], "s": round(secs, 1),
               "failing": [], "new": [], "known": []}
        if rc != 0:
            failing = selftest_failures(d, lines)
            res["failing"] = failing
            known_base = {f for f in failing if f in baseline_ids}
            at_head = set()
            rest = [f for f in failing if f not in known_base]
            if rest:
                at_head = head_selftest_failures(root, d)
            res["known"] = sorted(known_base | (set(rest) & at_head))
            res["new"] = sorted(set(failing) - set(res["known"]))
            if failing and not res["new"]:
                res["state"] = "KNOWN"
                res["detail"] += " (every failure also fails at HEAD or is in the baseline)"
        tools_res.append(res)

    # (4) archcheck
    arch = root / "tools" / "archcheck.py"
    if arch.is_file():
        a_rc, a_out, a_err, a_secs = run_cmd([sys.executable, str(arch), "--root", str(root)], root)
        arch_lines = (a_out + a_err).decode("utf-8", "replace").strip().splitlines()
        arch_res = {"exit": a_rc, "clean": a_rc == 0, "tail": arch_lines[-5:], "s": round(a_secs, 1)}
    else:
        arch_res = {"exit": None, "clean": False, "tail": ["tools/archcheck.py missing"], "s": 0}

    # results by id
    results = doc["results"] if doc else []
    by_id = {}
    for r in results:
        by_id.setdefault(r["id"], []).append(r)
    failing = sorted(i for i, rs in by_id.items() if any(r["state"] in FAIL_STATES for r in rs))
    base_doc = (doc or {}).get("baseline") or {"new_failures": [], "now_passing": [], "ok": True}
    new_fail = list(base_doc.get("new_failures", []))
    tool_fail = [t["dir"] for t in tools_res if t["state"] == "FAIL"]
    tool_known = sorted(f for t in tools_res for f in t.get("known", []))
    changed_tests = {i for i, rs in aff.reasons.items() if any(x.startswith("test: changed test file") for x in rs)}
    weak_scope = own | changed_tests
    weak_all = sorted({r["id"] + " [%s]" % r["mode"] for r in results if r.get("weak_native_evidence")})
    weak_task = sorted({r["id"] + " [%s]" % r["mode"] for r in results
                        if r.get("weak_native_evidence") and r["id"] in weak_scope})

    def part_counts(ids):
        c = {"ids": len(ids), "results": 0, "PASS": 0, "FAIL": 0, "SKIP": 0, "XFAIL": 0, "CACHED": 0}
        for i in ids:
            for r in by_id.get(i, []):
                c["results"] += 1
                st = r["state"]
                if st in FAIL_STATES:
                    c["FAIL"] += 1
                elif st in c:
                    c[st] += 1
                if r.get("cached"):
                    c["CACHED"] += 1
        return c

    groups = {}
    for i in all_ids:
        g = i.split("/", 1)[0]
        e = groups.setdefault(g, {"ids": 0, "failing": 0, "parts": set()})
        e["ids"] += 1
        if i in failing:
            e["failing"] += 1
        for pn, ids in parts.items():
            if i in ids:
                e["parts"].add(pn)
    for e in groups.values():
        e["parts"] = sorted(e["parts"])

    reasons = []
    if not arch_res["clean"]:
        reasons.append("archcheck not clean")
    if new_fail:
        reasons.append("new failures outside the baseline: %s" % " ".join(new_fail))
    if tool_fail:
        reasons.append("tool self-tests failed: %s" % " ".join(tool_fail))
    if weak_task:
        reasons.append("WEAK-NATIVE in the task's own/changed tests: %s" % " ".join(weak_task))
    if ax_rc not in (0, 1):
        reasons.append("axtest exited %s" % ax_rc)
    head = axtest_cache.git(root, "rev-parse", "HEAD")
    return {
        "schema": 1,
        "tool": "taskgate",
        "task": opts.task,
        "task_file": task_file_rel(tf, root),
        "root": root.as_posix(),
        "head": head.strip() if head else None,
        "compiler": (doc or {}).get("compiler") or opts.compiler,
        "jobs": opts.jobs,
        "change_source": change_src,
        "changed": aff.changed,
        "parts": {pn: part_counts(ids) for pn, ids in parts.items()},
        "total": part_counts(all_ids),
        "ids": {"own": parts["own"], "affected": parts["affected"], "smoke": parts["smoke"]},
        "unknown_extra": unknown_extra,
        "groups": dict(sorted(groups.items())),
        "affected": aff.as_dict(),
        "smoke": smoke.as_dict(),
        "cache": (doc or {}).get("cache"),
        "axtest": {"exit": ax_rc, "wall_s": round(ax_wall, 1), "total_line": (doc or {}).get("total_line"),
                   "lines": [l for l in ax_lines if re.match(r"^(CACHED|VERIFY-SAMPLE|CACHE-|BASELINE|NEW FAILURES|UNKNOWN-ID)", l)]},
        "failing": failing,
        "baseline": {"file": str(baseline), "new_failures": new_fail, "now_passing": base_doc.get("now_passing", []),
                     "ok": not new_fail},
        "weak_native": {"total": len(weak_all), "task_scope": weak_task},
        "tools": tools_res,
        "tools_known_failures": tool_known,
        "archcheck": arch_res,
        "exit": 1 if reasons else 0,
        "reasons": reasons,
    }


FAIL_LINE_RE = re.compile(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)")


def selftest_failures(d, lines):
    """`tools/tests/<dir>::<unittest id>` of every FAIL/ERROR line of a unittest run."""
    out = set()
    for l in lines:
        m = FAIL_LINE_RE.match(l)
        if m:
            uid = m.group(2)
            if not uid.endswith("." + m.group(1)):
                uid = uid + "." + m.group(1)
            out.add("%s::%s" % (d, uid))
    return sorted(out)


def head_selftest_failures(root, d):
    """Failing self-test ids of `d` in the HEAD version of tools/ (an empty set if that cannot be run)."""
    import shutil
    import zipfile
    tmp = Path(tempfile.mkdtemp(prefix="taskgate-head-"))
    try:
        zpath = tmp / "tools.zip"
        r = subprocess.run(["git", "archive", "--format=zip", "-o", str(zpath), "HEAD", "tools"], cwd=str(root),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            return set()
        with zipfile.ZipFile(str(zpath)) as z:
            z.extractall(str(tmp / "head"))
        script = tmp / "head" / d / "run_selftests.py"
        if not script.is_file():
            return set()
        rc, out, err, _s = run_cmd([sys.executable, str(script)], tmp / "head")
        return set(selftest_failures(d, (out + err).decode("utf-8", "replace").splitlines()))
    except (OSError, zipfile.BadZipFile):
        return set()
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)


def task_file_rel(tf, root):
    try:
        return tf.resolve().relative_to(root).as_posix()
    except ValueError:
        return tf.as_posix()


def markdown(s):
    L = []
    L.append("### taskgate %s (`tools/taskgate.py`)" % s["task"])
    L.append("")
    L.append("- root `%s`, HEAD `%s`, compiler `%s`, `-j %s`" % (s["root"], (s["head"] or "?")[:12], s["compiler"], s["jobs"]))
    L.append("- change set: %d file(s) (%s)" % (len(s["changed"]), s["change_source"]))
    for f in s["changed"][:60]:
        L.append("  - `%s`" % f)
    if len(s["changed"]) > 60:
        L.append("  - ... %d more (JSON)" % (len(s["changed"]) - 60))
    L.append("- wall time: %.1f s (axtest %.1f s)" % (s.get("wall_s", 0), s["axtest"]["wall_s"]))
    L.append("")
    L.append("| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |")
    L.append("|---|---|---|---|---|---|---|---|")
    for pn in ("own", "affected", "smoke"):
        c = s["parts"][pn]
        L.append("| %s | %d | %d | %d | %d | %d | %d | %d |" % (pn, c["ids"], c["results"], c["PASS"], c["FAIL"], c["SKIP"], c["XFAIL"], c["CACHED"]))
    c = s["total"]
    L.append("| **total (dedup)** | %d | %d | %d | %d | %d | %d | %d |" % (c["ids"], c["results"], c["PASS"], c["FAIL"], c["SKIP"], c["XFAIL"], c["CACHED"]))
    L.append("")
    L.append("Counts per group:")
    L.append("")
    L.append("| group | ids | failing | parts |")
    L.append("|---|---|---|---|")
    for g, e in s["groups"].items():
        L.append("| %s | %d | %d | %s |" % (g, e["ids"], e["failing"], ", ".join(e["parts"])))
    L.append("")
    a = s["affected"]
    L.append("Affected-set derivation (rule per id; rules in `tools/axtest_affected.py`):")
    L.append("")
    n = 0
    for tid, rs in a["ids"].items():
        n += 1
        if n > DERIVATION_LINES_MAX:
            L.append("- ... %d more ids (JSON `affected.ids`)" % (len(a["ids"]) - DERIVATION_LINES_MAX))
            break
        L.append("- `%s` <- %s%s" % (tid, rs[0], (" (+%d more)" % (len(rs) - 1)) if len(rs) > 1 else ""))
    for t, rs in a["tools"].items():
        L.append("- tool self-tests `%s` <- %s" % (t, rs[0]))
    if not a["ids"] and not a["tools"]:
        L.append("- (empty)")
    if a["noop"]:
        L.append("- no-op (select nothing): %s" % ", ".join("`%s`" % x for x in a["noop"]))
    L.append("- unmatched changed files: %s" % (", ".join("`%s`" % x for x in a["unmatched"]) or "none"))
    for u in a.get("unresolved") or []:
        L.append("- UNRESOLVED (whole group selected): %s" % u)
    for n in a.get("notes") or []:
        L.append("- MAP-NOTE: %s" % n)
    dfr = a.get("deferred") or {}
    if dfr:
        L.append("- deferred to the periodic full run (%d ids, list in JSON `affected.deferred`): %s%s" % (
            len(dfr), ", ".join("`%s`" % x for x in list(dfr)[:20]), " ..." if len(dfr) > 20 else ""))
    L.append("")
    sm = s["smoke"]
    L.append("Smoke: seed=%d, always %s; picks %s" % (sm["seed"], ", ".join("`%s`" % x for x in sm["always"]),
                                                     ", ".join("%s=`%s`" % kv for kv in sm["picks"].items())))
    L.append("")
    cache = s.get("cache") or {}
    if cache:
        L.append("Cache: CACHED %s, miss %s, uncacheable %s, stored %s, dep_source %s, verification sample seed=%s "
                 "n=%s of %s hits, mismatch %s, rejected %s, producer %s" % (
                     cache.get("cached"), cache.get("miss"), cache.get("uncacheable"), cache.get("stored"),
                     cache.get("dep_source"), cache.get("sample_seed"), cache.get("sample_n"), cache.get("hits"),
                     " ".join(cache.get("mismatch") or []) or "none", cache.get("rejected") or {},
                     (cache.get("producer") or {}).get("origin")))
    else:
        L.append("Cache: not used")
    w = s["weak_native"]
    L.append("WEAK-NATIVE: %d in the run; %d in the task's own/changed tests%s" % (
        w["total"], len(w["task_scope"]), (": " + " ".join(w["task_scope"])) if w["task_scope"] else ""))
    b = s["baseline"]
    L.append("Baseline (`%s`): %s%s" % (b["file"], "BASELINE OK" if b["ok"] else "NEW FAILURES: " + " ".join(b["new_failures"]),
                                       ("; BASELINE NOW PASSING: " + " ".join(b["now_passing"])) if b["now_passing"] else ""))
    L.append("Failing ids: %s" % (" ".join(s["failing"]) or "none"))
    if s["tools"]:
        L.append("Tool self-tests: " + "; ".join("`%s` %s (%s, %.1f s)" % (t["dir"], t["state"], t["detail"], t["s"]) for t in s["tools"]))
        for t in s["tools"]:
            for f in t.get("known", []):
                L.append("- known tool self-test failure (fails at HEAD too / baseline): `%s`" % f)
            for f in t.get("new", []):
                L.append("- NEW tool self-test failure: `%s`" % f)
    ar = s["archcheck"]
    L.append("archcheck: %s (exit %s) %s" % ("clean" if ar["clean"] else "NOT CLEAN", ar["exit"], " | ".join(ar["tail"][-2:])))
    L.append("axtest: `%s` (exit %s)" % (s["axtest"]["total_line"], s["axtest"]["exit"]))
    L.append("")
    L.append("TASKGATE %s exit=%d%s" % (s["task"], s["exit"], (" (" + "; ".join(s["reasons"]) + ")") if s["reasons"] else ""))
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
