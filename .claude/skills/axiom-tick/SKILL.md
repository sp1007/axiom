---
name: axiom-tick
description: One scheduling tick of the Axiom autopilot (fired every 30 minutes by the /tu-dong cron job as a safety net, or run manually with /axiom-tick). Recovers work after a session restart, repairs missing commits, respects the infrastructure backoff, stops or probes hung agents, advances finished work through QA/accept, unblocks blocked tasks via the architect, and refills every free slot with the next parallel-safe tasks. Use when the prompt is "/axiom-tick", "tick", "kiểm tra tiến độ và chạy tiếp".
model: sonnet
---

# axiom-tick — one autopilot step

Fast when nothing needs doing: most ticks cost a handful of script calls and one log line. Never ask
the user anything. All actions follow the axiom-compiler orchestrator procedures (run one task,
infrastructure failures, recovery, architect unblock). `S=.claude/skills/axiom-tasks/scripts`; the
scripts work from any directory. Any script exiting 2 with a board error means "fix the named file",
never "the board is empty".

## Steps

0. **Tools**: if `SendMessage`, `TaskStop` or the Cron tools are not callable yet in this session,
   load them with `ToolSearch` (`select:CronCreate,CronList,CronDelete,SendMessage,TaskStop`).
1. **Enabled?** `python $S/autopilot.py show`. Missing state or `enabled: false` → reply "autopilot
   off" in one line and stop. (A manual `/axiom-tick` with autopilot off still performs steps 2–10 once.)
2. **Session** — `python $S/autopilot.py session`.
   - "same session" → running agents of this session are alive or will notify; nothing to do here.
   - "new session: dead running entries …" → every listed agent died with the old session. For each
     task entry: `python $S/taskctl.py recover <ID>` and perform the printed action (`accept` /
     `qa <n>` / `fix <n>` / `block` / `requeue` → `requeue --no-attempt`) as in axiom-compiler
     "Recovery"; for an `unblock` entry: `python $S/taskctl.py unblock-end <ID> --failed`. Drop each
     dead entry (`python $S/autopilot.py drop <ID>`) unless the action re-registered it.
   - Any task in `doing/` that has **no** running entry at all (dropped after an infrastructure
     failure, or state lost) is handled the same way with `recover`.
3. **Renew cron** if `cron_created` is older than 6 days: `CronCreate` a new `7,37 * * * *` job with
   prompt `/axiom-tick`, `CronDelete` the old id, `python $S/autopilot.py set cron_id <id>` and
   `set cron_created "<now>"`. (Session cron jobs expire after 7 days.)
4. **Reconcile commits** — `python $S/taskctl.py reconcile --commit`: a task that reached `done/`
   without its commit (crash between the two steps of `accept`, or a manual `finish`) is committed
   now. A refusal is logged and retried next tick; it never blocks the rest of the tick.
5. **Backoff** — `python $S/autopilot.py backoff`. Exit 3 (infrastructure backoff after a rate
   limit, quota or API error): start **no** agent in this tick — skip the agent-spawning parts of
   steps 6–9 (still `accept` a PASS verdict that is already on disk), log `backoff <minutes>` and
   finish. The next tick after the backoff expires resumes automatically.
6. **Completions not yet processed** (arrived mid-turn or while the session was limited): for each
   running entry whose agent has reported, continue the orchestrator procedure from its stage (impl →
   snapshot + gate; qa → `accept` or fix round; fix → gate; unblock → `commit-report` +
   `unblock-end`). A result that is an infrastructure error goes to "Infrastructure failures"
   (`requeue --infra` / drop, `autopilot.py infra-fail`), never to block or unblock.
7. **Hung or silent agents** — `python $S/overdue.py`, one line per entry with an action:
   - `recover` → as step 2.
   - `probe` (within its limit but no file activity for 45+ minutes) → `SendMessage` to the agent:
     "<ID>: continue your task; if you are finished, write the report/verdict line and reply". A live
     agent just continues; an agent that died in this session (rate limit, API error) is resumed
     from its transcript. Log it. If the send fails, treat the entry as dead (step 2).
   - `keep` (overdue but files still changing) → log only.
   - `kill` (overdue and idle, or past the hard cap of 2× the limit) → `TaskStop` the agent, log,
     then by stage: `impl`/`fix` → `python $S/taskctl.py requeue <ID> --reason "hung: <n> min in <stage>"`
     (charged; the 3rd blocks) and drop; `qa` → spawn a fresh gate once, a second hung gate →
     `taskctl.py block`; `unblock` → `python $S/taskctl.py unblock-end <ID> --failed` and drop.
   - `set-since` (legacy entry without a start time) → re-register it with `autopilot.py run`.
   Limits: 180 min impl/fix (300 for requirement extraction and port phases, or the task's
   `timeout_min:`), 60 min gate and unblock.
8. **Blocked tasks** (status `blocked`; never `deferred`, never `parked`) — for each, in id order:
   `python $S/taskctl.py unblock-begin <ID>`: exit 0 → spawn the architect unblock (axiom-compiler
   procedure) and stop this step — unblocks are serialised; exit 3 → wait (a critical task runs or
   waits, or an unblock is running); exit 4 → the task was parked (cap reached): log it.
9. **Start / refill work** (owner decision: keep every slot busy) — `python $S/taskctl.py status --json`;
   free = `max_parallel` − number of tasks in `doing`. If free > 0: `python $S/taskctl.py next --max <free>`
   → for each returned task run the orchestrator's "run one task" procedure. `next` already excludes
   paths/locks of running tasks and of a running unblock, returns a critical task (priority < 10)
   alone once nothing runs, and returns nothing while a critical task runs or waits (drain) — idle
   slots then are expected, not a stall.
10. **Finished or stuck?** Only when nothing is running and steps 8–9 started nothing:
    - `python $S/autopilot.py check-board` — exit 0: the board is finished → completion steps in
      tu-dong. Exit 2: board error or tasks vanished → log, run `taskctl.py validate`, do **not**
      finish. Exit 1: work remains but nothing can run →
    - `python $S/taskctl.py stuck --write` — exit 3: `_workspaces/STUCK.md` now lists every waiting
      task with the dependency it waits for and every blocked/parked task with its last log line.
      `python $S/autopilot.py stuck` counts the tick; on the first stuck tick spawn the architect
      once (opus) with STUCK.md to repair what it can decide itself (wrong dependency edge, missing
      task); at count ≥ 3 stop the autopilot as described in tu-dong ("stuck stop") and report the
      contents of STUCK.md to the owner in Vietnamese. This is a stop with a report, not a question.
    Whenever something is running or was started, `python $S/autopilot.py unstuck`.
11. **Log** one line to `_workspaces/logs/autopilot.log`:
    `YYYY-MM-DD HH:MM tick done=<n> doing=<ids> blocked=<ids> parked=<ids> started=<ids> [backoff=<min>]`.
12. Reply with at most 2 lines (what changed). Do not stop the loop except as step 10 says; do not
    ask questions.
