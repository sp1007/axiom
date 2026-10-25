#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/obj (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_coff_edge_cases.ax', ['compiler.kernel.id', 'compiler.kernel.arena', 'compiler.obj.coff', 'compiler.obj.writer', 'compiler.obj']), ('qa_coff_writer_diff.ax', ['compiler.kernel.id', 'compiler.kernel.arena', 'compiler.obj.coff', 'compiler.obj.writer', 'compiler.obj']), ('qa_obj_model.ax', ['compiler.kernel.id', 'compiler.kernel.arena', 'compiler.obj.coff', 'compiler.obj.writer', 'compiler.obj'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
