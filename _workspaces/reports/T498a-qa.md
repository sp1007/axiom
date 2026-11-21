# T498a QA

## Round 0

Gate of T498a (round 0, engineer report `STATUS: COMPLETE round=0`). Snapshot `build-snap-T498a/` is HEAD 6d190d4 plus the
task change set plus the 3 QA tests below. I refreshed it with `taskctl.py snapshot T498a`: "14 changed, 0 deleted", bundles regenerated
(36 generators, 60 files), no BUNDLES FAILED.

### Change set
`python .claude/skills/axiom-tasks/scripts/taskctl.py changes T498a` stages isel.ax, the 9 tests under `tests/run/agg_odd_size/`
(6 by the engineer, 3 by QA), `tests/run/array_copy/nested_and_field.ax`, `tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax.in`
and the 2 reports. There are **no REFUSED lines**. Nothing changed under `bootstrap/axiom0`, `tools/`, `diag/`, `driver/` or the locked
files (`lir/builder.ax`, `lir/lir.ax`, `abi/win64.ax`, `x64/frame.ax`). The diff has no `BOOTSTRAP-SHORTCUT`.

### Build (fresh, inside the snapshot)
- `rm -rf build && cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Release && cmake --build build`:
  132/132 built, 0 warnings (log `_workspaces/T498a_qa_cmake.log`).
- `python tools/build_axiomc.py --out build --force`: STAGE1 OK, STAGE2 (O1) OK, STAGE3 OK, `FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`.
  axiomc2 sha256 is `dafee55db1e9badc…`, identical to the engineer's build, so the build is reproducible (log `_workspaces/T498a_qa_axiomc.log`).

### Code review (isel.ax)
- All 6 widening sites are replaced by the exact-width helpers: O0 LOAD, O0 STORE, O0 indirect ABI_RESULT, O1 LOAD (slot and address
  forms), O1 STORE (slot and address forms) and O1 indirect ABI_RESULT. I grepped for the remaining `!= 1u32 && != 2u32 && != 4u32` patterns:
  - `isel_check_diamond_arm` rejects odd sizes, so the cmov path never sees them.
  - In the slot-promotion analysis, odd sizes mark the slot as escaping, so the slot is not promoted.
  - `isel_type_is_ret_in_mem` returns 3/5/6/7-byte values in memory, which matches Win64.
  - The indirect ABI_ARG and incoming-parameter copies already used `isel_chunk_size` chunks.
- **Partial-register safety at -O1.** I checked the frame.ax peepholes against the new sequences:
  - `MOV r, 0` → `XOR r,r`: correct.
  - The dead-def unlink and the "copy into r1" rules require the next MOV to be 8 bytes. A 1- or 2-byte `MOV CL/CX` never qualifies,
    so the zeroing before the partial loads is never deleted.
  - Store-to-load forwarding stops at any def of the source register, including SHR/SHL and the partial MOV, and it only forwards
    8-byte stores.
  - The odd paths leave `tag_vreg` as NONE, so the RCX origin cache never claims a shifted RCX.

  objdump of the -O1 build of `qa_sizes_1_8` shows the expected code:
  - loads are `xor rcx,rcx; mov cl,[..+6]; shl rcx,16; mov cx,[..+4]; …`;
  - stores are `mov [..],ecx; shr rcx,32; mov [..+4],cx; shr rcx,16; mov [..+6],cl`;
  - when the vreg is allocated to R11, the `mov r11,rcx` comes before the shifts, and nothing reads RCX as the vreg after a shift.
- The selfhost isel check update is a correct expectation change and is stronger than before. The old check required the buggy 8-byte
  MOV. The new one checks the 2-byte loads at +4/+0, the 4-byte store at +0, the 2-byte store at +4, and that no 8-byte `[mem]` MOV
  appears anywhere in the block (return codes 203, 204, 206).

### Taskgate (inside the snapshot)
`python tools/taskgate.py --task T498a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T498a.json`
(log `_workspaces/T498a_qa_taskgate.log`):
- Affected set: exact deps of `run/agg_odd_size/*` and `run/array_copy/nested_and_field.ax`; the map `compiler/target` → `tests/mc` and
  `tests/selfhost/encode`; the bundles embedding `compiler.target.x64.isel` (`selfhost/{backend,driver,isel,obj_link_driver}`, changed bundle
  files plus `bundles_current.test`).
- Unmatched: none. The cache verification sample (n=20 of 51) had no mismatch.
- Smoke draw seed=2608341455. It includes `run/str/hello.ax` (Xin chào thế giới), `ui/typeck/type_unknown.ax` and `diff/002-arithmetic.ax`.
- Result: `TOTAL 217 PASS 205 FAIL 0 SKIP 12 XFAIL 0`, BASELINE OK, failing ids none, archcheck clean (232 files, 0 violations),
  WEAK-NATIVE 0 in the task's own/changed tests. `TASKGATE T498a exit=0`.

### Native groups (task acceptance groups)
`python tools/axtest.py --compiler build/axiomc2.exe --gate -j 2 --exclude-requires axiom0-internal --baseline _workspaces/baseline-failures.txt run conformance selfhost/lir selfhost/x64 selfhost/isel selfhost/encode`
(log `_workspaces/T498a_qa_groups.log`):
- `TOTAL 4331 PASS 4331 FAIL 0 SKIP 0 XFAIL 0`, BASELINE OK.
- Cache: 1199 hits, of which 60 were re-verified fresh. 295 misses and 174 uncacheable tests ran fresh.
- WEAK-NATIVE is 141 in the whole run; all of those are older tests, and none is in agg_odd_size, nested_and_field or the QA tests.

### Native evidence (step 4a)
- Every test the task added or touched is a `run` test in the default modes (interp, native, native-O1) with an exact `// stdout:`
  and `exit: 0`. No test is restricted to one mode and none uses `native-after`.
- Mutation proof: I changed `tests/run/agg_odd_size/repro.ax` `// stdout: 4\n…` to `5\n…` in the snapshot only. The `[native]` and
  `[native-O1]` legs FAILED ("stdout differs at byte 0"), along with interp. I then restored the file (`cmp` against the main tree: identical).
- Bug-is-live proof for the QA tests: with the HEAD compiler (`_workspaces/artifacts/compiler-cache/axiomc2_O1_8f1bf509637025c3.exe`,
  sha256 88fa98f2…), `qa_sizes_1_8` and `qa_signed_pressure` FAIL natively at O0 and O1. Example: `161 10 11 12 178` becomes `0 10 11 12 178`,
  because the store of `x: [3]u8` clobbered `pre`. Interp passes. With the fixed compiler all legs pass.

### Adversarial tests added (step 5)
Expectations are computed independently in Python, not taken from the interpreter.
- `qa_sizes_1_8.ax` and `qa_sizes_9_16.ax`: `struct W{ pre: u8, x: [N]u8, post: u8 }` and `[3]H{N}` for every N = 1..16. Each step prints
  every byte of `x` and of both canaries. The steps are:
  - struct literal, field store `w.x = …`, store through `mut_view`;
  - copy twice into a fresh literal, then assignment;
  - by-value argument;
  - an array of N-byte elements: constant-index whole-element store, element-field store, dynamic-index store of a struct returned by
    a function, and the array passed by value.

  `9_16` passes at HEAD too and guards the multi-chunk tails (sizes 9..15) against regression.
- `qa_signed_pressure.ax`:
  - sign of every loaded byte: `[3]i8`, `[5]i8` and `[7]i8` with -1, -128 and 127 next to negative canaries;
  - a `[3]i16` with -32768 and 32767 between `i16` and `i8` fields;
  - an `(i8,i8,i8)` tuple returned and destructured;
  - a 40-iteration loop that rebuilds and copies a `[3]i8` and a `[3]i16` while keeping ten live i64 accumulators. This puts
    register pressure on the partial-register RCX sequences at -O1.

  Result: 3/3 pass with the fixed compiler. The two native legs fail at HEAD.
- Probe (not committed): pass-through of a 3-byte struct `fn pass_on(t: T3) -> T3` twice, at O0 and O1, gives the same output as interp.
  `[3]u8 == [3]u8` is not supported by the type checker (AX_TYPE_OPERATOR), so I could not test it.

### Spec / scope
- No new diagnostics and no semantic choice: exact-width access is what SPEC-51's layout requires.
- No change to axiom0 (R7 is not affected). No shared tool or CMake file was edited.

### Findings
None that block.

### Notes (not FAIL)
- In the selfhost check, the 206 loop flags only `size == 8u8`. A MOV whose size field is 0 (the default 8-byte width) would not be caught.
  The fixed MI indices before it already pin the sequence, so this is a minor gap.
- I agree with the engineer's follow-up: `inspect --emit=mc` prints REX.W widths for sized MOVs. That is a printer issue and existed before.

## Files changed
- tests/run/agg_odd_size/qa_sizes_1_8.ax
- tests/run/agg_odd_size/qa_sizes_9_16.ax
- tests/run/agg_odd_size/qa_signed_pressure.ax

VERDICT: PASS round=0
