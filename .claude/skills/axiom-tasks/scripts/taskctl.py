#!/usr/bin/env python3
"""taskctl — task board for the Axiom compiler harness.

Board layout (relative to repo root):
    _workspaces/tasks/todo/   tasks not started (status: todo | blocked)
    _workspaces/tasks/doing/  tasks in progress (status: doing)
    _workspaces/tasks/done/   tasks accepted by QA (status: done)

Each task is one markdown file `<ID>-<slug>.md` with a simple front-matter block:
    ---
    id: T010
    title: Lexer
    owner: axiom-frontend
    depends: [T007, T009]
    priority: 10
    status: todo
    attempts: 0
    paths: [bootstrap/axiom0/src/lexer, tests/lex]
    ---

Commands:
    status                     board summary (add --json for machine output)
    list [todo|doing|done|blocked]
    next [--max N]             ready tasks: deps done, not blocked, paths disjoint from doing
                               and from each other (safe to run in parallel)
    show ID                    print the task file
    start ID [--agent NAME]    todo -> doing
    finish ID                  doing -> done
    block ID --reason TEXT     doing|todo -> todo with status blocked
    unblock ID                 blocked -> todo
    requeue ID --reason TEXT   doing -> todo (e.g. stale after session restart), keeps attempts
    note ID TEXT               append a line to the task's "## Log" section
    validate                   check ids unique, deps exist, no cycles
    commit ID                  git-commit the task: files listed in the report's
                               "## Files changed" section + the task files
"""
import datetime as _dt
import json
import os
import re
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.getcwd()
BOARD = os.path.join(ROOT, "_workspaces", "tasks")
STATES = ["todo", "doing", "done"]
REPORTS = os.path.join(ROOT, "_workspaces", "reports")
TRAILER = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


def now():
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- parsing

def parse(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"bad front-matter: {path}")
    meta = {}
    for line in m.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            v = [x.strip() for x in inner.split(",") if x.strip()] if inner else []
        meta[k.strip()] = v
    return meta, m.group(2)


def dump(meta, body):
    out = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            out.append(f"{k}: [{', '.join(v)}]")
        else:
            out.append(f"{k}: {v}")
    out.append("---")
    return "\n".join(out) + "\n" + body


def load_all():
    tasks = {}
    for st in STATES:
        d = os.path.join(BOARD, st)
        os.makedirs(d, exist_ok=True)
        for f in sorted(os.listdir(d)):
            if not f.endswith(".md"):
                continue
            p = os.path.join(d, f)
            meta, body = parse(p)
            meta.setdefault("status", st)
            tasks[meta["id"]] = {"meta": meta, "body": body, "path": p, "dir": st}
    return tasks


def save(t):
    with open(t["path"], "w", encoding="utf-8") as fh:
        fh.write(dump(t["meta"], t["body"]))


def move(t, dest):
    newp = os.path.join(BOARD, dest, os.path.basename(t["path"]))
    save(t)
    os.replace(t["path"], newp)
    t["path"], t["dir"] = newp, dest


def log(t, text):
    line = f"- {now()} {text}\n"
    if "## Log" in t["body"]:
        t["body"] = t["body"].rstrip("\n") + "\n" + line
    else:
        t["body"] = t["body"].rstrip("\n") + "\n\n## Log\n" + line


def get(tasks, tid):
    tid = tid.upper()
    if tid not in tasks:
        raise SystemExit(f"unknown task {tid}")
    return tasks[tid]


# ---------------------------------------------------------------- logic

def overlaps(a, b):
    for x in a:
        for y in b:
            x2, y2 = x.rstrip("/") + "/", y.rstrip("/") + "/"
            if x2.startswith(y2) or y2.startswith(x2):
                return True
    return False


def ready(tasks, maxn):
    done = {i for i, t in tasks.items() if t["dir"] == "done"}
    busy_paths, any_doing = [], False
    for t in tasks.values():
        if t["dir"] == "doing":
            any_doing = True
            busy_paths += t["meta"].get("paths", [])
    cands = []
    for i, t in tasks.items():
        m = t["meta"]
        if t["dir"] != "todo" or m.get("status") == "blocked":
            continue
        if all(d in done for d in m.get("depends", [])):
            cands.append(t)
    cands.sort(key=lambda t: (int(t["meta"].get("priority", 100)), t["meta"]["id"]))
    picked, used = [], list(busy_paths)
    for t in cands:
        critical = int(t["meta"].get("priority", 100)) < 10
        if critical:
            # Architecture-critical tasks run alone: only when nothing else runs or is picked.
            if not picked and not any_doing:
                return [t]
            continue
        p = t["meta"].get("paths", [])
        if p and overlaps(p, used):
            continue
        picked.append(t)
        used += p
        if len(picked) >= maxn:
            break
    return picked


def cmd_status(tasks, as_json):
    groups = {"todo": [], "blocked": [], "doing": [], "done": []}
    for i, t in sorted(tasks.items()):
        key = "blocked" if t["meta"].get("status") == "blocked" else t["dir"]
        groups[key].append(i)
    nxt = [t["meta"]["id"] for t in ready(tasks, 4)]
    if as_json:
        print(json.dumps({**{k: v for k, v in groups.items()}, "ready": nxt}, indent=1))
        return
    total = len(tasks)
    print(f"total {total} | done {len(groups['done'])} | doing {len(groups['doing'])} | "
          f"todo {len(groups['todo'])} | blocked {len(groups['blocked'])}")
    for k in ("doing", "blocked"):
        for i in groups[k]:
            m = tasks[i]["meta"]
            print(f"  [{k}] {i} {m.get('title')} ({m.get('owner')}) {m.get('agent', '')}")
    print("ready:", ", ".join(nxt) if nxt else "(none)")


def cmd_validate(tasks):
    ok = True
    for i, t in tasks.items():
        for d in t["meta"].get("depends", []):
            if d not in tasks:
                print(f"{i}: unknown dependency {d}")
                ok = False
    state = {}

    def visit(n, stack):
        nonlocal ok
        if state.get(n) == 1:
            print("cycle:", " -> ".join(stack + [n]))
            ok = False
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for d in tasks[n]["meta"].get("depends", []):
            if d in tasks:
                visit(d, stack + [n])
        state[n] = 2

    for n in tasks:
        visit(n, [])
    print("OK" if ok else "INVALID", f"({len(tasks)} tasks)")
    return ok


def report_files(tid):
    path = os.path.join(REPORTS, f"{tid}-report.md")
    if not os.path.exists(path):
        return None
    files, on = [], False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("## "):
                on = line.strip().lower().startswith("## files changed")
                continue
            if on:
                m = re.match(r"^\s*[-*]\s+`?([^`\s]+)`?", line)
                if m:
                    files.append(m.group(1))
    return files + [os.path.relpath(path, ROOT)]


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, check=check, capture_output=True, text=True)


def cmd_commit(tasks, tid):
    t = get(tasks, tid)
    m = t["meta"]
    files = report_files(m["id"])
    board = os.path.relpath(os.path.join(ROOT, "_workspaces", "tasks"), ROOT)
    others_doing = [i for i, x in tasks.items() if x["dir"] == "doing" and i != m["id"]]
    if files:
        existing = [f for f in files if os.path.exists(os.path.join(ROOT, f))]
        deleted = [f for f in files if not os.path.exists(os.path.join(ROOT, f))]
        if existing:
            git("add", "--", *existing)
        for f in deleted:
            git("rm", "--cached", "--quiet", "--ignore-unmatch", "--", f, check=False)
    elif not others_doing:
        # No parallel work in flight: everything outside the user's docs belongs to this task.
        git("add", "-A", "--", ".", ":(exclude)docs/base")
    else:
        raise SystemExit(f"{m['id']}: no '## Files changed' in report and other tasks are in "
                         f"progress ({', '.join(others_doing)}); refusing to guess which files to commit")
    git("add", "-A", "--", board)
    staged = git("diff", "--cached", "--name-only").stdout.strip()
    if not staged:
        print("nothing to commit")
        return
    msg = f"{m['id']}: {m.get('title', '')}\n\nTask {m['id']} ({m.get('owner', '')}) accepted by QA.\n\n{TRAILER}\n"
    r = subprocess.run(["git", "commit", "-q", "-F", "-"], cwd=ROOT, input=msg,
                       text=True, capture_output=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        raise SystemExit("git commit failed")
    print(git("log", "--oneline", "-1").stdout.strip())


def main(argv):
    if not argv:
        print(__doc__)
        return
    cmd, rest = argv[0], argv[1:]
    tasks = load_all()

    def opt(name, default=None):
        if name in rest:
            i = rest.index(name)
            v = rest[i + 1]
            del rest[i:i + 2]
            return v
        return default

    if cmd == "status":
        cmd_status(tasks, "--json" in rest)
    elif cmd == "list":
        which = rest[0] if rest else None
        for i, t in sorted(tasks.items()):
            key = "blocked" if t["meta"].get("status") == "blocked" else t["dir"]
            if which in (None, key):
                m = t["meta"]
                print(f"{i:6} {key:8} {m.get('owner', ''):18} {m.get('title', '')}  deps={','.join(m.get('depends', []))}")
    elif cmd == "next":
        n = int(opt("--max", "1"))
        for t in ready(tasks, n):
            m = t["meta"]
            print(f"{m['id']}\t{m.get('owner')}\t{m.get('title')}\t{os.path.relpath(t['path'], ROOT)}")
    elif cmd == "show":
        print(open(get(tasks, rest[0])["path"], encoding="utf-8").read())
    elif cmd == "start":
        t = get(tasks, rest[0])
        agent = opt("--agent", "")
        if t["dir"] != "todo" or t["meta"].get("status") == "blocked":
            raise SystemExit(f"{t['meta']['id']} is not a startable todo task")
        t["meta"]["status"] = "doing"
        t["meta"]["attempts"] = str(int(t["meta"].get("attempts", 0)) + 1)
        t["meta"]["started"] = now()
        if agent:
            t["meta"]["agent"] = agent
        log(t, f"started (attempt {t['meta']['attempts']}) {agent}")
        move(t, "doing")
        print("doing:", os.path.relpath(t["path"], ROOT))
    elif cmd == "finish":
        t = get(tasks, rest[0])
        if t["dir"] != "doing":
            raise SystemExit(f"{t['meta']['id']} is not in doing")
        t["meta"]["status"] = "done"
        t["meta"]["finished"] = now()
        t["meta"].pop("agent", None)
        log(t, "accepted by QA -> done")
        move(t, "done")
        print("done:", os.path.relpath(t["path"], ROOT))
    elif cmd in ("block", "requeue"):
        t = get(tasks, rest[0])
        reason = opt("--reason", "") or " ".join(rest[1:])
        t["meta"]["status"] = "blocked" if cmd == "block" else "todo"
        t["meta"].pop("agent", None)
        log(t, f"{cmd}: {reason}")
        move(t, "todo")
        print(f"{cmd}ed:", os.path.relpath(t["path"], ROOT))
    elif cmd == "unblock":
        t = get(tasks, rest[0])
        t["meta"]["status"] = "todo"
        log(t, "unblocked " + " ".join(rest[1:]))
        save(t)
        print("unblocked", t["meta"]["id"])
    elif cmd == "note":
        t = get(tasks, rest[0])
        log(t, " ".join(rest[1:]))
        save(t)
    elif cmd == "validate":
        sys.exit(0 if cmd_validate(tasks) else 1)
    elif cmd == "commit":
        cmd_commit(tasks, rest[0])
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
