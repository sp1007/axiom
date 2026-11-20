---
id: T495
title: Fix regression (fullrun-1 / T489) — native link AX_LINK_UNDEFINED_SYMBOL calling generic inherent method from impl<T> Drop
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T489]
priority: 0
status: done
attempts: 1
paths: [compiler/mir/builder.ax, tests/run/generic_drop_inherent_method]
locks: [compiler/traits/mono.ax, compiler/mir/drop.ax, tests/std/async/executor]
spec: [spec/SPEC-20-selfhost.md, spec/SPEC-03-core-semantics.md]
covers: [REQ-OPT-292, REQ-TST-072]
started: 2026-11-20 12:30:06
finished: 2026-11-20 14:11:54
---
# T495 — Fix regression: `impl<T> Drop` calling a generic inherent method fails native link (`AX_LINK_UNDEFINED_SYMBOL`)

## Why
Detected by both `T444` (Follow-up F4) and periodic Tier-1 sweep `fullrun-1` (`_workspaces/reports/fullrun-1.md`, Regression Cluster B) on HEAD `0b9ff70a`:

Failing test ID outside `_workspaces/baseline-failures.txt`:
- `std/async/executor/async_channel_pipeline.ax` (`[interp]` PASS, `[native]` FAIL, `[native-O1]` FAIL):
  ```text
  error[AX_LINK_UNDEFINED_SYMBOL]: undefined symbol 'close' (mangled: 'close') referenced by 'async_channel_pipeline.obj' in section '.text' (in function 'AsyncSender.drop')
   --> tests/std/async/executor/async_channel_pipeline.ax:4822:5
  ```

Culprit commit: `f0f98f33` (`T489`). `T489` updated `mb_count_generic_params_in_hir()` / `mb_item_cache()` in `compiler/mir/builder.ax` so inherent methods inside `impl<T> Struct<T>` (e.g. `AsyncSender<T>::close`) report `> 0` generic parameters and are treated as generic templates (only emitted when monomorphized for concrete type arguments, never as an unmangled `'close'` symbol). However, `impl<T> Drop for AsyncSender<T>` is explicitly excluded from generic monomorphization (`mb_impl_is_lang_drop`), so `AsyncSender.drop` is still lowered unspecialized and emits a native call to the unspecialized `'close'` symbol, which no longer exists in the object file.

## Scope
- Root-cause the interaction between `mb_impl_is_lang_drop` (unspecialized `impl<T> Drop for S<T>`) and generic inherent methods of `impl<T> S<T>` in `compiler/mir/builder.ax` (and `compiler/traits/mono.ax` / `compiler/mir/drop.ax` if involved).
- Fix cleanly so:
  1. `impl<T> Drop for S<T>` calling an inherent method of `impl<T> S<T>` compiles, links, and executes with correct field layout and semantics in `interp`, `native`, and `native-O1` (including both `tests/std/async/executor/async_channel_pipeline.ax` and structs with `T`-typed fields where the inherent method reads fields before/after `T`!).
  2. All `T489` regressions (`tests/run/generic_inherent_field/*`) continue to pass in `interp`, `native`, and `native-O1` (do NOT reintroduce the T489 silent miscompile!).
- Add focused regression tests under `tests/run/generic_drop_inherent_method/*.ax` covering:
  - `impl<T> Drop for S<T>` calling an inherent method `mut_view(*self).close()` / `self.helper()` on a generic struct (both with and without `T`-typed fields ahead of the accessed field, instantiated with two concrete types like `u64` and `u32` or a struct), checking exact observable stdout in `interp`, `native`, and `native-O1` (`WEAK-NATIVE 0`).
- Do NOT touch `std/async` or modify `tests/std/async/executor/async_channel_pipeline.ax` to work around the compiler bug.

## Acceptance
- [ ] `tests/std/async/executor/async_channel_pipeline.ax` passes 3/3 (`interp`, `native`, `native-O1`) with `--no-cache`.
- [ ] `tests/run/generic_inherent_field/*` passes 100% with `--no-cache`.
- [ ] New regression tests in `tests/run/generic_drop_inherent_method/*` pass in `interp`, `native`, and `native-O1` (`WEAK-NATIVE 0`), and fail on unpatched HEAD.
- [ ] Fresh bootstrap stage 1-3 fixed-point holds (`FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`) in `build-snap-T495`.
- [ ] `taskgate.py --task T495` exits 0 (`FAIL 0`, `BASELINE OK`, `WEAK-NATIVE 0` in own/changed tests, `archcheck` 0 violations).
- [ ] Report `_workspaces/reports/T495-report.md` with exact `## Files changed` and `STATUS: COMPLETE round=0`.

## Out of scope
- `bootstrap/axiom0` (frozen), `std/`, `docs/`.

## Log
- 2026-11-20 created from fullrun-1 bisect (Cluster B, culprit f0f98f33 T489) & T444 follow-up F4
- 2026-11-20 12:30:06 started (attempt 1) T495-impl
- 2026-11-20 14:11:54 accepted by QA -> done
