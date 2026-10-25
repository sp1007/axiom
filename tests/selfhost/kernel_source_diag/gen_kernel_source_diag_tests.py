#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/kernel_source_diag (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_corpus_differential.ax', ['compiler.kernel_source_diag.session']), ('qa_session_integration.ax', ['compiler.kernel_source_diag.session'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
