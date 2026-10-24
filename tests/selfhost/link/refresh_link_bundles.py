#!/usr/bin/env python3
"""Refreshes the embedded compiler modules of the hand-written link bundles (T147 round 1).

tests/selfhost/link/qa_pe_linker_diff.ax and qa_pe_headers_and_imports.ax carry verbatim copies of
compiler/obj and compiler/link (one `module X` section per file, in dependency order) followed by a
hand-written `module main` test. This script replaces each embedded section of the modules below with
the current file from compiler/, so the bundles test the code that exists and never go stale. The
`module main` part and every other embedded module (kernel, diag, ...) are left untouched.

A section starts at the block of `//` header comments directly above its `module` line.

Usage: python tests/selfhost/link/refresh_link_bundles.py
Run it after any change to compiler/obj or compiler/link (ADR-0034 section 2: lockstep).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

BUNDLES = ["qa_pe_linker_diff.ax", "qa_pe_headers_and_imports.ax"]
MODULES = {
    "compiler.obj.coff": "compiler/obj/coff.ax",
    "compiler.obj.writer": "compiler/obj/writer.ax",
    "compiler.obj": "compiler/obj/mod.ax",
    "compiler.link.pe": "compiler/link/pe.ax",
    "compiler.link.import": "compiler/link/import.ax",
    "compiler.link.linker": "compiler/link/linker.ax",
    "compiler.link": "compiler/link/mod.ax",
}

NL = chr(10)


def read(path):
    with open(path, "rb") as f:
        return f.read().decode("utf-8").replace(chr(13) + NL, NL)


def refresh(text):
    lines = text.split(NL)
    mod_at = [i for i, l in enumerate(lines) if l.startswith("module ")]
    starts = []
    for i in mod_at:
        s = i
        while s > 0 and lines[s - 1].startswith("//"):
            s -= 1
        starts.append(s)
    out = lines[:starts[0]]
    for k, i in enumerate(mod_at):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        name = lines[i].split()[1]
        if name in MODULES:
            src = read(os.path.join(ROOT, MODULES[name]))
            if (NL + "module " + name + NL) not in (NL + src):
                raise SystemExit("%s has no `module %s` line" % (MODULES[name], name))
            out.extend(src.rstrip(NL).split(NL))
            out.append("")
        else:
            out.extend(lines[starts[k]:end])
    return NL.join(out)


def main():
    for name in BUNDLES:
        path = os.path.join(HERE, name)
        old = read(path)
        new = refresh(old)
        with open(path, "wb") as f:
            f.write(new.encode("utf-8"))
        print("%s: %s" % (name, "updated" if new != old else "unchanged"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
