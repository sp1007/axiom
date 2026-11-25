"""Dependency closure of the std modules a bundled std/async test needs (T449a).

The bundle generators of tests/std/async/{executor,structured,waker,waker_qa} copy the live std sources into
each test file, because `TaskGroup.spawn` cannot be instantiated from a program that imports the live
`std.asyn.group` module (AX_CONC_CAPTURE_NOT_SEND, see tests/conformance/p11/e11_6_async_io/gen_tests.py), and
because bundling a module that live std code also imports, without bundling that code too, creates two
incompatible copies of its types: the bundle must hold the whole import closure.

A hand-written source list goes stale whenever a std module gains an import (std.asyn.executor started to
import std.asyn.reactor, std.asyn.timer and std.io, which made four bundle directories fail with
type-mismatch errors). `bundle_sources` therefore derives the closure from the `use std.*` lines instead:

  * seeds: the explicitly listed std files plus every std module the test program imports;
  * a `use` line is resolved to the longest dotted prefix that names a std module (`module` line of a file
    under std/); `std.core.*` is skipped (the compiler provides it, it is never bundled);
  * the result is dependency ordered (imports first), each file once, with a fixed traversal order so the
    generated bundle is deterministic.
"""

import os
import re

_MODULE_RE = re.compile(r"^module\s+([A-Za-z0-9_.]+)", re.MULTILINE)
_USE_RE = re.compile(r"^use\s+([A-Za-z0-9_.]+)", re.MULTILINE)


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def module_index(root):
    """Map every std module name to its path relative to `root` (forward slashes)."""
    index = {}
    std_dir = os.path.join(root, "std")
    for dirpath, dirnames, filenames in os.walk(std_dir):
        dirnames.sort()
        for filename in sorted(filenames):
            if not filename.endswith(".ax"):
                continue
            full = os.path.join(dirpath, filename)
            match = _MODULE_RE.search(_read(full))
            if match:
                index[match.group(1)] = os.path.relpath(full, root).replace(os.sep, "/")
    return index


def _imported_modules(text, index):
    """Std modules named by the `use` lines of `text`, in order of appearance, without std.core.*."""
    found = []
    for match in _USE_RE.finditer(text):
        parts = match.group(1).split(".")
        for cut in range(len(parts), 1, -1):
            name = ".".join(parts[:cut])
            if name in index:
                if not name.startswith("std.core.") and name not in found:
                    found.append(name)
                break
    return found


def bundle_sources(root, listed, program_text):
    """Ordered std file list (relative paths) to bundle: `listed` plus the closure of their imports and of
    the imports of `program_text` (the test program that is appended after the bundled sources)."""
    index = module_index(root)
    path_to_module = {path: name for name, path in index.items()}
    ordered = []
    visiting = set()

    def visit(name):
        if name in ordered or name in visiting:
            return
        visiting.add(name)
        text = _read(os.path.join(root, index[name].replace("/", os.sep)))
        for dep in _imported_modules(text, index):
            visit(dep)
        visiting.discard(name)
        ordered.append(name)

    for rel in listed:
        name = path_to_module.get(rel)
        if name is None:
            raise FileNotFoundError("listed std source defines no module: " + rel)
        visit(name)
    for name in _imported_modules(program_text, index):
        visit(name)
    return [index[name] for name in ordered]
