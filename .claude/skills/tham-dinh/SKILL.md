---
name: tham-dinh
description: Lệnh "thẩm định" — chạy đội 4 agent axiom-auditor song song để thẩm định lại tài liệu, roadmap, board task và harness của dự án compiler Axiom (self-host có khả thi không, bám ladder 0263 chưa, task có thực thi được không, quy trình có nhất quán không), rồi gộp kết quả, tự quyết định phương án tối ưu cho từng điểm, sửa và báo cáo lại cho chủ dự án. Dùng khi người dùng gõ /tham-dinh, "thẩm định", "audit kế hoạch", "rà soát lại task/tài liệu", "kiểm tra lại toàn bộ", hoặc trước khi chạy /tu-dong lần đầu.
model: sonnet
---

# /tham-dinh — independent plan audit

Run this **before** `/tu-dong` (never while autopilot has tasks in `doing/`: the fixes edit the
board). Autopilot state: if `python .claude/skills/axiom-tasks/scripts/autopilot.py show` reports
`enabled: true`, tell the user to run `/tu-dong dừng` first and stop.

## Why
The tasks were written by one author; gaps surfaced only when the owner pointed at them (raw
pointers planned after self-host although `Vec` needs them, missing `char`, slices, UTF-16…).
Requirement extraction (T092–T111) maps docs → tasks; `reqcov.py` now also checks timing (tier vs
phase, `needs`), but only for what the catalogue states. Four independent lenses look at the rest.

## Decision rule (owner decision 2026-10-01)

The owner has delegated all design and process decisions: this procedure **does not ask**. For every
finding that needs a choice, the consolidating architect lists the options, picks the best one,
applies it and records the rationale where it belongs (ADR for language/compiler design, ROADMAP
change log for scope or ordering, CLAUDE.md history for harness/process). The owner gets a report
afterwards and can overturn any item. Hard limits that no decision may cross: never edit or stage
`docs/`; never force-push; T224 stays `deferred`; a requirement in `spec/requirements/OWNER.md` is never
dropped or weakened silently (changing how or when it is delivered needs an ADR that names it and a
line in the report).

## Procedure

`S=.claude/skills/axiom-tasks/scripts`.

1. `python $S/harness_check.py` and `python $S/taskctl.py validate` must pass.
   Output dir: `_workspaces/audit/<YYYY-MM-DD>/`.
2. Spawn the four auditors **in one message, in parallel, background** — prompts in
   `references/lenses.md` (copy each verbatim, fill `<date>`):

   | name | lens | model |
   |---|---|---|
   | `audit-A1` | self-host feasibility | opus |
   | `audit-A2` | ladder conformance (0263 / tasks/0260) | opus |
   | `audit-A3` | task executability | sonnet |
   | `audit-A4` | process & document consistency | sonnet |

   `subagent_type: "axiom-auditor"` with the `model` of the table passed explicitly (it overrides the
   model named in the agent file); if the type is rejected: `general-purpose` and start the prompt
   with `You are axiom-auditor. First read .claude/agents/axiom-auditor.md and follow it exactly.`
   Tell the user in Vietnamese (≤ 3 lines) that the audit runs and roughly takes 20–40 minutes.
3. When all four have finished (task notifications; if one crashes, rerun it once; a rate-limit or
   API failure is retried after the limit resets, not counted as a crash), spawn `axiom-architect`
   with `model: "opus"` to consolidate — judging which findings are real needs design judgement, and
   this session runs on Sonnet. Give it the four files:
   - dedupe across lenses; keep the highest severity; drop findings disproven by reading the cited
     file (note them under "Rejected" with the reason);
   - write `_workspaces/audit/<date>/SUMMARY.md`: Vietnamese `## Tóm tắt` first, then a table
     `id | severity | title | decision / fix | status (fixed / decided / rejected)`.
4. **Fix and decide** — every CONFIRMED finding and every well-founded PLAUSIBLE BLOCKER/MAJOR is
   resolved now, including those that need a choice (decision rule above). Two fixers with disjoint
   scopes, in parallel (both `model: "opus"`, background), each given SUMMARY.md and the four files:
   - **plan fixer** — `axiom-architect`: `_workspaces/tasks/**`, `spec/**` (ROADMAP, ADRs via
     `taskctl.py adr-next`, requirements), `.claude/agents/**`, the domain skills. New tasks get ids
     from `taskctl.py new-id` and pass `taskctl.py lint`.
   - **harness fixer** — `axiom-architect` with the instruction "act as harness engineer":
     `.claude/skills/axiom-tasks/**`, the axiom-compiler / axiom-tick / tu-dong / tham-dinh skills,
     `.claude/hooks/**`, `.gitignore`. Script changes are tested on copies in temporary git
     repositories (`python $S/selftest.py`, extended with a check per fix), never on the real board.
     `.claude/settings.json` and `CLAUDE.md` are **not** edited by a subagent: the fixer writes the
     proposed file/text next to its report (`proposed-settings.json`, verified with
     `harness_check.py --settings`), and the main session applies it once the owner has approved.
   Each writes its part under `_workspaces/audit/<date>/` (`PLAN-FIXES.md`, `HARNESS-FIXES.md`):
   per finding what changed or why not, a Vietnamese `## Quyết định đã tự áp dụng` (options +
   rationale for every choice made), requests for the other fixer, and an exact `## Files changed`
   list. Both end with `taskctl.py validate` and `harness_check.py` passing.
5. Show the owner any proposed `settings.json` / `CLAUDE.md` change and apply it only on their
   approval (permission and hook changes are the one thing that is never decided on their behalf).
   Add one row to the `CLAUDE.md` history, then commit with
   `python $S/taskctl.py commit-report _workspaces/audit/<date>/SUMMARY.md --subject "arch: plan audit <date> — <n> fixes"`
   after copying both `## Files changed` lists (and the audit files themselves) into SUMMARY.md.
   Never `docs/`.
6. Report to the user in Vietnamese: counts per severity, what was fixed, and the list of decisions
   that were taken on their behalf (numbered, one line each: the choice and why) so they can overturn
   any of them. Do not ask questions; stop after the report. The next step is `/tu-dong`.

## Test scenarios
- Normal: four files arrive → 30 findings → 22 fixed (6 of them by a recorded decision), 8 rejected
  as duplicates/disproved → commit → Vietnamese report listing the 6 decisions.
- One auditor crashes → rerun once → still failing → consolidate the other three and say which lens
  is missing.
- A fixer is cut off (rate limit): its `*-FIXES.md` shows what is done; a fresh fixer continues from
  that file and from `harness_check.py` output instead of starting over.
