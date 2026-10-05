"""Gate tests added by QA for T006 (seams and edge cases the engineer's suite does not cover).

Run: python tools/tests/archcheck/run_selftests.py gate_t006
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent.parent
sys.path.insert(0, str(TOOLS))
import archcheck  # noqa: E402

SRC = "bootstrap/axiom0/src"


def src(rel):
    return SRC + "/" + rel


def run_tree(files):
    rules = archcheck.parse_rules(archcheck.read_text(str(TOOLS / "archcheck_rules.txt")))
    with tempfile.TemporaryDirectory() as tmp:
        for rel, content in files.items():
            p = Path(tmp) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content.encode("utf-8"))
        violations, scanned = archcheck.run_checks(rules, tmp)
        return [(v.path, v.line, v.inv, v.msg) for v in violations], scanned


class GateLayerSeams(unittest.TestCase):
    def test_deep_relative_include_from_target_into_front_end(self):
        # target/x64 is two directories deep; "../../hir/hir.h" must normalise to hir/ and hit INV-LAYER-005.
        files = {src("target/x64/enc.c"): '#include "../../hir/hir.h"\n#include "../../kernel/k.h"\n',
                 src("hir/hir.h"): "\n", src("kernel/k.h"): "\n"}
        got, _ = run_tree(files)
        self.assertEqual([(p, l, i) for p, l, i, _m in got], [(src("target/x64/enc.c"), 1, "INV-LAYER-005")])

    def test_objmodel_seams(self):
        files = {
            src("objmodel/om.h"): '#include "diag/diag.h"\n',     # objmodel may include only kernel
            src("diag/diag.h"): "\n",
            src("verify/v.c"): '#include "objmodel/om.h"\n',      # verify is not a user of objmodel
            src("driver/d.c"): '#include "objmodel/om.h"\n',      # driver wires the pipeline: allowed
            src("link/l.c"): '#include "obj/o.h"\n#include "objmodel/om.h"\n',  # allowed
            src("obj/o.h"): "\n",
        }
        got, _ = run_tree(files)
        self.assertEqual(sorted((p, l, i) for p, l, i, _m in got),
                         [(src("objmodel/om.h"), 1, "INV-LAYER-001"), (src("verify/v.c"), 1, "INV-LAYER-001")])

    def test_include_escaping_src_root_is_ignored_not_crashing(self):
        files = {src("lex/a.c"): '#include "../../../../outside.h"\n#include "../../generated/registry.h"\n'}
        got, _ = run_tree(files)
        self.assertEqual(got, [])

    def test_unknown_subdirectory_of_target(self):
        files = {src("target/arm64/enc.c"): "\n"}
        got, _ = run_tree(files)
        self.assertEqual([(p, i) for p, _l, i, _m in got], [(src("target/arm64/enc.c"), "INV-LAYER-001")])


def mutable_names(code):
    got, _ = run_tree({src("mir/x.c"): code})
    return [m.split("'")[1] for _p, _l, i, m in got if i == "INV-LAYER-006" and "mutable" in m]


class GateGlobals(unittest.TestCase):
    def test_extra_mutable_shapes(self):
        for code, names in [
            ("int (*table[4])(void);\n", ["table"]),
            ("static int a[2][2] = {{1, 2}, {3, 4}}, b;\n", ["a", "b"]),
            ("char *const *pp;\n", ["pp"]),
            ("static struct { int x; } anon_state;\n", ["anon_state"]),
        ]:
            with self.subTest(code=code):
                self.assertEqual(mutable_names(code), names)

    def test_extra_clean_shapes(self):
        for code in [
            "static const int grid[2][2] = {{1, 2}, {3, 4}};\n",
            "enum { N = sizeof(int) * 2 };\n",
            "static int (*const ops[2])(int) = { 0, 0 };\n",
        ]:
            with self.subTest(code=code):
                self.assertEqual(mutable_names(code), [])


def output_fns(code, rel="mir/x.c"):
    got, _ = run_tree({src(rel): code})
    return [(l, m) for _p, l, i, m in got if i == "INV-LAYER-006" and "must not call" in m]


class GateOutput(unittest.TestCase):
    def test_stream_chosen_by_expression_is_flagged(self):
        code = "void f(int e, FILE *o) {\n    fprintf(e ? stderr : o, \"x\");\n}\n"
        self.assertEqual([l for l, _m in output_fns(code)], [2])

    def test_pragma_two_lines_above_is_not_honoured(self):
        code = ("void f(void) {\n    /* archcheck:allow(INV-LAYER-006): debugging hook */\n\n"
                "    printf(\"x\");\n}\n")
        self.assertEqual([l for l, _m in output_fns(code)], [4])

    def test_multiline_call_reports_first_line(self):
        code = "void f(void) {\n    fputs(\"x\",\n          stderr);\n}\n"
        self.assertEqual([l for l, _m in output_fns(code)], [2])


class GateCli(unittest.TestCase):
    def test_cli_root_and_rules_from_another_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / SRC / "types" / "t.c"
            p.parent.mkdir(parents=True)
            p.write_text('#include "interp/i.h"\n', encoding="utf-8")
            std = Path(tmp) / "std" / "core" / "a.ax"
            std.parent.mkdir(parents=True)
            std.write_text("\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(TOOLS / "archcheck.py"), "--root", tmp,
                                "--rules", str(TOOLS / "archcheck_rules.txt")],
                               capture_output=True, text=True, cwd=os.path.dirname(tmp))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            lines = r.stdout.strip().splitlines()
            self.assertEqual(len(lines), 2, r.stdout)
            self.assertTrue(lines[0].startswith(SRC + "/types/t.c:1: layer types must not include interp"), lines[0])
            self.assertTrue(lines[0].endswith("[INV-LAYER-004]"), lines[0])
            self.assertEqual(lines[1], "archcheck: 2 files scanned, 1 violations")


if __name__ == "__main__":
    unittest.main()
