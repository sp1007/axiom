# T511 Report — E13.3 — Canonical runtime composition, hosted vs freestanding profiles, `@entry` & capability graph specification (`SPEC-52`)

## Summary
- Wrote `spec/SPEC-52-freestanding-runtime-composition.md` (`AXS-FRE-001`..`053`) starting with a Vietnamese `## Tóm tắt` section, specifying:
  - Modular runtime composition without a monolithic runtime, separate Runtime ABI versioning (`AXIOM_RUNTIME_ABI_VERSION`, `REQ-ABI-031`), and a unified Axiom semantic model across all execution profiles and domains (`REQ-FFI-066`, `AXS-FRE-001`).
  - Compilation profiles (`--profile hosted|freestanding|kernel|system`), three-layer `std` architecture (`std.core` zero-OS/zero-heap, `std.alloc`, hosted `std`), deterministic compile-time `static` initialization without C++-style hidden global constructors, explicit foreign allocator domains (`ForeignBox<T, A>`, `REQ-FFI-005..121`), and DMA buffer ownership (`DmaBuffer<T>` / `DmaTransfer<T>`, `REQ-CAP-140`, `REQ-CAP-143`, `AXS-FRE-002`..`005`).
  - `@entry`, `@panic_handler` (`PanicInfo`), `@global_allocator` (`Allocator` / `GlobalAlloc`), `@naked`, `@section("...")`, `@used`, `@no_mangle`, and hardware interrupt handler calling conventions (`extern "interrupt"`, `CallingConventionDescription`-driven GPR preservation and `IRETQ` per `REQ-ABI-078`, and compile-time prohibition of implicit heap allocation, blocking, thread creation, OS I/O, or `await` inside interrupt handlers per `REQ-ABI-102`, `AXS-FRE-010`..`016`).
  - The 12-capability `RuntimeCapabilityGraph` (`RuntimeCap`), post-optimization transitive discovery, per-profile capability policy matrix (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`), and CRT-free / `kernel32.dll`-free native PE32+ image emission for `--profile freestanding` (`AXS-FRE-020`..`023`).
- Updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` (`INV-FRE-001`..`004`, plus syncing `INV-CONC-001` `verify:` paths to `T089`'s delivered `tests/ui/concurrency/send_share, tests/run/concurrency/send_share`).

## Files changed
- spec/SPEC-52-freestanding-runtime-composition.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK` (exit 0)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit 0)
- `python tools/gatecheck.py --no-run`: `MS-P1`..`MS-P10b PASS` (exit 0)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T511`: `0 REFUSED` (exit 0)

STATUS: COMPLETE round=0
