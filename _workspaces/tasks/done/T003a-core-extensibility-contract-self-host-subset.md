---
id: T003a
title: Core extensibility contract + exact self-host subset (minimal C scope)
phase: P0-foundation
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T003]
priority: 12
status: done
attempts: 1
paths: [spec/SPEC-04-core-extensibility.md, spec/SPEC-00-bootstrap.md, spec/selfhost-subset.tsv]
timeout_min: 300
spec: [0263, tasks/0260, tasks/0494, 0152, 0056, 0054, 0161, 0162, 0163, spec/ROADMAP.md]
started: 2026-10-05 15:07:14
finished: 2026-10-05 15:20:07
---
# T003a — Core extensibility contract + exact self-host subset

## Goal
Make the C core small, fast and general (ROADMAP R7): axiom0 implements only what self-hosting needs,
but its data models are designed from day one so every later feature (P11–P22) plugs in without
redesign — "implement later ≠ design later" (0263 §42).

## Scope
- SPEC-04-core-extensibility.md: for each core data model — TypeKind, HIR/THIR nodes, MIR
  instructions/terminators/places, LIR, target description, object model, diagnostics — list the
  variants and fields reserved for later epics (async state machines E11.4, atomics & orderings
  E11.2, SIMD/vector types E12.3, raw pointers/volatile/address spaces E13.x, generators E14.3,
  dyn/vtables E14.4, GPU execution domains/device memory E22.x, other targets E16.x, debug info
  E17.x, query engine E18.1, **fixed-address declarations E13.6 / ADR-0001**: item placement
  attribute (overlay | place, const address), `fixed` provenance on places, `Volatile`/`Mmio` volatile
  MIR ops, absolute symbols and address-pinned sections in the object model). Say how each is represented (reserved enum values, extension tables,
  target hooks) and what axiom0 does on encountering it (clear "not supported in Stage-0" diagnostic,
  never a crash).
- SPEC-00-bootstrap.md: add the **exact self-host subset** — the features axiom0 must support to
  compile axiomc — with the rule that anything outside it belongs to post-T087 epics. Justify each
  inclusion by the compiler's needs (tasks/0260 §3-4).
- Artifact kinds as data: object model/driver/linker represent output kind (obj, exe, static lib, dynamic lib + import lib) and object/archive/image format independently; the core emits only obj/exe, E18.7 and E16.10 add writers without redesign (REQ-OWNER-006).
- **Self-host std subset**: the exact library surface axiomc needs (core, alloc/Box/Vec + sort, text/StringBuilder/formatting/parsing, ByteBuf LE writers, HashMap/HashSet, iterators, arenas + typed ID tables + interner, io/fs/path/dir listing/binary files/args/env/exit/monotonic clock) mapped to P9 tasks T069–T074, T073a; anything a P9 task lacks becomes a scope change filed now, not discovered at T076.
- Minimal raw pointers + `unsafe` blocks + memory intrinsics are in the self-host subset (T061a; std needs them); the full unsafe/UB model, volatile and MMIO stay in E13.1/E13.2. Slices (dynamic views) and `if let`/destructuring patterns are in the subset too (T048, T038).
- Scalars in the self-host subset: all integer widths, bool, unit, never, `char`; **no floating point** in axiom0 (f32/f64 → P12 E12.2, written in Axiom; axiom0 reports AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP). The compiler itself needs no floats.
- C-scope budget: rough size target per axiom0 module and the list of forbidden-in-C features.
- Subset items fixed by ADR-0002, ADR-0004 and ADR-0006 are listed explicitly: the host-interface intrinsic set with final names and signatures (SPEC-04); wrapping/bit intrinsics; `const` aggregate tables placed once in `.rdata` (no `static` items in axiom0); stored views; labelled `break`/`continue`; literal / char-range / or-patterns; `enum as uN`; `@derive(Copy, Clone, Eq, PartialEq, Ord, Hash)` and tuple `Eq`/`Ord`/`Hash`; generic drop glue with `drop_in_place`/`needs_drop`; `extern` items and `unsafe fn`; the `HashMap` insertion-order + hash contract; the const-evaluator interface (`types` never includes `interp`); the MIR text parser as C-only test infrastructure that is not ported.
- Every item of tasks/0260 §3 is marked in or out with a reason (`var` is excluded by the syntax rule; "comptime (limited)" = const items).
- `spec/selfhost-subset.tsv`: one row per subset feature — feature id, delivering task (oracle), native task, first consumer task. `tools/gatecheck.py` (T022) checks that each delivering task is an ancestor of its first consumer; T076 re-audits it.
- SPEC-04 also records the registry contracts of ADR-0005 §2: per-area diagnostic code files, command/emitter registration in the driver, option tables owned by commands/stages.

## Acceptance
- [ ] Every roadmap epic of P11–P22 that touches a core data model has an explicit extension point.
- [ ] Self-host subset list is concrete (feature-by-feature) and every P0–P10 task is consistent with it (list any task scope that should shrink; architect files the change).
- [ ] Report `_workspaces/reports/T003a-report.md` with exact `## Files changed`.
- [ ] `spec/selfhost-subset.tsv` exists; every row names existing board tasks and its delivering task is an ancestor of the consumer (checked by a few lines of Python in the report until gatecheck exists).
- [ ] tasks/0260 §3 in/out table present in SPEC-00.

## Out of scope
- Implementing anything.

## Notes
- Not a "critical, runs alone" task any more (ADR-0005 §11): ordered by `depends`; T010, T017, T023–T026 and T045 depend on it.
- ADRs: reserve the number with `python .claude/skills/axiom-tasks/scripts/taskctl.py adr-next <slug>` (never pick one by listing the directory) and list the ADR file in the report.

## Log
- 2026-10-05 11:52:51 started (attempt 1) T003a-impl
- 2026-10-05 14:19:43 requeue: quota (infrastructure failure: attempt refunded)
- 2026-10-05 15:07:14 started (attempt 1) T003a-impl
- 2026-10-05 15:20:07 accepted by QA -> done
