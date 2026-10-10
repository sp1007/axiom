# T060 — Modules & packages: multi-file, visibility, use, re-exports, prelude module

## Summary
Implemented the real module system with dotted module paths, multi-file packages with manifest discovery, visibility rules, `use` imports with aliases and re-exports, cycle detection, standard library root discovery, and implicit prelude importing per ADR-0006 §7 and §8.

Key components delivered:
1. **Manifest parsing (`manifest.c`, `manifest.h`)**:
   - Parses `axiom.toml` package manifest with `name`, `version`, and `kind` per ADR-0006 §7.
   - Diagnostic `AX_DRIVER_BAD_MANIFEST` emitted on syntax or structure errors.
2. **Package discovery and multi-file pipeline (`project.c`, `project.h`, `pipeline.c`)**:
   - Recursively scans package directories and files under `src/`.
   - Maps file paths to dotted module paths (e.g. `src/a/b.ax` -> `a.b`, `src/main.ax` -> `main`).
   - Deterministic lexicographical sorting of discovered files (`sl.items`).
   - Normalizes path separators and supports package or single-file compilations.
3. **Std root discovery and prelude mechanism (`std_root.c`, `std_root.h`, `std/core/prelude.ax`)**:
   - Implements ADR-0006 §8 search order: `--std-root <dir>`, `AXIOM_STD` env var, `<exe dir>/../std`, `<exe dir>/std`; emits `AX_DRIVER_NO_STD` if missing.
   - Loads `std.core.prelude` from `<std-root>/core/prelude.ax` and implicitly imports its public symbols into the compiler prelude scope.
   - External std items are loaded without disturbing single-file inspect emitter outputs via `filter_file`.
4. **Name resolution and visibility rules (`resolve.c`, `resolve.h`, `typeck.c`)**:
   - Lexical and hierarchical module resolution supporting dotted module paths, submodules, and package scoping.
   - Supports visibility levels: `pub`, `pub(package)`, `pub(module)`, and private.
   - Full support for `use` tree groups, aliases (`as`), and re-exports (`pub use`).
   - Cycle detection during import traversal emitting `AX_NAME_IMPORT_CYCLE`.
   - Separate symbol ID allocation for user items vs std items to preserve symbol ID stability.
   - Pass 1 split in `typeck.c` (Pass 1a: structs/enums, Pass 1b: fn signatures) enabling cross-module type references and accurate struct field privacy checking.
5. **Determinism and hygiene**:
   - Display paths in diagnostics and artifacts are package-relative or relative to project root, with no absolute filesystem paths leaked.

## Verification
- Built compiler snapshot `build-snap-T060` with zero warnings and zero errors (`-Wall -Wextra -Wpedantic -Werror`).
- `axiom0-unit.exe`: 69 tests pass, 0 failed.
- `axtest.py` on `modules`: 18 PASS, 0 FAIL.
- Full compiler test suite: 813 PASS, 0 FAIL across all modes (interp, native, native-O1, ui).

## Files changed
- bootstrap/axiom0/src/diag/codes/DRIVER.def
- bootstrap/axiom0/src/diag/codes/NAME.def
- bootstrap/axiom0/src/driver/driver.h
- bootstrap/axiom0/src/driver/emit_ast.c
- bootstrap/axiom0/src/driver/emit_hir.c
- bootstrap/axiom0/src/driver/emit_lir.c
- bootstrap/axiom0/src/driver/emit_mc.c
- bootstrap/axiom0/src/driver/emit_mi.c
- bootstrap/axiom0/src/driver/emit_mir.c
- bootstrap/axiom0/src/driver/emit_resolved.c
- bootstrap/axiom0/src/driver/emit_thir.c
- bootstrap/axiom0/src/driver/manifest.c
- bootstrap/axiom0/src/driver/manifest.h
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/driver/project.c
- bootstrap/axiom0/src/driver/project.h
- bootstrap/axiom0/src/driver/std_root.c
- bootstrap/axiom0/src/driver/std_root.h
- bootstrap/axiom0/src/hir/hir.h
- bootstrap/axiom0/src/hir/lower.c
- bootstrap/axiom0/src/resolve/resolve.c
- bootstrap/axiom0/src/resolve/resolve.h
- bootstrap/axiom0/src/source/source.c
- bootstrap/axiom0/src/source/source.h
- bootstrap/axiom0/src/types/typeck.c
- std/README.md
- std/core/prelude.ax
- tests/modules/hello/axiom.toml
- tests/modules/hello/src/main.ax
- tests/modules/hello/src/math.ax
- tests/modules/mutual/axiom.toml
- tests/modules/mutual/src/a.ax
- tests/modules/mutual/src/b.ax
- tests/modules/mutual/src/main.ax
- tests/modules/prelude_implicit/axiom.toml
- tests/modules/prelude_implicit/src/main.ax
- tests/modules/reexport/axiom.toml
- tests/modules/reexport/src/facade.ax
- tests/modules/reexport/src/internal.ax
- tests/modules/reexport/src/main.ax
- tests/modules/repro_oracle.py
- tests/modules/reproducibility.test
- tests/modules/std_root.test
- tests/modules/std_root_oracle.py
- tests/ui/modules/import_cycle.ax
- tests/ui/modules/private_field.ax
- tests/ui/modules/private_fn.ax
- tests/ui/modules/unresolved_import.ax

STATUS: COMPLETE round=0
