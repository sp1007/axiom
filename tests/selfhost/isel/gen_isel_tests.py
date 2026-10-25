#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/isel (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_frame_layout_and_verify.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.diag.format', 'compiler.hir.hir', 'compiler.types.types', 'compiler.types.layout', 'compiler.lir.lir', 'compiler.abi.win64', 'compiler.abi', 'compiler.obj.coff', 'compiler.target.x64.encode', 'compiler.target.x64.isel', 'compiler.target.x64.frame', 'compiler.target.x64']), ('qa_isel_diff_golden.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.diag.format', 'compiler.hir.hir', 'compiler.types.types', 'compiler.types.layout', 'compiler.lir.lir', 'compiler.abi.win64', 'compiler.abi', 'compiler.obj.coff', 'compiler.target.x64.encode', 'compiler.target.x64.isel', 'compiler.target.x64.frame', 'compiler.target.x64']), ('qa_isel_frame_seam_and_edge_cases.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.diag.format', 'compiler.hir.hir', 'compiler.types.types', 'compiler.types.layout', 'compiler.lir.lir', 'compiler.abi.win64', 'compiler.abi', 'compiler.obj.coff', 'compiler.target.x64.encode', 'compiler.target.x64.isel', 'compiler.target.x64.frame', 'compiler.target.x64']), ('qa_isel_instructions_and_abi.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.diag.format', 'compiler.hir.hir', 'compiler.types.types', 'compiler.types.layout', 'compiler.lir.lir', 'compiler.abi.win64', 'compiler.abi', 'compiler.obj.coff', 'compiler.target.x64.encode', 'compiler.target.x64.isel', 'compiler.target.x64.frame', 'compiler.target.x64'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
