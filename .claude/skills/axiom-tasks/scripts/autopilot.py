#!/usr/bin/env python3
"""autopilot — deterministic edits of _workspaces/autopilot.json (never hand-edit the JSON).

Repo root is found like taskctl (script location / git top level; AXIOM_ROOT overrides).

Commands:
    show                         print the state
    init --cron ID [--max N]     (re)write the base state: enabled, cron id/created, max_parallel,
                                 timeouts, session, board_total (from taskctl), counters reset
    session                      record the current session token (CLAUDE_CODE_SESSION_ID plus
                                 CLAUDE_PID, so a resumed session is a new one too); prints
                                 "new session" plus the running entries of the previous session
                                 (their agents died with it -> `taskctl recover ID` each) or
                                 "same session". Idempotent: safe on every tick.
    run ID --stage S --agent A [--round N] [--worktree P]
                                 record/replace running[ID] with since=now and this session
    drop ID                      remove running[ID]
    infra-fail [--reason TEXT]   an agent failed for infrastructure reasons (quota, rate limit,
                                 overloaded, API/tool error): backoff 30/60/120 min (cap 120)
    infra-ok                     a subagent completed normally: reset the infra backoff
    backoff                      exit 3 and print the remaining minutes while backing off, else 0
    check-board                  the only test for "board finished": exit 0 = finished (nothing in
                                 todo/doing/blocked/parked and at least one done task), 1 = work
                                 remains, 2 = the board is missing, empty or has FEWER tasks than
                                 the recorded board_total (never finished); records a grown total
    stuck                        count one more consecutive stuck tick, print the count
    unstuck                      reset the stuck counter
    set KEY VALUE                set a top-level scalar (enabled true/false, max_parallel 3, ...)
"""
import datetime as dt
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import taskctl  # noqa: E402

PATH = taskctl.AUTOPILOT
FMT = "%Y-%m-%d %H:%M"
BACKOFF = [30, 60, 120]


def now():
    return dt.datetime.now().strftime(FMT)


def load():
    try:
        return json.load(open(PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save(state):
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(state, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, PATH)


def current_session():
    return taskctl.session_token()


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], list(argv[1:])

    def opt(name, default=None):
        if name in rest:
            i = rest.index(name)
            v = rest[i + 1]
            del rest[i:i + 2]
            return v
        return default

    st = load()
    if cmd == "show":
        print(json.dumps(st, indent=1, ensure_ascii=False))
        return 0
    if cmd == "init":
        tasks = taskctl.load_all()
        st.update({"enabled": True, "cron_id": opt("--cron", st.get("cron_id")),
                   "cron_created": now(), "max_parallel": int(opt("--max", st.get("max_parallel", 3))),
                   "timeouts": st.get("timeouts", {"impl": 180, "fix": 180, "qa": 60, "unblock": 60}),
                   "timeouts_long": st.get("timeouts_long", {"impl": 300, "fix": 300}),
                   "idle_min": st.get("idle_min", 30), "hard_factor": st.get("hard_factor", 2),
                   "probe_min": st.get("probe_min", 45),
                   "board_total": len(tasks), "infra_failures": 0, "backoff_until": None,
                   "stuck_ticks": 0})
        st.setdefault("running", {})
        st["session_id"] = current_session() or st.get("session_id") or uuid.uuid4().hex
        st["session_started"] = now()
        save(st)
        print(f"autopilot.json initialised (board_total {len(tasks)})")
        return 0
    if cmd == "session":
        sid = current_session()
        if not sid:
            print("no session token (CLAUDE_CODE_SESSION_ID/CLAUDE_PID unset): only /tu-dong start marks "
                  "a new session; treat running entries with since < session_started as dead")
            return 0
        if st.get("session_id") == sid:
            print("same session")
            return 0
        old = sorted(i for i, r in st.get("running", {}).items() if r.get("session") != sid)
        st["session_id"], st["session_started"] = sid, now()
        save(st)
        print("new session" + (": dead running entries " + " ".join(old) if old else ""))
        return 0
    if cmd == "run":
        tid = rest[0] if rest else None
        stage, agent = opt("--stage"), opt("--agent")
        if not tid or not stage or not agent:
            print("usage: autopilot.py run ID --stage impl|qa|fix|unblock --agent NAME [--round N]")
            return 2
        entry = {"agent": agent, "stage": stage, "round": int(opt("--round", 0)), "since": now(),
                 "session": current_session() or st.get("session_id")}
        wt = opt("--worktree")
        if wt:
            entry["worktree"] = wt
        st.setdefault("running", {})[tid] = entry
        save(st)
        print(f"running {tid}: {entry}")
        return 0
    if cmd == "drop":
        if not rest:
            print("usage: autopilot.py drop ID")
            return 2
        st.get("running", {}).pop(rest[0], None)
        save(st)
        print(f"dropped {rest[0]}")
        return 0
    if cmd == "check-board":
        tasks = taskctl.load_all()  # exits 2 on a missing/empty/damaged board
        groups = taskctl.groups_of(tasks)
        known = int(st.get("board_total") or 0)
        if len(tasks) < known:
            print(f"ERROR board has {len(tasks)} tasks but {known} were recorded: tasks vanished "
                  "(wrong root, deleted or unparsable files). Not finished; run taskctl validate.")
            return 2
        if len(tasks) != known:
            st["board_total"] = len(tasks)
            save(st)
        open_ = [k for k in ("todo", "doing", "blocked", "parked") if groups[k]]
        if not open_ and groups["done"]:
            print(f"finished: {len(groups['done'])} done, {len(groups['deferred'])} deferred")
            return 0
        print(f"open: total {len(tasks)}, " + ", ".join(f"{k} {len(groups[k])}" for k in
                                                         ("done", "doing", "todo", "blocked", "parked")))
        return 1
    if cmd == "infra-fail":
        n = int(st.get("infra_failures", 0)) + 1
        mins = BACKOFF[min(n, len(BACKOFF)) - 1]
        until = dt.datetime.now() + dt.timedelta(minutes=mins)
        st["infra_failures"], st["backoff_until"] = n, until.strftime(FMT)
        st["infra_last"] = opt("--reason", "")
        save(st)
        print(f"infra failure {n}: no new agents until {st['backoff_until']} ({mins} min)")
        return 0
    if cmd == "infra-ok":
        if st.get("infra_failures") or st.get("backoff_until"):
            st["infra_failures"], st["backoff_until"] = 0, None
            save(st)
        print("infra ok")
        return 0
    if cmd == "backoff":
        until = st.get("backoff_until")
        if until:
            left = (dt.datetime.strptime(until, FMT) - dt.datetime.now()).total_seconds() / 60
            if left > 0:
                print(f"backoff until {until} ({int(left) + 1} min left): start no agents")
                return 3
        print("no backoff")
        return 0
    if cmd == "stuck":
        st["stuck_ticks"] = int(st.get("stuck_ticks", 0)) + 1
        save(st)
        print(st["stuck_ticks"])
        return 0
    if cmd == "unstuck":
        if st.get("stuck_ticks"):
            st["stuck_ticks"] = 0
            save(st)
        print(0)
        return 0
    if cmd == "set" and len(rest) == 2:
        k, v = rest
        try:
            v = json.loads(v)
        except ValueError:
            pass
        st[k] = v
        save(st)
        print(f"{k} = {v!r}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
