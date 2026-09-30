#!/usr/bin/env python3
"""overdue — find autopilot agents that have been running too long (probably hung).

Usage: python .claude/skills/axiom-tasks/scripts/overdue.py [--json]

Reads _workspaces/autopilot.json:
    "running": {"T010": {"agent": "T010-impl", "stage": "impl", "round": 0,
                         "since": "2026-09-30 14:05"}, ...}
    "timeouts": {"impl": 180, "fix": 180, "qa": 60, "unblock": 60}   (minutes, optional)

Prints one line per overdue entry: ID, agent, stage, minutes running, limit. Exit 0 always.
A hung agent still counts as "alive" for ListAgents, so only elapsed time can reveal it.
"""
import datetime as dt
import json
import os
import sys

DEFAULT = {"impl": 180, "fix": 180, "qa": 60, "unblock": 60}
PATH = os.path.join(os.getcwd(), "_workspaces", "autopilot.json")


def main():
    if not os.path.exists(PATH):
        print("no autopilot.json")
        return
    state = json.load(open(PATH, encoding="utf-8"))
    limits = {**DEFAULT, **state.get("timeouts", {})}
    now = dt.datetime.now()
    out = []
    for tid, r in sorted(state.get("running", {}).items()):
        since = r.get("since")
        if not since:
            out.append({"id": tid, "agent": r.get("agent"), "stage": r.get("stage"),
                        "minutes": None, "limit": None, "reason": "no 'since' recorded"})
            continue
        minutes = int((now - dt.datetime.strptime(since, "%Y-%m-%d %H:%M")).total_seconds() // 60)
        limit = limits.get(r.get("stage", "impl"), limits["impl"])
        if minutes > limit:
            out.append({"id": tid, "agent": r.get("agent"), "stage": r.get("stage"),
                        "minutes": minutes, "limit": limit, "reason": "overdue"})
    if "--json" in sys.argv:
        print(json.dumps(out, indent=1))
    elif not out:
        print("none overdue")
    else:
        for o in out:
            print(f"{o['id']}\t{o['agent']}\t{o['stage']}\t{o['minutes']} min (limit {o['limit']})\t{o['reason']}")


if __name__ == "__main__":
    main()
