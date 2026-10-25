#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/parse (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_parse_corpus_a.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_corpus_b.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_corpus_c.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_corpus_d.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_corpus_e.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_corpus_f.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_corpus_g.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_corpus_h.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_corpus_i.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_corpus_j.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_heavy_a.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_heavy_b.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_qa_edge.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_qa_tuple_struct.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_recovery_a.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_recovery_b.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_terminator_a.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_terminator_b.ax', ['compiler.syntax.parse', 'compiler.lexer.session']), ('qa_parse_terminator_heavy.ax', ['compiler.syntax.parse', 'compiler.lexer.session'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
