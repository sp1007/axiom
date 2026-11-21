# T453a QA

## Round 0

### Change set
`taskctl.py changes T453a`: stages the report, `compiler/lir/builder.ax` and the three engineer tests under `tests/run/print_int_unsigned/`. No REFUSED line. Bundles are not listed.
Diff reviewed (`compiler/lir/builder.ax`, `TY_BUILTIN_PRINT_INT` lowering). When the operand is not signed and its type kind is `TY_U64` or `TY_USIZE`, it calls `lower_print_int128_call(..., false, t_u128)`, which zero-extends the operand to u128 and uses the 128-bit unsigned decimal path. Signed types and u8/u16/u32 still use `__ax_host_print_int`. `compiler/link/import.ax` is untouched, and no new hand-written machine code is added. No spec or diagnostic changes, no `BOOTSTRAP-SHORTCUT`, and no `native-after: T453a` left in `tests/` (grep is empty).

### Evidence
- **Build:** the snapshot compiler `build-snap-T453a/build/axiomc2.exe` (Stage-0 clang Release, engineer's fixed-point build) was used. The snapshot was refreshed after I added tests: `bundles regenerated: 36 generator(s), 60 file(s)`.
- **Engineer tests plus my adversarial tests**
  - Command: `axtest --compiler build/axiomc2.exe --filter print_int_unsigned`.
  - Result: 15 results (5 files x interp, native, native-O1), all PASS, WEAK-NATIVE 0.
  - Each test has an exact `// stdout:` list and an exit value, so the native legs compare observable bytes.
- **Values covered:** 0, 2^63-1, 2^63, 2^63+1, 2^64-2 and 2^64-1 for u64 and usize.
  - Runtime-computed values: `wrapping_sub`, shifts, `as` casts from -1i64, struct fields, function returns, loop-carried values, branch-selected values, wide division, multiplication and modulo.
  - The new tests are run at -O0 and -O1 (native and native-O1). The -O1 results include constant-folded operands.
- **Neighbours:**
  - Unchanged signed values: i64 MIN/MAX, -1i64, and i8/i16/i32 MIN.
  - Unchanged narrow unsigned maxima: u8/u16/u32.
- **Alias and generic types:** `qa_alias_generic.ax` covers the alias types `Word = u64` and `Size = usize`, a generic identity `ident<T>`, an array element, and a `mut_view<u64>` write.
- **Pre-fix compiler** (`_workspaces/artifacts/compiler-cache/axiomc2_O1_27c02f54...exe`, `--no-cache`): `computed.ax`, `u64_edges.ax`, `qa_alias_generic.ax` and `qa_branch_arith.ax` fail `[native]` and `[native-O1]` with "interp/native disagree". `narrow_and_signed.ax` passes, so the behaviour for unaffected types is unchanged. Result: TOTAL 15 PASS 7 FAIL 8.
- **Mutation proof (step 4a):** in the snapshot only, I changed line 7 of `u64_edges.ax` to `// stdout: 18446744073709551616\n`. Native and native-O1 FAILED (`stdout differs at byte 81`). I restored the file from the main tree, and the snapshot was refreshed afterwards.
  - Command: `sed -i '7s/615/616/' tests/run/print_int_unsigned/u64_edges.ax`, then `axtest --no-cache --filter print_int_unsigned/u64_edges`.
- **Taskgate:** command: `python tools/taskgate.py --task T453a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --extra run/print_int_unsigned --json-out _workspaces/artifacts/taskgate-T453a.json`. Log: `_workspaces/T453a_qa_taskgate.log`. Exit 0.
  - Result: `TOTAL 206 PASS 195 FAIL 0 SKIP 11 XFAIL 0`. Failing ids: none. Baseline OK.
  - archcheck clean (232 files, 0 violations).
  - WEAK-NATIVE: 3 in the run, 0 in the task's own or changed tests.
  - Cache: CACHED 47, miss 11, uncacheable 88, mismatch none.
  - UNMATCHED: none. No UNRESOLVED or DEFERRED lists printed.
  - The affected set includes the `compiler/lir` map targets (`tests/mc`, `tests/run/native`, `tests/selfhost/lir`) and the selfhost abi, backend, driver, lir and obj_link_driver groups plus their `bundles_current` tests. All pass.
  - Smoke picks include `run/str/hello.ax` (Xin chao), the `ui/typeck/type_unknown.ax` compile-fail test, `diff/002-arithmetic.ax`, and one test per top-level group.
- Not run again by me: `run/numeric` and `conformance/p12`. The engineer ran them (832 and 472 PASS), and the taskgate affected set does not select them from this change.

### Findings
None.

### Notes
- Pointer-typed `print_int` operands are not routed. Typeck does not accept them, so there is nothing to verify.
- My first drafts of `qa_alias_generic.ax` and `qa_branch_arith.ax` hit unrelated limitations, which were test mistakes and not compiler findings. Indexing through `view<[3]u64>` gives AX_TYPE_CANNOT_INDEX, and one expression overflowed u64. I fixed the tests.

### Follow-ups
None.

## Files changed
- tests/run/print_int_unsigned/qa_alias_generic.ax
- tests/run/print_int_unsigned/qa_branch_arith.ax

VERDICT: PASS round=0
