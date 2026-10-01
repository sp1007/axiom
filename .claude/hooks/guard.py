#!/usr/bin/env python3
"""guard — PreToolUse safety hook of the Axiom harness (configured in .claude/settings.json).

Hard rules of the project owner, enforced for the main session and every subagent:
    1. docs/ belongs to the owner: never edited, moved, deleted, re-encoded or created by the harness.
    2. Nothing is ever pushed (git push in any form, gh publishing commands).
    3. docs/ is never staged or committed (git add / commit / rm / mv on docs/, and broad forms such
       as `git add -A` or `git commit -a` while docs/ has changes).
    4. Broad destructive git commands (reset --hard, checkout/restore of ".", clean, stash) are
       refused while docs/ has uncommitted changes, because they would destroy the owner's edits.

Everything else is allowed: reading docs/ (cat, grep, ls, python scripts that read it), copying
FROM docs/, every taskctl/autopilot command, builds, tests, commits of listed files.

Protocol: reads the hook JSON on stdin; to refuse it prints a JSON `permissionDecision: deny` object
and exits 0. It never exits 2 and any internal error allows the call (fail open) — a broken guard
must not stall the unattended loop. Refusals are appended to _workspaces/logs/guard.log.

Limits (a guard rail, not a sandbox): it analyses shell text. A script or `python -c` program that
writes into docs/ by itself is not seen; taskctl never stages docs/ and harness_check reports
changes under docs/, which covers that case after the fact.

Manual use:
    python .claude/hooks/guard.py --check "<command>" [--tool Bash|PowerShell] [--cwd DIR]
    python .claude/hooks/guard.py --check-file <path> [--cwd DIR]
    python .claude/hooks/guard.py --selftest          (exit 1 when a case fails)
"""
import datetime
import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OWNER_DIR = "docs"

FILE_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path",
              "NotebookEdit": "notebook_path"}
SHELL_TOOLS = {"Bash": False, "PowerShell": True}

SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", "|&", ";;"}
SKIP_WORDS = {"{", "}", "do", "then", "else", "elif", "if", "while", "until", "!", "time", "sudo",
              "exec", "command", "nohup", "env", "builtin", "start-process", "call"}
CD_VERBS = {"cd", "pushd", "chdir", "set-location", "sl", "push-location"}
# verbs that modify every path argument they are given
WRITE_VERBS = {"rm", "rmdir", "del", "erase", "rd", "ri", "remove-item", "touch", "truncate", "mkdir",
               "md", "new-item", "ni", "chmod", "chown", "clear-content", "clc", "rename-item", "rni",
               "ren", "rename", "mv", "move", "move-item", "mi", "set-content", "add-content", "ac",
               "out-file", "tee", "tee-object", "shred", "unlink", "attrib", "icacls", "takeown",
               "dos2unix", "unix2dos", "set-itemproperty", "dd", "export-csv", "export-clixml"}
# verbs that write only to their destination (last argument or an explicit destination option)
COPY_VERBS = {"cp", "copy", "copy-item", "cpi", "xcopy", "install", "ln", "rsync", "scp", "mklink"}
OUTPUT_OPT_VERBS = {"curl": {"-o", "--output"}, "wget": {"-O", "-P", "--output-document"},
                    "iconv": {"-o", "--output"}, "sort": {"-o", "--output"}, "tar": {"-C", "--directory"},
                    "unzip": {"-d"}, "invoke-webrequest": {"-outfile"}, "iwr": {"-outfile"},
                    "cmake": {"-B"}, "pandoc": {"-o", "--output"}}
NESTED_SHELLS = {"bash", "sh", "zsh", "dash", "cmd", "powershell", "pwsh", "wsl"}
NESTED_FLAGS = {"-c", "-lc", "-ic", "/c", "/k", "-command", "-encodedcommand"}
GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix",
                  "--config-env"}
COMMIT_VALUE_OPTS = {"-m", "-F", "-C", "-c", "-t", "--message", "--file", "--author", "--date",
                     "--reuse-message", "--reedit-message", "--template", "--fixup", "--squash",
                     "--cleanup", "--pathspec-from-file", "--trailer", "-S"}
GH_PUBLISH = {("pr", "create"), ("pr", "merge"), ("repo", "create"), ("repo", "sync"),
              ("release", "create"), ("release", "upload"), ("gist", "create"), ("repo", "fork")}


class Deny(Exception):
    pass


# ---------------------------------------------------------------- paths

def _canon(path):
    return os.path.normcase(os.path.normpath(path))


DOCS = _canon(os.path.join(ROOT, OWNER_DIR))
ROOT_C = _canon(ROOT)


def resolve(tok, cwd):
    """Absolute, normalised form of a path token as the shell would see it (best effort)."""
    t = tok.strip().strip("'\"").replace("\\", "/")
    if not t:
        return None
    m = re.match(r"^/([A-Za-z])(/.*)?$", t)  # Git Bash /d/x -> D:/x
    if m and os.name == "nt":
        t = m.group(1).upper() + ":" + (m.group(2) or "/")
    m = re.match(r"^/(?:mnt|cygdrive)/([A-Za-z])(/.*)?$", t)
    if m and os.name == "nt":
        t = m.group(1).upper() + ":" + (m.group(2) or "/")
    if t.startswith(":/"):  # git pathspec magic: repository root
        t = os.path.join(ROOT, t[2:])
    if not os.path.isabs(t) and not re.match(r"^[A-Za-z]:", t):
        t = os.path.join(cwd, t)
    return _canon(t)


def in_docs(tok, cwd):
    p = resolve(tok, cwd)
    if not p:
        return False
    # glob tails such as docs/* or docs/** still start with the directory
    return p == DOCS or p.startswith(DOCS + os.sep)


def covers_docs(tok, cwd):
    """True when a pathspec names docs/ itself, something inside it, or a directory above it."""
    p = resolve(re.sub(r"[*?].*$", "", tok.strip().strip("'\"")) or ".", cwd)
    if not p:
        return False
    return p == DOCS or p.startswith(DOCS + os.sep) or DOCS.startswith(p.rstrip(os.sep) + os.sep)


def any_docs(args, cwd):
    for a in args:
        if a.startswith("-") and "=" not in a:
            continue
        cands = [a]
        if "=" in a:
            cands.append(a.split("=", 1)[1])
        if ":" in a and not re.match(r"^[A-Za-z]:", a):
            cands.append(a.split(":", 1)[1])  # -Path:docs\x
        for c in cands:
            if in_docs(c, cwd):
                return c
    return None


# ---------------------------------------------------------------- git state

def _git(cwd, *args):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=20)
        return r.returncode, r.stdout
    except (OSError, subprocess.SubprocessError):
        return 1, ""


def same_repo(cwd):
    """Is `cwd` inside the main working tree of this repository (not a snapshot or temp repo)?"""
    if not os.path.isdir(cwd):
        return False  # the command fails by itself, or the directory is created by the command
    rc, out = _git(cwd, "rev-parse", "--show-toplevel")
    return rc == 0 and _canon(out.strip()) == ROOT_C


FAKE_STATE = None  # selftest only: {"lines": [porcelain lines], "staged": bool}


def docs_dirty(tracked_only=False, untracked_only=False):
    if FAKE_STATE is not None:
        out = "\n".join(FAKE_STATE["lines"])
    else:
        rc, out = _git(ROOT, "status", "--porcelain", "--", OWNER_DIR)
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if tracked_only:
        lines = [ln for ln in lines if not ln.startswith("??")]
    if untracked_only:
        lines = [ln for ln in lines if ln.startswith("??")]
    return bool(lines)


def docs_staged():
    if FAKE_STATE is not None:
        return FAKE_STATE["staged"]
    rc, out = _git(ROOT, "diff", "--cached", "--name-only", "--", OWNER_DIR)
    return bool(out.strip())


# ---------------------------------------------------------------- shell analysis

def tokenize(command, powershell):
    text = command.replace("\r", "")
    if powershell:
        text = text.replace("\\", "/").replace("`", "")
    else:
        text = text.replace("`", " ; ")
    text = text.replace("\n", " ; ")
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        lex.commenters = ""
        return list(lex)
    except ValueError:
        # unbalanced quotes (PowerShell syntax, apostrophes): split roughly, keep separators
        return [t for t in re.split(r"(\|\||&&|[;|&()<>]+)|\s+", text) if t]


def is_redirect(tok):
    return bool(tok) and set(tok) <= set("<>&|") and ">" in tok


def verb_of(tok):
    v = tok.strip("'\"").replace("\\", "/").rsplit("/", 1)[-1].lower()
    return v[:-4] if v.endswith(".exe") else v


def check_git(args, cwd, depth):
    i = 0
    while i < len(args):  # global options
        a = args[i]
        if a == "-C" and i + 1 < len(args):
            cwd = resolve(args[i + 1], cwd) or cwd
            i += 2
        elif a in GIT_VALUE_OPTS and i + 1 < len(args):
            i += 2
        elif a.startswith("-"):
            i += 1
        else:
            break
    if i >= len(args):
        return
    sub, rest = args[i].lower(), args[i + 1:]
    if sub in ("push", "send-pack"):
        raise Deny("`git push` is forbidden: this project commits locally only and never pushes")
    if not same_repo(cwd):
        return
    opts = [a for a in rest if a.startswith("-")]
    after_dd = rest[rest.index("--") + 1:] if "--" in rest else None

    def positional(value_opts=()):
        out, skip = [], False
        for a in rest:
            if skip:
                skip = False
                continue
            if a == "--":
                continue
            if a in value_opts:
                skip = True
                continue
            if a.startswith("-"):
                continue
            out.append(a)
        return out

    def short(flag):
        return any(re.fullmatch(r"-[A-Za-z]*" + flag + r"[A-Za-z]*", o) for o in opts)

    if sub in ("add", "stage"):
        paths = positional(("--pathspec-from-file", "--chmod"))
        hit = [p for p in paths if in_docs(p, cwd)]
        if hit:
            raise Deny(f"`git add` of {hit[0]}: docs/ is the owner's and is never staged")
        broad = (not paths and (short("A") or short("u") or "--all" in opts or "--update" in opts)) \
            or any(covers_docs(p, cwd) for p in paths)
        if broad and docs_dirty():
            raise Deny("broad `git add` while docs/ has changes would stage the owner's files; "
                       "stage explicit paths (or use taskctl accept / commit-report)")
    elif sub == "commit":
        paths = positional(COMMIT_VALUE_OPTS)
        hit = [p for p in paths if in_docs(p, cwd)]
        if hit:
            raise Deny(f"`git commit` of {hit[0]}: docs/ is never committed by the harness")
        if docs_staged():
            raise Deny("docs/ files are staged; unstage them first: git restore --staged docs")
        if (short("a") or "--all" in opts) and docs_dirty(tracked_only=True):
            raise Deny("`git commit -a` while docs/ has changes would commit the owner's files; "
                       "stage explicit paths")
    elif sub in ("rm", "mv"):
        hit = [p for p in positional() if in_docs(p, cwd)]
        if hit:
            raise Deny(f"`git {sub}` on {hit[0]}: docs/ is never changed by the harness")
    elif sub in ("checkout", "restore", "reset", "clean", "stash"):
        paths = after_dd if after_dd is not None else positional(("-b", "-B", "--source", "-s", "--orphan"))
        if sub == "stash":
            words = [a for a in rest if not a.startswith("-")]
            if words and words[0] in ("list", "show", "pop", "apply", "drop", "branch", "clear"):
                return
            paths = after_dd or []
        index_only = sub == "restore" and "--staged" in opts and "--worktree" not in opts and not short("W")
        # `git reset <paths>` and `git restore --staged <paths>` only unstage: always allowed
        if sub in ("checkout", "restore", "clean") and not index_only:
            hit = [p for p in paths if in_docs(p, cwd)]
            if hit:
                raise Deny(f"`git {sub}` on {hit[0]} would overwrite or delete the owner's files in docs/")
        if sub == "reset":
            broad = "--hard" in opts or "--merge" in opts or "--keep" in opts
        elif sub == "checkout":
            broad = short("f") or "--force" in opts or any(covers_docs(p, cwd) and os.path.isdir(
                resolve(p, cwd) or "") for p in (after_dd if after_dd is not None else paths))
        elif sub == "restore":
            broad = not index_only and any(covers_docs(p, cwd) for p in paths)
        elif sub == "clean":
            broad = not paths or any(covers_docs(p, cwd) for p in paths)
            if short("n") or "--dry-run" in opts:
                broad = False
        else:  # stash push / save / plain stash
            broad = not paths or any(covers_docs(p, cwd) for p in paths)
        # clean only removes untracked files; reset/checkout/restore only touch tracked ones
        if broad and docs_dirty(untracked_only=(sub == "clean"),
                                tracked_only=(sub in ("reset", "checkout", "restore"))):
            raise Deny(f"`git {sub}` in this form would discard or move the owner's uncommitted changes "
                       "under docs/; limit it to explicit paths outside docs/")


def check_segment(seg, cwd, powershell, depth):
    """Analyse one simple command; returns the (possibly changed) working directory."""
    # redirections anywhere in the segment
    words, i = [], 0
    while i < len(seg):
        t = seg[i]
        if is_redirect(t):
            if i + 1 < len(seg) and not re.fullmatch(r"&?\d+", seg[i + 1]) and in_docs(seg[i + 1], cwd):
                raise Deny(f"redirection into {seg[i + 1]}: docs/ is never written by the harness")
            i += 2
            continue
        if t in ("<", "<<", "<<<"):
            i += 2
            continue
        words.append(t)
        i += 1
    while words and (words[0].lower() in SKIP_WORDS or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0])
                     or re.fullmatch(r"\d+", words[0])):
        words = words[1:]
    if not words:
        return cwd
    verb, args = verb_of(words[0]), words[1:]
    if verb in CD_VERBS:
        target = [a for a in args if not a.startswith("-")]
        if target:
            new = resolve(target[0], cwd)
            if new:
                return new
        return cwd
    if verb == "git":
        check_git(args, cwd, depth)
    elif verb == "gh":
        w = [a.lower() for a in args if not a.startswith("-")]
        if len(w) >= 2 and (w[0], w[1]) in GH_PUBLISH:
            raise Deny(f"`gh {w[0]} {w[1]}` publishes to a remote: this project never pushes")
    elif verb in WRITE_VERBS:
        hit = any_docs(args, cwd)
        if hit:
            raise Deny(f"`{verb}` on {hit}: docs/ is the owner's and is never changed by the harness")
    elif verb in COPY_VERBS or verb == "robocopy":
        pos = [a for a in args if not a.startswith("-") and not (verb in ("xcopy", "robocopy")
                                                                  and re.fullmatch(r"/[A-Za-z:0-9]+", a))]
        dest = []
        for j, a in enumerate(args[:-1]):
            if a.lower() in ("-destination", "-t", "--target-directory"):
                dest.append(args[j + 1])
        for a in args:
            if a.lower().startswith(("--target-directory=", "-destination:")):
                dest.append(re.split(r"[=:]", a, 1)[1])
        if verb == "robocopy":
            if len(pos) >= 2:
                dest.append(pos[1])
            if any(re.fullmatch(r"/(mov|move|mir|purge)", a.lower()) for a in args) and pos:
                dest.append(pos[0])
        elif not dest and len(pos) >= 2:
            dest.append(pos[-1])
        hit = [d for d in dest if in_docs(d, cwd)]
        if hit:
            raise Deny(f"`{verb}` into {hit[0]}: docs/ is never written by the harness (copying from "
                       "docs/ is fine)")
    elif verb in ("sed", "perl", "ruby", "awk", "gawk"):
        inplace = any(re.fullmatch(r"-[A-Za-z]*i.*", a) or a.startswith("--in-place") or a == "-i"
                      or a.startswith("-i") for a in args if a.startswith("-"))
        if verb in ("awk", "gawk"):
            inplace = "inplace" in " ".join(args)
        if inplace:
            hit = any_docs(args, cwd)
            if hit:
                raise Deny(f"in-place `{verb}` on {hit}: docs/ is never edited by the harness")
    elif verb == "find":
        starts = []
        for a in args:
            if a.startswith("-") or a in ("(", "!", "\\("):
                break
            starts.append(a)
        if any(covers_docs(s, cwd) for s in (starts or ["."])):
            low = [a.lower() for a in args]
            destructive = "-delete" in low
            for flag in ("-exec", "-execdir", "-ok", "-okdir"):
                if flag in low and low.index(flag) + 1 < len(low) and \
                        verb_of(args[low.index(flag) + 1]) in WRITE_VERBS | {"sed", "perl"}:
                    destructive = True
            if destructive and (any(in_docs(s, cwd) for s in starts) or docs_exists_under(starts, cwd)):
                raise Deny("destructive `find` over docs/: the owner's files are never changed")
    elif verb in OUTPUT_OPT_VERBS:
        want = OUTPUT_OPT_VERBS[verb]
        for j, a in enumerate(args):
            val = None
            if a in want or a.lower() in want:
                val = args[j + 1] if j + 1 < len(args) else None
            else:
                for w in want:
                    if a.startswith(w + "=") or (len(w) == 2 and a.startswith(w) and len(a) > 2
                                                   and not a.startswith("--")):
                        val = a[len(w):].lstrip("=")
            if val and in_docs(val, cwd):
                raise Deny(f"`{verb}` output into {val}: docs/ is never written by the harness")
    elif verb in NESTED_SHELLS and depth < 3:
        for j, a in enumerate(args):
            if a.lower() in NESTED_FLAGS and j + 1 < len(args):
                inner = " ".join(args[j + 1:]) if verb in ("cmd", "powershell", "pwsh") else args[j + 1]
                check_command(inner, cwd, verb in ("powershell", "pwsh") or (powershell and verb == "cmd"),
                              depth + 1)
                break
    elif verb in ("eval", "xargs", "invoke-expression", "iex") and depth < 3:
        tail = [a for a in args if not a.startswith("-")] if verb == "xargs" else args
        if tail:
            check_command(" ".join(shlex.quote(a) for a in tail) if verb == "xargs" else " ".join(tail),
                          cwd, powershell, depth + 1)
    return cwd


def docs_exists_under(starts, cwd):
    """`find .` (or a parent directory) with -delete reaches docs/ too."""
    return any(covers_docs(s, cwd) for s in (starts or ["."]))


DOTNET_WRITE = re.compile(r"(?:WriteAll\w+|AppendAll\w+|::Delete|::Move|::Create\w*)\(\s*([^,)\s]+)")


def check_command(command, cwd, powershell=False, depth=0):
    if powershell:
        for m in DOTNET_WRITE.finditer(command):
            if in_docs(m.group(1), cwd):
                raise Deny(f".NET file write on {m.group(1)}: docs/ is never written by the harness")
    tokens = tokenize(command, powershell)
    seg = []
    for t in tokens + [";"]:
        if t in SEPARATORS or (set(t) <= set(";&|()") and t):
            if seg:
                cwd = check_segment(seg, cwd, powershell, depth)
            seg = []
        else:
            seg.append(t)


FALLBACK_PUSH = re.compile(r"(?:^|[;&|\n(]\s*)git(?:\.exe)?(?:\s+(?:-C\s+\S+|-c\s+\S+|--[\w-]+(?:=\S+)?))*\s+push\b")


def decide(tool, tool_input, cwd):
    """Returns a refusal reason, or None to allow."""
    cwd = cwd or ROOT
    if tool in FILE_TOOLS:
        path = tool_input.get(FILE_TOOLS[tool]) or tool_input.get("path") or ""
        if path and in_docs(path, cwd):
            return (f"{tool} on {path}: docs/ belongs to the project owner and is never edited by the "
                    "harness. Write canonical text under spec/ instead.")
        return None
    if tool in SHELL_TOOLS:
        command = tool_input.get("command") or ""
        try:
            check_command(command, cwd, SHELL_TOOLS[tool])
        except Deny as d:
            return str(d)
        except Exception:  # analysis failed: keep only the unambiguous rule
            if FALLBACK_PUSH.search(command):
                return "`git push` is forbidden: this project commits locally only and never pushes"
        return None
    return None


def log_refusal(tool, detail, reason, agent):
    if os.environ.get("AXIOM_GUARD_NOLOG"):
        return
    try:
        d = os.path.join(ROOT, "_workspaces", "logs")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "guard.log"), "a", encoding="utf-8", newline="\n") as fh:
            stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            fh.write(f"{stamp} DENY {tool} [{agent or 'main'}] {detail[:300]!r} :: {reason}\n")
    except OSError:
        pass


def hook_main():
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        data = json.loads(raw) if raw.strip() else {}
        tool = data.get("tool_name", "")
        tool_input = data.get("tool_input") or {}
        reason = decide(tool, tool_input, data.get("cwd") or os.getcwd())
        if reason:
            detail = tool_input.get("command") or tool_input.get("file_path") or tool_input.get("notebook_path") or ""
            log_refusal(tool, str(detail), reason, data.get("agent_type"))
            out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                          "permissionDecisionReason": "Axiom guard: " + reason}}
            sys.stdout.write(json.dumps(out))
    except Exception:
        pass  # fail open
    return 0


# ---------------------------------------------------------------- self test

def selftest():
    r = ROOT.replace("\\", "/")
    msys = "/" + r[0].lower() + r[2:] if re.match(r"^[A-Za-z]:", r) else r
    deny = [
        ("Bash", "git push"),
        ("Bash", "git push origin main"),
        ("Bash", "git -C . push --dry-run"),
        ("Bash", "git --no-pager -c x=y push -f"),
        ("Bash", "cd build && git push"),
        ("Bash", "echo ok; git push 2>&1 | tail -1"),
        ("Bash", 'bash -c "git push origin HEAD"'),
        ("PowerShell", "git push"),
        ("PowerShell", "git status; git push origin main"),
        ("Bash", "git add docs/base/specs/0001.md"),
        ("Bash", "git add -f docs"),
        ("Bash", f'git add "{msys}/docs/base"'),
        ("Bash", "git add spec docs/base/x.md"),
        ("Bash", "git rm docs/base/specs/0001.md"),
        ("Bash", "git mv docs/base/a.md docs/base/b.md"),
        ("Bash", "git checkout -- docs/base/specs/0001.md"),
        ("Bash", "git restore docs"),
        ("Bash", "git commit -m x docs/base/a.md"),
        ("Bash", "rm docs/base/specs/0001.md"),
        ("Bash", "rm -rf docs"),
        ("Bash", f"rm -rf '{msys}/docs/base'"),
        ("Bash", "cd docs && rm -f base/x.md"),
        ("Bash", "mv docs/base/a.md spec/a.md"),
        ("Bash", "cp spec/a.md docs/base/a.md"),
        ("Bash", "echo hi > docs/new.md"),
        ("Bash", "cat spec/a.md >> docs/base/a.md"),
        ("Bash", "sed -i 's/a/b/' docs/base/a.md"),
        ("Bash", "perl -pi -e 's/a/b/' docs/base/a.md"),
        ("Bash", "dos2unix docs/base/a.md"),
        ("Bash", "find docs -name '*.md' -delete"),
        ("Bash", "find docs/base -type f -exec rm {} +"),
        ("Bash", "touch docs/x && echo done"),
        ("Bash", "grep foo spec/a.md | tee docs/out.txt"),
        ("Bash", "mkdir -p docs/new"),
        ("Bash", "gh pr create --fill"),
        ("PowerShell", "Remove-Item -Recurse -Force docs\\base\\x.md"),
        ("PowerShell", "Set-Content -Path docs\\base\\a.md -Value 'x'"),
        ("PowerShell", "Get-Content spec\\a.md | Out-File docs\\a.md"),
        ("PowerShell", "Move-Item docs\\base\\a.md spec\\"),
        ("PowerShell", "Copy-Item spec\\a.md -Destination docs\\base\\"),
        ("PowerShell", "[IO.File]::WriteAllText('docs/base/a.md', 'x')"),
        ("PowerShell", "git add docs\\base\\a.md"),
    ]
    allow = [
        ("Bash", "git status --short"),
        ("Bash", "git log --oneline --grep push -5"),
        ("Bash", 'git commit -m "T010: lexer (never push, docs/ untouched)"'),
        ("Bash", "git add -- spec/SPEC-01.md _workspaces/tasks"),
        ("Bash", "git add _workspaces/reports/T010-report.md bootstrap/axiom0/src/lexer/lexer.c"),
        ("Bash", "git diff --stat -- docs"),
        ("Bash", "git log -3 -- docs/base/specs"),
        ("Bash", "git restore --staged spec/a.md"),
        ("Bash", "git worktree add --detach build-snap-T010 HEAD"),
        ("Bash", "git -C build-snap-T010 clean -fd"),
        ("Bash", "cat docs/base/specs/0263-ladder.md | head -50"),
        ("Bash", "ls docs/base/tasks | grep -i bootstrap"),
        ("Bash", "grep -rn 'raw pointer' docs/base/specs > _workspaces/artifacts/hits.txt"),
        ("Bash", "grep -o 'docs/base/[a-z]*' spec/INDEX.md"),
        ("Bash", "cp docs/base/specs/0263-ladder.md _workspaces/artifacts/"),
        ("Bash", "wc -l docs/base/specs/*.md | sort -n | tail -3"),
        ("Bash", "find docs/base -name '0263*'"),
        ("Bash", "python tools/axtest.py --compiler build-T010/axiom0.exe"),
        ("Bash", "python .claude/skills/axiom-tasks/scripts/taskctl.py accept T010"),
        ("Bash", "python .claude/skills/axiom-tasks/scripts/taskctl.py block T010 --reason \"docs/base/specs/0160 contradicts 0394; rm or keep?\""),
        ("Bash", "python .claude/skills/axiom-tasks/scripts/taskctl.py commit-report _workspaces/reports/unblock-T010.md --subject \"arch: unblock T010\""),
        ("Bash", "python .claude/skills/axiom-spec-index/scripts/x.py docs/base/specs"),
        ("Bash", "cmake -S bootstrap/axiom0 -B build-T010 -G Ninja && cmake --build build-T010"),
        ("Bash", "rm -rf build-T010 build-qa-T010"),
        ("Bash", "rm -rf build-snap-T010/docs/tmp"),
        ("Bash", "echo \"2026-10-01 10:00 T010 start docs/ untouched\" >> _workspaces/logs/autopilot.log"),
        ("Bash", "sed -n '1,40p' docs/base/specs/0001.md"),
        ("Bash", "sed -i 's/a/b/' spec/a.md"),
        ("Bash", "mkdir -p tests/run/basic && touch tests/run/basic/a.ax"),
        ("Bash", "gh pr list"),
        ("Bash", "git stash list"),
        ("Bash", "echo \"it's fine\" && git status"),
        ("PowerShell", "Get-Content docs\\base\\specs\\0001.md -TotalCount 20"),
        ("PowerShell", "Get-ChildItem docs\\base\\specs | Measure-Object"),
        ("PowerShell", "Copy-Item docs\\base\\specs\\0001.md -Destination _workspaces\\artifacts\\"),
        ("PowerShell", "git status; git log --oneline -3"),
        ("PowerShell", "Remove-Item -Recurse -Force build-T010"),
        ("PowerShell", "python .claude/skills/axiom-tasks/scripts/taskctl.py status"),
    ]
    files_deny = ["docs/base/specs/0001.md", os.path.join(ROOT, "docs", "x.md"), "docs\\new.md",
                  msys + "/docs/base/a.md"]
    files_allow = ["spec/SPEC-01.md", "CLAUDE.md", os.path.join(ROOT, "build-snap-T010", "docs", "x.md"),
                   "_workspaces/reports/T010-report.md", "documentation/x.md", "docs2/x.md"]
    # the tables above are judged against a clean docs/ so the result does not depend on what the
    # owner currently has in the working tree; the state-dependent rules are exercised below
    global FAKE_STATE
    FAKE_STATE = {"lines": [], "staged": False}
    bad = 0
    state_cases = [
        ({"lines": [" M docs/base/a.md"], "staged": False},
         ["git add -A", "git add .", "git add -u", "git commit -am x", "git reset --hard", "git checkout -- .",
          "git checkout -f", "git restore .", "git stash", "git stash push -u"],
         ["git add spec tools", "git commit -m x", "git reset -q", "git clean -fd", "git stash list",
          "git stash pop", "git restore --staged .", "git checkout main", "git clean -fd -- build"]),
        ({"lines": ["?? docs/owner-note.md"], "staged": False},
         ["git add -A", "git add .", "git clean -fd", "git clean -fdx .", "git stash -u"],
         ["git commit -am x", "git reset --hard", "git checkout -- .", "git clean -n", "git clean -fd -- build"]),
        ({"lines": ["A  docs/owner-note.md"], "staged": True},
         ["git commit -m x", "git commit"],
         ["git restore --staged docs", "git status"]),
        ({"lines": [], "staged": False},
         [],
         ["git add -A", "git add .", "git commit -am x", "git reset --hard", "git checkout -- .", "git stash",
          "git clean -fd"]),
    ]
    extra = 0
    for state, must_deny, must_allow in state_cases:
        FAKE_STATE = state
        for cmd in must_deny:
            extra += 1
            if not decide("Bash", {"command": cmd}, ROOT):
                print(f"FAIL should deny  [{state['lines']}] {cmd}")
                bad += 1
        for cmd in must_allow:
            extra += 1
            why = decide("Bash", {"command": cmd}, ROOT)
            if why:
                print(f"FAIL should allow [{state['lines']}] {cmd} -> {why}")
                bad += 1
    FAKE_STATE = {"lines": [], "staged": False}
    for tool, cmd in deny:
        if not decide(tool, {"command": cmd}, ROOT):
            print(f"FAIL should deny  [{tool}] {cmd}")
            bad += 1
    for tool, cmd in allow:
        why = decide(tool, {"command": cmd}, ROOT)
        if why:
            print(f"FAIL should allow [{tool}] {cmd}  -> {why}")
            bad += 1
    for f in files_deny:
        for tool in ("Edit", "Write"):
            if not decide(tool, {"file_path": f}, ROOT):
                print(f"FAIL should deny  [{tool}] {f}")
                bad += 1
    for f in files_allow:
        why = decide("Write", {"file_path": f}, ROOT)
        if why:
            print(f"FAIL should allow [Write] {f} -> {why}")
            bad += 1
    if not decide("Bash", {"command": "rm base/x.md"}, os.path.join(ROOT, "docs")):
        print("FAIL should deny  rm with cwd inside docs/")
        bad += 1
    FAKE_STATE = None
    n = len(deny) + len(allow) + 2 * len(files_deny) + len(files_allow) + 1 + extra
    print(f"guard selftest: {n - bad}/{n} ok")
    return 1 if bad else 0


def main(argv):
    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--selftest" in argv:
        return selftest()
    if "--check" in argv or "--check-file" in argv:
        cwd = opt("--cwd", os.getcwd())
        if "--check-file" in argv:
            why = decide("Write", {"file_path": opt("--check-file", "")}, cwd)
        else:
            why = decide(opt("--tool", "Bash"), {"command": opt("--check", "")}, cwd)
        print("DENY " + why if why else "ALLOW")
        return 1 if why else 0
    return hook_main()


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main(sys.argv[1:]))
