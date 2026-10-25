# T160 Implementation Report — `std` project test for `Arena` implicit drop (`round=0`)

## Summary

Implemented the project-mode integration test under `tests/std/project/arena_drop/` and its companion `.test` manifest `tests/std/project/arena_drop.test` (backed by `tests/std/project/arena_drop_oracle.py`) to close the `T141` QA finding on `std.core.arena.arena.Arena` implicit drop coverage.

- **Real `std.core.arena.arena.Arena` import and execution**:
  - `tests/std/project/arena_drop/axiom.toml` defines the `arena_drop` package (`edition = "2026"`).
  - `tests/std/project/arena_drop/src/main.ax` imports `std.core.arena.arena.{Arena, arena_with_chunk_size, arena_alloc_raw, arena_chunk_count, arena_chunks_freed, arena_chunks_in_use}` and exercises `Arena`'s `impl Drop for Arena` (`arena_destroy(self)`) in two scenarios:
    1. **Function scope exit (`run_in_fn`)**: Declares a companion `ArenaProbe` (`impl Drop for ArenaProbe`) before `let mut a: Arena = arena_with_chunk_size(64)`, allocates two 48-byte regions across two 64-byte chunks, writes `10` and `32` (`sum = 42`), and records `a`'s address in `probe.arena_ptr`. Before scope exit, `a.chunks_in_use()` is `2` and `a.chunks_freed()` is `0`. At scope exit, by `SPEC-12` `AXS-DROP-002` (locals drop in reverse declaration order), `a` drops first (`arena_destroy` frees both chunks, setting `chunks_freed = 2` and `chunk_count = 0`) and `probe` drops second, observing and printing `2` and `0`.
    2. **Struct owning an `Arena` (`run_in_struct`)**: Defines `struct WorkCtx { pub arena: Arena, pub probe: ArenaProbe }`, constructs a `WorkCtx` with a 64-byte chunk size, allocates three 48-byte regions across three chunks, writes `11`, `22`, and `33` (`total = 66`), and records `ctx.arena`'s address in `ctx.probe.arena_ptr`. Before scope exit, `ctx.arena.chunk_count()` is `3` and `ctx.arena.chunks_freed()` is `0`. At scope exit, by `SPEC-12` `AXS-DROP-002` (struct fields drop in declaration order), field 0 (`ctx.arena`) drops first (`chunks_freed = 3`, `chunk_count = 0`) and field 1 (`ctx.probe`) drops second, observing and printing `3` and `0`.
- **Both `interp` and `native` (`run` and `build` + execute) legs**:
  - `tests/std/project/arena_drop/src/main.ax` (`std/project/arena_drop`) runs `{compiler} run --interp --std-root {std_root}` via `arena_drop_oracle.py interp`.
  - `tests/std/project/arena_drop.test` (`std/project/arena_drop.test`) runs `{compiler} run --interp` (`run` leg) as well as `{compiler} build` + execute at both `-O0` and `-O1` (`native` legs) via `arena_drop_oracle.py native`, asserting all legs exit `0` and emit identical stdout (`42\n2\n0\n2\n0\n66\n3\n0\n3\n0\n`).
- **`T141` criterion status**:
  - `tests/run/drop/arena_implicit_drop.ax` is preserved untouched as a standalone unit test.
  - `T141`'s `Arena` acceptance criterion ("Project test using `std/core/arena`: allocate in a function, return without explicit free, confirm drop runs") is now met by `tests/std/project/arena_drop/` and `tests/std/project/arena_drop.test`.

## Verification & Gate 4a Native Evidence

1. **Snapshot build & targeted `std/project` run**:
   - Built `build-snap-T160/build/axiom0.exe` (`Debug`, `Ninja`, 0 warnings).
   - Ran `python build-snap-T160/tools/axtest.py --compiler build-snap-T160/build/axiom0.exe --root build-snap-T160 --filter std/project -v`:
     ```text
     PASS    std/project/arena_drop
     PASS    std/project/arena_drop.test
     TOTAL 2 PASS 2 FAIL 0 SKIP 0 XFAIL 0
     ```
2. **Gate 4a spot mutations (in `build-snap-T160`, then restored)**:
   - **Mutation A (expected stdout changed from post-drop `2\n0` / `3\n0` to pre-drop `0\n2` / `0\n3`)**:
     ```text
     FAIL    std/project/arena_drop: stdout differs at byte 7 (expected 22 bytes, got 22 bytes)
         expected: 2\n2\n0\n0\n2\n66\n3\n0\n0\n3\n | hex 32 0a 32 0a 30 0a 30 0a 32 0a 36 36 0a 33 0a 30 0a 30 0a 33 0a
         actual:   2\n2\n0\n2\n0\n66\n3\n0\n3\n0\n | hex 32 0a 32 0a 30 0a 32 0a 30 0a 36 36 0a 33 0a 30 0a 33 0a 30 0a
     FAIL    std/project/arena_drop.test: stdout differs at byte 7 (expected 22 bytes, got 22 bytes)
         expected: 2\n2\n0\n0\n2\n66\n3\n0\n0\n3\n | hex 32 0a 32 0a 30 0a 30 0a 32 0a 36 36 0a 33 0a 30 0a 30 0a 33 0a
         actual:   2\n2\n0\n2\n0\n66\n3\n0\n3\n0\n | hex 32 0a 32 0a 30 0a 32 0a 30 0a 36 36 0a 33 0a 30 0a 33 0a 30 0a
     TOTAL 2 PASS 0 FAIL 2 SKIP 0 XFAIL 0
     ```
   - **Mutation B (`Arena.drop` body in `build-snap-T160/std/core/arena/arena.ax` replaced with no-op `let _ = self`)**:
     ```text
     FAIL    std/project/arena_drop: stdout differs at byte 7 (expected 22 bytes, got 22 bytes)
         expected: 2\n2\n0\n2\n0\n66\n3\n0\n3\n0\n | hex 32 0a 32 0a 30 0a 32 0a 30 0a 36 36 0a 33 0a 30 0a 33 0a 30 0a
         actual:   2\n2\n0\n0\n2\n66\n3\n0\n0\n3\n | hex 32 0a 32 0a 30 0a 30 0a 32 0a 36 36 0a 33 0a 30 0a 30 0a 33 0a
     FAIL    std/project/arena_drop.test: stdout differs at byte 7 (expected 22 bytes, got 22 bytes)
         expected: 2\n2\n0\n2\n0\n66\n3\n0\n3\n0\n | hex 32 0a 32 0a 30 0a 32 0a 30 0a 36 36 0a 33 0a 30 0a 33 0a 30 0a
         actual:   2\n2\n0\n0\n2\n66\n3\n0\n0\n3\n | hex 32 0a 32 0a 30 0a 30 0a 32 0a 36 36 0a 33 0a 30 0a 30 0a 33 0a
     TOTAL 2 PASS 0 FAIL 2 SKIP 0 XFAIL 0
     ```
   - Restored snapshot via `taskctl.py snapshot T160` and re-verified `TOTAL 2 PASS 2 FAIL 0 SKIP 0 XFAIL 0`.
3. **Suite verification**:
   - `std/project` filter (`-v`): `TOTAL 2 PASS 2 FAIL 0 SKIP 0 XFAIL 0`
   - `std/` filter (`-j 1`): `TOTAL 125 PASS 125 FAIL 0 SKIP 0 XFAIL 0`
   - `run/drop/` filter (`-j 1`): `TOTAL 156 PASS 156 FAIL 0 SKIP 0 XFAIL 0`
   - Full suite (`-j 1`): `2689 / 2691 PASS` on first pass; the 2 CPU-contention timeouts in `selfhost/typeck/` (`qa_typeck_b.ax` and `qa_typeck_c.ax`) both passed on re-run (`TOTAL 9 PASS`, `qa_typeck_b.ax` `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`), giving `2691 / 2691 PASS`.

## Files changed

- `tests/std/project/arena_drop/axiom.toml`
- `tests/std/project/arena_drop/src/main.ax`
- `tests/std/project/arena_drop.test`
- `tests/std/project/arena_drop_oracle.py`

## Follow-ups

- `bootstrap/axiom0/src/driver/project.c` (`ax_project_discover`) and `compiler/driver/opts.ax` (`project_append_std_core_files`) currently auto-append only `core/option.ax`, `core/result.ax`, `core/prelude.ax`, and `core/host.ax` from `--std-root` rather than loading arbitrary `std.*` submodules (such as `core/arena/arena.ax`) on demand when imported by a project. To test against the live `{std_root}/core/arena/arena.ax` without modifying `bootstrap/` or `compiler/`, `arena_drop_oracle.py` stages `{std_root}/core/arena/arena.ax` into `<tmp>/arena_drop_<mode>/src/arena.ax` (where its leading `module std.core.arena.arena` declaration preserves `std.core.arena.arena` module resolution and `is_std = true`).

STATUS: COMPLETE round=0
