---
name: axiom-c-stage0
description: Engineering conventions for the Stage-0 Axiom compiler "axiom0" written in C11 — repository layout, layer/dependency rules, typed IDs, arenas, interners, diagnostics-as-data, determinism, host-semantics independence, build (CMake+Ninja, gcc/clang on Windows/MSYS2) and the definition of done. Use for ANY code change under bootstrap/axiom0, tools/, or when adding a compiler module, fixing a compiler bug, or reviewing compiler C code.
---

# axiom0 (Stage-0, C11) engineering conventions

axiom0 is not a throw-away toy: it is the first implementation of the final architecture and is
later ported module-by-module to Axiom (self-hosting). Anything that would be awkward to port —
hidden globals, pointer-identity semantics, host-library behaviour leaking into Axiom semantics —
is a defect even if tests pass. (docs 0152 §5, 0172, tasks/0260 ABOOT-41..57)

## Repository layout

```
bootstrap/axiom0/
  CMakeLists.txt          globs src/**/*.c → build/axiom0(.exe); never list files by hand
  src/
    kernel/    typed ids, arena, vec, hashmap, str/strview, interner, hash, utf8
    source/    SourceDatabase, FileId, Span, LineMap
    diag/      Diagnostic model, code registry (codes.def), human/json renderers
    lex/       tokens, lexer
    syntax/    AST, parser, AST dumper
    resolve/   scope graph, name resolution, module graph
    hir/       HIR data model, AST→HIR lowering, HIR dumper
    types/     type interner, typeck, inference, layout queries
    traits/    trait solver, impl tables, monomorphization requests
    own/       places, init/move analysis, capability/region analysis
    mir/       MIR data model, builder (THIR/HIR→MIR), drop elaboration, printer
    verify/    MIR verifier
    interp/    MIR interpreter (semantic oracle)
    opt/       MIR optimizations (only on verified MIR)
    lir/       LIR + MIR→LIR lowering
    abi/       target ABI descriptions (win64, sysv64) and ABI lowering
    target/x64 machine IR, isel, regalloc, frame lowering, encoder
    objmodel/  target-neutral sections/symbols/relocations
    obj/       COFF writer, ELF writer (+ readers for the linker)
    link/      PE32+ linker, ELF linker, startup stubs
    driver/    CLI (`axiom0 check|build|run|test|inspect`), pipeline orchestration
tests/        lex/ parse/ ui/ run/ mir/ interp/ diff/ encode/ obj/ link/ fuzz/ conformance/
tools/        axtest.py (test runner), archcheck.py (layer checker), helpers
std/          Axiom-source libraries: core/, std/ (written in Axiom)
spec/         canonical specs + decisions/ (architect)
```

## Layer rules (enforced by tools/archcheck.py once T006 lands)

A module may include headers only from its own layer or **lower** layers:

```
kernel < source < diag < lex < syntax < resolve < hir < types < traits < own < mir < verify
       < interp, opt < lir < abi < target/x64 < objmodel < obj < link < driver
```

Exceptions: `objmodel` depends only on `kernel`; `obj`/`link` depend on `objmodel`+`kernel`+`diag`
(never on MIR/HIR — "linker → parser" is an architecture violation, doc 0263 §46). `interp` must not
depend on `target`, `opt` must not depend on `syntax`. Why: this is what lets the backend, the
oracle and the frontend evolve and be ported independently.

## Coding rules

- **C11**, compiled warning-clean with `-std=c11 -Wall -Wextra -Wpedantic -Werror` under both gcc
  and clang. No compiler extensions in portable code (wrap the few needed builtins in `kernel/`).
- **Typed IDs**: `typedef struct { uint32_t v; } FileId;` etc. One struct per ID kind so the C
  type checker rejects `get_module(file_id)`. Index 0 = invalid/none. Tables are
  `IdTable`-style arrays accessed through `xxx_get(ctx, id)`, never raw indexing (AKERNEL-24).
- **Arenas** own phase data (AST arena, HIR arena, MIR arena per function…). Free whole arenas at
  phase boundaries; no per-node `free`. No GC, no refcounting.
- **No mutable globals** outside `driver/`. Everything flows through explicit context structs
  (`SourceDb*`, `DiagSink*`, `TypeCtx*`…). Keeps the code portable to Axiom and testable.
- **Interning**: identifiers → `StrId`, types → `TypeId` (hash-consed; equality = id equality).
  `StrId` is not a `SymbolId`.
- **Spans** are `FileId + byte start/end`. Line/column only in renderers.
- **Diagnostics are data**: every user-facing error has a stable code registered once in
  `diag/codes.def` (`AX_LEX_*`, `AX_PARSE_*`, `AX_NAME_*`, `AX_TYPE_*`, `AX_MOVE_*`, `AX_CAP_*`,
  `AX_DROP_*`, `AX_VERIFY_*`, `AX_LINK_*`…), a primary span, optional labels/notes/fix-its. Library
  code never prints or calls `exit()`; only the driver renders (human / `--json`).
- **Never crash on user input.** Malformed source must yield diagnostics (fuzzed). Internal
  invariant failures use `AX_ICE(...)` which reports an internal-compiler-error diagnostic with
  location, then aborts — never silent UB.
- **Determinism**: output (diagnostic order, symbol order, object bytes) must not depend on hash
  iteration order, pointer values, time, or environment. Sort where order is observable. Two runs
  on the same input produce byte-identical artifacts (needed for reproducible bootstrap).
- **Semantic independence from C**: Axiom integer overflow, division by zero, shifts, float
  behaviour are implemented explicitly per spec (use unsigned arithmetic / checked helpers), never
  by inheriting C UB. Axiom `Vec`/ownership semantics come from the spec, not from what C does.
- **No dangerous shortcuts** (doc 0263 §28): no AST→machine code, no textual assembly, no skipping
  MIR/verifier. Safe shortcuts (fixed registers before regalloc exists) are fine and must be marked
  `/* BOOTSTRAP-SHORTCUT: … */` so they can be found later.
- Headers: one public header per module (`lex/lex.h`), include guards `AX_LEX_LEX_H`. Names are
  module-prefixed (`lex_next`, `mir_build_fn`). Keep functions short; comment the *why* and cite
  spec numbers for semantic rules (`/* 0160 §12: partial move of field */`).

## Build & run

```bash
cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc -DCMAKE_BUILD_TYPE=Debug
cmake --build build                         # → build/axiom0.exe
python tools/axtest.py                      # all tests; --filter lex, --json for machine output
python tools/archcheck.py                   # layer rules
build/axiom0.exe inspect --emit=tokens|ast|hir|thir|mir|lir|mc file.ax
build/axiom0.exe run --interp file.ax       # oracle
build/axiom0.exe build file.ax -o out.exe   # native
```

When the orchestrator runs tasks in parallel, use a private build dir (`-B build-<TASKID>`) and
pass `--compiler build-<TASKID>/axiom0.exe` to the runner; `build*/` is git-ignored.
Also build with `-DCMAKE_C_COMPILER=clang` before declaring done when you touched portable code;
enable `-fsanitize=address,undefined` builds via clang in WSL for fuzz/QA runs when available.

## Definition of done (every task)

1. Code compiles warning-free (gcc; clang for portable changes).
2. New behaviour has tests in `tests/` (positive + negative), and the whole suite passes — not
   just the new tests.
3. archcheck passes; no new `BOOTSTRAP-SHORTCUT` without a follow-up task.
4. Any semantic choice not dictated by `spec/` is an ADR (via axiom-architect), not a silent pick.
5. Report written to `_workspaces/reports/<ID>-report.md` (format in axiom-tasks).
