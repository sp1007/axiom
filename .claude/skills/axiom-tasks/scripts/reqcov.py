#!/usr/bin/env python3
"""reqcov — requirement coverage / traceability checker for the Axiom harness.

Sources of truth (repo root found like taskctl, never from the cwd alone)
    spec/requirements/CATALOG.md   one table row per requirement:
        | REQ-OWN-012 | ownership | v1-core | statement | 0160 §12, tasks/0394 | T046 |
        | REQ-STD-001 | std | v1-core | Vec<T> | tasks/0412 | REQ-TYP-001 | T070 |
      columns: id | area | tier | statement | sources | [needs] | status   (status is always last)
      tier   : v1-core (needed for self-hosting) | v1-full (needed for Axiom v1.0) | post-v1
      needs  : optional, requirement ids this one is built on ("REQ-TYP-001, REQ-MEM-004" or "-")
      status : one or more task ids "T046, T051"   → planned/implemented by those tasks
               EPIC(E15.3)                          → planned in a roadmap epic (spec/ROADMAP.md),
                                                      converted to task ids by the phase planning task
               DEFERRED(<reason>)                   → consciously postponed (post-v1 only)
               REJECTED(ADR-NNNN)                   → dropped by an architecture decision
               DUPLICATE(REQ-...)                   → merged into another requirement
               GAP                                  → not yet planned (must be zero after T111)
    _workspaces/tasks/**.md front-matter `covers: [REQ-..., ...]` and optional `needs: [REQ-...]`

Timing rules ("planned, but too late"):
    - a v1-core requirement must be delivered before self-host: every task in its status has phase
      P0-P10, and EPIC(E<n>.x) with n > 10 is a PROBLEM (move it into a core task or re-tier it with
      a reason);
    - a post-v1 requirement mapped to a P0-P10 task is reported as REVIEW (possible over-scope);
    - needs: for a catalogue row A with needs B, every task implementing B must be done or an
      ancestor (transitive dependency) of every task implementing A; same for a task's `needs:`.
    - a status naming a superseded task is a PROBLEM (remap it to the replacement).

Usage
    python .claude/skills/axiom-tasks/scripts/reqcov.py            # summary + problems
    python .claude/skills/axiom-tasks/scripts/reqcov.py --gaps     # list GAP requirements
    python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P6-ownership
                                    # requirements whose tasks are in that phase, and their state
    python .claude/skills/axiom-tasks/scripts/reqcov.py --strict   # exit 1 on any problem, and when
                                    # the catalogue is missing or empty
    python .claude/skills/axiom-tasks/scripts/reqcov.py --strict --allow-missing
                                    # gates that may run before T110 created the catalogue
"""
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import taskctl  # noqa: E402

ROOT = taskctl.ROOT
CATALOG = os.path.join(ROOT, "spec", "requirements", "CATALOG.md")
ROW = re.compile(r"^\|\s*(REQ-[A-Z0-9]+-\d+[a-z]?)\s*\|(.*)\|\s*$")
REQ = re.compile(r"REQ-[A-Z0-9]+-\d+[a-z]?")
TIERS = {"v1-core", "v1-full", "post-v1"}
CORE_MAX_PHASE = 10


def load_catalog():
    reqs = {}
    if not os.path.exists(CATALOG):
        return None
    with open(CATALOG, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            m = ROW.match(line.rstrip("\n"))
            if not m:
                continue
            cols = [c.strip() for c in m.group(2).split("|")]
            if len(cols) < 5:
                reqs[m.group(1)] = {"line": n, "bad": "expected 6 or 7 columns"}
                continue
            area, tier, stmt, sources, status = cols[0], cols[1], cols[2], cols[3], cols[-1]
            needs = REQ.findall(cols[4]) if len(cols) >= 6 else []
            reqs[m.group(1)] = {"line": n, "area": area, "tier": tier, "stmt": stmt,
                                "sources": sources, "status": status, "needs": needs}
    return reqs


def phase_num(t):
    m = re.match(r"P(\d+)", t["meta"].get("phase", ""))
    return int(m.group(1)) if m else -1


def main(argv):
    reqs = load_catalog()
    tasks = taskctl.load_all()
    problems, reviews = [], []
    if not reqs:
        what = "no catalog" if reqs is None else "empty catalog (no REQ rows)"
        print(f"{what} at {os.path.relpath(CATALOG, ROOT)} (created by tasks T092-T111)")
        if "--strict" in argv and "--allow-missing" not in argv:
            print("COVERAGE INCOMPLETE (catalogue missing; pass --allow-missing only before T110)")
            return 1
        return 0

    rm_path = os.path.join(ROOT, "spec", "ROADMAP.md")
    roadmap = open(rm_path, encoding="utf-8").read() if os.path.exists(rm_path) else ""
    covered_by = {}
    for tid, t in tasks.items():
        for r in t["meta"].get("covers", []):
            covered_by.setdefault(r, []).append(tid)
            if r not in reqs:
                problems.append(f"{tid}: covers unknown requirement {r}")

    impl = {}  # requirement -> implementing task ids (from the status column)
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
            ep = re.search(r"E(\d+)\.\d+", st)
            if not ep or f"**{ep.group(0)} " not in roadmap:
                problems.append(f"{rid}: EPIC status names an epic not in spec/ROADMAP.md")
            elif r["tier"] == "v1-core" and int(ep.group(1)) > CORE_MAX_PHASE:
                problems.append(f"{rid}: v1-core but planned in post-self-host epic {ep.group(0)} "
                                f"(too late: map it to a P0-P{CORE_MAX_PHASE} task or re-tier with a reason)")
        elif st.startswith("DEFERRED"):
            kind = "deferred"
            if r["tier"] != "post-v1":
                problems.append(f"{rid}: DEFERRED but tier {r['tier']} (only post-v1 may be deferred)")
        elif st.startswith("REJECTED"):
            kind = "rejected"
        elif st.startswith("DUPLICATE"):
            kind = "duplicate"
            target = REQ.search(st)
            if not target or target.group(0) not in reqs:
                problems.append(f"{rid}: DUPLICATE of unknown requirement")
        else:
            ids = re.findall(r"T\d{3,4}[a-z]?", st)
            if not ids:
                problems.append(f"{rid}: unparseable status '{st}'")
            impl[rid] = [i for i in ids if i in tasks]
            for tid in ids:
                if tid not in tasks:
                    problems.append(f"{rid}: status names unknown task {tid}")
                    continue
                t = tasks[tid]
                if t["meta"].get("superseded_by"):
                    problems.append(f"{rid}: status names {tid}, superseded by {t['meta']['superseded_by']}")
                if rid not in t["meta"].get("covers", []):
                    hint = " (task is done: add it with `taskctl covers`)" if t["dir"] != "todo" else ""
                    problems.append(f"{rid}: task {tid} does not list it in covers:{hint}")
                if r["tier"] == "v1-core" and phase_num(t) > CORE_MAX_PHASE:
                    problems.append(f"{rid}: v1-core but mapped to {tid} of phase {t['meta'].get('phase')} "
                                    "(after self-host: too late)")
                if r["tier"] == "post-v1" and 0 <= phase_num(t) <= CORE_MAX_PHASE:
                    reviews.append(f"{rid}: post-v1 requirement mapped to core task {tid} (over-scope?)")
            if ids and all(tid in tasks and tasks[tid]["dir"] == "done" for tid in ids):
                kind = "implemented"
        counts.setdefault(r.get("tier", "?"), {}).setdefault(kind, 0)
        counts[r.get("tier", "?")][kind] += 1

    # needs: ordering between requirements (catalogue column) and task-level needs:
    memo = {}

    def order_check(label, consumers, need):
        if need not in reqs:
            problems.append(f"{label}: needs unknown requirement {need}")
            return
        producers = impl.get(need)
        if producers is None:
            st = reqs[need].get("status", "")
            if not st.startswith(("DUPLICATE", "REJECTED")):
                problems.append(f"{label}: needs {need} which has no implementing task yet ({st or 'GAP'})")
            return
        for c in consumers:
            anc = taskctl.ancestors(tasks, c, memo)
            for p in producers:
                if p != c and p not in anc and tasks[p]["dir"] != "done":
                    problems.append(f"{label}: {c} needs {need} but its implementing task {p} is not a "
                                    f"(transitive) dependency of {c} — planned too late or unordered")

    for rid, r in sorted(reqs.items()):
        for need in r.get("needs", []):
            order_check(rid, impl.get(rid, []), need)
    for tid, t in sorted(tasks.items()):
        for need in t["meta"].get("needs", []):
            order_check(f"task {tid}", [tid], need)

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
    for rv in reviews[:50]:
        print("REVIEW", rv)
    ok = not problems and not gaps
    print("COVERAGE OK" if ok else f"COVERAGE INCOMPLETE ({len(gaps)} gaps, {len(problems)} problems)")
    return 1 if ("--strict" in argv and not ok) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
