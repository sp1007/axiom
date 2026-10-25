#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/diag (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_diag_codes.ax', ['compiler.diag.code']), ('qa_diag_emitter.ax', ['compiler.diag.emitter', 'compiler.diag.code', 'compiler.diag.format', 'compiler.source.span']), ('qa_diag_format_json.ax', ['compiler.diag.json', 'compiler.diag.format'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
