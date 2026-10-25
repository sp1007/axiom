#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/parser (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_parser_diff_corpus_wide.ax', ['compiler.parser.session']), ('qa_parser_diff_neg_a.ax', ['compiler.parser.session']), ('qa_parser_diff_pos_a.ax', ['compiler.parser.session']), ('qa_parser_diff_pos_b.ax', ['compiler.parser.session']), ('qa_parser_session_integration.ax', ['compiler.parser.session'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
