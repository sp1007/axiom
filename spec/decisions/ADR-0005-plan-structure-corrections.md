# ADR-0005 — Plan structure corrections (audit 2026-09-30)

## Tóm tắt
Các sửa đổi cấu trúc kế hoạch sau đợt thẩm định 4 góc nhìn (chủ dự án giao toàn quyền quyết định):
(1) test viết trước bản native được đánh dấu `native-after: <task>` và task bắt kịp native xoá dấu
đó — VS1 (T028/T029) chỉ còn `return 42` + số học đúng ladder 0263; (2) file dùng chung được tách để
không task nào phải sửa cùng một file: mã chẩn đoán theo vùng `diag/codes/<AREA>.def`, lệnh/emit của
driver theo file riêng, CMake tự glob test C; (3) gate chỉ có PASS hoặc BLOCKED — lỗi còn lại chỉ
được là XFAIL cho khoảng trống spec có ADR; (4) frontend cắt dọc: resolver/HIR chỉ chờ phần parser lõi
(T011), phần còn lại (T012 → T015b) chạy song song trước P5; (5) spec ownership (T045) phải xong trước
khi thiết kế MIR (T018); (6) truy vết: T017 chờ T111 để backlog đầy đủ trước khi vào lõi ngữ nghĩa;
(7) ngân sách thời gian self-compile ở T086, vượt ngân sách thì kéo một lát cắt regalloc (E15.8) vào
trước T087 (ngoại lệ R7 có điều kiện); (8) tách các task quá lớn; (11–13) chỉ task sửa board mới
"chạy một mình", các task spec P0 và khung repo chạy song song; module (T060) mở ngay sau gate P5;
(14) file dùng chung khai báo bằng `locks:`; (15) quy trình đóng băng axiom0 sau T087; (16) kiểm tra
chữ tiếng Việt trên console bằng máy. Không bỏ yêu cầu nào của chủ dự án.
Revisit: có — mục 6 và 7 (lịch trình), chủ dự án có thể xem lại.

Status: **Accepted** (architect; owner delegated all design decisions on 2026-09-30).
Date: 2026-09-30. Revisit: yes (§6 timing of traceability vs P3, §7 regalloc contingency).

## Context

The audit (`_workspaces/audit/2026-09-30/`, lenses A1–A4) found structural problems: native tests
required before native features exist (A2-01, A3-04, A3-05); shared files outside every task's
`paths` (A3-02, A4-13); gates that could pass with failures (A2-04, A3-15); the whole frontend built
before the first MIR (A2-02); MIR designed before the ownership spec (A2-03); traceability consolidated
after code tasks finished (A3-12, A4-10); no compile-time budget before self-host (A1-11, A2-09);
oversized tasks (A3-14, A3-11).

## Decision

1. **Interp-first tests, native catch-up by directive.** A run test written before its native
   support carries `// native-after: <task-id>`; the runner (T005) reports its native mode as SKIP
   with that reason. The named catch-up task (T033 CFG/calls, T037 traps/numerics/aggregates, T040
   enums/patterns/Option, T042 strings, T051 ownership/views/slices, T059 methods/generics/traits/
   closures, T061b pointers, T061d const tables, T070/T074/T074b host functions) lists those test dirs in its
   `paths`, removes every `native-after: <self>` and must leave `grep -rn "native-after: <self>"
   tests` empty. VS1 (T028/T029) covers exactly 0263 §51 VS#1: constants, arithmetic without traps,
   locals, return; the first ABI test moves to T033.
2. **No shared hot files.** Diagnostic codes live in one file per area
   (`bootstrap/axiom0/src/diag/codes/<AREA>.def`, pre-created by T009 from T002's area list; tasks
   list their area file in `locks:`). Driver commands and inspect emitters are one file each
   (`src/driver/cmd_<name>.c`, `src/driver/emit_<name>.c`) collected by a CMake-generated table
   (T004); the pipeline file `src/driver/pipeline.c` (T016) is a `locks:` entry of each task that
   changes it. CMake
   globs `tests/unit/**/*.c` and `tests/**/cdriver_*.c`, so no task edits CMakeLists.txt after T004.
   The runner gets a generic `exec` kind and all directives up front (T005), so later tasks never
   edit `tools/axtest.py`. CI scripts are pre-wired by T004 and edited only by gate tasks.
   Process-level isolation of parallel work trees is a harness matter (not this ADR).
3. **Gate rule: PASS or BLOCKED** (0264 §20). A gate passes only if every failing test is an XFAIL
   (`// xfail: <task-id>`) naming an existing task for a **spec gap with an ADR**; implementation
   bugs are fixed before the gate closes; XPASS is a failure. Fuzz campaigns are defined by seed and
   iteration count, not wall time. Every core gate also runs `reqcov.py --strict`,
   `harness_check.py` and (from T022) `tools/gatecheck.py`. Phase gates use `gate_model: opus`.
4. **Vertical frontend slice.** T011 parses simple types and basic patterns; the resolver (T014)
   depends on T011 only; T015 lowers what T011 parses; the rest of the grammar (T012) is resolved and
   lowered to HIR by new task T015b, which the VS0 gate (T022) and P5 (T030) wait for — the semantic
   core T017–T021 does not. The AST/HIR data models still reserve every
   variant (0263 §42 "implement later ≠ design later").
5. **Ownership spec before MIR.** T018 depends on T045; T045 runs early (priority 10) in parallel
   with P1/P2 (0263 §42, ABOOT-43..45).
6. **Traceability before the semantic core.** T017 depends on T111, so the complete requirement
   backlog exists before P3 starts; P1/P2 (kernel, lexer, parser, resolver, HIR, driver) run in
   parallel with extraction. T111 may add `covers:` to tasks already done (metadata only).
   ROADMAP table: P1/P2 run alongside P0 traceability; P3 depends on the P0 gate T111.
7. **Compile-time budget with a regalloc contingency.** T075 adds a generated ~100k-line program
   (axiom0 compiles it in < 30 s, < 2 GB). T086 measures axiom0→axiomc1 and the axiomc1 self-compile
   against the SPEC-20 budget (default < 10 min, < 4 GB). If the budget is exceeded, the architect
   pulls a minimal linear-scan slice of E15.8 (T063 scope, written in C inside axiom0) in before T087
   as a new P10 task — an explicit, conditional exception to R7 recorded here and in ROADMAP R7.
8. **Task splits** (one sitting each): T015b, T025b, T038b, T048b, T054b, T061b, T061c, T061d, T071b,
   T071c, T074b. T076 must split each port task T077–T085 per C module (≤ ~1.5k lines of Axiom), name
   the exact differential artefact and harness entry of each, use Opus for typeck/traits/ownership/
   verifier/MIR-builder/interpreter ports, and re-path post-self-host tasks to the chosen
   `compiler/<module>` layout.
9. **Follow-up ids.** Tasks created outside planning tasks (unblock splits, gap tasks, fixes) take a
   letter suffix of the task they derive from (`T048c`) or, for P0–P10, the next free id in
   `T112–T199`; P11+ follow-ups use their phase block. Never reuse the reserved stale ids of the old
   FFI split.
10. **P24 frame.** P24 gets named epics E24.1–E24.8 (the domains ROADMAP already lists) and a deferred
    gate T324; T224 stays deferred until the owner schedules it.
11. **"Critical, runs alone" is for board-editing tasks only** (T110, T111, T2NN: they rewrite task
    files). The P0 spec tasks T001–T003a and the skeleton T004 write disjoint files, so they get
    priority ≥ 10 and are ordered by `depends` alone: T004–T008 (skeleton, runner, archcheck, kernel,
    source DB) run in parallel with the spec tasks instead of waiting for four sequential Opus tasks.
    Options considered: keep all five critical (simple, but ~4 Opus sittings of dead time); make only
    T001 critical (still serialises T004). Chosen: none of them critical.
12. **Spec dependencies of P1/P2.** T010 (first language task) depends on T003a (subset + stage-0
    "unsupported" diagnostics). T004–T009 need only the engineering conventions (axiom-c-stage0) and
    T002 (T009), so they do not wait for SPEC-00/SPEC-04.
13. **Modules open after the P5 gate.** T060 (modules, packages, visibility, std root, prelude
    mechanism) depends on T044 instead of T052 and runs in parallel with P6: it needs no ownership
    feature, its directories (`resolve`, `source`, `hir`, driver) are disjoint from the P6 analyses, and
    the std chain (T065 → T070 → …) no longer queues behind the whole P7 semantic chain (ROADMAP R8).
    Manifest and std-root rules are fixed in ADR-0006, so T060 stays a Sonnet task.
14. **Shared files use `locks:`.** A file several tasks must touch (a diagnostic area file
    `diag/codes/<AREA>.def`, `src/driver/pipeline.c`) is listed in the task's `locks:` front-matter;
    the scheduler treats it like a path. Files only one task creates (an emitter
    `src/driver/emit_<name>.c`) go in `paths`.
15. **After the fixed point.** T087 tags `axiom0-frozen` (harness_check then rejects any later commit
    under `bootstrap/axiom0` whose subject lacks an `AX0-FIX` task id), delivers
    `tools/build_axiomc.py` (per-task build directory of the stage-2 compiler) and makes the runner
    default to axiomc. Agent files state the rule; the orchestrator prompts are a harness matter.
16. **Console glyph check is automated.** The pipe/file byte-exact tests are the gate; in addition a
    Python `ctypes` helper allocates a console, runs the program and reads the screen buffer
    (`ReadConsoleOutputCharacterW`). It reports SKIP only when no console can be allocated.
17. **Long tasks.** Large Opus tasks (T001, T003a, T017, T045, T055, T076) carry `timeout_min: 300`.

## Consequences

Board edits across P0–P10 (dependencies, paths, acceptance), new tasks listed in §8 and T324, ROADMAP
§1 (R7 contingency, R-order), §2 table, §3 P24, §4 (follow-up ids, cross-phase dependencies,
harness_check), change log. Owner requirements (OWNER.md) are unchanged: nothing is dropped; the
console-glyph requirement for `Xin chào thế giới` becomes a machine-checkable test (T042) instead of
a manual one.

## Sources
0263 §20 §42 §45 §51; tasks/0262 §1 §6 §42 §50 §55; 0264 §18-20; 0172 §32; ROADMAP R1 R5 R7; audit
A1-11, A2-01..A2-10, A3-01..A3-27, A4-10, A4-17, A4-18, A4-19.
