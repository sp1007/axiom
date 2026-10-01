#!/usr/bin/env python3
"""selftest — regression tests for the harness scripts, run on COPIES in temporary git repositories.

Usage: python .claude/skills/axiom-tasks/scripts/selftest.py [--keep]     (exit 1 when a check fails)

Never touches the real board: it copies the scripts (and, read-only, the board, skills and spec) into
throw-away repositories under the system temp directory and drives them there:
    A  synthetic 10-task board  — scheduling, accept/commit, snapshot, recovery, unblock caps, infra
    B  copy of the real board   — validate, duplicate ids, task template, harness_check
    C  tiny boards              — wrong root, empty board, stuck, finished, guard hook
Run it after every change to taskctl.py, autopilot.py, overdue.py, reqcov.py, harness_check.py or
.claude/hooks/guard.py. --keep leaves the temporary repositories for inspection.
"""
import datetime as dt
import glob
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REAL = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
TR = os.path.join(tempfile.gettempdir(), "axiom-harness-selftest")
SCRIPTS = os.path.join(".claude", "skills", "axiom-tasks", "scripts")
results = []
BASE_ENV = dict(os.environ)
for k in ("AXIOM_ROOT", "AXIOM_COMMIT_TRAILER", "CLAUDE_PROJECT_DIR"):
    BASE_ENV.pop(k, None)
BASE_ENV["CLAUDE_CODE_SESSION_ID"] = "sess-1"
BASE_ENV["CLAUDE_PID"] = "1000"


def rmtree(p):
    def onerr(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if os.path.exists(p):
        shutil.rmtree(p, onerror=onerr)


def sh(args, cwd, env=None, inp=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env or BASE_ENV, input=inp)
    return r.returncode, (r.stdout + r.stderr).strip()


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"\n     {detail[:1500]}"))


def write(root, rel, text, mtime=None):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    if mtime:
        os.utime(p, (mtime, mtime))
    return p


def task(tid, pri, deps, paths, extra="", status="todo", phase="P1-core"):
    return (f"---\nid: {tid}\ntitle: Task {tid}\nphase: {phase}\nowner: axiom-frontend\nreviewer: axiom-qa\n"
            f"model: sonnet\ngate_model: sonnet\ndepends: [{', '.join(deps)}]\npriority: {pri}\n"
            f"status: {status}\nattempts: 0\npaths: [{', '.join(paths)}]\n{extra}---\n"
            f"## Goal\nx\n## Acceptance\n- tests pass\n")


def new_repo(name, copy_claude=True):
    root = os.path.join(TR, name)
    os.makedirs(root)
    sh(["git", "init", "-q", "-b", "main"], root)
    sh(["git", "config", "user.email", "t@example.invalid"], root)
    sh(["git", "config", "user.name", "tester"], root)
    sh(["git", "config", "core.autocrlf", "false"], root)
    sh(["git", "config", "core.longpaths", "true"], root)
    os.makedirs(os.path.join(root, SCRIPTS))
    for f in os.listdir(os.path.join(REAL, SCRIPTS)):
        if f.endswith(".py"):
            shutil.copy2(os.path.join(REAL, SCRIPTS, f), os.path.join(root, SCRIPTS, f))
    os.makedirs(os.path.join(root, ".claude", "hooks"))
    shutil.copy2(os.path.join(REAL, ".claude", "hooks", "guard.py"), os.path.join(root, ".claude", "hooks"))
    for f in (".gitignore", ".gitattributes"):
        shutil.copy2(os.path.join(REAL, f), os.path.join(root, f))
    for d in ("todo", "doing", "done"):
        os.makedirs(os.path.join(root, "_workspaces", "tasks", d))
        write(root, f"_workspaces/tasks/{d}/.gitkeep", "")
    write(root, "docs/base/owner.md", "owner text\n")
    return root


def commit_all(root, msg="init"):
    sh(["git", "add", "-A"], root)
    return sh(["git", "commit", "-q", "-m", msg], root)


def tc(root, *args, cwd=None, env=None):
    return sh([sys.executable, os.path.join(root, SCRIPTS, "taskctl.py"), *args], cwd or root, env)


def ap(root, *args, env=None):
    return sh([sys.executable, os.path.join(root, SCRIPTS, "autopilot.py"), *args], root, env)


def od(root, *args, env=None):
    return sh([sys.executable, os.path.join(root, SCRIPTS, "overdue.py"), *args], root, env)


def where(root, tid):
    for d in ("todo", "doing", "done"):
        for f in os.listdir(os.path.join(root, "_workspaces", "tasks", d)):
            if f.startswith(tid + "-"):
                return d, open(os.path.join(root, "_workspaces", "tasks", d, f), encoding="utf-8").read()
    return None, ""


def head_files(root):
    return sh(["git", "-c", "core.quotepath=false", "show", "--name-only", "--format=%s", "HEAD"], root)[1]


def status(root):
    return sh(["git", "status", "--porcelain", "-uall"], root)[1]


# =============================================================== repo A
def build_a():
    a = new_repo("A")
    T = "_workspaces/tasks/todo/"
    write(a, T + "T001-core.md", task("T001", 1, [], ["spec/core"]))
    write(a, T + "T002-lexer.md", task("T002", 20, ["T001"], ["src/lexer", "tests/lex"]))
    write(a, T + "T003-parser.md", task("T003", 21, ["T001"], ["src/parser"]))
    write(a, T + "T004-sub.md", task("T004", 22, ["T001"], ["src/lexer/sub"]))
    write(a, T + "T005-types.md", task("T005", 23, ["T001"], ["src/types"], "locks: [src/diag/codes.def]\n"))
    write(a, T + "T006-mir.md", task("T006", 24, ["T001"], ["src/mir"], "locks: [src/diag/codes.def]\n"))
    write(a, T + "T007-crit.md", task("T007", 5, ["T002"], ["spec/x"]))
    write(a, T + "T008-extract.md", task("T008", 30, ["T001"], ["std"], phase="P0-traceability"))
    write(a, T + "T009-tools.md", task("T009", 31, ["T001"], ["tools"], "timeout_min: 400\n"))
    write(a, T + "T224-eco.md", task("T224", 90, [], ["eco"], status="deferred", phase="P24-eco"))
    write(a, "spec/ROADMAP.md", "# roadmap\n- **E13.1 pointers** x\n- **E5.1 vec** y\n")
    write(a, "src/diag/codes.def", "X(1)\n")
    commit_all(a)
    return a


def test_a(a):
    rc, out = tc(a, "validate")
    check("A validate ok", rc == 0 and "OK (10 tasks)" in out, out)
    rc, out = tc(a, "next", "--max", "0")
    check("A4-22 next --max 0 returns nothing", rc == 0 and out == "", out)
    rc, out = tc(a, "next", "--max", "3")
    check("critical T001 returned alone", out.split("\t")[0] == "T001" and len(out.splitlines()) == 1, out)
    rc, out = tc(a, "start", "T002")
    check("start refuses unfinished deps", rc == 1 and "unfinished" in out, out)

    # ---- A4-01 cwd independence
    sub = os.path.join(a, "src", "deep")
    os.makedirs(sub)
    rc1, o1 = tc(a, "status", cwd=sub)
    rc2, o2 = tc(a, "status", cwd=os.path.expanduser("~"))
    check("A4-01 status from a subdirectory and from outside the repo sees the board",
          rc1 == 0 and rc2 == 0 and "total 10" in o1 and "total 10" in o2, o1 + o2)
    check("A4-01 no stray _workspaces created", not os.path.exists(os.path.join(sub, "_workspaces")))

    # ---- T001 accept: report formats, unlisted file, docs, ignored file
    tc(a, "start", "T001", "--agent", "T001-impl")
    write(a, "spec/core/a.md", "a\n")
    write(a, "spec/core/b.md", "b\n")
    write(a, "spec/core/c.md", "c\n")
    write(a, "spec/core/d.md", "d\n")
    write(a, "spec/core/unlisted.md", "u\n")
    write(a, "spec/core/tool.exe", "binary\n")          # git-ignored
    write(a, "docs/base/owner.md", "owner text changed by the owner\n")
    write(a, "_workspaces/reports/T001-report.md",
          "# T001 report\n## Summary\nx\n## Files changed\n"
          "- **spec/core/a.md** — new\n"
          "1. `spec/core/b.md` (edited)\n"
          "| File | Note |\n|---|---|\n| `spec/core/c.md` | table row |\n"
          "* [spec/core/d.md](spec/core/d.md)\n"
          "- docs/base/owner.md\n- spec/core/tool.exe\n- spec/core/missing.md\n"
          "some prose line\n"
          "## Tests\nnone\n\nSTATUS: COMPLETE round=0\n")
    rc, out = tc(a, "accept", "T001")
    check("accept refused without a QA verdict", rc == 1 and "not PASS" in out and where(a, "T001")[0] == "doing", out)
    write(a, "_workspaces/reports/T001-qa.md", "# QA\nVERDICT: FAIL round=0\n- broken\n")
    rc, out = tc(a, "accept", "T001")
    check("accept refused on VERDICT: FAIL", rc == 1 and where(a, "T001")[0] == "doing", out)
    write(a, "_workspaces/reports/T001-qa.md", "# QA\nVERDICT: FAIL round=0\n\n## Round 1\n**VERDICT: PASS** round=1\n")
    rc, out = tc(a, "accept", "T001")
    check("A4-04 accept refuses (exit 1) when a changed file under the task's paths is unlisted",
          rc == 1 and "unlisted.md" in out and where(a, "T001")[0] == "doing"
          and sh(["git", "diff", "--cached", "--name-only"], a)[1] == "", out)
    rc, out = tc(a, "changes", "T001")
    check("changes (dry run) reports the same refusal", rc == 1 and "REFUSED" in out, out)
    rc, out = tc(a, "accept", "T001", "--include-unlisted")
    hf = head_files(a)
    check("A4-05 accept commits code + reports + board in one commit and moves to done",
          rc == 0 and where(a, "T001")[0] == "done" and hf.startswith("T001: Task T001")
          and all(x in hf for x in ("spec/core/a.md", "spec/core/b.md", "spec/core/c.md", "spec/core/d.md",
                                    "spec/core/unlisted.md", "T001-report.md", "T001-qa.md",
                                    "_workspaces/tasks/done/T001-core.md")), out + "\n" + hf)
    check("A4-04 bold / numbered / table / link entries all parsed", "prose line" in out, out)
    check("docs/ and git-ignored files never staged",
          "docs/" not in hf and "tool.exe" not in hf and "M docs/base/owner.md" in status(a)
          and sh(["git", "diff", "--cached", "--name-only"], a)[1] == "", hf + status(a))
    body = sh(["git", "log", "-1", "--format=%B"], a)[1]
    check("A4-25 trailer has no hard-coded model name", "Co-Authored-By: Claude <noreply@anthropic.com>" in body, body)
    env = dict(BASE_ENV, AXIOM_COMMIT_TRAILER="Co-Authored-By: X <x@example.invalid>")

    # ---- parallel batch after the critical task
    rc, out = tc(a, "next", "--max", "3")
    ids = [ln.split("\t")[0] for ln in out.splitlines()]
    check("next honours paths and locks (T004 overlaps T002, T006 shares a lock with T005)",
          ids == ["T002", "T003", "T005"], out)
    for i in ids:
        tc(a, "start", i, "--agent", i + "-impl")

    # ---- A3-03 snapshot isolation
    write(a, "src/parser/broken.c", "this does not compile {\n")          # T003, half-written
    write(a, "src/lexer/ok.c", "int lexer(void) { return 0; }\n")         # T002
    write(a, "tests/lex/t1.ax", "fn main() = 0\n")
    write(a, "_workspaces/reports/T002-report.md",
          "# T002\n## Files changed\n- src/lexer/ok.c\n- tests/lex/t1.ax\n\nSTATUS: COMPLETE round=0\n")
    rc, out = tc(a, "snapshot", "T002")
    snap = os.path.join(a, "build-snap-T002")
    check("A3-03 snapshot = HEAD + only this task's files (other task's half-written file absent)",
          rc == 0 and os.path.exists(os.path.join(snap, "src", "lexer", "ok.c"))
          and os.path.exists(os.path.join(snap, "tests", "lex", "t1.ax"))
          and not os.path.exists(os.path.join(snap, "src", "parser"))
          and os.path.exists(os.path.join(snap, "spec", "core", "a.md")), out)
    check("snapshot directory is ignored by git", "build-snap" not in status(a), status(a))
    write(snap, "build/obj.o", "object\n")
    write(a, "src/lexer/new.c", "int n;\n")              # unlisted yet: snapshot still takes it
    os.remove(os.path.join(a, "tests", "lex", "t1.ax"))
    rc, out = tc(a, "snapshot", "T002")
    check("snapshot refresh in place keeps the build dir, adds new files, drops removed ones",
          rc == 0 and "refreshed" in out and os.path.exists(os.path.join(snap, "build", "obj.o"))
          and os.path.exists(os.path.join(snap, "src", "lexer", "new.c"))
          and not os.path.exists(os.path.join(snap, "tests", "lex", "t1.ax")), out)
    rc, out = sh([sys.executable, os.path.join(snap, SCRIPTS, "taskctl.py"), "start", "T004"], snap)
    check("board cannot be changed from inside a snapshot worktree", rc == 2 and "linked git worktree" in out, out)
    rc, out = sh([sys.executable, os.path.join(snap, SCRIPTS, "taskctl.py"), "status"], snap)
    check("read-only commands work inside a snapshot", rc == 0 and "total 10" in out, out)

    # ---- accept T002: entry inside another running task's paths, glob entry, directory entry
    write(a, "_workspaces/reports/T002-qa.md", "# QA\n## Files changed\n- tests/lex/qa_added.ax\n\nVERDICT: PASS round=0\n")
    write(a, "tests/lex/qa_added.ax", "fn main() = 1\n")
    write(a, "_workspaces/reports/T002-report.md",
          "# T002\n## Files changed\n- src/lexer/ok.c\n- src/lexer/new.c\n- src/parser/broken.c\n- **tests/**\n"
          "- src/*.c\n\nSTATUS: COMPLETE round=0\n")
    rc, out = tc(a, "accept", "T002")
    check("A4-04 refuses an entry inside a running task's paths, a directory outside paths, a glob",
          rc == 1 and "running task T003" in out and "directory entry 'tests/'" in out and "glob" in out
          and where(a, "T002")[0] == "doing", out)
    write(a, "_workspaces/reports/T002-report.md",
          "# T002\n## Files changed\n- src/lexer/ok.c\n- src/lexer/new.c\n- tests/lex/ (directory)\n\nSTATUS: COMPLETE round=0\n")
    rc, out = tc(a, "accept", "T002", env=env)
    hf = head_files(a)
    check("accept T002 commits its files (incl. QA-added test, directory entry inside paths), not T003's",
          rc == 0 and "src/lexer/ok.c" in hf and "tests/lex/qa_added.ax" in hf and "broken.c" not in hf
          and "?? src/parser/broken.c" in status(a), out + hf + status(a))
    check("A4-25 trailer configurable", "X <x@example.invalid>" in sh(["git", "log", "-1", "--format=%B"], a)[1])
    rc, out = tc(a, "snapshot", "T002", "--remove")
    check("snapshot --remove", rc == 0 and not os.path.exists(snap)
          and "build-snap" not in sh(["git", "worktree", "list"], a)[1], out)

    # ---- commit failure -> rollback; crash between move and commit -> reconcile
    write(a, "src/parser/broken.c", "int parser(void) { return 0; }\n")
    write(a, "_workspaces/reports/T003-report.md", "# T003\n## Files changed\n- src/parser/broken.c\n\nSTATUS: COMPLETE round=0\n")
    write(a, "_workspaces/reports/T003-qa.md", "VERDICT: PASS\n")
    hook = write(a, ".git/hooks/pre-commit", "#!/bin/sh\necho hook says no >&2\nexit 1\n")
    rc, out = tc(a, "accept", "T003")
    check("A4-05 failed git commit rolls the task back to doing with a clean index",
          rc == 1 and where(a, "T003")[0] == "doing" and "status: doing" in where(a, "T003")[1]
          and sh(["git", "diff", "--cached", "--name-only"], a)[1] == "", out)
    os.remove(hook)
    tc(a, "finish", "T003")       # simulates a crash after the move, before the commit
    rc, out = tc(a, "reconcile")
    check("A4-05 reconcile detects a done task without its commit", rc == 1 and "UNCOMMITTED T003" in out, out)
    rc, out = tc(a, "reconcile", "--commit")
    hf = head_files(a)
    check("A4-05 reconcile --commit repairs it", rc == 0 and hf.startswith("T003:") and "broken.c" in hf, out + hf)
    rc, out = tc(a, "reconcile")
    check("reconcile clean afterwards", rc == 0, out)

    # ---- critical drain + unblock lock + caps (A4-08, A4-09)
    rc, out = tc(a, "next", "--max", "3")
    check("drain: critical T007 ready while T005 runs -> nothing starts", out == "", out)
    tc(a, "block", "T005", "--reason", "QA failed 3 times")
    rc, out = tc(a, "unblock-begin", "T005")
    check("A4-09 unblock waits while a critical task is waiting to run", rc == 3 and "T007" in out, out)
    rc, out = tc(a, "next", "--max", "3")
    check("critical T007 alone once doing is empty", out.split("\t")[0] == "T007" and len(out.splitlines()) == 1, out)
    tc(a, "start", "T007")
    rc, out = tc(a, "unblock-begin", "T005")
    check("A4-09 unblock waits while a critical task runs", rc == 3, out)
    tc(a, "block", "T007", "--reason", "spec contradiction")
    rc, out = tc(a, "unblock-begin", "T005")
    check("unblock-begin takes the lock", rc == 0 and os.path.exists(os.path.join(a, "_workspaces/locks/unblock.json")), out)
    rc, out = tc(a, "unblock-begin", "T007")
    check("A4-09 unblocks are serialised", rc == 3 and "serialised" in out, out)
    rc, out = tc(a, "status")
    check("status shows the running unblock", "[unblock running] T005" in out, out)
    check("locks directory is git-ignored", "locks" not in status(a), status(a))
    tc(a, "unblock", "T005", "ADR-0009")
    tc(a, "unblock-end", "T005")
    check("unblock: blocked -> todo, attempts reset, cycle counted",
          "unblocks: 1" in where(a, "T005")[1] and "attempts: 0" in where(a, "T005")[1]
          and not os.path.exists(os.path.join(a, "_workspaces/locks/unblock.json")))
    tc(a, "block", "T005", "--reason", "again")
    tc(a, "unblock-begin", "T005"); tc(a, "unblock", "T005"); tc(a, "unblock-end", "T005")
    tc(a, "block", "T005", "--reason", "third time")
    rc, out = tc(a, "unblock-begin", "T005")
    check("A4-08 third unblock cycle is refused: task parked (exit 4)",
          rc == 4 and "status: parked" in where(a, "T005")[1], out)
    rc, out = tc(a, "unblock", "T005")
    check("parked task needs --owner-approved", rc == 1, out)
    tc(a, "unblock-begin", "T007"); rc1, _ = tc(a, "unblock-end", "T007", "--failed")
    tc(a, "unblock-begin", "T007"); rc2, out = tc(a, "unblock-end", "T007", "--failed")
    check("A4-08 two failed unblock agents park the task (no endless respawn)",
          "status: parked" in where(a, "T007")[1], out)
    rc, out = tc(a, "unblock", "T224")
    check("A4-24 deferred T224 cannot be unblocked without --owner-approved", rc == 1 and "deferred" in out, out)
    tc(a, "start", "T006")
    rc, out = tc(a, "unblock", "T006")
    check("A4-24 unblock refuses a doing task", rc == 1 and where(a, "T006")[0] == "doing", out)

    # ---- A4-07 infra failures / attempts
    rc, out = tc(a, "requeue", "T006", "--infra", "--reason", "rate limit: 429")
    d, txt = where(a, "T006")
    check("A4-07 requeue --infra refunds the attempt and does not block",
          rc == 0 and d == "todo" and "attempts: 0" in txt and "status: todo" in txt, out + txt)
    for n in range(3):
        tc(a, "start", "T006")
        rc, out = tc(a, "requeue", "T006", "--reason", "agent crashed")
    check("charged requeue blocks at the 3rd attempt", "status: blocked" in where(a, "T006")[1], out)
    for n in range(5):
        tc(a, "start", "T008")
        tc(a, "requeue", "T008", "--infra", "--reason", "rate limit")
    check("A4-07 five rate-limit failures in a row never block the task",
          "status: todo" in where(a, "T008")[1] and "attempts: 0" in where(a, "T008")[1], where(a, "T008")[1])

    # ---- autopilot.py: backoff, session, check-board
    rc, out = ap(a, "init", "--cron", "cron-1")
    check("autopilot init", rc == 0 and "board_total 10" in out, out)
    ap(a, "infra-fail", "--reason", "rate limit")
    rc, out = ap(a, "backoff")
    st = json.load(open(os.path.join(a, "_workspaces", "autopilot.json"), encoding="utf-8"))
    check("A4-07 infra-fail starts a 30-minute backoff (exit 3)", rc == 3 and st["infra_failures"] == 1, out)
    ap(a, "infra-fail"); rc, o2 = ap(a, "infra-fail"); ap(a, "infra-fail")
    check("backoff grows 30/60/120 and is capped", "120 min" in ap(a, "infra-fail")[1])
    ap(a, "infra-ok")
    rc, out = ap(a, "backoff")
    check("infra-ok clears the backoff", rc == 0, out)
    check("autopilot.json is git-ignored", "autopilot" not in status(a), status(a))

    tc(a, "start", "T008", "--agent", "T008-impl")
    ap(a, "run", "T008", "--stage", "impl", "--agent", "T008-impl")
    rc, out = ap(a, "session")
    check("A4-06 same process -> same session", "same session" in out, out)
    env2 = dict(BASE_ENV, CLAUDE_PID="2000")             # resumed session = new process
    rc, out = od(a, env=env2)
    check("A4-06 overdue.py lists a previous-session entry as `recover`", "recover" in out and "T008" in out, out)
    rc, out = ap(a, "session", env=env2)
    check("A4-06 new process -> new session, dead running entries listed", "new session" in out and "T008" in out, out)

    # ---- recover table
    now = time.time()
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: impl, no report -> requeue", out.startswith("requeue"), out)
    write(a, "_workspaces/reports/T008-report.md", "# r\n## Files changed\n- std/a.ax\n", mtime=now + 5)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("A4-06 recover: report without STATUS line is not complete -> requeue", out.startswith("requeue"), out)
    write(a, "_workspaces/reports/T008-report.md", "# r\n## Files changed\n- std/a.ax\n\nSTATUS: COMPLETE round=0\n",
          mtime=now - 5000)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: COMPLETE report older than this attempt (previous attempt) -> requeue", out.startswith("requeue"), out)
    os.utime(os.path.join(a, "_workspaces/reports/T008-report.md"), (now + 5, now + 5))
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: impl + STATUS COMPLETE -> qa", out.startswith("qa"), out)
    ap(a, "run", "T008", "--stage", "qa", "--agent", "T008-qa", env=env2)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: qa stage, no verdict -> qa (respawn gate)", out.startswith("qa"), out)
    write(a, "_workspaces/reports/T008-qa.md", "# QA\nVERDICT: FAIL round=0\n", mtime=now + 10)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: qa stage, FAIL round 0 -> fix 1", out.startswith("fix 1"), out)
    ap(a, "run", "T008", "--stage", "fix", "--agent", "T008-impl", "--round", "1", env=env2)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("A4-06 recover: fix stage, report not updated -> fix 1 again (no QA on unfixed code)",
          out.startswith("fix 1"), out)
    write(a, "_workspaces/reports/T008-report.md", "# r\n## Files changed\n- std/a.ax\n\nSTATUS: COMPLETE round=1\n",
          mtime=now + 20)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: fix stage, report round=1 newer than verdict -> qa 1", out.startswith("qa 1\t"), out)
    ap(a, "run", "T008", "--stage", "qa", "--agent", "T008-qa", "--round", "1", env=env2)
    os.utime(os.path.join(a, "_workspaces/reports/T008-qa.md"), (now + 30, now + 30))
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: qa round 1 but last verdict is tagged round=0 (stale) -> qa", out.startswith("qa"), out)
    write(a, "_workspaces/reports/T008-qa.md", "VERDICT: FAIL round=0\n## Round 1\nVERDICT: FAIL round=1\n", mtime=now + 30)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: qa round 1 FAIL -> fix 2", out.startswith("fix 2"), out)
    ap(a, "run", "T008", "--stage", "qa", "--agent", "T008-qa", "--round", "2", env=env2)
    write(a, "_workspaces/reports/T008-qa.md", "VERDICT: FAIL round=2\n", mtime=now + 30)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: qa round 2 FAIL -> block", out.startswith("block"), out)
    write(a, "_workspaces/reports/T008-qa.md", "VERDICT: PASS round=2\n", mtime=now + 30)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover: PASS -> accept", out.startswith("accept"), out)
    ap(a, "drop", "T008", env=env2)
    rc, out = tc(a, "recover", "T008", env=env2)
    check("recover without an autopilot record infers the stage from the files", out.startswith("accept"), out)
    tc(a, "requeue", "T008", "--no-attempt", "--reason", "test cleanup")

    # ---- overdue: per-task limits, long phases, activity (A4-12)
    def since(minutes):
        return (dt.datetime.now() - dt.timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")

    tc(a, "unblock", "T006", "--owner-approved") if "parked" in where(a, "T006")[1] else tc(a, "unblock", "T006")
    for i in ("T006", "T008", "T009"):
        tc(a, "start", i)
    stj = json.load(open(os.path.join(a, "_workspaces", "autopilot.json"), encoding="utf-8"))
    sess = stj["session_id"]
    stj["running"] = {
        "T006": {"agent": "T006-impl", "stage": "impl", "round": 0, "since": since(200), "session": sess},
        "T008": {"agent": "T008-impl", "stage": "impl", "round": 0, "since": since(200), "session": sess},
        "T009": {"agent": "T009-impl", "stage": "impl", "round": 0, "since": since(390), "session": sess}}
    json.dump(stj, open(os.path.join(a, "_workspaces", "autopilot.json"), "w", encoding="utf-8"))
    old = time.time() - 3 * 3600
    write(a, "src/mir/m.c", "x\n", mtime=old)
    os.utime(os.path.join(a, "src", "diag", "codes.def"), (old, old))
    rc, out = od(a, env=env2)
    lines = {ln.split("\t")[0]: ln for ln in out.splitlines()}
    check("A4-12 default limit 180: idle T006 at 200 min -> kill", "T006" in lines and lines["T006"].endswith("kill"), out)
    check("A4-12 extraction phase gets the long limit (300): T008 at 200 min not overdue", "T008" not in lines, out)
    check("A4-12 per-task timeout_min 400: T009 at 390 min not overdue (only probed: it is silent)",
          "T009" in lines and "limit 400" in lines["T009"] and lines["T009"].endswith("probe"), out)
    write(a, "src/mir/m.c", "y\n")
    rc, out = od(a, env=env2)
    check("A4-12 activity signal: overdue but files changing -> keep", "T006" in out and "keep" in out, out)
    stj["running"]["T006"]["since"] = since(400)
    json.dump(stj, open(os.path.join(a, "_workspaces", "autopilot.json"), "w", encoding="utf-8"))
    rc, out = od(a, env=env2)
    check("A4-12 hard cap (2x limit) kills even an active agent", "T006" in out and "kill" in out, out)
    stj["running"] = {"T008": {"agent": "T008-impl", "stage": "impl", "round": 0, "since": since(50), "session": sess},
                      "T009": {"agent": "T009-impl", "stage": "impl", "round": 0, "since": since(50), "session": sess},
                      "T006": {"agent": "T006-impl", "stage": "impl", "round": 0, "since": since(20), "session": sess}}
    json.dump(stj, open(os.path.join(a, "_workspaces", "autopilot.json"), "w", encoding="utf-8"))
    write(a, "tools/t.py", "x\n")                      # T009 is active, T008 (std/) is silent
    for f in ("T008-report.md", "T008-qa.md"):
        os.utime(os.path.join(a, "_workspaces", "reports", f), (old, old))
    rc, out = od(a, env=env2)
    lines = {ln.split("\t")[0]: ln for ln in out.splitlines()}
    check("A4-07 silent agent inside its limit (died on a rate limit in the same session) -> probe",
          "T008" in lines and lines["T008"].endswith("probe") and "T009" not in lines and "T006" not in lines, out)
    for i in ("T006", "T008", "T009"):
        tc(a, "requeue", i, "--no-attempt", "--reason", "hung while progressing")
    check("requeue --no-attempt does not charge", "attempts: 0" in where(a, "T009")[1], where(a, "T009")[1])

    # ---- misc commands
    r1 = tc(a, "adr-next", "First Decision")[1]
    r2 = tc(a, "adr-next", "second")[1]
    procs = [subprocess.Popen([sys.executable, os.path.join(a, SCRIPTS, "taskctl.py"), "adr-next", f"par{i}"],
                              cwd=a, stdout=subprocess.PIPE, text=True, env=BASE_ENV) for i in range(5)]
    outs = [p.communicate()[0].strip() for p in procs]
    nums = [x.split("ADR-")[1][:4] for x in [r1, r2] + outs]
    check("A4-09 adr-next allocates distinct numbers, also when called concurrently",
          len(set(nums)) == 7 and r1.endswith("ADR-0001-first-decision.md"), str(nums))
    check("A4-18 new-id for core and post-self-host phases",
          tc(a, "new-id", "--phase", "P7-own")[1] == "T112" and tc(a, "new-id", "--phase", "P18")[1] == "T750",
          tc(a, "new-id", "--phase", "P18")[1])
    rc, out = tc(a, "supersede", "T004", "--by", "T002")
    check("A4-18 supersede closes a todo task as done-by-split", rc == 0 and where(a, "T004")[0] == "done"
          and "superseded_by: T002" in where(a, "T004")[1], out)
    check("reconcile ignores superseded tasks", "T004" not in tc(a, "reconcile")[1])
    rc, out = tc(a, "covers", "T001", "REQ-LEX-001", "REQ-LEX-002")
    check("A4-10 covers edits metadata of a done task", rc == 0 and "covers: [REQ-LEX-001, REQ-LEX-002]" in where(a, "T001")[1], out)

    # ---- commit-report (architect unblock / review)
    write(a, "spec/x/new.md", "decision\n")
    write(a, "_workspaces/reports/unblock-T007.md",
          "# unblock T007\n## Files changed\n- **spec/x/new.md**\n- docs/base/owner.md\n- `spec/decisions/ADR-0001-first-decision.md`\n")
    rc, out = tc(a, "commit-report", "_workspaces/reports/unblock-T007.md", "--subject", "arch: unblock T007 — ADR")
    hf = head_files(a)
    check("commit-report commits the listed files + report + board, never docs/",
          rc == 0 and hf.startswith("arch: unblock T007") and "spec/x/new.md" in hf and "ADR-0001" in hf
          and "docs/" not in hf and "unblock-T007.md" in hf, out + hf)
    check("owner's docs change still uncommitted and unstaged at the end", "M docs/base/owner.md" in status(a)
          and sh(["git", "diff", "--cached", "--name-only"], a)[1] == "", status(a))

    # ---- reqcov (A4-10, A4-11, A4-16)
    rq = [sys.executable, os.path.join(a, SCRIPTS, "reqcov.py")]
    rc, out = sh(rq + ["--strict"], a)
    check("A4-16 reqcov --strict fails without a catalogue", rc == 1, out)
    rc, out = sh(rq + ["--strict", "--allow-missing"], a)
    check("reqcov --strict --allow-missing passes before the catalogue exists", rc == 0, out)
    write(a, "spec/requirements/CATALOG.md",
          "| id | area | tier | statement | sources | needs | status |\n|---|---|---|---|---|---|---|\n"
          "| REQ-TYP-001 | types | v1-core | raw pointers | 0160 | - | EPIC(E13.1) |\n"
          "| REQ-STD-001 | std | v1-core | Vec needs raw pointers | 0412 | REQ-TYP-001 | T002 |\n"
          "| REQ-LEX-001 | lex | v1-core | tokens | 0001 | - | T001 |\n"
          "| REQ-LEX-002 | lex | v1-core | more | 0001 | REQ-LEX-001 | T001 |\n"
          "| REQ-ECO-001 | eco | v1-core | late | 0001 | - | T224 |\n")
    tc(a, "covers", "T002", "REQ-STD-001")
    tc(a, "covers", "T224", "REQ-ECO-001")
    rc, out = sh(rq + ["--strict"], a)
    check("A4-11 v1-core requirement planned in a post-self-host epic is a PROBLEM",
          rc == 1 and "REQ-TYP-001: v1-core but planned in post-self-host epic E13.1" in out, out)
    check("A4-11 needs: consumer whose prerequisite has no implementing task is a PROBLEM",
          "REQ-STD-001: needs REQ-TYP-001 which has no implementing task" in out, out)
    check("A4-11 v1-core mapped to a post-self-host task is a PROBLEM", "REQ-ECO-001: v1-core but mapped to T224" in out, out)
    check("reqcov accepts a satisfied needs: edge", "REQ-LEX-002" not in out, out)


# =============================================================== repo B (real board copy)
def test_b():
    b = new_repo("B")
    shutil.rmtree(os.path.join(b, ".claude"))
    shutil.copytree(os.path.join(REAL, ".claude"), os.path.join(b, ".claude"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.rmtree(os.path.join(b, "_workspaces", "tasks"))
    shutil.copytree(os.path.join(REAL, "_workspaces", "tasks"), os.path.join(b, "_workspaces", "tasks"))
    shutil.copytree(os.path.join(REAL, "spec"), os.path.join(b, "spec"))
    shutil.copy2(os.path.join(REAL, "CLAUDE.md"), os.path.join(b, "CLAUDE.md"))
    for d in ("specs", "tasks", "others"):          # names only: harness_check resolves spec refs by name
        src = os.path.join(REAL, "docs", "base", d)
        if os.path.isdir(src):
            for f in os.listdir(src):
                write(b, f"docs/base/{d}/{f}", "")
    rc, out = commit_all(b)
    check("B initial commit of the board copy", rc == 0 and sh(["git", "rev-parse", "HEAD"], b)[0] == 0, out[-300:])
    rc, out = tc(b, "validate")
    n = int(out.split("(")[-1].split()[0])
    base_errors = [ln for ln in out.splitlines()[:-1] if not ln.startswith("NOTE")]
    # the architect edits the real board in parallel: its transient errors are reported, not asserted
    print(f"     copy of the real board: {out.splitlines()[-1]}; pre-existing errors: {base_errors}")
    check("B validate runs on a copy of the real board without crashing", rc in (0, 1) and "Traceback" not in out, out[-300:])
    todo = os.path.join(b, "_workspaces", "tasks", "todo")
    src = [f for f in os.listdir(todo) if f.startswith("T004-")][0]
    shutil.copy2(os.path.join(todo, src), os.path.join(todo, "T999-dup.md"))
    rc, out = tc(b, "validate")
    check("A4-03 validate reports a duplicate id (and the wrong file name)", rc == 1 and "duplicate id T004" in out, out[-400:])
    rc, out = tc(b, "status")
    check("A4-03 every other command refuses a board with duplicate ids (exit 2)", rc == 2 and "duplicate id" in out, out[-300:])
    hc = [sys.executable, os.path.join(b, SCRIPTS, "harness_check.py")]
    installed = "guard.py" in open(os.path.join(REAL, ".claude", "settings.json"), encoding="utf-8").read()
    proposals = sorted(glob.glob(os.path.join(REAL, "_workspaces", "audit", "*", "proposed-settings.json")))
    if not installed:
        # the hook is opt-in (only the owner installs it): its absence is a visible WARN, not a problem
        rc, out = sh(hc, b)
        check("harness_check mentions a settings.json without the guard hook (WARN, not silenced)",
              "guard hook (guard.py) not enabled" in out
              and "PROBLEM .claude/settings.json: optional" not in out, out[-400:])
        if proposals:
            shutil.copy2(proposals[-1], os.path.join(b, "proposed-settings.json"))
            hc += ["--settings", os.path.join(b, "proposed-settings.json")]
    rc, out = sh(hc, b)
    check("harness_check reports the duplicate id", rc == 1 and "duplicate id T004" in out, out[-600:])
    os.remove(os.path.join(todo, "T999-dup.md"))

    # template with inline comments (the old SKILL.md template), malformed fields
    tpl = ("---\nid: T998\ntitle: Struct + layout # engine\nphase: P5-language\n"
           "owner: axiom-semantics            # agent that implements\nreviewer: axiom-qa\n"
           "model: opus                       # implementation model\ngate_model: sonnet                # QA gate model\n"
           "depends: [T004]   # x\npriority: 34                      # lower runs first\nstatus: todo\nattempts: 0\n"
           "paths: [bootstrap/axiom0/src/layout, tests/run/struct]   # dirs/files\n"
           "# a full-line comment\ncovers: [REQ-LAY-003]   # ids\n---\n## Goal\nx\n## Acceptance\n- t\n")
    write(b, "_workspaces/tasks/todo/T998-template.md", tpl)
    rc, out = tc(b, "lint", "_workspaces/tasks/todo/T998-template.md")
    check("A4-02 a task copied from a commented template parses (lint OK)", rc == 0, out)
    rc, out = tc(b, "validate")
    check("A4-02 board with the commented task validates (no new error, one more task)",
          f"({n + 1} tasks)" in out and "T998" not in out
          and [ln for ln in out.splitlines()[:-1] if not ln.startswith("NOTE")] == base_errors, out[-300:])
    rc, out = tc(b, "show", "T998")
    rc2, o2 = tc(b, "next", "--max", "3")
    check("A4-02 commands keep working with the commented task on the board", rc == 0 and rc2 == 0, o2)
    write(b, "_workspaces/tasks/todo/T998-template.md", tpl.replace("priority: 34", "priority: high"))
    rc, out = tc(b, "status")
    check("A4-02 malformed priority -> clear error naming the file, no traceback",
          rc == 2 and "'priority' must be an integer" in out and "T998-template.md" in out and "Traceback" not in out, out[-400:])
    write(b, "_workspaces/tasks/todo/T998-template.md", tpl.replace("depends: [T004]   # x", "depends: T004"))
    rc, out = tc(b, "validate")
    check("A4-02 depends not a list -> clear error", rc == 1 and "'depends' must be a list" in out, out[-400:])
    write(b, "_workspaces/tasks/todo/T998-template.md", tpl.replace("status: todo", "status: wip"))
    rc, out = tc(b, "validate")
    check("unknown status -> clear error", rc == 1 and "status 'wip'" in out, out[-400:])
    os.remove(os.path.join(todo, "T998-template.md"))
    write(os.path.expanduser("~"), "axiom_lint_T997-x.md", tpl.replace("T998", "T997"))
    rc, out = tc(b, "lint", os.path.join(os.path.expanduser("~"), "axiom_lint_T997-x.md"))
    os.remove(os.path.join(os.path.expanduser("~"), "axiom_lint_T997-x.md"))
    check("lint works on a file on another drive / outside the repo", "Traceback" not in out and "file name must start" in out, out)

    # stray tree detection, T224 rule, docs staged
    os.makedirs(os.path.join(b, "tools", "_workspaces", "tasks", "todo"))
    rc, out = sh(hc, b)
    check("A4-01 harness_check flags a stray _workspaces tree", "stray directory tools/_workspaces" in out, out[-600:])
    shutil.rmtree(os.path.join(b, "tools"))
    write(b, "docs/base/specs/owner-new.md", "x\n")
    sh(["git", "add", "-f", "docs/base/specs/owner-new.md"], b)
    rc, out = sh(hc, b)
    check("harness_check flags a staged docs/ file", "owner file staged: docs/base/specs/owner-new.md" in out, out[-600:])
    sh(["git", "restore", "--staged", "docs/base/specs/owner-new.md"], b)
    os.remove(os.path.join(b, "docs/base/specs/owner-new.md"))
    rc, out = sh(hc, b)
    own = [ln for ln in out.splitlines() if ln.startswith("PROBLEM")
           and (installed or proposals or ".claude/settings.json" not in ln)]
    check("harness_check on the clean copy (installed or proposed settings): no problems, hook run end-to-end",
          not own and "not exercised" not in out, out[-600:])
    print("     harness_check(B copy) last line:", out.splitlines()[-1] if out else "")
    rc, out = sh(hc, os.path.join(b, "spec"))
    check("A4-01 harness_check from a subdirectory checks the same repo", "stray" not in out and "0 tasks" not in out, out[-300:])


# =============================================================== repo C (roots, empty, stuck, finished)
def test_c():
    c = new_repo("C")
    commit_all(c)
    rc, out = tc(c, "status")
    check("A4-01 empty board is an error (exit 2), never 'board finished'",
          rc == 2 and "0 tasks" in out and "finished" not in out.replace("never treat this as 'board finished'", ""), out)
    rc, out = tc(c, "validate")
    check("validate fails on an empty board", rc == 1, out)
    rc, out = sh([sys.executable, os.path.join(c, SCRIPTS, "reqcov.py"), "--strict", "--allow-missing"], c)
    check("reqcov refuses an empty board", rc == 2, out)
    # scripts without any board next to them and cwd outside a repo
    lone = os.path.join(TR, "lone", SCRIPTS)
    os.makedirs(lone)
    shutil.copy2(os.path.join(REAL, SCRIPTS, "taskctl.py"), lone)
    rc, out = sh([sys.executable, os.path.join(lone, "taskctl.py"), "status"], os.path.expanduser("~"))
    check("A4-01 no board found -> exit 2 'cannot locate', nothing created",
          rc == 2 and "cannot locate" in out and not os.path.exists(os.path.join(TR, "lone", "_workspaces")), out)

    T = "_workspaces/tasks/todo/"
    write(c, T + "T001-a.md", task("T001", 20, [], ["a"]))
    write(c, T + "T002-b.md", task("T002", 21, ["T001"], ["b"]))
    write(c, T + "T224-eco.md", task("T224", 90, [], ["eco"], status="deferred"))
    commit_all(c, "board")
    ap(c, "init", "--cron", "c1")
    rc, out = ap(c, "check-board")
    check("check-board: work remains -> exit 1", rc == 1, out)
    tc(c, "park", "T001", "--reason", "needs the owner")
    rc, out = tc(c, "stuck", "--write")
    check("A4-23 stuck: diagnosis written to _workspaces/STUCK.md (exit 3)",
          rc == 3 and "T002 Task T002: waits for T001 (parked)" in out
          and os.path.exists(os.path.join(c, "_workspaces", "STUCK.md")), out)
    check("STUCK.md is git-ignored", "STUCK" not in status(c), status(c))
    rc, out = ap(c, "stuck"); rc, out = ap(c, "stuck")
    check("autopilot stuck counter", out.strip() == "2", out)
    tc(c, "unblock", "T001", "--owner-approved")
    rc, out = tc(c, "stuck")
    check("not stuck once the parked task is released", rc == 0, out)
    for i in ("T001", "T002"):
        tc(c, "start", i)
        write(c, f"{i[-1]}/f.txt".replace("1", "a").replace("2", "b"), "x\n")
        p = "a/f.txt" if i == "T001" else "b/f.txt"
        write(c, f"_workspaces/reports/{i}-report.md", f"## Files changed\n- {p}\n\nSTATUS: COMPLETE round=0\n")
        write(c, f"_workspaces/reports/{i}-qa.md", "VERDICT: PASS\n")
        rc, out = tc(c, "accept", i)
    rc, out = ap(c, "check-board")
    check("check-board: all done, only deferred left -> finished (exit 0)", rc == 0 and "finished" in out, out)
    os.remove([os.path.join(c, "_workspaces/tasks/done", f) for f in os.listdir(os.path.join(c, "_workspaces/tasks/done"))
               if f.startswith("T002")][0])
    rc, out = ap(c, "check-board")
    check("A4-01 check-board: fewer tasks than recorded -> exit 2, not finished", rc == 2 and "vanished" in out, out)

    # guard inside this temp repo: protects ITS docs/, allows the rest
    g = [sys.executable, os.path.join(c, ".claude", "hooks", "guard.py")]
    rc, out = sh(g + ["--selftest"], c)
    check("guard selftest (95 allow/deny cases) in a temp repo", rc == 0, out)
    write(c, "docs/base/owner.md", "changed\n")
    for cmd, want in (("git add -A", 1), ("git add .", 1), ("git commit -am x", 1), ("git reset --hard", 1),
                      ("git checkout -- .", 1), ("git stash", 1), ("git clean -fd", 0), ("git add a b", 0),
                      ("git reset -q", 0), ("git commit -m x", 0), ("git stash list", 0)):
        rc, out = sh(g + ["--check", cmd], c)
        check(f"guard with dirty docs/: `{cmd}` -> {'deny' if want else 'allow'}", rc == want, out)
    write(c, "docs/untracked-owner-note.md", "x\n")
    rc, out = sh(g + ["--check", "git clean -fd"], c)
    check("guard: `git clean -fd` denied while docs/ has untracked owner files", rc == 1, out)
    rc, out = sh(g + ["--check", "git clean -fd -- build"], c)
    check("guard: `git clean` limited to another directory allowed", rc == 0, out)
    sh(["git", "add", "-f", "docs/untracked-owner-note.md"], c)
    rc, out = sh(g + ["--check", "git commit -m x"], c)
    check("guard: any `git commit` denied while docs/ is staged", rc == 1 and "staged" in out, out)
    sh(["git", "restore", "--staged", "docs/untracked-owner-note.md"], c)
    sh(["git", "checkout", "--", "docs"], c)
    os.remove(os.path.join(c, "docs/untracked-owner-note.md"))
    for cmd in ("git add -A", "git commit -am x", "git reset --hard", "git stash"):
        rc, out = sh(g + ["--check", cmd], c)
        check(f"guard with clean docs/: `{cmd}` allowed (never blocks legitimate work)", rc == 0, out)


def main():
    rmtree(TR)
    os.makedirs(TR)
    a = build_a()
    test_a(a)
    test_b()
    test_c()
    bad = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} checks passed")
    for n in bad:
        print("FAILED:", n)
    if "--keep" in sys.argv:
        print("kept:", TR)
    else:
        for name in ("A", "B", "C"):  # drop snapshot worktrees cleanly before deleting
            sh(["git", "worktree", "prune"], os.path.join(TR, name))
        rmtree(TR)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
