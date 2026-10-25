#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/link (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))
sys.path.insert(0, HERE)

import bundle_common as bc  # noqa: E402
import gen_local_symbols_test as gls  # noqa: E402

BUNDLES = [('qa_pe_headers_and_imports.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.diag.code', 'compiler.diag.emitter', 'compiler.obj.coff', 'compiler.obj.writer', 'compiler.obj', 'compiler.link.pe', 'compiler.link.import', 'compiler.link.linker', 'compiler.link']), ('qa_pe_linker_diff.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.diag.code', 'compiler.diag.emitter', 'compiler.obj.coff', 'compiler.obj.writer', 'compiler.obj', 'compiler.link.pe', 'compiler.link.import', 'compiler.link.linker', 'compiler.link'])]


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    check_mode = "--check" in argv or "check" in argv
    outputs = []
    for bname, seeds in BUNDLES:
        tpl_path = os.path.join(HERE, bname + ".in")
        out_path = os.path.join(HERE, bname)
        text = bc.assemble_template_bundle(tpl_path, seeds, include_std_sys=True, root=ROOT)
        outputs.append((out_path, text))
    outputs.append((os.path.join(HERE, "qa_pe_local_symbols.ax"), gls.build_local_symbols_bundle()))
    return bc.write_or_check_bundles(outputs, check_mode, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
