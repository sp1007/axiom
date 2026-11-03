# T223 — Plan Phase P23 (`v1.0 conformance, freeze & release`)

## Tóm tắt
Đã mở rộng toàn bộ Phase P23 (`P23-v1-0-conformance-freeze-releas` — *v1.0 conformance, freeze & release*) trong `spec/ROADMAP.md` §3 từ 3 epic (`E23.1`–`E23.3`) thành 11 task mới (`T1000`–`T1010`) kết hợp với task dựng sẵn `T091` đã được tinh chỉnh (tổng cộng 12 task trong P23). Toàn bộ 12 task trong P23 đều phụ thuộc vào `T223` và tất cả các cổng kiểm duyệt P11–P22 (`T311`–`T322`). Đồng thời đã chuyển đổi dòng `EPIC(E23.2)` (`REQ-CNF-001`) cùng 15 dòng yêu cầu thuộc P23 (`REQ-TOOL-001`, `REQ-CORE-021`, `REQ-TOOL-003`, `REQ-CORE-022`, `REQ-CONC-097`, `REQ-CAP-055`, `REQ-CORE-3133`–`REQ-CORE-3138`, `REQ-PKG-022`, `REQ-TST-112`, `REQ-ECO-8736`) trong `spec/requirements/CATALOG.md` sang danh sách các task cụ thể (`T091`, `T1000`–`T1010`, `T323`), qua đó đưa số lượng dòng `EPIC(...)` trong các tier `v1-core` và `v1-full` về đúng `0`. Đã nối cổng kiểm duyệt `T323` phụ thuộc vào toàn bộ task thuộc P23 (`T223`, `T311`–`T322`, `T091`, `T1000`–`T1010`), giữ nguyên `T224` và `T324` ở trạng thái `deferred`, và cập nhật nhật ký thay đổi tại `spec/ROADMAP.md` §2, §3, §5.

## Summary
Expanded Phase P23 (`P23-v1-0-conformance-freeze-releas` — *v1.0 conformance, freeze & release*) across epics `E23.1`–`E23.3` into 11 new concrete tasks (`T1000`–`T1010`) alongside refined pre-seeded task `T091` (12 tasks total), converted `EPIC(E23.2)` (`REQ-CNF-001`) and mapped 15 additional P23 `v1-full` requirements in `spec/requirements/CATALOG.md` to concrete task IDs (`T091`, `T1000`–`T1010`, `T323`), leaving `0` `EPIC(...)` rows in `v1-core` and `v1-full`, wired the P23 gate task `T323`, and updated `spec/ROADMAP.md` (§2, §3, §5).

### Task Breakdown by Epic (12 Tasks Total: `T091`, `T1000`–`T1010`)
All P23 tasks include `T223` and all P11–P22 gates (`T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322`) in their `depends:` chain. Each epic follows the 4-stage pipeline (`axiom-architect` spec → `axiom-semantics` / `axiom-backend` / `axiom-stdlib` implementation → `axiom-qa` conformance with `reviewer: axiom-architect`):

1. **E23.1 — Full conformance suite & compiler qualification (`T1000`–`T1003`, 4 tasks)** — *Src: `0017`, `0145`, `0150`, `tasks/0602` (`BOOTSTRAP-343`), `tasks/0605`, `tasks/0772`*
   - `T1000` (`axiom-architect`): Author `spec/SPEC-140-language-conformance-compiler-qualification.md` specifying the 3-level conformance suite architecture (Level 1 Positive Acceptance, Level 2 Negative Rejection & Diagnostic Precision, Level 3 Semantic Trace Verification), machine-readable rule-ID binding, and the 8-domain Compiler Qualification Profile (`AXQ-01`..`AXQ-08`).
   - `T1001` (`axiom-semantics`): Implement the machine-readable specification rule extractor, rule-to-test bidirectional coverage index, and Level 3 Semantic Trace Verifier (`src/sema/conformance_trace.*`).
   - `T1002` (`axiom-backend`): Implement the 8-domain Compiler Qualification Runner (`src/driver/qualification_runner.*`) and `axcert` CLI subcommands (`axcert run`, `axcert trace-verify`, `axcert qualify`) producing deterministic JSON/Markdown qualification reports (`src/driver/axcert_cmd.*`).
   - `T1003` (`axiom-qa`, `reviewer: axiom-architect`): Conformance & unit test suite (`tests/conformance/p23_e23_1_*.ax`, `tests/unit/conformance_qualification_test.cpp`).

2. **E23.2 — Global contradiction audit & spec freeze (`T091`, `T1004`–`T1006`, 4 tasks)** — *Src: `0151`, `0121`, `tasks/0603` (`BOOTSTRAP-344`), `tasks/1034`*
   - `T091` (`axiom-architect`): Refine pre-seeded task (`phase` normalized to `P23-v1-0-conformance-freeze-releas`) to author `spec/SPEC-141-global-contradiction-audit-spec-freeze.md` and `spec/RELEASE-v1.md` specifying the 15-axis Global Contradiction Audit protocol, 4-tier Frozen vs Evolving Semantic Boundary (`AXS-FRZ-001`..`012`), and Edition Interoperability Black-Box Contract.
   - `T1004` (`axiom-semantics`): Implement the Frozen Semantic Boundary enforcer and cross-edition black-box ABI/capability/ownership contract verifier (`src/sema/edition_boundary.*`).
   - `T1005` (`axiom-backend`): Implement the `aoracle 2.0` automated specification contradiction & invariant auditor (`src/driver/spec_audit.*`) verifying rule-ID uniqueness, diagnostic code consistency, and zero runtime footprint for oracle metadata (`REQ-TOOL-003`).
   - `T1006` (`axiom-qa`, `reviewer: axiom-architect`): Conformance & unit test suite (`tests/conformance/p23_e23_2_*.ax`, `tests/unit/spec_freeze_audit_test.cpp`).

3. **E23.3 — Release engineering (`T1007`–`T1010`, 4 tasks)** — *Src: `0145`, `others/0149`, `0150`, `0151`, `tasks/0604` (`BOOTSTRAP-345`), `tasks/0418`, `tasks/0423`*
   - `T1007` (`axiom-architect`): Author `spec/SPEC-142-release-engineering-versioning-installer-docs.md` specifying the 5-axis Versioning & Compatibility Policy, 4 Release Channels (`Nightly`, `Beta`, `Stable`, `LTS`), 5-layer Release Bundle format (`AXREL-01`..`05`), cryptographic provenance manifest, toolchain installer (`axup`), edition migration engine (`axiom migrate`), and offline docs bundle (`axiom doc --site`).
   - `T1008` (`axiom-backend`): Implement the deterministic multi-target release archive builder, channel qualification gate, and SHA-256 / Ed25519 provenance manifest generator (`src/driver/release_builder.*`).
   - `T1009` (`axiom-stdlib`): Implement the toolchain installer & channel manager (`src/tools/axup.*`), automated edition migration engine (`src/tools/migrate_cmd.*`), and static documentation site generator (`src/tools/doc_site.*`).
   - `T1010` (`axiom-qa`, `reviewer: axiom-architect`): Conformance & unit test suite (`tests/conformance/p23_e23_3_*.ax`, `tests/unit/release_engineering_test.cpp`).

### Requirement Coverage (`spec/requirements/CATALOG.md`)
- Converted `REQ-CNF-001` from `T091, EPIC(E23.2)` to `T091, T1004, T1005, T1006, T323`.
- Mapped 15 P23 `v1-full` requirements (`REQ-TOOL-001`, `REQ-CORE-021`, `REQ-TOOL-003`, `REQ-CORE-022`, `REQ-CONC-097`, `REQ-CAP-055`, `REQ-CORE-3133`–`REQ-CORE-3138`, `REQ-PKG-022`, `REQ-TST-112`, `REQ-ECO-8736`) to `T091`, `T1000`–`T1010`, and `T323`.
- Left `T224` and `T324` untouched (`status: deferred`).

## Files changed
- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md
- ./_workspaces/tasks/todo/T091-v1-0-conformance-audit-release-certification.md
- ./_workspaces/tasks/todo/T323-phase-p23-gate-v1-0-conformance-freeze-release.md
- ./_workspaces/tasks/todo/T1000-e23-1-language-conformance-semantic-trace-qualification-spec.md
- ./_workspaces/tasks/todo/T1001-e23-1-conformance-rule-db-semantic-trace-verifier.md
- ./_workspaces/tasks/todo/T1002-e23-1-compiler-qualification-runner-axcert-cli.md
- ./_workspaces/tasks/todo/T1003-e23-1-full-conformance-qualification-axcert-conformance.md
- ./_workspaces/tasks/todo/T1004-e23-2-frozen-semantic-boundary-edition-black-box.md
- ./_workspaces/tasks/todo/T1005-e23-2-spec-invariant-auditor-aoracle-20-cli.md
- ./_workspaces/tasks/todo/T1006-e23-2-contradiction-audit-freeze-conformance.md
- ./_workspaces/tasks/todo/T1007-e23-3-release-engineering-versioning-installer-docs-spec.md
- ./_workspaces/tasks/todo/T1008-e23-3-multi-target-release-builder-provenance-signer.md
- ./_workspaces/tasks/todo/T1009-e23-3-toolchain-installer-migration-engine-docs-site.md
- ./_workspaces/tasks/todo/T1010-e23-3-release-engineering-installer-docs-conformance.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P23-v1-0-conformance-freeze-releas --strict` → exited 0 (all 16 P23 requirements covered and verified).
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `requirements: 32308`, `v1-core implemented=5864`, `v1-full implemented=565 planned=8266` (`0` `EPIC(...)` rows remaining in `v1-core` or `v1-full`), `post-v1 epic=17535 planned=78`, `gaps: 0`, `COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T091`, `T323`, and `T1000`–`T1010` → `OK` on all 13 task files.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → `OK (598 tasks)`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → all checks passed.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T223` → 15 `ALLOWED` files, 0 `REFUSED` lines.

## Spec deviations
None.

## Follow-ups
None.

STATUS: COMPLETE round=0
