# Axiom canonical specification index

## Tóm tắt
Bản đồ của bộ spec chuẩn trong `spec/`: có những tài liệu nào (đã viết hay mới lên kế hoạch), mỗi tài
liệu gom những file nào trong `docs/base`, task nào sở hữu, trạng thái (bản nháp / chuẩn / đóng băng),
và ai dùng. Kèm danh sách ADR, các không gian mã (AXS-LEX, AXS-GRM, AXD, INV, mã chẩn đoán AX_…, REQ,
BOOT, epic E…), bảng chủ đề → nguồn chuẩn cho các vùng chưa có spec riêng, và các mâu thuẫn đã biết
trong tài liệu gốc.
Thứ tự ưu tiên khi các nguồn mâu thuẫn: ADR → spec chuẩn → skill axiom-syntax → tài liệu gốc mới hơn
hoặc đã đóng băng. Ba tài liệu nền là INDEX (file này), danh mục bất biến `spec/invariants.md` và
phân loại mã chẩn đoán `spec/diagnostics.md`.

Status: canonical (T002, 2026-10-04). Owner: axiom-architect. Updated by any architect task that has
`spec/INDEX.md` in its `paths:`/`locks:`, and at every phase-gate review.

## 1. Precedence and reading order

1. `spec/decisions/ADR-*.md`: resolved contradictions. They win over everything, including
   spec text written before them.
2. Canonical specs in `spec/` (table §2), with status `canonical` or `draft`. A draft is binding
   for its owner task and advisory for others until it is accepted.
3. `.claude/skills/axiom-syntax/SKILL.md`: binding surface syntax (`=` only, `.` only, `use`).
4. `docs/base/specs`, `docs/base/tasks`, `docs/base/others` (normative corpus). When they disagree,
   prefer the later document or the one marked FROZEN / "Audit & Freeze". `docs/base/discussions` is never normative.
5. Topic lookup in the corpus: skill `axiom-spec-index` (curated list, generated index).

Status values: **planned** (named by a board task, not written yet), **draft** (being written by a
task in `doing/`), **canonical** (accepted through a QA gate; changes need an architect task, and an
ADR when semantics change), **frozen** (v1.0 freeze at E23.2 / T091; nothing is frozen yet).

## 2. Canonical documents

| Document | Status | Owner task | Consolidates (docs/base) | Main consumers |
|---|---|---|---|---|
| `spec/ROADMAP.md` | canonical (binding baseline) | architect | 0152 §80-81, 0263 §51-52, tasks/0260, tasks/0262, all epic sources in its §3 | every planning task, gates |
| `spec/INDEX.md` (this file) | canonical | T002 | 0151 (contradiction audit), the curated list of axiom-spec-index | all agents |
| `spec/invariants.md` | canonical | T002 | 0153 §37, 0171 §40, 0172, tasks/0260 §45, tasks/0262 §42-49, tasks/0360 §51, 0151, 0263 §28/§46-47 | archcheck T006, gatecheck T022, QA, all engineers |
| `spec/diagnostics.md` | canonical | T002 | tasks/0360 (frozen), 0146 Part XXVII, 0153 §37, 0171 §40, 0172 §10-12, tasks/0262 §46 | T009, T016, T005, T006, every task that adds a code |
| `spec/SPEC-00-bootstrap.md` | draft | T003 (milestone ladder, manifests), T003a (exact self-host subset), T111 (coverage edits) | 0263, tasks/0262, tasks/0494, tasks/0260, 0152 | every core task (milestone blocks), gatecheck T022 |
| `spec/SPEC-01-lexical.md` | canonical | T001 | 0152 §12, 0154, 0155, 0173, 0243, 0109, tasks/0323, tasks/0324, tasks/0385, tasks/0476 | T010, T013, lexer port |
| `spec/SPEC-02-grammar.md` | canonical | T001 | tasks/0476 (v1.0 surface, frozen), 0155, 0174, 0243, tasks/0323, tasks/0386, 0109 | T011, T012, T013, T014/T015/T015b, parser port |
| `spec/SPEC-03-core-semantics.md` | draft | T003 | 0032, 0041, 0068, tasks/0327, 0010, 0263 | T017, T021, T030–T044 (types, literals, arithmetic, panics, exit codes) |
| `spec/SPEC-04-core-extensibility.md` | planned | T003a | 0056, 0054, 0161, 0162, 0163, 0263, tasks/0260, ROADMAP R7 | data-model tasks (HIR/types/MIR/LIR/objmodel), host intrinsics (ADR-0002) |
| `spec/selfhost-subset.tsv` | planned | T003a | tasks/0260, tasks/0494, ADR-0004, ADR-0006 | gatecheck T022 (rule d), T076 |
| `spec/SPEC-10-ownership.md` | planned | T045 | 0004, 0005, 0160, 0176, 0019, 0020, 0086, tasks/0394, 0263 | T018, T046, T047, T050 |
| `spec/SPEC-11-capability.md` | planned | T045 | 0177, 0021, 0028, tasks/0395, tasks/0541, tasks/0270 | T048, T048b, T050 |
| `spec/SPEC-12-drop.md` | planned | T045 | 0178, 0030, 0118, tasks/0674 | T049, T054b |
| `spec/SPEC-20-selfhost.md` | planned | T076 | 0167, 0150, tasks/0260, tasks/0261, tasks/0371, tasks/0473 | T077–T087 |
| `spec/BOOTSTRAP.md` | planned | T087 | 0167, tasks/0473, 0150 | trust chain, freeze rule (INV-BOOT-004) |
| `spec/RELEASE-v1.md` | planned | T091 | 0150, 0151, tasks/0602, 0121 | v1.0 release |
| `spec/requirements/OWNER.md` | canonical | owner / architect | owner decisions (REQ-OWNER-*) | everyone; never dropped silently |
| `spec/requirements/raw/C01.md` … `C18.md` | planned | T092 … T109 | the 18 extraction chunks of `docs/base` (`spec/requirements/chunks`) | T110 |
| `spec/requirements/CATALOG.md`, `spec/COVERAGE.md` | planned | T110 (then T111, planning tasks) | `spec/requirements/raw` | `reqcov.py`, every gate |
| `spec/decisions/` | canonical (append-only) | architect tasks; numbers from `taskctl.py adr-next` | — | everyone |

Specs for later epics (P11+) are created by the first task of each epic (ROADMAP §4 step 2) and added
to this table at the next INDEX update.

## 3. Decision register

| ADR | Title | Main effect |
|---|---|---|
| ADR-0001 | Fixed-address declarations (`@at`) | owner requirement; E13.6/E13.7; axiom0 parses `@at` and rejects it with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (spelling per ADR-0011 §3) |
| ADR-0002 | Oracle host interface | interpreter runs heap/OS code through host intrinsics (T061c); direct FFI native-only |
| ADR-0003 | Back-end pipeline robustness | ABI lowering on LIR, machine-IR verifier, stack probes, stack reserve (T025b) |
| ADR-0004 | Self-host subset additions | wrapping/bit intrinsics, constant tables, stored views, HashMap order and hash, generic drop glue, const-eval interface |
| ADR-0005 | Plan structure corrections | `native-after`, per-area diagnostic files and `locks:`, gate rule PASS/BLOCKED, task splits, follow-up ids |
| ADR-0006 | Bootstrap forms, manifest, std root | `impl Drop`, `u32 as char`, `len`, `axiom.toml`, std-root discovery |
| ADR-0007 | Canonical spelling | `=` only, `.` only, `use`, `module` |
| ADR-0008 | Statement termination | newline or `;`, one fixed parser rule, `NL_BEFORE` flag |
| ADR-0009 | Lexical decisions v0.1 | ASCII identifiers (revisit), keywords, literals, operators |
| ADR-0010 | Grammar forms v0.1 | types, precedence, statements, items, patterns |
| ADR-0011 | Diagnostic code taxonomy | named codes, 18 fixed areas, `_UNSUPPORTED_IN_BOOTSTRAP`, severities, ordering, streams, `INV-*` namespace, invariant `since:` |

## 4. Identifier namespaces

| Prefix | Meaning | Defined in |
|---|---|---|
| `AXS-LEX-NNN` | lexical rules | SPEC-01 |
| `AXS-GRM-NNN` | grammar rules | SPEC-02 |
| `AXD-NNN` | diagnostics rules | `spec/diagnostics.md` |
| `INV-<GROUP>-NNN` | architecture/semantic invariants | `spec/invariants.md` |
| `AX_<AREA>_<NAME>` | diagnostic codes (18 areas) | `spec/diagnostics.md` §3, §10–11; registry `bootstrap/axiom0/src/diag/codes/<AREA>.def` |
| `BOOT-NN` | milestone ladder entries | SPEC-00 (T003) |
| `REQ-…` | requirements (`REQ-OWNER-*` owner) | `spec/requirements/` |
| `E<phase>.<n>` | roadmap epics | ROADMAP §3 |
| `ADR-NNNN` | decisions | `spec/decisions/` |
| `Tnnn[a-z]` | board tasks | `_workspaces/tasks/` |
| `R01…`, `E01…`, `L01…`, `EX-nn` | example/conformance case numbers | local to SPEC-01/SPEC-02 |

Specs written later (SPEC-03, -04, -10, -11, -12, -20) declare their rule prefix in their header; the
prefix is added here at the next INDEX update. Prefix ids from the corpus (`AKERNEL-24`, `ABOOT-41`,
`ADIAG-22`, `ACAP-31` …) are cited only as sources, always together with the document number, because
the corpus reuses them (§6).

## 5. Topic → canonical source

| Topic | Canonical text today | Corpus sources (axiom-spec-index) |
|---|---|---|
| Plan, ladder, scope | ROADMAP, SPEC-00 | 0152, 0263, tasks/0260, tasks/0262, tasks/0494 |
| Surface syntax | SPEC-01, SPEC-02, axiom-syntax, ADR-0007..0010 | tasks/0476, 0154, 0155 |
| Kernel: IDs, arenas, interner, source DB | invariants §2, axiom-c-stage0 | 0153, 0171, 0172, tasks/0533, tasks/0479 |
| Diagnostics | `spec/diagnostics.md` | tasks/0360, 0146 |
| Resolver, HIR, modules | SPEC-02 §4, axiom-syntax (DottedChain), ADR-0006 §8 (std root) | 0156, 0244, tasks/0387, tasks/0357, tasks/0497 |
| Types, literals, arithmetic, panics | SPEC-03 (draft) | 0157, 0175, 0245, tasks/0388, tasks/0327, 0068 |
| Traits, generics | ADR-0004; task texts T053–T056 | 0158, 0212, tasks/0389, tasks/0611 |
| Ownership, capability, drop | invariants §8; SPEC-10/11/12 (T045) | 0160, 0176, 0177, 0178, tasks/0394, tasks/0395 |
| MIR, verifier, oracle | invariants §6–7; ADR-0002; SPEC-10..12 MIR requirements | 0161, 0227, 0247, 0027, 0025, 0031, 0145 |
| LIR, ABI, x86-64, COFF, PE | ADR-0003; skill axiom-x64-backend; SPEC-04 (object model, artifact kinds) | 0162, 0179, 0181, 0184–0187 |
| Tests and conformance | skill axiom-testing; ADR-0005 §1/§3 | 0166, 0017, 0022, 0026, 0114 |
| Self-hosting | SPEC-20 (T076), BOOTSTRAP.md (T087) | 0167, 0150, tasks/0259–0262, tasks/0371 |
| Fixed addresses, module-relative bindings | ADR-0001, OWNER.md | 0071, 0044, 0097, tasks/0328 |

## 6. Known inconsistencies in the corpus (already resolved)

| Issue | Sources | Resolution |
|---|---|---|
| Diagnostic code shape: `ETYPE_MISMATCH` vs `AX_TYPE_0001` vs `AX_NAME_0001` vs `AX1401` | tasks/0360 §3, 0146 §4, 0172 §10, tasks/0262 §46 | ADR-0011 §1: `AX_<AREA>_<NAME>` |
| Diagnostic namespaces differ (0146 §54 has 27, tasks/0360 §38 has 18) | 0146, tasks/0360 | ADR-0011 §2: 18 fixed areas, mapping in diagnostics §3 |
| `AX_ADDR_*` used by ADR-0001, SPEC-02 AXS-GRM-037 and axiom-syntax, but ADDR is not an area | ADR-0001, SPEC-02 | ADR-0011 §3: `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`data.construct = "@at"`), `AX_UNSAFE_AT_HOSTED` |
| Severity sets differ (Error/Warning/Info/Hint vs Error/Warning/Note/Help) | tasks/0360 §2, 0146 §3, 0172 §10 | ADR-0011 §4: four severities in the schema; note/help are attachments |
| `ADIAG-20…` numbers mean different things in 0146, 0153 and tasks/0360 | 0146 §65, 0153 §37, tasks/0360 §51 | ADR-0011 §8: own `INV-*` ids; corpus ids cited with the document number |
| Ladder numbering `BOOT-00…14` (summary list) vs `BOOT-00…37` (section headings) inside tasks/0262 | tasks/0262 §2 vs §3–§43 | SPEC-00 (T003) owns the BOOT map |
| Early docs: bootstrap via LLVM, ELF as the first target; later docs: no LLVM, Windows PE first | 0152 early sections vs 0263, 0172, 0181 | project decision (CLAUDE.md, axiom-spec-index): C11 axiom0, no LLVM, Windows x64 PE first |
| Async/GPU before self-hosting (0152 §80) vs core-first ladder | 0152 §80 vs 0263 §51, tasks/0262 | ROADMAP R2 |

## Sources
0151 (global contradiction audit); 0152; 0263; tasks/0260; tasks/0262; tasks/0360; 0146; 0153; 0171;
0172; skill axiom-spec-index; `spec/ROADMAP.md`; board task files (`paths:` and `spec:` fields of
T001, T002, T003, T003a, T045, T076, T087, T091, T092–T111).
