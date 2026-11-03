# T521 Report — E13.5 Canonical panic strategy (`--panic abort|unwind`), FFI no-unwind barrier & drop cleanup specification (`SPEC-54`)

## Summary
- Authored `spec/SPEC-54-panic-unwinding.md` specifying the canonical E13.5 contract (`AXS-PAN-001`..`005`, `AXS-PAN-010`..`014`, `AXS-PAN-020`..`023`, `AXS-PAN-050`..`053`):
  - **§1 Panic strategies (`--panic abort | unwind`) and `@no_panic` verification (`AXS-PAN-001`..`005`)**:
    - CLI flag `--panic abort|unwind` and `axiom.toml` `[package] panic = "abort" | "unwind"` (`REQ-FFI-125`), with invalid modes or unsupported `--no-std` unwind requests rejected via `AX_DRIVER_INVALID_PANIC_STRATEGY` (exit code `2`).
    - `--panic abort` default semantics: immediate process termination (exit code `101` on hosted targets; `core.panic.panic_handler` trap loop on `--no-std` targets) with zero stack unwinding or unwind metadata tables (`AXS-PAN-002`).
    - `--panic unwind` semantics: two-phase search + cleanup stack unwinding executing deterministic reverse-order (LIFO) `Drop` glue for live initialized locals, temporaries, and `defer` guards along MIR `unwind` edges (`REQ-FFI-094`, `AXS-PAN-003`).
    - Double-panic barrier: any secondary panic triggered inside a `Drop.drop` implementation or `defer` cleanup block while a thread is already unwinding immediately aborts the process (`AXS-PAN-003`, `AXS-PAN-014`).
    - `@no_panic` transitive call-graph panic-freedom verification (`REQ-ABI-105`, `AXS-PAN-005`): rejects direct or transitive `panic`, `assert`, `unwrap`, unchecked slice/array indexing, unverified integer division/remainder, or non-`@no_panic` calls with `AX_PANIC_FORBIDDEN_IN_NO_PANIC`, and rejects `@no_panic` on non-function items with `AX_TYPE_INVALID_NO_PANIC_ATTR`.
  - **§2 FFI no-unwind barrier & `std.panic.catch_unwind` (`AXS-PAN-010`..`014`)**:
    - Unwinding across `extern "C"`, WASM host-import/export, C-ABI plugin, or GPU host/device boundaries is forbidden (`REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-FFI-041`, `REQ-FFI-061`, `REQ-FFI-093`, `REQ-ABI-096`).
    - Exported `extern "C"` functions and Axiom function pointers coerced to `extern "C" fn(...)` receive a compiler-synthesized outermost `AbortOnUnwind` guard that runs intra-Axiom `Drop` glue and aborts before returning to the foreign caller (`AXS-PAN-010`, `AXS-PAN-011`).
    - Foreign C++/SEH exceptions attempting to unwind into Axiom frames are caught or blocked at the boundary and abort (`AXS-PAN-012`).
    - `std.panic.catch_unwind<F, R>(f: F) -> Result<R, PanicPayload>` (`REQ-FFI-127`, `AXS-PAN-013`) isolates intra-Axiom panics under `--panic unwind` after running inner `Drop` glue, and is ideal for translating panics into C status codes (`i32` / `@repr(C)` result structs) at FFI boundaries.
  - **§3 MIR unwind edges, native cleanup landing pads, and Windows x64 SEH `.pdata`/`.xdata` (`AXS-PAN-020`..`023`)**:
    - MIR `Call` and `Assert` terminators carry explicit `unwind: Option<BasicBlockId>` edges under `--panic unwind`, targeting synthesized cleanup blocks (`Drop(..., unwind: ...)` -> `Resume` / `AbortOnUnwind` / `CatchUnwindEnd`).
    - Native x86-64 codegen (`T523`) lowers cleanup blocks to native landing pads and emits Windows x64 SEH `.pdata` (`RUNTIME_FUNCTION`) and `.xdata` (`UNWIND_INFO`) tables in COFF/PE outputs.
  - **§4 Conformance, diagnostics, and invariant mapping (`AXS-PAN-050`..`053`)**:
    - Catalogues the E13.5 diagnostic codes, invariant mapping (`INV-PAN-001`..`INV-PAN-003`), requirement traceability matrix (`REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-FFI-041`, `REQ-FFI-061`, `REQ-FFI-093`, `REQ-FFI-094`, `REQ-ABI-096`, `REQ-FFI-125`, `REQ-FFI-127`, `REQ-ABI-105`), and oracle vs native x86-64 parity contract (`0 WEAK-NATIVE`).
- Updated `spec/SPEC-12-drop.md` (`AXS-DROP-006` and `## References`) to link `SPEC-54` for `--panic abort|unwind`, reverse-order `Drop` unwinding, double-panic abort, and FFI no-unwind barriers.
- Registered `SPEC-54` and `AXS-PAN-NNN` in `spec/INDEX.md`, registered E13.5 diagnostics in `spec/diagnostics.md`, and registered `INV-PAN-001`..`INV-PAN-003` in `spec/invariants.md`.

## Verification
- Canonical Axiom syntax check on `spec/SPEC-54-panic-unwinding.md`: `0` occurrences of `::`, `:=`, or `\bvar\b`.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `COVERAGE OK` (`gaps: 0`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.
- `python tools/gatecheck.py --no-run` -> `MS-P1`..`MS-P10b PASS`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T521` -> `0 REFUSED`.

## Files changed
- spec/SPEC-54-panic-unwinding.md
- spec/SPEC-12-drop.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

STATUS: COMPLETE round=0
