# T512 report

## Summary

Implemented `SPEC-52` (`AXS-FRE-001`..`005`, `AXS-FRE-010`..`016`, `AXS-FRE-020`..`022`, `AXS-FRE-050`..`053`, covering `REQ-ABI-102` and `REQ-ABI-031`):

1. **Driver & Manifest `--profile` Configuration (`compiler/driver/opts.ax`, `compiler/driver/mod.ax`, `compiler/driver/pipeline.ax`)**:
   - Added `--profile hosted|freestanding|kernel|system` CLI option (defaulting to `hosted`) and `axiom.toml` `[package]` / `[target]` `profile = "..."` configuration (`[target]` / `[target.*]` overrides `[package]`, CLI `--profile` overrides `axiom.toml`).
   - Unknown profile names exit with code `2` (`AX_EXIT_USAGE`) and emit `AX_DRIVER_INVALID_PROFILE` (`217u32`, matching `compiler/build/manifest/mod.ax`).
   - Suppressed implicit Windows host provider linking (`pipe_wants_host_providers`) and Layer-3 hosted `std` module auto-loading (`pipe_std_on_demand`) under `--profile freestanding` and `--profile kernel`.
   - Enforced `@no_mangle` generic parameter rejection (`AX_FFI_GENERIC_EXPORT`) alongside `@export` in `pipe_validate_export_item`, and allowed freestanding/attributed `static` items through `session_comptime_check_and_eval` while preserving `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` on un-attributed `static` items in `--profile hosted`.

2. **Syntax & HIR Support (`compiler/syntax/ast.ax`, `compiler/syntax/parse.ax`, `compiler/hir/hir.ax`, `compiler/hir/lower.ax`)**:
   - Generalized `at_fn_item_start` to scan past arbitrary combinations of `unsafe`, `extern ["abi"]`, `async`, and `comptime` before `fn` (enabling `unsafe extern "interrupt" fn` and `@naked pub unsafe extern "interrupt" fn`).
   - Parsed and lowered leading attributes on `fn`/closure parameters and statements (`AstParam.attrs`, `AstStmt.attrs` -> `HirParam.attrs`, `HirStmt.attrs`) while keeping AST/HIR dumps unchanged when `attrs` is null, and populated `is_entry`, `is_naked`, `is_used`, `is_panic_handler`, `is_global_allocator`, and `is_no_mangle` on `HirItem`.
   - Enabled `never` in path-type annotations (`TYPE_PATH | 128u8` -> `TY_NEVER`) and `async` as a dotted segment in `use` trees (`use std.async.*` per `AXS-FRE-020`).

3. **Attribute, Interrupt & Runtime Capability Graph Verifier (`compiler/types/typeck.ax`, `compiler/types/mod.ax`, `compiler/diag/code.ax`)**:
   - Registered `SPEC-52` diagnostic codes (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`, `AX_NAME_FREESTANDING_FORBIDDEN_IMPORT`, `AX_TYPE_ENTRY_MISSING`, `AX_TYPE_DUPLICATE_ENTRY`, `AX_TYPE_ENTRY_SIGNATURE`, `AX_TYPE_INVALID_PANIC_HANDLER`, `AX_TYPE_DUPLICATE_PANIC_HANDLER`, `AX_TYPE_INVALID_GLOBAL_ALLOCATOR`, `AX_TYPE_DUPLICATE_GLOBAL_ALLOCATOR`, `AX_TYPE_INVALID_NAKED_FN`, `AX_TYPE_INVALID_SECTION`, `AX_UNSAFE_INTERRUPT_FORBIDDEN_OP`, `AX_FFI_BAD_TYPE`, `AX_DRIVER_INVALID_PROFILE`) in `compiler/diag/code.ax` without altering `compiler/diag/explain/mod.ax`.
   - Validated `@entry` (including bare-metal `() -> never|i32|u32|usize`, `(usize) -> never`, UEFI `(*const u8, *const u8) -> usize`, missing/duplicate `@entry` for freestanding/kernel `exe`, and preserving hosted PE DLL `@entry` hooks), `@panic_handler`, `@global_allocator`, `@naked` (modifier rules, `<= 8`-byte register-fit non-`Drop` signature types, and no `let`/`for` local stack bindings), `@section("...")` (1..=64 printable ASCII string literal on `fn`/`static`), `@used` (on `fn`/`static`), and `extern "interrupt"` signatures (`()`, `(view<InterruptFrame>)`, `(*const InterruptFrame)`, `(frame, err_code: u64)` -> `()` / `never`, non-`async`, non-generic, non-`comptime`).
   - Built the 12-capability `RuntimeCap` fixed-point `CapGraph` analyser over functions, methods, `std.core.host` / `@intrinsic` / `@lang` leaves, `@blocking` functions, `@thread_local` / `@global_allocator` statics, `.await`, and implicit `Drop` glue, enforcing `ExecutionDomain.Interrupt` (`AX_UNSAFE_INTERRUPT_FORBIDDEN_OP`, `REQ-ABI-102`) in all profiles and the `AXS-FRE-022` profile capability matrix (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`, `AX_NAME_FREESTANDING_FORBIDDEN_IMPORT`) from `Roots` (`@entry`, `extern "interrupt"`, `@export`, `@used`, `@panic_handler`) with structured JSON `data` and transitive call-chain `notes`.

4. **Tests (`tests/ui/freestanding/`)**:
   - Added 19 test cases (23 files) covering valid freestanding/kernel/system/lib programs, `SPEC-52 AXS-FRE-052` canonical multi-error diagnostics, Layer-3 forbidden imports in `freestanding` and `kernel`, direct and multi-hop transitive `extern "interrupt"` capability rejections (`HeapAlloc` even when `@global_allocator` is declared, `Blocking`, `Thread`, `OsIo`, `AsyncSuspend`, and implicit `Drop` glue), `@entry`/`@panic_handler`/`@global_allocator`/`@naked`/`@section`/`@used`/`@no_mangle` valid and invalid forms, `axiom.toml` `[package]`/`[target]`/`--profile` precedence, invalid `--profile` exit code `2`, and `--json` `data`/`notes` verification.

## Files changed

- compiler/diag/code.ax
- compiler/driver/mod.ax
- compiler/driver/opts.ax
- compiler/driver/pipeline.ax
- compiler/hir/hir.ax
- compiler/hir/lower.ax
- compiler/syntax/ast.ax
- compiler/syntax/parse.ax
- compiler/types/mod.ax
- compiler/types/typeck.ax
- tests/ui/freestanding/entry_invalid_and_duplicate.ax
- tests/ui/freestanding/entry_missing.ax
- tests/ui/freestanding/forbidden_imports.ax
- tests/ui/freestanding/forbidden_imports_kernel.ax
- tests/ui/freestanding/interrupt_bad_signatures.ax
- tests/ui/freestanding/interrupt_forbidden_ops.ax
- tests/ui/freestanding/naked_and_section_invalid.ax
- tests/ui/freestanding/panic_and_allocator_invalid.ax
- tests/ui/freestanding/pkg_cli_override_hosted/axiom.toml
- tests/ui/freestanding/pkg_cli_override_hosted/src/main.ax
- tests/ui/freestanding/pkg_manifest_freestanding/axiom.toml
- tests/ui/freestanding/pkg_manifest_freestanding/src/main.ax
- tests/ui/freestanding/pkg_target_kernel_override/axiom.toml
- tests/ui/freestanding/pkg_target_kernel_override/src/main.ax
- tests/ui/freestanding/profile_cli_and_manifest.test
- tests/ui/freestanding/profile_cli_and_manifest_oracle.py
- tests/ui/freestanding/profile_forbidden_caps.ax
- tests/ui/freestanding/spec52_bad_freestanding.ax
- tests/ui/freestanding/valid_entry_signatures.ax
- tests/ui/freestanding/valid_freestanding_boot.ax
- tests/ui/freestanding/valid_freestanding_lib.ax
- tests/ui/freestanding/valid_kernel_global_allocator.ax
- tests/ui/freestanding/valid_system_profile.ax

## Tests

All builds and tests executed inside isolated snapshot `build-snap-T512/` on `HEAD 3b6026d3f72b` at `-j 2`:

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T512` -> refreshed `HEAD 3b6026d + 34 changed, 0 deleted`, 36 bundle generators / 60 files regenerated cleanly.
- `python tools/build_axiomc.py --out build --root . --stage 2` (in `build-snap-T512/`) ->
  - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 89a5e7feac1e9a27b20e4d576ef29bdfd1849490faca1df5333767774642db58` (`9324032` bytes)
  - `STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on 6 smoke program(s) (O1, incl. Xin chào thế giới)`
- `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 --filter ui/freestanding` -> `TOTAL 19 PASS 19 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --filter driver` -> `TOTAL 81 PASS 69 FAIL 0 SKIP 12 XFAIL 0`, `WEAK-NATIVE 0`.
- `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --filter run/diag_ux2` -> `TOTAL 11 PASS 11 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --filter ui/` -> `TOTAL 420 PASS 420 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- `python tools/taskgate.py --task T512 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T512.json` ->
  - `own`: `19 ids | 19 PASS | 0 FAIL`
  - `affected`: `319 ids | 485 PASS | 0 FAIL | 2 SKIP` (including 80 `selfhost` tests, 83 `ui` tests, 45 `parse` tests, 34 `driver` tests, 25 `modules` tests, 23 `typeck` tests, 15 `run` tests, 11 `conformance` tests)
  - `smoke`: `33 ids | 54 PASS | 0 FAIL`
  - `total (dedup)`: `TOTAL 534 PASS 532 FAIL 0 SKIP 2 XFAIL 0` (exit `0`)
  - `WEAK-NATIVE`: `0` in own/changed tests
  - `Baseline`: `BASELINE OK`, `Failing ids: none`
  - `archcheck`: `232 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T512` -> exit `0`, `0 REFUSED`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

## Spec deviations

none

## Follow-ups

- `T513` (E13.4) will lower `@entry`, `@naked`, `@section("...")`, `@used`, `@panic_handler`, `@global_allocator`, and `extern "interrupt"` prologues/epilogues in MIR/LIR/object/linker codegen.
- `T514` (E13.5) will complete freestanding Layer 1/2 stdlib refactoring (`std/core`, `std/alloc`, `std/sync`, including generic `Box<T>` return annotations in `std/alloc/box.ax`).

STATUS: COMPLETE round=0