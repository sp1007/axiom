#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/resolve_hir (T144, T488)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [
    bc.MergeGroup(
        'qa_resolve_hir_all.ax',
        ['qa_resolve_hir_corpus_neg_a.ax', 'qa_resolve_hir_corpus_neg_b.ax', 'qa_resolve_hir_corpus_neg_c.ax', 'qa_resolve_hir_corpus_neg_d.ax', 'qa_resolve_hir_corpus_pos_a.ax', 'qa_resolve_hir_corpus_pos_b.ax', 'qa_resolve_hir_corpus_pos_c.ax', 'qa_resolve_hir_corpus_wide_a.ax', 'qa_resolve_hir_corpus_wide_b.ax', 'qa_resolve_hir_multifile_modules_a.ax', 'qa_resolve_hir_multifile_modules_b.ax'],
        ['compiler.kernel.id', 'compiler.kernel.hash', 'compiler.kernel.arena', 'compiler.kernel.interner', 'compiler.source.span', 'compiler.source.manager', 'compiler.diag.code', 'compiler.diag.emitter', 'compiler.diag.format', 'compiler.diag.json', 'compiler.kernel_source_diag.session', 'compiler.lex.token', 'compiler.lex.scanner', 'compiler.lexer.session', 'compiler.syntax.ast', 'compiler.syntax.parse', 'compiler.parser.session', 'compiler.resolve.symtab', 'compiler.resolve.rib', 'compiler.resolve.resolver', 'compiler.hir.hir', 'compiler.hir.lower', 'compiler.resolve_hir.session'], timeout=1200,
    ),
]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
