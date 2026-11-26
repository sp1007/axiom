# Triage 2026-11-26 — the two failures after T502 (and T428j's other findings)

## Tóm tắt
- Hai test hỏng sau T502 (`run/opt_lto/opt_lto_engine.test`, `selfhost/opt/qa_opt_pipeline.ax`) là **lỗi thật đã có sẵn**,
  không phải báo động giả. Bộ dò UB-04 mới của T502 làm đúng, giữ nguyên.
- Lỗi 1 nằm ở `compiler/opt/{inline,escape,ipa,sroa}`: 26 chỗ nạp nguyên một `MirStmt` từ bộ nhớ arena vừa cấp phát mà
  chưa ghi gì. Lỗi 2 nằm ở harness test `harness_opt_pipeline.ax.in`: harness gắn bảng băm interner lấy từ arena nhưng
  không xoá về 0. Bản native chạy được chỉ vì HeapAlloc của Windows trả về bộ nhớ đã xoá 0. Ngôn ngữ không bảo đảm
  điều đó.
- Đã kiểm chứng: lấy mã nguồn đúng HEAD, sửa trên bản chép rồi chạy lại. Cả hai test đều qua.
- Tạo task T543 (priority 0, axiom-semantics) để sửa tận gốc. Hai id được đưa vào `baseline-failures.txt`, gắn với T543.
- Lỗi phụ phát hiện thêm: `compiler/kernel/interner.ax` có biểu thức kích thước bị hỏng (`old_(mcap << 3)`…). Chúng chỉ
  biên dịch được nhờ shim trong `bundle_common.py`, và shim này nằm luôn trong axiomc thật. Hậu quả: bảng chuỗi tràn
  heap khi intern quá 65.536 chuỗi. Tạo task T544 (priority 15).
- Phát hiện của T428j: (1) không dựng được biến thể enum dạng struct. Đã tái hiện, tạo T428n. (2) toán hạng bị đọc
  muộn. Đây là vi phạm AXS-SEM-040 thật và rộng hơn mô tả: `add(z, { z = 9; 1 })` cho 10, `w + { w = 9; 1 }` cho 10,
  sai như nhau ở interp, native và O1. Tạo T428o (priority 25).

## 1. The two failing ids: real latent uninitialised reads (not detector false positives)

Setup: compiler `build-head-T428j/build/axiomc2.exe` (built from untouched HEAD e085e8e6 by the T428j engineer). Sources
come from `git archive HEAD` (e085e8e6) into a scratch directory, so the uncommitted T428j/T428m edits play no part.

### 1a. `run/opt_lto/opt_lto_engine.test`
- I assembled the oracle's part-A probe with `opt_lto_oracle.assemble_opt_lto_probe` from the HEAD sources and ran it
  with `run --interp`. Result: exit 125, after `PROBE_LTO_SUMMARY_AND_ALIAS_BARRIERS=OK`:
  `AX_UNSAFE_INTERP_UB: read of uninitialized memory` at module `compiler.opt.inline`
  (`compiler/opt/inline/mod.ax:2607`):
  `let mut ast = unsafe { *(arena_alloc_raw(mut_view(*arena), size_of<MirStmt>(), align_of<MirStmt>()) as *mut MirStmt) };`
  This is a typed load of a whole struct from arena bytes that were never written. That is UB-04 (SPEC-50 AXS-UNS-014,
  UB table), and the detector is right. T428j's report put this failure at `interner_intern_bytes` too. My repro shows
  the probe's site is in `compiler/opt/inline`. Only the selfhost bundle stops in the interner (1b).
- The pattern occurs at 26 sites: `escape` 9 (one is `MemOptStats`), `inline` 5, `ipa` 3, `sroa` 9.
- Experiment: I changed all 26 sites in the bundle copy to read from a zero-filled allocation. Result: exit 0 and all
  nine `PROBE_LTO_*=OK` lines, ending with `PROBE_LTO_ALL=PASS`.

### 1b. `selfhost/opt/qa_opt_pipeline.ax [interp]`
- The committed bundle run with `run --interp` gives exit 125 at `qa_opt_pipeline.ax:1106`
  (`let id_v = unsafe { *(mids0 + slot) };` in `interner_intern_bytes`).
- Cause: the interner is correct. `interner_grow_map` zero-fills every slot it allocates. The harness
  (`tests/selfhost/opt/harness_opt_pipeline.ax.in` ~383–394) replaces the session interner's map with
  `arena_alloc_raw(perm_arena, smap_cap * 4, 4)` and never zeroes it. The probe loop relies on `0u32` meaning "empty".
- Experiment: I added a loop that zeroes the 1024 `smap_ids` slots in a copy of the bundle. Result: exit 0,
  `OK opt pipeline`.
- Six other probe templates copy the same block: e15_3, e15_4, opt2 sroa_inline, opt_bce, opt_ipa_devirt and
  static_items opt_static_summary_alias. They are included in T543.

### Decision
This is a real bug at the source of each read, so the detector stays as it is (T502 acceptance, `unblock-T502.md`).
The fix task is **T543** (priority 0, axiom-semantics, sonnet). Its scope:
- replace the 26 typed loads;
- zero the 7 harness maps;
- add a guard test that rejects `*(arena_alloc_raw(` / `*(heap_alloc(` in `compiler/`;
- remove the two baseline lines.

Both ids are admitted to `_workspaces/baseline-failures.txt` as `regression:t502-uninit-latent  T543`, with the evidence
in a comment block.

## 2. Side finding: garbled interner sizes reach the shipped axiomc (T544)
`compiler/kernel/interner.ax` has garbled size arguments since T081 (d57fb098). T082d-report §4 already noted them, but
no task fixed them:
- `heap_alloc(new_(((cap as isize) * …)))`
- `heap_free(…, old_(mcap << 3), 8)`
- `heap_free(…, cur_(cap << 2), 4)`

They resolve only through `INTERNER_SHIM_MODULE` in `tests/selfhost/bundle_common.py` (`new_(x) = 1048576`,
`old_(x) = cur_(x) = x`, `cap = mcap = 1`). I checked that `gen_obj_link_driver_tests.axiomc_bundle_text()`, which
`tools/bootstrap.py` uses to build axiomc, contains `module _interner_shim`. So the production compiler has two defects:
- Every string-table growth allocates exactly 1 MiB. The 65,537th distinct string is written past that block.
- Every free passes a wrong size.

**T544** (priority 15, axiom-stdlib) restores the expressions, removes the shim, and adds a 70,000-string regression.
It does not block any gate today.

## 3. T428j finding 1: struct-like enum variant construction (T428n)
I reproduced it on HEAD. `enum E { A, S { x: i64, y: i64 } }` with `let s = E.S { x: 5i64, y: 6i64 };` gives
`AX_VERIFY_TYPE_MISMATCH: enum aggregate variant field count mismatch` in both `run --interp` and `build`. SPEC-02
AXS-GRM-030/095 allow these variants, so this is a TYPE A bug. No board task covered it (grep for "struct variant",
"field count mismatch", "struct-like").

**T428n**: priority 30, axiom-semantics, depends on T428j because it shares `compiler/mir/builder.ax`. It also restores
the case T428j removed from `enum_payload.ax`.

## 4. T428j finding 3: place-operand timing (T428o)
This is a real semantics gap (AXS-SEM-040) and it is wider than aggregates. Probes on HEAD, with the same wrong result
in `--interp`, native `-O0` and `-O1`:

| Program | Expected | Got |
|---------|----------|-----|
| `add(z, { z = 9i64; 1i64 })` | 6 | 10 |
| `w + { w = 9i64; 1i64 }` | 6 | 10 |
| `[y[0], bump(mut_view(y))]` gives `x[0]` | 1 | 100 |
| `P { a: p.a, b: bump_p(mut_view(p)) }` gives `q.a` | 3 | 200 |
| `(t5, { t5 = 9i64; 1i64 })` gives `.0` | 5 | 9 |

Because all modes agree, differential testing cannot catch it. This is a TYPE A implementation bug: the spec rule is
unambiguous, so no ADR is needed.

**T428o**: priority 25, axiom-semantics, opus/opus, depends on T428j. Scope: snapshot an earlier place operand into a
temporary only when a later sibling may write memory, and add golden MIR proof that the common case gets no extra
copies. Its gate includes a Tier-1 sweep.

## Board checks
- `taskctl.py lint` passes on all 4 new files.
- `taskctl.py validate`: OK (780 tasks).
- `harness_check.py`: HARNESS OK. The only warning is the optional guard hook, unchanged.
- `reqcov.py --strict`: gaps 0, COVERAGE OK.
- No file under the `paths`/`locks` of T428j or T428m was edited. Nothing under `docs/` was touched. Nothing was
  committed.

## Files changed
- _workspaces/baseline-failures.txt
- _workspaces/tasks/todo/T543-baseline-fix-uninitialised-reads-in-opt-passes-and-opt-harnesses.md
- _workspaces/tasks/todo/T544-fix-garbled-size-expressions-in-kernel-interner-and-drop-interner-shim.md
- _workspaces/tasks/todo/T428n-fix-struct-like-enum-variant-construction-verify-field-count-mismatch.md
- _workspaces/tasks/todo/T428o-fix-place-operands-read-at-use-not-at-evaluation-axs-sem-040.md
- _workspaces/reports/triage-2026-11-26-T502-regression.md
