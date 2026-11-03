# T475 — E12.5 — Canonical CPU feature detection, `@target_feature` legality & function multiversioning specification (`SPEC-44`)

## Summary
- Authored canonical `spec/SPEC-44-cpu-features-multiversioning.md` (`AXS-CPU-001`..`AXS-CPU-042`) starting with a Vietnamese `## Tóm tắt` section and consolidating `specs/0095 §7–8, §42 (ASIMD-14)`, `specs/0163 §1–7`, `tasks/0341 §100 (ANUM-29..30)`, `tasks/0344 §100 (ASIMD-71..78, 97)`, `tasks/0347 §100 (ASIMD-71..78, 97)`, `tasks/0403 §82`, `tasks/0407 §35`, `tasks/0453 §194.14–15`, and `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-022/032/054/060/091`).
- Defined the x86-64 `TargetDesc` feature bitmask (`AXS-CPU-001`, baseline `sse`/`sse2` on `x86_64-windows`, optional `sse3`, `ssse3`, `sse4.1`, `sse4.2`, `popcnt`, `lzcnt`, `bmi1`, `bmi2`, `avx`, `avx2`, `fma`, `avx512f`), the implication DAG (`avx512f -> avx2 -> avx -> sse4.2 -> sse4.1 -> ssse3 -> sse3 -> sse2 -> sse`, `fma -> avx`, `sse4.2 -> popcnt`, `bmi2 -> bmi1`, `AXS-CPU-002`), the `--target-feature=+feat,-feat` CLI option (`AXS-CPU-003`), the semantics vs codegen legality separation (`AXS-CPU-004`), and the prohibition of implicit `CPUID` probing in ordinary functions (`AXS-CPU-005`).
- Specified `@target_feature("...")` lowering (`AXS-CPU-010`), call-site legality rules (`AXS-CPU-011`, requiring static feature inclusion, a dominating `is_x86_feature_detected` guard, an `unsafe` block, or a `@multiversion` dispatcher; otherwise emitting `AX_TARGET_FEATURE_MISMATCH`), function-pointer coercion restrictions (`AXS-CPU-012`), inliner boundary restrictions (`AXS-CPU-013`), and per-function legalizer/isel confinement (`AXS-CPU-014`).
- Specified `std.arch.x86_64.cpuid_count` / `xgetbv` (`AXS-CPU-020`), the `CPUID` Leaf `1`/`7`/`0x80000001` + OS `XGETBV(0)` (`XCR0` XMM/YMM/ZMM) verification protocol (`AXS-CPU-021`), lock-free `Atomic<u64>` feature caching and `std.arch.is_x86_feature_detected` (`AXS-CPU-022`), and deterministic `--interp-cpu-features` oracle simulation (`AXS-CPU-023`).
- Specified `@multiversion("...")` syntax and validation (`AXS-CPU-030`), `<sym>$mv$<slug>` and mandatory `<sym>$mv$default` clone synthesis (`AXS-CPU-031`), common semantic contract and external `Win64` ABI preservation (`AXS-CPU-032`), deterministic descending feature-priority runtime dispatcher generation (`AXS-CPU-033`), and compile-time static dispatch elimination / LTO pruning / PGO profitability rules (`AXS-CPU-034`).
- Updated `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md` (`INV-SIMD-009` and `INV-SIMD-010`), and `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-022`, `AXS-EXT-032`, `AXS-EXT-054`, `AXS-EXT-060`, `AXS-EXT-091`, `AXS-EXT-130`).

## Files changed
- `spec/SPEC-44-cpu-features-multiversioning.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`
- `spec/SPEC-04-core-extensibility.md`

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `COVERAGE OK` (`0 gaps`, `0 problems`, exit 0)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK` (exit 0)
- `python tools/gatecheck.py --no-run` -> `MS-P1 PASS` .. `MS-P10b PASS` (exit 0)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T475` -> `0 REFUSED` lines (exit 0)

STATUS: COMPLETE round=0
