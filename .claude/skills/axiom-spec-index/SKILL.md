---
name: axiom-spec-index
description: Find the normative Axiom design text for any compiler topic inside the huge docs/base corpus (~1060 files, 37 MB of specs/tasks) and resolve which document wins when they disagree. Use before implementing or reviewing any Axiom compiler task, when a task lists spec references, when you need "what does the spec say about X" (lexer, grammar, resolver, types, traits, ownership, view/capability, drop, MIR, verifier, interpreter, LIR, x86-64, Windows ABI, COFF/PE, ELF, linker, runtime, std), or when two specs contradict each other.
---

# Axiom spec lookup

**Normative vs non-normative.** `docs/base/specs/`, `docs/base/tasks/`, `docs/base/others/` hold
conclusions that were already debated and lightly critiqued — they are normative.
`docs/base/discussions/` is brainstorming only: never treat it as a requirement or decision; use it
at most as background when a normative text is unclear.

Requirements catalogue and traceability (which board task implements which goal of the corpus):
`spec/requirements/CATALOG.md`, `spec/COVERAGE.md`, checked by
`python .claude/skills/axiom-tasks/scripts/reqcov.py`. The extraction procedure is in
`references/requirements-extraction.md` — read it when working on T092–T111 or a phase review.

The corpus is too large to read. Read **only** what the task needs, in this priority order:

1. `spec/` — canonical, consolidated specs written by the axiom-architect agent (authoritative once
   present). `spec/decisions/ADR-*.md` record resolved contradictions — they win over everything.
2. `.claude/skills/axiom-syntax/SKILL.md` — binding surface-syntax rules (`=` for binding and
   assignment, `.` as the only path separator). Wins over any syntax in `docs/base`.
3. The curated reading list below (the documents that actually drive the implementation).
4. `references/index.md` — generated topic index of every file (grep it by topic keyword).
5. Content search: `Grep` over `docs/base/specs` / `docs/base/tasks` for the exact term
   (e.g. `AKERNEL-`, `AX_MOVE`, `shadow space`). Read excerpts with offset/limit, not whole files.

## Why the ordering

The corpus grew chronologically through many design passes. Later documents usually supersede
earlier ones, several topics were re-frozen 3–5 times, and some directions were reversed (e.g.
early docs say "bootstrap via LLVM", later ones forbid LLVM; early docs target Linux ELF first,
0181 re-targets Windows PE64 first because development happens on Windows). Reading an early doc
alone produces confident but wrong implementations.

## Project-level decisions already fixed (do not relitigate)

- Owner requirements `spec/requirements/OWNER.md` (REQ-OWNER-*) and the binding roadmap
  `spec/ROADMAP.md` (phases, epics, R1–R7: minimal C core, axiom0 frozen after self-hosting T087).

- Stage-0 compiler `axiom0` is written in **C11** (`bootstrap/axiom0/`), no LLVM, no external
  assembler or linker in the production path (docs 0263, 0172, 0181). Using clang/llvm-objdump **as
  test oracles** (to validate our bytes/objects) is fine.
- First target **x86_64-windows (MS x64 ABI, COFF → PE32+)**, second **x86_64-linux (SysV, ELF64)**
  testable through WSL (doc 0181).
- Pipeline: Source → Lexer → Parser → AST → Resolver → HIR → Typeck → Typed HIR → Ownership/
  Capability → MIR (+Drop elaboration) → Verifier → Verified MIR → {Oracle interpreter | Optimizer →
  LIR → Machine IR → Encoder → Object → Linker → Executable} (doc 0152).
- Build vertically: every feature goes through the whole pipeline with tests before the next one.
- Diagnostics are data (`code, severity, primary span, labels, notes, fixes`); spans are
  FileId + byte range.

## Curated reading list by stage (docs/base/specs unless noted)

| Stage | Primary docs |
|---|---|
| Plan / ladder | 0152 blueprint, 0263 Stage-0 decisions, tasks/0262 ladder, tasks/0260 self-host subset, tasks/0494 bootstrap subset, 0172 impl principles |
| Kernel (IDs, arena, interner, source DB, diagnostics) | 0153, 0171, 0172, tasks/0533, tasks/0479 |
| Lexer | 0154, 0173, tasks/0324, tasks/0385 |
| Grammar / parser / AST | tasks/0476 (v1.0 surface, frozen), 0155, 0174, 0243, tasks/0323, tasks/0386 — apply axiom-syntax |
| Resolver / HIR / modules | 0156, 0244, tasks/0387, tasks/0357, tasks/0497, 0103, 0108 |
| Type system / inference | 0157, 0175, 0245, tasks/0388, tasks/0482, tasks/0500 |
| Traits / generics | 0158, 0212, 0046, tasks/0389, tasks/0611, tasks/0506 |
| Typed HIR / expressions / control flow / patterns | 0159, 0041, 0063, 0065, tasks/0391, tasks/0392 |
| Ownership / init / places | 0160, 0176, 0246, 0019, 0020, tasks/0394, tasks/0503 |
| Capability / view / regions | 0177, 0021, 0028, tasks/0395 |
| Drop elaboration / cleanup | 0178, 0030, 0118, tasks/0674 |
| MIR | 0161, 0227, 0228, 0247, 0024, tasks/0393, tasks/0539 |
| Verifier | 0027, 0029, 0034, 0035, tasks/0365 |
| Oracle / MIR interpreter | 0025, 0031, 0145 |
| Error / panic / Result | 0068, 0107, 0222, 0229, tasks/0288 |
| Optimizer | 0165, 0226, 0074 |
| LIR / ABI / layout | 0162, 0179, 0215, 0230, 0231, 0232, 0250, 0043 |
| x86-64 machine IR / isel / regalloc | 0163, 0180, 0182, 0183, 0233–0235, 0251, 0252, 0253 |
| Windows x64 ABI / encoder / COFF / PE | 0181, 0184, 0185, 0186, 0187, 0189 (unwind 0188, CodeView 0190, PDB 0191 later) |
| Linux ELF | 0192, 0053, 0197, 0255, 0256 |
| Linker / driver / toolchain | 0164, 0217, 0256, 0257, 0099 |
| Runtime / std / intrinsics | 0169, 0170, 0219, 0258, 0045, 0087–0089 |
| Conformance / harness / tests | 0166, 0017, 0022, 0026, 0114, 0145 |
| Bootstrap / self-hosting | 0167, 0150, tasks/0259–0262, tasks/0371 |
| Contradiction audits | 0151, 0110, 0121, 0016 |

Application-domain documents (AI serving, finance, GUI, audio…) are not compiler work; they are
listed under "XX" in `references/index.md` and triaged once as `post-v1` requirements (chunk C18).
Note that GPU, other targets, async, threads, LSP etc. ARE part of the v1 specs (tier `v1-full`).

## When documents conflict

1. Prefer `spec/decisions/` → `spec/` → axiom-syntax → the later/frozen doc (look for
   "FROZEN", "Audit & Freeze", "Consistency Pass", "Contradiction Audit").
2. If still ambiguous and the choice changes observable semantics, do not pick silently: the
   engineer stops and hands the question to axiom-architect, who writes an ADR
   (`spec/decisions/ADR-NNNN-<slug>.md`: context, options, decision, consequences, source docs).
   The architect decides autonomously — the project runs unattended, so never block waiting for the
   human.

Regenerate the index after docs change: `python .claude/skills/axiom-spec-index/scripts/build_index.py`.
