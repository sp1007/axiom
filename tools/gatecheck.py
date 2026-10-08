#!/usr/bin/env python3
"""gatecheck: phase-gate checker for the Axiom bootstrap (T022; SPEC-00 AXS-BOOT-050/051).

What it checks (Python 3 standard library only):

  structure  every ```milestone block of spec/SPEC-00-bootstrap.md parses as JSON with exactly the
             fields of AXS-BOOT-050, unique ids, known feature ids (the `| F-...` rows of SPEC-00 §4),
             known shortcut ids (the `| X-...` rows of AXS-BOOT-004), a linear `previous` chain and a
             `gate` that is a board task                                       (AXS-BOOT-051 step 1)
  milestones for every due milestone, cumulatively: every `must_pass` path exists and holds tests,
             `tools/axtest.py` reports no FAIL/XPASS/CRASH/TIMEOUT for them, every XFAIL names an
             open board task, every SKIP has an accepted reason                (steps 2-3)
             native features: no `native-after: <native task>` left in tests/ (step 4)
             the listed `checks` exit 0                                        (step 5)
  rule (a)   spec/invariants.md: ids, field order, `verify:` targets exist once the `since:` task is
             done, otherwise the `since:` task is on the board and not superseded (IG-1..IG-4)
  rule (c)   every `xfail:` / `native-after:` directive under tests/ names a board task that exists
             and is not done
  rule (d)   spec/selfhost-subset.tsv: every delivering task (oracle and native columns) exists and is
             an ancestor (`depends` closure) of the feature's first consumer

A milestone is *due* when it is current (`--gate <TID>` selects the milestones whose gate is TID) or
its gate task is done. Output: one line per due milestone, `MS-Px PASS` or `MS-Px BLOCKED: <first
reason>` (there is no third state, AXS-BOOT-005), preceded by one `gatecheck: ...` line per global
problem.

Usage: python tools/gatecheck.py [--gate TID] [--compiler PATH] [--root DIR] [--no-run] [-v]
  --no-run   structural checks and rules (a), (c), (d) only: no test run, no check commands
Exit status: 0 every due milestone passes and no global problem, 1 otherwise, 2 usage error.
"""

import argparse
import json
import os
import re
import subprocess
import sys

TASK_ID_RE = re.compile(r"T\d{3}[a-z]?")
TASK_ID_FULL_RE = re.compile(r"^T\d{3}[a-z]?$")
MILESTONE_ID_RE = re.compile(r"^MS-P\d+[a-z]?$")
FEATURE_ROW_RE = re.compile(r"^\|\s*(F-[A-Z0-9-]+)\s*\|")
SHORTCUT_ROW_RE = re.compile(r"^\|\s*(X-[A-Z0-9-]+)\s*\|")
INV_HEAD_RE = re.compile("^### (INV-[A-Z]+-[0-9]{3}) [-\u2014] \\S")  # IG-1; the file uses an em dash
INV_FIELDS = ("statement", "source", "verify", "since", "check")
DIRECTIVE_AX_RE = re.compile(r"^\s*//[ \t]*(xfail|native-after):[ \t]*(\S+)")
DIRECTIVE_TEST_RE = re.compile(r"^(xfail|native-after):[ \t]*(\S+)")
SKIP_NATIVE_AFTER_RE = re.compile(r"^native after (T\d{3}[a-z]?)$")
SKIP_MODE_RE = re.compile(r"^mode unavailable: (\w+)$")
XFAIL_MSG_RE = re.compile(r"^(T\d{3}[a-z]?):")
TEST_FILE_EXTS = (".ax", ".test")

FIELDS = {
    "id": str, "title": str, "phase": str, "gate": str, "previous": (str, type(None)),
    "aliases": list, "goal": str, "components": list, "introduces": list, "native": list,
    "modes": list, "must_pass": list, "checks": list, "forbidden": list,
}
LIST_OF_STR = ("aliases", "components", "introduces", "native", "modes", "must_pass", "checks",
               "forbidden")
MODES = ("interp", "native")

# AXS-BOOT-050 check table: name -> command (argv after the python interpreter), run from the root.
# `gatecheck` is this tool's own structural step 1, step 4 and rules (a)-(d): evaluated in-process.
# `differential` and `determinism` are defined by T029; until then a due milestone listing them is
# BLOCKED with "no command".
CHECK_COMMANDS = {
    "axtest_selftest": ["tools/tests/axtest/run_selftests.py"],
    "archcheck_selftest": ["tools/tests/archcheck/run_selftests.py"],
    "archcheck": ["tools/archcheck.py"],
    "reqcov": [".claude/skills/axiom-tasks/scripts/reqcov.py", "--strict"],
    "harness_check": [".claude/skills/axiom-tasks/scripts/harness_check.py"],
    "gatecheck": None,
    "differential": ["python", "tools/axtest.py", "diff"],
    "determinism": ["bash", "tools/ci.sh"],
}
INTERNAL_CHECKS = ("gatecheck",)


class Ctx:
    def __init__(self, root):
        self.root = root
        self.spec00 = os.path.join(root, "spec", "SPEC-00-bootstrap.md")
        self.invariants = os.path.join(root, "spec", "invariants.md")
        self.subset = os.path.join(root, "spec", "selfhost-subset.tsv")
        self.board = os.path.join(root, "_workspaces", "tasks")
        self.tests = os.path.join(root, "tests")

    def rel(self, path):
        try:
            return os.path.relpath(path, self.root).replace(os.sep, "/")
        except ValueError:
            return path


# --------------------------------------------------------------------------------------- reading

def read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read().replace("\r\n", "\n")


def load_board(ctx, problems):
    """{id: {"dir": todo|doing|done, "status": str, "depends": [..], "superseded_by": str|None}}"""
    tasks = {}
    if not os.path.isdir(ctx.board):
        problems.append("board: no task board at %s" % ctx.rel(ctx.board))
        return tasks
    for st in ("todo", "doing", "done"):
        d = os.path.join(ctx.board, st)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md"):
                continue
            path = os.path.join(d, name)
            try:
                text = read_text(path)
            except (OSError, UnicodeDecodeError) as e:
                problems.append("board: cannot read %s: %s" % (ctx.rel(path), e))
                continue
            m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            if not m:
                problems.append("board: %s has no front-matter" % ctx.rel(path))
                continue
            meta = {}
            for line in m.group(1).splitlines():
                if ":" not in line or line.lstrip().startswith("#"):
                    continue
                k, v = line.split(":", 1)
                v = re.sub(r"\s+#.*$", "", v).strip()
                if v.startswith("[") and v.endswith("]"):
                    v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
                meta[k.strip()] = v
            tid = meta.get("id")
            if not isinstance(tid, str) or not TASK_ID_FULL_RE.match(tid):
                problems.append("board: %s has no valid id" % ctx.rel(path))
                continue
            if tid in tasks:
                problems.append("board: duplicate task id %s" % tid)
                continue
            deps = meta.get("depends", [])
            sup = meta.get("superseded_by")
            tasks[tid] = {
                "dir": st,
                "status": meta.get("status", st) if isinstance(meta.get("status", st), str) else st,
                "depends": deps if isinstance(deps, list) else [],
                "superseded_by": sup if isinstance(sup, str) and sup else None,
            }
    if not tasks:
        problems.append("board: 0 tasks found under %s (wrong root or damaged board)" % ctx.rel(ctx.board))
    return tasks


def is_done(task):
    return task is not None and task["dir"] == "done"


def is_superseded(task):
    return task is not None and (task["status"] == "superseded" or task["superseded_by"] is not None)


def open_task_problem(board, tid):
    """None when `tid` is an existing, not-done, not-superseded task; otherwise the reason."""
    t = board.get(tid)
    if t is None:
        return "task %s is not on the board" % tid
    if is_superseded(t):
        return "task %s is superseded" % tid
    if is_done(t):
        return "task %s is already done" % tid
    return None


# ------------------------------------------------------------------------------- SPEC-00 parsing

def spec00_tables(text):
    features, shortcuts = set(), set()
    for line in text.split("\n"):
        m = FEATURE_ROW_RE.match(line)
        if m:
            features.add(m.group(1))
        m = SHORTCUT_ROW_RE.match(line)
        if m:
            shortcuts.add(m.group(1))
    return features, shortcuts


def native_tasks_of_features(text):
    """{feature id: [native task ids]} from the §4 feature table (column 4, AXS-BOOT-030)."""
    out = {}
    for line in text.split("\n"):
        if not FEATURE_ROW_RE.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        cell = re.sub(r"\([^)]*\)", " ", cells[3])  # text in parentheses only explains the ids
        out[cells[0]] = TASK_ID_RE.findall(cell)
    return out


def extract_blocks(text, problems):
    blocks, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        if lines[i] == "```milestone":
            start = i + 1
            j = start
            while j < len(lines) and lines[j] != "```":
                j += 1
            if j >= len(lines):
                problems.append("SPEC-00: milestone block at line %d is not closed" % (i + 1))
                break
            blocks.append((i + 1, "\n".join(lines[start:j])))
            i = j + 1
            continue
        i += 1
    return blocks


def parse_milestones(ctx, board, problems):
    try:
        text = read_text(ctx.spec00)
    except OSError as e:
        problems.append("SPEC-00: cannot read %s: %s" % (ctx.rel(ctx.spec00), e))
        return [], {}, text_or_empty()
    features, shortcuts = spec00_tables(text)
    if not features:
        problems.append("SPEC-00: no feature rows (`| F-...`) found in §4")
    milestones, seen, prev_id = [], set(), None
    for line_no, body in extract_blocks(text, problems):
        where = "SPEC-00 line %d" % line_no
        try:
            ms = json.loads(body)
        except ValueError as e:
            problems.append("%s: milestone block is not valid JSON: %s" % (where, e))
            prev_id = None
            continue
        if not isinstance(ms, dict):
            problems.append("%s: milestone block is not a JSON object" % where)
            continue
        ok = True
        missing = [k for k in FIELDS if k not in ms]
        extra = [k for k in ms if k not in FIELDS]
        if missing:
            problems.append("%s: missing field(s) %s" % (where, ", ".join(missing)))
            ok = False
        if extra:
            problems.append("%s: unknown field(s) %s" % (where, ", ".join(extra)))
            ok = False
        for k, ty in FIELDS.items():
            if k in ms and not isinstance(ms[k], ty):
                problems.append("%s: field `%s` has the wrong type" % (where, k))
                ok = False
        for k in LIST_OF_STR:
            if isinstance(ms.get(k), list) and not all(isinstance(x, str) for x in ms[k]):
                problems.append("%s: field `%s` must be a list of strings" % (where, k))
                ok = False
        if not ok:
            prev_id = ms.get("id") if isinstance(ms.get("id"), str) else None
            continue
        mid = ms["id"]
        where = "%s (%s)" % (where, mid)
        if not MILESTONE_ID_RE.match(mid):
            problems.append("%s: id is not of the form MS-P<n>[letter]" % where)
        if mid in seen:
            problems.append("%s: duplicate milestone id" % where)
        seen.add(mid)
        if ms["previous"] != prev_id:
            problems.append("%s: `previous` is %r but the preceding block is %r"
                            % (where, ms["previous"], prev_id))
        prev_id = mid
        for k in ("introduces", "native"):
            for f in ms[k]:
                if f not in features:
                    problems.append("%s: unknown feature id %s in `%s`" % (where, f, k))
        for x in ms["forbidden"]:
            if x not in shortcuts:
                problems.append("%s: unknown shortcut id %s" % (where, x))
        for m in ms["modes"]:
            if m not in MODES:
                problems.append("%s: unknown mode %s" % (where, m))
        for c in ms["checks"]:
            if c not in CHECK_COMMANDS:
                problems.append("%s: unknown check %s" % (where, c))
        for p in ms["must_pass"]:
            if not p.startswith("tests/") or "\\" in p or any(ch in p for ch in "*?[") or p.endswith("/"):
                problems.append("%s: must_pass entry %r is not a repository-relative tests/ path "
                                "without globs" % (where, p))
        if not TASK_ID_FULL_RE.match(ms["gate"]) or ms["gate"] not in board:
            problems.append("%s: gate %s is not a board task" % (where, ms["gate"]))
        ms["_line"] = line_no
        milestones.append(ms)
    if not milestones and not any(p.startswith("SPEC-00") for p in problems):
        problems.append("SPEC-00: no ```milestone blocks found")
    return milestones, native_tasks_of_features(text), text


def text_or_empty():
    return ""


# -------------------------------------------------------------------------------- rule (a)

def check_invariants(ctx, board, problems):
    try:
        text = read_text(ctx.invariants)
    except OSError as e:
        problems.append("rule (a): cannot read %s: %s" % (ctx.rel(ctx.invariants), e))
        return
    lines = text.split("\n")
    seen, count, in_fence = set(), 0, False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            in_fence = not in_fence  # the format example in §1 is fenced; it is not an invariant
            i += 1
            continue
        if in_fence or not line.startswith("### INV-"):
            i += 1
            continue
        m = INV_HEAD_RE.match(line)
        if not m:
            problems.append("rule (a): invariants.md:%d: heading does not match "
                            "`### INV-<GROUP>-<NNN> - <title>`" % (i + 1))
            i += 1
            continue
        inv = m.group(1)
        count += 1
        if inv in seen:
            problems.append("rule (a): %s is defined twice (IG-1)" % inv)
        seen.add(inv)
        fields, j = [], i + 1
        while j < len(lines) and len(fields) < len(INV_FIELDS) and lines[j].startswith("- "):
            fm = re.match(r"^- ([a-z]+): ?(.*)$", lines[j])
            if not fm:
                break
            fields.append((fm.group(1), fm.group(2).strip()))
            j += 1
        names = [f for f, _ in fields]
        if tuple(names) != INV_FIELDS:
            problems.append("rule (a): %s: fields are %s, expected %s in this order (IG-4)"
                            % (inv, ", ".join(names) or "none", ", ".join(INV_FIELDS)))
            i = j
            continue
        val = dict(fields)
        retired = val["statement"].startswith("RETIRED")
        targets = [t.strip() for t in val["verify"].split(",") if t.strip()]
        since = val["since"]
        if retired:
            if val["verify"] != "none":
                problems.append("rule (a): %s is RETIRED but `verify:` is not `none` (IG-1)" % inv)
            i = j
            continue
        if not targets or targets == ["none"]:
            problems.append("rule (a): %s has no `verify:` target (IG-2)" % inv)
            i = j
            continue
        for t in targets:
            if not (t.startswith("tests/") or t.startswith("tools/") or
                    re.match(r"^\.claude/skills/[^/]+/scripts/", t)):
                problems.append("rule (a): %s: verify target %r is neither tests/..., tools/... nor a "
                                "harness script (IG-2)" % (inv, t))
        if not TASK_ID_FULL_RE.match(since):
            problems.append("rule (a): %s: `since:` %r is not a task id (IG-3)" % (inv, since))
            i = j
            continue
        task = board.get(since)
        if task is None:
            problems.append("rule (a): %s: `since:` task %s is not on the board (IG-3)" % (inv, since))
        elif is_superseded(task):
            problems.append("rule (a): %s: `since:` task %s is superseded (IG-3)" % (inv, since))
        elif is_done(task):
            for t in targets:
                path = os.path.join(ctx.root, *t.split("/"))
                if os.path.isdir(path):
                    if not any(files for _r, _d, files in os.walk(path)):
                        problems.append("rule (a): %s: verify directory %s holds no file although %s "
                                        "is done (IG-3)" % (inv, t, since))
                elif not os.path.isfile(path):
                    problems.append("rule (a): %s: verify target %s does not exist although %s is "
                                    "done (IG-3)" % (inv, t, since))
        i = j
    if count == 0:
        problems.append("rule (a): no invariant blocks found in %s" % ctx.rel(ctx.invariants))


# -------------------------------------------------------------------------------- rule (c)

def scan_directives(ctx):
    """[(rel path, line, directive, task)] for every xfail/native-after directive under tests/."""
    found = []
    if not os.path.isdir(ctx.tests):
        return found
    for dirpath, dirnames, filenames in os.walk(ctx.tests):
        dirnames[:] = sorted(d for d in dirnames if d != "fixtures")
        for name in sorted(filenames):
            if not name.endswith(TEST_FILE_EXTS):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            rx = DIRECTIVE_AX_RE if name.endswith(".ax") else DIRECTIVE_TEST_RE
            for n, raw in enumerate(data.split(b"\n"), 1):
                m = rx.match(raw.decode("utf-8", "replace").rstrip("\r"))
                if m:
                    found.append((ctx.rel(path), n, m.group(1), m.group(2)))
    return found


def check_directives(ctx, board, problems, directives):
    for rel, line, kind, task in directives:
        if not TASK_ID_FULL_RE.match(task):
            problems.append("rule (c): %s:%d: `%s:` names %r, not a task id" % (rel, line, kind, task))
            continue
        why = open_task_problem(board, task)
        if why:
            problems.append("rule (c): %s:%d: `%s: %s` but %s" % (rel, line, kind, task, why))


# -------------------------------------------------------------------------------- rule (d)

def ancestors(board, tid, memo):
    if tid in memo:
        return memo[tid]
    memo[tid] = set()  # cycle guard
    out = set()
    t = board.get(tid)
    for d in (t["depends"] if t else []):
        out.add(d)
        out |= ancestors(board, d, memo)
    memo[tid] = out
    return out


def check_subset(ctx, board, features, problems):
    try:
        text = read_text(ctx.subset)
    except OSError as e:
        problems.append("rule (d): cannot read %s: %s" % (ctx.rel(ctx.subset), e))
        return
    rows = [r for r in text.split("\n") if r.strip()]
    if not rows:
        problems.append("rule (d): %s is empty" % ctx.rel(ctx.subset))
        return
    header = [c.strip() for c in rows[0].split("\t")]
    need = ("feature", "oracle", "native", "consumer")
    if any(h not in header for h in need):
        problems.append("rule (d): %s header must contain %s" % (ctx.rel(ctx.subset), ", ".join(need)))
        return
    col = {h: header.index(h) for h in need}
    memo = {}
    for n, row in enumerate(rows[1:], 2):
        cells = row.split("\t")
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        feat = cells[col["feature"]].strip()
        where = "rule (d): selfhost-subset.tsv:%d (%s)" % (n, feat)
        if features and feat.split(".")[0] not in features:
            problems.append("%s: feature id is not a SPEC-00 §4 feature" % where)
        delivering = []
        for d in TASK_ID_RE.findall(cells[col["oracle"]]) + TASK_ID_RE.findall(cells[col["native"]]):
            if d not in delivering:
                delivering.append(d)
        consumers = TASK_ID_RE.findall(cells[col["consumer"]])
        if not consumers:
            problems.append("%s: no first consumer task" % where)
            continue
        for c in consumers:
            if c not in board:
                problems.append("%s: consumer %s is not on the board" % (where, c))
                continue
            anc = ancestors(board, c, memo)
            for d in delivering:
                if d not in board:
                    problems.append("%s: delivering task %s is not on the board" % (where, d))
                elif d != c and d not in anc:
                    problems.append("%s: delivering task %s is not an ancestor of the consumer %s"
                                    % (where, d, c))


# ---------------------------------------------------------------------------- milestone run

def path_has_tests(abs_path):
    if os.path.isfile(abs_path):
        return True
    if os.path.isfile(os.path.join(abs_path, "axiom.toml")):
        return True
    for _r, dirnames, files in os.walk(abs_path):
        dirnames[:] = [d for d in dirnames if d != "fixtures"]
        if any(f.endswith(TEST_FILE_EXTS) for f in files):
            return True
    return has_c_unit_tests(abs_path)


def has_c_unit_tests(abs_path):
    """C unit tests (axiom-testing: tests/unit/**/*.c, compiled into axiom0-unit; cdriver_*.c are
    separate exec drivers)."""
    norm = abs_path.replace(os.sep, "/")
    if "/tests/unit" not in norm or not os.path.isdir(abs_path):
        return False
    for _r, dirnames, files in os.walk(abs_path):
        dirnames[:] = [d for d in dirnames if d != "fixtures"]
        if any(f.endswith(".c") and not f.startswith("cdriver_") for f in files):
            return True
    return False


def unit_runner_ids(ctx):
    """Test ids of the exec manifests under tests/unit that run the axiom0-unit binary: they are
    the axtest-discovered tests of every C unit test (AX_TEST markers) under tests/unit."""
    ids, base = [], os.path.join(ctx.tests, "unit")
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d != "fixtures")
        for name in sorted(filenames):
            if not name.endswith(".test"):
                continue
            path = os.path.join(dirpath, name)
            try:
                text = read_text(path)
            except (OSError, UnicodeDecodeError):
                continue
            if re.search(r"^cmd:.*axiom0-unit(\s|$)", text, re.M):
                ids.append(os.path.relpath(path, ctx.tests).replace(os.sep, "/"))
    return ids


def test_id_prefix(must_pass_path):
    return must_pass_path[len("tests/"):]


def belongs(test_id, prefix):
    return test_id == prefix or test_id.startswith(prefix + "/")


def run_axtest(ctx, compiler, prefixes, verbose):
    axtest = os.path.join(ctx.root, "tools", "axtest.py")
    if not os.path.isfile(axtest):
        return None, "tools/axtest.py not present"
    cmd = [sys.executable, axtest, "--json", "--root", ctx.root]
    if compiler:
        cmd += ["--compiler", compiler]
    cmd += sorted(set(prefixes))
    if verbose:
        print("gatecheck: running " + " ".join(cmd), file=sys.stderr)
    try:
        proc = subprocess.run(cmd, cwd=ctx.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=False)
    except OSError as e:
        return None, "cannot run tools/axtest.py: %s" % e
    try:
        doc = json.loads(proc.stdout.decode("utf-8", "replace"))
        results = doc["results"]
    except (ValueError, KeyError, TypeError):
        tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or [""]
        return None, "tools/axtest.py produced no JSON document (exit %d) %s" % (proc.returncode, tail[0])
    return results, None


def judge_results(ms_results, board, allowed_modes):
    """First blocking reason among one milestone's results, or None."""
    for r in ms_results:
        st, tid, mode, msg = r.get("state"), r.get("id"), r.get("mode") or "", r.get("message") or ""
        name = tid + (" [%s]" % mode if mode else "")
        if st in ("FAIL", "XPASS", "CRASH", "TIMEOUT"):
            return "%s %s: %s" % (st, name, msg.splitlines()[0] if msg else "")
        if st == "XFAIL":
            m = XFAIL_MSG_RE.match(msg)
            if not m:
                return "XFAIL %s does not name a task" % name
            why = open_task_problem(board, m.group(1))
            if why:
                return "XFAIL %s: %s" % (name, why)
        if st == "SKIP":
            m = SKIP_NATIVE_AFTER_RE.match(msg)
            if m:
                why = open_task_problem(board, m.group(1))
                if why:
                    return "SKIP %s (native after %s): %s" % (name, m.group(1), why)
                continue
            m = SKIP_MODE_RE.match(msg)
            if m:
                if m.group(1) in allowed_modes:
                    return "SKIP %s: mode %s is required by a due milestone" % (name, m.group(1))
                continue
            if msg.startswith("tool ") and msg.endswith(" not found"):
                continue
            if msg.startswith("requires ") and msg.endswith("(excluded for this compiler)"):
                continue
            return "SKIP %s without an accepted reason: %s" % (name, msg or "(none)")
    return None


def run_check(ctx, name, verbose):
    cmd = CHECK_COMMANDS.get(name)
    if cmd is None:
        return "check %s has no command yet (AXS-BOOT-050)" % name
        
    if cmd[0] in ("python", "bash"):
        prog = cmd[0]
        script_idx = 1
    else:
        prog = None
        script_idx = 0
        
    script = os.path.join(ctx.root, *cmd[script_idx].split("/"))
    if not os.path.isfile(script):
        return "check %s: %s not present" % (name, cmd[script_idx])
        
    if prog == "python":
        full = [sys.executable, script] + cmd[script_idx+1:]
    elif prog == "bash":
        full = ["bash", cmd[script_idx]] + cmd[script_idx+1:]
    else:
        full = [sys.executable, script] + cmd[script_idx+1:]
    if verbose:
        print("gatecheck: running check %s: %s" % (name, " ".join(full)), file=sys.stderr)
    try:
        proc = subprocess.run(full, cwd=ctx.root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              check=False)
    except OSError as e:
        return "check %s: cannot run: %s" % (name, e)
    if proc.returncode != 0:
        out = proc.stdout.decode("utf-8", "replace").strip().splitlines()
        return "check %s exited %d%s" % (name, proc.returncode, (": " + out[-1]) if out else "")
    return None


# ------------------------------------------------------------------------------------- main

def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="gatecheck.py", description=__doc__.split("\n")[0])
    ap.add_argument("--gate", metavar="TID", help="select the current milestone(s): those closed by TID")
    ap.add_argument("--compiler", default=None, help="compiler under test, passed to tools/axtest.py")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help="repository root (default: parent of tools/)")
    ap.add_argument("--no-run", action="store_true",
                    help="structure and rules (a), (c), (d) only; no tests, no check commands")
    ap.add_argument("-v", "--verbose", action="store_true")
    opts = ap.parse_args(argv)
    if opts.gate is not None and not TASK_ID_FULL_RE.match(opts.gate):
        ap.error("--gate needs a task id such as T022")
    ctx = Ctx(os.path.abspath(opts.root))
    compiler = opts.compiler
    if compiler and not os.path.isabs(compiler):
        compiler = os.path.abspath(compiler)

    problems = []          # global problems (structure, rules a/c/d): each one makes the exit 1
    board = load_board(ctx, problems)
    milestones, native_tasks, spec_text = parse_milestones(ctx, board, problems)
    features, _shortcuts = spec00_tables(spec_text) if spec_text else (set(), set())
    if opts.gate is not None and opts.gate not in board:
        problems.append("--gate %s is not a board task" % opts.gate)
    check_invariants(ctx, board, problems)
    directives = scan_directives(ctx)
    check_directives(ctx, board, problems, directives)
    check_subset(ctx, board, features, problems)

    due = [ms for ms in milestones
           if ms["gate"] == opts.gate or is_done(board.get(ms["gate"]))]
    if opts.gate is not None and not any(ms["gate"] == opts.gate for ms in milestones):
        problems.append("--gate %s closes no milestone" % opts.gate)

    # step 4 is part of the `gatecheck` check: native features of due milestones
    step4 = []
    for ms in due:
        for f in ms["native"]:
            for t in native_tasks.get(f, []):
                hits = [(rel, ln) for rel, ln, kind, task in directives
                        if kind == "native-after" and task == t]
                if hits:
                    step4.append("%s: native feature %s still has `native-after: %s` (%s:%d)"
                                 % (ms["id"], f, t, hits[0][0], hits[0][1]))
    problems.extend(step4)

    for p in problems:
        print("gatecheck: " + p)

    reasons = {ms["id"]: None for ms in due}
    allowed_modes = set(m for ms in due for m in ms["modes"])

    if not opts.no_run and due:
        prefixes = []
        runners = unit_runner_ids(ctx)
        covered = {}       # must_pass path -> test-id prefixes whose results count for it
        for ms in due:
            for p in ms["must_pass"]:
                abs_p = os.path.join(ctx.root, *p.split("/"))
                if not os.path.exists(abs_p):
                    reasons[ms["id"]] = reasons[ms["id"]] or "must_pass path %s does not exist" % p
                elif not path_has_tests(abs_p):
                    reasons[ms["id"]] = reasons[ms["id"]] or "must_pass path %s holds no test" % p
                else:
                    pre = [test_id_prefix(p)]
                    if has_c_unit_tests(abs_p):
                        if not runners:
                            reasons[ms["id"]] = reasons[ms["id"]] or (
                                "must_pass path %s holds C unit tests but no tests/unit manifest "
                                "runs axiom0-unit" % p)
                        pre += runners
                    covered[p] = pre
                    prefixes.extend(pre)
        results, err = (None, None)
        if prefixes:
            results, err = run_axtest(ctx, compiler, prefixes, opts.verbose)
        for ms in due:
            if reasons[ms["id"]]:
                continue
            if err:
                reasons[ms["id"]] = err
                continue
            mine = []
            for p in ms["must_pass"]:
                part = [r for r in (results or [])
                        if any(belongs(r.get("id", ""), q) for q in covered.get(p, []))]
                if not part:
                    reasons[ms["id"]] = "must_pass path %s: tools/axtest.py discovered no test" % p
                    break
                mine.extend(r for r in part if r not in mine)
            if not reasons[ms["id"]]:
                reasons[ms["id"]] = judge_results(mine, board, allowed_modes)
        check_cache = {}
        for ms in due:
            if reasons[ms["id"]]:
                continue
            for c in ms["checks"]:
                if c in INTERNAL_CHECKS:
                    r = ("gatecheck: " + problems[0]) if problems else None
                else:
                    if c not in check_cache:
                        check_cache[c] = run_check(ctx, c, opts.verbose)
                    r = check_cache[c]
                if r:
                    reasons[ms["id"]] = r
                    break
    elif due:
        for ms in due:
            if "gatecheck" in ms["checks"] and problems:
                reasons[ms["id"]] = "gatecheck: " + problems[0]

    # cumulative (AXS-BOOT-005): a milestone passes only if every earlier due milestone passes
    blocked_before = None
    for ms in due:
        r = reasons[ms["id"]]
        if r is None and blocked_before:
            r = "earlier milestone %s is blocked" % blocked_before
        if r is None:
            print("%s PASS" % ms["id"])
        else:
            print("%s BLOCKED: %s" % (ms["id"], r))
            blocked_before = blocked_before or ms["id"]
    if not due and opts.verbose:
        print("gatecheck: no milestone is due", file=sys.stderr)
    if problems or blocked_before:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
