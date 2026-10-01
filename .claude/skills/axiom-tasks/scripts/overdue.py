#!/usr/bin/env python3
"""overdue — find autopilot agents that have been running too long and show no activity (hung).

Usage: python .claude/skills/axiom-tasks/scripts/overdue.py [--json]

Reads _workspaces/autopilot.json (repo root found like taskctl, never from the cwd alone):
    "running": {"T010": {"agent": "T010-impl", "stage": "impl", "round": 0,
                         "since": "2026-09-30 14:05", "session": "<id>"}, ...}
    "timeouts": {"impl": 180, "fix": 180, "qa": 60, "unblock": 60}   (minutes, optional)
    "timeouts_long": {"impl": 300, "fix": 300}  (phases P0-traceability and P10, optional)
    "idle_min": 30        an overdue agent with file activity newer than this is kept
    "hard_factor": 2      beyond limit * hard_factor it is hung regardless of activity

Limit for impl/fix: the task's `timeout_min:` front-matter, else timeouts_long for requirement
extraction (phase P0-traceability) and port tasks (phase P10), else timeouts. Activity = newest mtime
of files under the task's paths/locks, its _workspaces/reports/<ID>-* files and its build dirs
(build-<ID>, build-qa-<ID>, build-snap-<ID>) and an optional running[ID].worktree directory.

    "probe_min": 45       a running agent silent (no file activity) this long gets a probe message

One line per entry needing attention: ID, agent, stage, minutes, limit, idle minutes, reason, action:
    kill   (overdue and idle, or past the hard cap)  -> TaskStop + the tick's hang handling
    keep   (overdue but files changed recently)     -> log only, check again next tick
    probe  (within its limit but silent)            -> SendMessage to the agent ("continue <ID>"):
           a live agent just continues, an agent that died in this session (rate limit, API error)
           is resumed from its transcript
Entries from a previous session (running[ID].session differs from the current session token =
$CLAUDE_CODE_SESSION_ID:$CLAUDE_PID, so a resumed session also counts as new) are
listed with action `recover` (the agent died with its session; use `taskctl recover ID`).
Exit 0 always.
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import taskctl  # noqa: E402

DEFAULT = {"impl": 180, "fix": 180, "qa": 60, "unblock": 60}
LONG = {"impl": 300, "fix": 300}
LONG_PHASES = re.compile(r"^(P0-traceability|P10)\b")
ROOT = taskctl.ROOT
PATH = taskctl.AUTOPILOT
SKIP_DIRS = {".git", "__pycache__"}


def parse_time(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return dt.datetime.strptime(s, fmt)
        except (TypeError, ValueError):
            pass
    return None


def newest_mtime(paths, cap=20000):
    best, seen = None, 0
    for p in paths:
        if not os.path.exists(p):
            continue
        if os.path.isfile(p):
            m = os.path.getmtime(p)
            best = m if best is None or m > best else best
            continue
        for d, dirs, fs in os.walk(p):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for f in fs:
                seen += 1
                if seen > cap:
                    return best
                try:
                    m = os.path.getmtime(os.path.join(d, f))
                except OSError:
                    continue
                best = m if best is None or m > best else best
    return best


def activity_paths(tid, task, entry):
    out = []
    if task:
        out += [os.path.join(ROOT, p) for p in taskctl.own_paths(task)]
    out += taskctl.report_paths(tid)
    out += [os.path.join(ROOT, f"build-{tid}"), os.path.join(ROOT, f"build-qa-{tid}"),
            os.path.join(ROOT, f"build-snap-{tid}")]
    if entry.get("worktree"):
        out.append(entry["worktree"])
    if entry.get("stage") == "unblock":
        out += [os.path.join(ROOT, "spec"), os.path.join(ROOT, "_workspaces", "tasks"),
                os.path.join(ROOT, "_workspaces", "reports", f"unblock-{tid}.md")]
    return out


def main():
    if not os.path.exists(PATH):
        print("no autopilot.json")
        return
    state = json.load(open(PATH, encoding="utf-8"))
    limits = {**DEFAULT, **state.get("timeouts", {})}
    long_limits = {**LONG, **state.get("timeouts_long", {})}
    idle_min = int(state.get("idle_min", 30))
    hard_factor = float(state.get("hard_factor", 2))
    probe_min = int(state.get("probe_min", 45))
    session = taskctl.session_token() or state.get("session_id")
    tasks = taskctl.load_all([], allow_empty=True)
    now = dt.datetime.now()
    out = []
    for tid, r in sorted(state.get("running", {}).items()):
        base = {"id": tid, "agent": r.get("agent"), "stage": r.get("stage")}
        if r.get("session") and session and r["session"] != session:
            out.append({**base, "minutes": None, "limit": None, "idle": None,
                        "reason": "previous session", "action": "recover"})
            continue
        since = parse_time(r.get("since"))
        if not since:
            out.append({**base, "minutes": None, "limit": None, "idle": None,
                        "reason": "no 'since' recorded", "action": "set-since"})
            continue
        stage = r.get("stage", "impl")
        task = tasks.get(tid)
        limit = limits.get(stage, limits["impl"])
        if stage in ("impl", "fix") and task:
            if LONG_PHASES.match(task["meta"].get("phase", "")):
                limit = long_limits.get(stage, limit)
            if taskctl.ival(task["meta"], "timeout_min", 0) > 0:
                limit = taskctl.ival(task["meta"], "timeout_min")
        minutes = int((now - since).total_seconds() // 60)
        if minutes < min(limit + 1, probe_min):
            continue
        last = newest_mtime(activity_paths(tid, task, r))
        idle = None if last is None else min(minutes, int((now.timestamp() - last) // 60))
        if minutes <= limit:
            # not overdue yet, but silent: after a rate limit or API error the agent may be dead in
            # this same session. A message is harmless to a live agent and resumes a dead one.
            if idle is None or idle >= probe_min:
                out.append({**base, "minutes": minutes, "limit": limit, "idle": idle,
                            "reason": f"no file activity for {probe_min}+ min", "action": "probe"})
            continue
        if minutes > limit * hard_factor:
            reason, action = "past hard cap", "kill"
        elif idle is None or idle >= idle_min:
            reason, action = "overdue and idle", "kill"
        else:
            reason, action = "overdue but active", "keep"
        out.append({**base, "minutes": minutes, "limit": limit, "idle": idle, "reason": reason,
                    "action": action})
    if "--json" in sys.argv:
        print(json.dumps(out, indent=1))
    elif not out:
        print("none overdue")
    else:
        for o in out:
            print(f"{o['id']}\t{o['agent']}\t{o['stage']}\t{o['minutes']} min (limit {o['limit']}, "
                  f"idle {o['idle']})\t{o['reason']}\t{o['action']}")


if __name__ == "__main__":
    main()
