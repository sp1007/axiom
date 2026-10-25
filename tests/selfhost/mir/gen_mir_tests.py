#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/mir (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_mir_builder_and_drop_a.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.source.manager', 'compiler.diag.code', 'compiler.diag.emitter', 'compiler.diag.format', 'compiler.diag.json', 'compiler.kernel_source_diag.session', 'compiler.lex.token', 'compiler.lex.scanner', 'compiler.lexer.session', 'compiler.syntax.ast', 'compiler.syntax.parse', 'compiler.parser.session', 'compiler.resolve.symtab', 'compiler.resolve.rib', 'compiler.resolve.resolver', 'compiler.hir.hir', 'compiler.hir.lower', 'compiler.resolve_hir.session', 'compiler.types.types', 'compiler.types.layout', 'compiler.types.exhaust', 'compiler.traits.solver', 'compiler.traits.mono', 'compiler.types.typeck', 'compiler.types', 'compiler.traits', 'compiler.typeck.session', 'compiler.typeck', 'compiler.typeck_traits.session', 'compiler.typeck_traits', 'compiler.mir.mir', 'compiler.mir.drop', 'compiler.mir.builder', 'compiler.mir']), ('qa_mir_builder_and_drop_b.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.source.manager', 'compiler.diag.code', 'compiler.diag.emitter', 'compiler.diag.format', 'compiler.diag.json', 'compiler.kernel_source_diag.session', 'compiler.lex.token', 'compiler.lex.scanner', 'compiler.lexer.session', 'compiler.syntax.ast', 'compiler.syntax.parse', 'compiler.parser.session', 'compiler.resolve.symtab', 'compiler.resolve.rib', 'compiler.resolve.resolver', 'compiler.hir.hir', 'compiler.hir.lower', 'compiler.resolve_hir.session', 'compiler.types.types', 'compiler.types.layout', 'compiler.types.exhaust', 'compiler.traits.solver', 'compiler.traits.mono', 'compiler.types.typeck', 'compiler.types', 'compiler.traits', 'compiler.typeck.session', 'compiler.typeck', 'compiler.typeck_traits.session', 'compiler.typeck_traits', 'compiler.mir.mir', 'compiler.mir.drop', 'compiler.mir.builder', 'compiler.mir']), ('qa_mir_builder_and_drop_c.ax', ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.source.manager', 'compiler.diag.code', 'compiler.diag.emitter', 'compiler.diag.format', 'compiler.diag.json', 'compiler.kernel_source_diag.session', 'compiler.lex.token', 'compiler.lex.scanner', 'compiler.lexer.session', 'compiler.syntax.ast', 'compiler.syntax.parse', 'compiler.parser.session', 'compiler.resolve.symtab', 'compiler.resolve.rib', 'compiler.resolve.resolver', 'compiler.hir.hir', 'compiler.hir.lower', 'compiler.resolve_hir.session', 'compiler.types.types', 'compiler.types.layout', 'compiler.types.exhaust', 'compiler.traits.solver', 'compiler.traits.mono', 'compiler.types.typeck', 'compiler.types', 'compiler.traits', 'compiler.typeck.session', 'compiler.typeck', 'compiler.typeck_traits.session', 'compiler.typeck_traits', 'compiler.mir.mir', 'compiler.mir.drop', 'compiler.mir.builder', 'compiler.mir']), ('qa_mir_text_roundtrip.ax', ['compiler.mir.mir'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
