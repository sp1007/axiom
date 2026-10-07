"""Self-tests for tools/gatecheck.py (T022). Each test builds a small repository in a temp dir.

The fixture repository has the parts gatecheck reads: spec/SPEC-00-bootstrap.md (feature and
shortcut tables, milestone blocks), spec/invariants.md, spec/selfhost-subset.tsv, a task board under
_workspaces/tasks, tests/, a stub tools/axtest.py that prints a canned JSON result document, and
stub check programs. Python 3 standard library only.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATECHECK = HERE.parent.parent / "gatecheck.py"

SPEC00_HEAD = """\
# SPEC-00 fixture

| Id | Forbidden | Source |
|---|---|---|
| X-LLVM | llvm | r |
| X-GC | gc | r |

| Id | Feature | Oracle task(s) | Native task | Milestone |
|---|---|---|---|---|
| F-INT | integers | T017 | T028 (constants), T037 (all widths) | MS-P3 |
| F-CF | control flow | T017 | T033 | MS-P3 |
| F-MUT | mutation | T030 | T033 | MS-P5 |

"""

AXTEST_STUB = """\
import json, os, sys
args, filters, root, i = sys.argv[1:], [], None, 0
while i < len(args):
    if args[i] in ("--root", "--compiler"):
        if args[i] == "--root":
            root = args[i + 1]
        i += 2
        continue
    if not args[i].startswith("--"):
        filters.append(args[i])
    i += 1
with open(os.path.join(root, "axtest_results.json"), encoding="utf-8") as fh:
    results = json.load(fh)
sel = [r for r in results if not filters or any(f in r["id"] for f in filters)]
with open(os.path.join(root, "axtest_argv.json"), "w", encoding="utf-8") as fh:
    json.dump(args, fh)
print(json.dumps({"schema": 1, "results": sel}))
sys.exit(1 if any(r["state"] in ("FAIL", "XPASS", "CRASH", "TIMEOUT") for r in sel) else 0)
"""


def milestone(mid, gate, previous, must_pass, checks=(), native=(), introduces=(), modes=("interp",),
              forbidden=("X-LLVM",), **extra):
    d = {
        "id": mid, "title": "t " + mid, "phase": "P" + mid[4:], "gate": gate, "previous": previous,
        "aliases": [], "goal": "g", "components": [], "introduces": list(introduces),
        "native": list(native), "modes": list(modes), "must_pass": list(must_pass),
        "checks": list(checks), "forbidden": list(forbidden),
    }
    d.update(extra)
    return d


def block(obj_or_text):
    body = obj_or_text if isinstance(obj_or_text, str) else json.dumps(obj_or_text, indent=2)
    return "```milestone\n" + body + "\n```\n\n"


INV_OK = """\
# invariants fixture

```text
### INV-<GROUP>-<NNN> - <short title>
- statement: x
```

### INV-KERN-001 \u2014 Typed IDs
- statement: ids are typed
- source: s
- verify: tests/unit/kernel
- since: T007
- check: c

### INV-ORACLE-001 - Later
- statement: later
- source: s
- verify: tests/diff
- since: T029
- check: c
"""

TSV_OK = "feature\toracle\tnative\tconsumer\tneed\nF-INT\tT017\tT028 T037\tT069\tnums\n"


class Repo:
    def __init__(self, tmp):
        self.root = Path(tmp)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return p

    def task(self, tid, state="todo", depends=(), status=None, extra=""):
        status = status or state
        self.write("_workspaces/tasks/%s/%s-x.md" % (state, tid),
                   "---\nid: %s\ntitle: t\nstatus: %s\ndepends: [%s]\n%s---\n# %s\n"
                   % (tid, status, ", ".join(depends), extra, tid))

    def results(self, results):
        self.write("axtest_results.json", json.dumps(results))

    def run(self, *args):
        cmd = [sys.executable, str(GATECHECK), "--root", str(self.root)] + list(args)
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")


def base_repo(tmp, blocks=None, inv=INV_OK, tsv=TSV_OK, results=None):
    r = Repo(tmp)
    for tid, st, deps in (("T007", "done", ()), ("T017", "done", ()), ("T022", "doing", ("T017",)),
                          ("T028", "todo", ("T022",)), ("T029", "todo", ("T028",)),
                          ("T030", "todo", ("T029",)), ("T033", "todo", ("T030",)),
                          ("T037", "todo", ("T033",)), ("T044", "todo", ("T037",)),
                          ("T069", "todo", ("T044",))):
        r.task(tid, st, deps)
    if blocks is None:
        blocks = [milestone("MS-P1", "T022", None, ["tests/unit/kernel"], checks=["harness_check"]),
                  milestone("MS-P3", "T022", "MS-P1", ["tests/run/basic"], checks=["gatecheck"],
                                introduces=["F-INT", "F-CF"]),
                  milestone("MS-P5", "T044", "MS-P3", ["tests/run/vars"], native=["F-INT", "F-CF"],
                            introduces=["F-MUT"], modes=["interp", "native"])]
    r.write("spec/SPEC-00-bootstrap.md", SPEC00_HEAD + "".join(block(b) for b in blocks))
    r.write("spec/invariants.md", inv)
    r.write("spec/selfhost-subset.tsv", tsv)
    r.write("tests/unit/kernel/kernel_unit.test", "cmd: {build}/axiom0-unit\nexit: 0\n")
    r.write("tests/unit/kernel/test_x.c", "/* unit */\n")
    r.write("tests/run/basic/ret.ax", "// test: run\n// exit: 1\n// native-after: T033\nfn main() -> i32 { 1 }\n")
    r.write("tools/axtest.py", AXTEST_STUB)
    r.write(".claude/skills/axiom-tasks/scripts/harness_check.py", "import sys\nsys.exit(0)\n")
    r.results(results if results is not None else [
        {"id": "unit/kernel/kernel_unit.test", "mode": "", "state": "PASS", "message": ""},
        {"id": "run/basic/ret.ax", "mode": "interp", "state": "PASS", "message": ""},
        {"id": "run/basic/ret.ax", "mode": "native", "state": "SKIP", "message": "native after T033"},
    ])
    return r


class GatecheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="gatecheck-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def lines(self, out):
        return [ln for ln in out.splitlines() if ln.strip()]

    # ---- happy path / due selection -------------------------------------------------------

    def test_pass_current_gate(self):
        r = base_repo(self.tmp)
        rc, out, err = r.run("--gate", "T022")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.lines(out), ["MS-P1 PASS", "MS-P3 PASS"])

    def test_without_gate_only_done_gates_are_due(self):
        r = base_repo(self.tmp)
        rc, out, err = r.run()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.lines(out), [])

    def test_done_gate_is_due_without_flag(self):
        r = base_repo(self.tmp)
        shutil.rmtree(r.root / "_workspaces/tasks/doing")
        r.task("T022", "done", ("T017",))
        rc, out, _ = r.run()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.lines(out), ["MS-P1 PASS", "MS-P3 PASS"])

    def test_c_unit_dir_uses_axiom0_unit_manifest(self):
        blocks = [milestone("MS-P1", "T022", None, ["tests/unit/source"])]
        r = base_repo(self.tmp, blocks=blocks)
        r.write("tests/unit/source/test_source.c", "/* unit */\n")
        rc, out, err = r.run("--gate", "T022")
        self.assertEqual(rc, 0, out + err)
        argv = json.loads((r.root / "axtest_argv.json").read_text(encoding="utf-8"))
        self.assertIn("unit/kernel/kernel_unit.test", argv)

    # ---- step 1: structure ----------------------------------------------------------------

    def test_bad_json(self):
        r = base_repo(self.tmp, blocks=['{"id": "MS-P1",'])
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("not valid JSON", out)

    def test_missing_and_extra_field(self):
        b = milestone("MS-P1", "T022", None, ["tests/unit/kernel"], color="red")
        del b["goal"]
        r = base_repo(self.tmp, blocks=[b])
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("missing field(s) goal", out)
        self.assertIn("unknown field(s) color", out)

    def test_wrong_type(self):
        b = milestone("MS-P1", "T022", None, ["tests/unit/kernel"])
        b["must_pass"] = "tests/unit/kernel"
        r = base_repo(self.tmp, blocks=[b])
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("field `must_pass` has the wrong type", out)

    def test_duplicate_id_and_bad_previous(self):
        blocks = [milestone("MS-P1", "T022", None, ["tests/unit/kernel"]),
                  milestone("MS-P1", "T022", "MS-P0", ["tests/unit/kernel"])]
        r = base_repo(self.tmp, blocks=blocks)
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("duplicate milestone id", out)
        self.assertIn("`previous` is 'MS-P0'", out)

    def test_unknown_feature_shortcut_check_and_gate(self):
        b = milestone("MS-P1", "T999", None, ["tests/unit/kernel"], introduces=["F-NOPE"],
                      forbidden=["X-NOPE"], checks=["telepathy"])
        r = base_repo(self.tmp, blocks=[b])
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        for text in ("unknown feature id F-NOPE", "unknown shortcut id X-NOPE", "unknown check telepathy",
                     "gate T999 is not a board task"):
            self.assertIn(text, out)

    def test_glob_in_must_pass(self):
        r = base_repo(self.tmp, blocks=[milestone("MS-P1", "T022", None, ["tests/unit/*"])])
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("without globs", out)

    # ---- steps 2-3: tests -----------------------------------------------------------------

    def test_missing_must_pass_path(self):
        blocks = [milestone("MS-P1", "T022", None, ["tests/nothing"])]
        r = base_repo(self.tmp, blocks=blocks)
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 1)
        self.assertIn("MS-P1 BLOCKED: must_pass path tests/nothing does not exist", out)

    def test_empty_must_pass_path(self):
        blocks = [milestone("MS-P1", "T022", None, ["tests/empty"])]
        r = base_repo(self.tmp, blocks=blocks)
        r.write("tests/empty/notes.md", "nothing\n")
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 1)
        self.assertIn("holds no test", out)

    def test_fail_blocks_and_later_milestones_follow(self):
        r = base_repo(self.tmp, results=[
            {"id": "unit/kernel/kernel_unit.test", "mode": "", "state": "FAIL", "message": "exit 1"},
            {"id": "run/basic/ret.ax", "mode": "interp", "state": "PASS", "message": ""},
        ])
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 1)
        self.assertIn("MS-P1 BLOCKED: FAIL unit/kernel/kernel_unit.test: exit 1", out)
        self.assertIn("MS-P3 BLOCKED: earlier milestone MS-P1 is blocked", out)

    def test_xpass_crash_timeout_block(self):
        for state in ("XPASS", "CRASH", "TIMEOUT"):
            with self.subTest(state=state):
                tmp = tempfile.mkdtemp(prefix="gatecheck-")
                try:
                    r = base_repo(tmp, results=[
                        {"id": "unit/kernel/kernel_unit.test", "mode": "", "state": "PASS", "message": ""},
                        {"id": "run/basic/ret.ax", "mode": "interp", "state": state, "message": "m"},
                    ])
                    rc, out, _ = r.run("--gate", "T022")
                    self.assertEqual(rc, 1)
                    self.assertIn("MS-P3 BLOCKED: %s run/basic/ret.ax [interp]" % state, out)
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_xfail_must_name_open_task(self):
        r = base_repo(self.tmp, results=[
            {"id": "unit/kernel/kernel_unit.test", "mode": "", "state": "PASS", "message": ""},
            {"id": "run/basic/ret.ax", "mode": "interp", "state": "XFAIL", "message": "T017: gap -- x"},
        ])
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 1)
        self.assertIn("XFAIL run/basic/ret.ax [interp]: task T017 is already done", out)

    def test_xfail_open_task_accepted(self):
        r = base_repo(self.tmp, results=[
            {"id": "unit/kernel/kernel_unit.test", "mode": "", "state": "PASS", "message": ""},
            {"id": "run/basic/ret.ax", "mode": "interp", "state": "XFAIL", "message": "T030: gap -- x"},
        ])
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 0, out)

    def test_skip_reasons(self):
        cases = [
            ("native after T017", 1, "native after T017): task T017 is already done"),
            ("mode unavailable: native", 0, None),
            ("mode unavailable: interp", 1, "mode interp is required"),
            ("tool gcc not found", 0, None),
            ("compiler lacks feature opt", 1, "without an accepted reason"),
        ]
        for msg, want_rc, text in cases:
            with self.subTest(msg=msg):
                tmp = tempfile.mkdtemp(prefix="gatecheck-")
                try:
                    r = base_repo(tmp, results=[
                        {"id": "unit/kernel/kernel_unit.test", "mode": "", "state": "PASS", "message": ""},
                        {"id": "run/basic/ret.ax", "mode": "native", "state": "SKIP", "message": msg},
                    ])
                    # the directive scan must not trip over the test file for these cases
                    rc, out, _ = r.run("--gate", "T022")
                    self.assertEqual(rc, want_rc, out)
                    if text:
                        self.assertIn(text, out)
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_axtest_without_json(self):
        r = base_repo(self.tmp)
        r.write("tools/axtest.py", "print('no json')\n")
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 1)
        self.assertIn("produced no JSON document", out)

    # ---- step 4: native-after for native features -----------------------------------------

    def test_native_feature_with_native_after_left(self):
        r = base_repo(self.tmp)
        shutil.rmtree(r.root / "_workspaces/tasks/doing")
        r.task("T022", "done", ("T017",))
        r.task("T044", "doing", ("T037",))
        os.remove(r.root / "_workspaces/tasks/todo/T044-x.md")
        r.write("tests/run/vars/v.ax", "// test: run\n// exit: 0\nfn main() {}\n")
        rc, out, _ = r.run("--gate", "T044", "--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("MS-P5: native feature F-CF still has `native-after: T033` (tests/run/basic/ret.ax:3)",
                      out)

    # ---- step 5: checks -------------------------------------------------------------------

    def test_failing_check_blocks(self):
        r = base_repo(self.tmp)
        r.write(".claude/skills/axiom-tasks/scripts/harness_check.py",
                "print('harness: 2 problems')\nimport sys\nsys.exit(1)\n")
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 1)
        self.assertIn("MS-P1 BLOCKED: check harness_check exited 1: harness: 2 problems", out)

    def test_check_without_command_blocks(self):
        blocks = [milestone("MS-P1", "T022", None, ["tests/unit/kernel"], checks=["differential"])]
        r = base_repo(self.tmp, blocks=blocks)
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 1)
        self.assertIn("check differential has no command yet", out)

    def test_internal_gatecheck_check_reports_rule_problem(self):
        r = base_repo(self.tmp, tsv="feature\toracle\tnative\tconsumer\nF-INT\tT069\t\tT017\n")
        rc, out, _ = r.run("--gate", "T022")
        self.assertEqual(rc, 1)
        self.assertIn("MS-P1 PASS", out)
        self.assertIn("MS-P3 BLOCKED: gatecheck: rule (d)", out)

    # ---- rule (a): invariants -------------------------------------------------------------

    def test_invariant_verify_missing_for_done_task(self):
        inv = INV_OK.replace("verify: tests/unit/kernel", "verify: tests/unit/nowhere")
        r = base_repo(self.tmp, inv=inv)
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("INV-KERN-001: verify target tests/unit/nowhere does not exist although T007 is done",
                      out)

    def test_invariant_since_unknown_or_superseded(self):
        inv = INV_OK.replace("since: T029", "since: T555")
        r = base_repo(self.tmp, inv=inv)
        rc, out, _ = r.run("--no-run")
        self.assertIn("`since:` task T555 is not on the board", out)
        r.task("T029", "done", ("T028",), status="superseded", extra="superseded_by: T030\n")
        os.remove(r.root / "_workspaces/tasks/todo/T029-x.md")
        r.write("spec/invariants.md", INV_OK)
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("`since:` task T029 is superseded", out)

    def test_invariant_field_order_duplicate_and_target_kind(self):
        inv = INV_OK + textwrap.dedent("""
            ### INV-KERN-001 - Again
            - statement: s
            - source: s
            - verify: docs/x
            - since: T007
            - check: c

            ### INV-DET-001 - Order
            - statement: s
            - verify: tests/unit/kernel
            - source: s
            - since: T007
            - check: c
            """)
        r = base_repo(self.tmp, inv=inv)
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("INV-KERN-001 is defined twice", out)
        self.assertIn("verify target 'docs/x' is neither", out)
        self.assertIn("INV-DET-001: fields are statement, verify, source", out)

    def test_retired_invariant(self):
        inv = INV_OK + "\n### INV-DET-009 - Old\n- statement: RETIRED (ADR-0001)\n- source: s\n" \
                       "- verify: none\n- since: T007\n- check: none\n"
        r = base_repo(self.tmp, inv=inv)
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 0, out)

    # ---- rule (c): directives -------------------------------------------------------------

    def test_directive_names_done_or_unknown_task(self):
        r = base_repo(self.tmp)
        r.write("tests/run/basic/a.ax", "// test: run\n// exit: 0\n// native-after: T017\nfn main() {}\n")
        r.write("tests/run/basic/b.test", "cmd: x\nxfail: T404 spec gap\n")
        r.write("tests/run/basic/fixtures/c.ax", "// native-after: T017\n")
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("tests/run/basic/a.ax:3: `native-after: T017` but task T017 is already done", out)
        self.assertIn("tests/run/basic/b.test:2: `xfail: T404` but task T404 is not on the board", out)
        self.assertNotIn("fixtures", out)

    # ---- rule (d): self-host subset -------------------------------------------------------

    def test_subset_delivering_not_ancestor(self):
        tsv = TSV_OK + "F-CF\tT017\tT044\tT037\tcf\n"
        r = base_repo(self.tmp, tsv=tsv)
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("(F-CF): delivering task T044 is not an ancestor of the consumer T037", out)
        self.assertNotIn("delivering task T017", out)

    def test_subset_unknown_tasks_and_feature(self):
        tsv = TSV_OK + "F-ZZZ.SUB\tT404\t\u2014\tT405\tz\n"
        r = base_repo(self.tmp, tsv=tsv)
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("(F-ZZZ.SUB): feature id is not a SPEC-00 §4 feature", out)
        self.assertIn("consumer T405 is not on the board", out)

    def test_subset_refined_feature_and_same_task_ok(self):
        tsv = TSV_OK + "F-INT.WIDE\tT069\tT069\tT069\tsame task delivers and consumes\n"
        r = base_repo(self.tmp, tsv=tsv)
        rc, out, _ = r.run("--no-run")
        self.assertEqual(rc, 0, out)

    # ---- usage ----------------------------------------------------------------------------

    def test_bad_gate_argument(self):
        r = base_repo(self.tmp)
        rc, _out, err = r.run("--gate", "MS-P3")
        self.assertEqual(rc, 2)
        self.assertIn("--gate needs a task id", err)

    def test_gate_that_closes_nothing(self):
        r = base_repo(self.tmp)
        rc, out, _ = r.run("--gate", "T030", "--no-run")
        self.assertEqual(rc, 1)
        self.assertIn("--gate T030 closes no milestone", out)

    def test_real_repository_structure(self):
        """The real SPEC-00 manifests parse (step 1) — independent of test results and rules."""
        root = HERE.parent.parent.parent
        spec = root / "spec" / "SPEC-00-bootstrap.md"
        if not spec.is_file():
            self.skipTest("not run inside the repository")
        p = subprocess.run([sys.executable, str(GATECHECK), "--root", str(root), "--no-run"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        out = p.stdout.decode("utf-8")
        self.assertNotIn("SPEC-00", out, out)


if __name__ == "__main__":
    unittest.main()
