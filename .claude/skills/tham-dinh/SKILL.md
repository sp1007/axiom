---
name: tham-dinh
description: Lệnh "thẩm định" — chạy đội 4 agent axiom-auditor song song để thẩm định lại tài liệu, roadmap, board task và harness của dự án compiler Axiom (self-host có khả thi không, bám ladder 0263 chưa, task có thực thi được không, quy trình có nhất quán không), rồi gộp kết quả, sửa lỗi rõ ràng và trình các điểm cần chủ dự án quyết định. Dùng khi người dùng gõ /tham-dinh, "thẩm định", "audit kế hoạch", "rà soát lại task/tài liệu", "kiểm tra lại toàn bộ", hoặc trước khi chạy /tu-dong lần đầu.
model: sonnet
---

# /tham-dinh — independent plan audit

Run this **before** `/tu-dong` (never while autopilot has tasks in `doing/`: the fixes edit the
board). Autopilot state: if `_workspaces/autopilot.json` has `enabled: true`, tell the user to run
`/tu-dong dừng` first and stop.

## Why
The tasks were written by one author; gaps surfaced only when the owner pointed at them (raw
pointers planned after self-host although `Vec` needs them, missing `char`, slices, UTF-16…).
Requirement extraction (T092–T111) maps docs → tasks and counts an item "planned" if some epic
holds it — it does not ask whether it arrives *in time*. Four independent lenses do.

## Procedure

1. `python .claude/skills/axiom-tasks/scripts/harness_check.py` and `taskctl.py validate` must pass.
   Output dir: `_workspaces/audit/<YYYY-MM-DD>/`.
2. Spawn the four auditors **in one message, in parallel, background** — prompts in
   `references/lenses.md` (copy each verbatim, fill `<date>`):

   | name | lens | model |
   |---|---|---|
   | `audit-A1` | self-host feasibility | opus |
   | `audit-A2` | ladder conformance (0263 / tasks/0260) | opus |
   | `audit-A3` | task executability | sonnet |
   | `audit-A4` | process & document consistency | sonnet |

   `subagent_type: "axiom-auditor"` (if rejected: `general-purpose` and start the prompt with
   `You are axiom-auditor. First read .claude/agents/axiom-auditor.md and follow it exactly.`).
   Tell the user in Vietnamese (≤ 3 lines) that the audit runs and roughly takes 20–40 minutes.
3. When all four have finished (task notifications; if one crashes, rerun it once), spawn
   `axiom-architect` with `model: "opus"` to consolidate — judging which findings are real, mechanical
   or owner decisions needs design judgement, and this session runs on Sonnet. Give it the four files:
   - dedupe across lenses; keep the highest severity; drop findings disproven by reading the cited
     file (note them under "Rejected" with the reason);
   - write `_workspaces/audit/<date>/SUMMARY.md`: Vietnamese `## Tóm tắt` first, then a table
     `id | severity | title | fix | status (fixed / owner decision / rejected)`.
4. **Fix** every CONFIRMED BLOCKER/MAJOR whose fix is mechanical and inside the roadmap rules (add
   dependency, add path, add acceptance line, split a task, add a missing core task in the right
   phase with the next free id of that phase block): spawn `axiom-architect` (opus) with
   SUMMARY.md and the list; it edits board/ROADMAP/skills, runs `taskctl.py validate` and
   `harness_check.py`, and writes an exact `## Files changed` list in the summary.
   Anything that changes scope, the roadmap rules R1–R8, or owner decisions → **do not fix**; list
   it under `## Cần chủ dự án quyết định` with the options and a recommendation.
5. Update `CLAUDE.md` history, commit only the listed files + `_workspaces/audit/<date>/`
   (`arch: plan audit <date> — <n> fixes`, trailer), never `docs/`.
6. Report to the user in Vietnamese: counts per severity, what was fixed, the decisions they need to
   make (numbered, each with a recommendation). Ask only those decisions; then stop.

## Test scenarios
- Normal: four files arrive → 30 findings → 18 fixed mechanically, 4 owner decisions, 8 rejected
  as duplicates/disproved → commit → Vietnamese report with 4 numbered questions.
- One auditor crashes → rerun once → still failing → consolidate the other three and say which lens
  is missing.
