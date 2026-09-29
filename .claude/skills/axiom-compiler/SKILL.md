---
name: axiom-compiler
description: Orchestrator for building the Axiom compiler with the agent team (architect, frontend, semantics, backend, stdlib, qa). Runs board tasks end-to-end — start → implementation subagent → QA gate → fix rounds → done → auto-commit — in parallel batches, unblocks blocked tasks via the architect, and handles follow-ups. Use for ANY request to build/continue/implement/fix/test the Axiom compiler or run a specific task ("làm task T010", "tiếp tục compiler", "chạy lại task", "sửa lỗi QA", "làm lại phần lexer", "cập nhật kết quả", "run next task", "implement the parser"). For unattended continuous running use the tu-dong skill; this skill is the procedure it calls.
---

# Axiom compiler orchestrator

**Execution mode: sub-agents (multi, parallel, background).** Each task is executed by one
specialist subagent; QA is a separate subagent (generator–verifier pattern); independent tasks run
concurrently (fan-out) when the board says their `paths` don't overlap. Coordination is file-based
(`_workspaces/`) so nothing depends on conversation memory and any session can resume. Agent-team
tools (TeamCreate) are not assumed; if they are available, the same roles and files apply.

## Team

| Agent (`.claude/agents/`) | Owns |
|---|---|
| axiom-architect | `spec/`, ADRs, backlog planning, unblocking, phase-gate reviews |
| axiom-frontend | kernel, source, diag, lex, syntax, resolve, hir, driver |
| axiom-semantics | types, traits, own, mir, verify, interp, opt, comptime |
| axiom-backend | lir, abi, target/x64, objmodel, obj, link, startup, FFI |
| axiom-stdlib | `std/` (Axiom code), self-hosting ports in `compiler/` |
| axiom-qa | tools/, test suites, fuzzing, **gate for every task** |

Always pass `model: "opus"` when spawning. Spawn with `subagent_type: "<agent-name>"`; if the
runtime rejects that type (agent files added mid-session are not yet registered), use
`subagent_type: "general-purpose"` and start the prompt with
`You are <agent-name>. First read .claude/agents/<agent-name>.md and follow it exactly.`

## Files

- Board: `_workspaces/tasks/{todo,doing,done}` via `python .claude/skills/axiom-tasks/scripts/taskctl.py`
- Reports: `_workspaces/reports/<ID>-report.md`, `<ID>-qa.md`
- Autopilot state: `_workspaces/autopilot.json` (see tu-dong); log `_workspaces/logs/autopilot.log`
  (append one line per decision: `YYYY-MM-DD HH:MM <ID> <event> <detail>`).

## Phase 0 — context check (every invocation)

1. `taskctl.py status` and read `_workspaces/autopilot.json` if present.
2. Decide the mode:
   - user names a task (`T010`) → **single task run** (or re-run: if it is in `done/`, move it back
     with a note only if the user asked to redo it; otherwise run a follow-up task).
   - user gives feedback on a finished task ("parser recovery is weak") → architect creates a
     follow-up task (or re-opens scope) → run it.
   - otherwise → **batch run**: `taskctl.py next --max 3` and run those.
3. Stale work: a task in `doing/` with no live agent (check `ListAgents` / autopilot.json) →
   if `<ID>-report.md` says COMPLETE and no PASS QA yet → go to step "QA gate"; else
   `taskctl.py requeue <ID> --reason stale` and treat as ready.

## Procedure: run one task `<ID>` (owner from the task front-matter)

1. `taskctl.py start <ID> --agent <ID>-impl`
2. Spawn implementation agent (background):
   - `name: "<ID>-impl"`, `subagent_type: <owner>`, `model: "opus"`, `run_in_background: true`
   - prompt (fill in):
     ```
     Task <ID>: <title>. Task file: _workspaces/tasks/doing/<file>.
     Read the task file, your agent definition, and the skills it lists. Previous attempt files, if
     any: _workspaces/reports/<ID>-report.md, <ID>-qa.md — read them first and continue.
     Implement, test (full suite), write _workspaces/reports/<ID>-report.md with an exact
     "## Files changed" list. Do not commit; do not move task files.
     Use your own build directory build-<ID> (other agents build in parallel) and pass
     --compiler build-<ID>/axiom0.exe to tools/axtest.py.
     Finish with "<ID> COMPLETE" or "<ID> BLOCKED: <reason>".
     ```
   - record in autopilot.json `running[<ID>] = {agent: "<ID>-impl", stage: "impl", round: 0}`.
3. When the agent finishes (task notification):
   - `BLOCKED` → `taskctl.py block <ID> --reason "<reason>"`; queue an architect unblock (below).
   - `COMPLETE` but no report → send it back once (SendMessage to `<ID>-impl`: "write the report");
     still missing → requeue.
4. **QA gate**: spawn `name: "<ID>-qa"`, `subagent_type: axiom-qa`, `model: "opus"`, background,
   prompt: `Gate task <ID>. Task file: … Report: _workspaces/reports/<ID>-report.md. Follow your
   Gate protocol and write _workspaces/reports/<ID>-qa.md ending with VERDICT: PASS|FAIL.`
5. On QA result (read the last `VERDICT:` line of `<ID>-qa.md`, not the chat summary):
   - **PASS** → `taskctl.py finish <ID>` → `taskctl.py commit <ID>` (auto-commit, local, never
     push) → log → remove from `running`.
     `taskctl commit` stages the report's "Files changed" list; QA's added tests are listed in the
     QA file — append them to the engineer report's list before committing (or `git add` them
     explicitly).
   - **FAIL**, round < 2 → round += 1; `SendMessage` to `<ID>-impl` with the path of the QA file and
     "fix every finding, add regression tests, update the report (Round N)". If the agent cannot be
     resumed, spawn a fresh owner agent with the same prompt plus the QA file. Then QA again.
   - **FAIL**, round == 2 → `taskctl.py block <ID> --reason "QA failed 3 times: <top findings>"` →
     architect unblock.
6. After any task leaves `doing/`: if `doing/` is now empty, immediately start the next batch
   (do not wait for the 5-minute tick).

## Procedure: architect unblock

Spawn `name: "unblock-<ID>"`, `subagent_type: axiom-architect`, `model: "opus"`, background:
`Task <ID> is blocked. Task file: …; report/QA files: …; blocker: <reason>. Follow your Unblocking
protocol (ADR / split / prerequisite / rescope), run taskctl validate, report what changed.`
Architect changes to `spec/` and the board are committed afterwards with
`git add spec _workspaces/tasks && git commit -m "arch: unblock <ID> — <summary>"` (+ trailer).
Unblocking never waits for the human.

## Parallelism rules

- At most **3** implementation tasks at once (plus their QA gates and architect unblocks). More
  agents means more merge risk and noisier builds for little gain.
- Only start tasks returned together by `taskctl next` (disjoint `paths`). Two agents building at
  the same time share `build/`; tell each implementation agent to use its own build dir
  `build-<ID>` and QA to use `build-qa-<ID>` so parallel builds don't clobber each other
  (add that to the prompts).
- Architecture-critical tasks (priority < 10) run alone.

## Error handling summary

| Situation | Action |
|---|---|
| Subagent errors/crashes | retry once with a fresh agent; then block with the error text |
| QA FAIL | up to 2 fix rounds, then block → architect |
| Engineer BLOCKED (spec question) | block → architect ADR → unblock → re-run |
| Build broken on main by a committed task | create a P0 fix task (owner = module owner, priority 0) and run it before anything else |
| Git commit fails (hook, conflict) | do not bypass hooks; log, fix the cause, retry; never `--no-verify` |
| All remaining tasks blocked | run architect unblock for each; if architect cannot unblock, log and keep ticking |

## Roadmap frame

`spec/ROADMAP.md` is binding. Planning tasks (T2NN, owner architect, priority 6 → run alone) expand a
phase's roadmap epics into tasks; gate tasks (T3NN, owner qa) close phases. Never create tasks outside
the roadmap: if work appears that no epic covers, hand it to the architect for an ADR + new epic.
`deferred` tasks are ignored until the owner schedules them.

## Phase gates (milestones)

When the last task of a phase lands (see `phase:` in task files), spawn axiom-architect for a
short phase review (`_workspaces/reports/phase-<P>-review.md`): spec drift, shortcuts to retire,
requirement coverage of the phase (`reqcov.py --phase <P>` — every mapped requirement implemented
or explicitly re-mapped), backlog adjustments for the next phase. Commit its board/spec changes.

## Test scenarios

- **Normal**: board has T001 ready → start → architect produces `spec/SPEC-01…` + report → QA
  PASS → finish → commit `T001: …` → next batch (T002, T004 in parallel) starts immediately.
- **QA fail then pass**: T010 lexer misses `0b` literals → QA FAIL with finding → SendMessage to
  `T010-impl` → fix + regression test → QA PASS → commit.
- **Blocked**: T039 engineer finds specs disagree on partial-move of Drop types → BLOCKED →
  architect writes ADR-0007, unblocks → T039 re-runs and passes.
- **Stale after restart**: session ended with T020 in `doing/` → next tick finds no live agent →
  report missing → requeue → re-run reads old report and continues.
