#!/usr/bin/env python3
"""Periodic 2-tier suite sweep bookkeeping (owner decisions 2026-11-13, updated 2026-11-14).

  fullrun.py due            exit 0 and print the reason + tier when a sweep is due and none runs;
                            exit 1 when nothing is due; exit 3 when one is already running
  fullrun.py start [--full] mark a run as started on HEAD (prints the run number n; records mode
                            'full-nocache' at phase gates / --full, else 'non-selfhost')
  fullrun.py finish --clean the run found no new failing id: last_full_commit := the run's commit
  fullrun.py finish         the run is over but found regressions: keep the old reference commit
  fullrun.py non-selfhost-ids <out-file> [--root <dir>]
                            write all non-selfhost test ids (+ selfhost/bundles_current.test) to <out-file>
  fullrun.py show

Tiers (owner decision 2026-11-14):
  - Tier 1 ('non-selfhost'): triggered every `threshold` (default 25) accepted tasks; runs all
    non-selfhost tests + selfhost/bundles_current.test with cache enabled (`--gate -j 2`).
  - Tier 2 ('full-nocache'): triggered when a phase-gate commit (`T3<nn>:`) was accepted or with
    `start --full`; runs the entire suite incl. `tests/selfhost/**` with `--no-cache -j 2`.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), *[".."] * 4))
STATE = os.path.join(ROOT, "_workspaces", "fullrun-state.json")
DEFAULT_THRESHOLD = 25


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, check=True).stdout.strip()


def load():
    with open(STATE, encoding="utf-8") as f:
        return json.load(f)


def save(st):
    with open(STATE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(st, f, indent=2)
        f.write("\n")


def accepted_since(st):
    ref = st.get("last_full_commit") or st.get("baseline_commit_for_count")
    subjects = git("log", "--format=%s", f"{ref}..HEAD").splitlines()
    tasks = [s for s in subjects if re.match(r"^T\d+[a-z]?:", s)]
    gates = [s for s in tasks if re.match(r"^T3\d\d:", s)]
    return ref, len(tasks), gates


def write_non_selfhost_ids(out_path, repo_root):
    axtest = os.path.join(repo_root, "tools", "axtest.py")
    res = subprocess.run(
        [sys.executable, axtest, "--root", repo_root, "--exclude-requires", "axiom0-internal", "--list"],
        capture_output=True, text=True, check=True, encoding="utf-8"
    )
    seen = set()
    ids = []
    for line in res.stdout.splitlines():
        parts = line.split()
        if not parts:
            continue
        tid = parts[0]
        if tid not in seen and (not tid.startswith("selfhost/") or tid == "selfhost/bundles_current.test"):
            seen.add(tid)
            ids.append(tid)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for tid in ids:
            f.write(tid + "\n")
    print(f"wrote {len(ids)} ids to {out_path}")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    st = load()
    threshold = int(st.get("threshold", DEFAULT_THRESHOLD))
    if cmd == "show":
        ref, n, gates = accepted_since(st)
        print(json.dumps(st, indent=2))
        print(f"accepted since {ref}: {n}/{threshold}; phase gates among them: {len(gates)}")
        return 0
    if cmd == "due":
        if st.get("running"):
            mode = st["running"].get("mode", "full-nocache")
            print(f"full run {st['running']['n']} ({mode}) already running since {st['running']['since']}")
            return 3
        ref, n, gates = accepted_since(st)
        if gates:
            print(f"due (full-nocache): phase gate accepted ({gates[0]}) ; {n} tasks since {ref[:8]}")
            return 0
        if n >= threshold:
            print(f"due (non-selfhost): {n} tasks accepted since {ref[:8]} (threshold {threshold})")
            return 0
        print(f"not due: {n}/{threshold} tasks since {ref[:8]}")
        return 1
    if cmd == "start":
        if st.get("running"):
            print("a full run is already running", file=sys.stderr)
            return 3
        _ref, _n, gates = accepted_since(st)
        mode = "full-nocache" if ("--full" in sys.argv or gates) else "non-selfhost"
        n = int(st.get("runs_started", 0)) + 1
        st["runs_started"] = n
        st["running"] = {
            "n": n,
            "mode": mode,
            "commit": git("rev-parse", "HEAD"),
            "since": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        save(st)
        print(n)
        return 0
    if cmd == "finish":
        run = st.get("running")
        if not run:
            print("no full run is running", file=sys.stderr)
            return 1
        if "--clean" in sys.argv:
            st["last_full_commit"] = run["commit"]
            st["last_full_at"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            st["last_full_mode"] = run.get("mode", "non-selfhost")
        st["running"] = None
        save(st)
        print("finished", "(clean)" if "--clean" in sys.argv else "(regressions: reference commit kept)")
        return 0
    if cmd == "non-selfhost-ids":
        if len(sys.argv) < 3:
            print("usage: fullrun.py non-selfhost-ids <out-file> [--root <dir>]", file=sys.stderr)
            return 2
        out_path = sys.argv[2]
        repo_root = ROOT
        if "--root" in sys.argv:
            idx = sys.argv.index("--root")
            if idx + 1 < len(sys.argv):
                repo_root = sys.argv[idx + 1]
        return write_non_selfhost_ids(out_path, repo_root)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
