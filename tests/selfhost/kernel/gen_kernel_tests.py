#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/selfhost/kernel (T144)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))
sys.path.insert(0, HERE)

import bundle_common as bc  # noqa: E402
import gen_hash_native  # noqa: E402

BUNDLES = [
    ("qa_kernel_arena.ax", ["compiler.kernel.arena"]),
    ("qa_kernel_dynarray.ax", ["compiler.kernel.dynarray"]),
    ("qa_kernel_id.ax", ["compiler.kernel.id"]),
    ("qa_kernel_interner.ax", ["compiler.kernel.interner"]),
]


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    rc1 = gen_hash_native.main(argv=argv)
    rc2 = bc.run_template_generator(HERE, BUNDLES, argv=argv, root=ROOT)
    return rc1 or rc2


if __name__ == "__main__":
    sys.exit(main())
