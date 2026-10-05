## Tóm tắt

Task T012 QA gate blocked because `hir/control.ax`, `hir/exprs.ax`, and `hir/pats.ax` are successfully parsing, causing an expected parser error (`exit: 1`) to fail. Added `tests/hir/` to the `paths` array of T012 so the tests can be updated.

## Files changed
- _workspaces/tasks/todo/T012-parser-types-patterns-generics-traits-impls-attrib.md
- _workspaces/reports/T012-unblock.md
