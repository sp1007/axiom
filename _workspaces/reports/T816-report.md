# T816 Report — E19.5 Canonical Documentation Generator (`axiomc doc`) & Integrated Test/Pass-Bisection Framework Specification (`SPEC-104`)

## Summary
Authored `spec/SPEC-104-docgen-test-framework-ux.md` and updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` to specify Phase 19 Epic E19.5 (`T816`–`T819`):
1. **Canonical Documentation Generator (`axiomc doc` — `AXS-DOC-001..012`)**:
   - Unified `CompilerDB` (`SPEC-21`) and lossless CST trivia (`SPEC-101`) extraction for `///` item and `//!` module doc comments with zero mandatory codegen and zero impact on production binaries (`REQ-TOOL-187`).
   - Canonical `SPEC-101` item signature rendering (`=` and `.` only) with `CapabilityBadge` (`owns`, `view<T>`, `mut_view<T>`, `Send`, `Share`), `ApiEffectSummary` (`allocates`, `blocks`, `synchronizes`, `panics`, `invalidates_views`, `complexity`), and `ContainerContract` (`SPEC-103`) badges.
   - Compiler-checked intra-doc `[module.Item]` link resolution emitting `AX_NAME_UNRESOLVED` (`data.context = "doc_link"`).
   - Deterministic offline static HTML output (`target/doc/`), machine-readable `doc-graph.json`, client-side `search-index.json`, and the `axiomc doc --test` executable doc-test runner (`compile_fail` blocks verified with `PoisonTaint` cascade suppression `REQ-TOOL-298`).
2. **Integrated Test Runner (`axiomc test` UX 2.0) & MIR Differential Oracle (`AXS-TST-001..012`)**:
   - First-class `test "name" { ... }` and `@test fn` discovery (`ATEST-20`), isolated test harness compilation, and build-feature semantic invariance (`REQ-TOOL-002`).
   - Parallel multi-worker execution (`--jobs <N>`), deterministic `--seed <u64>` replay, and `--format human|json|ndjson` output.
   - `Verified MIR` reference interpreter (`axiomc test --interp`, `REQ-TOOL-009`), zero production runtime oracle dependency (`REQ-TOOL-003`), and differential harness (`axiomc test --diff`) comparing `--interp` against native execution across `-O0`, `-O2`, and `-O3`.
3. **Optimization Pass Replay & Automatic $O(\log_2 M)$ Pass Bisection (`AXS-TST-020..022`, `REQ-TOOL-179`)**:
   - Deterministic 1-based pass execution index `1..M` across `OptIR`, `LIR`, and Machine IR pipelines with `--opt-bisect-limit=<N>` cutoff.
   - Automatic binary-search pass bisection (`axiomc test --opt-bisect <test_filter>`) isolating the exact first miscompiling pass $K^*$ and function in $\lceil \log_2(M + 1) \rceil$ steps and dumping `ProofCertificate` / `TranslationWitness` artifacts (`SPEC-25`).
   - Self-contained `.axreplay` bundle capture and replay (`axiomc test --opt-replay=<bundle.axreplay>`).
4. **Target-Independent Debug/Trace Architecture & `--audit-debug` (`AXS-TST-030..035`)**:
   - Target-independent `SemanticDebugModel` (`REQ-TOOL-007`) lowering to COFF/PE `.debug_line` at `-O0` (`REQ-TOOL-010`) and tiered DWARF v5 / CodeView across `-O1..-O3` (`REQ-TOOL-011`).
   - Logical inlined call-frame preservation (`REQ-TOOL-006`), honest `OptimizedOut` variable reporting without artificial register spills or suppressed dead-store elimination (`REQ-TOOL-005`), zero-cost disabled trace points (`REQ-TOOL-008`), and integrated `axiomc test --audit-debug` verification (`REQ-TST-112`).
5. **Index, Diagnostics, and Invariants**:
   - Registered `SPEC-104`, `AXS-DOC-NNN`, and `AXS-TST-NNN` in `spec/INDEX.md`.
   - Documented E19.5 diagnostic reuse (`NAME`, `DRIVER`, `IO`, `VERIFY`, `ICE`) in `spec/diagnostics.md` (`AXD-021`).
   - Added Section 50 (`INV-DOC-001` for `T817`, `INV-TST-001` for `T818`, `INV-TST-002` for `T819`) in `spec/invariants.md`.

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T816`: all modified files within allowed `paths:` and `locks:`.

## Files changed
- spec/SPEC-104-docgen-test-framework-ux.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

STATUS: COMPLETE round=0
