# T491 report — stage-1 axiomc1 access violation on parity programs

## Summary
Root cause found: an **axiom0 native-backend bug** (stack buffer overflow in the branch-fixup pass), not UB in
`compiler/`. axiom0 is frozen, so the fix needs an `AX0-FIX` task; this task is BLOCKED (case (b) of the task scope).

## Reproduction at HEAD (a8c458d1)
Snapshot `build-snap-T491` (HEAD + 0 changes), axiom0 built in the snapshot (clang, Release), stage 1 built with
`tools/bootstrap.py --stage 1` (`axiomc1.exe` sha256 prefix 51c28625f2b30edd).
- `axiomc1 inspect --emit=thir` segfaults (rc 139 / 0xC0000005) on `tests/run/parity/backend/const_table_str.ax`,
  `tests/run/parity/backend/qa_narrow_const_repeat_and_print_int_edges.ax` and `tests/run/comptime/scalar_const.ax`
  (the T164 follow-up 4 crash is the same bug). `--emit=resolved` and `--emit=hir` succeed.
- Minimal trigger in axiomc1: any `const` whose initializer is evaluated by the oracle through a binary/unary op,
  e.g. `const A: i32 = -42;` or `const A: i32 = 10 + 20;` (a literal or `const B: i32 = A;` is fine).

## Diagnosis (gdb + objdump evidence)
1. The crash is `ret` to a stack address (rip 0x43df7f8 = a stale local slot). Hardware watch/rwatch showed the
   `ret` belongs to a tiny function at .text+0x370 (`lnk_ptr_from_mut_*`) reached **by a jump, not a call**, from a
   frame whose rbp belongs to another function: execution jumped from the middle of a large function into an
   unrelated function body and later returned through garbage.
2. That large function is `exec_assign_binop` (`compiler/interp/interp.ax:2597`, the oracle's binary-op evaluator,
   ~129 KB of code). In both the PE image and `axiom0 build --emit=obj` of the bundle, 65 of its 1076 intra-function
   `jmp`/`jcc` have targets outside the function, at .text+0x12a..0x3a2, e.g. obj offset 0x80aa86:
   `e9 f1 58 7f ff  jmp 37c <ptr_from_mut_38796_38795_38794+0xc>`. No other function in axiomc has more than 900
   branches.
3. Cause in axiom0, `bootstrap/axiom0/src/driver/build_native/build.c:515-516`:
   ```c
   uint32_t bb_offsets[1024] = {0};
   struct { uint32_t fixup; uint32_t target; } fixups[1024];
   ```
   No bound check: a function with more than 1024 branch fixups (JMP/JCC/ASSERT) or more than 1024 machine blocks
   writes past the arrays. In `exec_assign_binop` (1076 fixups) the overflowing `(fixup, target)` pairs overwrite
   `bb_offsets[]` entries with block indices (≈0x37c..0x3a2), so the patched rel32 of those jumps points to
   section offset ≈ "block index" — exactly the bad targets observed. With other layouts the same overflow smashes
   axiom0's own stack (see repro below). Undefined behaviour in axiom0; axiomc2 is unaffected because axiomc's own
   backend has no such fixed limit.

## Minimal repro for the AX0-FIX task
A function with ~250 sequential `if`s (> 1024 fixups) built by axiom0:
```
// test: run
// exit: 0
fn many_branches(x: i64) -> i64 {
    let mut r: i64 = 0;
    if x == 0 { r = r + 1; }
    if x == 1 { r = r + 2; }
    ...                                  // k = 0 .. 249: if x == k { r = r + (k + 1); }
    r
}
fn main() -> i32 {
    let mut sum: i64 = 0;
    let mut i: i64 = 0;
    while i < 250 { sum = sum + many_branches(i); i = i + 1; }
    if sum != 31375 { return 1; }
    0
}
```
`axiom0 build` / `axiom0 run` of it: segfault in `ax_stage_build_native` (backtrace frames are the smashed
`(fixup,target)` pairs, e.g. 0x0001fac20001f993); with 150 ifs it builds and runs correctly. With 400 ifs the
build completes but the exe dies with an illegal instruction (wild jump). The generator used is a 20-line Python
script (`n` ifs, optionally grouped 100 per nested `if x >= g { ... }`); 600 grouped ifs reproduce too.

## Proposed fix (decision, for the architect)
- **AX0-FIX (required, root cause):** in `bootstrap/axiom0/src/driver/build_native/build.c` allocate `bb_offsets`
  with `mi_body->bb_count` entries and `fixups` as a growable array (or count JMP/JCC/ASSERT first), free them after
  patching; assert `target < bb_count`. Add the repro above (n ≈ 1500, grouped) as `tests/run/parity/backend/
  many_branch_fixups.ax` (run, interp + native) — it fails today, so it belongs to the AX0-FIX task, not here.
  Rebuilt stage 1 must then pass `selfhost/obj_link_driver/axiomc_e2e.test`; afterwards remove that id from
  `_workspaces/baseline-failures.txt` (this task's path).
- An interim workaround of splitting `exec_assign_binop` (e.g. move the 128-bit branch into its own function) in
  `compiler/interp/interp.ax` is possible but not chosen: it hides a silent miscompile that will recur for the next
  large function, and the file is outside this task's paths.
- Nothing in `compiler/` is wrong; the two parity programs stay in the parity set unchanged.

## Tests
None run beyond the diagnosis above (no code changed). Full suite left to the gate.

## Files changed
- _workspaces/reports/T491-report.md

STATUS: BLOCKED axiom0 miscompile: build_native/build.c fixed bb_offsets[1024]/fixups[1024] overflow (exec_assign_binop has 1076 branch fixups) — needs AX0-FIX in bootstrap/axiom0/src/driver/build_native/build.c
