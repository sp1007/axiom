# Audit A4 — Process & document consistency

## Summary
Read CLAUDE.md, all agents, all skills, settings.json, ROADMAP, OWNER.md, ADR-0001, the four scripts and every board task front-matter (143 tasks). Ran status/list/next/validate/reqcov/harness_check/overdue on the real repo (all clean) and exercised state-changing commands on a copy in a temp git repo (/tmp/axaudit).
Counts: BLOCKER 0, MAJOR 14, MINOR 11 (25 findings; 20 CONFIRMED by reading or by running, 5 PLAUSIBLE).
Board rules hold: no `:=`/`::`/`var`/`import`/"hello world" outside the intended diagnostics text, no task edits `docs/`, no post-P10 task edits `bootstrap/axiom0`, no core task depends on a post-self-host task, all epic titles exist in ROADMAP. The weaknesses are in the autonomous loop, the scripts, and traceability timing.

## Findings

### A4-01 [MAJOR] [CONFIRMED] taskctl/reqcov/harness_check use `os.getcwd()` as repo root; from a subdirectory they report an empty board and the tick would shut the autopilot down
- Where: taskctl.py:54-55 (`ROOT = os.getcwd()`), :99-111 (`load_all` does `os.makedirs` for every state dir); axiom-tick SKILL step 6 (line 46: "nothing ready, nothing blocked, todo empty -> board finished -> CronDelete").
- Problem: test run from `sub/dir`: `status` prints `total 0 ... ready: (none)`, `validate` prints `OK (0 tasks)`, and a stray `_workspaces/tasks/{todo,doing,done}` tree is created there. The Bash tool keeps its cwd between calls, and engineers `cd` into build dirs. Evidence that it already happened: the real repo contains an empty stray `_workspaces/tasks/todo/_workspaces/tasks/{todo,doing,done}` (mtime 2026-09-30 23:00).
- Consequence if not fixed: one `status` from a wrong cwd makes the tick conclude "board finished": it runs the final review, calls CronDelete and sets `enabled:false`. Also `validate`/`reqcov --strict` pass vacuously in gates.
- Proposed fix: resolve ROOT with `git rev-parse --show-toplevel` (fallback: walk up until `_workspaces/tasks` exists), never `makedirs` outside it, and exit 2 when the board has 0 tasks. Same in reqcov.py, harness_check.py, overdue.py. Add to tick step 6: "finished only if `status` shows done >= 1 and `validate` reports the expected count (store `total` in autopilot.json)".

### A4-02 [MAJOR] [CONFIRMED] Front-matter parser breaks on inline `#` comments, and the SKILL.md template is full of them
- Where: axiom-tasks/SKILL.md "Task file format" (lines `owner: ...   # agent that implements`, `priority: 34   # lower runs first`, `paths: [...]   # dirs/files`, `covers: [...]  # ...`); taskctl.py:69-85 `parse`, :159/:169 `int(priority)`.
- Problem: `parse` keeps the comment in the value. Tested in the temp repo: `priority: 1   # c` makes every command crash (`ValueError: invalid literal for int()`) once the task is a candidate; `depends: [T004]   # x` becomes a string and `validate` prints one "unknown dependency <char>" per character; `paths: [...]  # c` becomes a string and `overlaps()` iterates characters (almost every pair overlaps or none does). The planning tasks T211-T223 and every unblock/split write new task files by hand, using this template as the model.
- Consequence if not fixed: one architect-written task file kills `taskctl` for the whole board (autopilot cannot repair itself) or silently mis-schedules parallel tasks. harness_check does not validate numeric `priority` or list types.
- Proposed fix: (1) in `parse` strip ` #...` from values; (2) after parsing validate types: `depends/paths/spec/covers` must be lists, `priority/attempts` int, `status` in {todo,doing,done,blocked,deferred}; fail with file name; (3) remove the comments from the template (put them below the block); (4) add a `taskctl new` (or `lint FILE`) used by planning tasks, and run `harness_check` in their acceptance (see A4-19).

### A4-03 [MAJOR] [CONFIRMED] `validate` does not detect duplicate task ids (docstring claims it does)
- Where: taskctl.py:36 docstring "check ids unique", :99-111 `tasks[meta["id"]] = ...`, :205-231 `cmd_validate`.
- Problem: copied T004 to `T999-dup.md` (same `id: T004`): `validate` prints `OK (143 tasks)` (should be 144), the second file is silently invisible to every command. Planning tasks create 3-10 tasks per epic by hand.
- Consequence if not fixed: a task vanishes from the plan (never runs, not counted, gate still passes), or an id collision overwrites a finished task's view. ROADMAP §4 step 5 and the T2NN acceptance rely on `validate`.
- Proposed fix: in `load_all` raise on a duplicate id (report both files); also check filename prefix == id, id appears in only one state dir, `done` tasks have all deps done, and a todo task does not depend on a `deferred` task except the one documented chain.

### A4-04 [MAJOR] [CONFIRMED] `taskctl commit` silently drops work that is not listed as a `-`/`*` bullet; glob pathspecs can even unstage it
- Where: taskctl.py:234-248 `_files_section`, :281-312 `cmd_commit`; axiom-tasks SKILL "Report format".
- Problem (all reproduced): (a) numbered (`1. path`), table or prose entries are ignored; since the report file itself is always added, `files` is never empty, so the safe fallbacks (`elif not others_doing`, the refusal) never trigger and the commit succeeds with only the report + board; (b) a bullet like `* **tests/**` yields the path `**tests/**`, which is not an existing file, so it goes to the `git rm --cached --ignore-unmatch` branch and, being a glob pathspec, un-stages `tests/other/parallel.txt` that an earlier line had just added; (c) a bullet naming a directory (`tests/`, or worse `bootstrap/`) stages everything under it, including another parallel task's half-finished files when the directory is shared; (d) there is no post-commit check that the task's `paths` are clean, so unlisted new files stay untracked (I reproduced "commit ok, `bootstrap/` and `tests/` still `??`").
- Consequence if not fixed: code of an accepted task is not in git although the board says done; the next task's commit (or the "no report" fallback `git add -A`) may absorb it under the wrong message; QA's note "omissions lose work" is only a manual check.
- Proposed fix: use `git --literal-pathspecs`; accept numbered items; refuse entries that resolve to a directory outside the task's `paths`; after staging, run `git status --porcelain -- <task paths>` and (i) stage any modified/untracked file under the task's own `paths` (paths are disjoint by construction, so this is safe) and (ii) print WARN for changes outside `paths` and outside the listed files; fail the commit when the report has no parsable Files-changed entries. Also the trailer is hard-coded `Claude Opus 5.5` (taskctl.py:58) while the session attribution is per model — make it configurable (minor).

### A4-05 [MAJOR] [CONFIRMED] `finish` and `commit` are two steps; a crash between them leaves an accepted, uncommitted task that nothing ever reconciles
- Where: axiom-compiler SKILL step 5 (PASS -> finish -> commit); axiom-tick SKILL steps 3-7 (no "done but uncommitted" check); taskctl.py:364-373 vs :399.
- Problem: after `finish` the task file is in `done/` (so it is no longer `doing`, never requeued). If the session dies, or `git commit` fails and is "retried" without a record, the tick does nothing for it. The board change is swept by a later task's `git add -A -- board`, but the code files listed in its report are not.
- Consequence if not fixed: missing commits, dirty tree, later tasks' fallback `git add -A` commits foreign changes, broken "one commit per accepted task" history (owner rule).
- Proposed fix: add `taskctl accept ID` (verify `VERDICT: PASS` is the last verdict line of `<ID>-qa.md`, then finish + commit in one process; commit first, move second is also acceptable) and a tick step "for every done task with no commit whose subject starts `<ID>:` (`git log --grep`) run `commit ID`". Log it.

### A4-06 [MAJOR] [CONFIRMED] Restart/stale recovery is ambiguous and keys on a marker the report format does not contain
- Where: axiom-tick SKILL step 4 (lines 25-31); axiom-compiler SKILL "Phase 0" step 3; axiom-tasks SKILL "Report format".
- Problem: (1) "agent recorded in running and alive (`ListAgents`, **or** you received no completion yet in this session)": after a restart "no completion received" is always true, so a dead agent is considered alive until `overdue.py` fires 180 min later; (2) "report says COMPLETE": the report template has no status line, COMPLETE exists only in the agent's chat message; a report written early and never finished is taken as complete and goes to QA; (3) the recovery ignores `running[ID].stage/round` and the `<ID>-qa.md` VERDICT: a restart during a fix round (qa.md says FAIL, report says COMPLETE from round 0) re-runs QA on unfixed code and burns a fix round; (4) `ListAgents` is not among the deferred tools visible in this session, so the check may be unavailable.
- Consequence if not fixed: up to 3 h of dead time after every session restart, wasted rounds, QA on partial work.
- Proposed fix: make the report's last line `STATUS: COMPLETE round=<n>` (and add it to the impl prompt and the template); define recovery as a table keyed on (`stage`, latest mtime of report vs qa, last VERDICT): `impl` + report STATUS COMPLETE -> QA; `fix` + report round > qa round -> QA; `qa` + verdict exists -> handle verdict; otherwise requeue. Store a `session_id`/start timestamp in autopilot.json and treat every `running` entry older than the session start as dead (no ListAgents needed). Do not let restart requeues consume an attempt (A4-12).

### A4-07 [MAJOR] [PLAUSIBLE] No handling of infrastructure failure (rate limit, quota, API error): tasks are burned to `blocked` and architect unblocks are spawned at full cost
- Where: axiom-compiler SKILL "Error handling summary" row 1 ("retry once with a fresh agent; then block with the error text"); taskctl.py:374-385 requeue->block after 3 attempts.
- Problem: a quota/rate-limit period makes every subagent fail within seconds. Each failure consumes an attempt, blocked tasks trigger Opus architect unblocks (tick step 5, up to 2 at a time) which also fail; the whole ready frontier ends `blocked` in a few ticks. `unblock` then resets attempts, so it repeats.
- Consequence if not fixed: unattended run wastes the remaining quota and leaves a polluted board (logs full of bogus blockers).
- Proposed fix: classify an agent result as INFRA (error text with 429/overloaded/quota/timeout, or finished in < 2 min with no report/no file change) vs TASK. INFRA -> do not count an attempt, do not block, write `autopilot.json.backoff_until` (exponential 30/60/120 min) and let the tick skip starts until then; never spawn unblock agents for INFRA.

### A4-08 [MAJOR] [CONFIRMED] Unblock loop is unbounded in two ways
- Where: axiom-tick SKILL steps 4b, 5; axiom-compiler SKILL step 5 (FAIL round 2 -> block -> architect unblock) and "Procedure: architect unblock"; taskctl.py:386-392 (`unblock` resets attempts).
- Problem: (a) a task that fails QA 3x is blocked, the architect "unblocks" it (attempts reset), it fails 3x again ... no cap on cycles; (b) if the unblock agent crashes or is overdue, 4b says "spawn once more, then leave the task blocked and log", but step 5 of the next tick again sees "blocked without an active unblock agent" and respawns, every 30 minutes forever. "All remaining tasks blocked -> keep ticking" (error table) means an Opus agent every tick.
- Consequence if not fixed: quota drain on an unfixable task with no signal; the pipeline behind it is stalled but the loop never ends or reports.
- Proposed fix: counters in autopilot.json (`unblock_attempts[ID]`) and in the task front-matter (`cycles:`). Cap at 2 unblock cycles per task and 2 failed unblock agents per task; then `taskctl park ID` (status `parked`, skipped by `next` and by step 5), write `_workspaces/STUCK.md` (blocked chain + reasons), and when nothing is ready/doing and only parked/blocked remain: disable the cron and stop (this is a stop, not a question, so "never asks" holds).

### A4-09 [MAJOR] [CONFIRMED] Architect unblock agents and critical tasks edit the same board/spec files concurrently; unblock is invisible to the path lock and to the critical drain
- Where: axiom-compiler SKILL "Procedure: architect unblock" and "Parallelism rules" ("plus their QA gates and architect unblocks"); axiom-tick step 5 (max 2 at a time); T111 Notes ("runs alone, so no agent moves task files while you edit"); T211-T224 Notes; taskctl.py `ready` counts only `doing/`.
- Problem: the critical-alone/drain rule is computed from `doing/` only. An unblock agent (Opus, edits `_workspaces/tasks/todo`, `spec/`, ROADMAP, CATALOG) can run while T110/T111/T211... (same files) run alone, and two unblock agents can edit the same spec. They also pick ADR numbers concurrently ("next free number": architect.md, ADR-0001 exists) -> two `ADR-0002-*`.
- Consequence if not fixed: lost edits to CATALOG/ROADMAP/task files during planning; duplicate ADR ids; half-written spec committed by the unblock commit (`git add -- <listed> _workspaces/tasks`).
- Proposed fix: orchestrator rule "an unblock counts as a path holder of `_workspaces/tasks`, `spec/`; while a critical task is in doing (or waiting to start) queue unblocks; while an unblock runs a critical task does not start"; serialise unblocks (max 1). Add `taskctl adr-next` that atomically creates `spec/decisions/ADR-NNNN-reserved.md` and returns the number (also for T001/T045/T110 which each write ADRs; T045 runs in parallel with P5 tasks and writes under `spec/` with paths that omit `spec/decisions`).

### A4-10 [MAJOR] [CONFIRMED] T111 must not edit done tasks, but reqcov requires `covers:` on every task named in the catalogue, and many mapped tasks will already be done
- Where: T111 §Scope ("never rewrite tasks already in doing/ or done/"); reqcov.py:110-116 (`task {tid} does not list it in covers:`); OWNER.md (REQ-OWNER-001 -> T001, T010, T011; REQ-OWNER-004 -> T003a; REQ-OWNER-006 -> T026, T028 ...); scheduling: T110 needs T092-T109 (priority 16-33) while T004-T016 (priority 5-26) are ordered ahead of P3+ tasks.
- Problem: priority ordering lets T004-T016 (and possibly T017+) finish before T110/T111 are ready (T110 is ready only after all 18 extraction tasks). T001, T003a, T004.. are done at T111 time; OWNER rows and any catalogue row naming them cannot satisfy reqcov, and T111's acceptance `reqcov --strict` exit 0 is unreachable without breaking its own rule. Second effect: gaps found by extraction in already-done lexer/parser tasks (T010-T016) become rework follow-ups instead of scope.
- Consequence if not fixed: T111 QA FAIL x3 -> block (or silent rule breach), and avoidable rework of P2.
- Proposed fix: minimal: allow T111 to edit only the `covers:` line of done/doing tasks via `taskctl covers ID REQ...` (metadata only, code untouched). Better: add T111 to `depends` of T010 (first language implementation task; T004-T009 tooling still run in parallel with extraction), so the complete backlog exists before language work starts. NEEDS OWNER DECISION only for the dependency option (delays the lexer by the duration of the extraction wave).

### A4-11 [MAJOR] [CONFIRMED] Traceability cannot detect "planned, but too late" (the raw-pointer case)
- Where: reqcov.py:85-116 (status kinds), requirements-extraction.md (tier definition, Phase A status column, Phase C), ROADMAP R5.
- Problem: reproduced with a 3-row catalogue: `REQ-TYP-001 v1-core "Vec<T> needs raw pointers" EPIC(E13.1)` + `REQ-STD-001 v1-core ... T070`; `reqcov --strict` prints `COVERAGE OK`. reqcov checks existence of the mapping only: (a) a `v1-core` row may be `EPIC(E11+)` or map to a task of phase > P10; (b) there is no relation between requirements ("Vec needs raw pointers"), so ordering across rows is never checked; (c) `tier` is the extractor's judgement, made without dependency analysis.
- Consequence if not fixed: each future "we forgot X" (as with char, slices, UTF-16, pointers) passes the gate and is discovered by T076 or later.
- Proposed fix (three cheap layers): (1) reqcov rule: tier `v1-core` must map to task ids all with phase <= P10 (or DUPLICATE/REJECTED); `EPIC(...)` or a P11+ task on a v1-core row is a PROBLEM; also `post-v1`/`v1-full` rows mapped to P0-P10 tasks are flagged for review. (2) Add a 7th catalogue column (or a `requires:` list in the status cell) `needs: REQ-...`; reqcov checks that every implementing task of a required requirement is a (transitive) ancestor of each implementing task of the dependent one; extraction Phase A asks for `needs` whenever a statement says "built on / uses / requires". (3) T003a emits the self-host subset as a machine-readable list (`spec/selfhost-subset.tsv`: feature id, REQ id, delivering task, first consumer task) and `reqcov --selfhost` checks delivering task in ancestors(first consumer) and every consumer in ancestors(T076); T076 re-runs it and T062/T075 gates call it. Optionally a `needs:` front-matter on tasks checked the same way.

### A4-12 [MAJOR] [PLAUSIBLE] Hang/timeout limits are wall-clock only (180 min impl/fix) and restarts consume attempts
- Where: overdue.py:19-20 and axiom-tu-dong state `timeouts`; axiom-tick step 4b; taskctl.py:357 (`start` increments attempts), :377 requeue->block at 3.
- Problem: there is no per-task override and no activity signal. The extraction tasks T092-T109 (about 100 files each, architect/sonnet, incremental) and the large opus tasks (T017 typeck, T081 typeck port, T110 consolidation) may legitimately exceed 3 h; each kill is `TaskStop` + requeue (attempt++), so after the third kill the task is blocked although it was progressing. Session restarts (laptop sleep) also requeue and spend attempts.
- Consequence if not fixed: long tasks are blocked for being long; architect unblock runs on a non-problem.
- Proposed fix: `timeout_min:` in task front-matter read by overdue.py (default from `timeouts`), and treat an agent as hung only if no file changed under its `paths`/`_workspaces/reports/<ID>-*` for N minutes (heartbeat by mtime) in addition to the hard cap; `requeue --no-attempt` for stale/restart/hung-without-progress cases.

### A4-13 [MAJOR] [CONFIRMED] Shared registry `diag/codes.def` (and `spec/diagnostics.md`) has no owner task other than T009; later tasks must edit it outside their `paths`
- Where: T009 (`paths: src/diag`, scope "codes.def X-macro registry"); axiom-c-stage0 (every code registered once in codes.def), axiom-qa Gate step 6 ("new diagnostics have registered codes"); only T009 names codes.def (grep).
- Problem: every lexer/parser/resolver/typeck/ownership task adds codes to `bootstrap/axiom0/src/diag/codes.def`; `next` cannot see it (`overlaps` works on declared `paths`), so two parallel tasks (e.g. T053 and T060, T046 and T060) edit it simultaneously; `taskctl commit` of whichever finishes first also commits the other's half-registered codes, and the same holds for `tools/axtest.py`, `tools/ci.sh`, `tests/README.md`.
- Consequence if not fixed: sporadic edit collisions, commits that contain codes of an unfinished task, QA failures that blame the wrong task.
- Proposed fix: one `.def` per module (`src/diag/codes/<module>.def`, included by `codes.def` via X-macro includes; each task lists its own file in `paths`; archcheck checks prefix == module) and likewise per-area test-runner extension files; or add `bootstrap/axiom0/src/diag/codes.def` as a shared-file lock that `ready()` honours (`locks:` front-matter). Amend axiom-tasks "Rules that keep the board healthy" which names the registry as edited only by its owner.

### A4-14 [MAJOR] [PLAUSIBLE] No post-T087 build/test/freeze procedure: skills and gates are hard-wired to axiom0 and R3 is not enforced outside task paths
- Where: axiom-qa Gate protocol steps 2-3 (cmake `bootstrap/axiom0`, `build-qa-<ID>/axiom0.exe`); axiom-compiler SKILL prompt template ("--compiler build-<ID>/axiom0.exe"); axiom-c-stage0 (all of it); T086/T087 paths (`tools/bootstrap.py`, tests only); harness_check.py:45-46 (R3 checked on task `paths` only).
- Problem: P11+ tasks change `compiler/` (Axiom) and `std/`; none of the orchestrator/QA prompts say which compiler builds them (axiomc stage-2?), how parallel tasks get private builds, or how axtest selects the compiler. Nothing stops an engineer from editing `bootstrap/axiom0` inside a P11+ task whose `paths` are clean (R3 exception "bug fixes needed to rebuild axiomc" also has no task type or approval path).
- Consequence if not fixed: P11 start stalls on an ad-hoc decision; silent growth of the frozen C compiler.
- Proposed fix: in T087 (architect-reviewed) add deliverables: `git tag axiom0-frozen`, `tools/freeze_check.py` (diff of `bootstrap/axiom0` vs the tag must be empty or limited to allow-listed fixes recorded as `AX0-FIX-nn` tasks), a `tools/build_axiomc.py` per-task build dir command, and updates of the QA/orchestrator prompt text (`--compiler` = stage-2 axiomc). Add the freeze check to the QA gate protocol after T087 and to harness_check.

### A4-15 [MINOR] [CONFIRMED] Core tasks T004-T016 consume `spec/SPEC-00-bootstrap.md` without depending on T003/T003a
- Where: ~99 task bodies cite SPEC-00 (boilerplate "see the milestone ladder"); my ref check (spec file -> producer task -> ancestor) found 14 consumers without a dependency path: T002, T004-T016. T010 (lexer) is where `@at`/unsupported-feature diagnostics (T003a, ADR-0001) first matter.
- Consequence if not fixed: in the happy path priority (T001-T004 critical, run first) hides it; if T003/T003a are blocked, T004-T016 start on missing/stale spec.
- Proposed fix: T004 depends on T003a; T010 depends on T003a.

### A4-16 [MINOR] [CONFIRMED] `reqcov --strict` exits 0 when CATALOG.md does not exist
- Where: reqcov.py:66-69.
- Problem: prints "no catalog" and returns 0 (verified). Gates T022-T075 run before or without a catalogue would pass R5 vacuously; after T110 a deleted/renamed catalogue also passes.
- Proposed fix: under `--strict` return 1 when the catalogue is missing or empty; add a minimum-row sanity check (e.g. >= OWNER rows).

### A4-17 [MINOR] [CONFIRMED] T224 and the catalogue refer to epics/gate that do not exist (E24.x, T324)
- Where: T224 Scope/Acceptance ("gate task T324"), ROADMAP §2 table (P24 gate "—"), ROADMAP §3 P24 (no E24.n bullets), T111 Scope ("`EPIC(E24.x)` or DEFERRED"), reqcov.py:91-95 (EPIC must name `**E..** ` in ROADMAP).
- Problem: `EPIC(E24.*)` statuses can never validate, and T224's own acceptance names a gate that is not on the board.
- Proposed fix: add epics E24.1..E24.n (AI serving, GUI/windowing, audio/media, graphics, scientific/ML, storage engines, distributed, domain runtimes) to ROADMAP §3 P24, create gate T324 (deferred, depends T224), or instruct T111 to use DEFERRED only.

### A4-18 [MINOR] [CONFIRMED] No ID/phase rule for tasks created outside planning tasks (unblock splits, P0 fix tasks, T076 gap tasks, phase-review follow-ups); "done-by-split" has no command
- Where: axiom-tasks SKILL ("suffix or the next free number"); axiom-architect Unblocking protocol (b) "mark the original done-by-split"; axiom-compiler error table ("P0 fix task, priority 0"); T076 Scope (gap tasks); taskctl.py:364-366 (`finish` refuses a task not in `doing`).
- Problem: "next free number" from T112 upward collides in spirit with the reserved blocks (a P11 fix could get T112); a blocked task in `todo` cannot be closed as superseded; P0 fix tasks have priority 0 (critical, alone) but no phase/ID rule.
- Proposed fix: `taskctl new --phase P.. --owner ..` allocating ids (P0-P10 follow-ups from T112-T199, P11+ from the phase block, never from T2NN/T3NN), `taskctl supersede ID --by T..` (todo/blocked -> done, log), and a line in ROADMAP §4 for follow-up ids.

### A4-19 [MINOR] [CONFIRMED] Planning-task acceptance omits `harness_check` and cross-phase dependencies
- Where: T211-T223 Acceptance (validate + reqcov only); ROADMAP §4 step 5; core gates T022/T029/T044/T052/T062/T075 (no reqcov or harness_check although R5 says `reqcov --strict` at every gate).
- Problem: only `harness_check` enforces `model/gate_model`, core-before-post deps, R3 paths and CR/LF; new tasks are hand-written. ROADMAP says E15.5 needs P12 and P16/P20... but §4 step 2 never tells the planner to add dependencies on other phases' gates (T215 depends only on T087).
- Proposed fix: add "`harness_check.py` exits 0" to every T2NN/T3NN and core gate acceptance; add to §4 step 2: "add `depends` on the gate of every phase the roadmap lists as a prerequisite of the epic (e.g. E15.5 -> T312)".

### A4-20 [MINOR] [CONFIRMED] Stale or inconsistent statements in docs
- Where / problem / fix (one line each):
  - axiom-x64-backend SKILL:17 "Linear-scan regalloc (T053)" — T053 is methods; linear scan is T063, post-self-host (R7). Fix: "(E15.8, T063, after T087)".
  - axiom-spec-index SKILL:40 "R1–R7" — ROADMAP has R8. Fix text.
  - axiom-compiler SKILL:164 scenario "next batch (T002, T004 in parallel)" — both are critical (priority < 10) and never run together.
  - axiom-tick SKILL description (line 3) still says "if no task is in progress — picks the next batch" while step 6 refills every free slot.
  - ROADMAP §2 table omits T003a (P0) and T061a (P7) though the change log and tasks define them; R-list order is R1..R5, R7, R8, R6.
  - spec-index SKILL says Linux ELF is "second" target "testable through WSL" — R7/E16.9 puts it after self-host; say so to avoid an engineer building ELF in axiom0.
  - harness_check's STALE list does not catch any of the above; consider a check that every `T\d{3}` mentioned in skills/agents exists and has the claimed phase.

### A4-21 [MINOR] [PLAUSIBLE] settings.json can stall the unattended loop and its deny rules are thin
- Where: .claude/settings.json; axiom-tick step 4b (`TaskStop`), step 0 (`ToolSearch`).
- Problem: `TaskStop` (and possibly `ToolSearch`) are not in `allow`; a permission prompt in an unattended session stops the loop although "autopilot never asks". `deny` covers `Edit/Write(docs/**)` and `git push:*` only: `git -C . push`, `git remote add`, `gh ...`, `Bash(sed -i ... docs/...)`, `mv/rm` on docs/ are not blocked (`Bash` is fully allowed), so the owner rules "docs/ never edited, never push" rely on agent discipline.
- Proposed fix: add `TaskStop`, `ToolSearch`, `Monitor` to allow; add deny `Bash(git * push*)`, `Bash(git remote*)`, `Bash(gh *)`, `PowerShell(gh *)`; consider a PreToolUse hook that rejects Bash/PowerShell commands touching `docs/` or containing `git push`; have harness_check assert `git status --porcelain docs` is empty (unstaged edits, not only staged).

### A4-22 [MINOR] [CONFIRMED] `next --max 0` returns one task
- Where: taskctl.py:174-181 (append happens before the `>= maxn` test); axiom-compiler Phase 0 step 2 calls `next --max <3 - doing>` with no guard.
- Problem: verified `next --max 0` prints T001. With 3 tasks running the orchestrator could start a 4th.
- Proposed fix: return [] when maxn <= 0; orchestrator computes free slots against `max_parallel` from autopilot.json.

### A4-23 [MINOR] [PLAUSIBLE] Tick has no branch for "todo not empty, nothing ready, nothing doing, nothing blocked"
- Where: axiom-tick step 6 last sentence.
- Problem: cases such as a dependency on a deferred/parked task, a dependency edge added wrongly by a planning task, a critical task waiting behind `doing` that never drains: the tick logs and idles forever, with no diagnosis.
- Proposed fix: in that state run `taskctl validate`, list each todo task with its first unfinished dependency and its status, write `_workspaces/STUCK.md`, spawn one architect diagnosis, then stop after N ticks (same stop as A4-08).

### A4-24 [MINOR] [CONFIRMED] `unblock` is unguarded
- Where: taskctl.py:386-392.
- Problem: works on any task (verified logic): on a `doing` task it sets `status: todo` while the file stays in `doing/`; on `deferred` (T224) it succeeds although tick/compiler skills say only the owner may do this; no record who asked.
- Proposed fix: refuse unless the file is in `todo/` with status blocked; `deferred` requires `--owner-approved` (and log it).

### A4-25 [MINOR] [CONFIRMED] Attribution trailer hard-coded
- Where: taskctl.py:58 `Co-Authored-By: Claude Opus 5.5`; session attribution for this project run is per-model (orchestrator runs on Sonnet; architect/engineers on Opus/Sonnet).
- Fix: read the trailer from an env var or `.claude/` config, or omit the model name.

## Checked and OK
- Board rules: grep of all task files for `:=`, `::`, `var `, `import`, `hello world` -> only intentional mentions in T001/T011 (diagnostics and fix-its); `Xin chào thế giới` appears in 13 places.
- No task `paths` start with `docs/`; `stageable()` also blocks `docs/`; `.gitattributes` has `docs/** -text`; settings deny Edit/Write `docs/**`.
- Post-self-host rule: harness_check passes; every phase > 10 task has `compiler/` or `std/` paths (T058, T063, T064, T066, T067, T068, T088-T090, T750, T751); no pre-P10 task uses `compiler/`.
- IDs: all IDs outside the ROADMAP §4 blocks are explained (T088-T091, T750/T751 sit at the start of the P18 block T750-T799, T211-T224, T311-T323, suffix tasks T003a/T061a/T073a). The planning tasks must continue from T752 in P18.
- Phase table vs board: T211-T224 (14, T224 `deferred`), T311-T323 (13), planning-task and gate dependencies match ROADMAP "Depends on gates" (T216->T313, T217->T316, T219->T318, T220->T316+T318, T221->T311+T313, T222->T311+T312+T316, T223->T311..T322).
- Every epic named in a task title exists in ROADMAP (harness_check + manual: E11.1/3/4, E14.4, E15.4/8, E16.9, E17.3, E18.6/7, E23.2). REQ-OWNER rows point to existing tasks/epics (T001, T003a, T010, T011, T014, T026, T028, T750, T751, E13.6, E13.7).
- Critical rule in `ready()`: priorities < 10 are T001-T004, T110, T111, T211-T224; verified critical-alone + drain with a start/block/requeue/unblock/finish sequence in the temp repo; requeue blocks at the 3rd attempt (verified); `start` refuses unfinished deps; deferred T224 is never returned by `next`.
- Model/gate_model present and valid on all tasks; reviewer is never the owner (QA-owned tasks are reviewed by the architect); escalation to Opus on QA fix round 2 is consistent between CLAUDE.md and axiom-compiler SKILL; 30-minute tick is consistent in CLAUDE.md, tu-dong, tick, compiler skills and harness_check STALE list.
- overdue.py tested with fake state: reports overdue, unknown stage falls back to impl limit, missing `since` reported.
- Spec-file producer/consumer check for all `spec/*.md` references: every consumer except T002/T004-T016 (A4-15) depends on the task that produces the file (SPEC-01..04, SPEC-10..12, SPEC-20, BOOTSTRAP, diagnostics, invariants, INDEX).
- Git handling: `.gitignore` ignores build dirs, `*.exe/*.obj` (fixtures exempt), autopilot.json and logs; reports, audit files and the board are tracked; no remote is configured (`git remote -v` empty).

## Cross-lens notes
- A3: shared files outside `paths` (A4-13) also affect tools/axtest.py, tools/ci.sh and tests/README.md; T061a lists `tests/run/native_ptr` but no `lir`/`target/x64` path, so native lowering of raw pointers may be nobody's job before T065 (verify in T061a body).
- A1/A2: T086/T087 have no acceptance for axiom0 freeze enforcement and their gate is sonnet (A4-14).
- Environment hygiene: the stray empty directory `_workspaces/tasks/todo/_workspaces/` (see A4-01) is untracked noise created by a wrong-cwd run; remove it when the audit is over (not touched here, read-only).
- tham-dinh SKILL step 2 says A3/A4 run on Sonnet while the auditor agent file pins Opus; the Agent `model` override makes this consistent, but say so in lenses.md to avoid a reviewer "fixing" it.
