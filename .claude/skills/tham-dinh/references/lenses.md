# Auditor prompts (copy verbatim, replace `<date>` with YYYY-MM-DD)

Models: the model in each heading is passed as the Agent `model` parameter and overrides the model
named in `.claude/agents/axiom-auditor.md` (A1/A2 need design judgement → opus; A3/A4 are checklist
work → sonnet). This is deliberate — do not "fix" the difference.

## Shared context (prepend to every lens prompt)

```
You are axiom-auditor. Read .claude/agents/axiom-auditor.md and follow it exactly (read-only; your
only output is your findings file). Working directory: the repository root. Date: <date>.
Context: Axiom is a new systems language. Plan: Stage-0 compiler `axiom0` in C11 (bootstrap/axiom0,
Windows x64 first, own COFF writer + minimal PE linker, no LLVM, no external assembler/linker in the
production path), then the compiler is ported to Axiom (`axiomc`, tasks T076–T087, phase P10) and
must compile itself (fixed point); breadth features after self-host. Binding plan: spec/ROADMAP.md
(R1–R8: R2 core → self-host → breadth, R3 axiom0 frozen after T087, R7 minimal C, R8 std in Axiom
early). Owner decisions: CLAUDE.md, spec/requirements/OWNER.md, spec/decisions/ADR-*. Canonical
syntax: .claude/skills/axiom-syntax/SKILL.md (`=` only, `.` paths only). Board:
_workspaces/tasks/todo (read with `python .claude/skills/axiom-tasks/scripts/taskctl.py list` and
`show ID`; format in .claude/skills/axiom-tasks/SKILL.md). Corpus navigation:
.claude/skills/axiom-spec-index/SKILL.md (docs/base/specs, docs/base/tasks, docs/base/others are
normative; docs/base/discussions is not). Known deliberate choices: no floating point in axiom0
(E12.2 after self-host); T061a minimal raw pointers/unsafe; slices in T048; if-let/destructuring in
T038; char in T034; std uses Windows W APIs (T074). Toolchain: MSYS2 ucrt64 gcc/clang/cmake/ninja,
GNU as/objdump, Python 3.12; no MSVC.
```

## A1 — self-host feasibility (opus) → `_workspaces/audit/<date>/A1-selfhost.md`

```
LENS A1 — SELF-HOST FEASIBILITY. Mentally write axiomc in Axiom, module by module, the way tasks
T076–T087 describe it and the way axiom0 is structured (.claude/skills/axiom-c-stage0/SKILL.md:
kernel, source, diag, lex, syntax, resolve, hir, types, traits, own, mir, verify, interp, opt, lir,
abi, target/x64, objmodel, obj, link, driver). For each module list concretely the language features
and std APIs the Axiom code needs (enums with payloads for AST nodes, recursive types via Box or
arena ids, HashMap with string keys, interning, generic Vec<T>, traits, closures, bit ops/shifts for
encoding, wrapping arithmetic for hashing, u64 math, byte buffers with LE writes, file I/O, exit
codes, args, sorting for determinism, `?`, panics/ICE, number/hex formatting for dumps, const
tables, match on integers/ranges, labelled break, mutual recursion across modules, static data,
recursion depth, memory via arenas).
For every needed feature find the P0–P9 task that delivers it (quote id + scope line) and check it is
delivered BEFORE the first task that needs it by (transitive) depends — especially before T076.
Check native support too (catch-up tasks T033, T037, T040, T042, T051, T059, T061a): axiomc runs as
a native exe. Check scale risks (axiom0 compiling a 50–100k line Axiom program: recursion depth,
O(n^2) passes, naive register allocation — is self-compile time plausible?). Check the fixed-point /
differential verification plan in T076–T087. Missing or late features → findings (BLOCKER if axiomc
cannot be written or compiled as planned). Put the full feature→task matrix under "Checked and OK".
```

## A2 — ladder conformance (opus) → `_workspaces/audit/<date>/A2-ladder.md`

```
LENS A2 — LADDER CONFORMANCE. The owner chose the milestone ladder of doc 0263 with
docs/base/tasks/0260* (over the older blueprint 0152 ordering). Read 0263 fully, tasks/0260* and the
BOOTSTRAP-0xx task documents it references (`ls docs/base/tasks | grep -i bootstrap`), and
0172/0181 for kernel/backend rules. Extract every milestone/step, its required contents, exit
criteria/gates, mandatory invariants (no AST→machine code, mandatory MIR verifier, interpreter as
oracle, differential testing…) and the order. Map each step onto board tasks P0–P10 (T001–T087,
T003a, T061a, T073a, T092–T111). Find: steps with no task; partially covered steps (name the missing
items); order violations; ladder gates/exit criteria missing from the gate tasks (T022, T029, T044,
T052, T062, T075, T086, T087); items moved after self-host that the ladder says bootstrap needs
(check each against R7 — flag, don't just accept); tasks contradicting the ladder's forbidden
shortcuts; vertical-slice naming (VS1, VS2…). Include a step→task table under "Checked and OK".
```

## A3 — task executability (sonnet) → `_workspaces/audit/<date>/A3-executability.md`

```
LENS A3 — TASK EXECUTABILITY. Each task is executed by one subagent in one sitting, gated by QA,
then auto-committed using ONLY the files in the report's "## Files changed". Up to 3 tasks run in
parallel when their `paths` do not overlap — `paths` is the concurrency lock. For every task
T001–T087, T003a, T061a, T073a, T092–T111 (skim post-self-host tasks), read it as the executing agent
in dependency order, tracking what exists in the repo at that moment. Find:
1. use of a feature/tool/file produced only by a later or non-dependency task (runner T005, print
   T041, native T028, SPEC files from T001–T003a…);
2. acceptance criteria not verifiable at that point, vague, or not checkable by a command;
3. `paths` problems: scope edits directories not listed (src/mir, src/driver, diag/codes.def,
   tests/README.md, CMakeLists, tools/axtest.py) → parallel clobbering; paths too broad; shared hot
   files edited by many tasks without being listed;
4. tasks too large for one sitting (suggest split) or trivial;
5. owner/reviewer/model mismatches;
6. priority vs dependency oddities, wrong critical flags, missing deps on T001/T002/T003/T003a/T045;
7. a feature supported in interp but never lowered natively before T076.
Give exact task ids and the fix. One-line per-task OK list under "Checked and OK".
```

## A4 — process & document consistency (sonnet) → `_workspaces/audit/<date>/A4-process.md`

```
LENS A4 — PROCESS & DOCUMENT CONSISTENCY. Read CLAUDE.md, .claude/agents/*, .claude/skills/*
(including scripts taskctl.py, autopilot.py, overdue.py, reqcov.py, harness_check.py and
axiom-spec-index/references/requirements-extraction.md), .claude/settings.json, .claude/hooks/guard.py,
spec/ROADMAP.md, OWNER.md, ADRs, and the board. Owner rules: docs/ never edited/staged; commit locally
after each QA-accepted task (`taskctl accept`), never push; autopilot never asks — decisions are
delegated (decide, record the rationale, report afterwards); max 3 parallel with disjoint paths/locks,
QA gates on per-task snapshots; critical (priority < 10) alone with drain; QA fix round 2 escalates to
opus; infrastructure failures never burn attempts; T224 deferred until the owner asks.
Find:
1. contradictions between documents, stale statements, references to missing files/sections/tasks/
   epics, IDs outside the ROADMAP §4 blocks;
2. board rule violations (non-canonical syntax `:=` `::` `var` `import`; tasks editing docs/;
   post-self-host tasks editing bootstrap/axiom0; core depending on post-self-host; tasks outside any
   epic; "hello world");
3. autonomous-loop failure modes, walking the real scripts and skill text: session restart
   mid-task; agent crash; rate limit / quota hitting every agent and the session itself; QA FAIL ×3;
   unblock that fails or repeats; architect editing a task in doing; two tasks needing the same shared
   file; incomplete Files-changed; a report listing a directory; crash between the steps of accept;
   critical task ready while 3 run; cron expiry; failing phase gate; planning tasks T211–T223
   creating tasks (ID collisions); reqcov strict failing; board fully done; board stuck — report gaps
   with concrete fixes;
4. script bugs (run read-only commands only: status, list, next, validate, changes, reconcile without
   --commit, recover, stuck without --write, reqcov, harness_check, overdue, guard.py --selftest;
   test state-changing commands only on a copy in a temp git repo — the scripts find their root from
   their own location, so copy them into the temp repo);
5. traceability: can extraction → CATALOG → reqcov detect a requirement "planned" in an epic but
   needed earlier (raw pointers were in E13.1 but Vec needs them before self-host)? Propose how.
```
