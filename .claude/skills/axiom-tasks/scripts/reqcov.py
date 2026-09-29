#!/usr/bin/env python3
"""reqcov — requirement coverage / traceability checker for the Axiom harness.

Sources of truth
    spec/requirements/CATALOG.md   one table row per requirement:
        | REQ-OWN-012 | ownership | v1-core | statement | 0160 §12, tasks/0394 | T046 |
      columns: id | area | tier | statement | sources | status
      tier   : v1-core (needed for self-hosting) | v1-full (needed for Axiom v1.0) | post-v1
      status : one or more task ids "T046, T051"   → planned/implemented by those tasks
               EPIC(E15.3)                          → planned in a roadmap epic (spec/ROADMAP.md),
                                                      converted to task ids by the phase planning task
               DEFERRED(<reason>)                   → consciously postponed (post-v1 only)
               REJECTED(ADR-NNNN)                   → dropped by an architecture decision
               DUPLICATE(REQ-...)                   → merged into another requirement
               GAP                                  → not yet planned (must be zero after T111)
    _workspaces/tasks/**.md front-matter `covers: [REQ-..., ...]`

Usage
    python .claude/skills/axiom-tasks/scripts/reqcov.py            # summary + problems
    python .claude/skills/axiom-tasks/scripts/reqcov.py --gaps     # list GAP requirements
    python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P6-ownership
                                    # requirements whose tasks are in that phase, and their state
    python .claude/skills/axiom-tasks/scripts/reqcov.py --strict   # exit 1 on any problem
"""
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(__file__))
import taskctl  # noqa: E402

ROOT = os.getcwd()
CATALOG = os.path.join(ROOT, "spec", "requirements", "CATALOG.md")
ROW = re.compile(r"^\|\s*(REQ-[A-Z0-9]+-\d+[a-z]?)\s*\|(.*)\|\s*$")
TIERS = {"v1-core", "v1-full", "post-v1"}


def load_catalog():
    reqs = {}
    if not os.path.exists(CATALOG):
        return reqs
    with open(CATALOG, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            m = ROW.match(line.rstrip("\n"))
            if not m:
                continue
            cols = [c.strip() for c in m.group(2).split("|")]
            if len(cols) < 5:
                reqs[m.group(1)] = {"line": n, "bad": "expected 6 columns"}
                continue
            area, tier, stmt, sources, status = cols[0], cols[1], cols[2], cols[3], cols[-1]
            reqs[m.group(1)] = {"line": n, "area": area, "tier": tier, "stmt": stmt,
                                "sources": sources, "status": status}
    return reqs


def main(argv):
    reqs = load_catalog()
    tasks = taskctl.load_all()
    problems = []
    if not reqs:
        print(f"no catalog at {os.path.relpath(CATALOG, ROOT)} (created by tasks T092-T111)")
        return 0

    covered_by = {}
    for tid, t in tasks.items():
        for r in t["meta"].get("covers", []):
            covered_by.setdefault(r, []).append(tid)
            if r not in reqs:
                problems.append(f"{tid}: covers unknown requirement {r}")

    counts = {}
    gaps = []
    for rid, r in sorted(reqs.items()):
        if "bad" in r:
            problems.append(f"CATALOG.md:{r['line']}: {rid}: {r['bad']}")
            continue
        if r["tier"] not in TIERS:
            problems.append(f"CATALOG.md:{r['line']}: {rid}: unknown tier '{r['tier']}'")
        st = r["status"]
        kind = "planned"
        if st == "GAP" or not st:
            kind = "gap"
            gaps.append(rid)
        elif st.startswith("EPIC("):
            kind = "epic"
            ep = re.search(r"E\d+\.\d+", st)
            rm_path = os.path.join(ROOT, "spec", "ROADMAP.md")
            roadmap = open(rm_path, encoding="utf-8").read() if os.path.exists(rm_path) else ""
            if not ep or f"**{ep.group(0)} " not in roadmap:
                problems.append(f"{rid}: EPIC status names an epic not in spec/ROADMAP.md")
        elif st.startswith("DEFERRED"):
            kind = "deferred"
            if r["tier"] != "post-v1":
                problems.append(f"{rid}: DEFERRED but tier {r['tier']} (only post-v1 may be deferred)")
        elif st.startswith("REJECTED"):
            kind = "rejected"
        elif st.startswith("DUPLICATE"):
            kind = "duplicate"
            target = re.search(r"REQ-[A-Z0-9]+-\d+[a-z]?", st)
            if not target or target.group(0) not in reqs:
                problems.append(f"{rid}: DUPLICATE of unknown requirement")
        else:
            ids = re.findall(r"T\d{3,4}[a-z]?", st)
            if not ids:
                problems.append(f"{rid}: unparseable status '{st}'")
            for tid in ids:
                if tid not in tasks:
                    problems.append(f"{rid}: status names unknown task {tid}")
                elif rid not in tasks[tid]["meta"].get("covers", []):
                    problems.append(f"{rid}: task {tid} does not list it in covers:")
            if ids and all(tid in tasks and tasks[tid]["dir"] == "done" for tid in ids):
                kind = "implemented"
        counts.setdefault(r.get("tier", "?"), {}).setdefault(kind, 0)
        counts[r.get("tier", "?")][kind] += 1

    if "--phase" in argv:
        ph = argv[argv.index("--phase") + 1]
        for rid, r in sorted(reqs.items()):
            ids = re.findall(r"T\d{3,4}[a-z]?", r.get("status", ""))
            hit = [i for i in ids if i in tasks and tasks[i]["meta"].get("phase") == ph]
            if hit:
                state = ",".join(f"{i}:{tasks[i]['dir']}" for i in ids if i in tasks)
                print(f"{rid:16} {state:30} {r['stmt'][:80]}")
        return 0

    print(f"requirements: {len(reqs)}")
    for tier in ("v1-core", "v1-full", "post-v1"):
        c = counts.get(tier, {})
        print(f"  {tier:8} " + "  ".join(f"{k}={v}" for k, v in sorted(c.items())))
    if "--gaps" in argv:
        for g in gaps:
            print("GAP", g, reqs[g]["stmt"][:100])
    else:
        print(f"gaps: {len(gaps)}")
    for p in problems[:200]:
        print("PROBLEM", p)
    if len(problems) > 200:
        print(f"... {len(problems) - 200} more problems")
    ok = not problems and not gaps
    print("COVERAGE OK" if ok else f"COVERAGE INCOMPLETE ({len(gaps)} gaps, {len(problems)} problems)")
    return 1 if ("--strict" in argv and not ok) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
