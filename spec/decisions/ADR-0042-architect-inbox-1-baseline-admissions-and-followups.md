# ADR-0042 — Architect inbox 1: baseline admissions, compiler-bug follow-ups, saturating fix before T453, AX_CONST_SHIFT_RANGE

Status: accepted (2026-11-13, architect; owner-delegated decision)

## Tóm tắt
- Xử lý hộp thư architect do các gate T421, T422, T430, T437a, T452 để lại. 18 id lỗi có sẵn (đã chứng minh lỗi y hệt
  ở HEAD) được thêm vào `_workspaces/baseline-failures.txt`, mỗi id có task sửa: d10–d12 → T435 (cùng triệu chứng exit
  300); 2 id so sánh MIR ngoài `selfhost/drop` → T441; 2 id `obj_link_driver` panic → T442; 8 oracle Python p18/p19/p20
  + `lsp_vfs` (có thể do quá tải máy, mã 143) → T440 với chính sách timeout khi máy tải nặng; `encode/encode.test`,
  `link/link.test` (snapshot không build được test C vì clang `-Werror`) → T438; self-test `gatecheck` → T439.
- Lỗi compiler phát hiện khi làm std/async (T421 FU-1..6, T422 FU-A..K) được gom theo nguyên nhân gốc thành 9 task P11
  (T444–T449, T422a, T422b) và 1 task std/async (T421a); API đúng hình SPEC-34 (`TaskGroup<T>`, `Timeout<F>`,
  `spawn(fut)`) là T422c sau khi các lỗi generic được sửa. Bắt panic thật trong task cần unwinding → T536 (P13, sau T523).
- `saturating_add/sub/mul` native sai trên u8..i64 → T481 (P12) phải xong **trước** T453; T453 phụ thuộc T481 và T452.
- `neg_carry` miscompile ở O1 → điều tra T482. Bit intrinsic chưa được gấp hằng ở -O1 → T484.
- Mâu thuẫn spec: SPEC-03 nói dịch bit ngoài phạm vi lúc biên dịch là `AX_CONST_OVERFLOW`, SPEC-40/SPEC-42 nói
  `AX_CONST_SHIFT_RANGE`. Chọn `AX_CONST_SHIFT_RANGE` (spec sau, cụ thể hơn); sửa SPEC-03; T483 đăng ký mã và sửa luôn
  literal `-9223372036854775808i64` bị panic.
- Quy tắc test: test đọc file ngoài thư mục của mình phải khai `nocache:`/`cache-inputs:` (G1); chạy đủ định kỳ dùng
  `--no-cache`; G2 (prelude ngầm định trong quét never-cache) giao cho T437b.
- Mọi task sửa baseline có priority 18–20, task lỗi compiler 21–30, đều thấp hơn task tính năng (≥ 100) và ≥ 10.
- Revisit: có — §1 lớp `maybe-timeout` (nếu T440 chứng minh chỉ là timeout thì đổi lớp `environment` hoặc xoá dòng).

## Context
- `_workspaces/architect-inbox.txt` (7 items) and `_workspaces/baseline-candidates.txt` (16 ids) accumulated by the
  gates of T421, T422, T430, T437a and T452 on 2026-11-13. Every candidate was re-run by its gate (or the T452
  implementer) on a HEAD copy and failed identically (ADR-0041 §3 admission rule).
- Sources: `_workspaces/reports/T421-report.md` (FU-1..FU-6), `T422-report.md` (FU-A..FU-K), `T422-qa.md` §7,
  `T430-qa.md` (snapshot cmake failure), `T437a-report.md` ("Harness follow-up"), `T437a-qa.md` (G1..G3, R1, R2),
  `T452-report.md` (FU-T452-NEG, WEAK-NATIVE generators, 17 pre-existing bundles), `T452-qa.md` (FINDING-2, FINDING-3,
  spec gap, i64 MIN literal).
- Spec conflict: `spec/SPEC-03-core-semantics.md` AXS-SEM-037 lists "shift out of range" under `AX_CONST_OVERFLOW`;
  `spec/SPEC-40-integers.md` (line 81, table line 491, AXS-INT-005) and `spec/SPEC-42-simd.md` (line 100) name a
  separate `AX_CONST_SHIFT_RANGE`. The compiler registers neither the name nor a code for it
  (`compiler/diag/code.ax`).

## Options and decisions

### §1 Baseline admissions (18 ids)
Options: (a) admit each id under an existing fix task where the symptom matches, else a new task per root cause
(chosen); (b) one catch-all task (rejected: crosses owners, violates one sitting); (c) leave them out and let gates
go BLOCKED (rejected: blocks every gate on unrelated failures).
| ids | class | task |
|---|---|---|
| `selfhost/drop/qa_drop_d10..d12` | fixture-regen:drop-fixtures | T435 (already in its scope "d10..d12 included") |
| `selfhost/interp_opt/qa_interp_opt_diff_mir_b`, `selfhost/own_mir_verify/qa_own_mir_diff_drop_b` | undiagnosed:mir-fixture | T441 (after T435, reuses its prelude-independent comparison if the cause is the same) |
| `selfhost/obj_link_driver/qa_obj_link_driver_{diff,smoke}` | undiagnosed:obj-link-driver | T442 |
| 7 `conformance/p18|p19|p20/*_oracle.test`, `run/lsp_vfs/lsp_vfs_engine.test` | undiagnosed:maybe-timeout | T440 |
| `encode/encode.test`, `link/link.test` | environment:snapshot-cbuild | T438 |
| `tools/tests/gatecheck::test_gatecheck.GatecheckTest.test_check_without_command_blocks` | undiagnosed:gatecheck-selftest | T439 |
`encode/encode.test` and `link/link.test` were not on the candidate list but fail in every fresh snapshot for the
same reason (T430-qa: `cannot execute build/tests/ct_*`, the snapshot cmake build stops on
`tests/mc/isel/cdriver_abi_qa2.c:19 unused variable 'sig'` with clang `-Werror`); they are admitted with T438.
**maybe-timeout policy** (T440, also added to axiom-qa.md): a test killed on timeout is re-run once alone with
`--timeout-scale 6`; only a failure that reproduces then is a real failure. T440 decides per id: real bug (fix or
split), load-only (make the oracle's internal subprocess timeout honour `--timeout-scale`/an env factor, remove the
line), never a blanket timeout increase that hides a hang.

### §2 Compiler-bug follow-ups grouped by root cause (P11)
| task | owner | items | root cause |
|---|---|---|---|
| T444 | axiom-semantics | FU-1, FU-3 | struct layout: forward-referenced pointee; lang-item struct fields inside `std.*` modules |
| T445 | axiom-semantics | FU-4, FU-6 | move/drop elaboration through `mut_view` fields and receivers |
| T446 | axiom-semantics | FU-F, FU-G | impl-level generics are not monomorphised (layout, `size_of`, `needs_drop`, trait dispatch, native instantiation) |
| T447 | axiom-semantics | FU-B, FU-C | impl generics in associated types; overlap check ignores concrete type arguments |
| T448 | axiom-semantics | FU-D, FU-H, FU-5 | explicit type arguments ignored; inference from bounds / inside `poll` (after T446) |
| T449 | axiom-semantics | FU-E | concurrency checker keyed on the callee spelling `spawn` |
| T422a | axiom-frontend | FU-A, FU-J | parser: `a.f < b.g` read as generic args; generic fn `g<F>` as a value |
| T422b | axiom-semantics | FU-2, FU-K | native call through a fn-pointer field expression; oracle drops buffered stdout on step-limit |
| T421a | axiom-stdlib | FU-I + inbox | `std/async`: join-waker race, `task_wake` livelock, `tcb_poll_fn` flag clobber, `Waker` wake/clone/drop ignoring the vtable, detached task outputs not dropped |
| T422c | axiom-stdlib | T421/T422 API deviations | converge `std/async` on the SPEC-34 shape once T446–T449, T422a, T421a are done |
All compiler tasks lock `tests/selfhost` (bundle regeneration) and therefore depend on T452 (holder of that lock).
The P11 gate T311 depends on all of them: the E11.5 API is not delivered as specified until T422c.
**Panic containment** needs real unwinding (no catch mechanism exists in `std/`). Options: (a) keep cooperative
`task_panic` forever (rejected: SPEC-34/REQ-ASY-019 want a panicking task captured); (b) implement a task-local catch in
P11 (rejected: duplicates E13.5); (c) **T536 in P13 after T523** (native landing pads) installs `catch_unwind` in
`group_poll_fn`/`tcb_poll_fn` (chosen). Until then the cooperative mechanism stays documented.

### §3 Native saturating arithmetic before T453 (P12)
`saturating_add/sub/mul` are wrong natively for every width u8..i64 (`compiler/lir/builder.ax` maps
`MIR_BINOP_SAT_*` to nothing; only `WRAPPING_*` are mapped), silently, since before T452. Options: (a) leave it in T453's
128-bit scope (rejected: T453 is large and the bug is live for every narrow width today); (b) **T481 fixes
narrow widths now, T453 depends on T481 and on T452 (chosen)**. T453 keeps the 128-bit saturating lowering and must
remove `native-after: T453` from `tests/run/int128_interp/*` (now in its `locks:`), and its acceptance adds
narrow-width native saturating checks staying green.

### §4 `AX_CONST_SHIFT_RANGE` and related constant-evaluation gaps (P12)
Options: (a) amend SPEC-40/42 to `AX_CONST_OVERFLOW` (rejected: loses the distinct, more useful diagnostic, two specs
would change); (b) **register `AX_CONST_SHIFT_RANGE` and amend SPEC-03 AXS-SEM-037 (chosen; later + more specific
specs win)**. The numeric column of SPEC-40's table (`3104`) is a catalogue number; the compiler assigns its next free
id in `compiler/diag/code.ax` and maps the name. T483 implements it and also fixes the literal
`-9223372036854775808i64` (AXS-INT-004: the range check is applied after folding unary `-`; today it panics
`arithmetic overflow` at run time). Bit-intrinsic folding at -O1 (T452 FINDING-2, a T452 scope bullet not delivered)
becomes T484. The O1 `neg_carry` miscompile of the stage-2 compiler (FU-T452-NEG) becomes the investigation T482 with
the recipe from T452-qa/T452-report.

### §5 Test-cache hygiene (T437a G1–G3, R1, R2)
- G1: a test that reads files outside its own directory declares `nocache:` or `cache-inputs:` (axiom-testing SKILL).
- R1: the periodic full run uses `--no-cache` (axiom-qa.md).
- G2: the never-cache scan must start from the implicitly loaded prelude files too; added to T437b's scope (exact
  dependency list includes the prelude; superset mode seeds the traversal with `std/core/{prelude,option,result,host}.ax`).
- G3 (addendum to ADR-0041 §4 S4): tests whose output depends on ASLR or timing are outside the cache's soundness
  conditions; they are made deterministic or `nocache:`, never baselined.
- R2: the failing gatecheck self-test is baselined with fix task T439.
- `tests/selfhost/bundle_common.py` rejects duplicate module names (T443, after T452).

### §6 Ordering
Priorities: baseline fix tasks 18–20 (T438, T439, T441, T442 18; T440 19; T443, T481 20); compiler-bug follow-ups
21–30 (T444, T446 21; T445 22; T447, T448 23; T449, T422a, T422b 24; T421a 25; T482 26; T483 27; T422c 30); T484 145 and
T536 174 (feature priorities of their phases). All are ≥ 10 (none architecture-critical) and below every feature task of P11+ (≥ 100),
so `taskctl next` picks them first when their dependencies and locks allow.

## Consequences
- Baseline grows from 72 ids (87 of ADR-0041 minus the 15 removed by T430) to 90 ids, all with a task on the board; recorded in the ROADMAP change log.
- New tasks: T438–T449, T421a, T422a, T422b, T422c (P11); T481–T484 (P12); T536 (P13). T311, T312, T313 depend on
  their phase's new tasks. T453 depends on T452 and T481. T437b gains G2. T435 notes d10–d12 in acceptance.
- `spec/SPEC-03-core-semantics.md` AXS-SEM-037 amended (shift out of range → `AX_CONST_SHIFT_RANGE`).
- `.claude/agents/axiom-qa.md` and `.claude/skills/axiom-testing/SKILL.md` carry the T437a harness follow-up text, G1,
  the `--no-cache` full run and the loaded-machine timeout rule.
- Revisit: yes — §1 `maybe-timeout` class after T440; §2 T536 placement if E13.5 slips past P13.

## Sources
- `_workspaces/architect-inbox.txt`, `_workspaces/baseline-candidates.txt` (2026-11-13, both now processed).
- Reports named in Context; ADR-0041 (§1–§4, §6); ADR-0005 (R9, native-after); SPEC-03 AXS-SEM-037; SPEC-40
  AXS-INT-004/005; SPEC-42; SPEC-34 (structured concurrency API).
