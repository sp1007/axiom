# Audit oracle-independence — Independence of test oracles

## Tóm tắt
- Đã phân loại toàn bộ 946 test (802 file `.ax` + 144 manifest `.test`) theo nguồn gốc của kết quả kỳ vọng.
- Chỉ khoảng 16% số phép kiểm tra (~1.270/7.700) có kỳ vọng độc lập với compiler (đặc tả, tính tay, Python, GNU as/ld/objdump, Windows).
  ~72% (~5.500) là đối chứng axiomc-port với đầu ra của axiom0 (loại B, chung thiết kế). Phần còn lại là golden tự chụp hoặc chân native không kiểm tra gì.
- Đã chạy thử và xác nhận 4 lỗi ngữ nghĩa thật mà bộ test hiện tại không bắt được:
  (1) phép chia/lấy dư u64/usize ở native dùng `idiv` có dấu, nên sai khi số bị chia ≥ 2^63. Hậu quả: axiomc build native sẽ panic khi in hằng u64 lớn (`compiler/lir/lir.ax:502`, `mir.ax:1071`);
  (2) phép nhân u64/usize tràn số không bẫy ở native (interp bẫy, mã 101);
  (3) `isize/usize` dịch ≥ 32 bit bị panic ở **cả hai** chế độ (`builder.c:1650`);
  (4) `impl Drop` cho struct chỉ có trường kiểu scalar/con trỏ không bao giờ được gọi khi ra khỏi scope, ở **cả hai** chế độ.
  Lỗi (3) và (4) đúng loại điểm mù mà đối chứng interp/native, T139 và stage2==stage3 đều không thể thấy.
- Bộ vector băm AXH64 độc lập (Python) có sẵn, nhưng test Axiom dùng nó chỉ chạy ở interp; chạy native hiện trả về sai (rc=1).
  Test selfhost về hash lại kiểm tra một bản sao có thân intrinsic khác với `compiler/kernel/hash.ax`.
- 31 test LIR chỉ kiểm tra mã thoát 0: 49 file golden `.lir` không được so sánh (5/32 đã lệch). Bản thân `tests/obj/dummy.test` là `exit(0)`.
- COFF/PE: không có công cụ ngoài nào kiểm tra đầu ra thật của compiler. Cross-link gcc chỉ áp dụng cho `fn main() {}` và cho object viết tay (chỉ chạy trong ctest).
  `.obj` của chương trình thật không link được bằng ld (`kernel32$HeapAlloc`, `__ax_host_print`).
- Bảng encoder đối chiếu GNU as chỉ phủ 9/81 hàm encode, và bị loại khi compiler cần kiểm là axiomc (T086).
- Đề xuất: thêm task sửa AX0-FIX-02 (chia/nhân u64, độ rộng dịch usize, kèm bảng số học sinh bằng Python), là điều kiện của T086;
  cho T134 đối chiếu với `hash_vectors.txt` của Python; kiểm objdump cho mọi exe/obj; mở rộng bảng GNU as và đưa nó vào test của axiomc.
  Lỗi Drop phải sửa trước khi đóng băng axiom0 (T087).

## Summary
Checked every test under `tests/` (852 `.ax` incl. 50 helpers, 144 `.test` manifests) against `tools/axtest.py`
semantics, classified each by where its expected result comes from, counted checks (ui annotations,
pinned exit/stdout, early-return checks, asserts, golden files), and probed the current compiler
(`build-snap-T085c/build/axiom0.exe`, no bootstrap change since) for the requested risk areas.
Findings: 4 BLOCKER, 7 MAJOR, 3 MINOR (7 of them CONFIRMED by reproduction).

## Method and categories
- **A-diag**: expected diagnostic code/line written by hand (ui `//~`, manifest `stderr-contains: AX_...`).
- **A-strong**: value pinned by a non-zero `exit:` or exact `stdout:` written by the author (spec/hand computation), not
  selfhost. **A-weak**: same, but the correct result is exit 0 (a "return 0" stub or vacuous backend can pass).
- **A-ext**: expected bytes/values from an external tool (GNU as, gcc/ld, objdump, Python reference, Windows loader).
- **B**: cross-check of two compiler paths (`test: diff`; selfhost bundles whose goldens are axiom0's output; determinism).
- **C**: self-snapshot golden (`--bless` / generator writing axiom0 output; reports T012, T034, T036, T054, T132 record re-blessing).
- **D**: no observable check (unit `fn main()` with no output, assert-only, exit-0-only manifest, dummy).
- "checks" = ui annotations + 1 per pinned exit/stdout + `return <non-zero>` checks + `assert(` calls + golden files
  (scripts: classification heuristics over directives and bodies; selfhost bundles counted as B).

## Tables

### 1. Totals
| Category | Tests | Checks (approx.) | Share of checks |
|---|---|---|---|
| A-diag (ui `.ax` 175 + manifests 69) | 244 | 305 | 4% |
| A-strong (non-selfhost, exit≠0 or stdout) | 229 | ~1 030 | 13% |
| A-weak (exit 0 is the pass value) | 116 | ~720 (128 of them native-vacuous asserts until T134) | 9% |
| A-ext (GNU as 135 vectors, Python hash 55 lines, gcc link 1+2 objects, objdump 1, PE loader 1) | 6 manifests (+ ctest-only drivers) | ~200 | 3% |
| A-hand exit-3 ICE/verifier drivers | 13 | 13 | <1% |
| B (31 diff, 144 selfhost, 2 determinism) | 177 | ~5 600 | 72% |
| C (68 golden `.ax`, 5 inline MIR/LIR dumps, drop goldens) | 74 | ~110 | 1% |
| D (37 smoke runs, 2 assert-only, 39 exit-0 manifests, 2 dummies) | 80 | 80 (prove nothing) | — |
| in-progress (T085 `axiomc_e2e.test`, not classified) | 1 | — | — |

Independent (A-*) ≈ 16% of checks if A-weak counts as half. Excluding B, the suite would hold ~2 100 checks, of which
only ~200 come from a tool outside the compiler and its authors.

### 2. Per area (tests; checks in parentheses where large)
| Area | A-diag | A-strong | A-weak | A-ext | B | C | D |
|---|---|---|---|---|---|---|---|
| lex | 22 (ui/lex manifests) | – | – | – | 7 selfhost | 15 `.tokens` | 1 (E01 exit-only) |
| parse | 6 manifests + ui | – | – | – | 26 selfhost | 28 `.ast` | 4 exit-only |
| resolve / hir / modules | 23 | 5 modules | – | – | 17 selfhost | 10 | 1 |
| types (typeck/trait/generic/enum…) | 104 (152) | – | 2 | – | 9 selfhost | 2 | – |
| own / drop | 39 (ui + verify/own) | 28 run/drop | 1 | – | 21 selfhost + drop goldens | 1 | 7 |
| mir / verify | 11 | – | – | – | 6 selfhost | 13 | – |
| interp (lang run tests) | – | 37 | 60 (228) | – | 10 diff + 10 selfhost | – | 24 |
| numeric semantics | – | 17 (exit 101 traps) | 7 (131, assert-based) | – | conformance diff | – | – |
| conformance vs0/p5/p7/std | 28 | 68 (127) | 8 | – | 21 diff | – | 8 |
| opt | – | – | 3 | – | 3 diff + 7 selfhost | – | – |
| lir | – | – | – | – | 7 selfhost | 1 inline | **31 (orphaned `.lir`)** |
| x64 isel/frame/abi | 5 (exit 3) | 10 native | 24 | 6 ctest-only drivers (hand ABI) | 13 selfhost | 4 `.mi/.mc` | 7 |
| x64 encode | – | – | – | 1 (135 GNU-as vectors) | 3 selfhost (260) | – | – |
| obj (COFF) | – | – | – | ctest-only `cdriver_coff` (gcc); `build_emit_obj` (`fn main(){}`) | 3 selfhost | – | **`obj/dummy.test`** |
| link (PE) | 1 | – | – | `link.test` (loader), `build_stack_reserve` (objdump -p) | 2 selfhost | – | – |
| runtime / io / UTF-8 | – | 12 | 6 | 8 stdout UTF-8 byte tests | – | – | 1 |
| std | 2 | 36 (727) | 5 | hash vectors (**interp-only**) | – | – | – |
| selfhost | – | – | – | – | 144 (~5 500) | – | – |

### 3. Existing independence mechanisms: do they actually run?
| Mechanism | Where | Per-task axtest gate | With axiomc (T086, `--exclude-requires axiom0-internal`) | Strength |
|---|---|---|---|---|
| GNU as encoder vectors | `tests/encode/encode.test`, `encode_tests.inc` (135), `tools/gen_encode_tests.py` | yes | **excluded** (`requires: axiom0-internal`) | 9 of 81 encoder entry points |
| AXH64 Python reference | `tests/unit/kernel/gen_hash_vectors.py`, `hash_vectors.txt` | yes (C kernel only) | C unit excluded; std check `modes: interp` | Axiom-side native never checked |
| T026 gcc cross-link of hand-built objects | `tests/obj/cdriver_coff.c` | **no** (ctest only; axtest has `obj/dummy.test`) | no | hand bytes, not compiler output; passes today (re-run in scratch) |
| T028 cross-link of every native run test | T028 acceptance line 33 | **not implemented** | – | infeasible as built (see OI-07) |
| gcc link of `--emit=obj` | `tests/driver/build_emit_obj.test` | yes | yes | only `fn main() {}` |
| objdump -p stack reserve | `tests/driver/build_stack_reserve.py` | yes | yes | one header field |
| PE written from hand bytes + Windows loader | `tests/link/cdriver_pe.c` | yes | excluded | one 6-byte program |
| Windows loader + CPU running every native test | all native run legs | yes | yes | broad but only as good as the expected values |
| UTF-8 stdout bytes | 8 tests (`run/str/hello.ax`, `std/io/qa_console.ax`, …) | yes, both modes (7) | yes | pipe only, console path untested |
| `native-after` / `xfail` | – | 0 / 0 remaining | – | no hidden native skips |
| `modes: interp` without accepted reason | 9 tests (OI-09) | hides native | hides native | – |

## Findings

### OI-01 [BLOCKER] [CONFIRMED] Native unsigned 64-bit `/` and `%` are compiled as signed `idiv`
- Where: `bootstrap/axiom0/src/target/x64/isel/isel.c:338-351` (DIV/REM: `sar rdx,63` + `idiv` for every type; LIR `div`
  carries no signedness, `tests/lir/div.lir`); ported as-is in `compiler/target/x64/frame.ax:572`.
- Problem: when the dividend is ≥ 2^63, u64/usize results are wrong natively, while interp is correct. Probes (exit code,
  interp vs native): `0x8000000000000000/2^56` 128 vs 127; `u64::MAX % 10` 5 vs wrong; `usize::MAX/2^56` 255 vs 0.
  No test divides a u64 with the high bit set. `std/text/fmt/int.ax:404 u64_div_u32` is a workaround for this bug in std.
- Consequence: the natively built axiomc prints u64 constants with `n % 10u64` / `n / 10u64` (`compiler/lir/lir.ax:502`,
  `compiler/mir/mir.ax:1071`, `compiler/interp/interp.ax:455`). The same loop compiled natively panics on `u64::MAX`
  (probe: interp 20 digits, native `panic: arithmetic overflow`, exit 101). Stage-1 `inspect`/golden output then differs or
  aborts. stage2==stage3 cannot detect it because the axiomc port has the same isel design.
- Proposed oracle: a Python generator (`tests/run/numeric/gen_int_semantics.py`) that emits run tests per op × width
  (i8..i64, u8..u64, isize, usize) × edge operands {0, 1, 2, MAX, MIN, MAX-1, 2^(w-1), 2^(w-1)±1}. Expected results are
  computed in Python with SPEC-03 rules (trap → exit 101). Results are printed as decimal `stdout:` or folded into a
  checksum exit. Runs in interp, native and -O1. Effort: generator 0.5 day; fix (LIR `udiv/urem` or signed flag; x64
  `xor edx,edx` + `div`) 0.5–1 day in axiom0 and in the port.
- Gate T086: **yes**. DECISION NEEDED: (a) widen T134; (b) a new task AX0-FIX-02 (paths `lir`, `target/x64`, `mir/build`,
  `tests/run/numeric`; the port's `compiler/target/x64` as follow-up); recommend (b), depending on T134 (shared paths), with T086 depending on it.

### OI-02 [BLOCKER] [CONFIRMED] Native u64/usize multiplication overflow is not trapped
- Where: `isel.c:210-262` (`UMUL_OVERFLOW`, 64-bit path). Probes: `2^32*2^32` and `usize::MAX*2` interp 101, native and
  -O1 continue (exit 9). Other widths and ops trap correctly in both modes (19 probes).
- Problem: this is an interp/native divergence that no test covers, because only u8/u16/u32/i* multiplication-overflow
  tests exist (`tests/run/numeric/qa_overflow_*.ax`). It also hides wrong code: `tests/selfhost/kernel/qa_kernel_hash.ax:30-31`
  declares `wrapping_mul_u64 { a * b }`. That body is checked arithmetic and passes natively only because of this bug.
- Consequence: natively built axiomc silently wraps where its oracle run panics. Any accidental u64 overflow in the port
  gives different stage-1 vs interp behaviour.
- Proposed oracle: the OI-01 generator (checked `+ - * neg` at boundaries per width). Effort: included in OI-01.
- Gate T086: **yes** (same fix task).

### OI-03 [BLOCKER] [CONFIRMED] Native hash correctness is never checked against the independent reference
- Where: `tests/std/core/qa_hash_vectors.ax:2` is `modes: interp` with no accepted reason. Built natively today it exits 1
  (first vector wrong). `tests/selfhost/kernel/qa_kernel_hash.ax` tests a hand copy, not `compiler/kernel/hash.ax:3-5`
  (`{ 0 }` placeholder bodies, embedded verbatim in 58 selfhost bundles). T134 acceptance ("reference constant produced
  by axiom0's C `kernel/hash.c`") picks a B oracle, although the Python reference
  `tests/unit/kernel/gen_hash_vectors.py` / `hash_vectors.txt` (55 vectors) already exists.
- Consequence: interner, HashMap and mangling in natively built axiomc use a constant hash. Outputs that depend on hash
  values or iteration order differ between stage-1 and the oracle; selfhost tests cannot see it, because their goldens
  come from axiom0 C built by gcc and they test copies.
- Proposed oracle: remove `modes: interp` from `qa_hash_vectors.ax`. Add a test built from the real `compiler/kernel/hash.ax`
  that reads every line of `hash_vectors.txt` (or a generated byte table) and prints the hashes, in both modes. Change T134's
  acceptance to cite the Python vectors. Effort: 2 h.
- Gate T086: **yes** (amend T134 acceptance; already a T086 dependency).

### OI-04 [BLOCKER] [CONFIRMED] Correctness of the self-host rests mainly on axiom0-vs-port agreement
- Where: 144 `tests/selfhost/**` bundles hold ~5 500 of ~7 700 counted checks (72%), and their goldens are axiom0 output
  (`gen_backend_tests.py` docstring, `gen_drop_tests.py:3-20`, `cdriver_drop_oracle.c:1-10`). T086 acceptance line 2
  (`--emit=obj` of axiomc1 byte-identical to axiom0) is B again. At T086 the A-ext checks drop out: encoder vectors,
  `link.test`, `mc/frame`, C units and `drop_oracle` are all `requires: axiom0-internal`.
- Problem: any defect in axiom0's design is inherited. OI-01 (port `frame.ax:572` uses `idiv` like the C), OI-05 (builder
  shift width) and OI-06 (drop elaboration, ported from C) are confirmed instances.
- Consequence: T086 can PASS with stage-1 wrong on u64 arithmetic, usize shifts and destructors.
- Proposed fix: add an "independent subset" acceptance to T086. With `--compiler axiomc1`, every A-diag/A-strong/A-ext test
  must pass natively: conformance/vs0, run/numeric (+ the OI-01 generator), run/drop (+ OI-06 tests), hash vectors (OI-03),
  objdump validation (OI-07), and an Axiom port of the GNU-as vectors (OI-08). No new infrastructure beyond those items.
- Gate T086: **yes**.

### OI-05 [MAJOR] [CONFIRMED] `isize`/`usize` shifts by ≥ 32 panic in both executors
- Where: `bootstrap/axiom0/src/mir/build/builder.c:1650-1656`: `bits` defaults to 32 and ISIZE/USIZE are not listed. Probes:
  `usize >> 32..63` and `isize << 40` give `panic: shift amount out of range` (101) in interp and native. u64 shifts are fine.
- Problem: this is a shared-MIR bug. T139's cross-mode agreement cannot detect it (both modes agree), and no test shifts a
  usize by ≥ 32 (`tests/conformance/vs0/shift_*` use i32/u8).
- Consequence: any port or std code doing `x >> 32` on usize aborts. The current sources happen to use u64 for wide shifts
  (`compiler/obj/coff.ax:143`, `std/core/hash.ax:134`).
- Proposed oracle: the OI-01 generator with amounts {0, 1, w-1, w, w+1, negative} per width, from SPEC-03 AXS-SEM-034.
  Effort: 1-line fix plus tests.
- Gate T086: **yes** (trivial; include in AX0-FIX-02).

### OI-06 [MAJOR] [CONFIRMED] `impl Drop` on a struct with only scalar/pointer fields never runs implicitly
- Where: SPEC-12 AXS-DROP-001. Probes: `struct Foo { x: i32 }` (and `{ p: *mut u8 }`, generic `G<T> { p: *mut T }`)
  with `impl Drop` print nothing at scope end in interp and native. Explicit `drop(f)` works, `Foo` is move-only
  (`AX_MOVE_USE_AFTER_MOVE`), and field-less or droppable-field structs work. std works around it with a `_glue: DropGlue`
  field (8 files, e.g. `std/alloc/vec.ax:13`, `std/bytes/byte_buf.ax:10`). `std/core/arena/arena.ax:21` (Arena) has no such
  field and never frees implicitly.
- Problem: all 28 run/drop tests use field-less or nested-droppable structs, and the selfhost drop goldens are the C
  elaboration's own output (C/B). Both executors agree, so neither T134 nor T139 sees it.
- Consequence: leaks and unclosed handles in axiomc (relevant to the ADR-0005 §7 memory budget at T086). User-visible
  semantic bug, frozen into axiom0 after T087.
- Proposed oracle: SPEC-12-derived run tests whose expected drop order is written by hand (`stdout:`): scalar-field,
  pointer-field and generic structs; nested; early return; loop break. Effort: 0.5 day tests, fix in `mir/drop` + port.
- Gate T086: no (unless the budget fails); **gate T087 (freeze): yes**. File AX0-FIX-03.

### OI-07 [MAJOR] [CONFIRMED] COFF/PE output of real programs is never validated by an external tool
- Where: T026 acceptance (`_workspaces/tasks/done/T026-coff-object-writer.md:35`, objdump -x/-d) and T028 acceptance
  line 33 (cross-link every native run test) have no test. `tests/driver/build_emit_obj.test` links only
  `tests/driver/test.ax` = `fn main() {}`, and `tests/obj/dummy.test` is `python -c "exit(0)"`. The real gcc cross-link
  (`tests/obj/cdriver_coff.c`) links hand-built objects and runs only in ctest (`tools/ci.sh:101`, i.e. phase gates); the
  last recorded ctest log (`build/Testing/Temporary/LastTestsFailed.log`, 2026-10-11) lists it as failed. It passes today
  (re-run in scratch). It also prints SKIP and exits 0 without gcc.
- Problem: as built, T028's oracle is infeasible. `axiom0 build --emit=obj tests/std/fmt/qa_int_format.ax` linked with
  `ld` gives undefined `kernel32$HeapAlloc`, `__ax_host_print` and `axiom_panic`, because the runtime and the import naming
  exist only in axiom0's own linker. `objdump -x/-d` does parse our .obj and .exe (0 `(bad)` in 24 k lines, KERNEL32.dll
  import shown), but nothing checks that in the suite.
- Proposed oracle: (a) an exec manifest `tests/link/objdump_validate.test` running a Python script that builds a fixed
  list of native run tests (obj + exe). The script runs `objdump -x -d` and checks: parse OK, no `(bad)`, entry point
  inside `.text`, section flags, every import named in the program present, relocation count equal to the `.mc`
  relocation listing. Effort 0.5–1 day. (b) Optional: `--emit=obj` emits standard `__imp_` references plus a runtime
  object, so gcc/ld can link real programs (2–3 days; changes the obj model).
- Gate T086: **(a) yes** (cheap, and it is the only external check of axiomc's ported COFF/PE writer); (b) no.

### OI-08 [MAJOR] [CONFIRMED] GNU-as encoder vectors cover 9 of 81 encoder entry points and vanish at T086
- Where: `tests/encode/encode_tests.inc` covers only mov_rr/add_rr (48 each), mov_rm with addressing modes (34),
  cdq/cqo/int3/jmp8/ret; call/jmp rel32 is hand-written in `cdriver_encode.c:30-40`. The API has 81 functions
  (`target/x64/encode/encode.h`). A real exe uses movabs (2 218), lea (2 194), shl/shr/sar (786), setcc, idiv/div, imul,
  push/pop and jcc (objdump of `qa_int_format`), and none of these are vector-checked. `encode.test` has
  `requires: axiom0-internal`. The selfhost encoder test (`tests/selfhost/encode/qa_encode_instructions.ax`, 227 checks)
  partly transcribes the same table and otherwise uses axiom0 bytes.
- Consequence: the CPU indirectly validates only the forms it actually executes. A wrong encoding on a rarely used
  register/form (r12/r13 base, spl..dil, imm8/imm32 boundary, setcc on r8b+) passes until a program hits it.
- Proposed oracle: extend `tools/gen_encode_tests.py` to every entry point × {rax..r15, 8/16/32/64}, × addressing
  {base, base+disp8/32, SIB, rsp/r12, rbp/r13, rip}, × imm boundaries. Emit the same table also as an Axiom test against
  `compiler/target/x64/encode.ax`, so axiomc is checked against GNU as and not against axiom0. Effort: 1–2 days.
- Gate T086: **yes**, at least for the forms isel emits (list from `isel.c` emit calls).

### OI-09 [MAJOR] [CONFIRMED] Weak or vacuous native legs remain outside T134/T139's net
- Where: 37 run tests have a unit `main` and no output (e.g. `tests/run/vars/compound.ax`,
  `tests/run/comptime/table_u8_256.ax`, whose checks `return;` with exit 0). Two are assert-only
  (`tests/run/str/qa_hello_empty.ax`). 116 tests pass when the result is exit 0. 6 numeric tests (128 asserts,
  `tests/run/numeric/intrinsic_ops.ax`) are vacuous natively until T134. 9 `modes: interp` lack an accepted reason
  (`run/basic/t117_panic.ax`, `t117_qa_neg_i8_min.ax`, `run/fn/eval_order_panic1/2.ax`, `std/core/qa_hash_vectors.ax`,
  `std/alloc/qa_sort_interp.ax`, `std/arena/qa_arena_scale_interp.ax`, `run/basic/008-step-limit.ax`, `009-call-depth.ax`).
  The four panic tests pass natively today, so these restrictions are stale.
- Problem: T139 (`_workspaces/tasks/todo/T139-*.md` §Scope) makes `WEAK-NATIVE` informational only, and agreement checks
  do not help when both modes agree.
- Proposed fix: T134's sweep converts D-smoke tests to return or print computed values that differ from 0. Remove stale
  `modes: interp`. Make `WEAK-NATIVE` = 0 for `tests/run/{numeric,drop,ptr,native_*}` and `tests/std` a T086 acceptance
  line. Effort: 0.5–1 day.
- Gate T086: **yes** (via T134/T139, already dependencies).

### OI-10 [MAJOR] [CONFIRMED] LIR lowering "tests" compare nothing; their goldens are orphaned
- Where: 31 `tests/lir/*.test` manifests contain only `cmd: {compiler} inspect --emit=lir tests/lir/X.mir`. Exec
  manifests do not read sibling files (`tools/axtest.py:956-993`), so 49 `.lir` files are never compared; 5 of 32 already
  differ from current output (abi_arg, abi_result, call, offset, qa_multi_branch). `tests/lir/COVERAGE.md` claims per-op
  coverage, and `tests/hir/more.test` is the same pattern.
- Consequence: false coverage claim exactly where OI-01 lives (LIR `div` without signedness).
- Proposed fix: since T139 locks `tools/axtest.py`, it adds golden comparison for `.mir` inputs with a sibling `.lir` (or
  an exec `stdout-file:` directive); the 5 drifted goldens are reviewed, not blind-blessed. These remain C-category
  evidence; real independence for LIR comes from OI-01 execution.
- Gate T086: no (fold into T139).

### OI-11 [MAJOR] [PLAUSIBLE] Selfhost bundles test copies, and freshness is not enforced
- Where: `tests/selfhost/kernel/qa_kernel_hash.ax:30-31` differs from `compiler/kernel/hash.ax:3-5`.
  `tests/selfhost/drop/gen_drop_tests.py` (MODULES comment) says the front end comes from "copies QA accepted with T082a,
  because the compiler/ front-end files at HEAD do not build together". Only 3 of 9 generators have a `check` mode, and
  only drop has a manifest (`drop_oracle.test`).
- Consequence: B evidence may concern code that is not what axiomc is built from.
- Proposed fix: a `bundles_current.test` per generator (regenerate into `{tmp}` and byte-compare), like
  `hash_vectors_current.test`. Effort: 0.5 day.
- Gate T086: yes (cheap; otherwise T086's first full run is the first real test of HEAD sources).

### OI-12 [MINOR] [CONFIRMED] Windows x64 ABI is checked only against kernel32/msvcrt and hand assertions
- Where: `tests/mc/isel/cdriver_abi*.c` use C `assert()` (compiled out under NDEBUG) and run only in ctest. `tests/run/ffi/*`
  call abs/labs/kernel32. CreateFileW (7 args) in native std fs tests is the only stack-argument evidence. My probe: a
  7-argument mixed-width call plus struct-by-value passing gives 183 in interp, native and -O1, matching Python;
  `@repr(C)` sizes 24/12 match C rules.
- Proposed oracle: a gcc-built test DLL (`gcc -shared`) exporting functions with 1..8 mixed-width args and structs of size
  1/2/3/4/8/12/16/24 by value and return; Axiom calls them via `@link` and prints checksums. Also add a `gcc` `offsetof`
  table for `@repr(C)` layouts. Effort: 1 day.
- Gate T086: no (axiomc only calls kernel32 with scalars/pointers); before FFI breadth (E13).

### OI-13 [MINOR] [CONFIRMED] UTF-8 output and panic/exit codes: independent, with small gaps
- Where: 8 tests pin `Xin chào thế giới` stdout bytes, encoded by the runner from the UTF-8 directive (Python is the oracle;
  7 run in both modes, `run/ffi/write_file.ax` native-only). Panic exit 101 goes through ExitProcess and is pinned in
  17 numeric and many conformance tests, plus the exact `panic: <msg>\n` stderr line. Gaps: console output
  (WriteConsoleW, not a pipe) is untested; native `assert`/`panic` canaries wait for T134.
- Proposed fix: none before T086 beyond T134's canaries. Console check is manual (owner) or via a pseudo-console later.
- Gate T086: no.

### OI-14 [MINOR] [PLAUSIBLE] Symbol mangling has no independent oracle
- Where: mangled names appear only in selfhost B diffs (`tests/selfhost/backend/*`). ADR-0032 names destructors `T_drop`,
  which a user function `Foo_drop` could collide with. A probe could not show it because of OI-06. The linker's
  duplicate-symbol check (`cdriver_pe.c` dup test) would catch collisions only at link time.
- Proposed oracle: run/ui tests with deliberately colliding names (user `Foo_drop`, same method name on two types, generic
  instances `G<i32>`/`G<u32>`), expecting distinct behaviour or `AX_LINK_DUPLICATE`. Effort: 2 h.
- Gate T086: no.

## Prioritised recommendations (before T086)
| # | Finding | Evidence | Independent oracle | Effort | Gate T086 |
|---|---|---|---|---|---|
| 1 | u64/usize `/ %` signed idiv | `isel.c:338-351`; `compiler/lir/lir.ax:502` | Python integer-semantics generator | 1–1.5 d (tests + fix) | yes (AX0-FIX-02) |
| 2 | u64 mul overflow not trapped | `isel.c:210-262` | same generator | in #1 | yes |
| 3 | usize/isize shift width 32 | `builder.c:1650-1656` | same generator (SPEC-03 AXS-SEM-034) | 1 h + tests | yes |
| 4 | native hash unchecked vs Python | `tests/std/core/qa_hash_vectors.ax:2`; `compiler/kernel/hash.ax:3-5` | `hash_vectors.txt` in both modes from real module | 2 h | yes (amend T134) |
| 5 | T086 lacks an independent subset | T086 §Acceptance | A-subset must pass with axiomc native | 0 (acceptance edit) | yes |
| 6 | objdump validation of real exe/obj | T026:35, T028:33 unmet | objdump -x -d script manifest | 0.5–1 d | yes |
| 7 | encoder vectors 9/81, excluded at T086 | `encode_tests.inc`, `encode.test` | extended GNU-as table + Axiom twin | 1–2 d | yes |
| 8 | weak/vacuous native legs, stale `modes: interp` | OI-09 list | computed exits/stdout; WEAK-NATIVE=0 in core dirs | 0.5–1 d | yes (T134/T139) |
| 9 | selfhost bundle freshness | `gen_drop_tests.py` comment; `qa_kernel_hash.ax:30` | regenerate-and-compare manifests | 0.5 d | yes |
| 10 | Drop on scalar-field structs | SPEC-12 AXS-DROP-001; std `DropGlue` workaround | hand-written drop-order stdout tests | 0.5 d + fix | no (gate T087) |
| 11 | LIR goldens orphaned | `tests/lir/*.test`, 5/32 drifted | golden compare in runner (T139) | 2 h | no |
| 12 | ABI vs gcc-built DLL | `cdriver_abi*.c` | gcc `-shared` DLL + offsetof table | 1 d | no |
| 13 | mangling collisions | ADR-0032 | colliding-name tests | 2 h | no |

## Checked and OK
- No `native-after` or `xfail` directive remains (`grep -rn native-after tests` = 0), so no native leg is silently skipped by directive.
- Checked arithmetic traps (+, -, *, neg, /, %, shift range) give exit 101 natively for i8..i64, u8..u32 and usize add (19 probes).
- Signed `>>` is arithmetic and unsigned `>>` logical for i8/i16/i32/i64/u8/u16 with variable amounts (6 probes); narrowing/widening casts are correct (4 probes); i8/i16/u8 div/rem/mul are correct (5 probes).
- 7-argument mixed-width calls and struct by value/return (3, 12, 16, 24 bytes) agree in interp, native and -O1 and match Python; `@repr(C)` layout matches C rules.
- `objdump` parses our .obj and .exe without `(bad)`; the import table names KERNEL32.dll.
- C drivers `ct_obj_cdriver_coff`, `ct_link_cdriver_pe`, `ct_mc_isel_cdriver_abi*` and `ct_mc_frame_cdriver_probe*` pass (re-run on scratch copies).
- The AXH64 Python reference is a genuinely independent implementation (`gen_hash_vectors.py`), and `hash_vectors_current.test` keeps the file in sync.
- conformance/vs0 (84 tests) cites SPEC-03 rule ids and pins non-zero exits or panic stderr: spec-derived (A).
- run/drop (28) pins drop order by `stdout:` written by hand per SPEC-12.
- UTF-8 greeting bytes are compared as raw bytes in both modes.

## Cross-lens notes
- Process: `tests/std/core/qa_hash_vectors.ax` and the 9 unexplained `modes: interp` contradict axiom-testing's rule
  "QA fails any other restriction", yet they passed gates.
- Process: the repo root contains ~300 ad-hoc scripts (e.g. `fix_tests.py`, `restore_tests.py`,
  `patch_remove_native_after.py`). Any of them may have edited expectations; not audited here.
- Frontend (PLAUSIBLE): `fn main() -> i32 { ...; if c { return 5; } return 6; }` written on one line gives
  `AX_TYPE_RETURN` ("can reach its end"), while the multi-line form is accepted.
- Build hygiene: `build/axiom0.exe` (2026-10-14) is older than HEAD. Anyone running `tools/axtest.py` with its default
  `--compiler` tests a stale compiler.
- `tests/std/alloc/qa_sort_interp.ax` does not build natively (`AX_LINK_UNDEFINED_SYMBOL __ax_host_heap_alloc`): host
  intrinsics need `std/sys/windows` discovery (known; see `run/host/heap/alloc.ax` reason).

## Answer
About one sixth of the suite's evidence comes from outside the compiler: diagnostic codes and values hand-derived from the
specs (~1 270 of ~7 700 checks), plus a thin layer of real external tools. That layer is 135 GNU-as encoder vectors, a
Python AXH64 reference, one header field via objdump, gcc linking two hand-built objects and an empty program, and the
Windows loader/CPU executing every native test. Nearly three quarters of the checks (the 144 selfhost bundles) compare the
Axiom port with axiom0's own output. Most remaining checks are self-snapshot goldens or native legs that check nothing.
This is not hypothetical. Reproducing the requested risk areas found four live semantic bugs the suite misses:
- u64/usize division and remainder with the high bit set are wrong natively;
- u64 multiplication overflow is not trapped natively;
- usize/isize shifts ≥ 32 panic in both modes;
- Drop never runs for structs with only scalar or pointer fields, in both modes.

The native std hash check is interp-only and fails natively. Two of these bugs (shift width, Drop) are invisible to every
interp/native, axiom0/axiomc and stage2==stage3 comparison by construction. The first one would make a natively built axiomc
abort when printing large u64 constants. Before T086, add one cheap Python-generated integer-semantics table plus fix task
(AX0-FIX-02), point T134 at the Python hash vectors, add objdump validation and a widened GNU-as table that also runs
against axiomc, and require this independent subset to pass with axiomc natively. Drop fixes can wait until just before
the T087 freeze.
