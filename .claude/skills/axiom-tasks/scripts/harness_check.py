#!/usr/bin/env python3
"""harness_check — consistency checks for the Axiom harness itself.

Usage: python .claude/skills/axiom-tasks/scripts/harness_check.py   (exit 1 on problems)

Checks: board validity, phase/roadmap rules (core tasks never depend on post-self-host tasks, post-
self-host tasks never edit bootstrap/axiom0), skills/agents front-matter, cross references to skills
and agents, CRLF in harness files, owner files never staged, stale phrases from superseded rules.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import taskctl  # noqa: E402

ROOT = os.getcwd()
problems = []


def p(msg):
    problems.append(msg)


def phase_num(t):
    m = re.match(r"P(\d+)", t["meta"].get("phase", ""))
    return int(m.group(1)) if m else -1


# --- board -------------------------------------------------------------------
tasks = taskctl.load_all()
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
    if phase_num(t) > 10 and any(x.startswith("bootstrap/axiom0") for x in m.get("paths", [])):
        p(f"{tid}: post-self-host task edits bootstrap/axiom0 (ROADMAP R3)")
    if 0 <= phase_num(t) <= 9 and any(x.startswith("compiler/") for x in m.get("paths", [])):
        p(f"{tid}: pre-P10 task edits compiler/ (Axiom compiler starts in P10)")
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

# roadmap epics referenced by task titles exist
roadmap = open(os.path.join(ROOT, "spec", "ROADMAP.md"), encoding="utf-8").read()
for tid, t in tasks.items():
    mm = re.match(r"(E\d+\.\d+) ", t["meta"].get("title", ""))
    if mm and f"**{mm.group(1)} " not in roadmap:
        p(f"{tid}: title epic {mm.group(1)} not in ROADMAP")

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
for f in docs:
    text = open(f, encoding="utf-8").read()
    fm = text.split("---")[1] if text.startswith("---\n") else ""
    mm = re.search(r"\nmodel:\s*(\S+)", fm)
    if mm and mm.group(1) not in ("opus", "sonnet", "haiku", "inherit"):
        p(f"{os.path.relpath(f, ROOT)}: invalid model '{mm.group(1)}'")
    if not text.startswith("---\n") or "\nname:" not in text.split("---")[1] or "\ndescription:" not in text.split("---")[1]:
        p(f"{os.path.relpath(f, ROOT)}: bad front-matter")
    for ref in set(re.findall(r"`((?:axiom-[a-z0-9-]+)|tu-dong)`", text)):
        if ref not in skills and ref not in agents:
            p(f"{os.path.relpath(f, ROOT)}: reference to unknown skill/agent `{ref}`")
if os.path.isdir(os.path.join(ROOT, ".claude", "commands")):
    p(".claude/commands exists (harness uses skills as commands)")

# --- line endings --------------------------------------------------------------
for base in (".claude", "spec", "_workspaces/tasks", "CLAUDE.md", ".gitattributes"):
    path = os.path.join(ROOT, base)
    files = [path] if os.path.isfile(path) else [os.path.join(d, f) for d, _, fs in os.walk(path) for f in fs]
    for f in files:
        if f.endswith((".md", ".py", ".txt")) or os.path.basename(f).startswith("."):
            data = open(f, "rb").read()
            if b"\r" in data:
                p(f"CR characters (CRLF or stray \\r): {os.path.relpath(f, ROOT)}")
            # an escaped \n that a shell turned into a real line break: `<LF>`
            if f.endswith(".md") and re.search(rb"[^`]`\n`[^`]", data):
                p(f"broken inline-code escape (`<newline>`): {os.path.relpath(f, ROOT)}")

# --- owner files never staged ------------------------------------------------------
staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT,
                        capture_output=True, text=True).stdout.split()
for f in staged:
    if f.startswith("docs/"):
        p(f"owner file staged: {f} (unstage with `git restore --staged {f}`)")

# --- stale phrases from superseded decisions -----------------------------------------
STALE = [r"doing/ is (now )?empty", r"only when doing", r"T092-T108", r"\bP11a\b", r"Linux ELF first",
         r"x86_64-linux first", r"\bT065a\b", r"\bT065b\b"]
for base in (".claude", "spec", "_workspaces/tasks", "CLAUDE.md"):
    path = os.path.join(ROOT, base)
    files = [path] if os.path.isfile(path) else [os.path.join(d, f) for d, _, fs in os.walk(path) for f in fs]
    for f in files:
        # a real line break right after newline=" (shell-escaping accident) breaks the LF advice
        if f.endswith((".md", ".py")) and "harness_check" not in f and \
                re.search(r'newline="\n', open(f, encoding="utf-8").read()):
            p(f"broken newline literal in {os.path.relpath(f, ROOT)}")
        if not f.endswith(".md") or "harness_check" in f:
            continue
        for n, line in enumerate(open(f, encoding="utf-8"), 1):
            for rx in STALE:
                if re.search(rx, line) and "replaced" not in line:
                    p(f"stale phrase /{rx}/ in {os.path.relpath(f, ROOT)}:{n}")
    # "hello world" allowed only when stating it is not used
for d, _, fs in os.walk(os.path.join(ROOT, "_workspaces", "tasks")):
    for f in fs:
        if re.search(r"hello world", open(os.path.join(d, f), encoding="utf-8").read(), re.I):
            p(f"'hello world' in task {f} — use 'Xin chào thế giới'")

for x in problems:
    print("PROBLEM", x)
print("HARNESS OK" if not problems else f"HARNESS: {len(problems)} problems")
sys.exit(1 if problems else 0)
