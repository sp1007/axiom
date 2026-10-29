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

**Decide and report (owner decision 2026-10-01).** The owner has delegated design and process
decisions: neither the orchestrator nor any agent stops to ask. Whoever meets an open question
chooses the best option, applies it, records the options and the rationale (ADR for language/compiler
design, ROADMAP change log for scope/ordering, CLAUDE.md history for harness/process) and reports
afterwards. Hard limits that no decision may cross: never edit or stage `docs/`; never force-push or rewrite remote history (a plain `git push origin <branch>` after each accept is allowed, orchestrator only); T224
stays `deferred`; a requirement in `spec/requirements/OWNER.md` is never dropped or weakened
silently (re-planning it needs an ADR that names it and appears in the report to the owner).

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

## Files and scripts

`S=.claude/skills/axiom-tasks/scripts` below. The scripts find the repository root themselves; run
them from any directory.
- Board: `_workspaces/tasks/{todo,doing,done}` via `python $S/taskctl.py` (axiom-tasks skill).
- Reports: `_workspaces/reports/<ID>-report.md` (last line `STATUS: COMPLETE round=<n>`),
  `<ID>-qa.md` (last line `VERDICT: PASS|FAIL round=<n>`), `unblock-<ID>.md`.
- Autopilot state: `_workspaces/autopilot.json`, changed **only** through `python $S/autopilot.py`
  (`run`, `drop`, `session`, `infra-fail`, `infra-ok`, `backoff`, `check-board`, `stuck`, `unstuck`,
  `set`, `show`) — never hand-edit the JSON.
- Log: `_workspaces/logs/autopilot.log`, one line per decision: `YYYY-MM-DD HH:MM <ID> <event> <detail>`.

## Phase 0 — context check (every invocation)

0. `SendMessage` and `TaskStop` are deferred tools: load them once per session with `ToolSearch`
   (`select:SendMessage,TaskStop`) before the first fix round or hang check.
1. `python $S/taskctl.py status` and `python $S/autopilot.py show`. A non-zero exit of `status`
   is a board error (duplicate id, malformed task, wrong root): fix the named file (architect) before
   anything else; never conclude that the board is empty or finished from an error.
2. Decide the mode:
   - user names a task (`T010`) → **single task run** (or re-run: if it is in `done/`, redo it only if
     the user asked; otherwise run a follow-up task).
   - user gives feedback on a finished task ("parser recovery is weak") → architect creates a
     follow-up task (or re-opens scope) → run it.
   - otherwise → **batch run**: free = `max_parallel` (3) − tasks in `doing`; if free > 0,
     `python $S/taskctl.py next --max <free>` and run those.
3. Interrupted work — see "Recovery" below: `python $S/autopilot.py session`, then
   `python $S/taskctl.py recover <ID>` for every task in `doing/` that has no live agent of this session.

## Procedure: run one task `<ID>` (owner from the task front-matter)

1. `python $S/taskctl.py start <ID> --agent <ID>-impl`, then
   `python $S/autopilot.py run <ID> --stage impl --agent <ID>-impl --round 0`.
   Call `autopilot.py run` again on **every** stage change (`--stage qa|fix|unblock`, `--round <n>`):
   it records agent, stage, round, start time and session — the hang check and restart recovery
   depend on it.
2. Spawn the implementation agent (background):
   - `name: "<ID>-impl"`, `subagent_type: <owner>`, `model: <task model>`, `run_in_background: true`
   - prompt (fill in):
     ```
     Task <ID>: <title>. Task file: _workspaces/tasks/doing/<file>.
     Read the task file, your agent definition, and the skills it lists. Previous attempt files, if
     any: _workspaces/reports/<ID>-report.md, <ID>-qa.md — read them first and continue.
     Edit files only in the main working tree and only under this task's `paths`/`locks`. Other
     tasks run in parallel in the same tree: never touch, fix or delete their files, and do not judge
     your work by a build of the main tree (their unfinished files may break it).
     Build and test in your snapshot: `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot <ID>`
     creates/refreshes build-snap-<ID>/ (last commit + only your changes; run it again after each
     batch of edits). Build there (build dir build-snap-<ID>/build) and run the full suite there with
     --compiler pointing at that build. Quick local builds may use build-<ID> in the main tree.
     Write _workspaces/reports/<ID>-report.md (format in the axiom-tasks skill) with an exact
     "## Files changed" list (`- path` per line, every created/modified/deleted file) and, as its
     LAST line, "STATUS: COMPLETE round=0" (or "STATUS: BLOCKED <reason>"). Do not commit or push; do not
     move task files; never edit docs/. Open questions: decide, record the rationale in the report
     (the architect turns design decisions into ADRs) — do not ask.
     Finish with "<ID> COMPLETE" or "<ID> BLOCKED: <reason>".
     ```
3. When the agent finishes (task notification), classify the result **before** anything else:
   - **infrastructure failure** (see "Infrastructure failures") → that procedure; no attempt is burned.
   - `BLOCKED` → `python $S/taskctl.py block <ID> --reason "<reason>"`, `python $S/autopilot.py drop <ID>`;
     the architect unblock is queued (below).
   - `COMPLETE` but the report is missing or has no `STATUS: COMPLETE` last line → send it back once
     (SendMessage to `<ID>-impl`: "write the report with the STATUS line"); still missing →
     `python $S/taskctl.py requeue <ID> --reason "no report"`.
   - otherwise `python $S/autopilot.py infra-ok` and go on to the gate.
4. **QA gate**: `python $S/taskctl.py snapshot <ID>` (refresh), `python $S/autopilot.py run <ID> --stage qa --agent <ID>-qa --round <n>`.
   The gate agent is the task's `reviewer` (axiom-qa for most tasks; axiom-architect for tasks owned
   by axiom-qa, so nobody grades their own work — its prompt adds "follow the Gate protocol in
   .claude/agents/axiom-qa.md"). Spawn `name: "<ID>-qa"`, `subagent_type: <reviewer>`,
   `model: <task gate_model>` (`opus` after escalation), background, prompt:
   ```
   Gate task <ID>, round <n>. Task file: …  Report: _workspaces/reports/<ID>-report.md.
   Follow your Gate protocol with these overrides:
   - Build and test ONLY inside the snapshot build-snap-<ID>/ (already created: last commit + exactly
     this task's change set). Build dir build-snap-<ID>/build; run the full suite from inside the
     snapshot. Never build or test the main working tree: other tasks are half-way through edits there.
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes <ID>` lists what will be committed;
     any REFUSED line (unlisted changed file, entry outside the task's paths, glob) is a FAIL finding.
   - Tests you add: write them in the MAIN tree under the task's paths, list them under
     "## Files changed" in the QA file, rerun `taskctl.py snapshot <ID>` and test again.
   - Write _workspaces/reports/<ID>-qa.md: a "## Round <n>" section, and as the LAST line of the file
     "VERDICT: PASS round=<n>" or "VERDICT: FAIL round=<n>" (findings above it).
   ```
5. On the QA result (read the last `VERDICT:` line of `<ID>-qa.md`, not the chat summary):
   - **PASS** → `python $S/taskctl.py accept <ID>` — one command that re-checks the verdict, checks
     the change set, moves the task to `done/` and makes the single commit (code + both reports +
     board). Exit 1 = refused, task still in `doing/`: read the `REFUSED` lines. An
     unlisted changed file under the task's paths → if it clearly belongs to the task, rerun with
     `--include-unlisted`; otherwise send it back to the owner agent. A failed git commit (hook) rolls
     the task back to `doing/`: fix the cause, rerun `accept`; never `--no-verify`.
     Then push (owner decision 2026-10-29): `git push origin $(git rev-parse --abbrev-ref HEAD)` —
     plain fast-forward only, never `--force`/`-f`/`--delete`. A rejected push (remote ahead) or a
     network/auth error is logged (`<ID> push-failed <reason>`) and retried after the next accept or
     tick; it never blocks, rolls back or requeues the task, and never triggers a pull/rebase/force.
     Then `python $S/autopilot.py drop <ID>`, `python $S/taskctl.py snapshot <ID> --remove`, delete
     `build-<ID>`, log.
   - **FAIL**, round 0 → round 1: `autopilot.py run <ID> --stage fix --agent <ID>-impl --round 1`;
     `SendMessage` to `<ID>-impl` with the path of the QA file and "fix every finding, add regression
     tests, update the report, last line STATUS: COMPLETE round=1". If the agent cannot be resumed,
     spawn a fresh owner agent (task model) with the implementation prompt plus the QA file. Gate again.
   - **FAIL**, round 1 → round 2, **escalate**: fresh owner agent `name: "<ID>-fix2"`,
     `model: "opus"`, prompt = implementation prompt + the QA file, report ends `STATUS: COMPLETE
     round=2`; re-gate with `model: "opus"`.
   - **FAIL**, round 2 → `python $S/taskctl.py block <ID> --reason "QA failed 3 times: <top findings>"`,
     `autopilot.py drop <ID>` → architect unblock.
6. After any task leaves `doing/` (done or blocked): immediately refill the free slots with
   `python $S/taskctl.py next --max <free>` (do not wait for the 30-minute safety tick) — unless
   `python $S/autopilot.py backoff` exits 3.

## Infrastructure failures (rate limit, quota, API or tool errors)

A failure is **infrastructure**, not the task's fault, when the agent's result text is an error such
as rate limit / 429 / quota or usage limit / overloaded / 5xx / API or connection error / tool or
permission error, or the agent ended within about 2 minutes without touching its report or any file.
Never count it as an attempt, never block the task for it, never send it to the architect:

| Stage that failed | Action |
|---|---|
| impl | `python $S/taskctl.py requeue <ID> --infra --reason "<error text>"`, `python $S/autopilot.py drop <ID>` |
| fix, qa | leave the task in `doing/`; `python $S/autopilot.py drop <ID>` (the next tick runs `recover` and respawns that stage) |
| unblock | `python $S/taskctl.py unblock-end <ID>` (no `--failed`), `python $S/autopilot.py drop <ID>` |

Then `python $S/autopilot.py infra-fail --reason "<error text>"`: it sets a backoff of 30, then 60,
then 120 minutes (capped). While `python $S/autopilot.py backoff` exits 3, start **no** agent of any
kind (implementation, gate, fix, unblock, review); bookkeeping that needs no agent (`reconcile`,
`accept` of a PASS already on disk) continues. The first agent that completes normally clears it
(`infra-ok`). If the orchestrator's own turn is cut off by a session limit, nothing is lost: state is
on disk, and the next tick (cron, or the owner running `/tu-dong` again) recovers it — agents that
died silently in the same session are found by `overdue.py` (`probe`) and resumed.

## Recovery (session restart, crash, tick)

`python $S/autopilot.py session` compares the stored session token with the current process. On
"new session" every `running` entry is dead (background agents never outlive their session) — there
is no liveness guessing. For each task in `doing/` without a live agent of this session run
`python $S/taskctl.py recover <ID>` and do what it prints (it reads `autopilot.json` stage/round, the
report's `STATUS:` line, the QA `VERDICT:` line and their times):

| Output | Action |
|---|---|
| `accept` | step 5 PASS |
| `qa <n>` | step 4 with round n (fresh gate agent) |
| `fix <n>` | step 5 FAIL for round n with a fresh owner agent (n = 2 → Opus) and the QA file |
| `block` | `taskctl.py block <ID> --reason …` → architect unblock |
| `requeue` | `python $S/taskctl.py requeue <ID> --no-attempt --reason "restart"`, `autopilot.py drop <ID>`; the task is picked again and continues from its files |

A dead `unblock` entry: `python $S/taskctl.py unblock-end <ID> --failed`, `autopilot.py drop <ID>`.
`python $S/taskctl.py reconcile --commit` repairs a task that reached `done/` without its commit.
Unpushed commits (`git status -sb` shows `ahead`) are pushed by the next accept or tick.

## Procedure: architect unblock

One unblock at a time, never beside a critical task, at most 2 cycles per task:

1. `python $S/taskctl.py unblock-begin <ID>` — exit 0: lock taken, go on; exit 3: wait (a critical
   task runs or waits to run, or another unblock runs) and try again at the next event; exit 4: the
   task was **parked** (2 unblock cycles used, or 2 failed unblock agents) — do not spawn; it is
   reported in `_workspaces/STUCK.md`.
2. `python $S/autopilot.py run <ID> --stage unblock --agent unblock-<ID>`; spawn
   `name: "unblock-<ID>"`, `subagent_type: axiom-architect`, `model: "opus"` (always), background:
   ```
   Task <ID> is blocked. Task file: …; report/QA files: …; blocker: <reason>.
   Follow your Unblocking protocol (ADR / split / prerequisite / rescope). You decide: choose the
   best option, apply it, and record options + rationale (ADR via
   `python .claude/skills/axiom-tasks/scripts/taskctl.py adr-next <slug>` — never pick an ADR number
   by hand; scope/ordering changes also in the ROADMAP change log). Do not ask the owner. Limits:
   never edit docs/, T224 stays deferred, an OWNER.md requirement is never dropped silently.
   New task files: id from `taskctl.py new-id --phase <P>`, check with `taskctl.py lint`; a task you
   replace by a split: `taskctl.py supersede <ID> --by <new>`; otherwise `taskctl.py unblock <ID>`.
   Run `taskctl.py validate` and harness_check.py. Write _workspaces/reports/unblock-<ID>.md with a
   Vietnamese "## Tóm tắt" and an exact "## Files changed" list.
   ```
3. When it finishes: `python $S/taskctl.py commit-report _workspaces/reports/unblock-<ID>.md
   --subject "arch: unblock <ID> — <summary>"` (stages exactly the listed files + the report + the
   board; refuses entries inside a running task's paths), then `python $S/taskctl.py unblock-end <ID>`
   and `python $S/autopilot.py drop <ID>`.
   If the agent crashed, was killed as hung, or left the task blocked without an explanation:
   `python $S/taskctl.py unblock-end <ID> --failed` (the second failure parks the task).

## Parallelism rules

- At most **3** implementation tasks at once (`max_parallel`), plus their gates, plus at most one
  architect unblock.
- Only start tasks returned by `taskctl next` (disjoint `paths`/`locks`, also disjoint from a
  running unblock, which holds `spec` and `_workspaces/tasks`).
- All agents edit the one main tree; verdicts come only from snapshots (`build-snap-<ID>`), so a
  gate never fails because of another task's half-written files (axiom-tasks, "What makes parallel
  work safe").
- Architecture-critical tasks (priority < 10) run alone. When one becomes ready while others run,
  `next` returns nothing (drain): let the running tasks and a running unblock finish, then the
  critical task starts alone; `unblock-begin` waits while it runs. Idle slots during a drain are
  intended — do not start other tasks by hand.
- A charged `requeue` blocks a task at its 3rd attempt (crash loops go to the architect); `unblock`
  resets the attempt budget and is itself capped at 2 cycles per task. `start` refuses a task whose
  dependencies are not done.

## Error handling summary

| Situation | Action |
|---|---|
| Rate limit / quota / API or tool error | "Infrastructure failures": `requeue --infra`, backoff, no attempt burned, no unblock |
| Subagent crashes for another reason | charged `requeue` (3rd attempt → blocked → architect) |
| QA FAIL | up to 2 fix rounds (2nd on Opus), then block → architect |
| Engineer BLOCKED (spec question) | block → architect decides (ADR) → unblock → re-run |
| `accept` refused | read the REFUSED lines: fix the report's Files changed, or `--include-unlisted`; never bypass |
| Git commit fails (hook, conflict) | task is rolled back to doing; fix the cause, rerun `accept`; never `--no-verify` |
| Done task without a commit (crash) | `taskctl.py reconcile --commit` |
| Build broken on main by a committed task | architect creates a P0 fix task (priority 0, owner = module owner); it runs alone before anything else |
| Task parked (unblock cap) | stays parked, listed in `_workspaces/STUCK.md`; other work continues |
| Nothing ready, nothing running, tasks left | `taskctl.py stuck --write`; after 3 such ticks the autopilot stops and reports (tu-dong) |
| Board error (exit 2) | fix the named task file; never treat as an empty or finished board |

## After self-host: axiom0 freeze (ROADMAP R3)

When T087 is accepted the Stage-0 compiler is frozen. Immediately after `accept T087`:
1. `git tag axiom0-frozen` (local tag; tags are not pushed). From then on `harness_check.py` fails if a
   commit after the tag touches `bootstrap/axiom0` unless its subject names an `AX0-FIX` task, and
   warns about uncommitted changes there.
2. A change to axiom0 that is needed to keep rebuilding axiomc is its own task: title starting
   `AX0-FIX-<nn>`, phase `P10-selfhost`, created by the architect with the reason, `paths` limited to
   the files fixed, normal QA gate. No other task may list or edit `bootstrap/axiom0`.
3. Compiler under test: tasks of P11+ change `compiler/` and `std/` (Axiom sources). Their snapshot
   builds its own axiomc with the bootstrap command recorded by the self-host tasks (T086/T087 report
   and the axiom-qa Gate protocol) into `build-snap-<ID>/build`, and the suite runs with `--compiler`
   pointing at that stage-2 axiomc. In the prompts above replace "build there" accordingly; nothing
   else in the procedures changes.
4. Every gate after T087 also runs `harness_check.py` (freeze check).

## Roadmap frame

`spec/ROADMAP.md` is binding. Planning tasks (T2NN, owner architect, priority 6 → run alone) expand a
phase's roadmap epics into tasks; gate tasks (T3NN, owner qa) close phases. Never create tasks outside
the roadmap: if work appears that no epic covers, the architect writes an ADR + new epic.
`deferred` and `parked` tasks are ignored until the owner releases them.

## Phase gates (milestones)

When the last task of a phase lands (see `phase:` in task files), spawn axiom-architect for a
short phase review (`_workspaces/reports/phase-<P>-review.md`, starting with a Vietnamese
`## Tóm tắt` for the owner): spec drift, shortcuts to retire, `harness_check.py` clean,
`taskctl.py reconcile` clean, requirement coverage of the phase (`reqcov.py --phase <P>` and
`reqcov.py --strict` — every mapped requirement implemented or explicitly re-mapped), backlog
adjustments for the next phase, with an exact `## Files changed` list. Commit it with
`taskctl.py commit-report _workspaces/reports/phase-<P>-review.md --subject "arch: phase <P> review"`.

## Test scenarios

- **Normal**: board has T001 ready → start → architect produces `spec/SPEC-01…` + report ending
  `STATUS: COMPLETE round=0` → snapshot → QA PASS → `accept` → commit `T001: …` → the next ready tasks
  start immediately (critical ones one at a time, others up to three with disjoint paths).
- **QA fail then pass**: T010 lexer misses `0b` literals → `VERDICT: FAIL round=0` → SendMessage to
  `T010-impl` → fix + regression test, `STATUS: COMPLETE round=1` → `VERDICT: PASS round=1` → `accept`.
- **Blocked**: T039 engineer finds specs disagree on partial-move of Drop types → BLOCKED →
  `unblock-begin` → architect reserves an ADR with `adr-next`, decides, `unblock` → `commit-report` →
  `unblock-end` → T039 re-runs and passes.
- **Restart**: session ended with T020 in `doing/` at stage qa → `autopilot.py session` says new
  session → `recover T020` prints `qa 0` → fresh gate on a fresh snapshot.
- **Rate limit**: three agents die with "rate limit" → impl tasks `requeue --infra` (attempts
  unchanged), `infra-fail` → backoff 30 min → ticks start nothing until it expires → work resumes.
- **Parallel isolation**: T037 and T038 run together; T038's half-written `match.c` does not compile;
  T037's gate builds `build-snap-T037` (HEAD + T037's files only) and passes.
