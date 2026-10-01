#!/usr/bin/env python3
"""taskctl — task board for the Axiom compiler harness.

The repository root is found from this script's own location (…/.claude/skills/axiom-tasks/scripts),
then from `git rev-parse --show-toplevel`, never from the current directory alone; set AXIOM_ROOT to
override. A root without `_workspaces/tasks/todo`, or a board with 0 tasks, is an error (exit 2) —
never "board finished". Nothing is ever created outside the board.

Board layout (relative to repo root):
    _workspaces/tasks/todo/   tasks not started (status: todo | blocked | deferred | parked)
    _workspaces/tasks/doing/  tasks in progress (status: doing)
    _workspaces/tasks/done/   tasks accepted by QA and committed (status: done)

Each task is one markdown file `<ID>-<slug>.md` with a simple front-matter block (one `key: value`
per line, lists in `[a, b]`; a ` # comment` after a value is ignored; full-line `#` comments too):
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
Optional keys: locks (shared files, honoured like paths), needs (requirement ids consumed, see
reqcov), timeout_min (hang limit for impl/fix, see overdue.py), unblocks, unblock_failures,
superseded_by.

Commands (exit 0 ok, 1 refused/check failed, 2 usage or board error, 3 wait, 4 parked):
    status [--json]            board summary; --json adds total/finished for the tick
    list [todo|doing|done|blocked|deferred|parked]
    next [--max N]             ready tasks: deps done, not blocked, paths/locks disjoint from doing,
                               from an active unblock and from each other. A ready critical
                               (priority < 10) task is returned alone once doing/ is empty and no
                               unblock runs; until then nothing new starts (drain). N <= 0 -> none.
    show ID                    print the task file
    start ID [--agent NAME] [--force]  todo -> doing (refuses unfinished deps without --force)
    accept ID [--include-unlisted|--allow-unlisted]
                               the ONLY way to close a task: checks that the last VERDICT line of
                               <ID>-qa.md is PASS, checks the change set (see commit), moves the
                               task to done and commits code + reports + board in ONE commit; if
                               the commit fails the task goes back to doing
    finish ID                  doing -> done without committing (manual repair only; prefer accept)
    commit ID [--include-unlisted|--allow-unlisted] [--all]
                               commit a done task (repair path used by reconcile): files listed in
                               the "## Files changed" sections of <ID>-report.md and <ID>-qa.md
                               (bullets, numbered items, table rows; bold/backticks stripped), all
                               <ID>-*.md reports, and the board. Entries are literal paths (never
                               globs). Refuses (exit 1): no parsable entries; a directory entry
                               outside the task's paths; an entry inside another running task's
                               paths; changes under the task's own paths/locks that are not listed
                               (--include-unlisted stages them, --allow-unlisted leaves them).
                               Never docs/, never git-ignored paths. --all: no report, stage all.
    commit-report FILE --subject TEXT
                               commit the files listed under "## Files changed" of a non-task
                               report under _workspaces/ (architect unblock, phase review, audit
                               summary) plus that report and the board; same literal-path rules;
                               refuses entries that overlap a running task's paths
    changes ID                 print the change set commit/accept would stage (dry run)
    reconcile [--commit]       done tasks without a commit whose subject starts "<ID>:" (crash
                               between move and commit); --commit commits each
    recover ID [--stage S] [--round N]
                               restart recovery: prints the next action for a task in doing from
                               autopilot.json stage/round, the report's STATUS line and the QA
                               VERDICT (and their mtimes): accept | qa <round> | fix <round> |
                               block | requeue. Read-only; the caller performs the action.
    snapshot ID [--dir D] [--remove]
                               isolated build tree: git worktree of HEAD at build-snap-<ID> plus
                               exactly this task's change set (listed files + every changed file
                               under its paths). Run again to refresh in place (build dirs inside
                               are kept). QA gates build and test only there, so another task's
                               half-written files can never fail a gate.
    block ID --reason TEXT     doing|todo -> todo with status blocked
    requeue ID --reason TEXT [--infra|--no-attempt]
                               doing -> todo; after 3 charged attempts it blocks instead.
                               --infra (quota, rate limit, API/tool error) and --no-attempt
                               (session restart, stale entry) do not charge the attempt; a hung
                               agent that was killed is charged (3 hangs -> architect)
    unblock-begin ID           before spawning an architect unblock: exit 0 = go (takes the unblock
                               lock), 3 = wait (a critical task runs or waits, or another unblock
                               runs), 4 = parked (unblock cap reached)
    unblock-end ID [--failed]  release the unblock lock; --failed counts a failed unblock agent
                               (2 failures -> parked)
    unblock ID [--owner-approved]
                               blocked -> todo, attempts reset, unblocks += 1 (refused at the cap:
                               parks instead). deferred/parked need --owner-approved
    park ID --reason TEXT      todo/blocked -> parked (skipped by next and by the unblock step)
    supersede ID --by TNNN     todo/blocked/parked -> done as superseded (split/replaced)
    covers ID REQ...           add requirement ids to covers: (metadata only, any state)
    note ID TEXT               append a line to the task's "## Log" section
    validate                   ids unique and well-formed, file name = id, field types, status vs
                               directory, deps exist, done deps done, no cycles
    lint FILE...               parse + validate task files before they are put on the board
    stuck [--write]            diagnose "todo not empty, nothing ready, nothing running";
                               --write also writes _workspaces/STUCK.md; exit 3 when stuck
    adr-next SLUG              reserve the next ADR number atomically, create
                               spec/decisions/ADR-NNNN-SLUG.md (placeholder), print its path
    new-id --phase PNN         next free task id for a follow-up task of that phase
                               (P0-P10: T112-T199; P11-P24: the ROADMAP §4 block of 50)
"""
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.realpath(__file__))


def die(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _board_at(path):
    return bool(path) and os.path.isdir(os.path.join(path, "_workspaces", "tasks", "todo"))


def find_root():
    cands = []
    if os.environ.get("AXIOM_ROOT"):
        cands.append(os.environ["AXIOM_ROOT"])
    cands.append(os.path.normpath(os.path.join(HERE, "..", "..", "..", "..")))
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if r.returncode == 0:
            cands.append(r.stdout.strip())
    except OSError:
        pass
    for c in cands:
        if _board_at(c):
            return os.path.abspath(c)
    die("taskctl: cannot locate the repository root (no _workspaces/tasks/todo next to the script "
        "or at the git top level of the current directory); set AXIOM_ROOT. Refusing to guess.")


ROOT = find_root()
BOARD = os.path.join(ROOT, "_workspaces", "tasks")
STATES = ["todo", "doing", "done"]
STATUSES = {"todo", "doing", "done", "blocked", "deferred", "parked"}
DIR_STATUSES = {"todo": {"todo", "blocked", "deferred", "parked"}, "doing": {"doing"}, "done": {"done"}}
LIST_KEYS = ("depends", "paths", "spec", "covers", "needs", "locks")
INT_KEYS = ("priority", "attempts", "timeout_min", "unblocks", "unblock_failures")
NO_COMMENT_KEYS = ("title",)  # prose: a '#' there is text, not a comment
REPORTS = os.path.join(ROOT, "_workspaces", "reports")
LOCKS = os.path.join(ROOT, "_workspaces", "locks")
AUTOPILOT = os.path.join(ROOT, "_workspaces", "autopilot.json")
UNBLOCK_LOCK = os.path.join(LOCKS, "unblock.json")
UNBLOCK_LOCK_PATHS = ["spec", "_workspaces/tasks"]
UNBLOCK_LOCK_STALE_MIN = 180
DEFAULT_TRAILER = "Co-Authored-By: Claude <noreply@anthropic.com>"
MAX_ATTEMPTS = 3
MAX_UNBLOCKS = 2          # architect unblock cycles per task, then parked for the owner
MAX_UNBLOCK_FAILURES = 2  # crashed/overdue unblock agents per task, then parked
OWNER_DIRS = ("docs/",)   # the owner's documents: never staged by the harness
ID_RX = re.compile(r"^T\d{3,4}[a-z]?$")
MUTATING = {"start", "accept", "finish", "commit", "block", "requeue", "unblock", "unblock-begin",
            "unblock-end", "park", "supersede", "covers", "note", "reconcile", "snapshot", "adr-next",
            "commit-report"}


def now():
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def session_token():
    """Identity of the running Claude process: session id + claude.exe pid. A resumed session keeps
    its id but gets a new process, and background agents never survive the process."""
    sid, pid = os.environ.get("CLAUDE_CODE_SESSION_ID"), os.environ.get("CLAUDE_PID")
    if not sid and not pid:
        return None
    return f"{sid or '-'}:{pid or '-'}"


def is_linked_worktree():
    return os.path.isfile(os.path.join(ROOT, ".git"))


# ---------------------------------------------------------------- parsing

def relp(path):
    """Path relative to the repo root for messages; a path on another drive stays absolute."""
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return path


def strip_comment(v):
    return re.sub(r"\s+#.*$", "", v).strip()


def parse(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read().replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path}: bad front-matter (expected '---' lines around it)")
    meta = {}
    for line in m.group(1).splitlines():
        s = line.strip()
        if not s or s.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip() if k in NO_COMMENT_KEYS else strip_comment(v)
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            v = [x.strip() for x in inner.split(",") if x.strip()] if inner else []
        meta[k] = v
    return meta, m.group(2)


def check_meta(meta, path, state=None):
    """Type/shape errors of one task's front-matter (list of strings, empty when fine)."""
    errs, rel = [], relp(path) if os.path.isabs(path) else path
    tid = meta.get("id")
    if not isinstance(tid, str) or not ID_RX.match(tid):
        errs.append(f"{rel}: id {tid!r} is not of the form T123 / T123a")
    elif not os.path.basename(path).startswith(tid + "-"):
        errs.append(f"{rel}: file name must start with '{tid}-'")
    for k in LIST_KEYS:
        if k in meta and not isinstance(meta[k], list):
            errs.append(f"{rel}: '{k}' must be a list like [a, b] (got {meta[k]!r})")
    for k in INT_KEYS:
        if k in meta and not re.fullmatch(r"-?\d+", str(meta[k])):
            errs.append(f"{rel}: '{k}' must be an integer (got {meta[k]!r})")
    st = meta.get("status")
    if st is not None and st not in STATUSES:
        errs.append(f"{rel}: status {st!r} not in {sorted(STATUSES)}")
    if state and st is not None and st not in DIR_STATUSES[state]:
        errs.append(f"{rel}: status {st!r} does not belong in {state}/")
    for k in ("depends", "paths", "locks"):
        for x in meta.get(k, []) if isinstance(meta.get(k), list) else []:
            if " " in x or x.startswith("#"):
                errs.append(f"{rel}: suspicious {k} entry {x!r}")
    return errs


def ival(meta, key, default=0):
    try:
        return int(meta.get(key, default))
    except (TypeError, ValueError):
        return default


def dump(meta, body):
    out = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            out.append(f"{k}: [{', '.join(v)}]")
        else:
            out.append(f"{k}: {v}")
    out.append("---")
    return "\n".join(out) + "\n" + body


def load_all(errors=None, allow_empty=False):
    """Load the board. With errors=None any problem aborts (exit 2); otherwise problems are appended
    to the list and the loadable tasks are returned."""
    strict = errors is None
    errs = [] if strict else errors
    if not os.path.isdir(BOARD):
        die(f"taskctl: no board at {BOARD}")
    tasks = {}
    for st in STATES:
        d = os.path.join(BOARD, st)
        if not os.path.isdir(d):
            errs.append(f"missing board directory {os.path.relpath(d, ROOT)}")
            continue
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if os.path.isdir(p):
                errs.append(f"unexpected directory {os.path.relpath(p, ROOT)} in the board")
                continue
            if not f.endswith(".md"):
                continue
            try:
                meta, body = parse(p)
            except (ValueError, UnicodeDecodeError) as e:
                errs.append(str(e))
                continue
            e = check_meta(meta, p, st)
            if e:
                errs.extend(e)
                if not isinstance(meta.get("id"), str) or not ID_RX.match(meta.get("id", "")):
                    continue
                for k in LIST_KEYS:  # keep going with a sane shape so later checks do not explode
                    if k in meta and not isinstance(meta[k], list):
                        meta[k] = []
            meta.setdefault("status", st)
            tid = meta["id"]
            if tid in tasks:
                errs.append(f"duplicate id {tid}: {os.path.relpath(tasks[tid]['path'], ROOT)} and "
                            f"{os.path.relpath(p, ROOT)}")
                continue
            tasks[tid] = {"meta": meta, "body": body, "path": p, "dir": st}
    if not tasks and not allow_empty:
        errs.append(f"board at {os.path.relpath(BOARD, ROOT)} has 0 tasks — wrong root or damaged board; "
                    "never treat this as 'board finished'")
    if strict and errs:
        for e in errs:
            print("ERROR", e, file=sys.stderr)
        die(f"taskctl: {len(errs)} board error(s); fix the task files (see above)")
    return tasks


def save(t):
    with open(t["path"], "w", encoding="utf-8", newline="\n") as fh:
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
    for key in tasks:
        if key.lower() == tid.lower():
            return tasks[key]
    die(f"unknown task {tid}")


def key_of(t):
    st = t["meta"].get("status")
    return st if t["dir"] == "todo" and st in ("blocked", "deferred", "parked") else t["dir"]


# ---------------------------------------------------------------- scheduling

def _norm(p):
    return p.replace("\\", "/").strip().strip("/")


def under(path, prefix):
    a, b = _norm(path), _norm(prefix)
    return bool(b) and (a == b or a.startswith(b + "/"))


def overlaps(a, b):
    for x in a:
        for y in b:
            if under(x, y) or under(y, x):
                return True
    return False


def own_paths(t):
    return list(t["meta"].get("paths", [])) + list(t["meta"].get("locks", []))


def unblock_lock():
    """The active unblock lock (dict) or None; a lock older than the stale limit is ignored."""
    if not os.path.exists(UNBLOCK_LOCK):
        return None
    try:
        lock = json.load(open(UNBLOCK_LOCK, encoding="utf-8"))
        since = _dt.datetime.strptime(lock["since"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, KeyError, OSError):
        return {"id": "?", "since": "?", "paths": UNBLOCK_LOCK_PATHS}
    if (_dt.datetime.now() - since).total_seconds() > UNBLOCK_LOCK_STALE_MIN * 60:
        print(f"WARN stale unblock lock for {lock.get('id')} since {lock['since']} ignored "
              f"(run unblock-end {lock.get('id')})", file=sys.stderr)
        return None
    return lock


def candidates(tasks):
    done = {i for i, t in tasks.items() if t["dir"] == "done"}
    cands = [t for t in tasks.values() if key_of(t) == "todo"
             and all(d in done for d in t["meta"].get("depends", []))]
    cands.sort(key=lambda t: (ival(t["meta"], "priority", 100), t["meta"]["id"]))
    return cands


def ready(tasks, maxn):
    if maxn <= 0:
        return []
    busy_paths, any_doing = [], False
    for t in tasks.values():
        if t["dir"] == "doing":
            any_doing = True
            busy_paths += own_paths(t)
            if ival(t["meta"], "priority", 100) < 10:
                return []  # a critical task is running alone
    lock = unblock_lock()
    if lock:
        busy_paths += lock.get("paths", UNBLOCK_LOCK_PATHS)
    cands = candidates(tasks)
    if cands and ival(cands[0]["meta"], "priority", 100) < 10:
        # Architecture-critical tasks run alone. While one is ready, start nothing new so the
        # running tasks (and a running unblock) drain; otherwise refilling would starve it forever.
        return [] if (any_doing or lock) else [cands[0]]
    picked, used = [], list(busy_paths)
    for t in cands:
        p = own_paths(t)
        if p and overlaps(p, used):
            continue
        picked.append(t)
        used += p
        if len(picked) >= maxn:
            break
    return picked


def groups_of(tasks):
    groups = {"todo": [], "blocked": [], "deferred": [], "parked": [], "doing": [], "done": []}
    for i, t in sorted(tasks.items()):
        groups[key_of(t)].append(i)
    return groups


def cmd_status(tasks, as_json):
    groups = groups_of(tasks)
    nxt = [t["meta"]["id"] for t in ready(tasks, 4)]
    total = len(tasks)
    finished = (not groups["todo"] and not groups["doing"] and not groups["blocked"]
                and not groups["parked"] and len(groups["done"]) >= 1)
    lock = unblock_lock()
    if as_json:
        print(json.dumps({**groups, "ready": nxt, "total": total, "finished": finished,
                          "unblock_lock": lock["id"] if lock else None}, indent=1))
        return
    print(f"total {total} | done {len(groups['done'])} | doing {len(groups['doing'])} | "
          f"todo {len(groups['todo'])} | blocked {len(groups['blocked'])} | parked {len(groups['parked'])} | "
          f"deferred {len(groups['deferred'])}")
    for k in ("doing", "blocked", "parked"):
        for i in groups[k]:
            m = tasks[i]["meta"]
            print(f"  [{k}] {i} {m.get('title')} ({m.get('owner')}) {m.get('agent', '')}")
    if lock:
        print(f"  [unblock running] {lock.get('id')} since {lock.get('since')}")
    print("ready:", ", ".join(nxt) if nxt else "(none)")
    if finished:
        print("board finished (only deferred tasks remain)")


# ---------------------------------------------------------------- validation

def ancestors(tasks, tid, memo=None):
    memo = {} if memo is None else memo
    if tid in memo:
        return memo[tid]
    memo[tid] = set()
    acc = set()
    for d in tasks.get(tid, {"meta": {}})["meta"].get("depends", []):
        if d in tasks:
            acc.add(d)
            acc |= ancestors(tasks, d, memo)
    memo[tid] = acc
    return acc


def cmd_validate(tasks, errors):
    ok = not errors
    for e in errors:
        print("ERROR", e)
    for i, t in tasks.items():
        for d in t["meta"].get("depends", []):
            if d not in tasks:
                print(f"{i}: unknown dependency {d}")
                ok = False
            elif t["dir"] == "done" and tasks[d]["dir"] != "done":
                print(f"{i}: done but its dependency {d} is not done")
                ok = False
            elif key_of(t) in ("todo", "blocked") and key_of(tasks[d]) in ("deferred", "parked"):
                print(f"NOTE {i}: depends on {key_of(tasks[d])} task {d} — it cannot run until the owner "
                      f"schedules {d}")
        sb = t["meta"].get("superseded_by")
        if sb and sb not in tasks:
            print(f"{i}: superseded_by unknown task {sb}")
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


def cmd_lint(files, tasks):
    ok = True
    for f in files:
        try:
            meta, body = parse(f)
        except (ValueError, OSError, UnicodeDecodeError) as e:
            print("ERROR", e)
            ok = False
            continue
        errs = check_meta(meta, os.path.abspath(f))
        for k in ("id", "title", "phase", "owner", "priority", "status", "paths", "model", "gate_model"):
            if k not in meta:
                errs.append(f"{f}: missing '{k}'")
        tid = meta.get("id")
        if tid in tasks and os.path.abspath(tasks[tid]["path"]) != os.path.abspath(f):
            errs.append(f"{f}: id {tid} already used by {os.path.relpath(tasks[tid]['path'], ROOT)}")
        for d in meta.get("depends", []) if isinstance(meta.get("depends"), list) else []:
            if d not in tasks:
                errs.append(f"{f}: unknown dependency {d}")
        if "## Acceptance" not in body:
            errs.append(f"{f}: no '## Acceptance' section")
        for e in errs:
            print("ERROR", e)
        ok = ok and not errs
        if not errs:
            print("OK", f)
    return ok


# ---------------------------------------------------------------- git helpers

def git(*args, check=True, stdin=None):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, input=stdin,
                       encoding="utf-8")
    if check and r.returncode != 0:
        die(f"git {' '.join(args)} failed:\n{r.stdout}{r.stderr}", 1)
    return r


def git_lit(*args, check=True, stdin=None):
    """git with --literal-pathspecs: entries are never globs or :(magic)."""
    return git("--literal-pathspecs", *args, check=check, stdin=stdin)


def dirty_under(paths):
    """Modified, deleted or untracked (not ignored) files under the given paths."""
    paths = [_norm(p) for p in paths if _norm(p)]
    if not paths:
        return []
    r = git_lit("status", "--porcelain=v1", "-z", "-uall", "--", *paths)
    out, parts, i = [], r.stdout.split("\0"), 0
    while i < len(parts):
        e = parts[i]
        i += 1
        if len(e) < 4:
            continue
        xy, f = e[:2], e[3:]
        if xy[0] in "RC":
            i += 1  # skip the rename source
        out.append(f)
    return sorted(set(out))


def is_tracked(f):
    return git_lit("ls-files", "--error-unmatch", "--", f, check=False).returncode == 0


def is_ignored(f):
    return git("check-ignore", "-q", "--", f, check=False).returncode == 0


def trailer():
    return os.environ.get("AXIOM_COMMIT_TRAILER", DEFAULT_TRAILER)


# ---------------------------------------------------------------- reports / change set

def _extract_path(text):
    text = text.replace("**", "").replace("__", "").strip()
    m = re.match(r"^\[([^\]]+)\]\(([^)]*)\)", text)
    if m:
        text = m.group(1)
    m = re.search(r"`([^`]+)`", text)
    tok = m.group(1).strip() if m else (text.split()[0] if text.split() else "")
    tok = tok.replace("\\", "/").strip().rstrip(":,;").strip("*_")
    while tok.startswith("./"):
        tok = tok[2:]
    if tok.lower() in ("", "none", "(none)", "n/a", "-", "—"):
        return None
    return tok


def files_section(path):
    """(entries, ignored_lines) of every '## Files changed' section of a report."""
    files, ignored, on = [], [], False
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.lstrip().startswith("#"):
                on = bool(re.match(r"^\s*#{2,4}\s+files changed\b", line, re.I))
                continue
            if not on or not line.strip():
                continue
            s = line.strip()
            if s.startswith("```"):
                continue
            if s.startswith("|"):
                cells = [c.strip() for c in s.strip("|").split("|")]
                if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    continue
                if cells and cells[0].lower().strip("*") in ("file", "files", "path", "file path", "paths"):
                    continue
                tok = _extract_path(cells[0]) if cells else None
            else:
                m = re.match(r"^(?:[-*+]|\d+[.)])\s+(.*)$", s)
                if not m:
                    ignored.append(s)
                    continue
                tok = _extract_path(m.group(1))
            if tok:
                files.append(tok)
            else:
                ignored.append(s)
    return files, ignored


def report_paths(tid):
    if not os.path.isdir(REPORTS):
        return []
    return sorted(os.path.join(REPORTS, f) for f in os.listdir(REPORTS)
                  if f.startswith(tid + "-") and f.endswith(".md"))


def last_match(path, rx):
    if not path or not os.path.exists(path):
        return None
    hit = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(rx, line.strip())
            if m:
                hit = m
    return hit


VERDICT_RX = r"^\**VERDICT:\s*(PASS|FAIL)\b(?:.*?round\s*=\s*(\d+))?"


def last_verdict(tid):
    m = last_match(os.path.join(REPORTS, f"{tid}-qa.md"), VERDICT_RX)
    return m.group(1) if m else None


def last_verdict_round(tid):
    """Round named by the last VERDICT line ('VERDICT: FAIL round=1'), or None when it has none."""
    m = last_match(os.path.join(REPORTS, f"{tid}-qa.md"), VERDICT_RX)
    return int(m.group(2)) if m and m.group(2) is not None else None


def report_status(tid):
    m = last_match(os.path.join(REPORTS, f"{tid}-report.md"),
                   r"^\**STATUS:\s*(COMPLETE|BLOCKED)\b(?:.*?round\s*=\s*(\d+))?")
    return (m.group(1), int(m.group(2) or 0)) if m else (None, None)


def changeset(tasks, t, include_unlisted=False, allow_unlisted=False, snapshot=False):
    """Compute what to stage for task t. Returns (files, problems, notes)."""
    tid = t["meta"]["id"]
    own = own_paths(t)
    reports = [os.path.relpath(p, ROOT).replace("\\", "/") for p in report_paths(tid)]
    entries, notes, problems = [], [], []
    for rp in (f"_workspaces/reports/{tid}-report.md", f"_workspaces/reports/{tid}-qa.md"):
        full = os.path.join(ROOT, rp)
        if os.path.exists(full):
            e, ign = files_section(full)
            entries += e
            for s in ign:
                notes.append(f"ignored line in {os.path.basename(rp)} Files changed: {s[:100]}")
    others = {i: own_paths(x) for i, x in tasks.items() if x["dir"] == "doing" and i != tid}
    files = set(reports)
    listed_real = 0
    for e in dict.fromkeys(entries):
        if e.startswith(OWNER_DIRS) or e.startswith("/") or ".." in e.split("/") or re.match(r"^[A-Za-z]:", e):
            notes.append(f"skip (not stageable): {e}")
            continue
        if any(c in e for c in "*?[") and not os.path.exists(os.path.join(ROOT, e)):
            problems.append(f"entry '{e}' looks like a glob; list literal file paths")
            continue
        full = os.path.join(ROOT, e)
        owner_of = [i for i, p in others.items() if any(under(e, x) for x in p)]
        if owner_of and not snapshot:
            problems.append(f"entry '{e}' lies inside the paths of running task {', '.join(owner_of)}")
            continue
        if os.path.isdir(full):
            if not any(under(e, p) for p in own):
                problems.append(f"directory entry '{e}' is outside the task's paths/locks {own}; "
                                "list the files instead")
                continue
            got = dirty_under([e])
            files.update(got)
            listed_real += 1
            continue
        if os.path.exists(full):
            if is_ignored(e):
                notes.append(f"skip (git-ignored): {e}")
                continue
            files.add(e)
            listed_real += 1
        elif is_tracked(e):
            files.add(e)  # deletion
            listed_real += 1
        else:
            notes.append(f"listed but neither present nor tracked (ignored): {e}")
            continue
        if not any(under(e, p) for p in own) and e not in reports:
            notes.append(f"WARN {e} is outside the task's paths/locks — make sure it belongs to {tid}")
    unlisted = [f for f in dirty_under(own) if f not in files]
    if unlisted:
        if include_unlisted or snapshot:
            files.update(unlisted)
            notes.append(f"including {len(unlisted)} unlisted changed file(s) under the task's paths: "
                         + ", ".join(unlisted[:20]))
        elif allow_unlisted:
            notes.append(f"WARN leaving {len(unlisted)} unlisted changed file(s) under the task's paths "
                         "uncommitted: " + ", ".join(unlisted[:20]))
        else:
            problems.append(f"{len(unlisted)} changed file(s) under the task's own paths/locks are not in "
                            "any '## Files changed' list (work would be lost): " + ", ".join(unlisted[:20])
                            + " — add them to the report, or rerun with --include-unlisted "
                            "(stage them) / --allow-unlisted (leave them)")
    if not listed_real and not snapshot and not (include_unlisted and unlisted):
        problems.append(f"no parsable '## Files changed' entries in the reports of {tid} "
                        "(bullets '- path', numbered '1. path' or table rows)")
    return sorted(files), problems, notes


def stage(files):
    files = [f for f in files if os.path.exists(os.path.join(ROOT, f)) or is_tracked(f)]
    if files:
        git_lit("add", "-A", "--pathspec-from-file=-", "--pathspec-file-nul", stdin="\0".join(files) + "\0")
    git("add", "-A", "--", os.path.relpath(BOARD, ROOT).replace("\\", "/"))


def do_commit(t, files, subject_extra=""):
    m = t["meta"]
    msg = (f"{m['id']}: {m.get('title', '')}\n\nTask {m['id']} ({m.get('owner', '')}) accepted by QA."
           f"{subject_extra}\n\n{trailer()}\n")
    return commit_files(files, msg, m["id"])


def commit_files(files, msg, label):
    """Stage exactly `files` plus the board and commit. True = committed, None = nothing to commit,
    False = git commit failed (hooks are never bypassed)."""
    stage(files)
    staged = git("-c", "core.quotepath=false", "diff", "--cached", "--name-only").stdout.split("\n")
    staged = [s for s in staged if s.strip()]
    board = os.path.relpath(BOARD, ROOT).replace("\\", "/")
    bad = [s for s in staged if s.startswith(OWNER_DIRS)
           or (s not in files and not under(s, board))]
    for s in bad:
        print(f"WARN unstaging {s}: staged earlier but not part of {label}'s change set")
    if bad:
        git_lit("restore", "--staged", "--", *bad, check=False)
    if not [s for s in staged if s not in bad]:
        print("nothing to commit")
        return None
    r = subprocess.run(["git", "commit", "-q", "-F", "-"], cwd=ROOT, input=msg, text=True,
                       capture_output=True, encoding="utf-8")
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        return False
    print(git("log", "--oneline", "-1").stdout.strip())
    return True


def cmd_commit_report(tasks, report, subject):
    """Commit the files an architect/QA report lists (unblock, phase review, audit summary)."""
    full = report if os.path.isabs(report) else os.path.join(ROOT, report)
    if not os.path.isfile(full):
        die(f"commit-report: no such report {report}", 1)
    rel = os.path.relpath(full, ROOT).replace("\\", "/")
    if not under(rel, "_workspaces"):
        die("commit-report: the report must live under _workspaces/ (reports/ or audit/)", 1)
    if not subject or "\n" in subject:
        die('commit-report needs --subject "arch: <one line>"')
    entries, ignored = files_section(full)
    doing = {i: own_paths(x) for i, x in tasks.items() if x["dir"] == "doing"}
    files, problems = {rel}, []
    for s in ignored:
        print(f"ignored line in Files changed: {s[:100]}")
    for e in dict.fromkeys(entries):
        if e.startswith(OWNER_DIRS) or e.startswith("/") or ".." in e.split("/") or re.match(r"^[A-Za-z]:", e):
            print(f"skip (not stageable): {e}")
            continue
        if any(c in e for c in "*?[") and not os.path.exists(os.path.join(ROOT, e)):
            problems.append(f"entry '{e}' looks like a glob; list literal paths")
            continue
        hit = [i for i, p in doing.items() if any(under(e, x) or under(x, e) for x in p)]
        if hit:
            problems.append(f"entry '{e}' overlaps the paths of running task {', '.join(hit)}")
            continue
        if os.path.isdir(os.path.join(ROOT, e)):
            files.update(f for f in dirty_under([e]) if not f.startswith(OWNER_DIRS))
        elif os.path.exists(os.path.join(ROOT, e)):
            if is_ignored(e):
                print(f"skip (git-ignored): {e}")
            else:
                files.add(e)
        elif is_tracked(e):
            files.add(e)
        else:
            print(f"listed but neither present nor tracked (ignored): {e}")
    for p in problems:
        print("REFUSED", p)
    if problems:
        die(f"commit-report refused ({len(problems)} problem(s)); nothing staged", 1)
    r = commit_files(sorted(files), f"{subject}\n\nReport: {rel}\n\n{trailer()}\n", rel)
    if r is False:
        die("git commit failed", 1)


def print_plan(files, problems, notes):
    for n in notes:
        print(n)
    for p in problems:
        print("REFUSED", p)


def cmd_commit(tasks, tid, flags):
    t = get(tasks, tid)
    if "--all" in flags:
        others = [i for i, x in tasks.items() if x["dir"] == "doing" and i != t["meta"]["id"]]
        if others or unblock_lock():
            die(f"--all refused: other work in progress ({', '.join(others) or 'unblock'})", 1)
        files = dirty_under(["."])
        files = [f for f in files if not f.startswith(OWNER_DIRS)]
        problems, notes = [], ["--all: staging every change outside docs/"]
    else:
        files, problems, notes = changeset(tasks, t, "--include-unlisted" in flags, "--allow-unlisted" in flags)
    print_plan(files, problems, notes)
    if problems:
        die(f"{t['meta']['id']}: commit refused ({len(problems)} problem(s)); nothing staged", 1)
    r = do_commit(t, files)
    if r is False:
        die("git commit failed", 1)
    return r


def cmd_accept(tasks, tid, flags):
    t = get(tasks, tid)
    i = t["meta"]["id"]
    if t["dir"] == "done":
        die(f"{i} is already done; use `reconcile --commit` if its commit is missing", 1)
    if t["dir"] != "doing":
        die(f"{i} is not in doing", 1)
    v = last_verdict(i)
    if v != "PASS":
        die(f"{i}: last VERDICT line of _workspaces/reports/{i}-qa.md is {v or 'missing'}, not PASS", 1)
    st, rnd = report_status(i)
    files, problems, notes = changeset(tasks, t, "--include-unlisted" in flags, "--allow-unlisted" in flags)
    if st != "COMPLETE":
        notes.append(f"WARN {i}-report.md has no 'STATUS: COMPLETE' line")
    print_plan(files, problems, notes)
    if problems:
        die(f"{i}: accept refused ({len(problems)} problem(s)); task left in doing, nothing staged", 1)
    t["meta"]["status"] = "done"
    t["meta"]["finished"] = now()
    t["meta"].pop("agent", None)
    log(t, "accepted by QA -> done")
    move(t, "done")
    r = do_commit(t, files)
    if r is False:
        git("reset", "-q", check=False)
        t["meta"]["status"] = "doing"
        t["meta"].pop("finished", None)
        log(t, "accept rolled back: git commit failed")
        move(t, "doing")
        die(f"{i}: git commit failed; task moved back to doing (fix the cause, rerun accept)", 1)
    print("done:", os.path.relpath(t["path"], ROOT))


def committed_ids():
    subj = git("log", "--format=%s", check=False).stdout.splitlines()
    return {s.split(":", 1)[0].strip() for s in subj if ":" in s}


def cmd_reconcile(tasks, do_commit_flag):
    have = committed_ids()
    missing = [i for i, t in sorted(tasks.items()) if t["dir"] == "done" and i not in have
               and not t["meta"].get("superseded_by") and "reconciled:" not in t["body"]]
    if not missing:
        print("reconcile: every done task has its commit")
        return True
    for i in missing:
        print(f"UNCOMMITTED {i} (in done/, no commit subject '{i}: ...')")
    if not do_commit_flag:
        return False
    ok = True
    for i in missing:
        t = tasks[i]
        files, problems, notes = changeset(tasks, t, include_unlisted=True)
        print_plan(files, problems, notes)
        if problems:
            ok = False
            print(f"{i}: reconcile refused; fix the report and rerun")
            continue
        r = do_commit(t, files, "\n(reconciled after an interrupted accept)")
        if r is None:
            log(t, "reconciled: nothing to commit (already in history under another subject)")
            save(t)
            git("add", "-A", "--", os.path.relpath(t["path"], ROOT).replace("\\", "/"))
            do_commit(t, [], "\n(reconcile marker)")
        elif r is False:
            ok = False
    return ok


# ---------------------------------------------------------------- recovery / snapshot

def autopilot_state():
    try:
        return json.load(open(AUTOPILOT, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def cmd_recover(tasks, tid, stage_arg, round_arg):
    t = get(tasks, tid)
    i = t["meta"]["id"]
    if t["dir"] != "doing":
        die(f"{i} is not in doing (recover is for interrupted running tasks)", 1)
    run = autopilot_state().get("running", {}).get(i, {})
    rep = os.path.join(REPORTS, f"{i}-report.md")
    qa = os.path.join(REPORTS, f"{i}-qa.md")
    rep_m = os.path.getmtime(rep) if os.path.exists(rep) else None
    qa_m = os.path.getmtime(qa) if os.path.exists(qa) else None
    verdict, vround = last_verdict(i), last_verdict_round(i)
    st, rep_round = report_status(i)
    rep_round = rep_round or 0
    qa_newer = bool(verdict) and (rep_m is None or qa_m >= rep_m)
    try:  # a report older than this attempt's start belongs to an earlier attempt
        started = _dt.datetime.strptime(t["meta"].get("started", ""), "%Y-%m-%d %H:%M:%S").timestamp()
    except ValueError:
        started = 0
    fresh = rep_m is not None and rep_m >= started - 1
    if stage_arg or run.get("stage"):
        stage = stage_arg or run["stage"]
        rnd = int(round_arg if round_arg is not None else run.get("round", 0) or 0)
    else:  # no autopilot record (manual run): infer from the files
        stage = "qa" if qa_newer else "impl"
        rnd = int(round_arg) if round_arg is not None else max(rep_round, vround or 0)
    # a verdict tagged with an older round is a leftover of the previous gate, not this gate's result
    current = qa_newer and (vround is None or vround >= rnd)

    def after_fail():
        if rnd >= 2:
            return "block", f"QA FAIL after fix round {rnd} (QA failed 3 times)"
        return f"fix {rnd + 1}", f"QA FAIL at round {rnd}"

    if stage == "fix":
        if st == "COMPLETE" and rep_round >= rnd and not qa_newer:
            action, why = "qa", f"fix report STATUS: COMPLETE round={rep_round} is newer than the last verdict"
        elif st == "BLOCKED" and not qa_newer:
            action, why = "block", "report STATUS: BLOCKED"
        else:
            action, why = f"fix {max(rnd, 1)}", "fix round interrupted before its report was complete (respawn the fix agent)"
    elif stage == "qa":
        if current and verdict == "PASS":
            action, why = "accept", "QA verdict PASS is newer than the report"
        elif current:
            action, why = after_fail()
        elif st == "COMPLETE":
            action, why = "qa", "gate interrupted before a verdict for this round (respawn the gate)"
        else:
            action, why = "requeue", "no complete report (requeue --no-attempt)"
    else:  # impl
        if qa_newer and verdict == "PASS" and fresh:
            action, why = "accept", "QA verdict PASS is newer than the report"
        elif st == "COMPLETE" and fresh and not qa_newer:
            action, why = "qa", f"report STATUS: COMPLETE round={rep_round}, no verdict for it yet"
        elif st == "BLOCKED" and fresh and not qa_newer:
            action, why = "block", "report STATUS: BLOCKED"
        else:
            action, why = "requeue", ("no complete report written by this attempt "
                                      "(requeue --no-attempt; the next agent continues from the files)")
    if action == "qa":  # the gate round is the round the report claims to have completed
        action = f"qa {max(rep_round, rnd if stage in ('fix', 'qa') else 0)}"
    print(f"{action}\t# {i} stage={stage} round={rnd}: {why}")
    return action


def cmd_snapshot(tasks, tid, d, remove):
    t = get(tasks, tid)
    i = t["meta"]["id"]
    d = os.path.abspath(d or os.path.join(ROOT, f"build-snap-{i}"))
    if under(ROOT, d) or os.path.normcase(d) == os.path.normcase(ROOT):
        die(f"snapshot: {d} is the repository itself", 1)

    def drop():
        git("worktree", "remove", "--force", d, check=False)
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
        git("worktree", "prune", check=False)

    if remove:
        drop()
        print("removed", d)
        return
    head = git("rev-parse", "HEAD").stdout.strip()
    refreshed = False
    if os.path.isfile(os.path.join(d, ".git")):
        # refresh in place: tracked files back to HEAD, earlier copies of new files removed; ignored
        # files (the build directory inside the snapshot) are kept, so the rebuild is incremental
        def wt(*args):
            return subprocess.run(["git", *args], cwd=d, capture_output=True, text=True, encoding="utf-8")
        refreshed = (wt("reset", "-q", "--hard").returncode == 0
                     and wt("clean", "-q", "-fd").returncode == 0
                     and wt("checkout", "-q", "--detach", head).returncode == 0)
    if not refreshed:
        if os.path.exists(d):
            drop()
        git("worktree", "prune", check=False)
        git("worktree", "add", "--detach", "-q", d, head)
    files, problems, notes = changeset(tasks, t, snapshot=True)
    copied = deleted = 0
    for f in files:
        src, dst = os.path.join(ROOT, f), os.path.join(d, f)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
        elif os.path.exists(dst):
            os.remove(dst)
            deleted += 1
    for n in notes:
        print(n)
    for p in problems:
        print("WARN", p)
    print(f"snapshot {d}  ({'refreshed' if refreshed else 'created'}: HEAD {head[:7]} + {copied} changed, "
          f"{deleted} deleted file(s) of {i})")


# ---------------------------------------------------------------- unblock / park

def cmd_unblock_begin(tasks, tid):
    t = get(tasks, tid)
    i, m = t["meta"]["id"], t["meta"]
    if key_of(t) != "blocked":
        die(f"{i} is not blocked (status {key_of(t)})")
    if ival(m, "unblocks") >= MAX_UNBLOCKS or ival(m, "unblock_failures") >= MAX_UNBLOCK_FAILURES:
        park(t, f"unblock cap reached (unblocks={ival(m, 'unblocks')}, failed unblock agents="
                f"{ival(m, 'unblock_failures')}); needs the owner")
        print(f"parked {i}")
        raise SystemExit(4)
    for x in tasks.values():
        if x["dir"] == "doing" and ival(x["meta"], "priority", 100) < 10:
            print(f"wait: critical task {x['meta']['id']} is running")
            raise SystemExit(3)
    c = candidates(tasks)
    if c and ival(c[0]["meta"], "priority", 100) < 10:
        print(f"wait: critical task {c[0]['meta']['id']} is waiting to run (drain)")
        raise SystemExit(3)
    lock = unblock_lock()
    if lock:
        print(f"wait: unblock of {lock.get('id')} is running (unblocks are serialised)")
        raise SystemExit(3)
    os.makedirs(LOCKS, exist_ok=True)
    if os.path.exists(UNBLOCK_LOCK):
        os.remove(UNBLOCK_LOCK)  # stale (unblock_lock() ignored it)
    try:
        fd = os.open(UNBLOCK_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print("wait: unblock lock taken concurrently")
        raise SystemExit(3)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"id": i, "since": now(), "paths": UNBLOCK_LOCK_PATHS}, fh)
    print(f"go: unblock lock taken for {i}")


def cmd_unblock_end(tasks, tid, failed):
    t = get(tasks, tid)
    i = t["meta"]["id"]
    lock = None
    if os.path.exists(UNBLOCK_LOCK):
        try:
            lock = json.load(open(UNBLOCK_LOCK, encoding="utf-8"))
        except (OSError, ValueError):
            lock = {"id": i}
        if lock.get("id") == i:
            os.remove(UNBLOCK_LOCK)
        else:
            print(f"WARN unblock lock belongs to {lock.get('id')}, left in place")
    if failed:
        n = ival(t["meta"], "unblock_failures") + 1
        t["meta"]["unblock_failures"] = str(n)
        log(t, f"architect unblock agent failed ({n}/{MAX_UNBLOCK_FAILURES})")
        if n >= MAX_UNBLOCK_FAILURES and key_of(t) == "blocked":
            park(t, f"{n} failed unblock agents; needs the owner")
            print(f"parked {i}")
            return
        save(t)
    print(f"unblock lock released for {i}")


def park(t, reason):
    t["meta"]["status"] = "parked"
    t["meta"].pop("agent", None)
    log(t, f"parked: {reason}")
    if t["dir"] != "todo":
        move(t, "todo")
    else:
        save(t)


# ---------------------------------------------------------------- misc commands

def cmd_stuck(tasks, write):
    groups = groups_of(tasks)
    unblockable = [i for i in groups["blocked"]
                   if ival(tasks[i]["meta"], "unblocks") < MAX_UNBLOCKS
                   and ival(tasks[i]["meta"], "unblock_failures") < MAX_UNBLOCK_FAILURES]
    if (groups["doing"] or unblock_lock() or unblockable or ready(tasks, 1)
            or not (groups["todo"] or groups["blocked"] or groups["parked"])):
        print("not stuck" + (f" (blocked tasks awaiting an architect unblock: {', '.join(unblockable)})"
                             if unblockable else ""))
        return False
    lines = [f"# Board stuck — {now()}", "",
             "todo tasks exist, nothing is ready and nothing is running.", ""]
    for i in groups["todo"]:
        t = tasks[i]
        pend = [d for d in t["meta"].get("depends", []) if d in tasks and tasks[d]["dir"] != "done"]
        miss = [d for d in t["meta"].get("depends", []) if d not in tasks]
        if miss:
            why = f"unknown dependency {', '.join(miss)}"
        elif pend:
            d = pend[0]
            why = f"waits for {d} ({key_of(tasks[d])})"
        else:
            why = "deps done but not returned by next (paths overlap an unblock lock?)"
        lines.append(f"- {i} {t['meta'].get('title', '')}: {why}")
    for k in ("blocked", "parked"):
        for i in groups[k]:
            last = [ln for ln in tasks[i]["body"].splitlines() if ln.startswith("- 20")]
            lines.append(f"- [{k}] {i} {tasks[i]['meta'].get('title', '')}: {last[-1][2:] if last else ''}")
    text = "\n".join(lines) + "\n"
    print(text, end="")
    if write:
        path = os.path.join(ROOT, "_workspaces", "STUCK.md")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("written", os.path.relpath(path, ROOT))
    return True


def cmd_adr_next(slug):
    slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-") or "decision"
    ddir = os.path.join(ROOT, "spec", "decisions")
    os.makedirs(ddir, exist_ok=True)
    os.makedirs(LOCKS, exist_ok=True)
    nums = [int(m.group(1)) for f in os.listdir(ddir) for m in [re.match(r"ADR-(\d{4})", f)] if m]
    nums += [int(m.group(1)) for f in os.listdir(LOCKS) for m in [re.match(r"adr-(\d{4})$", f)] if m]
    n = max(nums, default=0) + 1
    while True:
        try:
            fd = os.open(os.path.join(LOCKS, f"adr-{n:04d}"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            n += 1
    path = os.path.join(ddir, f"ADR-{n:04d}-{slug}.md")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"# ADR-{n:04d} — {slug} (reserved {now()}, fill in)\n\n## Tóm tắt\n\n## Context\n\n"
                 "## Decision\n\n## Consequences\n")
    print(os.path.relpath(path, ROOT).replace("\\", "/"))


def cmd_new_id(tasks, phase):
    m = re.match(r"P(\d+)", phase or "")
    if not m:
        die("new-id needs --phase P<n> (e.g. P7 or P12-numeric)")
    n = int(m.group(1))
    lo, hi = (112, 199) if n <= 10 else (400 + (n - 11) * 50, 449 + (n - 11) * 50)
    for k in range(lo, hi + 1):
        if f"T{k:03d}" not in tasks:
            print(f"T{k:03d}")
            return
    die(f"no free id in T{lo}-T{hi}; use a suffix id (e.g. T{hi}a)", 1)


# ---------------------------------------------------------------- main

def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd, rest = argv[0], list(argv[1:])
    if cmd in MUTATING and is_linked_worktree() and not os.environ.get("AXIOM_ROOT"):
        die(f"taskctl {cmd}: {ROOT} is a linked git worktree (e.g. a QA snapshot); the board is changed "
            "only from the main working tree")
    errors = []
    tasks = load_all(errors) if cmd in ("validate", "lint") else load_all()

    def opt(name, default=None):
        if name in rest:
            i = rest.index(name)
            if i + 1 >= len(rest):
                die(f"{name} needs a value")
            v = rest[i + 1]
            del rest[i:i + 2]
            return v
        return default

    def need_id():
        if not rest:
            die(f"usage: taskctl {cmd} ID ...")
        return rest[0]

    if cmd == "status":
        cmd_status(tasks, "--json" in rest)
    elif cmd == "list":
        which = rest[0] if rest else None
        for i, t in sorted(tasks.items()):
            key = key_of(t)
            if which in (None, key):
                m = t["meta"]
                print(f"{i:6} {key:8} {m.get('owner', ''):18} {m.get('title', '')}  deps={','.join(m.get('depends', []))}")
    elif cmd == "next":
        try:
            n = int(opt("--max", "1"))
        except ValueError:
            die("--max needs an integer")
        for t in ready(tasks, n):
            m = t["meta"]
            print(f"{m['id']}\t{m.get('owner')}\t{m.get('title')}\t{os.path.relpath(t['path'], ROOT)}")
    elif cmd == "show":
        print(open(get(tasks, need_id())["path"], encoding="utf-8").read())
    elif cmd == "start":
        t = get(tasks, need_id())
        agent = opt("--agent", "")
        if key_of(t) != "todo":
            die(f"{t['meta']['id']} is not a startable todo task ({key_of(t)})", 1)
        pending = [d for d in t["meta"].get("depends", []) if d in tasks and tasks[d]["dir"] != "done"]
        if pending and "--force" not in rest:
            die(f"{t['meta']['id']} depends on unfinished {', '.join(pending)} "
                f"(run those first, or --force with an architect note)", 1)
        t["meta"]["status"] = "doing"
        t["meta"]["attempts"] = str(ival(t["meta"], "attempts") + 1)
        t["meta"]["started"] = now()
        if agent:
            t["meta"]["agent"] = agent
        log(t, f"started (attempt {t['meta']['attempts']}) {agent}")
        move(t, "doing")
        print("doing:", os.path.relpath(t["path"], ROOT))
    elif cmd == "accept":
        cmd_accept(tasks, need_id(), rest)
    elif cmd == "finish":
        t = get(tasks, need_id())
        if t["dir"] != "doing":
            die(f"{t['meta']['id']} is not in doing", 1)
        t["meta"]["status"] = "done"
        t["meta"]["finished"] = now()
        t["meta"].pop("agent", None)
        log(t, "finished without commit (manual) -> done; run `taskctl commit` next")
        move(t, "done")
        print("done:", os.path.relpath(t["path"], ROOT), "(not committed: run commit, or use accept)")
    elif cmd in ("block", "requeue"):
        t = get(tasks, need_id())
        infra, free = "--infra" in rest, "--no-attempt" in rest
        rest[:] = [x for x in rest if x not in ("--infra", "--no-attempt")]
        reason = opt("--reason", "") or " ".join(rest[1:])
        if key_of(t) in ("done", "deferred", "parked"):
            die(f"{t['meta']['id']} is {key_of(t)}; {cmd} applies to doing/todo tasks", 1)
        if cmd == "requeue" and t["dir"] != "doing":
            die(f"{t['meta']['id']} is not in doing", 1)
        if cmd == "requeue" and (infra or free):
            t["meta"]["attempts"] = str(max(0, ival(t["meta"], "attempts") - 1))
            reason = f"{reason} ({'infrastructure failure' if infra else 'not charged'}: attempt refunded)"
        elif cmd == "requeue" and ival(t["meta"], "attempts") >= MAX_ATTEMPTS:
            # A task that keeps dying (crash, no report) goes to the architect instead of looping.
            cmd, reason = "block", f"{reason}; {MAX_ATTEMPTS} attempts without acceptance"
        t["meta"]["status"] = "blocked" if cmd == "block" else "todo"
        t["meta"].pop("agent", None)
        log(t, f"{cmd}: {reason}")
        move(t, "todo")
        print(f"{cmd}ed:", os.path.relpath(t["path"], ROOT))
    elif cmd == "unblock":
        t = get(tasks, need_id())
        m, k = t["meta"], key_of(t)
        approved = "--owner-approved" in rest
        rest[:] = [x for x in rest if x != "--owner-approved"]
        if k in ("deferred", "parked"):
            if not approved:
                die(f"{m['id']} is {k}: only the owner releases it (--owner-approved)", 1)
            m["unblocks"], m["unblock_failures"] = "0", "0"
        elif k != "blocked":
            die(f"{m['id']} is {k}, not blocked", 1)
        elif ival(m, "unblocks") >= MAX_UNBLOCKS:
            park(t, f"unblock refused: {MAX_UNBLOCKS} unblock cycles already used; needs the owner")
            print(f"parked {m['id']}")
            raise SystemExit(4)
        else:
            m["unblocks"] = str(ival(m, "unblocks") + 1)
        m["status"] = "todo"
        m["attempts"] = "0"  # fresh budget after the architect changed something
        log(t, f"unblocked ({'owner-approved ' if approved else ''}cycle {m.get('unblocks')}) " + " ".join(rest[1:]))
        save(t)
        print("unblocked", m["id"])
    elif cmd == "unblock-begin":
        cmd_unblock_begin(tasks, need_id())
    elif cmd == "unblock-end":
        cmd_unblock_end(tasks, need_id(), "--failed" in rest)
    elif cmd == "park":
        t = get(tasks, need_id())
        reason = opt("--reason", "") or " ".join(rest[1:])
        if key_of(t) not in ("todo", "blocked"):
            die(f"{t['meta']['id']} is {key_of(t)}; only todo/blocked tasks can be parked", 1)
        park(t, reason)
        print("parked", t["meta"]["id"])
    elif cmd == "supersede":
        by = opt("--by")
        t = get(tasks, need_id())
        if not by or by not in tasks:
            die("supersede needs --by <existing task id>")
        if key_of(t) not in ("todo", "blocked", "parked"):
            die(f"{t['meta']['id']} is {key_of(t)}; only todo/blocked/parked tasks can be superseded", 1)
        t["meta"]["status"] = "done"
        t["meta"]["superseded_by"] = by
        t["meta"]["finished"] = now()
        log(t, f"superseded by {by} -> done (no code of its own)")
        move(t, "done")
        print("superseded:", os.path.relpath(t["path"], ROOT))
    elif cmd == "covers":
        t = get(tasks, need_id())
        reqs = [r for r in rest[1:] if re.fullmatch(r"REQ-[A-Z0-9]+-\d+[a-z]?", r)]
        if not reqs or len(reqs) != len(rest[1:]):
            die("usage: taskctl covers ID REQ-XXX-001 [REQ-...]")
        cur = list(t["meta"].get("covers", []))
        cur += [r for r in reqs if r not in cur]
        t["meta"]["covers"] = cur
        log(t, "covers += " + ", ".join(reqs) + " (metadata only)")
        save(t)
        print(f"{t['meta']['id']} covers: {', '.join(cur)}")
    elif cmd == "note":
        t = get(tasks, need_id())
        log(t, " ".join(rest[1:]))
        save(t)
    elif cmd == "validate":
        sys.exit(0 if cmd_validate(tasks, errors) else 1)
    elif cmd == "lint":
        if not rest:
            die("usage: taskctl lint FILE...")
        sys.exit(0 if cmd_lint(rest, tasks) else 1)
    elif cmd == "commit":
        cmd_commit(tasks, need_id(), rest)
    elif cmd == "commit-report":
        subject = opt("--subject")
        if not rest:
            die('usage: taskctl commit-report REPORT.md --subject "arch: ..."')
        cmd_commit_report(tasks, rest[0], subject)
    elif cmd == "changes":
        files, problems, notes = changeset(tasks, get(tasks, need_id()),
                                           "--include-unlisted" in rest, "--allow-unlisted" in rest)
        print_plan(files, problems, notes)
        for f in files:
            print("stage", f)
        sys.exit(1 if problems else 0)
    elif cmd == "reconcile":
        sys.exit(0 if cmd_reconcile(tasks, "--commit" in rest) else 1)
    elif cmd == "recover":
        tid = need_id()
        r = opt("--round")
        cmd_recover(tasks, tid, opt("--stage"), int(r) if r is not None else None)
    elif cmd == "snapshot":
        tid = need_id()
        cmd_snapshot(tasks, tid, opt("--dir"), "--remove" in rest)
    elif cmd == "stuck":
        sys.exit(3 if cmd_stuck(tasks, "--write" in rest) else 0)
    elif cmd == "adr-next":
        cmd_adr_next(need_id())
    elif cmd == "new-id":
        cmd_new_id(tasks, opt("--phase"))
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
