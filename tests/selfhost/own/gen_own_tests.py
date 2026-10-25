#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/own (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_own_init.ax', ['compiler.own.cap', 'compiler.own.move_ck', 'compiler.own.init', 'compiler.own.unsafe_ck', 'compiler.diag.code', 'compiler.diag.emitter'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
