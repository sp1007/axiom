# T018 Report

## Task details
- Phase: IMPLEMENTATION
- Task: T018: MIR data model, printer and text parser

## Changes made
- Defined MIR data structures in `mir.h` matching the required day-one ownership semantics.
- Implemented C text printer for MIR in `print.c`.
- Implemented C-only text parser in `parse.c` capable of round-tripping output from the printer.
- Wired `--emit=mir` in `driver/emit_mir.c` and registered `axemit_mir` so it can be used for tests.
- Fixed `TypeInterner` pointer usage, `ax_arena_alloc` macros, and unused variables.
- Fixed an edge-case in MIR parser where `_` was prematurely consumed.
- Added test fixtures in `tests/mir/basic.mir` and `tests/mir/complex.mir`, and their respective `axtest.py` manifest files to ensure round-tripping works byte-for-byte.

## Round 1
- Fixed layer violation in `mir.h` by removing `#include "driver/driver.h"`.
- Fixed layer violation in `print.c` by using `FILE*` instead of `AxIo*`.
- Updated `emit_mir.c` to use `io->out` for printing.
- Fixed layer violation in `parse.c` by removing `fprintf` and `exit` with `AX_ICE`.
- Completed parsing logic in `parse.c` for `switchInt`, `call`, `assert`, unary ops, binary ops, and `deref` projections.
- Fixed printer bug where commas were missing before `otherwise:` in `switchInt`.
- Fixed tests in `tests/mir/exhaustive.mir` and `.test` to expect `copy _1` in `switchInt`.
- Added missing `AxMirRegion`, `AxMirView`, and `drop_flag` to data structures in `mir.h`.

## Files changed
- bootstrap/axiom0/src/mir/mir.h
- bootstrap/axiom0/src/mir/parse.c
- bootstrap/axiom0/src/mir/print.c
- bootstrap/axiom0/src/driver/emit_mir.c
- tests/mir/basic.mir
- tests/mir/roundtrip.test
- tests/mir/complex.mir
- tests/mir/complex.test
- tests/mir/exhaustive.mir
- tests/mir/exhaustive.test

STATUS: COMPLETE round=1
