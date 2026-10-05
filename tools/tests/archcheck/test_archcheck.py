"""Self-tests of tools/archcheck.py (T006). Run: python tools/tests/archcheck/run_selftests.py"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent.parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import archcheck  # noqa: E402

RULES_FILE = TOOLS / "archcheck_rules.txt"
SRC = "bootstrap/axiom0/src"
FIXTURES = HERE / "fixtures"

# The spec chain of INV-LAYER-001, written out independently of the rules file.
CHAIN = [["kernel"], ["source"], ["diag"], ["lex"], ["syntax"], ["resolve"], ["hir"], ["types"], ["traits"],
         ["own"], ["mir"], ["verify"], ["interp", "opt"], ["lir"], ["abi"], ["target/x64"], ["obj"], ["link"],
         ["driver"]]
RANK = {m: i for i, grp in enumerate(CHAIN) for m in grp}


def load_rules():
    return archcheck.parse_rules(archcheck.read_text(str(RULES_FILE)))


def make_tree(root, files):
    for rel, content in files.items():
        p = Path(root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content.encode("utf-8"))


def run_tree(files, extra_args=()):
    """Create a tree, run the checker in-process; returns [(path, line, inv, msg)]."""
    with tempfile.TemporaryDirectory() as tmp:
        make_tree(tmp, files)
        violations, _ = archcheck.run_checks(load_rules(), tmp)
        return [(v.path, v.line, v.inv, v.msg) for v in violations]


def src(rel):
    return SRC + "/" + rel


def cli(*args):
    p = subprocess.run([sys.executable, str(TOOLS / "archcheck.py")] + list(args),
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class FixtureTests(unittest.TestCase):
    def test_good_fixture_is_clean(self):
        rc, out, err = cli("--root", str(FIXTURES / "good"))
        self.assertEqual((rc, err), (0, ""), out)
        self.assertIn("0 violations", out)

    def test_bad_fixture_reports_exactly_the_expected_violations(self):
        expected = sorted(
            tuple(line.split()) for line in (FIXTURES / "bad" / "expected.txt").read_text(encoding="utf-8").split("\n")
            if line.strip() and not line.startswith("#"))
        rules = load_rules()
        violations, _ = archcheck.run_checks(rules, str(FIXTURES / "bad"))
        got = sorted(("%s:%d" % (v.path, v.line), v.inv) for v in violations)
        self.assertEqual(got, expected)

    def test_bad_fixture_exercises_every_invariant(self):
        violations, _ = archcheck.run_checks(load_rules(), str(FIXTURES / "bad"))
        self.assertEqual({v.inv for v in violations}, {"INV-LAYER-00%d" % i for i in range(1, 9)})

    def test_bad_fixture_exit_code_and_format(self):
        rc, out, _ = cli("--root", str(FIXTURES / "bad"))
        self.assertEqual(rc, 1)
        self.assertIn("bootstrap/axiom0/src/lir/lir.h:1: layer lir must not include syntax", out)
        self.assertIn("[INV-LAYER-005]", out)
        self.assertTrue(out.rstrip().endswith("violations"))

    def test_json_output(self):
        rc, out, _ = cli("--root", str(FIXTURES / "bad"), "--json")
        data = json.loads(out)
        self.assertEqual(rc, 1)
        expected = [l for l in (FIXTURES / "bad" / "expected.txt").read_text(encoding="utf-8").split("\n")
                    if l.strip() and not l.startswith("#")]
        self.assertEqual(len(data["violations"]), len(expected))
        self.assertEqual(set(data["violations"][0]), {"file", "line", "inv", "message"})

    def test_deterministic_output(self):
        a = cli("--root", str(FIXTURES / "bad"))
        b = cli("--root", str(FIXTURES / "bad"))
        self.assertEqual(a, b)


class LayerMatrixTests(unittest.TestCase):
    def expected_inv(self, a, b):
        """Independent oracle for the include a -> b (None when allowed).

        Precedence as documented in the rules file: deny rules, then only, then users, then order.
        """
        if a == b:
            return None
        # deny rules
        if a in ("lir", "abi", "target/x64", "objmodel", "obj", "link") and b in ("lex", "syntax", "resolve", "hir"):
            return "INV-LAYER-005"
        if a == "interp" and b in ("target/x64", "lir", "abi", "obj", "link"):
            return "INV-LAYER-003"
        if a == "opt" and b == "syntax":
            return "INV-LAYER-003"
        if a == "types" and b == "interp":
            return "INV-LAYER-004"
        # only rules
        if a == "kernel":
            return "INV-LAYER-001"
        if a == "objmodel":
            return None if b == "kernel" else "INV-LAYER-001"
        if a == "obj" and b not in ("objmodel", "kernel", "diag"):
            return "INV-LAYER-002"
        if a == "link" and b not in ("objmodel", "kernel", "diag", "obj"):
            return "INV-LAYER-002"
        # users rule: objmodel is a low layer outside the chain
        if b == "objmodel":
            return None if a in ("target/x64", "obj", "link", "driver") else "INV-LAYER-001"
        return None if RANK[b] < RANK[a] else "INV-LAYER-001"

    def test_every_pair_of_layers(self):
        layers = sorted(RANK) + ["objmodel"]
        files = {}
        for a in layers:
            for b in layers:
                if a != b:
                    files[src("%s/from_%s.c" % (a, b.replace("/", "_")))] = '#include "%s/h.h"\n' % b
        for b in layers:
            files[src("%s/h.h" % b)] = "/* header */\n"
        got = {(p, inv) for p, _l, inv, _m in run_tree(files)}
        want = set()
        for a in layers:
            for b in layers:
                if a == b:
                    continue
                inv = self.expected_inv(a, b)
                if inv:
                    want.add((src("%s/from_%s.c" % (a, b.replace("/", "_"))), inv))
        self.assertEqual(got, want)

    def test_include_resolution_forms(self):
        files = {
            src("lex/a.c"): '#include "../syntax/ast.h"\n',                  # relative, goes up a layer
            src("lex/b.c"): '#include "lex.h"\n#include "./lex.h"\n',        # same directory
            src("lex/lex.h"): "/* x */\n",
            src("syntax/ast.h"): "/* x */\n",
            src("lex/c.c"): '#include <syntax/ast.h>\n#include "generated/x.h"\n#include "/* no */"\n',
            src("lex/d.c"): '/* #include "syntax/ast.h" */\n// #include "syntax/ast.h"\n',
            src("lex/e.c"): '#  include   "syntax/ast.h"\n',
            src("lex/f.c"): '#include "target/x64/missing.h"\n',             # missing file: path decides
        }
        got = sorted((p, l, inv) for p, l, inv, _m in run_tree(files))
        self.assertEqual(got, [(src("lex/a.c"), 1, "INV-LAYER-001"), (src("lex/e.c"), 1, "INV-LAYER-001"),
                               (src("lex/f.c"), 1, "INV-LAYER-001")])

    def test_crlf_sources(self):
        files = {src("lex/a.c"): '#include "kernel/k.h"\r\n#include "syntax/ast.h"\r\n',
                 src("syntax/ast.h"): "\r\n", src("kernel/k.h"): "\r\n"}
        self.assertEqual([(l, i) for _p, l, i, _m in run_tree(files)], [(2, "INV-LAYER-001")])

    def test_unknown_layer_and_root_files(self):
        files = {src("newmod/x.c"): "/* x */\n", src("stray.h"): "/* x */\n"}
        got = run_tree(files)
        self.assertEqual(sorted((p, i) for p, _l, i, _m in got),
                         [(src("newmod/x.c"), "INV-LAYER-001"), (src("stray.h"), "INV-LAYER-001")])

    def test_non_c_files_ignored(self):
        files = {src("lex/README.md"): '#include "syntax/ast.h"\n', src("lex/notes.txt"): "printf(\n"}
        self.assertEqual(run_tree(files), [])

    def test_tests_dir_not_scanned(self):
        files = {"bootstrap/axiom0/tests/unit/t.c": '#include "driver/driver.h"\nint x;\n'}
        files[src("kernel/k.h")] = "/* x */\n"
        self.assertEqual(run_tree(files), [])


def flagged(code, name="x.c", layer="verify"):
    files = {src("%s/%s" % (layer, name)): code}
    return [(v[1], v[3].split("'")[1]) for v in run_tree(files) if v[2] == "INV-LAYER-006" and "mutable" in v[3]]


class GlobalsTests(unittest.TestCase):
    def test_mutable_file_scope_variables(self):
        for code, names in [
            ("int a;\n", ["a"]),
            ("static int a = 1;\n", ["a"]),
            ("static int a[4];\n", ["a"]),
            ("static const char *p = \"x\";\n", ["p"]),
            ("static const char *names[] = { \"a\" };\n", ["names"]),
            ("struct S { int f; } s;\n", ["s"]),
            ("struct S *p;\n", ["p"]),
            ("static struct S s = { 1, 2 };\n", ["s"]),
            ("int a, b;\n", ["a", "b"]),
            ("const int a = 1, *b;\n", ["b"]),
            ("static void (*hook)(int);\n", ["hook"]),
            ("static _Thread_local int t;\n", ["t"]),
            ("static volatile int v;\n", ["v"]),
            ("static unsigned long long counter = 0;\n", ["counter"]),
            ("int x = f(1) + g(2);\n", ["x"]),
            ("int main(void) { return 0; }\nint after_function;\n", ["after_function"]),
            ("void f(void) AX_ATTR { }\nint after_attr_function;\n", ["after_attr_function"]),
            ("int f(int a) { if (a) { return 1; } return 0; }\nint y;\n", ["y"]),
        ]:
            with self.subTest(code=code):
                self.assertEqual([n for _l, n in flagged(code)], names)

    def test_const_and_non_variables_are_clean(self):
        for code in [
            "static const int a = 1;\n",
            "const int a[] = { 1, 2 };\n",
            "static const char *const names[] = { \"a\" };\n",
            "static const char text[] = \"abc\";\n",
            "int *const p = 0;\n",
            "static void (*const hook)(int) = 0;\n",
            "const struct S s = { 1 };\n",
            "static const struct S *const t[] = { 0 };\n",
            "const int a = 1, b = 2;\n",
            "typedef int T;\n",
            "typedef struct { int x; } S;\n",
            "typedef void (*Fn)(int);\n",
            "struct S { int a; };\n",
            "struct S;\n",
            "union U { int a; float b; };\n",
            "enum E { A, B = 5 };\n",
            "enum { A, B };\n",
            "extern int declared;\n",
            "extern struct S s;\n",
            "int proto(int a, const char *b);\n",
            "static int proto2(void);\n",
            "int f(int a[sizeof(int)]);\n",
            "_Static_assert(sizeof(int) == 4, \"int\");\n",
            "static inline int f(void) { return 1; }\n",
            "struct S *make(void) { return 0; }\n",
            "AX_DECLARE_THING(foo);\n",
            "static int f(void) { static const int k = 1; return k; }\n",
            "static int f(void) { int local = 0; return local; }\n",
            "/* int commented; */\n// int commented2;\n",
            "#define MACRO int not_a_var;\n",
            "#define LONG_MACRO(a) \\\n    int not_a_var2;\n",
            "static const char *const s = \"int fake;\";\n",
        ]:
            with self.subTest(code=code):
                self.assertEqual(flagged(code), [])

    def test_function_local_static(self):
        code = ("int f(void) {\n    static int n = 0;\n    static const int k = 1;\n"
                "    if (n) {\n        static char buf[8];\n    }\n    return n + k;\n}\n")
        self.assertEqual(flagged(code), [(2, "n"), (5, "buf")])

    def test_line_numbers(self):
        code = "/* c\n   c */\nstatic const int ok = 1;\n\nint bad;\n"
        self.assertEqual(flagged(code), [(5, "bad")])

    def test_driver_may_hold_mutable_globals(self):
        self.assertEqual(flagged("static int g;\n", layer="driver"), [])
        self.assertEqual(flagged("static int g;\nint f(void) { static int n; return n; }\n", layer="driver"), [])

    def test_headers_are_checked_too(self):
        self.assertEqual(flagged("static int shared;\n", name="x.h"), [(1, "shared")])


def output_hits(code, rel="verify/x.c"):
    return [(v[1], v[3].split("(")[0].split()[-1]) for v in run_tree({src(rel): code})
            if v[2] == "INV-LAYER-006" and "must not call" in v[3]]


class OutputTests(unittest.TestCase):
    def test_forbidden_calls(self):
        code = ("void f(void) {\n    printf(\"x\");\n    vprintf(a, b);\n    puts(\"x\");\n    putchar(1);\n"
                "    exit(1);\n    _Exit(1);\n    quick_exit(1);\n    abort();\n"
                "    fprintf(stderr, \"x\");\n    fputs(\"x\", stdout);\n    fwrite(a, 1, 1, stderr);\n}\n")
        self.assertEqual([n for _l, n in output_hits(code)],
                         ["printf", "vprintf", "puts", "putchar", "exit", "_Exit", "quick_exit", "abort",
                          "fprintf", "fputs", "fwrite"])

    def test_calls_that_are_not_output(self):
        code = ("void f(FILE *out) {\n    snprintf(b, 1, \"x\");\n    fprintf(out, \"x\");\n    fputs(\"x\", out);\n"
                "    ax_printf(1);\n    x->exit(1);\n    x.abort();\n    my_exit(1);\n    fflush(stdout);\n"
                "    const char *s = \"printf(1) exit(2)\";\n    /* abort(); */\n    // exit(3);\n    (void)s;\n}\n"
                "#define NOPE printf(\"x\")\n")
        self.assertEqual(output_hits(code), [])

    def test_allowed_places(self):
        code = "void f(void) { printf(\"x\"); exit(1); abort(); }\n"
        for rel in ["driver/main.c", "driver/cmd_x.c", "diag/render_human.c", "diag/render_json.c", "diag/ice.c",
                    "diag/ice_report.c"]:
            with self.subTest(rel=rel):
                self.assertEqual(output_hits(code, rel), [])
        for rel in ["diag/diag.c", "diag/codes_registry.c", "kernel/x.c", "source/x.c"]:
            with self.subTest(rel=rel):
                self.assertEqual(len(output_hits(code, rel)), 3)

    def test_pragma_with_reason_allows_same_or_previous_line(self):
        code = ("void f(void) {\n    abort(); /* archcheck:allow(INV-LAYER-006): AX_ICE terminates */\n"
                "    // archcheck:allow(INV-LAYER-006): second case\n    abort();\n    abort();\n}\n")
        self.assertEqual(output_hits(code), [(5, "abort")])

    def test_pragma_without_reason_or_for_other_rule_is_a_violation(self):
        got = run_tree({src("verify/x.c"): "void f(void) {\n    abort(); /* archcheck:allow(INV-LAYER-006) */\n"
                                           "    int x; /* archcheck:allow(INV-LAYER-001): no */\n}\n"})
        invs = sorted((l, i) for _p, l, i, _m in got)
        self.assertEqual(invs, [(2, "INV-LAYER-006"), (2, "INV-LAYER-006"), (3, "INV-LAYER-001")])


class CodesTests(unittest.TestCase):
    def codes(self, files):
        return sorted((p.split("src/")[1], l) for p, l, i, _m in run_tree({src(k): v for k, v in files.items()})
                      if i == "INV-LAYER-007")

    def test_correct_registration_is_clean(self):
        self.assertEqual(self.codes({"diag/codes/LEX.def": 'AX_DIAG(AX_LEX_A, ERROR, "a")\nAX_DIAG(AX_LEX_B_C, WARNING, "b")\n',
                                     "diag/codes/ICE.def": 'AX_DIAG(AX_ICE_X, ERROR, "x")\n',
                                     "diag/codes.def": '#include "diag/codes/LEX.def"\n'}), [])

    def test_wrong_area_file(self):
        self.assertEqual(self.codes({"diag/codes/NAME.def": 'AX_DIAG(AX_TYPE_X, ERROR, "x")\n'}),
                         [("diag/codes/NAME.def", 1)])

    def test_all_eighteen_areas_accepted_in_their_file(self):
        files = {"diag/codes/%s.def" % a: 'AX_DIAG(AX_%s_CODE, ERROR, "x")\n' % a for a in load_rules().areas}
        self.assertEqual(len(files), 18)
        self.assertEqual(self.codes(files), [])

    def test_registered_outside_codes_dir(self):
        files = {"lex/lex.c": 'AX_DIAG(AX_LEX_A, ERROR, "a")\n', "diag/codes.def": 'AX_DIAG(AX_LEX_B, ERROR, "b")\n',
                 "diag/extra.def": 'AX_DIAG(AX_LEX_C, ERROR, "c")\n', "diag/codes/sub/LEX.def": 'AX_DIAG(AX_LEX_D, ERROR, "d")\n'}
        self.assertEqual(self.codes(files), [("diag/codes.def", 1), ("diag/codes/sub/LEX.def", 1),
                                             ("diag/extra.def", 1), ("lex/lex.c", 1)])

    def test_duplicates_across_files_and_unknown_area(self):
        files = {"diag/codes/LEX.def": 'AX_DIAG(AX_LEX_A, ERROR, "a")\nAX_DIAG(AX_LEX_A, ERROR, "a")\n',
                 "diag/codes/PARSE.def": 'AX_DIAG(AX_ZZ_A, ERROR, "a")\n'}
        self.assertEqual(self.codes(files), [("diag/codes/LEX.def", 2), ("diag/codes/PARSE.def", 1)])

    def test_non_area_file_name(self):
        self.assertEqual(self.codes({"diag/codes/lex.def": "", "diag/codes/README.txt": ""}),
                         [("diag/codes/lex.def", 1)])

    def test_using_a_code_is_not_registering_it(self):
        files = {"lex/lex.c": 'void f(void) { diag_emit(s, AX_LEX_A, sp); AX_ICE(AX_ICE_X); }\n'}
        self.assertEqual(self.codes(files), [])

    def test_comments_do_not_register(self):
        self.assertEqual(self.codes({"lex/lex.c": '/* AX_DIAG(AX_LEX_A, ERROR, "a") */\n',
                                     "diag/codes/NAME.def": '// AX_DIAG(AX_TYPE_X, ERROR, "x")\n'}), [])

    def test_multiline_entry_reports_code_line(self):
        self.assertEqual(self.codes({"diag/codes/NAME.def": 'AX_DIAG(\n    AX_TYPE_X,\n    ERROR, "x")\n'}),
                         [("diag/codes/NAME.def", 2)])
        self.assertEqual(self.codes({"diag/codes/TYPE.def": 'AX_DIAG(\n    AX_TYPE_X,\n    ERROR, "x")\n'}), [])
        self.assertEqual(self.codes({"diag/codes/NAME.def": 'AX_DIAG(AX_TYPE_X,\n    ERROR, "x")\n'}),
                         [("diag/codes/NAME.def", 1)])


class StdTests(unittest.TestCase):
    def std(self, files):
        files = dict(files)
        files.setdefault(src("kernel/k.h"), "")  # a missing src-root is a usage error (exit 2)
        return sorted((p, i) for p, _l, i, _m in run_tree(files) if i == "INV-LAYER-008")

    def test_c_sources_forbidden(self):
        files = {"std/a.c": "", "std/core/b.h": "", "std/core/deep/c.cpp": "", "std/d.S": "", "std/e.asm": "",
                 "std/f.CC": ""}
        self.assertEqual([p for p, _ in self.std(files)],
                         ["std/a.c", "std/core/b.h", "std/core/deep/c.cpp", "std/d.S", "std/e.asm", "std/f.CC"])

    def test_axiom_sources_and_data_allowed(self):
        files = {"std/core/a.ax": "", "std/axiom.toml": "", "std/data/table.bin": "", "std/README.md": "",
                 "std/core/test.c.ax": ""}
        self.assertEqual(self.std(files), [])

    def test_missing_std_dir_is_fine(self):
        self.assertEqual(self.std({src("kernel/k.h"): ""}), [])

    def test_c_outside_std_not_flagged(self):
        self.assertEqual(self.std({"tools/x.c": "", "other/std/y.c": ""}), [])


class RulesFileTests(unittest.TestCase):
    def test_shipped_rules_parse(self):
        r = load_rules()
        self.assertEqual(r.src_root, SRC)
        self.assertEqual(len(r.areas), 18)
        self.assertEqual([m for m in RANK if r.rank.get(m) != RANK[m]], [])

    def test_bad_rules_are_rejected(self):
        for text in ["nonsense line\n", "order a a\nsrc-root x\n", "src-root x\n", "order a\n",
                     "src-root x\norder a\ndeny INV-1 a b\n", "src-root x\norder a\nonly INV-1 a b : a\n"]:
            with self.subTest(text=text), self.assertRaises(archcheck.RulesError):
                archcheck.parse_rules(text)

    def test_cli_error_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, _o, err = cli("--root", tmp)
            self.assertEqual(rc, 2)
            self.assertIn("src-root", err)
            bad = Path(tmp) / "r.txt"
            bad.write_text("garbage\n", encoding="utf-8")
            rc, _o, err = cli("--rules", str(bad))
            self.assertEqual(rc, 2)
            rc, _o, err = cli("--rules", str(Path(tmp) / "missing.txt"))
            self.assertEqual(rc, 2)

    def test_custom_rules_change_behaviour(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_tree(tmp, {"s/a/x.c": '#include "b/y.h"\n', "s/b/y.h": ""})
            rules = Path(tmp) / "r.txt"
            rules.write_text("src-root s\norder b a\n", encoding="utf-8")
            rc, out, _ = cli("--root", tmp, "--rules", str(rules))
            self.assertEqual(rc, 0, out)
            rules.write_text("src-root s\norder a b\n", encoding="utf-8")
            rc, out, _ = cli("--root", tmp, "--rules", str(rules))
            self.assertEqual(rc, 1)
            self.assertIn("layer a must not include b", out)


class StripTests(unittest.TestCase):
    def test_strip_keeps_lines(self):
        text = 'a /* x\ny */ b // c\n"str\\"ing" \'c\' d\n'
        s = archcheck.strip_c(text, False)
        self.assertEqual(s.count("\n"), text.count("\n"))
        self.assertNotIn("x", s.replace("\n", ""))
        self.assertIn("a", s)
        self.assertIn("d", s)

    def test_line_continuation_in_line_comment(self):
        s = archcheck.strip_c("// c \\\nstill comment\nint x;\n", False)
        self.assertNotIn("still", s)
        self.assertIn("int x;", s)

    def test_unterminated_constructs_do_not_crash(self):
        for text in ['/* never closed', '"never closed', "'", 'a "b\nc', "// x"]:
            archcheck.strip_c(text, True)
            archcheck.strip_c(text, False)


class RealTreeTests(unittest.TestCase):
    def test_current_tree_is_clean(self):
        """The shipped axiom0 tree must pass (CI runs the same check)."""
        rc, out, _ = cli()
        self.assertEqual(rc, 0, out)


if __name__ == "__main__":
    unittest.main()
