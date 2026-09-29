---
name: tu-dong
description: Lệnh "tự động" — bật chế độ autopilot cho dự án compiler Axiom. Tạo monitor chạy mỗi 5 phút; luôn giữ tối đa 3 task chạy song song — hễ có chỗ trống (task xong hoặc bị chặn) là tự xác định task tiếp theo không đụng thư mục đang làm và chạy ngay bằng subagent, tự QA, tự commit sau mỗi task, không hỏi người dùng, không ngủ đông. Dùng khi người dùng gõ /tu-dong, "tự động", "chạy tự động", "autopilot", "cứ chạy tiếp đi", "bật tự động"; cũng dùng cho "tự động dừng"/"dừng tự động" (tắt) và "tự động trạng thái"/"tiến độ" (xem trạng thái).
---

# /tu-dong — Axiom autopilot

The user has given standing authorisation for this mode: pick tasks, run subagents, gate with QA,
move task files, and **commit locally after every accepted task** — without asking. Do not push to
any remote. Do not pause to ask questions; decisions go to axiom-architect (ADRs). Keep going until
the board is finished or the user says stop.

## Arguments

- (none) / `bật` / `start` → start autopilot (below)
- `dừng` / `stop` / `tắt` → `CronDelete` the job id from `_workspaces/autopilot.json`, set
  `enabled: false`, let running agents finish (their completion notifications are still processed:
  QA/commit happen, but no new task is started). Report.
- `trạng thái` / `status` → `taskctl.py status`, running agents, last 10 lines of
  `_workspaces/logs/autopilot.log`, cron job id. Report in Vietnamese, short.

## Start procedure

1. Ensure the repo is a git repo on a working branch (`git rev-parse --abbrev-ref HEAD`); if on
   `main`/`master`, that is acceptable for this local, single-user project — the user asked for
   automatic commits here. Never force-push, never rewrite history.
2. `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` — fix board errors first
   (architect) if invalid.
3. `CronList`; if an autopilot job already exists, reuse it. Otherwise `CronCreate` with
   `cron: "*/5 * * * *"`, `recurring: true`, `prompt: "/axiom-tick"`.
4. Write `_workspaces/autopilot.json`:
   ```json
   {"enabled": true, "cron_id": "<id>", "cron_created": "YYYY-MM-DD HH:MM",
    "max_parallel": 3, "running": {}}
   ```
5. Run one tick **immediately** (follow the axiom-tick skill) — don't wait 5 minutes for the first.
6. Tell the user (Vietnamese, ≤ 6 lines): autopilot on, cron id, which tasks started, how to stop
   (`/tu-dong dừng`), and that session cron jobs expire after 7 days and live only while this
   Claude session is open (the tick renews the job automatically before expiry; if the session is
   closed, run `/tu-dong` again — stale tasks are resumed automatically).

## Behaviour contract ("không ngủ đông")

- Idle is never a stopping point: whenever a task finishes or blocks, refill its slot right away
  (the orchestrator does this; owner decision 2026-09-29 replaced "only when doing/ is empty"); the 5-minute tick is the safety net that catches
  anything missed (stale tasks, crashed agents, blocked tasks awaiting the architect).
- Never end a turn by asking the user what to do next while autopilot is enabled. Summarise in one
  or two lines **in Vietnamese** and continue.
- If the whole board is done: run the final phase review (architect), commit, `CronDelete`, set
  `enabled: false`, and report completion.
