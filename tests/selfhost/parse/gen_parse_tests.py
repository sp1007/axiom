#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/parse (T144, T488)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [
    bc.MergeGroup(
        'qa_parse_interp.ax',
        ['qa_parse_corpus_a.ax', 'qa_parse_corpus_b.ax', 'qa_parse_corpus_c.ax', 'qa_parse_corpus_d.ax', 'qa_parse_corpus_e.ax', 'qa_parse_corpus_f.ax', 'qa_parse_corpus_g.ax', 'qa_parse_corpus_h.ax', 'qa_parse_corpus_i.ax', 'qa_parse_corpus_j.ax', 'qa_parse_recovery_a.ax', 'qa_parse_recovery_b.ax', 'qa_parse_terminator_a.ax', 'qa_parse_terminator_b.ax'],
        ['compiler.syntax.parse', 'compiler.lexer.session'], timeout=600,
    ),
    bc.MergeGroup(
        'qa_parse_native.ax',
        ['qa_parse_heavy_a.ax', 'qa_parse_heavy_b.ax', 'qa_parse_qa_edge.ax', 'qa_parse_qa_tuple_struct.ax', 'qa_parse_terminator_heavy.ax'],
        ['compiler.syntax.parse', 'compiler.lexer.session'], modes='native', timeout=300, reason='heavy parser corpus batch; interp twin is qa_parse_interp.ax',
    ),
]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
