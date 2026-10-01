# Requirement extraction & traceability procedure

Used by tasks T092–T111 (axiom-architect) and by every later phase review. Goal: every goal and
decision stated in the normative corpus is either planned by a board task, merged as a duplicate,
consciously deferred (post-v1) or rejected by an ADR — nothing silently dropped.

## What is normative

| Source | Weight |
|---|---|
| `docs/base/specs/`, `docs/base/tasks/`, `docs/base/others/`, `docs/base/init prompt.txt` | **Normative**: conclusions that were already debated and lightly critiqued. Extract requirements from these. |
| `docs/base/discussions/` | **Non-normative**: brainstorming only. Never extract requirements from it; read only as background when a normative text is unclear. |
| Owner decisions (CLAUDE.md, axiom-syntax) | Override everything. |

Owner requirements live in `spec/requirements/OWNER.md` (REQ-OWNER-*): they are copied into the
catalogue unchanged and override conflicting corpus rows.

## Phase A — per-chunk extraction (one task per chunk, `spec/requirements/chunks/Cnn.txt`)

Chunks are ~2 MB: far too much to read line by line. For each file:
1. Read the title, headings (`grep -n '^#'`) and the closing sections ("Kết luận", "Invariants",
   "Frozen", "Quyết định", "Acceptance", "Gate", "MUST/SHALL/phải/không được").
2. Read in full only the passages that state decisions, invariants, rule IDs (`AKERNEL-24`,
   `ABOOT-41`, `AXIOM-BOOT-001`…), required behaviours, required tests, or milestones.
3. Skip pure explanation, repeated background and speculative "có thể/sau này" material, unless it
   is phrased as a commitment.

**Work incrementally.** A chunk is ~100 files; your context may be compacted or the task restarted
part-way. Create `raw/Cnn.md` at the start, append rows and add the file to `## Files skimmed`
after every few files, so the file on disk is always the complete state. On (re)start read the
existing `raw/Cnn.md` and continue with the files not yet listed; dedup within the chunk at the
end.

Write `spec/requirements/raw/Cnn.md` with one table of six columns (the catalogue later adds a
`needs` column before `status`):

```
| RQ-Cnn-001 | ownership | v1-core | Partial move of a field leaves the parent PARTIAL; using the parent afterwards is an error unless the field is re-initialised | 0160 §12; tasks/0394 §7 | T046 |
```

- **id**: provisional `RQ-Cnn-NNN`.
- **area**: one of lexical, grammar, resolve, module, types, traits, generics, expr, pattern,
  ownership, capability, drop, mir, verifier, oracle, error, comptime, optimizer, abi, layout,
  lir, x64, target-other, object, linker, runtime, core-lib, std-lib, text, collections, numeric,
  simd, concurrency, async, atomics, ffi, gpu, build, package, driver, diagnostics, tooling,
  debug, testing, conformance, bootstrap, security, ecosystem.
- **tier**: `v1-core` = needed to reach a self-hosting compiler; `v1-full` = part of Axiom v1.0
  as specified (e.g. async, threads, GPU model, other targets, LSP); `post-v1` = ecosystem/
  application-domain or explicitly future material.
- **statement**: one testable sentence in English, canonical syntax in any code (`=`, `.`).
- **sources**: doc numbers + section (e.g. `0181 §3`, `tasks/0476 217.25`). List several when the
  same requirement recurs — duplicates across docs are expected and are the main thing Phase B
  collapses.
- **status**: best-guess existing board task id(s) that would implement it (read
  `taskctl.py list`), else the roadmap epic `EPIC(E12.3)` from `spec/ROADMAP.md` §3, or `GAP`.
- **needs** (inside the statement cell): when the text says a requirement is built on, uses or
  requires another one ("Vec<T> is built on raw pointers"), end the statement with
  `[needs RQ-Cnn-NNN, …]` (or a short description if the other requirement is in another chunk).
  T110 turns these into the catalogue's `needs` column. This is what lets `reqcov.py` detect
  "planned, but too late" — a feature scheduled after the task that needs it.
- **Tier discipline**: mark `v1-core` only what the self-hosting compiler or the self-host std
  subset really needs (check `spec/SPEC-00-bootstrap.md` and `spec/selfhost-subset.tsv` when they
  exist). A `v1-core` row may only be mapped to P0–P10 tasks: mapping it to `EPIC(E11+)` is an error
  that reqcov reports — either the tier or the plan is wrong, say which in `## Conflicts`.

Also record at the bottom `## Conflicts` — requirements in this chunk that contradict each other or
the canonical `spec/` (with sources) — and `## Files skimmed` (count; any file you could not read).

Ecosystem chunks (application domains): one row per document at most, tier `post-v1`, area
`ecosystem`, statement summarising what the language/runtime must *enable* for that domain (e.g.
"std must expose a stable C ABI and threads so GUI toolkits can bind"). Language-level requirements
found inside them (rare) are extracted normally.

Target volume: typically 40–150 rows per chunk. Precision beats volume — one well-sourced row
covering five documents is better than five rows.

## Phase B — consolidation (T110)

1. Merge all raw tables; cluster by area; collapse duplicates into a single requirement with the
   union of sources; assign final ids `REQ-<AREA>-NNN` (AREA uppercase short: LEX, GRM, RES, MOD,
   TYP, TRT, GEN, EXP, PAT, OWN, CAP, DRP, MIR, VER, ORC, ERR, CTM, OPT, ABI, LAY, LIR, X64, TGT,
   OBJ, LNK, RT, CORE, STD, TXT, COL, NUM, SIMD, CONC, ASY, ATM, FFI, GPU, BLD, PKG, DRV, DIAG,
   TOOL, DBG, TST, CNF, BOOT, SEC, ECO).
2. Resolve conflicts by the spec-index priority rules → ADRs.
3. Write `spec/requirements/CATALOG.md` (the table reqcov.py reads) and `spec/COVERAGE.md`
   (human summary: counts per area × tier, list of GAPs, list of DEFERRED with reasons). The
   catalogue has seven columns — `id | area | tier | statement | sources | needs | status` — where
   `needs` lists the requirement ids this one is built on (`-` when none), taken from the
   `[needs …]` notes of Phase A.
4. Keep `raw/` files as the audit trail (never delete).
5. ADR numbers come from `taskctl.py adr-next <slug>`, never from listing the directory.

## Phase C — backlog expansion (T111)

1. For every GAP, following `spec/ROADMAP.md`: v1-core → extend an existing P0–P10 task (only if it
   stays one-sitting sized) or create a new task there; v1-full → `EPIC(E<phase>.<n>)` of the matching
   roadmap epic (tasks come later from the phase planning task); post-v1 → `EPIC(E24.x)` or
   `DEFERRED(<reason>)`. No epic fits → ADR + new epic in the roadmap.
2. Add `covers: [REQ-…]` to every task's front-matter; set each catalog status to task ids. A task
   that is already running or done is not rewritten: its `covers:` is extended with
   `taskctl.py covers <ID> <REQ-…>` (metadata only), and missing scope becomes a follow-up task
   (id from `taskctl.py new-id --phase <P>`, i.e. T112–T199 for P0–P10).
3. `taskctl.py validate`, `reqcov.py --strict` and `harness_check.py` must all pass (zero GAP, zero
   problems; `EPIC(...)` counts as planned, except on a `v1-core` row of a post-self-host epic).
4. T017 (first task of the semantic core) depends on T111: the backlog is complete before P3 starts
   (ADR-0005 §6).

## Ongoing (phase reviews)

At each phase gate the architect runs `reqcov.py --phase <P>`: every requirement mapped to that
phase's tasks must be implemented (all tasks done) or explicitly moved to a later task with a note.
New requirements discovered during implementation are appended to CATALOG.md with the next id.
