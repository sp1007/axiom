#!/usr/bin/env python3
"""harness_check — consistency checks for the Axiom harness itself.

Usage: python .claude/skills/axiom-tasks/scripts/harness_check.py   (exit 1 on problems)
       python .claude/skills/axiom-tasks/scripts/harness_check.py --settings <proposed-settings.json>
The repo root is found like taskctl (script location / git top level), never from the cwd alone.
`.claude/settings.json` (permissions, hooks) is changed only by the owner or with the owner's explicit
approval: agents put a proposal next to their report and verify it with --settings.

Checks: board validity (duplicate ids, front-matter types, status vs directory, file name = id),
phase/roadmap rules (core tasks never depend on post-self-host tasks, post-self-host tasks never edit
bootstrap/axiom0, axiom0 freeze after the `axiom0-frozen` tag, T224 stays deferred), the task template
in axiom-tasks parses, skills/agents front-matter, cross references to skills, agents and taskctl /
autopilot commands, task ids named in skills/agents exist, settings.json guard rails, stray
`_workspaces` trees (wrong-cwd runs), CRLF in harness files, owner files never staged, stale phrases
from superseded rules. WARN lines do not fail the check.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import taskctl  # noqa: E402

ROOT = taskctl.ROOT
problems, warns = [], []


def p(msg):
    problems.append(msg)


def phase_num(t):
    m = re.match(r"P(\d+)", t["meta"].get("phase", ""))
    return int(m.group(1)) if m else -1


def rel(f):
    return os.path.relpath(f, ROOT).replace("\\", "/")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


# --- board -------------------------------------------------------------------
board_errors = []
tasks = taskctl.load_all(board_errors)
for e in board_errors:
    p(f"board: {e}")
ids = set(tasks)
corpus = {d: os.listdir(os.path.join(ROOT, "docs", "base", d))
          for d in ("specs", "tasks", "others") if os.path.isdir(os.path.join(ROOT, "docs", "base", d))}
for tid, t in tasks.items():
    m = t["meta"]
    for key in ("id", "title", "phase", "owner", "priority", "status", "paths"):
        if key not in m:
            p(f"{tid}: missing front-matter '{key}'")
    for d in m.get("depends", []):
        if d not in ids:
            p(f"{tid}: unknown dependency {d}")
            continue
        if 0 <= phase_num(t) <= 10 and phase_num(tasks[d]) > 10:
            p(f"{tid} (core) depends on post-self-host task {d}")
    if phase_num(t) > 10 and any(x.startswith("bootstrap/axiom0") for x in m.get("paths", []) + m.get("locks", [])):
        p(f"{tid}: post-self-host task edits bootstrap/axiom0 (ROADMAP R3)")
    if 0 <= phase_num(t) <= 9 and any(x.startswith("compiler/") for x in m.get("paths", [])):
        p(f"{tid}: pre-P10 task edits compiler/ (Axiom compiler starts in P10)")
    if any(x.startswith("docs") for x in m.get("paths", []) + m.get("locks", [])):
        p(f"{tid}: paths include the owner's docs/ (never edited by the harness)")
    owner = m.get("owner", "")
    if owner and not os.path.exists(os.path.join(ROOT, ".claude", "agents", owner + ".md")):
        p(f"{tid}: owner '{owner}' has no agent file")
    for key in ("model", "gate_model"):
        if m.get(key) not in ("opus", "sonnet"):
            p(f"{tid}: {key} must be opus or sonnet (got {m.get(key)!r})")
    if "## Acceptance" not in t["body"]:
        p(f"{tid}: no Acceptance section")
    # spec refs: plain NNNN = docs/base/specs, tasks/NNNN = docs/base/tasks, others/NNNN = docs/base/others
    for s in m.get("spec", []):
        mm = re.fullmatch(r"(?:(tasks|others)/)?(\d{4})", s)
        if mm and not any(f.startswith(mm.group(2)) for f in corpus.get(mm.group(1) or "specs", [])):
            p(f"{tid}: spec ref {s} not found in docs/base/{mm.group(1) or 'specs'}")
for tid in ("T224", "T324"):  # post-v1 ecosystem planning task and its gate
    if tid in tasks and tasks[tid]["meta"].get("status") != "deferred":
        p(f"{tid} must stay deferred (post-v1 ecosystem; only the owner schedules it)")

# roadmap epics referenced by task titles exist
roadmap = open(os.path.join(ROOT, "spec", "ROADMAP.md"), encoding="utf-8").read()
for tid, t in tasks.items():
    mm = re.match(r"(E\d+\.\d+) ", t["meta"].get("title", ""))
    if mm and f"**{mm.group(1)} " not in roadmap:
        p(f"{tid}: title epic {mm.group(1)} not in ROADMAP")

# axiom0 freeze (ROADMAP R3): after the tag, only commits whose subject names an AX0-FIX task
if git("rev-parse", "-q", "--verify", "refs/tags/axiom0-frozen").returncode == 0:
    for line in git("log", "--format=%h %s", "axiom0-frozen..HEAD", "--", "bootstrap/axiom0").stdout.splitlines():
        if "AX0-FIX" not in line:
            p(f"axiom0 frozen (tag axiom0-frozen) but commit touches bootstrap/axiom0: {line}")
    if git("status", "--porcelain", "--", "bootstrap/axiom0").stdout.strip():
        warns.append("uncommitted changes under frozen bootstrap/axiom0 (allowed only for an AX0-FIX task)")

# --- skills / agents ---------------------------------------------------------
skills_dir = os.path.join(ROOT, ".claude", "skills")
skills = {s for s in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, s))}
for s in sorted(skills):
    if not os.path.exists(os.path.join(skills_dir, s, "SKILL.md")):
        p(f".claude/skills/{s}: no SKILL.md")
skills = {s for s in skills if os.path.exists(os.path.join(skills_dir, s, "SKILL.md"))}
agents = {f[:-3] for f in os.listdir(os.path.join(ROOT, ".claude", "agents")) if f.endswith(".md")}
docs = [os.path.join(ROOT, ".claude", "skills", s, "SKILL.md") for s in skills] + \
       [os.path.join(ROOT, ".claude", "agents", a + ".md") for a in agents]
TASKCTL_CMDS = set(re.findall(r"^    ([a-z][a-z-]+)(?= )", taskctl.__doc__, re.M))
autopilot_doc = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "autopilot.py"),
                     encoding="utf-8").read()
AUTOPILOT_CMDS = set(re.findall(r"^    ([a-z][a-z-]+)(?=[ \n])", autopilot_doc.split('"""')[1], re.M))
PLACEHOLDER_IDS = {"T123", "T999"}
for f in docs:
    text = open(f, encoding="utf-8").read()
    fm = text.split("---")[1] if text.startswith("---\n") else ""
    mm = re.search(r"\nmodel:\s*(\S+)", fm)
    if mm and mm.group(1) not in ("opus", "sonnet", "haiku", "inherit"):
        p(f"{rel(f)}: invalid model '{mm.group(1)}'")
    if not text.startswith("---\n") or "\nname:" not in text.split("---")[1] or "\ndescription:" not in text.split("---")[1]:
        p(f"{rel(f)}: bad front-matter")
    for ref in set(re.findall(r"`((?:axiom-[a-z0-9-]+)|tu-dong)`", text)):
        if ref not in skills and ref not in agents:
            p(f"{rel(f)}: reference to unknown skill/agent `{ref}`")
    for c in set(re.findall(r"taskctl(?:\.py)? ([a-z][a-z-]+)\b", text)):
        if c not in TASKCTL_CMDS:
            p(f"{rel(f)}: unknown taskctl command '{c}'")
    for c in set(re.findall(r"autopilot\.py ([a-z][a-z-]+)\b", text)):
        if c not in AUTOPILOT_CMDS:
            p(f"{rel(f)}: unknown autopilot.py command '{c}'")
    # id ranges ("T112–T199", "T400–T449") describe reserved blocks, not tasks that must exist
    no_ranges = re.sub(r"`?\bT\d{3,4}[a-z]?`?\s*[–-]\s*`?T\d{3,4}[a-z]?\b`?", " ", text)
    for tid in set(re.findall(r"\bT\d{3}[a-z]?\b", no_ranges)):
        if tid not in ids and tid not in PLACEHOLDER_IDS:
            p(f"{rel(f)}: names task {tid}, which is not on the board")
if os.path.isdir(os.path.join(ROOT, ".claude", "commands")):
    p(".claude/commands exists (harness uses skills as commands)")

# the task template in axiom-tasks must parse cleanly (planning tasks copy it)
tpl_src = open(os.path.join(skills_dir, "axiom-tasks", "SKILL.md"), encoding="utf-8").read()
tpl = re.search(r"```markdown\n(---\n.*?\n---\n.*?)```", tpl_src, re.S)
if not tpl:
    p("axiom-tasks SKILL.md: task template block not found")
else:
    tmp_meta = {}
    for line in tpl.group(1).split("---\n")[1].splitlines():
        if "#" in line:
            p(f"axiom-tasks SKILL.md: task template front-matter line carries a comment: {line.strip()}")
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            fn = os.path.join(d, "T034-template.md")
            with open(fn, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(tpl.group(1))
            tmp_meta, _ = taskctl.parse(fn)
            for e in taskctl.check_meta(tmp_meta, fn, "todo"):
                p(f"axiom-tasks SKILL.md template: {e}")
    except ValueError as e:
        p(f"axiom-tasks SKILL.md template: {e}")
if "STATUS: COMPLETE" not in tpl_src:
    p("axiom-tasks SKILL.md: report format lacks the 'STATUS: COMPLETE round=<n>' marker")
comp = open(os.path.join(skills_dir, "axiom-compiler", "SKILL.md"), encoding="utf-8").read()
for needle, why in (("STATUS: COMPLETE", "impl prompt must require the report STATUS marker"),
                    ("taskctl.py accept", "PASS must go through `taskctl accept` (atomic)"),
                    ("taskctl.py snapshot", "QA must build from the task snapshot"),
                    ("unblock-begin", "unblocks must take the unblock lock"),
                    ("--infra", "infrastructure failures must not burn attempts")):
    if needle not in comp:
        p(f"axiom-compiler SKILL.md: {why} (missing '{needle}')")
tick = open(os.path.join(skills_dir, "axiom-tick", "SKILL.md"), encoding="utf-8").read()
for needle in ("reconcile", "autopilot.py session", "overdue.py", "stuck", "backoff", "check-board",
               "taskctl.py recover", "unblock-begin"):
    if needle not in tick:
        p(f"axiom-tick SKILL.md: missing step for '{needle}'")
tudong = open(os.path.join(skills_dir, "tu-dong", "SKILL.md"), encoding="utf-8").read()
for needle in ("autopilot.py init", "check-board", "--infra"):
    if needle not in tudong:
        p(f"tu-dong SKILL.md: missing '{needle}'")
thamdinh = open(os.path.join(skills_dir, "tham-dinh", "SKILL.md"), encoding="utf-8").read()
if "Quyết định đã tự áp dụng" not in thamdinh:
    p("tham-dinh SKILL.md: must record decisions under '## Quyết định đã tự áp dụng' (decide and report)")
# agent files must match the harness contract (edited by the architect, checked here)
for agent, needle, why in (
        ("axiom-qa", "build-snap-", "the gate must build and test only in the task snapshot"),
        ("axiom-qa", "round=", "the verdict line must carry the round (VERDICT: PASS round=<n>)"),
        ("axiom-architect", "adr-next", "ADR numbers are reserved with `taskctl adr-next`")):
    f = os.path.join(ROOT, ".claude", "agents", agent + ".md")
    if os.path.exists(f) and needle not in open(f, encoding="utf-8").read():
        p(f".claude/agents/{agent}.md: {why} (missing '{needle}')")

# --- settings / gitignore guard rails -------------------------------------------
def git_bash():
    """The bash that runs hook commands (Git Bash on Windows), or None."""
    cands = [os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")]
    if os.name == "nt":
        d = git("--exec-path").stdout.strip()
        for _ in range(4):
            d = os.path.dirname(d)
            cands.append(os.path.join(d, "bin", "bash.exe"))
    else:
        import shutil
        cands.append(shutil.which("bash"))
    return next((c for c in cands if c and os.path.isfile(c)), None)


def check_guard(commands):
    """The safety hook must refuse the owner's hard limits, allow normal work, and fail open."""
    guard = os.path.join(ROOT, ".claude", "hooks", "guard.py")
    if not os.path.isfile(guard):
        p(".claude/hooks/guard.py missing")
        return
    r = subprocess.run([sys.executable, guard, "--selftest"], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        p("guard.py --selftest failed: " + " | ".join((r.stdout + r.stderr).strip().splitlines()[-4:]))
    if not commands:
        return  # "not configured" is already reported
    bash = git_bash()
    if not bash:
        warns.append("guard hook command not exercised end-to-end (no Git Bash found)")
        return
    import tempfile

    def run(cmd, payload, project_dir, cwd):
        env = dict(os.environ, AXIOM_GUARD_NOLOG="1")
        env.pop("CLAUDE_PROJECT_DIR", None)
        if project_dir:
            env["CLAUDE_PROJECT_DIR"] = project_dir
        return subprocess.run([bash, "-c", cmd], input=json.dumps(payload).encode("utf-8"), cwd=cwd, env=env,
                              capture_output=True, timeout=60)

    push = {"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}, "cwd": ROOT}
    edit = {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(ROOT, "docs", "x.md")}, "cwd": ROOT}
    okay = {"tool_name": "Bash", "tool_input": {"command": "git status --short"}, "cwd": ROOT}
    with tempfile.TemporaryDirectory() as elsewhere:
        for cmd in commands:
            for name, payload in (("git push --force", push), ("Edit under docs/", edit)):
                out = run(cmd, payload, ROOT, elsewhere)
                if b'"permissionDecision": "deny"' not in out.stdout or out.returncode == 2:
                    p(f"guard hook does not refuse {name} when run as configured: {cmd}")
            out = run(cmd, okay, ROOT, elsewhere)
            if out.stdout.strip() or out.returncode != 0:
                p(f"guard hook interferes with a harmless command (rc {out.returncode}): {cmd}")
            out = run(cmd, push, os.path.join(elsewhere, "missing dir"), elsewhere)
            if out.returncode == 2:
                p("guard hook command exits 2 when guard.py cannot be found: it would block every tool "
                  "call (must fail open)")


SETTINGS = os.path.join(ROOT, ".claude", "settings.json")
if "--settings" in sys.argv:  # check a proposed settings file before the owner installs it
    SETTINGS = os.path.abspath(sys.argv[sys.argv.index("--settings") + 1])
try:
    settings = json.load(open(SETTINGS, encoding="utf-8"))
    perms = settings.get("permissions", {})
    for rule in ("Edit(docs/**)", "Write(docs/**)", "Bash(git push --force:*)", "Bash(git push -f:*)",
                 "PowerShell(git push --force:*)", "PowerShell(git push -f:*)"):
        if rule not in perms.get("deny", []):
            p(f".claude/settings.json: deny rule {rule} missing")
    for tool in ("TaskStop", "ToolSearch", "SendMessage", "CronCreate", "CronDelete", "CronList"):
        if tool not in perms.get("allow", []):
            p(f".claude/settings.json: allow {tool} missing (a prompt would stall the unattended loop)")
    hooks = json.dumps(settings.get("hooks", {}))
    if "guard.py" not in hooks:
        # Opt-in: a hook runs on every tool call, so only the owner installs it (the deny rules
        # above stay in force without it). Once configured, it is verified end to end below.
        warns.append(".claude/settings.json: optional PreToolUse guard hook (guard.py) not enabled "
                     "— the owner can enable it from _workspaces/audit/2026-09-30/proposed-settings.json")
    guard_cmds = []
    for grp in settings.get("hooks", {}).get("PreToolUse", []):
        mine = [h.get("command", "") for h in grp.get("hooks", []) if "guard.py" in json.dumps(h)]
        if mine:
            guard_cmds += mine
            for tool in ("Edit", "Write", "Bash", "PowerShell"):
                if tool not in re.split(r"[|,\s]+", grp.get("matcher", "")):
                    p(f".claude/settings.json: guard hook matcher does not cover {tool}")
    check_guard(guard_cmds)
except (OSError, ValueError) as e:
    p(f".claude/settings.json unreadable: {e}")
gi = open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read()
for pat in ("_workspaces/locks/", "_workspaces/autopilot.json", "build-*/"):
    if pat not in gi:
        p(f".gitignore: {pat} missing")

# --- stray _workspaces trees (a script run from the wrong cwd) --------------------
for d, dirs, _ in os.walk(ROOT):
    dirs[:] = [x for x in dirs if x not in (".git", "docs", "node_modules") and not x.startswith("build")]
    if d.count(os.sep) - ROOT.count(os.sep) > 5:
        dirs[:] = []
        continue
    for x in dirs:
        full = os.path.join(d, x)
        if x == "_workspaces" and os.path.normpath(full) != os.path.normpath(os.path.join(ROOT, "_workspaces")):
            p(f"stray directory {rel(full)} (created by a wrong-cwd run; delete it)")

# --- line endings --------------------------------------------------------------
for base in (".claude", "spec", "_workspaces/tasks", "CLAUDE.md", ".gitattributes", ".gitignore"):
    path = os.path.join(ROOT, base)
    files = [path] if os.path.isfile(path) else [os.path.join(d, f) for d, _, fs in os.walk(path) for f in fs]
    for f in files:
        if f.endswith((".md", ".py", ".txt", ".json")) or os.path.basename(f).startswith("."):
            data = open(f, "rb").read()
            if b"\r" in data:
                p(f"CR characters (CRLF or stray \\r): {rel(f)}")
            # an escaped \n that a shell turned into a real line break: `<LF>`
            if f.endswith(".md") and re.search(rb"[^`]`\n`[^`]", data):
                p(f"broken inline-code escape (`<newline>`): {rel(f)}")

# --- owner files never staged or edited --------------------------------------------
staged = git("diff", "--cached", "--name-only").stdout.split("\n")
for f in staged:
    if f.startswith("docs/"):
        p(f"owner file staged: {f} (unstage with `git restore --staged {f}`)")
if git("status", "--porcelain", "--", "docs").stdout.strip():
    warns.append("docs/ has uncommitted changes — fine if the owner made them; the harness never edits docs/")

# --- stale phrases from superseded decisions -----------------------------------------
STALE = [r"doing/ is (now )?empty", r"only when doing", r"T092-T108", r"\bP11a\b", r"Linux ELF first",
         r"x86_64-linux first", r"\bT065a\b", r"\bT065b\b", r"\*/5 \* \* \* \*", r"5-minute",
         r"every 5 minutes", r"mỗi 5 phút", r"no completion yet", r"without git worktrees",
         r"finish <ID>` → `taskctl\.py commit", r"T002, T004 in parallel",
         r"Cần chủ dự án quyết định", r"Ask only those decisions", r"NEEDS OWNER DECISION",
         r"next free number — list the directory"]
for base in (".claude", "spec", "_workspaces/tasks", "CLAUDE.md"):
    path = os.path.join(ROOT, base)
    files = [path] if os.path.isfile(path) else [os.path.join(d, f) for d, _, fs in os.walk(path) for f in fs]
    for f in files:
        # a real line break right after newline=" (shell-escaping accident) breaks the LF advice
        if f.endswith((".md", ".py")) and "harness_check" not in f and \
                re.search(r'newline="\n', open(f, encoding="utf-8").read()):
            p(f"broken newline literal in {rel(f)}")
        if not f.endswith(".md") or "harness_check" in f:
            continue
        for n, line in enumerate(open(f, encoding="utf-8"), 1):
            for rx in STALE:
                if re.search(rx, line) and "replaced" not in line:
                    p(f"stale phrase /{rx}/ in {rel(f)}:{n}")
# "hello world" allowed only when stating it is not used
for d, _, fs in os.walk(os.path.join(ROOT, "_workspaces", "tasks")):
    for f in fs:
        if re.search(r"hello world", open(os.path.join(d, f), encoding="utf-8").read(), re.I):
            p(f"'hello world' in task {f} — use 'Xin chào thế giới'")

for x in warns:
    print("WARN", x)
for x in problems:
    print("PROBLEM", x)
print("HARNESS OK" if not problems else f"HARNESS: {len(problems)} problems")
sys.exit(1 if problems else 0)
