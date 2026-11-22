# T498c QA report

## Round 0

Snapshot `build-snap-T498c` (HEAD ab771643 + T498c). The engineer's build was made at 01ab165, and HEAD has since moved:
`build/axiomc2.exe.inputs.json` listed `std/sys/windows/fiber.ax` (changed by T423b) as stale. I rebuilt in the snapshot
(`python tools/build_axiomc.py --out build --stage 3`, log `_workspaces/T498c_qa_axiomc.log`): STAGE3 OK, FIXED-POINT (O1) OK,
axiomc2 == axiomc3, sha256 `861fde146b774c2e...` (same as the engineer's), STAGE0-GUARD OK.

### Checks and evidence

1. **Change set** (`taskctl.py changes T498c`): 3 compiler files + 3 engineer tests + report. The only REFUSED line was
   the 4 QA tests I added (not in the engineer's list); they are listed under `## Files changed` below. No bundle is listed.
2. **Code review of the design** (`compiler/interp/value.ax`, `frame.ax`, `interp.ax`):
   - Every consumer of the buffer that `prepare_call_args_from_term` returns frees it with the size from `out_args_bytes`
     (main call path interp.ax ~4161/4173, concurrent pair ~4692/4712/4736, serial call ~4746/4774, sched path
     ~6087/6096/6109/6129/6149/6157/6170); the buffer is replaced on growth and the old one is freed inside
     `interp_arg_store`, so one `heap_free` still covers value slots and spill area. No leak, no double free found.
   - `frame_init` copies the spilled bytes into the callee's own local storage, so the callee's frame does not point
     into the argument buffer. The buffer is freed right after the call/push, and a callee that stores or returns its
     parameter is safe (tests `store`, `back`, `qa_fiber_big_capture`).
   - Descriptor offsets, not pointers, so the realloc on a second spill does not invalidate the first (tests `m3`, `m4`, `many`: up to 6 spills in one call).
   - `interp_arg_load` only reads the descriptor when the parameter's storage is more than one slot, and local storage
     is at least a slot (rounded to 16), so small parameters cannot be misread. Theoretical residual: a by-value aggregate
     larger than 256 bytes passed by a caller that builds the buffer without `interp_arg_store` (none today: thread entry,
     fiber, drop glue, `main` pass scalars) and whose bytes 16..24 equal the magic. Not a finding.
   - Intrinsic path (interp.ax ~2204, ~6118) reads only `vals[0]`; no intrinsic takes an aggregate above 256 bytes by value in std (`address_of`/`address_of_mut` take `val: T` but are special-cased; `replace`/`drop`/`forget` are ordinary generics and are covered by `qa_std_mem.ax`).
3. **Engineer's tests** (`run/interp_big_args`, 3 files): `axtest --no-cache` TOTAL 9 PASS 9 in the first run; all native legs compare exact stdout.
4. **Regression proof (HEAD)**: the HEAD-equivalent compiler
   `_workspaces/artifacts/compiler-cache/axiomc2_O1_b64ea0de4626c290.exe` (same interp sources as HEAD) run through
   `axtest --no-cache` on `run/interp_big_args`: TOTAL 21 PASS 14 FAIL 7. All 7 files FAIL in `[interp]`
   (array_args: byte 18, e.g. `256` instead of `257/300/1024/4096`; enum_closure; struct_self_return; my 4 tests; the
   fiber test CRASHES with status 3221226356, the old over-256-byte capture write), and all 14 native legs PASS.
   With the task's compiler: `TOTAL 21 PASS 21 FAIL 0`, WEAK-NATIVE 0.
5. **Native-evidence (4a)**: every test has an exact `// stdout:`, so native legs compare observable bytes. Mutation in the
   snapshot only (`sed -i '3s/rec 154/rec 155/' tests/run/interp_big_args/qa_matrix.ax`, then restored and diffed against
   the main tree): `[interp]`, `[native]` and `[native-O1]` all FAIL ("stdout differs at byte 91"). Restored; 21/21 PASS again.
   Interp vs native stdout also compared by hand for each new test (`run --interp` vs built exe): identical bytes.
6. **Adversarial tests added** (expected values computed independently with a Python script, not taken from the compiler):
   - `qa_matrix.ax`: 3 big args in one call, big/small in every order (`m1` big,small,big,small; `m2` small,big,small;
     `m3` big,big,small,big,small,small; `m4` small,big,small,big,small,big), distinct array contents with a position-weighted checksum
     (a swapped, shifted or truncated copy changes it); recursion 3 deep where each frame edits its own `[300]u8`/`[600]u8`
     parameters before recursing (frames must not alias); callee mutation not written through to the caller; a callee storing its
     copy in a struct that outlives the argument buffer; big temporaries as nested call arguments; function pointer;
     generic fn with a big type argument plus big concrete parameter; generic struct method with by-value `self` and a big argument;
     trait method with big by-value `self` and big argument (direct and through a generic `W: Weigh`); closure capturing
     two big values with scalars between them (capture offsets/alignment); values returned back through two calls.
   - `qa_extremes.ax`: 64 KiB and 128 KiB by-value arrays, `[4][300]u8`, tuple `([300]u8, [300]u8)`, closure with a big capture
     called through generic `Fn`/`FnMut`/`FnOnce` wrappers with a big argument, `FnMut` closure with a big argument and mutable capture,
     a `Drop` struct with a big field moved into the callee (drop runs once, in the callee, in order), `Option<[300]u8>` through a generic
     fn, one call with six spilled arguments (300/600/257/1024/1200/300 bytes + scalar).
   - `qa_std_mem.ax`: the `std.core.mem` generics `replace` (returns a big old value by value), `drop`, `forget` with big values.
     (Copied locally: a test cannot import `std.core.mem` without a std module bundle.)
   - `qa_fiber_big_capture.ax`: a std fiber (bundle std part copied verbatim from `tests/std/fiber/qa_fiber_values.ax`) whose closure
     captures a `[300]u8`, a scalar and a `[1024]u8`, yields a big value and returns a big value that was edited from a capture.
     This is the thread/fiber path: the entry point itself takes only a pointer, so the big captures reach the interpreter through
     the closure call. HEAD compiler crashes on it; the task's compiler passes in all three modes.
   - Not tested (not supported by the language subset at this stage): `dyn Trait` (SPEC-00 §self-host subset excludes it); real OS threads
     (`std.thread`) need the large std bundle; the fiber test covers the closure-entry path.
7. **Full task gate** (`python tools/taskgate.py --task T498c --compiler build/axiomc2.exe --build-dir build
   --exclude-requires axiom0-internal -j 2 --extra run/interp_big_args --json-out _workspaces/artifacts/taskgate-T498c.json`):
   exit 0, wall 502 s, `TOTAL 156 PASS 156 FAIL 0`. Log `_workspaces/T498c_qa_taskgate.log`.
   - own: 8 ids / 21 results, all PASS (the 7 `interp_big_args` files plus the engineer's directory entry).
   - affected: 42 ids / 109 results PASS. Derivation printed by the tool: `compiler/interp -> tests/run/{basic,intrinsics}` map,
     selfhost `interp`, `interp_opt`, `driver`, `obj_link_driver` (bundles embedding `compiler.interp.value`; their `bundles_current.test`
     and the changed bundle files), exact-dependency for the new tests. UNMATCHED none; UNRESOLVED none; MAP-NOTE none; DEFERRED none.
   - smoke: 31 ids / 50 results PASS (one test per top-level group, incl. `run/str/hello.ax` (Xin chào thế giới), `ui/typeck/type_unknown.ax`,
     `diff/002-arithmetic.ax`, `diff/001-return.ax`).
   - archcheck clean (232 files, 0 violations), BASELINE OK, failing ids: none. WEAK-NATIVE 13 in the whole run, 0 in the task's own/changed tests.
   - Cache line: CACHED 38, miss 14, uncacheable 22, mismatch none, rejected {}.
8. **Selfhost interp groups, no cache** (`python tools/axtest.py --no-cache --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 2
   --baseline _workspaces/baseline-failures.txt selfhost/interp selfhost/interp_opt`): `TOTAL 11 PASS 11 FAIL 0`, BASELINE OK, WEAK-NATIVE 0.
   Log `_workspaces/T498c_qa_suites.log`.
9. **Speed** (acceptance: no >10 % slowdown), `run --interp`, interleaved, HEAD-equivalent compiler vs task compiler, shared machine:
   - `selfhost/lex/qa_lex_all.ax`, 3 runs each: old 3.12/2.94/2.91 s, new 3.17/2.92/2.83 s.
   - `selfhost/parse/qa_parse_interp.ax`, 3 runs each (interleaved): old 21.34/21.13/20.11 s, new 20.77/19.96/20.10 s; stdout identical.
   No measurable slowdown (the inline fast path is unchanged).
10. **Spec / scope check**: change is in `compiler/interp` (Axiom sources) only; no `bootstrap/axiom0`, `spec/`, `docs/`, no diag codes, no
    `BOOTSTRAP-SHORTCUT`. Mode check: all new run tests use the default modes (interp, native, native-O1) except the fiber test, which declares
    `modes: interp native` like every other fiber bundle in `tests/std/fiber` (no `native-after` involved). Shared-file check: no edit of
    `tools/axtest.py`, CMake, CI scripts, `diag/codes.def` or `driver/pipeline.c`.
11. **Cache hygiene**: the new tests read no files outside their own text (the fiber test embeds the std sources it needs); none needs `nocache:`.

### Findings

None blocking. No FAIL finding.

Notes (not FAILs, outside this task):
- N1. `tests/run/array_copy/large_and_edge.ax` (T498) keeps a comment saying large arrays are read through a view because of the 256-byte oracle
  limit; the limit is gone (the engineer already listed this as a follow-up).
- N2. The report lists the timing of `qa_typeck_all` with an initial +17.7 % sample later re-measured at -1.9 %; I confirmed no slowdown on two other bundles above.

### Follow-ups (for the architect)

- FU-QA-T498c-1 (pre-existing, not caused by T498c): a by-value `[262144]u8` argument crashes the NATIVE executable at HEAD and with
  the task compiler (exit 127 before any output; `fn huge(a: [262144]u8, t: u32)` called once from `main`, 3 copies of 256 KiB on a stack that is
  probably the default PE reserve). The interp handles it. `qa_extremes.ax` stops at 128 KiB so that the native legs pass. Repro:
  `build/axiomc2.exe build h.ax` with a 262144-byte by-value argument, run the exe.
- FU-QA-T498c-2 (pre-existing): the `swap<T>` generic of `std/core/mem.ax` exchanges only the first element when `T` is an array. Repro:
  copy `swap` into a test, `let mut p: [4]u32 = [1,2,3,4]; let mut q: [4]u32 = [10,20,30,40]; swap(mut_view(p), mut_view(q))` prints
  `p = [10,2,3,4]`... (p[0]=10, p[3]=4, q[0]=1, q[3]=40) in the HEAD-equivalent interp, the task's interp and native alike. `ptr_copy_nonoverlapping<T>(.., 1)`
  with an array `T` copies one element instead of `size_of<T>()` bytes (or the `[1]T` temporary is built from the wrong type). Not covered by any test today.

## Files changed
- tests/run/interp_big_args/qa_matrix.ax
- tests/run/interp_big_args/qa_extremes.ax
- tests/run/interp_big_args/qa_std_mem.ax
- tests/run/interp_big_args/qa_fiber_big_capture.ax

VERDICT: PASS round=0

## Round 0 (rebase)

HEAD moved to 3b705825 (T496a: `compiler/mir/builder.ax`, `compiler/hir/lower.ax`); snapshot `build-snap-T498c` refreshed (HEAD 3b70582 + T498c).

1. Rebuild in the snapshot: `python tools/build_axiomc.py --out build --stage 3` (log `_workspaces/T498c_qa_axiomc_rb.log`): STAGE3 OK,
   `FIXED-POINT (O1) OK` axiomc2 == axiomc3 sha256 `b5213f118f0f6275...`, STAGE0-GUARD OK, BUILD-AXIOMC OK.
2. `taskgate` in the refreshed snapshot (`--task T498c --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`,
   log `_workspaces/T498c_qa_taskgate_rb.log`, no cache hits): `TOTAL 156 PASS 155 FAIL 1`. archcheck clean (232 files), UNMATCHED none, WEAK-NATIVE 0 in the
   task's own/changed tests. Affected set unchanged (map `compiler/interp` -> `run/basic`, `run/intrinsics`, selfhost `interp`, `interp_opt`, `driver`,
   `obj_link_driver` bundles and their `bundles_current.test`).
3. The single failure was **my own test** `run/interp_big_args/qa_extremes.ax [native-O1]`: `TIMEOUT ... axiom0 build did not finish within 10s`
   under the load of the gate (`-j 2` and other agents). Re-run alone: `build` takes 5.4 s and `build -O1` 7.2 s, and with `--timeout-scale 6` the
   test passes 3 of 3. This is a QA test defect (too close to the default 10 s limit because of the 64/128 KiB array literals), not a task defect. I added
   `// timeout: 60` to `qa_extremes.ax` (main tree, refreshed into the snapshot, same convention as the fiber bundles) and re-ran:
   `axtest --no-cache run/interp_big_args` -> `TOTAL 21 PASS 21 FAIL 0`, WEAK-NATIVE 0.
4. Selfhost groups, no cache, after the rebase: `axtest --no-cache --exclude-requires axiom0-internal -j 2 --baseline _workspaces/baseline-failures.txt
   selfhost/interp selfhost/interp_opt selfhost/obj_link_driver` -> `TOTAL 21 PASS 21 FAIL 0`, WEAK-NATIVE 0.
5. All other 155 gate results (own 20 + affected 108 + smoke 50, deduplicated) PASS, including the smoke picks and the
   Xin chào thế giới test. No new failing id outside `_workspaces/baseline-failures.txt` remains.

### Files changed
- tests/run/interp_big_args/qa_extremes.ax

VERDICT: PASS round=0 (rebase)
