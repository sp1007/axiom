# T006 report

## Summary
`tools/archcheck.py` (Python 3 stdlib only) enforces INV-LAYER-001..008 of `spec/invariants.md`
(axiom-c-stage0 layer rules, ADR-0004 §8, ADR-0005 §2, ROADMAP R8) on `bootstrap/axiom0/src/**`
and `std/`. The rules are data in `tools/archcheck_rules.txt` (ordered layers, `deny`/`only`/`users`
exceptions, diagnostic areas, output functions and their allowed files).

- Layers: `#include "..."` in `.c/.h/.def/.inc` files is resolved (src-root relative, then
  file-relative; a missing file is decided by its path) and mapped to the layer = longest layer
  directory prefix. Rule precedence: `deny` → `only` → `users` → order. Peers of one rank
  (`interp|opt`) may not include each other. `objmodel` is outside the chain: includes only
  `kernel`, included only by `target/x64`, `obj`, `link`, `driver`. A file in an unknown layer
  directory is itself a violation (new modules must be added to the rules file).
- Output format: `file:line: layer X must not include Y (#include "...": reason) [INV-LAYER-nnn]`,
  summary line `archcheck: N files scanned, M violations`; `--json` for machines; exit 0 clean,
  1 violations, 2 usage/rules error (also when src-root does not exist — protects against a wrong
  `--root` silently passing).
- INV-LAYER-006: heuristic mutable-global detector (file-scope and function-local `static`
  non-const variables; pointers are const only as `* const`) outside `driver/`; forbidden calls
  `printf vprintf puts putchar exit _Exit _exit quick_exit abort` and stream functions
  (`fprintf vfprintf fputs fputc putc fwrite`) when `stdout`/`stderr` is any argument (the stream is
  last for fputs/fwrite/putc — fixed in this round; the earlier attempt only looked at the first
  argument). Allowed in `driver/*`, `diag/*render*`, `diag/*ice*`. Escape hatch: a comment
  `archcheck:allow(INV-LAYER-006): <reason>` on the line or the line above; a pragma without reason
  or for another rule is itself a violation.
- INV-LAYER-007: `AX_DIAG(AX_<AREA>_...)` entries only in `diag/codes/<AREA>.def`, AREA one of the
  18 areas, no duplicates, no other files in `diag/codes/`, no registrations in any other `.def` or
  via `AX_DIAG(` in C files. Using a code is not registering it.
- INV-LAYER-008: no C/C++/assembly source files under `std/`.
- Comments, string contents and preprocessor lines are blanked (line structure kept) before the
  call/global heuristics run; CRLF input is handled.

CI: T004's `tools/ci.sh` / `tools/ci.ps1` already call `tools/archcheck.py` when it exists; no CI
script was edited.

### Design decisions (for the architect / ADR)
1. Rule precedence deny → only → users → order, so the most specific invariant id is reported
   (e.g. `objmodel` → `lex` is INV-LAYER-005, not 001).
2. `driver` may include `objmodel` (it wires the pipeline); `link` may include `obj` (the object
   readers used by the linker live in `obj`, axiom-c-stage0 layout).
3. `interp` and `opt` are peers: neither includes the other.
4. Unknown top-level directory under `src/` = violation (forces the rules file to be updated with
   a new module instead of silently not checking it).
5. Missing src-root = exit 2 (usage error), not "clean".
6. `diag/codes.def` may only `#include` the area files; any `AX_DIAG(...)` entry in it is a
   violation (ADR-0005 §2: nothing registered outside `diag/codes/`).
7. Mutable-global detection is a heuristic; `archcheck:allow` is honoured only for INV-LAYER-006
   and only with a reason, so layer/registry rules can never be waived inline.

## Files changed
- tools/archcheck.py
- tools/archcheck_rules.txt
- tools/tests/archcheck/run_selftests.py
- tools/tests/archcheck/test_archcheck.py
- tools/tests/archcheck/fixtures/bad/expected.txt
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/diag/codes/FOO.def
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/diag/codes/LEX.def
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/diag/codes/NAME.def
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/diag/diag.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/hir/hir.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/interp/interp.c
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/interp/interp.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/kernel/k.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/kernel/k2.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/lex/codes_here.c
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/lex/lex.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/link/link.c
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/lir/lir.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/lir/lir2.c
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/mir/mir.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/obj/obj.c
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/objmodel/om.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/opt/opt.c
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/syntax/ast.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/target/x64/enc.h
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/types/types.c
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/verify/ver.c
- tools/tests/archcheck/fixtures/bad/bootstrap/axiom0/src/zzz/z.c
- tools/tests/archcheck/fixtures/bad/std/core/ok.ax
- tools/tests/archcheck/fixtures/bad/std/x.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/diag/codes.def
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/diag/codes/ICE.def
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/diag/codes/LEX.def
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/diag/diag.h
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/diag/ice.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/diag/render_human.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/driver/main.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/interp/interp.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/kernel/k.h
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/kernel/k2.h
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/lex/lex.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/link/link.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/lir/lir.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/lir/lir.h
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/mir/mir.h
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/obj/obj.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/obj/obj.h
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/objmodel/om.h
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/opt/opt.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/opt/opt.h
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/target/x64/enc.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/verify/ver.c
- tools/tests/archcheck/fixtures/good/bootstrap/axiom0/src/verify/ver.h
- tools/tests/archcheck/fixtures/good/std/axiom.toml
- tools/tests/archcheck/fixtures/good/std/core/ok.ax

## Tests
All run inside `build-snap-T006/` (HEAD 03f8604 + this task's changes):
- `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc` + `cmake --build build --clean-first`:
  OK, 0 warnings (no C source touched by this task, so no clang run).
- `ctest --test-dir build`: 100% tests passed, 0 failed out of 1.
- `python tools/tests/archcheck/run_selftests.py`: `SELFTEST 44 tests, 0 failures, 0 errors`
  (fixtures: good tree clean; bad tree reports exactly the 34 violations in `expected.txt`, covering
  every INV-LAYER-001..008; full 20x20 layer-pair matrix against an independent oracle; include
  forms; CRLF; globals/output/pragma/codes/std heuristics; rules-file errors; exit codes; JSON;
  determinism; the real tree is clean).
- `python tools/archcheck.py`: `archcheck: 7 files scanned, 0 violations`, exit 0.
- `AX_CI_COMPILERS=gcc tools/ci.ps1`: runs `== archcheck.py` → 0 violations, `ci: OK (gcc)`.
  (`bash tools/ci.sh` could not run here: the `bash` on PATH is WSL without cmake — environment, the
  script's archcheck hook is identical.)
- `tools/axtest.py` is not in HEAD yet (T005 in progress), so the runner suite is not part of this
  snapshot; `ci` skips it.

Fixes in this round over the interrupted attempt: stream-last output functions were missed
(checker fix + fixture lines ver.c:42/43); test oracle crashed on `objmodel` and did not follow the
rule precedence; std tests built trees without a src-root; a multi-line wrong-area test expected no
violation; JSON count now derived from `expected.txt`.

## Spec deviations
none

## Follow-ups
- None required. Note for the architect: decisions 1–7 above may be recorded in an ADR; adding a new
  module directory under `bootstrap/axiom0/src` requires a line in `tools/archcheck_rules.txt`
  (owned by QA; T006 lock).

STATUS: COMPLETE round=0
