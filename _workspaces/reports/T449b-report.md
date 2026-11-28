# T449b Report — Harness: regenerate std live-source test bundles automatically

## Summary

Extended the harness bundle-regeneration mechanism (`.claude/skills/axiom-tasks/scripts/bundles.py`) so all 12 class-(a) live-source test bundle generators outside `tests/selfhost/` participate in `regen`/`check`/`list`, `taskctl.py snapshot`, and `taskctl.py accept` (including REGATE checks and retired-file cleanup) identically to `tests/selfhost/**/gen_*.py`.

### Design choices
- **Explicit allowlist (`EXTRA_GENERATORS`)** in `.claude/skills/axiom-tasks/scripts/bundles.py`: lists the 12 class-(a) live-source bundle generators (`8` under `tests/std/**`, `3` under `tests/conformance/p11/**`, `1` under `tests/perf/p11_executor/`). Using an explicit allowlist guarantees that static fixture generators (class b, such as `tests/std/num/gen_tests.py` or `tests/conformance/p12/e12_1_integers/gen_conformance.py`) can never be accidentally picked up or executed.
- **Determinism & output-tracking contract**:
  - All 12 class-(a) generators resolve `ROOT` from `__file__`, run purely from tree sources with no compiler or external tool calls in write mode, write LF-only `.ax` bundles, and fail non-zero in `--check` mode when stale or missing.
  - Adapted all 8 `tests/std/**/gen_tests.py` generators (in task `paths`) to emit `wrote <path-relative-to-ROOT>` lines in write mode, matching the `tests/selfhost/**/gen_*.py` contract directly.
  - For the 4 allowlisted conformance/perf generators outside `paths` (`tests/conformance/p11/{e11_3_threads_sync,e11_5_executors,e11_6_async_io}/gen_tests.py`, `tests/perf/p11_executor/gen_tests.py`), `bundles.py` resolves their existing `Generated <rel>` lines relative to the generator's directory so they participate without out-of-scope edits.
- **Single manifest (`tests/selfhost/generated-files.txt`)**: `bundles.regen()` records all 164 generated bundles (selfhost + std/conformance/perf) plus the manifest itself (165 files total from 48 generators). `taskctl.py snapshot` and `taskctl.py accept` automatically regenerate, `--check`, REGATE-check, stage, and retire them.
- **`taskctl.py` `touches_bundle_inputs`**: also treats edits to `bundles.py` itself as bundle-affecting so a `bundles.py`-only change refreshes the manifest on `accept`.
- **Docs & regression tests**: updated `.claude/skills/axiom-tasks/SKILL.md` and `.claude/skills/axiom-testing/SKILL.md` (agents never hand-edit or list these bundles in `## Files changed`), and added 3 end-to-end tests in `selftest.py` verifying std/conformance class-(a) regeneration/staging and class-(b) exclusion.

## Inventory of non-selfhost generators

| Generator | Class | Bundles live `std/`/`compiler/`? | Harness-owned? | Notes |
|---|---|---|---|---|
| `tests/std/async/executor/gen_tests.py` | (a) | Yes (`std/async/*`, `std/sync/*`) | Yes (`EXTRA_GENERATORS`) | Adapted to `wrote <rel>` (9 `.ax` bundles; `check_async_bundles.test`) |
| `tests/std/async/structured/gen_tests.py` | (a) | Yes (`std/async/*`, `std/sync/*`) | Yes (`EXTRA_GENERATORS`) | Adapted to `wrote <rel>` (16 `.ax` bundles; `check_structured_bundles.test`) |
| `tests/std/async/waker/gen_tests.py` | (a) | Yes (`std/async/*`) | Yes (`EXTRA_GENERATORS`) | Adapted to `wrote <rel>` (4 `.ax` bundles; `check_waker_bundles.test`) |
| `tests/std/async/waker_qa/gen_tests.py` | (a) | Yes (`std/async/*`) | Yes (`EXTRA_GENERATORS`) | Adapted to `wrote <rel>` (5 `.ax` bundles; `check_waker_qa_bundles.test`) |
| `tests/std/channel/gen_tests.py` | (a) | Yes (`std/sync/channel/mod.ax`, prereqs) | Yes (`EXTRA_GENERATORS`) | Adapted to `wrote <rel>` (8 `.ax` bundles; `check_channel_bundles.test`) |
| `tests/std/fiber/gen_tests.py` | (a) | Yes (`std/fiber/mod.ax`, `std/sys/windows/fiber.ax`, prereqs) | Yes (`EXTRA_GENERATORS`) | Adapted to `wrote <rel>` (30 `.ax` bundles incl. `native_panic/*`; `check_fiber_bundles.test`) |
| `tests/std/sync/gen_tests.py` | (a) | Yes (`std/sync/*.ax`, prereqs) | Yes (`EXTRA_GENERATORS`) | Adapted to `wrote <rel>` (9 `.ax` bundles; `check_sync_bundles.test`) |
| `tests/std/thread/native_panic_hook/gen_tests.py` | (a) | Yes (`std/sys/windows/thread.ax`, prereqs) | Yes (`EXTRA_GENERATORS`) | Adapted to `wrote <rel>` (2 `.ax` bundles; `check_bundles.test`) |
| `tests/conformance/p11/e11_3_threads_sync/gen_tests.py` | (a) | Yes (`std/sync/*`, `std/thread/*`, prereqs) | Yes (`EXTRA_GENERATORS`) | Pure; `Generated <rel>` parsed by `bundles.py` (8 `.ax` bundles; `check_conformance_bundles.test`) |
| `tests/conformance/p11/e11_5_executors/gen_tests.py` | (a) | Yes (`std/async/*`, `std/fiber/mod.ax`) | Yes (`EXTRA_GENERATORS`) | Pure; `Generated <rel>` parsed by `bundles.py` (9 `.ax` bundles; `check_conformance_bundles.test`) |
| `tests/conformance/p11/e11_6_async_io/gen_tests.py` | (a) | Yes (`std/async/*`, `std/io/*`, `std/net/*`) | Yes (`EXTRA_GENERATORS`) | Pure; `Generated <rel>` parsed by `bundles.py` (1 `.ax` bundle; `check_conformance_bundles.test`) |
| `tests/perf/p11_executor/gen_tests.py` | (a) | Yes (`std/async/*`, `std/fiber/mod.ax`) | Yes (`EXTRA_GENERATORS`) | Pure; `Generated <rel>` parsed by `bundles.py` (4 `.ax` bundles; `check_perf_bundles.test`) |
| `tests/abi/win64_float/gen_expected.py` | (b) | No | Excluded | Static Python IEEE-754 oracle (`abi_calls.txt`) |
| `tests/build_native/gen_stress_4096_jumps.py` | (b) | No | Excluded | Static 4096-jump stress fixture |
| `tests/conformance/p12/e12_1_integers/gen_conformance.py` | (b) | No | Excluded | Static `.ax`/`.test` fixtures (`num_oracle.py` stages live std at test runtime) |
| `tests/link/local_symbols/gen_local_symbols_obj.py` | (b) | No | Excluded | Hand-built COFF `.obj` binary fixtures |
| `tests/lir/float/gen_float_cases.py` | (b) | No | Excluded | Static float `.ax` test cases |
| `tests/run/int128_native/regen_expected.py` | (b) | No | Excluded | Static 128-bit `.ax` fixtures |
| `tests/run/intrinsics/gen_ops_table.py` | (b) | No | Excluded | Independent Python oracle for static `ops_table.ax` |
| `tests/run/numeric/gen_int_semantics.py` | (b) | No | Excluded | Independent Python reference for static integer semantics `.ax` |
| `tests/run/numeric/mixed_int_matrix/gen_matrix.py` | (b) | No | Excluded | Static mixed-width integer matrix `.ax` |
| `tests/run/numeric/tilde_tree/gen_tilde.py` | (b) | No | Excluded | Static `ctx_*.ax` fixtures |
| `tests/run/symbol_id_space/gen_symbol_id_space.py` | (b) | No | Excluded | Static symbol-id-space regression `.ax` |
| `tests/std/float_fmt/make_vectors.py` | (b) | No | Excluded | Static float-format vector `.ax` fixtures |
| `tests/std/math/gen_tables.py` | (b) | No (writes `std/math/tables.ax`) | Excluded | Generates live std source from `mathtables.py`, not a test bundle |
| `tests/std/math/make_vectors.py` | (b) | No | Excluded | Static 300-bit mpmath vector `.ax` fixtures |
| `tests/std/num/gen_num.py` | (b) | No (writes `std/core/num.ax`, `convert.ax`) | Excluded | Generates live std sources from templates, not test bundles |
| `tests/std/num/gen_tests.py` | (b) | No | Excluded | Static integer `.ax`/`.test` fixtures (`num_oracle.py` stages live std at runtime) |
| `tests/std/num/qa_gen_matrix128.py` | (b) | No | Excluded | Static 128-bit `try_from` matrix `.ax` |
| `tests/unit/kernel/gen_hash_vectors.py` | (b) | No | Excluded | Independent Python reference for static AXH64 hash vectors |
| `tools/gen_encode_tests.py` | (b) | Embeds `encode.ax` + GNU `as` | Excluded | Non-pure: invokes external GNU `as` + `objdump` in write mode |
| `tools/gen_large.py` | (b) | No | Excluded | CLI tool for ad-hoc large scale-test generation |

## Files changed

- .claude/skills/axiom-tasks/scripts/bundles.py
- .claude/skills/axiom-tasks/scripts/taskctl.py
- .claude/skills/axiom-tasks/scripts/selftest.py
- .claude/skills/axiom-tasks/SKILL.md
- .claude/skills/axiom-testing/SKILL.md
- tests/std/async/executor/gen_tests.py
- tests/std/async/structured/gen_tests.py
- tests/std/async/waker/gen_tests.py
- tests/std/async/waker_qa/gen_tests.py
- tests/std/channel/gen_tests.py
- tests/std/fiber/gen_tests.py
- tests/std/sync/gen_tests.py
- tests/std/thread/native_panic_hook/gen_tests.py

## Tests

- `python .claude/skills/axiom-tasks/scripts/selftest.py`: **159/159 checks passed** (including 3 new T449b checks covering `bundles.py regen`/`list`, `snapshot` regeneration on `std/` edit, `accept` single-commit staging, and class-(b) `tests/std/num/gen_tests.py` never being invoked).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: **HARNESS OK** (exit 0).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T449b`: refreshed `build-snap-T449b` on HEAD `99f29bd` -> `bundles regenerated in build-snap-T449b: 48 generator(s), 165 file(s), 44s`.
- `python .claude/skills/axiom-tasks/scripts/bundles.py check --root build-snap-T449b`: **exit 0** (`bundles check: 48 generator(s), 0 file(s), 46s`).
- `python .claude/skills/axiom-tasks/scripts/bundles.py list --root build-snap-T449b`: lists all 165 generated files, including all outputs from all 12 class-(a) generators (`tests/std/**`, `tests/conformance/p11/**`, `tests/perf/p11_executor/`).
- Simulated `std/` edit check in `build-snap-T449b` (appended comment to `std/sync/atomic.ax`, verified `--check` failed with exit 1 before regen, ran `bundles.py regen --root build-snap-T449b`, verified all 12 class-(a) generators passed `--check` with exit 0 and refreshed bundles contained the edit, then restored snapshot cleanly): **SIMULATED CHECK OK**.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T449b`: verified 0 `REFUSED`.

## Spec deviations

none

## Follow-ups

- Optional: migrate the 4 conformance/perf generators (`tests/conformance/p11/{e11_3_threads_sync,e11_5_executors,e11_6_async_io}/gen_tests.py` and `tests/perf/p11_executor/gen_tests.py`) from `Generated <name>` to `wrote <rel>` in a small cleanup task so every allowlisted generator uses the identical output prefix (they already work via `bundles.py`'s `Generated ` fallback).

## Status

STATUS: COMPLETE round=0
