---
name: axiom-compiler
description: Orchestrator for building the Axiom compiler with the agent team (architect, frontend, semantics, backend, stdlib, qa). Runs board tasks end-to-end — start → implementation subagent → QA gate → fix rounds → done → auto-commit — in parallel batches, unblocks blocked tasks via the architect, and handles follow-ups. Use for ANY request to build/continue/implement/fix/test the Axiom compiler or run a specific task ("làm task T010", "tiếp tục compiler", "chạy lại task", "sửa lỗi QA", "làm lại phần lexer", "cập nhật kết quả", "run next task", "implement the parser"). For unattended continuous running use the tu-dong skill; this skill is the procedure it calls.
model: sonnet
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

**Model policy (owner decision 2026-09-30): Opus for design judgement, Sonnet for spec-driven work
that tests can verify.** Every spawn passes an explicit `model`:
- implementation agent → the task's `model:` field (defaults per agent: architect/semantics `opus`,
  frontend/backend/stdlib/qa `sonnet`; requirement extraction `sonnet`; phase gates `opus`);
- gate agent → the task's `gate_model:` (`sonnet`, `opus` for the critical spec tasks);
- architect unblock and phase reviews → `opus`;
- **escalation:** the second QA fix round always runs on a fresh owner agent with `model: "opus"`
  (and its re-gate on `opus`), because a Sonnet agent that failed twice rarely fixes it a third time.
The main session (orchestrator, `/tu-dong`, ticks, `/tham-dinh`) only coordinates: these skills carry
`model: sonnet` in their front-matter, so the session switches to Sonnet automatically while they
run — the owner never picks models by hand. Design discussions outside these skills keep the
session's own model.

Spawn with `subagent_type: "<agent-name>"`; if the
runtime rejects that type (agent files added mid-session are not yet registered), use
`subagent_type: "general-purpose"` and start the prompt with
`You are <agent-name>. First read .claude/agents/<agent-name>.md and follow it exactly.`

## Files

- Board: `_workspaces/tasks/{todo,doing,done}` via `python .claude/skills/axiom-tasks/scripts/taskctl.py`
- Reports: `_workspaces/reports/<ID>-report.md`, `<ID>-qa.md`
- Autopilot state: `_workspaces/autopilot.json` (see tu-dong); log `_workspaces/logs/autopilot.log`
  (append one line per decision: `YYYY-MM-DD HH:MM <ID> <event> <detail>`).

## Phase 0 — context check (every invocation)

0. `SendMessage` and `ListAgents` are deferred tools: load them once per session with `ToolSearch`
   (`select:SendMessage,ListAgents`) before the first fix round or stale check.
1. `taskctl.py status` and read `_workspaces/autopilot.json` if present.
2. Decide the mode:
   - user names a task (`T010`) → **single task run** (or re-run: if it is in `done/`, move it back
     with a note only if the user asked to redo it; otherwise run a follow-up task).
   - user gives feedback on a finished task ("parser recovery is weak") → architect creates a
     follow-up task (or re-opens scope) → run it.
   - otherwise → **batch run**: `taskctl.py next --max <3 − tasks in doing>` and run those.
3. Stale work: a task in `doing/` with no live agent (check `ListAgents` / autopilot.json) →
   if `<ID>-report.md` says COMPLETE and no PASS QA yet → go to step "QA gate"; else
   `taskctl.py requeue <ID> --reason stale` and treat as ready.

## Procedure: run one task `<ID>` (owner from the task front-matter)

1. `taskctl.py start <ID> --agent <ID>-impl`
2. Spawn implementation agent (background):
   - `name: "<ID>-impl"`, `subagent_type: <owner>`, `model: <task model>`, `run_in_background: true`
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
4. **QA gate**: the gate agent is the task's `reviewer` (axiom-qa for most tasks; axiom-architect
   for tasks owned by axiom-qa, so nobody grades their own work — its prompt adds "follow the Gate
   protocol in .claude/agents/axiom-qa.md"). Spawn `name: "<ID>-qa"`, `subagent_type: <reviewer>`,
   `model: <task gate_model>` (`opus` after escalation), background, prompt: `Gate task <ID>. Task file: … Report: _workspaces/reports/<ID>-report.md. Follow your
   Gate protocol and write _workspaces/reports/<ID>-qa.md ending with VERDICT: PASS|FAIL.`
5. On QA result (read the last `VERDICT:` line of `<ID>-qa.md`, not the chat summary):
   - **PASS** → `taskctl.py finish <ID>` → `taskctl.py commit <ID>` (auto-commit, local, never
     push) → log → remove from `running`.
     `taskctl commit` stages the "Files changed" lists of both `<ID>-report.md` and `<ID>-qa.md`
     (so QA-added tests are committed) plus both report files.
   - **FAIL**, round 0 → round = 1; `SendMessage` to `<ID>-impl` with the path of the QA file and
     "fix every finding, add regression tests, update the report (Round 1)". If the agent cannot be
     resumed, spawn a fresh owner agent (task model) with the same prompt plus the QA file. QA again.
   - **FAIL**, round 1 → round = 2; **escalate**: spawn a fresh owner agent `name: "<ID>-fix2"`,
     `model: "opus"`, prompt = implementation prompt + both QA files; re-gate with `model: "opus"`.
   - **FAIL**, round == 2 → `taskctl.py block <ID> --reason "QA failed 3 times: <top findings>"` →
     architect unblock.
6. After any task leaves `doing/` (done or blocked): immediately refill the free slots with
   `taskctl next --max <free slots>` (do not wait for the 5-minute tick).

## Procedure: architect unblock

Spawn `name: "unblock-<ID>"`, `subagent_type: axiom-architect`, `model: "opus"` (always), background:
`Task <ID> is blocked. Task file: …; report/QA files: …; blocker: <reason>. Follow your Unblocking
protocol (ADR / split / prerequisite / rescope), run taskctl validate, report what changed.`
The architect writes `_workspaces/reports/unblock-<ID>.md` with an exact `## Files changed` list.
Commit only those files plus the board: `git add -- <listed files> _workspaces/tasks` then
`git commit -m "arch: unblock <ID> — <summary>"` (+ trailer). Never `git add spec` wholesale — other
architect tasks may have half-written files there.
Unblocking never waits for the human.

## Parallelism rules

- At most **3** implementation tasks at once (plus their QA gates and architect unblocks). More
  agents means more merge risk and noisier builds for little gain.
- Only start tasks returned together by `taskctl next` (disjoint `paths`). Two agents building at
  the same time share `build/`; tell each implementation agent to use its own build dir
  `build-<ID>` and QA to use `build-qa-<ID>` so parallel builds don't clobber each other
  (add that to the prompts).
- Architecture-critical tasks (priority < 10) run alone. When one becomes ready while others run,
  `next` returns nothing (drain): let the running tasks finish, then the critical task starts alone.
  Idle slots during a drain are intended — do not start other tasks by hand.
- `requeue` blocks a task instead after 3 attempts (crash loops go to the architect); `unblock`
  resets the attempt budget. `start` refuses a task whose dependencies are not done.

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
short phase review (`_workspaces/reports/phase-<P>-review.md`, starting with a Vietnamese
`## Tóm tắt` for the owner): spec drift, shortcuts to retire,
`harness_check.py` clean, requirement coverage of the phase (`reqcov.py --phase <P>` — every mapped requirement implemented
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
