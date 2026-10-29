---
name: tu-dong
description: Lệnh "tự động" — bật chế độ autopilot cho dự án compiler Axiom. Tạo nhịp giám sát dự phòng mỗi 30 phút (tiến độ chính chạy theo sự kiện khi subagent xong); luôn giữ tối đa 3 task chạy song song — hễ có chỗ trống (task xong hoặc bị chặn) là tự xác định task tiếp theo không đụng thư mục đang làm và chạy ngay bằng subagent, tự QA, tự commit sau mỗi task, không hỏi người dùng, không ngủ đông. Dùng khi người dùng gõ /tu-dong, "tự động", "chạy tự động", "autopilot", "cứ chạy tiếp đi", "bật tự động"; cũng dùng cho "tự động dừng"/"dừng tự động" (tắt) và "tự động trạng thái"/"tiến độ" (xem trạng thái).
model: sonnet
---

# /tu-dong — Axiom autopilot

The user has given standing authorisation for this mode: pick tasks, run subagents, gate with QA,
move task files, **commit after every accepted task and push it** (`git push origin <branch>`, plain
fast-forward; owner decision 2026-10-29) — without asking. Do not pause to ask questions: design and process decisions are delegated — the
architect (or whoever meets the question) decides the best option, applies it, records the rationale
(ADR / ROADMAP change log / CLAUDE.md history) and it is reported afterwards. Hard limits: never edit
or stage `docs/`, never force-push or rewrite remote history, T224 stays deferred, an OWNER.md requirement is never dropped silently.
Keep going until the board is finished, the board is stuck (reported, see below) or the user says stop.

`S=.claude/skills/axiom-tasks/scripts`. `_workspaces/autopilot.json` is written only through
`python $S/autopilot.py`.

## Arguments

- (none) / `bật` / `start` → start autopilot (below)
- `dừng` / `stop` / `tắt` → `CronDelete` the job id shown by `python $S/autopilot.py show`,
  `python $S/autopilot.py set enabled false`, let running agents finish (their completion
  notifications are still processed: gate/accept happen, but no new task is started). Report.
- `trạng thái` / `status` → `python $S/taskctl.py status`, `python $S/autopilot.py show` (running
  agents, backoff, stuck counter), `python $S/overdue.py`, last 10 lines of
  `_workspaces/logs/autopilot.log`, `_workspaces/STUCK.md` if it exists. Report in Vietnamese, short.

## Start procedure

0. Load the deferred tools first: `ToolSearch` with query
   `select:CronCreate,CronList,CronDelete,SendMessage,TaskStop` (they cannot be called before their
   schemas are loaded). Models are automatic: this skill runs on Sonnet (front-matter), every subagent
   gets its model from the task file (axiom-compiler model policy). Never ask the user to switch.
   If the Cron tools do not exist in this runtime, continue without them (step 3 says how).
1. Ensure the repo is a git repo on a working branch (`git rev-parse --abbrev-ref HEAD`); if on
   `main`/`master`, that is acceptable for this local, single-user project — the user asked for
   automatic commits here. Never force-push, never rewrite history.
2. `python $S/taskctl.py validate` and `python $S/harness_check.py` — fix errors first (architect)
   if either fails; `python $S/taskctl.py reconcile --commit` so no accepted work is left uncommitted.
3. `CronList`; if an autopilot job already exists, reuse it. Otherwise `CronCreate` with
   `cron: "7,37 * * * *"` (every 30 minutes, off the :00/:30 marks), `recurring: true`,
   `prompt: "/axiom-tick"`. Without Cron tools: use the `loop` skill (`/loop 30m /axiom-tick`) if it
   is available, otherwise run event-driven only and tell the user that the safety tick must be
   triggered by hand with `/axiom-tick`; use `manual` as the cron id.
4. `python $S/autopilot.py init --cron <id>` — writes the base state: `enabled`, cron id and time,
   `max_parallel` 3, timeouts (impl/fix 180 min, 300 for extraction and port phases, gate/unblock 60),
   the current session token, `board_total`, counters reset. It keeps `running` entries; the tick's
   session step decides whether they are alive.
5. Run one tick **immediately** (follow the axiom-tick skill) — don't wait for the first cron firing.
   The tick recovers work left by an earlier session (`autopilot.py session` → `taskctl.py recover`).
6. Tell the user (Vietnamese, ≤ 6 lines): autopilot on, cron id, which tasks started, how to stop
   (`/tu-dong dừng`), and that session cron jobs expire after 7 days and live only while this
   Claude session is open (the tick renews the job automatically before expiry; if the session is
   closed or was cut off by a usage limit, run `/tu-dong` again — interrupted tasks are recovered
   from their files, nothing is lost and no attempt is charged).

## Behaviour contract ("không ngủ đông")

- Idle is never a stopping point: whenever a task finishes or blocks, refill its slot right away
  (the orchestrator does this; owner decision 2026-09-29 replaced "only when doing/ is empty"); progress is event-driven (every subagent completion re-invokes the session, which
  advances the task and refills slots at once); the 30-minute tick is the safety net that catches
  anything missed (interrupted tasks, dead or hung agents, missing commits, blocked tasks awaiting
  the architect).
- Infrastructure failures (rate limit, quota, API errors) never burn task attempts and never go to
  the architect: the task is requeued with `--infra`, `autopilot.py infra-fail` starts a backoff of
  30 → 60 → 120 minutes, and ticks start nothing until it expires. The loop then resumes by itself.
- Never end a turn by asking the user what to do next while autopilot is enabled. Summarise in one
  or two lines **in Vietnamese** and continue.
- **Finished**: only when `python $S/autopilot.py check-board` exits 0 (nothing left in todo, doing,
  blocked or parked, at least one done task, and no task has vanished since the last tick). A script
  error, an empty board or a wrong directory is never "finished". Then: run the final phase review
  (architect), commit it with `taskctl.py commit-report`, `CronDelete`,
  `python $S/autopilot.py set enabled false`, and report completion.
- **Stuck stop**: when the tick has found the board stuck three times in a row (tasks remain, nothing
  is ready or running, nothing can be unblocked — typically parked tasks at the unblock cap or their
  dependants): `CronDelete`, `python $S/autopilot.py set enabled false`, and report in Vietnamese
  what `_workspaces/STUCK.md` lists (each stuck task and why) together with the option the architect
  recommends. Releasing a parked task is `python $S/taskctl.py unblock <ID> --owner-approved` after
  the owner says so; then `/tu-dong` again.
