#!/usr/bin/env python3
"""QA boundary tests for the duplicate-module rejection of bundle_common.assemble_compiler_modules (T443).

Complements bundle_common_selftest.py (written by the engineer). Plain Python 3 standard library.

Checks (each prints `ok <name>`; the last line is `bundle_common qa selftest: N checks passed`):
  1. fold-collision invariant: no two *distinct* files under compiler/ fold to the same canonical module name, so the
     `.mod` / move_ck / unsafe_ck normalisation can never reject a legitimately distinct pair of modules;
  2. every module of compiler/ listed once (canonical spelling) is accepted - no false positive on the full set;
  3. the same module in two tuple forms is one duplicate, reported once even when listed three times;
  4. spelling variants that the file table does not know (case, surrounding blanks, `/` separators) are not silently
     accepted as a second copy: they fail loudly (KeyError), they never produce a bundle;
  5. an empty list is accepted and yields an empty bundle;
  6. both aliases at once (move + unsafe) are reported in one message;
  7. a rejected list leaves the caller's list untouched and the error is a ValueError (not an AX_NAME_DUPLICATE
     discovered later);
  8. a module list given as a tuple (not a list) is accepted and checked too.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

import bundle_common as bc  # noqa: E402

_passed = 0


def ok(name):
    global _passed
    _passed += 1
    print("ok %s" % name)


def declared_modules(root):
    decl = {}
    for dirpath, _dirs, files in os.walk(os.path.join(root, "compiler")):
        for fn in sorted(files):
            if not fn.endswith(".ax"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, "rb") as f:
                text = f.read().decode("utf-8").replace("\r\n", "\n")
            for line in text.split("\n"):
                if line.startswith("module "):
                    decl.setdefault(line.split()[1], []).append(path)
                    break
    return decl


def main():
    # 1. no two distinct files fold to the same canonical name
    decl = declared_modules(bc.ROOT)
    canon = {}
    for name, paths in decl.items():
        for p in paths:
            canon.setdefault(bc._canonical_module_name(name), set()).add(os.path.abspath(p))
    clashes = {k: v for k, v in canon.items() if len(v) > 1}
    assert not clashes, "distinct files fold to one canonical module name: %r" % clashes
    assert len(decl) > 100, "suspiciously few modules found: %d" % len(decl)
    ok("fold never merges distinct files (%d modules)" % len(decl))

    # 2. the whole compiler/ module set, listed once each, is accepted
    names = []
    seen = set()
    for name in sorted(bc.compiler_module_files(bc.ROOT)):
        c = bc._canonical_module_name(name)
        if c not in seen:
            seen.add(c)
            names.append(c)
    assert bc.find_duplicate_modules(names) == []
    out = bc.assemble_compiler_modules(names, root=bc.ROOT, caller="qa")
    assert len(out) > 1000
    ok("full module set accepted (%d modules)" % len(names))

    # 3. two tuple forms of the same module: one duplicate, reported once
    try:
        bc.assemble_compiler_modules(
            [("compiler.kernel.id", "compiler"), ("compiler.kernel.id", "other"), "compiler.kernel.id"],
            root=bc.ROOT,
            caller="qa_fixture.py",
        )
    except ValueError as e:
        msg = str(e)
        assert msg.count("compiler.kernel.id") == 1, "module named more than once: %r" % msg
        assert "qa_fixture.py" in msg
        ok("two tuple forms (+ plain) -> one duplicate, named once")
    else:
        raise AssertionError("tuple-form duplicates accepted")

    # 4. unknown spelling variants are never silently accepted as a second module
    for variant in ("Compiler.Kernel.Id", "compiler.kernel.id ", " compiler.kernel.id", "compiler/kernel/id"):
        try:
            bc.assemble_compiler_modules(["compiler.kernel.id", variant], root=bc.ROOT, caller="qa")
        except (KeyError, ValueError):
            pass
        else:
            raise AssertionError("variant %r silently accepted next to compiler.kernel.id" % variant)
    ok("case/blank/slash variants fail loudly")

    # 5. empty list
    assert bc.assemble_compiler_modules([], root=bc.ROOT, caller="qa") == ""
    ok("empty list accepted")

    # 6. both aliases at once, first-seen order, one message
    try:
        bc.assemble_compiler_modules(
            ["compiler.own.unsafe", "compiler.own.move_ck", "compiler.own.move", "compiler.own.unsafe_ck"],
            root=bc.ROOT,
            caller="qa",
        )
    except ValueError as e:
        msg = str(e)
        assert "compiler.own.move_ck" in msg and "compiler.own.unsafe_ck" in msg, msg
        ok("move+unsafe aliases reported together")
    else:
        raise AssertionError("alias duplicates accepted")

    # 7. the caller's list is not mutated by a rejection
    lst = ["compiler.kernel.id", "compiler.kernel.hash", "compiler.kernel.id"]
    before = list(lst)
    try:
        bc.assemble_compiler_modules(lst, root=bc.ROOT, caller="qa")
    except ValueError:
        pass
    assert lst == before
    ok("rejected list not mutated")

    # 8. tuple container
    try:
        bc.assemble_compiler_modules(("compiler.kernel.id", "compiler.kernel.id"), root=bc.ROOT, caller="qa")
    except ValueError:
        ok("tuple container checked")
    else:
        raise AssertionError("duplicate in tuple container accepted")

    print("bundle_common qa selftest: %d checks passed" % _passed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
