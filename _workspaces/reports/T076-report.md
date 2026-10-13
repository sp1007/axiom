# T076 — Self-hosting plan: feature audit, compiler layout, differential strategy

## Summary of Work
Authored canonical specification `spec/SPEC-20-selfhost.md`, audited the self-host language and standard library subset, defined the canonical `compiler/` layout mirroring `bootstrap/axiom0/src/`, performed the port split of T077–T085 into 23 bite-sized sub-tasks (≤ 1,500 LOC Axiom each), established the model assignment policy (`opus` for semantic passes, `sonnet` elsewhere), defined differential artefacts and harness entry points, fixed the multi-stage self-compilation resource budget, and re-pathed post-self-host tasks to `compiler/<module>`.

1. **Canonical Specification `spec/SPEC-20-selfhost.md`**:
   - Vietnamese `## Tóm tắt` overview for project owner.
   - Core self-hosting principles and architectural rules `AXS-SELF-001` through `AXS-SELF-013`.
   - Complete 1:1 directory layout matching `bootstrap/axiom0/src/` across all 20 compiler modules.
   - Exact differential artefact mapping for each compilation stage (`inspect --emit=tokens|ast|hir|thir|mir|mir-opt|lir|obj` and PE executable image bytes).
   - Multi-stage bootstrap ladder (Stage 0 -> Stage 1 -> Stage 2 -> Stage 3) with exact resource budgets:
     - `axiom0` -> `axiomc1`: < 2 min wall time, < 2 GB peak RAM.
     - `axiomc1` -> `axiomc2` (self-compile): < 10 min wall time, < 4 GB peak RAM.
     - Standard compilation flags: `-O1 --stack-reserve 67108864`.
   - Fixed-point byte identity and reproducibility requirements.
   - Freeze protocol (`axiom0-frozen` tag, `AX0-FIX` commit gate rule).

2. **Feature Audit (`spec/selfhost-subset.tsv`)**:
   - Re-audited all 72 features from `F-INT` to `F-STD-OS.CLOCK`.
   - Verified that every required feature has been implemented, validated natively, and tested across standard conformance and real-world program suites (`T075`).
   - Audit result: **0 feature gaps**. Zero gap tasks required.

3. **Port Split (ADR-0005 §8)**:
   - Split each of T077–T085 into sub-tasks of ≤ 1,500 lines of Axiom:
     - **T077**: `T077a` (kernel), `T077b` (source DB), `T077c` (diagnostics emitter); `T077` integration & differential task.
     - **T078**: `T078a` (lexer scanner); `T078` integration & differential tokens task.
     - **T079**: `T079a` (AST data structures), `T079b` (recursive-descent parser); `T079` integration & differential AST task.
     - **T080**: `T080a` (resolver & module graph), `T080b` (HIR lowering); `T080` integration & differential HIR task.
     - **T081**: `T081a` (types & layout), `T081b` (trait solver & mono), `T081c` (typeck & inference); `T081` integration & differential typeck task.
     - **T082**: `T082a` (MIR builder), `T082b` (ownership & definite init), `T082c` (capabilities), `T082d` (drop elaboration), `T082e` (MIR verifier); `T082` integration & differential MIR task.
     - **T083**: `T083a` (MIR interpreter & host oracle), `T083b` (MIR optimizer); `T083` integration & differential interpreter & optimizer task.
     - **T084**: `T084a` (LIR builder), `T084b` (Win64 ABI), `T084c` (isel & frame), `T084d` (x64 encoder); `T084` integration & differential backend task.
     - **T085**: `T085a` (COFF writer), `T085b` (PE linker), `T085c` (compiler driver); `T085` integration & differential driver task.
   - Assigned `model: opus` to all semantic sub-tasks (types, traits, ownership, capability, drop, MIR build, verifier, interpreter, optimizer); `model: sonnet` to others.

4. **Post-Self-Host Tasks Re-Pathing**:
   - Re-pathed `T058`, `T063`, `T064`, `T066`, `T067`, `T068`, `T750`, `T751` to canonical `compiler/<module>` layout.

## Files changed
- spec/SPEC-20-selfhost.md
- ./_workspaces/tasks/todo/T058-dyn-trait-vtables-and-dynamic-dispatch.md
- ./_workspaces/tasks/todo/T063-linear-scan-register-allocation.md
- ./_workspaces/tasks/todo/T064-optimizer-ladder-2-copy-propagation-inlining-sroa.md
- ./_workspaces/tasks/todo/T066-linux-x86-64-sysv-abi-elf64-writer-static-elf-link.md
- ./_workspaces/tasks/todo/T067-linker-v2-separate-compilation-multiple-objects-ar.md
- ./_workspaces/tasks/todo/T068-windows-unwind-info-pdata-xdata-and-panic-backtrac.md
- ./_workspaces/tasks/todo/T076-self-hosting-plan-feature-audit-compiler-layout-di.md
- ./_workspaces/tasks/todo/T077-port-kernel-source-db-diagnostics-to-axiom.md
- ./_workspaces/tasks/todo/T077a-port-kernel-to-axiom.md
- ./_workspaces/tasks/todo/T077b-port-source-db-to-axiom.md
- ./_workspaces/tasks/todo/T077c-port-diagnostics-to-axiom.md
- ./_workspaces/tasks/todo/T078-port-lexer-to-axiom-differential-tokens.md
- ./_workspaces/tasks/todo/T078a-port-lexer-to-axiom.md
- ./_workspaces/tasks/todo/T079-port-parser-ast-to-axiom-differential-ast.md
- ./_workspaces/tasks/todo/T079a-port-ast-data-model-to-axiom.md
- ./_workspaces/tasks/todo/T079b-port-parser-to-axiom.md
- ./_workspaces/tasks/todo/T080-port-resolver-hir-to-axiom.md
- ./_workspaces/tasks/todo/T080a-port-resolver-to-axiom.md
- ./_workspaces/tasks/todo/T080b-port-hir-to-axiom.md
- ./_workspaces/tasks/todo/T081-port-typeck-trait-solver-to-axiom.md
- ./_workspaces/tasks/todo/T081a-port-types-data-model-to-axiom.md
- ./_workspaces/tasks/todo/T081b-port-trait-solver-to-axiom.md
- ./_workspaces/tasks/todo/T081c-port-typeck-to-axiom.md
- ./_workspaces/tasks/todo/T082-port-ownership-mir-builder-drop-verifier-to-axiom.md
- ./_workspaces/tasks/todo/T082a-port-mir-builder-to-axiom.md
- ./_workspaces/tasks/todo/T082b-port-ownership-init-to-axiom.md
- ./_workspaces/tasks/todo/T082c-port-capability-to-axiom.md
- ./_workspaces/tasks/todo/T082d-port-drop-elaboration-to-axiom.md
- ./_workspaces/tasks/todo/T082e-port-mir-verifier-to-axiom.md
- ./_workspaces/tasks/todo/T083-port-interpreter-optimizer-to-axiom.md
- ./_workspaces/tasks/todo/T083a-port-interpreter-to-axiom.md
- ./_workspaces/tasks/todo/T083b-port-optimizer-to-axiom.md
- ./_workspaces/tasks/todo/T084-port-lir-x64-backend-encoder-to-axiom.md
- ./_workspaces/tasks/todo/T084a-port-lir-to-axiom.md
- ./_workspaces/tasks/todo/T084b-port-abi-to-axiom.md
- ./_workspaces/tasks/todo/T084c-port-isel-frame-to-axiom.md
- ./_workspaces/tasks/todo/T084d-port-encoder-to-axiom.md
- ./_workspaces/tasks/todo/T085-port-coff-writer-pe-linker-driver-axiomc.md
- ./_workspaces/tasks/todo/T085a-port-coff-writer-to-axiom.md
- ./_workspaces/tasks/todo/T085b-port-pe-linker-to-axiom.md
- ./_workspaces/tasks/todo/T085c-port-driver-to-axiom.md
- ./_workspaces/tasks/todo/T750-e18-7-static-libraries-coff-archive.md
- ./_workspaces/tasks/todo/T751-e18-7-pe-dll-output-import-library.md

## Verification
- `tools/archcheck.py`: 188 files scanned, 0 violations.
- `reqcov.py --strict`: 0 gaps, COVERAGE OK.
- `harness_check.py`: HARNESS OK.
- `taskctl.py validate`: OK (216 tasks).
- `taskctl.py lint`: All 46 task files pass lint cleanly.

STATUS: COMPLETE round=0
