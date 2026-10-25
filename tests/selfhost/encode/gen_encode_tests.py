#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/encode (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

BUNDLES = [('qa_encode_edge_cases.ax', ['compiler.kernel.id', 'compiler.kernel.arena', 'compiler.obj.coff', 'compiler.target.x64.encode']), ('qa_encode_instructions.ax', ['compiler.kernel.id', 'compiler.kernel.arena', 'compiler.obj.coff', 'compiler.target.x64.encode']), ('qa_encode_relocs_and_frames.ax', ['compiler.kernel.id', 'compiler.kernel.arena', 'compiler.obj.coff', 'compiler.obj.writer', 'compiler.target.x64.encode'])]


def main(argv=None):
    return bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
