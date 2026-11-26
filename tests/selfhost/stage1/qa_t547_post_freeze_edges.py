#!/usr/bin/env python3
"""QA boundary cross-check for T547: the post-freeze skip rule must not hide real parity bugs.

Usage: qa_t547_post_freeze_edges.py <root> <tmp>
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stage1_oracle as oracle  # noqa: E402

CODE = "AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP"


def doc(*codes, **extra):
    d = {"schema": 1, "errors": len(codes), "warnings": 0, "diagnostics": [{"code": c, "message": "m"} for c in codes]}
    d.update(extra)
    return json.dumps(d).encode()


def test_rule_edges():
    skip = oracle.stage0_reports_post_freeze
    # The code appearing only in a message / related field is not axiom0 reporting it.
    mentions = json.dumps({"diagnostics": [{"code": "AX_TYPE_MISMATCH", "message": CODE, "related": [CODE]}]}).encode()
    assert not skip((1, b"", mentions))
    # Prefix / suffix lookalikes are different codes.
    assert not skip((1, b"", doc(CODE + "_X")))
    assert not skip((1, b"", doc("X" + CODE)))
    # stdout is used when stderr is empty (same precedence as canonical_json_diag).
    assert skip((1, doc(CODE), b""))
    # stderr wins when both are present: a non-post-freeze stderr is still compared.
    assert not skip((1, doc(CODE), doc("AX_TYPE_MISMATCH")))
    # Malformed shapes never skip (they reach the comparison, which fails loudly).
    assert not skip((1, b"", b"[]"))
    assert not skip((1, b"", b'{"diagnostics": "x"}'))
    assert not skip((1, b"", b'{"diagnostics": [1, null, "AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP"]}'))
    assert not skip((1, b"", b"{"))
    assert not skip((139, b"", b""))  # crash with no output
    # Exit code alone never decides.
    assert skip((0, b"", doc(CODE)))


def test_sample_edges(tmp):
    root = os.path.join(tmp, "t547_edges")
    for d in ("p", "q", "h"):
        os.makedirs(os.path.join(root, "tests", d), exist_ok=True)

    def mk(rel, helper=False):
        with open(os.path.join(root, rel), "w", encoding="utf-8", newline="\n") as f:
            f.write("// test: helper\n" if helper else "// test: ui\n")

    for n in ("a1", "a2", "a3", "a4"):
        mk("tests/p/%s.ax" % n)
    mk("tests/q/b1.ax")
    mk("tests/q/b2.ax")
    mk("tests/h/helper1.ax", helper=True)

    # Accept-all filter is identical to no filter.
    pats = ["tests/p/*.ax", "tests/q/*.ax", "tests/h/*.ax"]
    plain = oracle.collect_sample(root, pats, per_pattern=3)
    skipped, starved = [], []
    filt = oracle.collect_sample(root, pats, per_pattern=3, accept=lambda r: True, skipped=skipped, starved=starved)
    assert plain == filt, (plain, filt)
    assert skipped == [] and starved == [], (skipped, starved)
    # Helper-only pattern has no candidates, so it is not "starved".
    assert "tests/h/*.ax" not in starved

    # Everything in one pattern skipped: that pattern (and only it) is starved; others still fill.
    skipped, starved = [], []
    got = oracle.collect_sample(
        root, pats, per_pattern=3, accept=lambda r: not r.startswith("tests/q/"), skipped=skipped, starved=starved
    )
    assert starved == ["tests/q/*.ax"], starved
    assert skipped == ["tests/q/b1.ax", "tests/q/b2.ax"], skipped
    assert got == ["tests/p/a1.ax", "tests/p/a2.ax", "tests/p/a3.ax"], got

    # The filter is consulted only until per_pattern files are kept (no needless stage-0 runs).
    seen = []

    def accept(rel):
        seen.append(rel)
        return True

    oracle.collect_sample(root, ["tests/p/*.ax"], per_pattern=3, accept=accept)
    assert seen == ["tests/p/a1.ax", "tests/p/a2.ax", "tests/p/a3.ax"], seen

    # Partial starvation (1 of 3 kept) is not an error by itself: the rule only forbids 0.
    skipped, starved = [], []
    got = oracle.collect_sample(
        root, ["tests/p/*.ax"], per_pattern=3, accept=lambda r: r.endswith("a4.ax"), skipped=skipped, starved=starved
    )
    assert got == ["tests/p/a4.ax"] and starved == [], (got, starved)


def test_no_hardcoded_exclusions():
    src = open(os.path.join(HERE, "stage1_oracle.py"), "r", encoding="utf-8").read()
    assert "bug_float" not in src and "float_unsupported" not in src, "hand-maintained exclusion in the oracle"
    # The skip decision must be taken from stage-0's output, not from axiomc's.
    assert "run_cmd([stage0, \"check\", \"--json\"" in src.replace("\n", " ").replace("  ", " ") or "[stage0, \"check\"" in src


def main():
    tmp = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(HERE, "_tmp_t547")
    os.makedirs(tmp, exist_ok=True)
    test_rule_edges()
    test_sample_edges(tmp)
    test_no_hardcoded_exclusions()
    print("QA-T547-POST-FREEZE-EDGES OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
