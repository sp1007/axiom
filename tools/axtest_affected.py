#!/usr/bin/env python3
"""axtest_affected - test selection for the per-task QA gate (T437a): `--affected` and `--smoke`.

`axtest.py --affected <git-range | @file-list | path...>` selects the tests that can observe a change set
and prints, for every selected id, the rule that selected it (the derivation the QA file records). Rules, in
order (`.claude/agents/axiom-qa.md` "Per-task gate scope", T437a scope (b)):

 1. exact      a cached entry with `dep_source: exact` (tools/axtest_cache.py deps-index) whose compiler-reported
               dependency list contains a changed file selects that test (also a file created where the compiler
               probed an absent path, and any change inside a directory whose listing it used: T437b). Tests
               with such an entry are not subject to the grep rules 2a/2b below (their dependency list is
               exact).
 2a. test      a changed test file selects itself; any other changed file under tests/ (helper, expectation,
               fixture, generator) selects the tests of its directory (a `fixtures/`/`__pycache__/` directory
               counts as its parent) and every test whose `input:`/`stdout-file:` names it. Files directly in
               tests/ (README.md, smoke.list) are read by no compiled test and select nothing.
 2b. std       a changed std/ source selects the tests and std modules that reference its module path
               (`std.a.b`, `use std.a.b`, `std.a.b.Item`) or a public top-level name (`pub` item at column 0)
               declared or changed in its diff, transitively over std modules.
 2c. compiler  a changed compiler/<mod>/... file selects the test groups mapped from <mod> in
               tools/affected_map.txt; the bundle grep (a `module compiler.a.b` line in a selfhost bundle, or
               the module named in a bundle generator/template) selects the generator check manifest
               (`bundles_current.test`) of every directory whose bundles embed the changed module and the
               embedding bundles inside the module's own map targets; embedding bundles elsewhere are printed
               as DEFERRED (they observe the change only through the compiler binary, like every test; the
               periodic full run covers them). Applies even to tests with an exact entry (the compiler binary
               changes, so exact dependencies alone do not bound it).
 2d. tools     a changed tools/X.py (or tools/tests/X/...) selects the tool self-test directory tools/tests/X
               (longest tools/tests/<d> with X starting with d) and every test manifest whose `cmd:` names the
               tool.
 -   no-op     spec/, _workspaces/, .claude/, docs/ select nothing.
Changed files no rule matched are listed as UNMATCHED (the QA agent decides; the periodic full run covers
them).

`axtest.py --smoke [--seed N]` runs the `always:` ids of tests/smoke.list plus one id per top-level test
group drawn from its pool; `--smoke --check` validates the list (every group has a pool, every id exists, the
always: cases are present, the worst-case draw fits 20 minutes at -j 2 by the recorded durations).

CLI: `python tools/axtest_affected.py --check-map` validates tools/affected_map.txt.
Python 3 standard library only.
"""

import os
import random
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import axtest_cache  # noqa: E402

SMOKE_BOUND_S = 20 * 60
SMOKE_JOBS = 2
GREETING = "Xin chào thế giới".encode("utf-8")
NOOP_PREFIXES = ("spec/", "_workspaces/", ".claude/", "docs/")
SKIP_DIRS = {"fixtures", "__pycache__"}
PUB_DECL_RE = re.compile(r"\bpub\s+(?:unsafe\s+|const\s+|extern\s+\"[^\"]*\"\s+)*"
                         r"(?:fn|struct|enum|trait|type|const|static|union|mod|macro)\s+([A-Za-z_][A-Za-z0-9_]*)")


class AffectedError(Exception):
    pass


def git(root, *args):
    try:
        r = subprocess.run(["git", *args], cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise AffectedError("git %s: %s" % (" ".join(args), e))
    if r.returncode != 0:
        raise AffectedError("git %s failed: %s" % (" ".join(args), r.stderr.decode("utf-8", "replace").strip()))
    return r.stdout.decode("utf-8", "replace")


# ----------------------------------------------------------------------------------------------
# Change sets
# ----------------------------------------------------------------------------------------------

def norm(path, root):
    p = path.strip().replace("\\", "/")
    if os.path.isabs(p):
        try:
            p = Path(p).resolve().relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            pass
    while p.startswith("./"):
        p = p[2:]
    return p


def is_range(arg, root):
    return ".." in arg and not arg.startswith("@") and not (Path(root) / arg).exists()


def changed_files(root, args):
    """(sorted changed paths, diff_fn) where diff_fn(path) returns the unified diff text of that path (or
    None when no diff is available)."""
    if len(args) == 1 and is_range(args[0], root):
        rng = args[0]
        a, _, b = rng.partition("...") if "..." in rng else rng.partition("..")
        a = a or "HEAD"
        b = b or "HEAD"
        out = git(root, "diff", "--name-only", "-z", "--no-renames", a, b)
        files = sorted({norm(p, root) for p in out.split("\0") if p.strip()})

        def diff_fn(path, a=a, b=b):
            try:
                return git(root, "diff", "--no-renames", "-U0", a, b, "--", path)
            except AffectedError:
                return None
        diff_fn.sides = (a, b)
        return files, diff_fn
    files = []
    for a in args:
        if a.startswith("@"):
            with open(a[1:], "rb") as f:
                for line in f.read().decode("utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        files.append(norm(line, root))
        else:
            files.append(norm(a, root))

    def diff_fn(path):
        try:
            txt = git(root, "diff", "--no-renames", "-U0", "HEAD", "--", path)
        except AffectedError:
            return None
        return txt if txt.strip() else None
    diff_fn.sides = ("HEAD", None)          # None = the working tree
    return sorted(set(files)), diff_fn


def file_at(root, rev, path):
    """Text of `path` at git revision `rev` (None = working tree), or None when it does not exist there."""
    if rev is None:
        p = Path(root) / path
        return p.read_bytes().decode("utf-8", "replace") if p.is_file() else None
    try:
        r = subprocess.run(["git", "show", "%s:%s" % (rev, path)], cwd=str(root), stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


# ----------------------------------------------------------------------------------------------
# Module paths and names
# ----------------------------------------------------------------------------------------------

def module_path(rel, top):
    """`std/a/b.ax` -> `std.a.b`; `std/a/b/mod.ax` -> `std.a.b` (same for compiler/)."""
    if not rel.endswith(".ax"):
        return None
    parts = rel[:-3].split("/")
    if parts[0] != top:
        return None
    if parts[-1] == "mod":
        parts = parts[:-1]
    return ".".join(parts)


def top_level_pub(text):
    """Names of public top-level items (`pub ...` at column 0) in one line of source."""
    if not text.startswith("pub"):
        return []
    return PUB_DECL_RE.findall(text)


TYPE_DECL_RE = re.compile(r"^[ \t]*(?:pub(?:\([^)]*\))?[ \t]+)?(?:unsafe[ \t]+)?(?:struct|enum|trait|type|union)"
                          r"[ \t]+([A-Za-z_][A-Za-z0-9_]*)", re.M)
IMPL_RE = re.compile(r"^[ \t]*(?:unsafe[ \t]+)?impl\b[ \t]*(?:<[^{\n]*?>)?[ \t]*"
                     r"(?:[A-Za-z_][A-Za-z0-9_.]*[ \t]*(?:<[^{\n]*?>)?[ \t]+for[ \t]+)?"
                     r"(?:[A-Za-z_][A-Za-z0-9_]*\.)*([A-Za-z_][A-Za-z0-9_]*)", re.M)
TOP_FN_RE = re.compile(r"^(?:pub(?:\([^)]*\))?[ \t]+)?(?:unsafe[ \t]+|const[ \t]+|extern[ \t]+\"[^\"]*\"[ \t]+)*fn[ \t]+")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PUB_USE_RE = re.compile(r"^pub[ \t]+use[ \t]+[A-Za-z_][A-Za-z0-9_.]*?\.?([A-Za-z_][A-Za-z0-9_]*)[ \t]*;?[ \t]*$")


def _header_names(ctx):
    """Names from git's hunk-header context (the enclosing column-0 declaration): the implemented type of an
    `impl [<..>] [Trait for] Type` line, a type/trait declaration, or a public top-level item."""
    names = set(IMPL_RE.findall(ctx))
    names.update(TYPE_DECL_RE.findall(ctx))
    names.update(top_level_pub(ctx))
    return names


# ----------------------------------------------------------------------------------------------
# Declaration scanner (T437a QA F6): which item(s) contain a given line of a std file
# ----------------------------------------------------------------------------------------------

ITEM_KW = ("fn", "impl", "trait", "struct", "enum", "union", "type", "const", "static", "macro", "mod", "extern")
CONTAINER_KINDS = ("impl", "trait", "mod", "extern")      # bodies that hold items
BRACE_BODY_KINDS = ("fn", "struct", "enum", "union", "macro", "impl", "trait", "mod", "extern")
ITEM_START_RE = re.compile(
    r"(?:pub(?:\s*\([^)\n]*\))?\s+)?(?:(?:unsafe|async|default|const(?=\s+(?:unsafe\s+)?fn\b)|"
    r"extern\s+\"[^\"\n]*\"(?=\s+(?:unsafe\s+)?fn\b))\s+)*"
    r"(fn|impl|trait|struct|enum|union|type|const|static|macro|mod|extern)\b")
ATTR_LINE_RE = re.compile(r"^\s*(?:@[A-Za-z_][A-Za-z0-9_]*|#!?\[)")
FILE_WIDE_LINE_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:use|module|import)\b")
TRAIT_IMPL_RE = re.compile(r"\bimpl\b\s*(?:<[^{\n]*?>)?\s*(?:[A-Za-z_][A-Za-z0-9_]*\.)*([A-Za-z_][A-Za-z0-9_]*)"
                           r"\s*(?:<[^{\n]*?>)?\s+for\s+(?:[A-Za-z_][A-Za-z0-9_]*\.)*([A-Za-z_][A-Za-z0-9_]*)")


def blank_noise(text):
    """Source text with comments and string/char literal contents replaced by spaces (same length, same line
    structure), so braces and keywords inside them are not seen by the scanner."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            depth = 0
            while i < n:
                if text.startswith("/*", i):
                    depth += 1
                    out[i] = out[i + 1] = " "
                    i += 2
                    continue
                if text.startswith("*/", i):
                    depth -= 1
                    out[i] = out[i + 1] = " "
                    i += 2
                    if depth == 0:
                        break
                    continue
                if text[i] != "\n":
                    out[i] = " "
                i += 1
        elif c == '"':
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    out[i] = " "
                    i += 1
                if text[i] != "\n":
                    out[i] = " "
                i += 1
            i += 1
        elif c == "'" and i + 2 < n and (text[i + 2] == "'" or (text[i + 1] == "\\" and "'" in text[i + 2:i + 12])):
            j = text.index("'", i + 2) if text[i + 1] == "\\" else i + 2
            for k in range(i + 1, j):
                out[k] = " "
            i = j + 1
        else:
            i += 1
    return "".join(out)


class Item:
    __slots__ = ("kind", "name", "pub", "start", "end", "parent", "impl_type", "impl_trait", "members")

    def __init__(self, kind, name, pub, start, parent):
        self.kind, self.name, self.pub, self.start, self.end, self.parent = kind, name, pub, start, None, parent
        self.impl_type = self.impl_trait = None
        self.members = []

    def __repr__(self):
        return "Item(%s %s %d-%s)" % (self.kind, self.name, self.start, self.end)


class Decls:
    """Items of one source file with 1-based inclusive line ranges. Items are recognised at item position
    only (file top level and inside impl/trait/mod/extern bodies); anything inside a fn/struct/... body belongs
    to that item. `ok` is False when the braces do not balance (the caller treats every line as unresolved)."""

    def __init__(self, text):
        self.text = text
        self.items = []
        self.ok = True
        self.lines = text.split("\n")
        code = blank_noise(text)
        self.code_lines = code.split("\n")
        self._scan(code)

    def _line_of(self, pos, starts):
        lo, hi = 0, len(starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    def _scan(self, code):
        starts = [0]
        for i, ch in enumerate(code):
            if ch == "\n":
                starts.append(i + 1)
        n = len(code)
        stack = []        # frames: ("container", item) | ("body", item) | ("other", None)
        cur = None        # the item being declared at the current item level (not yet in its body)
        cur_depth = 0     # nesting of (), [], {} of `cur` before its body opens / for brace-less items
        i = 0
        tok_re = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[{}();\[\]\n]")
        at_item_level = lambda: not stack or stack[-1][0] == "container"
        line_start = True
        while i < n:
            m = tok_re.search(code, i)
            if not m:
                break
            tok = m.group(0)
            i = m.end()
            if tok == "\n":
                line_start = True
                continue
            was_line_start, line_start = line_start, False
            if at_item_level() and (cur is None or (cur.kind in ("type", "const", "static") and cur_depth == 0
                                                     and was_line_start)):
                sm = ITEM_START_RE.match(code, m.start())
                if sm and (cur is None or was_line_start):
                    kw = sm.group(1)
                    rest = code[sm.end():sm.end() + 200]
                    nm = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", rest)
                    valid = kw in ("impl", "extern") or (nm is not None and not (kw == "fn" and rest.lstrip()
                                                                                   .startswith("(")))
                    if kw == "extern" and not re.match(r'\s*"[^"\n]*"\s*\{', code[sm.end(1):sm.end(1) + 80]):
                        valid = False
                    if valid:
                        if cur is not None:                     # a brace-less item ended on the previous line
                            cur.end = self._line_of(m.start(), starts) - 1
                            cur = None
                        parent = stack[-1][1] if stack else None
                        name = nm.group(1) if nm and kw not in ("impl", "extern") else None
                        pub = code[m.start():sm.end()].lstrip().startswith("pub")
                        it = Item(kw, name, pub, self._line_of(m.start(), starts), parent)
                        if kw == "impl":
                            head = code[m.start():code.find("{", m.start()) if "{" in code[m.start():] else n]
                            tm = TRAIT_IMPL_RE.search(head)
                            if tm:
                                it.impl_trait, it.impl_type = tm.group(1), tm.group(2)
                            else:
                                im = IMPL_RE.search(head)
                                it.impl_type = im.group(1) if im else None
                            it.name = it.impl_type
                        self.items.append(it)
                        if parent is not None:
                            parent.members.append(it)
                        cur, cur_depth = it, 0
                        i = sm.end()
                        continue
            if (cur is not None and cur.kind in ("type", "const", "static") and cur_depth == 0 and was_line_start
                    and (m.start() == 0 or code[m.start() - 1] == "\n")):
                # an unindented line that starts no item ends a brace-less item (`const X = 1` without `;`):
                # continuation lines of its initializer are indented; this line belongs to no declaration
                cur.end = self._line_of(m.start(), starts) - 1
                cur = None
            if cur is not None:
                # tokens of the item being declared, before its body
                if tok in "([":
                    cur_depth += 1
                elif tok in ")]":
                    cur_depth -= 1
                elif tok == ";" and cur_depth == 0:
                    cur.end = self._line_of(m.start(), starts)
                    cur = None
                elif tok == "{":
                    if cur.kind in BRACE_BODY_KINDS and cur_depth == 0:
                        stack.append(("container" if cur.kind in CONTAINER_KINDS else "body", cur))
                        cur = None
                    else:
                        cur_depth += 1
                elif tok == "}":
                    if cur_depth > 0:
                        cur_depth -= 1
                    else:                                 # closes the enclosing container: brace-less item ends
                        cur.end = self._line_of(m.start(), starts) - 1
                        cur = None
                        self._close(stack, m.start(), starts)
                continue
            if tok == "{":
                stack.append(("other", None))
            elif tok == "}":
                if not stack:
                    self.ok = False
                    continue
                self._close(stack, m.start(), starts)
        if cur is not None:
            cur.end = len(starts)
        if stack:
            self.ok = False
            for kind, it in stack:
                if it is not None and it.end is None:
                    it.end = len(starts)
        for it in self.items:
            if it.end is None:
                it.end = len(starts)
                self.ok = False
            if it.end < it.start:
                it.end = it.start
            # a brace-less item ended by the next item's start: trailing blank/comment/attribute lines belong to
            # the next item (or to nothing)
            while it.end > it.start and (not self.code_lines[it.end - 1].strip()
                                         or ATTR_LINE_RE.match(self.code_lines[it.end - 1])):
                it.end -= 1

    def _close(self, stack, pos, starts):
        kind, it = stack.pop()
        if it is not None:
            it.end = self._line_of(pos, starts)

    def chain(self, line):
        """Items containing `line`, outermost first."""
        out = [it for it in self.items if it.start <= line <= it.end]
        out.sort(key=lambda it: (it.start, -it.end))
        return out

    def next_item(self, line):
        """The item an attribute line belongs to: the first item starting after `line`, provided only
        attribute / blank / comment lines lie between."""
        for it in sorted(self.items, key=lambda x: x.start):
            if it.start > line:
                for ln in range(line + 1, it.start):
                    s = self.code_lines[ln - 1].strip() if ln - 1 < len(self.code_lines) else ""
                    if s and not ATTR_LINE_RE.match(self.code_lines[ln - 1]):
                        return None
                return it
        return None

    def is_noise(self, line):
        """Blank or comment-only line."""
        return line - 1 >= len(self.code_lines) or not self.code_lines[line - 1].strip()

    def top(self, it):
        while it.parent is not None:
            it = it.parent
        return it

    def item_text(self, it):
        return "\n".join(self.code_lines[it.start - 1:it.end])

    def labels(self, it):
        """The names a test can reference to reach item `it`: a public top-level item's own name; an impl
        member -> the implemented type (and trait); a trait (member) -> the trait, its implementers in this
        file and the member's name (default bodies run for every implementer); a public member of an extern
        block -> its name. A private top-level item has no label (reached through its users)."""
        top = self.top(it)
        out = set()
        if top.kind == "impl":
            out.update(x for x in (top.impl_type, top.impl_trait) if x)
        elif top.kind == "trait":
            if top.name:
                out.add(top.name)
                out.update(self.implementers(top.name))
            if it is not top and it.name:
                out.add(it.name)
        elif top.kind in ("mod", "extern"):
            if top.pub and top.name:
                out.add(top.name)
            if it is not top and it.pub and it.name:
                out.add(it.name)
        elif top.pub and top.name:
            out.add(top.name)
        return out

    def implementers(self, trait):
        return {it.impl_type for it in self.items if it.kind == "impl" and it.impl_trait == trait and it.impl_type}

    def users_closure(self, seeds):
        """Seed items plus every item that (transitively) mentions the name of one of them (in-file callers)."""
        units = [it for it in self.items if it.parent is None or it.parent.kind in CONTAINER_KINDS]
        texts = {id(u): self.item_text(u) for u in units}
        done = []
        seen = set()
        todo = list(seeds)
        while todo:
            it = todo.pop()
            if id(it) in seen:
                continue
            seen.add(id(it))
            done.append(it)
            names = {it.name} if it.name else set()
            if it.kind in ("impl", "trait"):
                names |= {x.name for x in it.members if x.name}
            names.discard(None)
            if not names:
                continue
            rx = re.compile(r"(?<![A-Za-z0-9_])(?:%s)(?![A-Za-z0-9_])" % "|".join(re.escape(x) for x in names))
            for u in units:
                if id(u) in seen or u is it or self._contains(u, it):
                    continue
                if rx.search(texts[id(u)]):
                    todo.append(u)
        return done

    @staticmethod
    def _contains(outer, inner):
        p = inner.parent
        while p is not None:
            if p is outer:
                return True
            p = p.parent
        return False

    def file_names(self):
        """Every label of the file (public top-level names, implemented types/traits, trait members)."""
        out = set()
        for it in self.items:
            out |= self.labels(it)
        return out


HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def diff_changed_lines(diff_text):
    """[(hunk header, [old line numbers removed], [new line numbers added], {line: text})] of a unified diff."""
    out = []
    cur = None
    o = nw = 0
    for line in diff_text.splitlines():
        m = HUNK_RE.match(line)
        if m:
            o, nw = int(m.group(1)), int(m.group(3))
            cur = {"header": line, "ctx": m.group(5), "old": [], "new": [], "text_old": {}, "text_new": {},
                   "new_file": m.group(1) == "0" and m.group(2) == "0", "pos_new": []}
            out.append(cur)
            continue
        if cur is None or line.startswith(("+++", "---", "\\")):
            continue
        if line.startswith("-"):
            cur["old"].append(o)
            cur["text_old"][o] = line[1:]
            cur["pos_new"].append(nw)
            o += 1
        elif line.startswith("+"):
            cur["new"].append(nw)
            cur["text_new"][nw] = line[1:]
            nw += 1
        else:
            o += 1
            nw += 1
    return out


def derive_names(diff_text, file_text, old_text=None, rel=None):
    """(names, unresolved) for one changed std file (T437a QA F4, F6).

    Every changed line is attributed to the declaration(s) containing it, found from its position in the file:
    `+` lines in the NEW file, `-` lines in the OLD file (`old_text`; a pure deletion is seen there). The affected
    items are those declarations plus every item of the same file that (transitively) mentions one of their names
    (in-file callers); their labels are the names (see Decls.labels): a public top-level item's name, the type
    and trait of an `impl` block, a trait with its implementers and the member name. A changed attribute line
    belongs to the item below it; a `use`/`module` line affects the whole file (every label of the file). A
    changed code line outside any declaration, a file whose braces do not balance, or affected items without any
    label are UNRESOLVED (the caller selects a whole group and every label of the file): nothing is dropped
    silently. Blank and comment-only lines carry no semantics and are ignored."""
    if file_text is None and old_text is None:
        return _derive_names_headers(diff_text)
    new_d = Decls(file_text) if file_text is not None else None
    old_d = Decls(old_text) if old_text is not None else None
    if not diff_text:
        names = set()
        for d in (new_d, old_d):
            if d is not None:
                names |= d.file_names()
        return names, []
    names = set()
    unresolved = []
    file_wide = False
    for h in diff_changed_lines(diff_text):
        per_side = []
        if h["new"]:
            per_side.append((new_d, h["new"], h["text_new"], "+"))
        if h["old"]:
            if old_d is not None:
                per_side.append((old_d, h["old"], h["text_old"], "-"))
            elif new_d is not None:
                # no old text: a removed line sits where the new file continues; attribute it there (and to any
                # declaration the removed line itself spells)
                per_side.append((new_d, sorted(set(max(1, p) for p in h["pos_new"])), {}, "~"))
                for t in h["text_old"].values():
                    names.update(top_level_pub(t))
                    names.update(IMPL_RE.findall(t))
                    names.update(TYPE_DECL_RE.findall(t))
        hunk_unres = []
        for d, lines, texts, side in per_side:
            if d is None:
                hunk_unres.append("%s lines without file text" % side)
                continue
            seeds = []
            for ln in lines:
                if side != "~" and d.is_noise(ln):
                    continue
                if not d.ok:
                    hunk_unres.append("braces of the %s file do not balance" % ("new" if side != "-" else "old"))
                    break
                ch = d.chain(ln)
                if ch:
                    seeds.append(ch[-1])
                    continue
                code = d.code_lines[ln - 1] if ln - 1 < len(d.code_lines) else ""
                if ATTR_LINE_RE.match(code):
                    it = d.next_item(ln)
                    if it is not None:
                        seeds.append(it)
                        continue
                if FILE_WIDE_LINE_RE.match(code):
                    file_wide = True
                    m = PUB_USE_RE.match(code.strip())
                    if m:
                        names.add(m.group(1))          # `pub use a.b.Name` re-exports Name
                    continue
                if side == "~":
                    continue
                hunk_unres.append("%s line %d `%s` is outside any declaration" % (side, ln, code.strip()[:60]))
            if seeds:
                got = set()
                for it in d.users_closure(seeds):
                    got |= d.labels(it)
                if not got:
                    # e.g. private dead code: nothing names it; be conservative
                    got = d.file_names()
                if got:
                    names |= got
                elif not h["new_file"]:     # a new file is reached through its module path until it exports
                    hunk_unres.append("%s change in %s yields no name" % (side, ", ".join(
                        sorted({"%s %s" % (s.kind, s.name or "") for s in seeds}))))
        if hunk_unres:                 # one entry per hunk (both sides may report the same line)
            uniq = []
            for u in hunk_unres:
                if u.split(" ", 1)[1] not in [x.split(" ", 1)[1] for x in uniq]:
                    uniq.append(u)
            unresolved.append("hunk `%s`: %s" % (h["header"].strip()[:80], "; ".join(uniq)))
    if file_wide or unresolved:
        for d in (new_d, old_d):
            if d is not None:
                names |= d.file_names()
    return names, unresolved


def _derive_names_headers(diff_text):
    """Fallback without any file text: the T437a round-1 rules on the diff alone (hunk-header context and the
    changed lines). Only used by direct callers that pass no file text; `derive` always passes both sides."""
    file_text = None
    names = set()
    unresolved = []
    declared = set(TYPE_DECL_RE.findall(file_text)) if file_text else set()
    file_pub = set()
    if file_text:
        for line in file_text.splitlines():
            file_pub.update(top_level_pub(line))
    if not diff_text:
        return (file_pub | declared), []
    hunks = []
    cur = None
    for line in diff_text.splitlines():
        if line.startswith("@@"):
            parts = line.split("@@", 2)
            cur = {"header": line, "ctx": parts[2] if len(parts) > 2 else "", "lines": []}
            hunks.append(cur)
        elif cur is not None and line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            cur["lines"].append(line[1:])
    for h in hunks:
        got = set()
        ctx = h["ctx"].lstrip(" ")
        got |= _header_names(ctx)
        for text in h["lines"]:
            got.update(top_level_pub(text))
            got.update(IMPL_RE.findall(text))
            got.update(TYPE_DECL_RE.findall(text))
            if declared:
                got.update(x for x in IDENT_RE.findall(text) if x in declared)
        private_fn = bool(TOP_FN_RE.match(ctx)) and not ctx.startswith("pub")
        for text in h["lines"]:
            m = PUB_USE_RE.match(text)
            if m:
                got.add(m.group(1))       # `pub use a.b.Name` re-exports Name
        if not got or private_fn:
            got |= file_pub | declared
        if got:
            names |= got
        elif h["header"].startswith("@@ -0,0 "):
            pass    # a new file: nothing can name it yet except through its module path (module-path rule)
        else:
            unresolved.append("hunk `%s` yields no name" % h["header"].strip()[:120])
    return names, unresolved


def public_names(diff_text, file_text):
    """Names derived for a changed std file (see derive_names)."""
    return derive_names(diff_text, file_text)[0]


# ----------------------------------------------------------------------------------------------
# The affected-map table
# ----------------------------------------------------------------------------------------------

def read_map(root):
    path = Path(root) / "tools" / "affected_map.txt"
    rows = {}
    problems = []
    if not path.is_file():
        return rows, ["tools/affected_map.txt does not exist"]
    for ln, line in enumerate(path.read_bytes().decode("utf-8").splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^(compiler/[A-Za-z0-9_]+)\s*->\s*(.*)$", s)
        if not m:
            problems.append("affected_map.txt line %d: expected `compiler/<mod> -> <tests/...> ...`" % ln)
            continue
        if m.group(1) in rows:
            problems.append("affected_map.txt line %d: duplicate row for %s" % (ln, m.group(1)))
        rows[m.group(1)] = m.group(2).split()
    return rows, problems


def tracked_paths(root):
    """The set of files git tracks under compiler/ and tests/ (HEAD + index), or None outside a git checkout."""
    try:
        r = subprocess.run(["git", "ls-files", "--", "compiler", "tests"], cwd=str(root), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return set(r.stdout.decode("utf-8", "replace").splitlines())


def _tracked(path, tracked):
    if tracked is None:
        return None
    pre = path.rstrip("/") + "/"
    return path in tracked or any(f.startswith(pre) for f in tracked)


def check_map(root, notes=None):
    """Problems (the table is unusable): a tracked compiler/<mod> directory without a row, a row whose module is
    not a directory, a row without targets, a target outside tests/.

    Notes (printed, not failures; T437a QA F2): a target that does not exist or is not tracked by git (e.g. an
    untracked directory of another task's in-progress work) and an untracked module directory without a row.
    Such targets are skipped by the selection, so a gate never depends on another task's working files."""
    root = Path(root)
    rows, problems = read_map(root)
    notes = notes if notes is not None else []
    tracked = tracked_paths(root)
    comp = root / "compiler"
    mods = sorted("compiler/" + d.name for d in comp.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))) \
        if comp.is_dir() else []
    for m in mods:
        if m not in rows:
            if _tracked(m, tracked) is False:
                notes.append("affected_map.txt: untracked module directory %s has no row (ignored)" % m)
            else:
                problems.append("affected_map.txt: no row for module directory %s" % m)
    for m, targets in sorted(rows.items()):
        if not (root / m).is_dir():
            problems.append("affected_map.txt: row for %s, which is not a directory" % m)
        if not targets:
            problems.append("affected_map.txt: row %s has no targets" % m)
        for t in targets:
            if not t.startswith("tests/"):
                problems.append("affected_map.txt: %s target %s does not start with tests/" % (m, t))
            elif not (root / t).exists():
                notes.append("affected_map.txt: %s target %s does not exist (skipped)" % (m, t))
            elif _tracked(t, tracked) is False:
                notes.append("affected_map.txt: %s target %s is not tracked by git (skipped)" % (m, t))
    return problems


def usable_target(root, t, tracked):
    return (Path(root) / t).exists() and _tracked(t, tracked) is not False


# ----------------------------------------------------------------------------------------------
# Derivation
# ----------------------------------------------------------------------------------------------

class Affected:
    def __init__(self, changed):
        self.changed = changed
        self.reasons = {}          # id -> [rule text]
        self.tools = {}            # tools/tests/X -> [rule text]
        self.unmatched = []
        self.noop = []
        self.exact_ids = set()
        self.deferred = {}         # id -> [rule text]: observable, but left to the periodic full run
        self.notes = []            # MAP-NOTE lines (skipped map targets)
        self.unresolved = []       # changed files whose affected names could not be derived

    def defer(self, tid, rule):
        lst = self.deferred.setdefault(tid, [])
        if rule not in lst:
            lst.append(rule)

    def add(self, tid, rule):
        lst = self.reasons.setdefault(tid, [])
        if rule not in lst:
            lst.append(rule)

    @property
    def ids(self):
        return sorted(self.reasons)

    def groups(self):
        g = {}
        for t in self.reasons:
            k = t.split("/", 1)[0]
            g[k] = g.get(k, 0) + 1
        return dict(sorted(g.items()))

    def lines(self):
        out = ["AFFECTED-CHANGED %d file(s)" % len(self.changed)]
        for f in self.changed:
            out.append("  changed %s" % f)
        for tid in self.ids:
            rs = self.reasons[tid]
            out.append("SELECT %s  <- %s%s" % (tid, rs[0], (" (+%d more)" % (len(rs) - 1)) if len(rs) > 1 else ""))
        for t in sorted(self.tools):
            out.append("TOOL %s  <- %s" % (t, self.tools[t][0]))
        for g, n in self.groups().items():
            out.append("GROUP %s %d" % (g, n))
        for tid in sorted(self.deferred):
            if tid not in self.reasons:
                out.append("DEFERRED %s  <- %s" % (tid, self.deferred[tid][0]))
        for f in self.noop:
            out.append("NOOP %s" % f)
        for n in self.notes:
            out.append("MAP-NOTE %s" % n)
        for u in self.unresolved:
            out.append("UNRESOLVED %s" % u)
        for f in self.unmatched:
            out.append("UNMATCHED %s" % f)
        out.append("AFFECTED TOTAL %d test id(s), %d tool self-test dir(s), %d unmatched, %d deferred" %
                   (len(self.reasons), len(self.tools), len(self.unmatched),
                    len([t for t in self.deferred if t not in self.reasons])))
        return out

    def as_dict(self):
        return {"changed": self.changed, "ids": {t: self.reasons[t] for t in self.ids},
                "tools": {t: self.tools[t] for t in sorted(self.tools)}, "groups": self.groups(),
                "unmatched": self.unmatched, "noop": self.noop, "notes": self.notes,
                "unresolved": self.unresolved,
                "deferred": {t: self.deferred[t] for t in sorted(self.deferred) if t not in self.reasons}}


class Corpus:
    """Test-side files: which test ids a file belongs to."""

    def __init__(self, root, tests):
        self.root = Path(root)
        self.tests = tests
        self.by_rel = {}               # tests/<id> (file or project dir) -> id
        self.projects = []             # (tests/<id>/, id)
        for t in tests:
            rel = "tests/" + t.id
            self.by_rel[rel] = t.id
            if Path(t.path).is_dir():
                self.projects.append((rel + "/", t.id))
        self._files = None

    def ids_under(self, rel_dir):
        pre = rel_dir.rstrip("/") + "/"
        return sorted(t.id for t in self.tests if ("tests/" + t.id).startswith(pre))

    def ids_in_dir_of(self, rel):
        d = rel.rsplit("/", 1)[0] if "/" in rel else ""
        while d and d.rsplit("/", 1)[-1] in SKIP_DIRS:
            d = d.rsplit("/", 1)[0] if "/" in d else ""
        if d in ("", "tests"):
            return []
        return self.ids_under(d)

    def owner_ids(self, rel):
        """The test id(s) a test-side file belongs to (a test, a project, or its directory's tests)."""
        if rel in self.by_rel:
            return [self.by_rel[rel]]
        for pre, tid in self.projects:
            if rel.startswith(pre):
                return [tid]
        return self.ids_in_dir_of(rel)

    def files(self):
        """[(rel, bytes)] of every test-side source/manifest/template (read once)."""
        if self._files is None:
            out = []
            base = self.root / "tests"
            for dirpath, dirnames, filenames in os.walk(str(base)):
                dirnames[:] = sorted(d for d in dirnames if d != "__pycache__" and not d.startswith("."))
                for fn in sorted(filenames):
                    if fn.endswith((".ax", ".test", ".ax.in")):
                        p = os.path.join(dirpath, fn)
                        try:
                            data = Path(p).read_bytes()
                        except OSError:
                            continue
                        if not fn.endswith(".test"):
                            data = code_only(data)
                        out.append((Path(p).relative_to(self.root).as_posix(), data))
            self._files = out
        return self._files


CODE_NOISE_RE = re.compile(rb'"(?:\\.|[^"\\\n])*"' + rb"|'(?:\\.|[^'\\\n])'" + rb"|//[^\n]*")
DECL_NAME_RE = re.compile(rb"\b(?:fn|struct|enum|trait|type|const|static|union|mod)\s+([A-Za-z_][A-Za-z0-9_]*)")


def code_only(data):
    """Source bytes without string/char literals and line comments (a module path inside a diagnostic
    message or a comment is not a reference). Line structure is kept, so `^module ...` lines survive."""
    return CODE_NOISE_RE.sub(b"", data)


def std_files(root):
    base = Path(root) / "std"
    out = []
    if base.is_dir():
        for p in sorted(base.rglob("*.ax")):
            out.append((p.relative_to(root).as_posix(), code_only(p.read_bytes())))
    return out


class RefMatcher:
    """Finds whole-identifier occurrences of many literal tokens fast: a substring prefilter (bytes `in`, C
    speed) picks the tokens present in a file, and a small regex compiled for exactly that subset checks the
    identifier boundaries. (One alternation of ~100 names over the 260 MB test corpus is minutes; this is
    seconds.)"""

    def __init__(self, tokens):
        self.tokens = sorted({t.encode("utf-8") for t in tokens}, key=len, reverse=True)
        self._rx = {}

    def _regex(self, subset):
        rx = self._rx.get(subset)
        if rx is None:
            rx = re.compile(b"|".join(rb"(?<![A-Za-z0-9_])" + re.escape(t) + rb"(?![A-Za-z0-9_])" for t in subset))
            self._rx[subset] = rx
        return rx

    def all(self, data):
        """Every token (str) that occurs as a whole identifier/path in data, in first-occurrence order."""
        subset = tuple(t for t in self.tokens if t in data)
        if not subset:
            return []
        seen = []
        for m in self._regex(subset).finditer(data):
            tok = m.group(0).decode("utf-8", "replace")
            if tok not in seen:
                seen.append(tok)
                if len(seen) == len(subset):
                    break
        return seen

    def first(self, data):
        subset = tuple(t for t in self.tokens if t in data)
        if not subset:
            return None
        m = self._regex(subset).search(data)
        return m.group(0).decode("utf-8", "replace") if m else None


def derive(root, args, tests, cache_dir=None):
    root = Path(root)
    changed, diff_fn = changed_files(root, args)
    aff = Affected(changed)
    corpus = Corpus(root, tests)
    exact = axtest_cache.load_exact_deps_index(cache_dir) if cache_dir else {}
    known_ids = {t.id for t in tests}
    exact = {k: set(v) for k, v in exact.items() if k in known_ids}
    aff.exact_ids = set(exact)
    changed_set = set(changed)

    # rule 1: exact dependency lists
    sentinel_tail = "/" + axtest_cache.DIRLIST_SENTINEL
    for tid, deps in sorted(exact.items()):
        hit = sorted(changed_set & deps)
        if not hit:
            # a listed directory (T437b `--dep-file` `<dir>/ dir`): any change inside it
            hit = sorted(f for f in changed_set for d in deps
                         if d.endswith(sentinel_tail) and axtest_cache.dep_matches_change(d, f))
        if hit:
            aff.add(tid, "exact: dependency %s" % hit[0])

    def grep_ok(tid):
        return tid not in exact

    std_mods = {}
    std_names = set()
    comp_changes = []
    test_by_input = {}
    for t in tests:
        p = Path(t.path)
        for q in ([Path(t.input)] if Path(t.input) != p else []) + \
                ([p.parent / t.stdout_file] if t.stdout_file else []):
            try:
                rel = q.resolve().relative_to(root.resolve()).as_posix()
            except (ValueError, OSError):
                continue
            test_by_input.setdefault(rel, []).append(t.id)

    # rule 2c (T437b round 1): a changed file at or under a `cache-inputs:` path selects the test, whatever
    # its location (a declared run-time input is a key input in both cache modes, ADR-0041 S4)
    declared = []
    for t in tests:
        for ci in getattr(t, "cache_inputs", None) or []:
            q = Path(ci)
            if not q.is_absolute():
                q = root / q
            try:
                rel = Path(os.path.normpath(str(q))).resolve().relative_to(root.resolve()).as_posix()
            except (ValueError, OSError):
                continue
            declared.append((rel.rstrip("/"), t.id))
    declared_hit = set()
    for f in changed:
        for rel, tid in declared:
            if rel == "." or f == rel or f.startswith(rel + "/"):
                aff.add(tid, "test: cache-inputs: %s names %s" % (rel, f))
                declared_hit.add(f)

    for f in changed:
        if f.startswith(NOOP_PREFIXES):
            aff.noop.append(f)
            continue
        if f.startswith("tests/"):
            matched = f in declared_hit
            if f in corpus.by_rel:
                aff.add(corpus.by_rel[f], "test: changed test file")
                matched = True
            else:
                if f.count("/") == 1:
                    aff.noop.append(f)       # tests/README.md, tests/smoke.list: read by no compiled test
                    continue
                # rule 2a applies to exact entries too (T437b round 1, QA F1): a program may read files of its
                # own directory at run time, which no compiler dependency list records
                for tid in corpus.owner_ids(f):
                    aff.add(tid, "test: %s is in the test's directory" % f)
                    matched = True
            for tid in test_by_input.get(f, []):
                aff.add(tid, "test: input:/stdout-file: names %s" % f)
                matched = True
            if not matched:
                if not (root / f).exists():
                    aff.noop.append(f + " (deleted test-side file)")
                else:
                    aff.unmatched.append(f)
            continue
        if f.startswith("std/"):
            mod = module_path(f, "std")
            if mod is None:
                aff.noop.append(f + " (not a std source)")
                continue
            std_mods[mod] = f
            old_rev, new_rev = getattr(diff_fn, "sides", ("HEAD", None))
            got, unres = derive_names(diff_fn(f), file_at(root, new_rev, f), file_at(root, old_rev, f), f)
            std_names |= got
            for u in unres:
                aff.unresolved.append("%s: %s" % (f, u))
            continue
        if f.startswith("compiler/"):
            comp_changes.append(f)
            continue
        if f.startswith("tools/"):
            if not tools_rule(root, f, aff, corpus) and f not in declared_hit:
                aff.unmatched.append(f)
            continue
        if f not in declared_hit:
            aff.unmatched.append(f)

    if std_mods:
        std_rule(root, std_mods, std_names, aff, corpus, grep_ok)
    if aff.unresolved:
        # nothing silently selected: an underivable std change selects its whole top-level test group
        for tid in corpus.ids_under("tests/std"):
            aff.add(tid, "unresolved std change: whole group std (%s)" % aff.unresolved[0].split(":", 1)[0])
    if comp_changes:
        problems = check_map(root, aff.notes)
        if problems:
            raise AffectedError("tools/affected_map.txt is invalid:\n  " + "\n  ".join(problems))
        compiler_rule(root, comp_changes, aff, corpus, tests)
    return aff


def std_rule(root, std_mods, names, aff, corpus, grep_ok):
    modules = set(std_mods)
    sfiles = std_files(root)
    # transitive closure over std modules that reference a module/name of the set
    via = {m: "%s changed" % std_mods[m] for m in modules}
    names_m = RefMatcher(names) if names else None
    changed_once = True
    while changed_once:
        changed_once = False
        mods_m = RefMatcher(modules)
        for rel, data in sfiles:
            mod = module_path(rel, "std")
            if mod is None or mod in modules:
                continue
            why = None
            tok = mods_m.first(data)
            if tok:
                why = "references %s" % tok
            elif names_m is not None:
                found = names_m.all(data)
                if found:
                    own = {x.decode("utf-8", "replace") for x in DECL_NAME_RE.findall(data)}
                    rest = [x for x in found if x not in own]   # a name the file declares itself is no reference
                    if rest:
                        why = "references public name %s" % rest[0]
            if why:
                modules.add(mod)
                via[mod] = "%s %s" % (rel, why)
                changed_once = True
    if not modules and not names:
        return
    all_m = RefMatcher(set(modules) | set(names))
    for rel, data in corpus.files():
        tok = all_m.first(data)
        if not tok:
            continue
        root_mod = None
        for mm in sorted(modules, key=len, reverse=True):
            if tok == mm or tok.startswith(mm + "."):
                root_mod = mm
                break
        if root_mod is not None:
            rule = "std: %s references %s (%s)" % (rel, tok, via.get(root_mod, "changed"))
        else:
            rule = "std: %s references public name %s" % (rel, tok)
        for tid in corpus.owner_ids(rel):
            if grep_ok(tid):
                aff.add(tid, rule)


def compiler_rule(root, comp_changes, aff, corpus, tests):
    rows, _ = read_map(root)
    tracked = tracked_paths(root)
    mods = {}
    for f in comp_changes:
        top = "/".join(f.split("/")[:2])
        mp = module_path(f, "compiler")
        mods.setdefault(top, set())
        if mp:
            mods[top].add((mp, f))
        targets = rows.get(top)
        if not targets:
            aff.unmatched.append(f)
            continue
        for tgt in targets:
            if not usable_target(root, tgt, tracked):
                continue
            for tid in corpus.ids_under(tgt) if (root / tgt).is_dir() else \
                    [corpus.by_rel[tgt]] if tgt in corpus.by_rel else []:
                aff.add(tid, "compiler: map %s -> %s (%s)" % (top, tgt, f))
    # selfhost bundles embedding a changed module
    modpaths = {}
    for top, s in mods.items():
        for mp, f in s:
            modpaths[mp] = f
    if not modpaths:
        return
    mod_rx = re.compile(rb"^module\s+(" + b"|".join(re.escape(m.encode("utf-8")) for m in sorted(modpaths))
                        + rb")\s*$", re.M)
    gen_rx = re.compile(rb"[\"'](" + b"|".join(re.escape(m.encode("utf-8")) for m in sorted(modpaths))
                        + rb")[\"']")
    manifests_by_dir = {}
    for t in tests:
        if t.id.startswith("selfhost/") and t.kind == "exec" and t.cmd and "gen_" in t.cmd:
            manifests_by_dir.setdefault(t.id.rsplit("/", 1)[0], []).append(t.id)
    # A bundle compiles the copy of the module embedded when it was generated, so a compiler change that is
    # not regenerated into the bundles makes them stale (caught cheaply by the directory's generator check
    # manifest, selected here) while the bundles themselves observe the change only through the compiler
    # binary, like every test. Selected: the generator checks of every directory that embeds/lists a changed
    # module, and the embedding bundles inside the module's own map targets (e.g. compiler/mir ->
    # tests/selfhost/mir). The other embedding bundles are listed as DEFERRED (periodic full run); a
    # regenerated bundle is a changed test file and is selected by the test rule.
    own_targets = set()
    for top in mods:
        own_targets.update(t.rstrip("/") + "/" for t in rows.get(top, []))
    hit_dirs = {}
    for rel, data in corpus.files():
        if not rel.startswith("tests/selfhost/"):
            continue
        if rel.endswith(".ax"):
            m = mod_rx.search(data)
            if m:
                mp = m.group(1).decode("utf-8")
                tid = corpus.by_rel.get(rel)
                if tid:
                    why = "compiler: bundle embeds module %s (%s)" % (mp, modpaths[mp])
                    if any(rel.startswith(t) for t in own_targets):
                        aff.add(tid, why)
                    else:
                        aff.defer(tid, why)
                hit_dirs.setdefault(rel.rsplit("/", 1)[0], mp)
        elif rel.endswith(".ax.in"):
            m = mod_rx.search(data) or gen_rx.search(data)
            if m:
                hit_dirs.setdefault(rel.rsplit("/", 1)[0], m.group(1).decode("utf-8"))
    sh = Path(root) / "tests" / "selfhost"
    for gen in sorted(sh.rglob("gen_*.py")) if sh.is_dir() else []:
        if "__pycache__" in gen.parts:
            continue
        try:
            m = gen_rx.search(gen.read_bytes())
        except OSError:
            continue
        if m:
            hit_dirs.setdefault(gen.parent.relative_to(root).as_posix(), m.group(1).decode("utf-8"))
    for d, mp in sorted(hit_dirs.items()):
        for tid in manifests_by_dir.get(d[len("tests/"):], []):
            aff.add(tid, "compiler: generator check of a bundle embedding %s" % mp)


def tools_rule(root, f, aff, corpus):
    tests_dir = Path(root) / "tools" / "tests"
    matched = False
    parts = f.split("/")
    if len(parts) >= 3 and parts[1] == "tests":
        d = "/".join(parts[:3])
        if (Path(root) / d).is_dir():
            aff.tools.setdefault(d, []).append("tools: %s changed" % f)
            matched = True
    else:
        stem = Path(f).stem
        best = None
        if tests_dir.is_dir():
            for d in sorted(x.name for x in tests_dir.iterdir() if x.is_dir() and x.name != "__pycache__"):
                if stem == d or stem.startswith(d):
                    if best is None or len(d) > len(best):
                        best = d
        if best:
            aff.tools.setdefault("tools/tests/" + best, []).append("tools: %s changed" % f)
            matched = True
        # tool self-test directories whose sources name the changed file (a data file such as
        # tools/affected_map.txt, or a module imported by another tool's tests)
        if tests_dir.is_dir():
            needles = {Path(f).name.encode("utf-8"), stem.encode("utf-8")}
            for d in sorted(x for x in tests_dir.iterdir() if x.is_dir() and x.name != "__pycache__"):
                key = "tools/tests/" + d.name
                for src in sorted(d.glob("*.py")):
                    try:
                        data = src.read_bytes()
                    except OSError:
                        continue
                    if any(re.search(rb"(?<![A-Za-z0-9_])" + re.escape(n) + rb"(?![A-Za-z0-9_])", data)
                           for n in needles):
                        if key not in aff.tools or not any(f in r for r in aff.tools[key]):
                            aff.tools.setdefault(key, []).append("tools: %s names %s" % (src.name, f))
                        matched = True
                        break
    # exec manifests whose cmd names the tool
    name = Path(f).name.encode("utf-8")
    if f.endswith(".py"):
        for rel, data in corpus.files():
            if rel.endswith(".test") and re.search(rb"^cmd:.*" + re.escape(name), data, re.M):
                for tid in corpus.owner_ids(rel):
                    if rel == "tests/" + tid:
                        aff.add(tid, "tools: cmd: runs %s" % f)
                        matched = True
    return matched


# ----------------------------------------------------------------------------------------------
# Smoke set
# ----------------------------------------------------------------------------------------------

class SmokeList:
    def __init__(self):
        self.always = []
        self.pools = {}
        self.problems = []


def read_smoke(root):
    path = Path(root) / "tests" / "smoke.list"
    sl = SmokeList()
    if not path.is_file():
        sl.problems.append("tests/smoke.list does not exist")
        return sl
    for ln, line in enumerate(path.read_bytes().decode("utf-8").splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^always:\s*(\S+)\s*$", s)
        if m:
            sl.always.append(m.group(1))
            continue
        m = re.match(r"^pool\s+([A-Za-z0-9_.-]+):\s*(\S+)\s*$", s)
        if m:
            sl.pools.setdefault(m.group(1), []).append(m.group(2))
            continue
        sl.problems.append("tests/smoke.list line %d: expected `always: <id>` or `pool <group>: <id>`" % ln)
    return sl


class Smoke:
    def __init__(self, seed, always, picks):
        self.seed = seed
        self.always = always
        self.picks = picks          # group -> id

    @property
    def ids(self):
        return sorted(set(self.always) | set(self.picks.values()))

    def lines(self):
        out = ["SMOKE seed=%d always=%d groups=%d" % (self.seed, len(self.always), len(self.picks))]
        for a in self.always:
            out.append("SMOKE-ALWAYS %s" % a)
        for g, t in sorted(self.picks.items()):
            out.append("SMOKE-PICK %s %s" % (g, t))
        return out

    def as_dict(self):
        return {"seed": self.seed, "always": self.always, "picks": dict(sorted(self.picks.items()))}


def smoke_select(root, tests, seed):
    sl = read_smoke(root)
    if sl.problems:
        raise AffectedError("; ".join(sl.problems))
    known = {t.id for t in tests}
    picks = {}
    for g in sorted(sl.pools):
        pool = sorted(i for i in sl.pools[g] if i in known)
        if pool:
            picks[g] = random.Random("%d:%s" % (seed, g)).choice(pool)
    return Smoke(seed, [a for a in sl.always if a in known], picks)


def test_groups(tests):
    return sorted({t.id.split("/", 1)[0] for t in tests if "/" in t.id})


def smoke_check(root, tests, durations):
    """(problems, notes, estimate seconds or None)."""
    sl = read_smoke(root)
    problems = list(sl.problems)
    notes = []
    by_id = {t.id: t for t in tests}
    for g in test_groups(tests):
        if not sl.pools.get(g):
            problems.append("group %s has no pool entry" % g)
    for g, ids in sorted(sl.pools.items()):
        for i in ids:
            if i not in by_id:
                problems.append("pool %s: unknown id %s" % (g, i))
            elif i.split("/", 1)[0] != g:
                problems.append("pool %s: id %s belongs to group %s" % (g, i, i.split("/", 1)[0]))
    for i in sl.always:
        if i not in by_id:
            problems.append("always: unknown id %s" % i)
    alw = [by_id[i] for i in sl.always if i in by_id]
    if not any(t.kind == "run" and GREETING in (t.stdout or b"") for t in alw):
        problems.append("always: no run test whose stdout: expectation prints Xin chào thế giới")
    if not any(t.kind == "ui" and any(a[1] == "error" for a in t.annotations) for t in alw):
        problems.append("always: no compile-fail ui test (a ui test with an expected ERROR)")
    if not any(t.kind == "diff" for t in alw):
        problems.append("always: no native-vs-interp diff test")
    unknown = []

    def dur(i):
        d = axtest_cache.id_duration_ms(durations, i)
        if d is None:
            unknown.append(i)
            return 0
        return d
    total = sum(dur(i) for i in sl.always)
    longest = max([dur(i) for i in sl.always] + [0])
    for g, ids in sorted(sl.pools.items()):
        ds = [dur(i) for i in ids if i in by_id]
        if ds:
            total += max(ds)
            longest = max(longest, max(ds))
    est = max(total / 1000.0 / SMOKE_JOBS, longest / 1000.0)
    unknown = sorted(set(unknown))
    if unknown:
        notes.append("duration bound unverified: %d id(s) have no recorded duration (run `python tools/axtest.py "
                     "--id-file <all smoke ids> -j 2` once to record them): %s"
                     % (len(unknown), " ".join(unknown[:20]) + (" ..." if len(unknown) > 20 else "")))
    if est > SMOKE_BOUND_S:
        problems.append("worst-case smoke draw takes %.0f s at -j %d (> %d s bound)" % (est, SMOKE_JOBS, SMOKE_BOUND_S))
    return problems, notes, est, unknown


def smoke_check_main(root, tests, durations, info):
    problems, notes, est, unknown = smoke_check(root, tests, durations)
    for p in problems:
        info("SMOKE-CHECK PROBLEM %s" % p)
    for n in notes:
        info("SMOKE-CHECK NOTE %s" % n)
    info("SMOKE-CHECK worst-case estimate %.0f s at -j %d (bound %d s)%s" %
         (est, SMOKE_JOBS, SMOKE_BOUND_S, " UNVERIFIED" if unknown else ""))
    info("SMOKE-CHECK %s" % ("OK" if not problems else "FAILED (%d problem(s))" % len(problems)))
    return 1 if problems else 0


def all_smoke_ids(root):
    sl = read_smoke(root)
    ids = list(sl.always)
    for g in sorted(sl.pools):
        ids.extend(sl.pools[g])
    return sorted(set(ids))


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="axtest_affected.py")
    ap.add_argument("--root", default=str(HERE.parent))
    ap.add_argument("--check-map", action="store_true", help="validate tools/affected_map.txt")
    ap.add_argument("--smoke-ids", action="store_true", help="print every id of tests/smoke.list")
    o = ap.parse_args(argv)
    if o.check_map:
        notes = []
        probs = check_map(o.root, notes)
        for n in notes:
            print("MAP-NOTE %s" % n)
        for p in probs:
            print("MAP-PROBLEM %s" % p)
        print("MAP-CHECK %s" % ("OK" if not probs else "FAILED (%d)" % len(probs)))
        return 1 if probs else 0
    if o.smoke_ids:
        for i in all_smoke_ids(o.root):
            print(i)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass
    sys.exit(main(sys.argv[1:]))
