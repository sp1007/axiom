---
name: axiom-tick
description: One scheduling tick of the Axiom autopilot (fired every 5 minutes by the /tu-dong cron job, or run manually with /axiom-tick). Checks running agents and the task board, resumes stale tasks, advances finished work through QA/commit, unblocks blocked tasks via the architect, and — if no task is in progress — picks the next parallel-safe batch and starts it. Use when the prompt is "/axiom-tick", "tick", "kiểm tra tiến độ và chạy tiếp".
---

# axiom-tick — one autopilot step

Fast when nothing needs doing: most ticks should cost one `taskctl status` and one log line. Never
ask the user anything. All actions follow the axiom-compiler orchestrator procedures.

## Steps

1. **Enabled?** Read `_workspaces/autopilot.json`. If missing or `enabled: false` → do nothing,
   reply "autopilot off" in one line. (Manual `/axiom-tick` with autopilot off still performs steps
   2–6 once.)
2. **Renew cron** if `cron_created` is older than 6 days: `CronCreate` a new `*/5 * * * *` job with
   prompt `/axiom-tick`, `CronDelete` the old id, update the file. (Session cron jobs expire after
   7 days — renewing keeps the loop alive.)
3. **Board**: `python .claude/skills/axiom-tasks/scripts/taskctl.py status --json`.
4. **Reconcile running work** — for each task in `doing`:
   - agent recorded in `running` and alive (`ListAgents`, or you received no completion yet in this
     session) → leave it.
   - completion already arrived but not processed (e.g. arrived mid-turn) → continue the
     orchestrator procedure from the right stage (impl → QA gate; QA → finish/commit or fix round).
   - no live agent (session restart / crash) → report says COMPLETE and no PASS QA → start QA gate;
     otherwise `taskctl requeue <ID> --reason stale` and drop it from `running`.
5. **Blocked tasks** without an active `unblock-<ID>` agent → spawn architect unblock (max 2 at a
   time).
6. **Start work** — only if `doing` is empty after step 4 (the user's rule: start new work only
   when nothing is in progress):
   `taskctl next --max <max_parallel>` → for each returned task run the orchestrator's
   "run one task" procedure (background subagents, own build dirs). If a returned task is
   architecture-critical (priority < 10), start only that one.
   If nothing is ready and nothing is blocked and todo is empty → board finished → follow the
   completion steps in tu-dong.
7. **Log** one line to `_workspaces/logs/autopilot.log`:
   `YYYY-MM-DD HH:MM tick done=<n> doing=<ids> blocked=<ids> started=<ids>`.
8. Reply with at most 2 lines (what changed). Do not stop the loop, do not ask questions.
