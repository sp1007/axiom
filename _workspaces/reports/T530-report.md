# T530 — E13.7 — Canonical module-relative bindings (`@at(image("mod") + off)`, `image_self()`) specification (`SPEC-56`)

## Summary
- Authored `spec/SPEC-56-module-relative-bindings.md` (`AXS-MOD-001`..`053`) starting with a Vietnamese `## Tóm tắt` section and consolidating `ADR-0001 §5–7`, `REQ-OWNER-005`, `REQ-OWNER-006`, `REQ-OWNER-008`, `REQ-ABI-032`, `REQ-ABI-033`, `REQ-ABI-095`, `REQ-CAP-132`, `REQ-FFI-119`, `REQ-FFI-042`, `0104`, `0138`, `0187`, and `tasks/0336`:
  - **Module-Base Address Expressions & Hosted Overlays (`AXS-MOD-001`..`003`)**: Specified `image("name") -> usize` and `image_self() -> usize` in `--profile hosted`, `@at(image("mod") + offset)` and `@at(image_self() + offset)` overlays on `static`, `static mut`, and `extern "<abi>" fn`, ordinary-syntax usage after an `unsafe` declaration, the overlay-only restriction rejecting foreign placements (`AX_UNSAFE_AT_FOREIGN_PLACEMENT`), `@repr(C)`/primitive layout checks (`AX_UNSAFE_INVALID_AT_LAYOUT`), and constant RVA alignment/overlap checks (`AX_UNSAFE_AT_MISALIGNED`, `AX_UNSAFE_AT_OVERLAP`).
  - **Open-World Dynamic Linking Boundary & Separation from Hot Reload (`AXS-MOD-004`..`005`)**: Specified dynamic library loading as an open-world optimization barrier (`REQ-ABI-095`, `REQ-FFI-119`), explicit `@export` PE DLL export surfaces (`REQ-FFI-042`), capability lifetime retention on loaded library handles (`REQ-CAP-132`), and the strict separation of dynamic linking/module-relative bindings from hot reload (`REQ-ABI-032`, `REQ-ABI-033`).
  - **Load-Time Slot Lowering, PE DLL `DllMain` / EXE Startup Resolver & Oracle `ProcessModuleMap` (`AXS-MOD-010`..`014`)**: Specified `PlacementAddr.ImageRel` HIR/MIR slot lowering (`__ax_modslot_<S>`), x86-64 `RIP`-relative indirect call/load dispatch, `.rdata` `ModRelEntry` descriptors, pre-entry resolution via `GetModuleHandleW` (`image("mod")`) and `__ImageBase` (`image_self()`), deterministic failure when a target module is not loaded (`DllMain` returns `FALSE` on `DLL_PROCESS_ATTACH` so `LoadLibraryW` returns `NULL`; EXE startup panic), `addr_of(target) - image_self()` RVA computation (`REQ-OWNER-008`), and the `--interp` `ProcessModuleMap` oracle (`AX_UNSAFE_MODULE_NOT_LOADED`).
- Updated `spec/INDEX.md` (§2 Canonical documents, §4 Identifier namespaces `AXS-MOD-NNN`, §5 Topic map), `spec/diagnostics.md` (§11 `AX_UNSAFE_AT_FOREIGN_PLACEMENT`, `AX_TYPE_INVALID_IMAGE_ARG`, `AX_UNSAFE_MODULE_NOT_LOADED`, and Sources), and `spec/invariants.md` (§1 `MOD` group, §23 `INV-MOD-001`..`003`, and Sources).

## Files changed
- `spec/SPEC-56-module-relative-bindings.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `COVERAGE OK` (0 gaps).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.
- `python tools/gatecheck.py --no-run` -> `INV-MOD-001`..`003` verified cleanly (no `INV-*` errors).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T530` -> `0 REFUSED`.

STATUS: COMPLETE round=0
