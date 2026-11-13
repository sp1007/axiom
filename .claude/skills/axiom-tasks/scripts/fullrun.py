#!/usr/bin/env python3
"""Periodic full-suite run bookkeeping (owner decision 2026-11-13).

  fullrun.py due            exit 0 and print the reason when a full run is due and none runs;
                            exit 1 when nothing is due; exit 3 when one is already running
  fullrun.py start          mark a run as started on HEAD (prints the run number n)
  fullrun.py finish --clean the run found no new failing id: last_full_commit := the run's commit
  fullrun.py finish         the run is over but found regressions: keep the old reference commit
  fullrun.py show

State: _workspaces/fullrun-state.json. Accepted tasks are counted from git: commits whose subject
starts with `T<digits>:` after the reference commit (last full commit, else baseline_commit_for_count).
A phase-gate commit (subject `T3<nn>:`) also makes a run due.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), *[".."] * 4))
STATE = os.path.join(ROOT, "_workspaces", "fullrun-state.json")


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
    tasks = [s for s in subjects if re.match(r"^T\d+:", s)]
    gates = [s for s in tasks if re.match(r"^T3\d\d:", s)]
    return ref, len(tasks), gates


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    st = load()
    if cmd == "show":
        ref, n, gates = accepted_since(st)
        print(json.dumps(st, indent=2))
        print(f"accepted since {ref}: {n}; phase gates among them: {len(gates)}")
        return 0
    if cmd == "due":
        if st.get("running"):
            print(f"full run {st['running']['n']} already running since {st['running']['since']}")
            return 3
        ref, n, gates = accepted_since(st)
        if gates:
            print(f"due: phase gate accepted ({gates[0]}) ; {n} tasks since {ref[:8]}")
            return 0
        if n >= int(st.get("threshold", 10)):
            print(f"due: {n} tasks accepted since {ref[:8]} (threshold {st.get('threshold', 10)})")
            return 0
        print(f"not due: {n}/{st.get('threshold', 10)} tasks since {ref[:8]}")
        return 1
    if cmd == "start":
        if st.get("running"):
            print("a full run is already running", file=sys.stderr)
            return 3
        n = int(st.get("runs_started", 0)) + 1
        st["runs_started"] = n
        st["running"] = {"n": n, "commit": git("rev-parse", "HEAD"),
                         "since": dt.datetime.now().strftime("%Y-%m-%d %H:%M")}
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
        st["running"] = None
        save(st)
        print("finished", "(clean)" if "--clean" in sys.argv else "(regressions: reference commit kept)")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
