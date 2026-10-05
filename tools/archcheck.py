#!/usr/bin/env python3
"""archcheck: architecture layer checker for axiom0 (T006).

Enforces INV-LAYER-001..008 of spec/invariants.md on the C sources under bootstrap/axiom0/src and on
the std/ tree:

  INV-LAYER-001  layer order (a module includes its own or lower layers; objmodel is a low layer)
  INV-LAYER-002  obj/link stay below the IR
  INV-LAYER-003  interp independent of the native back end, opt independent of syntax
  INV-LAYER-004  types never includes interp
  INV-LAYER-005  back end never includes lex/syntax/resolve/hir
  INV-LAYER-006  no mutable globals, no printing/terminating in library layers
  INV-LAYER-007  diagnostic codes only in diag/codes/<AREA>.def
  INV-LAYER-008  std/ holds no C sources

Usage: python tools/archcheck.py [--root DIR] [--rules FILE] [--json] [-v]
Exit status: 0 clean, 1 violations found, 2 usage or rules-file error.
Every violation line is `file:line: <message> [INV-LAYER-nnn]`. Python 3 standard library only.
The rules live in tools/archcheck_rules.txt (the machine form of the invariants).
"""

import argparse
import bisect
import fnmatch
import json
import os
import posixpath
import re
import sys

C_EXTS = (".c", ".h", ".def", ".inc")
STD_FORBIDDEN_EXTS = (".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".inl", ".s", ".asm")
PRAGMA_RE = re.compile(r"archcheck:allow\(([A-Z]+-[A-Z]+-[0-9]+)\)(:\s*\S.*)?")
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*"([^"\n]+)"', re.M)
IDENT_RE = re.compile(r"[A-Za-z_]\w*$")
TOKEN_RE = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'|[A-Za-z_]\w*|\d[\w.]*|->|\S')
STORAGE = {"static", "const", "volatile", "inline", "_Thread_local", "thread_local", "register",
           "restrict", "__restrict", "__extension__"}
AGGREGATES = {"struct", "union", "enum"}


class RulesError(Exception):
    pass


class Violation:
    __slots__ = ("path", "line", "inv", "msg")

    def __init__(self, path, line, inv, msg):
        self.path, self.line, self.inv, self.msg = path, line, inv, msg

    def key(self):
        return (self.path, self.line, self.inv, self.msg)

    def text(self):
        return "%s:%d: %s [%s]" % (self.path, self.line, self.msg, self.inv)

    def as_dict(self):
        return {"file": self.path, "line": self.line, "inv": self.inv, "message": self.msg}


# ----------------------------------------------------------------------------- rules file


class Rules:
    def __init__(self):
        self.src_root = None
        self.std_root = None
        self.rank = {}          # layer -> rank (only layers in the order)
        self.layers = []        # every layer name, longest first for matching
        self.deny = []          # (inv, froms, tos)
        self.only = {}          # layer -> (inv, allowed set)
        self.users = {}         # layer -> (inv, allowed set)
        self.areas = []
        self.codes_dir = "diag/codes"
        self.diag_macros = []
        self.output_fns = []
        self.output_stream_fns = []
        self.output_allow = []  # (glob, set of fns or None)


def _split_colon(parts, lineno):
    if ":" not in parts:
        raise RulesError("line %d: missing ':'" % lineno)
    k = parts.index(":")
    return parts[:k], parts[k + 1:]


def parse_rules(text):
    r = Rules()
    names = set()
    for lineno, raw in enumerate(text.split("\n"), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        key, args = parts[0], parts[1:]
        if key == "src-root" and len(args) == 1:
            r.src_root = args[0]
        elif key == "std-root" and len(args) == 1:
            r.std_root = args[0]
        elif key == "order":
            for rank, group in enumerate(args):
                for name in group.split("|"):
                    if name in r.rank:
                        raise RulesError("line %d: layer %s listed twice" % (lineno, name))
                    r.rank[name] = rank
                    names.add(name)
        elif key == "deny" and len(args) >= 4:
            froms, tos = _split_colon(args[1:], lineno)
            r.deny.append((args[0], froms, tos))
        elif key in ("only", "users") and len(args) >= 3:
            head, allowed = _split_colon(args[1:], lineno)
            if len(head) != 1:
                raise RulesError("line %d: %s needs exactly one layer before ':'" % (lineno, key))
            getattr(r, key)[head[0]] = (args[0], set(allowed))
        elif key == "areas":
            r.areas = args
        elif key == "codes-dir" and len(args) == 1:
            r.codes_dir = args[0].strip("/")
        elif key == "diag-macro":
            r.diag_macros = args
        elif key == "output-fn":
            r.output_fns = args
        elif key == "output-stream-fn":
            r.output_stream_fns = args
        elif key == "output-allow" and args:
            r.output_allow.append((args[0], set(args[1:]) or None))
        else:
            raise RulesError("line %d: bad directive: %s" % (lineno, line))
    # layers named by deny/only/users but absent from the order are low layers like objmodel
    for inv, froms, tos in r.deny:
        names.update(froms)
        names.update(tos)
    for k, (inv, allowed) in list(r.only.items()) + list(r.users.items()):
        names.add(k)
        names.update(allowed)
    r.layers = sorted(names, key=lambda n: (-len(n), n))
    if r.src_root is None:
        raise RulesError("rules: no src-root directive")
    if not r.rank:
        raise RulesError("rules: no order directive")
    for _inv, froms, tos in r.deny:
        for n in froms + tos:
            if n not in names:
                raise RulesError("rules: unknown layer %s" % n)
    return r


# ----------------------------------------------------------------------------- C text helpers


def strip_c(text, keep_strings):
    """Blank comments (and string contents unless keep_strings), preserving every newline."""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = i
            while j < n and not (text[j] == "\n" and text[j - 1] != "\\"):
                j += 1
            out.append("".join(" " if ch != "\n" else "\n" for ch in text[i:j]))
            i = j
        elif c == "/" and nxt == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(" " if ch != "\n" else "\n" for ch in text[i:j]))
            i = j
        elif c == '"' or c == "'":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            j = min(j, n)
            body = text[i + 1:j]
            closed = j < n and text[j] == c
            if keep_strings:
                out.append(c + body + (c if closed else ""))
            else:
                out.append(c + "".join(" " if ch != "\n" else "\n" for ch in body) + (c if closed else ""))
            i = j + (1 if closed else 0)
        else:
            out.append(c)
            i += 1
    return "".join(out)


def blank_preprocessor(code):
    """Blank preprocessor directives (with continuation lines); keeps line structure."""
    lines = code.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("#"):
            while True:
                cont = lines[i].rstrip().endswith("\\")
                lines[i] = ""
                if not cont or i + 1 >= len(lines):
                    break
                i += 1
        i += 1
    return "\n".join(lines)


class Source:
    """One scanned file: raw lines (for pragmas) plus the stripped views."""

    def __init__(self, rel, text):
        self.rel = rel
        self.raw_lines = text.split("\n")
        self.keep = strip_c(text, True)
        self.code = blank_preprocessor(strip_c(text, False))
        self._nl = [m.start() for m in re.finditer("\n", self.code)]

    def line_at(self, pos):
        return bisect.bisect_left(self._nl, pos) + 1

    def pragma(self, line):
        """The pragma on `line` or the line above: (inv, has_reason) or None."""
        for ln in (line, line - 1):
            if 1 <= ln <= len(self.raw_lines):
                m = PRAGMA_RE.search(self.raw_lines[ln - 1])
                if m:
                    return m.group(1), bool(m.group(2))
        return None


# ----------------------------------------------------------------------------- layers


def layer_of(rules, rel_to_src):
    """Layer owning a path relative to src-root (longest layer name that is a directory prefix)."""
    for name in rules.layers:
        if rel_to_src.startswith(name + "/"):
            return name
    return None


def check_edge(rules, a, b):
    """Return (inv, reason) when layer a must not include layer b, else None."""
    if a == b:
        return None
    for inv, froms, tos in rules.deny:
        if a in froms and b in tos:
            return inv, "forbidden by the deny rule"
    if a in rules.only and b not in rules.only[a][1]:
        return rules.only[a][0], "may include only %s" % ", ".join(sorted(rules.only[a][1] | {a}))
    if b in rules.users and a not in rules.users[b][1]:
        return rules.users[b][0], "may be included only by %s" % ", ".join(sorted(rules.users[b][1] | {b}))
    if a in rules.rank and b in rules.rank:
        if rules.rank[b] > rules.rank[a]:
            return "INV-LAYER-001", "higher layer"
        if rules.rank[b] == rules.rank[a]:
            return "INV-LAYER-001", "peer layer of the same rank"
    return None


def resolve_include(rules, src_dir_abs, file_rel, inc):
    """Path of an include relative to src-root, or None when it points outside every layer."""
    cands = [posixpath.normpath(inc), posixpath.normpath(posixpath.join(posixpath.dirname(file_rel), inc))]
    for c in cands:
        if os.path.isfile(os.path.join(src_dir_abs, *c.split("/"))):
            return c
    for c in cands:  # file missing (generated or not yet written): the path alone decides
        if layer_of(rules, c) is not None:
            return c
    return None


def check_layers(rules, root, src_rel, files, out):
    src_abs = os.path.join(root, *src_rel.split("/"))
    for rel, source in files:
        a = layer_of(rules, rel)
        if a is None:
            top = rel.split("/")[0] if "/" in rel else "(root of src)"
            out.append(Violation(src_rel + "/" + rel, 1, "INV-LAYER-001",
                                 "file is in no known layer '%s' (add the layer to tools/archcheck_rules.txt)" % top))
            continue
        for m in INCLUDE_RE.finditer(source.keep):
            line = source.keep.count("\n", 0, m.start()) + 1
            inc = m.group(1)
            target = resolve_include(rules, src_abs, rel, inc)
            if target is None:
                continue
            b = layer_of(rules, target)
            if b is None:
                out.append(Violation(src_rel + "/" + rel, line, "INV-LAYER-001",
                                     'include "%s" resolves into no known layer' % inc))
                continue
            bad = check_edge(rules, a, b)
            if bad:
                out.append(Violation(src_rel + "/" + rel, line, bad[0],
                                     'layer %s must not include %s (#include "%s": %s)' % (a, b, inc, bad[1])))


# ----------------------------------------------------------------------------- output calls


STREAM_RE = re.compile(r"\b(stdout|stderr)\b")


def _call_args(code, open_paren):
    """Text between the parenthesis at open_paren and its matching ')' (or end of file)."""
    depth = 0
    for j in range(open_paren, len(code)):
        if code[j] == "(":
            depth += 1
        elif code[j] == ")":
            depth -= 1
            if depth == 0:
                return code[open_paren + 1:j]
    return code[open_paren + 1:]


def check_output(rules, src_rel, files, out):
    if not rules.output_fns and not rules.output_stream_fns:
        return
    plain = re.compile(r"(?<![\w.>])(%s)\s*\(" % "|".join(map(re.escape, rules.output_fns))) \
        if rules.output_fns else None
    # The stream is the first argument of fprintf/vfprintf but the last one of fputs/fputc/putc/
    # fwrite, so a stream call is flagged when stdout/stderr is any of its arguments.
    stream = re.compile(r"(?<![\w.>])(%s)\s*\(" % "|".join(map(re.escape, rules.output_stream_fns))) \
        if rules.output_stream_fns else None
    for rel, source in files:
        if not rel.endswith((".c", ".h")):
            continue
        if layer_of(rules, rel) == "driver":
            continue
        allowed = [fns for glob, fns in rules.output_allow if fnmatch.fnmatch(rel, glob)]
        if any(fns is None for fns in allowed):
            continue
        ok_fns = set().union(*allowed) if allowed else set()
        hits = []
        if plain is not None:
            hits += [(m.start(), m.group(1)) for m in plain.finditer(source.code)]
        if stream is not None:
            hits += [(m.start(), m.group(1)) for m in stream.finditer(source.code)
                     if STREAM_RE.search(_call_args(source.code, m.end() - 1))]
        for pos, fn in sorted(hits):
            if fn in ok_fns:
                continue
            lineno = source.line_at(pos)
            pr = source.pragma(lineno)
            if pr and pr[0] == "INV-LAYER-006" and pr[1]:
                continue
            out.append(Violation(src_rel + "/" + rel, lineno, "INV-LAYER-006",
                                 "library code must not call %s() (output only from driver/ and diagnostic renderers; abort only via AX_ICE)" % fn))


def check_pragmas(src_rel, files, out):
    for rel, source in files:
        for lineno, text in enumerate(source.raw_lines, 1):
            m = PRAGMA_RE.search(text)
            if not m or "archcheck:allow" not in text:
                continue
            if m.group(1) != "INV-LAYER-006":
                out.append(Violation(src_rel + "/" + rel, lineno, m.group(1),
                                     "archcheck:allow is honoured only for INV-LAYER-006"))
            elif not m.group(2):
                out.append(Violation(src_rel + "/" + rel, lineno, "INV-LAYER-006",
                                     "archcheck:allow(INV-LAYER-006) needs a reason after ':'"))


# ----------------------------------------------------------------------------- mutable globals


def _is_ident(tok):
    return bool(IDENT_RE.match(tok)) and tok not in STORAGE and tok not in AGGREGATES


def _match_brace(toks, i):
    depth = 0
    for j in range(i, len(toks)):
        if toks[j][0] == "{":
            depth += 1
        elif toks[j][0] == "}":
            depth -= 1
            if depth == 0:
                return j
    return len(toks) - 1


def _drop_groups(toks, opener, closer):
    out, depth = [], 0
    for t in toks:
        if t == opener:
            depth += 1
        elif t == closer:
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(t)
    return out


def _drop_calls(toks, names):
    """Remove NAME ( ... ) groups such as __attribute__((...))."""
    out, i = [], 0
    while i < len(toks):
        if toks[i] in names and i + 1 < len(toks) and toks[i + 1] == "(":
            depth, j = 0, i + 1
            while j < len(toks):
                depth += toks[j] == "("
                depth -= toks[j] == ")"
                j += 1
                if depth == 0:
                    break
            i = j
        else:
            out.append(toks[i])
            i += 1
    return out


def _split_top(toks, sep):
    pieces, cur, depth = [], [], 0
    for t in toks:
        if t in "([":
            depth += 1
        elif t in ")]":
            depth -= 1
        if t == sep and depth == 0:
            pieces.append(cur)
            cur = []
        else:
            cur.append(t)
    pieces.append(cur)
    return pieces


def analyze_decl(stmt):
    """Mutable variables declared by one file-scope or static statement: [(name, line)].

    stmt is a list of (token, line) with brace groups collapsed to '{}'. A heuristic, not a C
    parser: it recognises function declarations, typedefs and aggregate-only declarations and
    reports every other declarator that is not const (a pointer is const only as `* const p`).
    """
    toks = [t for t, _ in stmt]
    lines = [ln for _, ln in stmt]
    if not toks or "typedef" in toks[:4] or toks[0] in ("extern", "_Static_assert", "static_assert"):
        return []
    if "extern" in toks[:3]:
        return []
    toks = _drop_calls(toks, {"__attribute__", "_Alignas", "alignas", "__declspec"})
    if not toks:
        return []
    k = 0
    while k < len(toks) and toks[k] in STORAGE:
        k += 1
    if k < len(toks) and toks[k] in AGGREGATES:
        rest = toks[k + 1:]
        if rest and _is_ident(rest[0]):
            rest = rest[1:]
        if rest and rest[0] == "{}":
            rest = rest[1:]
        if not rest:
            return []
    line_of = {}
    for t, ln in stmt:
        line_of.setdefault(t, ln)
    result = []
    spec_const = False
    for idx, piece in enumerate(_split_top(toks, ",")):
        decl = _split_top(piece, "=")[0]
        decl = [t for t in _drop_groups(decl, "[", "]") if t != "{}"]
        if not decl:
            continue
        fp = next((i for i in range(len(decl) - 1) if decl[i] == "(" and decl[i + 1] == "*"), None)
        if "(" in decl and fp is None:
            continue  # function prototype / declaration macro
        stars = [i for i, t in enumerate(decl) if t == "*"]
        if idx == 0:
            first_star = stars[0] if stars else len(decl)
            spec_const = "const" in decl[:first_star]
        if fp is not None:
            j = fp + 1
            while j < len(decl) and decl[j] == "*":
                j += 1
            const = "const" in decl[j:j + 2] and decl[j] == "const"
            name = next((t for t in decl[j:] if _is_ident(t)), decl[-1])
        elif stars:
            const = "const" in decl[stars[-1] + 1:]
            name = next((t for t in reversed(decl) if _is_ident(t)), decl[-1])
        else:
            const = spec_const
            name = next((t for t in reversed(decl) if _is_ident(t)), decl[-1])
        if not const:
            result.append((name, line_of.get(name, lines[0])))
    return result


def _function_head(stmt_toks):
    if not stmt_toks or "=" in stmt_toks or "(" not in stmt_toks or ")" not in stmt_toks:
        return False
    last = stmt_toks[-1]
    return last == ")" or (bool(IDENT_RE.match(last)) and last not in AGGREGATES)


def _local_statics(body, found):
    """Mutable `static` declarations inside a function body (hidden global state)."""
    i, prev = 0, ";"
    while i < len(body):
        tok = body[i][0]
        if tok in ("static", "_Thread_local", "thread_local") and prev in (";", "{", "}"):
            stmt, depth, j = [], 0, i
            while j < len(body):
                t = body[j][0]
                if t == "{":
                    if depth == 0:
                        stmt.append(("{}", body[j][1]))
                    depth += 1
                elif t == "}":
                    depth -= 1
                elif depth == 0:
                    if t == ";":
                        break
                    stmt.append(body[j])
                j += 1
            for name, line in analyze_decl(stmt):
                found.append((name, line, True))
            i = j
            prev = ";"
            continue
        prev = tok
        i += 1


def find_mutable_globals(source):
    """[(name, line, is_local_static)] for a stripped C source (heuristic, see analyze_decl)."""
    toks = [(m.group(0), source.line_at(m.start())) for m in TOKEN_RE.finditer(source.code)]
    found = []
    stmt = []
    i = 0
    while i < len(toks):
        t, ln = toks[i]
        if t == "{":
            j = _match_brace(toks, i)
            if _function_head([x for x, _ in stmt]):
                _local_statics(toks[i + 1:j], found)
                stmt = []
            else:
                stmt.append(("{}", ln))
            i = j + 1
            continue
        if t == ";":
            for name, line in analyze_decl(stmt):
                found.append((name, line, False))
            stmt = []
        else:
            stmt.append((t, ln))
        i += 1
    return found


def check_globals(rules, src_rel, files, out):
    for rel, source in files:
        if not rel.endswith((".c", ".h")) or layer_of(rules, rel) == "driver":
            continue
        for name, line, local in find_mutable_globals(source):
            what = "function-local static" if local else "file-scope variable"
            out.append(Violation(src_rel + "/" + rel, line, "INV-LAYER-006",
                                 "mutable %s '%s' outside driver/ (make it const or pass state through a context struct)" % (what, name)))


# ----------------------------------------------------------------------------- diagnostic codes

CODE_RE = re.compile(r"\b(AX_([A-Z0-9]+)_[A-Z0-9_]*)\b")
DEF_ENTRY_RE = re.compile(r"^\s*[A-Za-z_]\w*\s*\(\s*(AX_([A-Z0-9]+)_[A-Z0-9_]*)\b", re.M)


def check_codes(rules, src_rel, files, out):
    codes_prefix = rules.codes_dir + "/"
    areas = set(rules.areas)
    seen = {}
    macro_re = None
    if rules.diag_macros:
        macro_re = re.compile(r"\b(%s)\s*\(\s*(AX_([A-Z0-9]+)_[A-Z0-9_]*)\b" % "|".join(map(re.escape, rules.diag_macros)))
    for rel, source in files:
        path = src_rel + "/" + rel
        in_codes = rel.startswith(codes_prefix)
        if in_codes:
            stem = posixpath.basename(rel)[:-4] if rel.endswith(".def") else None
            if stem is None or posixpath.dirname(rel) != rules.codes_dir:
                out.append(Violation(path, 1, "INV-LAYER-007",
                                     "only <AREA>.def files live in %s" % rules.codes_dir))
                continue
            if areas and stem not in areas:
                out.append(Violation(path, 1, "INV-LAYER-007",
                                     "%s.def is not a diagnostic area (areas: spec/diagnostics.md AXD-020)" % stem))
            entries = [(m.group(1), m.group(2), source.code.count("\n", 0, m.start(1)) + 1)
                       for m in DEF_ENTRY_RE.finditer(source.code)]
        else:
            if rel.endswith(".def"):
                entries = [(m.group(1), m.group(2), source.code.count("\n", 0, m.start(1)) + 1)
                           for m in DEF_ENTRY_RE.finditer(source.code)]
            elif macro_re is not None and rel.endswith((".c", ".h", ".inc")):
                entries = [(m.group(2), m.group(3), source.code.count("\n", 0, m.start(2)) + 1)
                           for m in macro_re.finditer(source.code)]
            else:
                entries = []
            for code, area, line in entries:
                out.append(Violation(path, line, "INV-LAYER-007",
                                     "diagnostic code %s defined outside %s/<AREA>.def" % (code, rules.codes_dir)))
            continue
        for code, area, line in entries:
            if areas and area not in areas:
                out.append(Violation(path, line, "INV-LAYER-007",
                                     "code %s: area %s is not one of the diagnostic areas" % (code, area)))
            elif area != stem:
                out.append(Violation(path, line, "INV-LAYER-007",
                                     "code %s (area %s) is registered in %s.def" % (code, area, stem)))
            if code in seen:
                out.append(Violation(path, line, "INV-LAYER-007",
                                     "code %s is defined twice (first at %s)" % (code, seen[code])))
            else:
                seen[code] = "%s:%d" % (path, line)


# ----------------------------------------------------------------------------- std tree


def check_std(rules, root, out):
    if not rules.std_root:
        return 0
    base = os.path.join(root, *rules.std_root.split("/"))
    if not os.path.isdir(base):
        return 0
    count = 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for f in sorted(filenames):
            count += 1
            if f.lower().endswith(STD_FORBIDDEN_EXTS) or f.endswith(".S"):
                rel = os.path.relpath(os.path.join(dirpath, f), root).replace(os.sep, "/")
                out.append(Violation(rel, 1, "INV-LAYER-008",
                                     "std/ is Axiom source only; C/assembly source '%s' is not allowed (ROADMAP R8)" % f))
    return count


# ----------------------------------------------------------------------------- driver


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "replace").replace("\r\n", "\n")


def collect(rules, root):
    src_abs = os.path.join(root, *rules.src_root.split("/"))
    files = []
    if not os.path.isdir(src_abs):
        raise RulesError("src-root %s does not exist under %s" % (rules.src_root, root))
    for dirpath, dirnames, filenames in os.walk(src_abs):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for f in sorted(filenames):
            if f.endswith(C_EXTS):
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, src_abs).replace(os.sep, "/")
                files.append((rel, Source(rel, read_text(full))))
    return files


def run_checks(rules, root):
    """Return (violations sorted, number of files scanned)."""
    out = []
    files = collect(rules, root)
    check_layers(rules, root, rules.src_root, files, out)
    check_output(rules, rules.src_root, files, out)
    check_pragmas(rules.src_root, files, out)
    check_globals(rules, rules.src_root, files, out)
    check_codes(rules, rules.src_root, files, out)
    scanned = len(files) + check_std(rules, root, out)
    uniq = {v.key(): v for v in out}
    return [uniq[k] for k in sorted(uniq)], scanned


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="axiom0 architecture layer checker (INV-LAYER-001..008)")
    ap.add_argument("--root", default=os.path.dirname(here), help="repository root (default: parent of tools/)")
    ap.add_argument("--rules", default=None, help="rules file (default: <tools>/archcheck_rules.txt)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    rules_path = args.rules or os.path.join(here, "archcheck_rules.txt")
    try:
        rules = parse_rules(read_text(rules_path))
        violations, scanned = run_checks(rules, os.path.abspath(args.root))
    except (RulesError, OSError) as e:
        print("archcheck: error: %s" % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"files": scanned, "violations": [v.as_dict() for v in violations]},
                         indent=2, sort_keys=True))
    else:
        for v in violations:
            print(v.text())
        print("archcheck: %d files scanned, %d violations" % (scanned, len(violations)))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
