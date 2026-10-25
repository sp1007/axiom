#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/abi (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_abi_boundary_seam.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.source.manager', 'compiler.diag.code', 'compiler.diag.emitter', 'compiler.diag.format', 'compiler.lex.token', 'compiler.syntax.ast', 'compiler.hir.hir', 'compiler.types.types', 'compiler.types.layout', 'compiler.lir.lir', 'compiler.abi.win64', 'compiler.abi']), ('qa_abi_lir_lower.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.source.manager', 'compiler.diag.code', 'compiler.diag.emitter', 'compiler.diag.format', 'compiler.lex.token', 'compiler.syntax.ast', 'compiler.hir.hir', 'compiler.types.types', 'compiler.types.layout', 'compiler.mir.mir', 'compiler.lir.lir', 'compiler.lir.builder', 'compiler.lir', 'compiler.abi.win64', 'compiler.abi']), ('qa_abi_win64_classify.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.source.manager', 'compiler.diag.code', 'compiler.diag.emitter', 'compiler.diag.format', 'compiler.lex.token', 'compiler.syntax.ast', 'compiler.hir.hir', 'compiler.types.types', 'compiler.types.layout', 'compiler.lir.lir', 'compiler.abi.win64', 'compiler.abi'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
