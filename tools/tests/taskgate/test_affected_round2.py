"""T437a round 2 self-audit of the `--affected` std rule (QA F6): every changed line is attributed to the
declaration(s) containing it, from its position in the NEW file (`+` lines) and the OLD file (`-` lines); a line
that cannot be attributed is UNRESOLVED (whole group), never silently dropped. Python 3 standard library only.
"""

import difflib
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(HERE))
import axtest_affected  # noqa: E402
from test_taskgate import Fixture, run_test  # noqa: E402


def names_of(old, new):
    diff = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), "a/f.ax", "b/f.ax", n=0))
    return axtest_affected.derive_names(diff, new, old, "std/f.ax")


BASE = ("module std.demo\n"
        "use std.core.cmp\n"
        "\n"
        "pub const LIMIT: i32 = 3\n"
        "\n"
        "pub fn first() -> i32 {\n"
        "    helper() + LIMIT\n"
        "}\n"
        "\n"
        "fn helper() -> i32 {\n"
        "    let s = \"} fn fake() {\";\n"
        "    1\n"
        "}\n"
        "\n"
        "pub trait Shape<T> {\n"
        "    fn area(self) -> T;\n"
        "    fn describe(self) -> i32 {\n"
        "        7\n"
        "    }\n"
        "}\n"
        "\n"
        "pub struct Square {\n"
        "    side: i32,\n"
        "}\n"
        "\n"
        "impl Shape<i32> for Square {\n"
        "    fn area(self) -> i32 {\n"
        "        self.side * self.side\n"
        "    }\n"
        "}\n"
        "\n"
        "fn only_for_square(s: Square) -> i32 {\n"
        "    s.side\n"
        "}\n"
        "\n"
        "impl Square {\n"
        "    pub fn grow(self) -> i32 {\n"
        "        only_for_square(self)\n"
        "    }\n"
        "}\n"
        "\n"
        "@inline\n"
        "pub fn where_clause<T>(x: T) -> T\n"
        "where\n"
        "    T: Copy,\n"
        "{\n"
        "    x\n"
        "}\n"
        "\n"
        "pub macro my_assert {\n"
        "    (x) => { x }\n"
        "}\n"
        "\n"
        "pub fn last() -> i32 {\n"
        "    0\n"
        "}\n")


class DeclarationAttribution(unittest.TestCase):
    def check(self, old, new, want, not_want=(), unresolved=False):
        names, unres = names_of(old, new)
        for w in want:
            self.assertIn(w, names, (names, unres))
        for w in not_want:
            self.assertNotIn(w, names, (names, unres))
        self.assertEqual(bool(unres), unresolved, unres)
        return names, unres

    def test_hunk_at_file_start(self):
        # line 1 / the `use` line: the whole file's names, not unresolved
        self.check(BASE, BASE.replace("module std.demo\nuse std.core.cmp\n", "module std.demo\nuse std.core.ord\n"),
                   ["first", "LIMIT", "Shape", "Square", "last"])

    def test_hunk_at_file_end(self):
        self.check(BASE, BASE.replace("    0\n}\n", "    1\n}\n"), ["last"], ["first", "Shape"])
        names, _ = self.check(BASE, BASE + "\npub fn appended() {}\n", ["appended"], ["last"])

    def test_generic_trait_default_method_body(self):
        # trait + its implementer + the member name (a default body runs for every implementer)
        self.check(BASE, BASE.replace("        7\n", "        8\n"), ["Shape", "Square", "describe"], ["first"])

    def test_first_body_line_of_impl_method(self):
        self.check(BASE, BASE.replace("        self.side * self.side\n", "        self.side + self.side\n"),
                   ["Square", "Shape"], ["first", "last"])

    def test_private_helper_reaches_public_callers(self):
        names, _ = self.check(BASE, BASE.replace("    1\n}\n\npub trait", "    2\n}\n\npub trait"), ["first"],
                              ["Shape", "last"])
        # a private fn used only by an inherent impl method -> the impl's type
        self.check(BASE, BASE.replace("    s.side\n", "    s.side + 0\n"), ["Square"], ["first", "last"])

    def test_rename(self):
        self.check(BASE, BASE.replace("pub fn last()", "pub fn final_one()"), ["last", "final_one"])

    def test_deleted_function(self):
        new = BASE.replace("pub fn last() -> i32 {\n    0\n}\n", "")
        self.check(BASE, new, ["last"], ["first"])

    def test_changed_const(self):
        # the const and its in-file user
        self.check(BASE, BASE.replace("LIMIT: i32 = 3", "LIMIT: i32 = 4"), ["LIMIT", "first"], ["Shape", "last"])

    def test_macro_body(self):
        self.check(BASE, BASE.replace("(x) => { x }", "(x) => { x + 0 }"), ["my_assert"], ["first"])

    def test_where_clause_and_attribute_lines(self):
        self.check(BASE, BASE.replace("    T: Copy,\n", "    T: Copy + Clone,\n"), ["where_clause"], ["last"])
        self.check(BASE, BASE.replace("@inline\n", "@inline(always)\n"), ["where_clause"], ["last"])

    def test_braces_inside_string_do_not_confuse_the_scanner(self):
        d = axtest_affected.Decls(BASE)
        self.assertTrue(d.ok)
        self.assertEqual([it.name for it in d.items if it.parent is None and it.kind == "fn"],
                         ["first", "helper", "only_for_square", "where_clause", "last"])

    def test_comment_only_change_selects_nothing_and_is_not_unresolved(self):
        names, unres = names_of(BASE, BASE.replace("\npub fn first", "\n// a note\npub fn first"))
        self.assertEqual(unres, [])
        self.assertEqual(names, set())

    def test_top_level_statement_is_unresolved(self):
        names, unres = self.check(BASE, BASE.replace("\npub fn first", "\nlet stray = 1\npub fn first"),
                                  ["first", "Shape", "last"], unresolved=True)
        self.assertIn("outside any declaration", unres[0])

    def test_unbalanced_braces_are_unresolved(self):
        self.check(BASE, BASE.replace("pub fn last() -> i32 {\n", "pub fn last() -> i32 {{\n"), ["last", "first"],
                   unresolved=True)


class GitEndToEnd(Fixture):
    """Through `derive` with a commit range: old text from the base commit, new text from HEAD."""

    def test_deleted_function_selects_its_callers(self):
        self.write("std/core/cmp.ax", "module std.core.cmp\npub fn compare(a: i32, b: i32) -> i32 {\n    0\n}\n"
                   "pub fn gone() -> i32 {\n    1\n}\n")
        self.write("tests/run/basic/calls_gone.ax", run_test("g", "fn f() {\n    x = gone()\n}\n"))
        self.commit()
        base = self.git("rev-parse", "HEAD")
        self.write("std/core/cmp.ax", "module std.core.cmp\npub fn compare(a: i32, b: i32) -> i32 {\n    0\n}\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "delete gone")
        aff = self.derive("%s..HEAD" % base)
        self.assertIn("run/basic/calls_gone.ax", aff.ids)
        self.assertEqual(aff.unresolved, [])

    def test_file_move_selects_users_of_the_old_and_new_module(self):
        self.write("tests/run/basic/uses_moved.ax", run_test("m", "use std.core.moved\n"))
        self.write("tests/run/basic/calls_widget.ax", run_test("w", "fn f() {\n    x = widget()\n}\n"))
        self.write("std/core/old_place.ax", "module std.core.old_place\npub fn widget() -> i32 {\n    1\n}\n")
        self.write("tests/run/basic/uses_old.ax", run_test("o", "use std.core.old_place\n"))
        self.commit()
        base = self.git("rev-parse", "HEAD")
        self.git("mv", "std/core/old_place.ax", "std/core/moved.ax")
        self.write("std/core/moved.ax", "module std.core.moved\npub fn widget() -> i32 {\n    1\n}\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "move")
        aff = self.derive("%s..HEAD" % base)
        self.assertEqual(aff.changed, ["std/core/moved.ax", "std/core/old_place.ax"])
        for tid in ("run/basic/uses_old.ax", "run/basic/uses_moved.ax", "run/basic/calls_widget.ax"):
            self.assertIn(tid, aff.ids)
        self.assertEqual(aff.unresolved, [])

    def test_working_tree_change_at_first_body_line(self):
        # QA F6 shape through derive (working tree vs HEAD): git's hunk header names the previous item
        self.write("std/core/cmp.ax", "module std.core.cmp\npub fn compare(a: i32, b: i32) -> i32 {\n    0\n}\n\n"
                   "pub fn is_lock_free() -> bool {\n    let s = 8;\n    s <= 8\n}\n")
        self.write("tests/run/basic/lock_free.ax", run_test("l", "fn f() {\n    x = is_lock_free()\n}\n"))
        self.commit()
        self.write("std/core/cmp.ax", "module std.core.cmp\npub fn compare(a: i32, b: i32) -> i32 {\n    0\n}\n\n"
                   "pub fn is_lock_free() -> bool {\n    let s = 16;\n    s <= 8\n}\n")
        aff = self.derive("std/core/cmp.ax")
        self.assertIn("run/basic/lock_free.ax", aff.ids)
        self.assertNotIn("run/basic/calls_compare2.ax", aff.ids)

    def test_unresolved_line_selects_the_group_and_is_printed(self):
        self.write("tests/std/x/s.ax", run_test("s"))
        self.commit()
        self.write("std/io/io.ax", "module std.io.io\nstray_statement()\npub fn print() {}\n")
        aff = self.derive("std/io/io.ax")
        self.assertEqual(len(aff.unresolved), 1)
        self.assertIn("UNRESOLVED std/io/io.ax", "\n".join(aff.lines()))
        self.assertIn("std/x/s.ax", aff.ids)


if __name__ == "__main__":
    unittest.main()
