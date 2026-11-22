#!/usr/bin/env python3
"""Scenario driver of the T423g tests: the per-task gate reports `axtest.py --smoke --check` (tests/smoke.list hygiene).

Usage: driver.py <scenario>. Prints `OK <scenario>` and exits 0 when every assertion held, otherwise prints the
failed expectation on stderr and exits 1.

Each scenario builds a tiny git repository in a temporary directory (a handful of test files and a smoke list), commits
it, applies the "change set" as working-tree changes and calls `taskgate.smoke_hygiene` exactly as `taskgate.gate`
does. No compiler runs. Python 3 standard library only.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[3] / "tools"
sys.path.insert(0, str(TOOLS))
import axtest  # noqa: E402
import axtest_cache  # noqa: E402
import taskgate  # noqa: E402

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}

BS = chr(92)  # a literal backslash (the expected-output escape of the test directives)
RUN = "// test: run\n// stdout: %s" + BS + "n\n//@ out %s" + BS + "n\n"
BASE = {
    "tests/run/hello.ax": RUN % ("Xin chào thế giới", "Xin chào thế giới"),
    "tests/run/other.ax": RUN % ("o", "o"),
    "tests/ui/err.ax": "// test: ui\n//@ diag AX_X error 3\nx //~ ERROR AX_X\n",
    "tests/diff/d.ax": "// test: diff\n// stdout: d\n\n//@ out d\n\n",
    "tests/smoke.list": ("always: run/hello.ax\nalways: ui/err.ax\nalways: diff/d.ax\n"
                         "pool run: run/other.ax\npool ui: ui/err.ax\npool diff: diff/d.ax\n"),
}


class Failure(Exception):
    pass


def expect(cond, what):
    if not cond:
        raise Failure(what)


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8"))


def git(root, *args):
    env = dict(os.environ)
    env.update(GIT_ENV)
    r = subprocess.run(["git", *args], cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if r.returncode != 0:
        raise Failure("git %s: %s" % (args, r.stderr.decode("utf-8", "replace")))


def make_repo(tmp):
    root = Path(tmp) / "repo"
    for rel, text in BASE.items():
        write(root, rel, text)
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    return root


def hygiene(root):
    changed = axtest_cache.changed_paths(root)
    tests = axtest.discover(root / "tests")
    return taskgate.smoke_hygiene(root, tests, {}, changed), changed


def scenario_healthy_change_passes(root):
    write(root, "tests/run/extra.ax", RUN % ("e", "e"))
    r, _ = hygiene(root)
    expect(r["ok"], "a healthy smoke list must be reported ok: %r" % r["problems"])
    expect(not r["reasons"], "no gate failure expected: %r" % r["reasons"])


def scenario_new_group_without_pool_fails(root):
    write(root, "tests/newgrp/a.ax", RUN % ("n", "n"))
    r, changed = hygiene(root)
    expect("tests/newgrp/a.ax" in changed, "the new file must be in the change set: %r" % changed)
    expect(not r["ok"], "the missing pool must be a smoke-check problem")
    expect(any("group newgrp has no pool entry" in p for p in r["problems"]), repr(r["problems"]))
    expect(r["new_groups_without_pool"] == ["newgrp"], repr(r["new_groups_without_pool"]))
    expect(len(r["reasons"]) == 1 and "newgrp" in r["reasons"][0] and "pool newgrp:" in r["reasons"][0],
           "the failure message must name the group and the fix: %r" % r["reasons"])


def scenario_new_group_with_pool_passes(root):
    write(root, "tests/newgrp/a.ax", RUN % ("n", "n"))
    write(root, "tests/smoke.list", BASE["tests/smoke.list"] + "pool newgrp: newgrp/a.ax\n")
    r, _ = hygiene(root)
    expect(r["ok"], "pool entry added: smoke list must be ok: %r" % r["problems"])
    expect(not r["reasons"] and not r["new_groups_without_pool"], repr(r["reasons"]))


def scenario_preexisting_gap_is_printed_not_failing(root):
    # HEAD already has a group without a pool; the change set only edits a file of it and an unrelated one.
    write(root, "tests/old/a.ax", RUN % ("a", "a"))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "group old without a pool")
    write(root, "tests/old/a.ax", RUN % ("a2", "a2"))
    write(root, "tests/run/extra.ax", RUN % ("e", "e"))
    r, _ = hygiene(root)
    expect(not r["ok"] and any("group old has no pool entry" in p for p in r["problems"]),
           "the pre-existing gap must still be reported: %r" % r["problems"])
    expect(not r["reasons"] and not r["new_groups_without_pool"],
           "a gap that predates the change set must not fail the gate: %r" % r["reasons"])


def scenario_range_base_decides_newness(root):
    # Group added by an earlier commit of the range: new relative to the range base, known relative to HEAD.
    write(root, "tests/newgrp/a.ax", RUN % ("n", "n"))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "add group")
    tests = axtest.discover(root / "tests")
    changed = ["tests/newgrp/a.ax"]
    at_head = taskgate.smoke_hygiene(root, tests, {}, changed, "HEAD")
    at_base = taskgate.smoke_hygiene(root, tests, {}, changed, "HEAD~1")
    expect(not at_head["reasons"], "known at HEAD: %r" % at_head["reasons"])
    expect(at_base["new_groups_without_pool"] == ["newgrp"], "new relative to HEAD~1: %r" % at_base)


def scenario_markdown_names_problems(root):
    # the Markdown of a summary names the problem lines (rendering is part of the gate output)
    write(root, "tests/newgrp/a.ax", RUN % ("n", "n"))
    r, _ = hygiene(root)
    s = {"smoke_check": r}
    text = "\n".join(l for l in taskgate.markdown_smoke_lines(s))
    expect("SMOKE-CHECK PROBLEM group newgrp has no pool entry" in text, text)
    expect("SMOKE-CHECK NEW-GROUP" in text, text)


SCENARIOS = {n[len("scenario_"):]: f for n, f in sorted(globals().items()) if n.startswith("scenario_")}


def main(argv):
    if len(argv) != 1 or argv[0] not in SCENARIOS:
        print("usage: driver.py <%s>" % "|".join(SCENARIOS), file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="taskgate-smoke-") as tmp:
        try:
            root = make_repo(tmp)
            SCENARIOS[argv[0]](root)
        except Failure as e:
            print("FAIL %s: %s" % (argv[0], e), file=sys.stderr)
            return 1
    sys.stdout.buffer.write(("OK %s" % argv[0]).encode("utf-8") + bytes([10]))  # LF on every platform (exact bytes)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
