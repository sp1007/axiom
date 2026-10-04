# T002 report

## Summary
Spec-only task. Three canonical documents and one ADR were written:

- `spec/INDEX.md`: the map of the canonical spec set. It lists every existing and planned spec with
  its status (planned / draft / canonical / frozen), owner task, the docs/base files it consolidates,
  and its consumers. It also has the precedence order, the ADR register (0001–0011), the identifier
  namespaces, a topic → canonical-source table, and the corpus inconsistencies already resolved.
- `spec/invariants.md`: 49 invariants with ids `INV-<GROUP>-NNN` in 10 groups: KERN, LAYER, DIAG, DET,
  PIPE, ORACLE, SEM, BOOT, plus LEX/GRM for the invariants SPEC-01/02 already state.
  - Each invariant has the machine-readable fields `statement`, `source`, `verify` (a test directory
    or tool), `since` (the task that delivers the check) and `check`.
  - §1 defines the format and the gatecheck rules IG-1…IG-4 that T022 implements. The `since` field
    lets invariants of later phases be catalogued before their tests exist: once the `since` task is
    done, the `verify` paths must exist.
  - Every `verify` path was taken from the `paths:` of the named task.
- `spec/diagnostics.md`: the diagnostics taxonomy, rules `AXD-NNN`.
  - Code shape `AX_<AREA>_<NAME>`. The area list is exactly the T002 scope list (LEX, PARSE, NAME,
    TYPE, TRAIT, PAT, MOVE, INIT, CAP, DROP, UNSAFE, CONST, VERIFY, FFI, LINK, IO, DRIVER, ICE), one
    `.def` file each, and adding an area needs an edit of this spec first.
  - Also covered: registry order and seeding, severity policy and exit codes, ICE handling, the stage
    barrier against cascades, the data model, the fix-it model, the human format, JSON schema 1, and
    the ordering key.
  - Seed list for P1–P4 with a one-line meaning and an example per code: 19 LEX, 25 PARSE, 9 NAME,
    13 TYPE, 8 VERIFY, 4 IO, 7 DRIVER, 5 LINK, 3 ICE. LEX and PARSE are taken unchanged from SPEC-01
    and SPEC-02 in their table order.
  - Names already fixed for later tasks (§11): T030, T038, T038b, T046, T061, T061a, T060, T065, E13.6.
- `spec/decisions/ADR-0011-diagnostic-code-taxonomy.md`, reserved with `taskctl.py adr-next`, records
  ten decisions:
  1. named codes, not numeric;
  2. the fixed 18 areas, with the corpus namespaces mapped onto them;
  3. `AX_ADDR_UNSUPPORTED_STAGE0` → `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`data.construct="@at"`),
     `AX_ADDR_HOSTED` → `AX_UNSAFE_AT_HOSTED`, and the suffix `_UNSUPPORTED_IN_BOOTSTRAP`;
  4. four severities in the schema, only error/warning emitted by axiom0, ICE as an area with exit 3;
  5. ties broken by registry ordinal rather than alphabetical order (needed by SPEC-01 AXS-LEX-101);
  6. a stage barrier against cascades (Revisit at E19.4);
  7. both output formats on stderr;
  8. an own `INV-*` namespace, because the corpus reuses ADIAG numbers in 0146, 0153 and tasks/0360;
  9. T009 seeds the whole P1–P4 list;
  10. the invariant `since:` field.

Coordination: T003-impl asked about its codes. I accepted its TYPE and CONST names. INTERP is not an
area, so `AX_INTERP_*` became `AX_DRIVER_INTERP_STEP_LIMIT`, `AX_DRIVER_INTERP_STACK_LIMIT` and
`AX_UNSAFE_INTERP_UB`. I sent T003-impl these names and wrote them into diagnostics §10.7/§11 and ADR-0011.

## Files changed
- spec/INDEX.md
- spec/invariants.md
- spec/diagnostics.md
- spec/decisions/ADR-0011-diagnostic-code-taxonomy.md
- _workspaces/reports/T002-report.md

## Tests
Spec-only task: no build and no test suite yet (T004/T005 not done).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → OK (155 tasks).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → HARNESS OK. It first flagged the stale
  phrase "Linux ELF first" in INDEX §6; I reworded it.
- All new files are UTF-8 with LF (0 CR bytes). Invariant ids are unique (49 blocks, no duplicates).
- `taskctl.py snapshot T002` includes the three files under `paths`. The ADR is under `spec/decisions`,
  created by `adr-next`.

## Spec deviations
These texts use spellings that ADR-0011 replaces. The ADR wins under the precedence rule. I did not edit
these files because they are outside T002's paths:
- SPEC-02 AXS-GRM-037 and ADR-0001 use `AX_ADDR_UNSUPPORTED_STAGE0` / `AX_ADDR_HOSTED`;
- the axiom-syntax skill (line 179) uses the same;
- the axiom-c-stage0 skill uses `AX_*_UNSUPPORTED_STAGE0`.
T009's "(file, offset, code)" order is refined: "code" means the registry ordinal (AXD-060).

## Follow-ups
- Text sync (architect, next touch of each file, or a small T112+ task): rename the `@at` codes in
  SPEC-02 AXS-GRM-037, ADR-0001 §Consequences and axiom-syntax SKILL.md, and the unsupported-code suffix
  in axiom-c-stage0 SKILL.md.
- T006 (archcheck): add the rules for INV-LAYER-005 (lir/abi/target/objmodel/obj/link never include
  lex/syntax/resolve/hir) and INV-LAYER-008 (no C sources under `std/`) to its scope or acceptance.
- T022 (gatecheck): implement invariants rules IG-1…IG-4 (the `since:` semantics) as the meaning of
  scope item (a).
- T009: seed the whole §10 list in order, add the registered-codes golden (INV-DIAG-002), and use
  ordering key AXD-060.
- T016: send diagnostics to stderr in both formats (AXD-061), and use exit code 2 only for the four
  usage codes (AXD-043).

STATUS: COMPLETE round=0

## Round 1

### Fixes for the QA findings
- **F1.** `spec/diagnostics.md` AXD-030 now cites INV-LAYER-007 ("Diagnostic codes registered in
  their area file") instead of INV-LAYER-008. I grepped every `INV-*` reference in diagnostics.md,
  INDEX.md, invariants.md and ADR-0011, and the others are correct:
  - INDEX → INV-BOOT-004;
  - ADR-0011 → INV-LAYER-005, INV-LAYER-008 and INV-DIAG-002;
  - INV-PIPE-001 ↔ INV-LAYER-005.
- **F2.** Two statements in the round-0 report were wrong:
  - The catalogue has **48** invariants (KERN 7, LAYER 8, DIAG 8, DET 4, PIPE 5, ORACLE 3, SEM 6,
    BOOT 4, LEX 2, GRM 1), not 49.
  - Not every `verify:` path lies in the `paths:` of its `since` task. Each one lies in the `paths:`
    of the `since` task or of a task in its `depends` closure, or is an existing harness script.
  `spec/invariants.md` now says this explicitly:
  - IG-3 allows such paths and requires the `check:` line to name the delivering task.
  - The six cases name it:
    - INV-KERN-004: T007 ← T017
    - INV-DIAG-005: T009 ← T016
    - INV-DIAG-008: T011 ← T017
    - INV-ORACLE-001: T021 ← T034
    - INV-BOOT-001: T011 ← T034
    - INV-BOOT-004: the existing `harness_check.py`; T087 creates the tag that activates it

### Notes addressed
- N1: added `AX_ASYNC_` to the "no area in v0.1" group (AXD-021).
- N2: removed the wrong citation 0171 AKERNEL-25 from INV-KERN-002.
- N3: added blank lines before AXD-014 and AXD-043, so they render as separate paragraphs.
- N4: kept as is. The choice is stated explicitly in §7; a SPEC-02 cross-reference is left for its next edit.
- N5: follow-up for T005: the runner reads the `--json` document from **stderr** (AXD-061, §9).
- N6: harness note for the orchestrator. `taskctl changes` drops the leading `_` of report paths; it
  still stages the right file.

### Checks
`harness_check.py`: HARNESS OK. Both edited files have 0 CR bytes. `grep -c "^### INV-[A-Z]"
spec/invariants.md` gives 48.

## Files changed
- spec/INDEX.md
- spec/invariants.md
- spec/diagnostics.md
- spec/decisions/ADR-0011-diagnostic-code-taxonomy.md
- _workspaces/reports/T002-report.md

STATUS: COMPLETE round=1
