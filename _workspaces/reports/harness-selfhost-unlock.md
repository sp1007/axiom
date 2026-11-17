# Harness change: generated selfhost bundles belong to the harness (2026-11-17)

## Tóm tắt
- Chủ dự án duyệt (2026-11-17): bỏ việc mọi task compiler phải xếp hàng vì khoá `tests/selfhost`, không giảm chất lượng kiểm thử.
- 154 file bundle do `tests/selfhost/**/gen_*.py` sinh ra (danh sách `tests/selfhost/generated-files.txt`) từ nay thuộc về harness. Agent không sinh lại, không sửa, không liệt kê, không commit bundle.
- `taskctl snapshot <ID>` tự chạy mọi generator bên trong snapshot (đo được ~70 giây ở `-j 3`, máy đang tải nặng), nên gate test đúng các bundle sẽ được commit. Snapshot ghi lại commit gốc và mã blob của từng bundle vào `_workspaces/locks/snap-<ID>.json`.
- `taskctl accept <ID>` làm mới snapshot lên HEAD hiện tại + change set, sinh lại bundle, chạy `--check` cho cả 36 generator (~65 giây), chép bundle thay đổi vào cây chính và stage vào đúng một commit của task.
- Chốt an toàn khi HEAD đã đổi sau gate: một bundle sắp commit mà khác cả bản gate đã test lẫn bản ở HEAD thì là tổ hợp chưa từng được test. Khi đó accept trả **mã 5 (REGATE)**, task vẫn ở `doing`, và orchestrator chạy lại gate ("rebase gate") trong snapshot đã rebase. Không có đường vòng.
- Bundle cũ/dở dang trong cây chính (do task khác để lại) bị bỏ qua: không bị REFUSED, không bao giờ stage từ cây chính. Nếu file đó nằm trong paths của một task đang chạy thì accept chỉ stage vào index và để nguyên file của task kia.
- Đã gỡ khoá `tests/selfhost` khỏi 40 task todo; harness_check cấm khoá cả cây này. Các khoá file thật vẫn giữ nguyên.
- Thực tế: sau khi gỡ, hàng đợi gần nhất bị giới hạn bởi 3 file nóng `typeck.ax`, `mir/builder.ax`, `lir/builder.ax`, nên sau T444 chạy được T485 + T481a song song (chưa phải 3).
- Selftest 150/150 (thêm 17 phép thử mới, sửa 2 phép thử đã lỗi sẵn ở HEAD); validate, harness_check, reqcov --strict đều đạt.

## Decision (TYPE B harness/process; owner-approved goal, details decided here)

### Options considered
1. **Regenerate in the main tree at accept** (the brief's literal step 3). Rejected: the main tree holds
   other running tasks' uncommitted `compiler/` edits. At the time of writing, T444's uncommitted
   `compiler/types/typeck.ax` makes 11 of 36 generators report DIFFERS in the main tree. A main-tree
   regeneration would bake another task's half-finished code into this task's commit.
2. **Regenerate in a clean tree = the task snapshot refreshed onto the current HEAD + the change set**
   (chosen). This is the same tree the gate used, rebased. `--check` runs there too, which is the
   equivalent of the requested main-tree check. The regenerated bundles are then copied into the main
   tree and staged.
3. Commit bundles without regeneration at accept, trusting the snapshot's copy. Rejected: if HEAD
   moved, the snapshot's bundles would silently drop the other task's module changes.

### HEAD-moved safeguard (chosen)
The snapshot records `{base, blobs}` (git blob id of every generated file) after its regeneration. At
accept, `changed` is the set of bundles whose regenerated blob differs from HEAD's, and `untested` is
the subset of `changed` whose blob differs from the recorded one.
- `untested` empty → commit. This covers HEAD moved with no shared bundle, as well as HEAD unchanged.
- `untested` non-empty → exit 5 REGATE. Two causes: HEAD moved and the two change sets meet in a
  bundle, or the task's sources changed after the gate.

Re-gating costs one taskgate run (~60–90 min). That is proportionate: it reproduces exactly what the
old serial lock guaranteed (the gate saw base + both changes), but only when a combination is actually
untested. Implementation still runs in parallel. "Compile only" was rejected as weaker than the
previous guarantee.

**Revisit:** nearly every bundle closure contains the hot modules (kernel, diag, types), so two
compiler tasks accepted back to back will usually trigger a REGATE for the second. If REGATE turns out
to be frequent, a narrower rebase gate (only the untested bundles' tests + own tests) is the next
optimisation.

### Legacy and transition (T444)
- No record (snapshot made by the old taskctl): the gate is assumed to have tested HEAD's bundles plus
  the listed ones. A listed bundle that equals the regenerated one is accepted; otherwise REGATE. A WARN
  is printed.
- T444 lists bundles or not: either way accept regenerates them and overwrites them. A listed
  generated file is still copied into the snapshot as an *input*, because
  `gen_obj_link_driver/gen_driver/gen_backend` extract axiom0-captured golden blobs from the bundle on
  disk. This keeps a deliberate `--refresh-goldens` working.
- T444's task file and paths were not touched. Its gate snapshot will be refreshed by the new
  taskctl (record written). harness_check shows only a WARN for its legacy lock while it is in doing.

### Regeneration facts (measured 2026-11-17, machine loaded by T444)
| run | generators | files | time |
|---|---|---|---|
| sequential write (shell loop) | 36 | 153 + manifest | 198 s |
| `bundles.py regen -j 3` | 36 | 154 | 68 s |
| `bundles.py check -j 3` | 36 | — | 64 s |

- Write mode is deterministic: a clean worktree of HEAD stays clean after regeneration.
- Plain write mode never runs a compiler: goldens are re-captured only with `--refresh-goldens`/`--axiom0`.
- Generators of one directory run in sequence, because `gen_kernel_tests` and `gen_hash_native` write
  the same files, and `gen_link_tests` imports `gen_local_symbols_test`. Directories run in parallel.
- One generated file lies outside `tests/selfhost`: `tests/std/core/qa_hash_vectors.ax`. It is in the
  manifest and handled the same way.
- "Only generators whose module lists include a changed module" was not implemented. `bundle_common`
  cannot answer it without assembling, which is the costly part. All 36 generators run (~70 s).
- A change set of only `spec/`, `_workspaces/`, `.claude/` or `*.md` skips regeneration at accept.

## Board
- `tests/selfhost` (whole tree) removed from `locks:` of 40 todo tasks. Every one held it only for bundle
  regeneration; no task body edits `bundle_common.py` or a generator.
- The 31 body lines "regenerate selfhost bundles…" were rewritten to the new rule. Area paths such as
  `tests/selfhost/typeck` (hand-written tests) were kept, and all real file locks were kept.
- Compatible task pairs among the 40 relocked tasks: 0 → 392 of 780. Over all 291 todo tasks:
  37,746 → 39,469 of 42,195.
- `taskctl next --max 3` now: nothing (T444 holds typeck/resolve/lir-builder locks). Simulated once T444
  finishes (scratch copy of the board):
  - wave 1: **T485 + T481a**
  - wave 2: T486 + T447
  - wave 3: T446
  - wave 4: T445 + T453

  The near-term queue is now limited by real file locks on `compiler/types/typeck.ax`,
  `compiler/mir/builder.ax` and `compiler/lir/builder.ax`, which almost every queued fix task locks,
  not by `tests/selfhost`. T485/T486 were created without the selfhost lock, so the old board would
  have paired T485 + T481a as well. The gain shows up from wave 4 onwards (T453) and across the P12–P14
  tail.
- validate OK (697 tasks), harness_check OK, `reqcov.py --strict` COVERAGE OK.

## Coordinator additions
1. ROADMAP change-log row for T485/T486 (E15.7 compile-time work pulled forward to P12 at priority 15,
   byte-identical output as the quality guard) was added alongside this change's row. The two task
   files were not edited.
2. **Bundle merge: proposed as a task (not created on the board).** Not implemented here, for three
   reasons:
   - Merging needs each bundle's `main` and clashing test-function names renamed, and it changes test
     ids (`_workspaces/baseline-failures.txt`, `tools/affected_map.txt`, smoke list). That is a
     generator/test-layout change, not a harness change.
   - A fair measurement needs at least two 5–19 min, ~3.5 GB axiomc2 compiles. The machine is
     currently saturated by T444, so the timing would be unreliable.
   - Size evidence: `qa_lir_from_ax_a.ax` is 2,910,602 bytes, of which its template is 39,730 bytes
     (1.4%). A 5-way merge therefore compiles about 1.06× one bundle instead of 5×. Even with
     superlinear passes the merge should be a clear win, but this is unmeasured.

   Proposed task:
   - **Title:** Merge selfhost bundles with identical module closures.
   - **Owner:** axiom-qa (test infrastructure). **Model:** sonnet; gate_model: opus.
   - **Paths:** `tests/selfhost/bundle_common.py`, the affected `tests/selfhost/<area>/gen_*.py`,
     `*.ax.in` and `*.test` files, `tools/affected_map.txt`, `tests/smoke.list`,
     `_workspaces/baseline-failures.txt`.
   - **Depends:** none for step 1.
   - **Acceptance:**
     1. Measure first, using the snapshot's axiomc2 with `--time-passes`: lir a..e separately vs merged.
        If merged > 0.6 × the sum of the separate compiles, mark the task BLOCKED on T485 + T486.
     2. A `bundle_common` "merge group" spec that concatenates several templates' bodies under one
        prelude and module closure, with each original `main` renamed and called in order, each still
        printing its own OK/FAIL line with the original bundle name, and continuing after a failure.
     3. Every original assertion kept. Mutation proof: break one case per merged group and see exactly
        that line FAIL natively.
     4. Remap baseline ids and the affected map; record the selfhost wall time before and after.

## Manifest note
`tests/selfhost/generated-files.txt` exists in the main tree (uncommitted, identical to a regeneration
of HEAD) but is deliberately not listed below. It lies under T444's legacy `tests/selfhost` lock, so
`commit-report` would refuse it, and it is itself a generated file: the next accept that touches bundle
inputs (T444's) regenerates it and stages it in that task's commit. Until then harness_check and
`taskctl` read the working copy.

## Files changed
- .claude/skills/axiom-tasks/scripts/bundles.py
- .claude/skills/axiom-tasks/scripts/taskctl.py
- .claude/skills/axiom-tasks/scripts/selftest.py
- .claude/skills/axiom-tasks/scripts/harness_check.py
- .claude/skills/axiom-tasks/SKILL.md
- .claude/skills/axiom-compiler/SKILL.md
- .claude/skills/axiom-testing/SKILL.md
- .claude/skills/axiom-tick/SKILL.md
- .claude/agents/axiom-qa.md
- spec/ROADMAP.md
- CLAUDE.md
- _workspaces/tasks/todo/T058-dyn-trait-vtables-and-dynamic-dispatch.md
- _workspaces/tasks/todo/T422a-fix-parser-generic-args-ambiguity-and-generic-fn-values.md
- _workspaces/tasks/todo/T422b-fix-native-fn-pointer-field-call-and-oracle-stdout-flush.md
- _workspaces/tasks/todo/T423-e11-5-stackful-fiber-runtime-context-switch.md
- _workspaces/tasks/todo/T426-e11-6-windows-iocp-reactor-timer-wheel-oracle.md
- _workspaces/tasks/todo/T445-fix-moves-through-mut-view-fields-and-receivers.md
- _workspaces/tasks/todo/T446-fix-impl-level-generics-monomorphisation.md
- _workspaces/tasks/todo/T447-fix-impl-generics-assoc-types-and-overlap-check.md
- _workspaces/tasks/todo/T448-fix-explicit-type-args-and-bound-inference.md
- _workspaces/tasks/todo/T449-fix-concurrency-checker-keyed-on-spawn-name.md
- _workspaces/tasks/todo/T453-e12-1-lir-i128-pair-lowering-x64-codegen.md
- _workspaces/tasks/todo/T454-e12-1-std-num-complete-integer-api-conversions.md
- _workspaces/tasks/todo/T457-e12-2-typeck-mir-float-and-req-owner-007-matrix.md
- _workspaces/tasks/todo/T458-e12-2-oracle-ieee754-float-eval-strict-opt.md
- _workspaces/tasks/todo/T459-e12-2-lir-xmm-win64-abi-sse2-scalar-codegen.md
- _workspaces/tasks/todo/T460-e12-2-std-float-methods-formatting-parsing.md
- _workspaces/tasks/todo/T461-e12-2-std-math-elementary-transcendental-library.md
- _workspaces/tasks/todo/T464-e12-3-typeck-mir-vector-mask-lowering-verifier.md
- _workspaces/tasks/todo/T465-e12-3-oracle-mir-interp-const-eval-simd.md
- _workspaces/tasks/todo/T466-e12-3-std-simd-portable-vector-mask-api.md
- _workspaces/tasks/todo/T467-e12-3-std-simd-tensor-matrix-views-soa.md
- _workspaces/tasks/todo/T470-e12-4-lir-vector-types-legalizer-win64-abi.md
- _workspaces/tasks/todo/T471-e12-4-x64-0f38-0f3a-vex-machine-encoder.md
- _workspaces/tasks/todo/T472-e12-4-x64-sse2-baseline-vector-isel-codegen.md
- _workspaces/tasks/todo/T473-e12-4-x64-sse41-avx2-fma-isel-std-arch.md
- _workspaces/tasks/todo/T476-e12-5-target-feature-attribute-call-verifier.md
- _workspaces/tasks/todo/T477-e12-5-std-arch-cpuid-xgetbv-runtime-detect.md
- _workspaces/tasks/todo/T478-e12-5-multiversion-clone-lowering-dispatcher-codegen.md
- _workspaces/tasks/todo/T481a-harden-saturating-lowering-and-backend-ice.md
- _workspaces/tasks/todo/T482-investigate-o1-neg-carry-miscompile-stage2.md
- _workspaces/tasks/todo/T483-const-shift-range-diag-and-min-literal-folding.md
- _workspaces/tasks/todo/T484-o1-const-folding-of-bit-intrinsics.md
- _workspaces/tasks/todo/T501-e13-1-typeck-mir-unsafe-provenance-req-owner-008.md
- _workspaces/tasks/todo/T507-e13-2-unions-packed-align-address-space-sema.md
- _workspaces/tasks/todo/T512-e13-3-profile-checking-entry-naked-capability-graph.md
- _workspaces/tasks/todo/T517-e13-4-safety-profile-forbid-unsafe-sandbox-sema.md
- _workspaces/tasks/todo/T522-e13-5-panic-mode-no-panic-catch-unwind-mir-oracle.md
- _workspaces/tasks/todo/T551-e14-1-comptime-fn-blocks-const-generics-sema.md
- _workspaces/tasks/todo/T562-e14-3-generator-syntax-hir-live-across-yield-own.md
- _workspaces/tasks/todo/T571-e14-5-typeck-mir-index-autoderef-view-mut-view.md

HARNESS COMPLETE
