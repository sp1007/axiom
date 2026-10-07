#!/usr/bin/env python3
"""Run the gatecheck self-tests: `python tools/tests/gatecheck/run_selftests.py [-v] [name-substring]`.

Exit status 0 when every test passes, non-zero otherwise. Python 3 standard library only.
"""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv):
    verbose = "-v" in argv
    names = [a for a in argv if not a.startswith("-")]
    sys.path.insert(0, str(HERE))
    loader = unittest.TestLoader()
    suite = loader.discover(str(HERE), pattern="test_*.py")
    if names:
        wanted = unittest.TestSuite()

        def walk(s):
            for t in s:
                if isinstance(t, unittest.TestSuite):
                    walk(t)
                elif any(n in t.id() for n in names):
                    wanted.addTest(t)

        walk(suite)
        suite = wanted
    result = unittest.TextTestRunner(verbosity=2 if verbose else 1).run(suite)
    print("SELFTEST %d tests, %d failures, %d errors" %
          (result.testsRun, len(result.failures), len(result.errors)))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
