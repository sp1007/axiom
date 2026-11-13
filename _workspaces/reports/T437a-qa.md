# T437a — QA gate

## Round 0

Scope: per-task gate scope for a tools-only task (axiom-qa.md): the task's own tool self-tests, the affected set
(tool self-test dirs), the smoke set and archcheck, plus an adversarial soundness audit of the cache and of
`--affected`. All runs inside `build-snap-T437a` (HEAD bed3d91 + this change set), `-j 2` at most, one run at a time.
Compiler: `build-snap-T437a/build/axiomc2.exe` (read-only copy, as in the report). Scratch caches under the session
scratchpad (`--cache-dir`), so the shared cache was not changed by the adversarial runs.

### Checks performed (evidence)
- `taskctl.py changes T437a`: no REFUSED line; 11 files staged (+ my test file below). Snapshot byte-identical to
  the main tree for all 10 tool files.
- `python tools/tests/axtest/run_selftests.py` -> `SELFTEST 110 tests, 0 failures` (107.6 s);
  `python tools/tests/taskgate/run_selftests.py` -> `SELFTEST 23 tests, 0 failures` (44.5 s);
  `python tools/archcheck.py` -> 229 files, 0 violations; `python tools/axtest.py --smoke --check` -> `SMOKE-CHECK OK`
  (worst case 20 s at -j 2).
- `python tools/taskgate.py --task T437a --compiler build/axiomc2.exe --build-dir build --exclude-requires
  axiom0-internal -j 2 --json-out ...` (my run): wall 197.0 s (implementer: 188.6 s); smoke seed 794409199, 31 ids /
  48 results, 46 PASS, failing `hir/basic.ax resolve/simple.ax` (both in the baseline, `BASELINE OK`); cache: 12 hits,
  all 12 re-run by the S6 sample (seed 749651345), no mismatch, producer `snapshot`; archcheck clean; WEAK-NATIVE 3 in
  the run (pre-existing smoke ids), 0 in own/changed tests. **Exit 1**, reason `tool self-tests failed:
  tools/tests/gatecheck` — selected by the tools rule because `test_gatecheck.py` names `tools/axtest.py`.
  The failing test `test_check_without_command_blocks` fails **identically at HEAD** (`git archive bed3d915 tools`
  into a temp dir, `python tools/tests/gatecheck/run_selftests.py` -> same `TypeError ... NoneType` assertion,
  33 tests / 1 failure). Pre-existing, not caused by this task (report to the architect, see Follow-ups).
- Smoke list: pools for all 28 top-level groups; `always:` = `run/str/hello.ax` (Xin chào thế giới, exact
  `stdout:`), `ui/typeck/type_unknown.ax` (compile-fail), `diff/002-arithmetic.ax` (native-vs-interp diff);
  archcheck is run by taskgate. `--smoke` inside taskgate took 8.2 s of axtest wall time at -j 2 (bound 20 min).

### Cache soundness audit (ADR-0041 §4)
Real compiler, test `run/str/hello.ax` unless named; command prefix
`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --cache-dir <scratch>`:
- MISS as required: std file changed (comment appended to `std/core/prelude.ax`), compiler binary changed (copy +1
  byte), `--timeout-scale 2`, env `AXIOM_X=1`; HIT again after restoring prelude.ax. Test bytes / expectation files
  / runner / mode / deleted dep / `cmd:` without inputs: covered by the self-tests and confirmed by reading
  `pre_material` + `superset_deps` (test bytes, golden + `stdout-file:` hashes, runner `tools/axtest*.py` hashes,
  labels, `file?` = `absent` digest for deleted files).
- `driver/version.test` (`cmd:`) and `std/thread/spawn_join_basic.ax` -> `UNCACHEABLE 2` on two consecutive runs.
- Corruption: truncated entries -> `CACHE-CORRUPT-DELETED 2`, fresh run; field-tampered entry (record_sha256 not
  fixed) -> deleted, fresh run.
- S5 (`--gate`): entry rewritten to `origin: local` with a valid record hash -> `CACHE-REJECTED origin-local=1`;
  base `0000…` -> `CACHE-REJECTED base-not-ancestor=1`; base `HEAD~5` -> accepted (HIT, sampled). Script:
  `scratchpad/qa437/setprod.py <cache> <field> <value>`.
- S6: poisoned hit (see F1) in `--gate` with 1 hit -> `VERIFY-SAMPLE n=1 of 1`, `CACHE-MISMATCH modules/hello`, real
  FAIL reported. Above 20 hits only max(20, 5 %) are sampled, so a single poisoned entry survives a gate with high
  probability (ADR design); see recommendation R1.
- Concurrency: two axtest processes (`-j 1` each) on one fresh cache over `lex/` at the same time: 15 entries,
  record hashes and file names all valid, no `.tmp-*` leftovers; a third run -> all cacheable ids HIT.

### --affected audit
- `48bac852` (test-only, 16 files): 14 ids = every test of the changed directory (complete).
- `bda2296a` (std): 90 ids; an independent transitive grep of the changed module paths over `std/` and `tests/`
  (`scratchpad/qa437/indep.py`) finds 0 further tests.
- `fa86bbfc` (compiler): 755 ids, 0 unmatched (same as the report).
- `e969c207` (compiler + selfhost generator `tests/selfhost/drop/gen_drop_tests.py`): 533 ids; the generator's
  directory is selected. `tests/selfhost/bundle_common.py` -> all 195 selfhost ids (sound).
- tools-only (`tools/perf.py tools/gen_large.py`): `UNMATCHED` printed for both (no user test exists).
- `compiler/mir/builder.ax` alone: 153 ids + 38 `DEFERRED` lines printed (bundles outside the module's own map rows).
- Narrowing decisions: D2 (comments/strings ignored), D3 (other bundles DEFERRED, printed), D4, D5 (WEAK-NATIVE in
  own/changed tests only) are acceptable given the periodic full run and that DEFERRED/UNMATCHED are printed into
  the QA file. D1 as implemented is not (F4).

### Findings
- **F1 (FAIL, false cache HIT).** `tools/axtest_cache.py:157-160` (`Hasher.tree`) skips dot-files, dot-directories
  and `__pycache__`, but the compiler loads every `*.ax` of a project directory including those
  (`compiler/driver/opts.ax` `scan_package_dir_recursive`). Repro (in `build-snap-T437a`):
  `A="python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --cache-dir <empty dir>"`;
  `$A modules/hello` (PASS, stored); `printf 'fn broken( {\n' > tests/modules/hello/src/.evil.ax`; `$A modules/hello`
  -> `CACHED 3 HITS 1`, `TOTAL 3 PASS 3`; `$A --no-cache modules/hello` -> `TOTAL 3 PASS 0 FAIL 3`. Same for
  `src/.hidden/x.ax` and `src/__pycache__/x.ax` (compiler exits 1). Expected: the superset digest covers every file
  the compiler may read (hash all files; at most skip `.git`). Same skip applies to the `test_bytes` tree of a
  project test (`pre_material`).
- **F2 (FAIL).** `tools/affected_map.txt:24` names `tests/run/int128_interp`, a directory that exists only untracked
  in the main tree (another task's in-progress work), not at HEAD or in this change set. In the snapshot:
  `python tools/axtest_affected.py --check-map` -> `MAP-CHECK FAILED (1)`, and
  `python tools/axtest.py --compiler build/axiomc2.exe --affected compiler/interp/interp.ax --list` ->
  `axtest: --affected: tools/affected_map.txt is invalid` (exit 2). Every gate whose change set touches `compiler/`
  would be unable to run until that other task lands. Expected: targets tracked at HEAD only.
- **F3 (FAIL, S4).** ADR-0041 S4 forbids caching tests that use "OS thread/timer bindings"; `NONDET_SOURCE_RE`
  (`tools/axtest_cache.py:59`) only knows `std.{thread,sync,async,time}`/`async`/`await`/`spawn`. Repro:
  `$A run/host/fs/clock.ax run/ffi/tick_count.ax` twice -> second run `CACHED 5 HITS 2` (clock via
  `std.core.host.monotonic_ns`, FFI `GetTickCount64`). 15 non-selfhost tests use a clock/env binding without being
  flagged (`scratchpad/qa437/clk.py`), e.g. `tests/std/fs/qa_time_clock.ax`, `tests/run/ffi/repr_c_struct.ax`
  (`GetSystemTime`). Expected: those bindings mark the test uncacheable.
- **F4 (FAIL, unsound selection without DEFERRED).** `tools/axtest_affected.py:156-176` (`public_names`): a change
  inside an `impl` block gets git's hunk header `impl<T> Atomic<T> {`, which is not a `pub` line, so no name is
  derived; only tests that spell the module path are selected. Repro: `python -I scratchpad/qa437/names.py
  <out>` in the snapshot -> `hunk headers: ['@@ -42,7 +42,7 @@ impl<T> Atomic<T> {']`, `derived public names: set()`.
  For the implicit prelude (`std/core/prelude.ax`, loaded by every compilation) 53 non-selfhost tests use `Atomic<`
  without naming `std.core.prelude`; none is selected and nothing is printed as DEFERRED. The D1 rationale
  ("methods are reached through their type") requires the type name to be derived from `impl [<..>] [Trait for]
  Type` headers/lines; a change in a private top-level helper (`fn helper` header) has the same gap — fall back to
  every public top-level name of the file (or the module's users) when a hunk yields no name.

### Tests added
`tools/tests/axtest/test_cache_qa.py` (9 tests, one per finding aspect: tree digest sees dot-file / dot-dir /
`__pycache__`; map targets tracked by git; monotonic_ns / GetTickCount64 / QueryPerformanceCounter uncacheable;
impl and trait-impl hunk headers derive the type name). All 9 FAIL now (`python tools/tests/axtest/run_selftests.py
test_cache_qa` -> `SELFTEST 9 tests, 9 failures`); they are the regression tests for the fix round. Snapshot
refreshed after adding it.

### Follow-ups / recommendations (not verdict-relevant)
- R1: the periodic full run should run with `--no-cache` (or at least verify every hit) so a poisoned entry that
  escaped the 5 % sample cannot persist; add to the "Harness follow-up" text for axiom-qa.md.
- R2: `tools/tests/gatecheck` `test_check_without_command_blocks` fails at HEAD (pre-existing); taskgate exits 1 for
  any task that touches `tools/axtest.py` until it is fixed — needs a fix task (architect), or a tool-self-test
  baseline in taskgate.
- R3: S5 "origin snapshot" is decided by directory names (`build-snap-*`), not by `tools/build_axiomc.py`
  provenance; sound because the compiler hash is in the key, but the report should say so.
- `taskctl changes` prints `listed but neither present nor tracked (ignored): workspaces/reports/T437a-report.md`
  (underscore dropped when parsing the report's list) — harmless, the file is staged.
- No processes left running by this gate (checked; remaining axiomc2/python processes belong to other tasks).

## Files changed
- tools/tests/axtest/test_cache_qa.py
- _workspaces/reports/T437a-qa.md

VERDICT: FAIL round=0

## Round 1

Snapshot `build-snap-T437a` (HEAD bed3d91 + 13 files at the start of the round; refreshed at the end to HEAD
ef323c3 + 13 files after my test update). `taskctl changes`: no REFUSED line. Compiler as in round 0. Scratch cache
dirs under `scratchpad/qa437/`. One run at a time, `-j 2` max (the thread-id probe below used `-j 1`).

### Round-0 findings re-checked (own repros)
- `tools/tests/axtest/test_cache_qa.py`: unchanged by the implementer (byte-identical to my round-0 file); the 9
  round-0 tests pass in the snapshot.
- **F1 fixed.** `$A modules/hello` stored; with `src/.evil.ax` -> `CACHED 0 ... MISS 1`, `TOTAL 3 PASS 0 FAIL 3`; file
  removed -> `CACHED 3 HITS 1` again.
- **F2 fixed.** `python tools/axtest_affected.py --check-map` -> `MAP-CHECK OK`; `axtest.py --affected
  compiler/interp/interp.ax --list` -> exit 0, `AFFECTED TOTAL 31 ... 13 deferred`.
- **F3 fixed for clock/env.** `$A run/host/fs/clock.ax run/ffi/tick_count.ax` twice -> `UNCACHEABLE 2`, `CACHED 0`.
- **F4 fixed for the round-0 case.** `impl<T> Atomic<T>` hunk header -> `Atomic`; private-helper fallback works
  (7a8ef713, private `ax_spawn_trampoline` in std/thread -> file-name fallback, 743 ids).
- **gatecheck at HEAD**: taskgate reports `tools/tests/gatecheck` as `KNOWN`, and the gate still exits 0.

### New checks
- **Hit rate (the digest now covers every file).** `$A lir/ mir/build ui/typeck run/basic` twice with a fresh cache:
  run 1 `MISS 40 UNCACHEABLE 63 STORED 40`, run 2 `CACHED 70 HITS 40 MISS 0 UNCACHEABLE 63`. That is 100 % of the
  cacheable ids, and no spurious misses from the wider digest. Wall time was ~22 min both times, though: 63 of 103
  ids are uncacheable (mostly `cmd:` manifests) and they dominate. That is an efficiency note for T437b
  (`cache-inputs:` on manifests), not a soundness problem.
- **KNOWN-vs-NEW.** I added a deliberately failing `tools/tests/taskgate/test_zz_qa_broken.py` in the snapshot
  only (file in `scratchpad/qa437/`), ran `taskgate.py --task T437a ...`, then removed the file. Result: `rc=1`,
  `tools/tests/taskgate FAIL (27 tests, 1 failures)`, gatecheck still `KNOWN`,
  `TASKGATE T437a exit=1 (tool self-tests failed: tools/tests/taskgate)`. A NEW failure still fails the gate.
  Code review: when a run fails but no FAIL/ERROR line can be parsed (crash, syntax error), `failing` is empty and
  the state stays FAIL, so the gate exits 1 (sound).
- **Clean taskgate run (my run):** `python tools/taskgate.py --task T437a --compiler build/axiomc2.exe --build-dir
  build --exclude-requires axiom0-internal -j 2 --json-out ...`:
  - wall time 227.2 s (axtest 25.8 s), smoke seed 1215543593, `TOTAL 51 PASS 49 FAIL 2`;
  - failing `hir/basic.ax resolve/R01_basic.ax`, both on the baseline (`BASELINE OK`);
  - cache: 19 hits, all 19 re-run by the S6 sample (seed 1210542409), no mismatch;
  - tool self-tests: axtest PASS (121), taskgate PASS (26), gatecheck KNOWN;
  - archcheck clean; WEAK-NATIVE 0 in own/changed tests; `TASKGATE T437a exit=0`.
  This matches the implementer's 218 s. The smoke part fits easily within the 20-minute bound.
- **More past commits:**
  - b433999e (new pub fns in std/future/mod.ax): 273 ids.
  - e969c207: 524 ids.
  - 7a8ef713: 743 ids.
  - 0 unresolved and 0 unmatched in all three, and the selection rules look plausible.

### Findings
- **F5 (FAIL, false cache HIT; S4 incomplete for OS *thread* bindings).** The new never-cache class only covers
  names about time, clock, env, random or pid. These bindings, all declared in `std/sys/windows/thread.ax`, are not
  covered: `CreateThread`, `GetCurrentThreadId`, `Sleep`, `SwitchToThread`, `WaitForSingleObject`, `WaitOnAddress`,
  `WakeByAddress*`. `std/sys/...` is also not one of the `NONDET_STD_DIRS`. ADR-0041 S4 names "OS thread/timer
  bindings". Repro: a test `tests/run/qa_tmp/tid.ax` (snapshot only, removed afterwards; content: `extern "system"
  { fn GetCurrentThreadId() -> u32; }`, prints `even`/`odd` by `(tid / 4) % 2`, `// stdout: even\n`, `modes:
  native`), run 8 times with `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build -j 1
  --cache-dir <empty> run/qa_tmp/`:
  - fresh runs: `FAIL 2`, `PASS 1 FAIL 1`, `FAIL 2`, `PASS 2` (then stored);
  - runs 5-8: `CACHED 2 HITS 1`, `PASS 2` each time.
  The flaky outcome is hidden by the cache. Probe: `StdIndex('std').nondet_reason(...)` returns None for `extern`
  `GetCurrentThreadId`, `extern CreateThread`, and `use std.sys.windows.thread.Sleep`. No checked-in test is
  affected today (every current thread test is flagged through `spawn`/`std.thread`), but the class is unsound as
  specified.
- **F6 (FAIL, unsound selection with no UNRESOLVED/DEFERRED output).** `derive_names` (`tools/axtest_affected.py`
  around lines 175-226) reads only the `+`/`-` lines and git's hunk header. When the changed line is within the first
  3 lines of an item's body, git's hunk starts above the item's declaration. The header then names the *previous*
  item, and the item's own declaration is only a context (` `) line. The result is a non-empty but wrong name set,
  so the fallback never fires.
  - Repro (in the snapshot): `python -I scratchpad/qa437/names2.py std/core/prelude.ax "^pub fn is_lock_free"
    is_lock_free <tmp>` -> hunk `@@ -99,7 +99,7 @@ pub fn compiler_fence(...)`, names `['compiler_fence']`,
    `MISSING is_lock_free`.
  - Impact: 4 conformance tests call `is_lock_free` without naming `std.core.prelude` and without using
    `compiler_fence`, e.g. `conformance/p11/e11_2_atomics/litmus_rmw_counter_wrapping_and_spinlock.ax` and
    `qa_signed_cas_const_ptr_and_sb_relaxed.ax`. They would not be selected, and nothing is printed.
  - The same applies to a change in the first lines of an `impl ... for T` body.
  - Expected: take the enclosing item from the file text by the changed line's number (scan backwards to the
    nearest column-0 declaration), or also parse the hunk's context lines.

### Tests added (round 1)
I added 5 tests to `tools/tests/axtest/test_cache_qa.py`, the 9 round-0 tests unchanged:
- `ThreadBindingsNeverCached`: FFI `GetCurrentThreadId`, FFI `CreateThread`, `use std.sys.windows.thread.Sleep`.
- `ContextLineDeclarationNamed`: a `pub fn` whose declaration is a context line, and an `impl Future for Sleep`
  whose declaration is a context line.

In the refreshed snapshot, `python tools/tests/axtest/run_selftests.py test_cache_qa` -> `SELFTEST 14 tests,
5 failures` (the 5 new ones; they are the regression tests for round 2).

### Notes
- HEAD moved to ef323c3 during the round (another task accepted). The snapshot refresh rebased onto it with no
  REFUSED line.
- No processes of this gate are left running. The two remaining axiomc2 processes belong to the main tree and to
  build-snap-T430.

## Files changed
- tools/tests/axtest/test_cache_qa.py
- _workspaces/reports/T437a-qa.md

VERDICT: FAIL round=1

## Round 2

Snapshot `build-snap-T437a` (HEAD ef323c3 + this change set; all tool files byte-identical to the main tree).
`taskctl changes T437a`: no REFUSED line. Compiler: as in round 0. Scratch caches and a scratch clone live under
`scratchpad/qa437/`. Runs were `-j 2` at most (the native flakiness probes used `-j 1`), one at a time.

### Earlier findings re-checked
- `tools/tests/axtest/test_cache_qa.py` is unmodified (134 lines, my round-1 text) and passes 14/14:
  `python tools/tests/axtest/run_selftests.py test_cache_qa` -> `SELFTEST 14 tests, 0 failures`.
- **F5:** `tests/run/qa_tmp/tid.ax` (FFI `GetCurrentThreadId`, even/odd output, snapshot only, removed afterwards).
  4 runs with a fresh cache (`... -j 1 --cache-dir <fresh> run/qa_tmp/`): every run printed `UNCACHEABLE 1
  STORED 0`, and the flaky outcome stayed visible (`PASS 1 FAIL 1` / `PASS 2`). Fixed.
- **F6:** `python -I scratchpad/qa437/names2.py std/core/prelude.ax "^pub fn is_lock_free" is_lock_free <tmp>`.
  git's header still names `compiler_fence`, but the derived names now include `is_lock_free` (and the Atomic*
  types). Fixed.

### F5 deny-by-default classifier: attacks
- **Positive-listed leaves and the cache key.**
  - Arguments, stdin and `env:` come from directives, which are part of the test bytes.
  - `AXIOM*`/`AX_*` variables are in the key. Any other environment read goes through
    `GetEnvironmentVariableW`/`env_get`, which are not on the list, so the test is uncacheable.
  - `GetProcAddress`, `VirtualProtect`, `GetModuleFileNameW` and `exe_path` are not on the list either: uncacheable.
  - Console input (`ReadConsoleW`) is not on the list.
  - A binding reached through an alias, a re-export, a function value or `GetProcAddress` is classified by the leaf
    it ends at. The implementer's self-tests cover alias and re-export, and I checked the leaf list:
    `StdIndex('std').binding_names()` -> 34 leaves, including `CreateThread`, `Sleep`, `WaitOnAddress` and
    `GetModuleHandleA`.
- **G1 (cached false HIT, accepted limitation).** File I/O on the positive list (`open`, `read`, `CreateFileW`,
  `FindFirstFileW`, ...) can read paths outside the dependency set, and the key does not cover such files.
  - Repro: `tests/run/qa_tmp/ext_read.ax` (snapshot only, removed afterwards; `modes: interp`; it reads
    `qa_r2_probe.txt` at the repository root and expects `A`).
  - With file content `A`: `STORED 1`, PASS.
  - Content changed to `B`: `CACHED 1 HITS 1`, `TOTAL 1 PASS 1`.
  - With `--no-cache`: `PASS 0 FAIL 1`.
  - Why accepted:
    - No checked-in test reads a repository file outside its own directory at run time. I grepped path literals and
      `open`/`dir_open`/`FindFirstFileW` users: they only touch files they create themselves, such as
      `test_host_dir`, `test_file_io.tmp` and `src/main.ax` in temp dirs.
    - The input is not a compiler/std/test change, so the cache cannot hide a regression from a task's change set.
    - The periodic full run with `--no-cache` (harness follow-up R1) re-runs it fresh.
  - Recommendation for the architect, in axiom-testing: a test that reads files outside its own directory must
    declare `nocache:` or list them in `cache-inputs:`.
- **G2 (latent, accepted limitation).** In superset mode, the nondet traversal only follows textual `std.a.b`
  references, not the implicitly loaded prelude files (`std/core/{prelude,option,result,host}.ax`).
  - Today none of them calls a nondeterministic leaf (`file_calls_binding` -> None for all 4), so no test is affected.
  - Synthetic check: appending `pub fn qa_now() -> u64 { monotonic_ns() }` to `std/core/prelude.ax` (snapshot only,
    restored) makes `file_calls_binding('std/core/prelude.ax')` return `monotonic_ns`. A test that calls `qa_now()`
    with no `std.` text is still classified cacheable (`nondet_reason` -> None).
  - Why accepted:
    - A prelude change changes the std digest, so no regression can be hidden.
    - Exact mode (T437b, `exact_deps_nondet` over the loaded files) closes the gap.
  - Recommendation: seed the traversal with the implicit prelude files.
- **G3 (accepted limitation, outside ADR S4).** A test whose output depends on ASLR, such as a heap address parity
  through positive-listed `HeapAlloc`, is cacheable and flaky: `tests/run/qa_tmp/addr.ax` (removed) failed in
  several of 6 fresh runs.
  - Why accepted: S4 is about scheduling and timing. Such a test is broken on its own, and any compiler, std or test
    change invalidates its key, so the cache cannot hide a regression with it.
- `cmd:` tests stay uncacheable without `cache-inputs:` (`driver/*.test` -> UNCACHEABLE). An exact dependency list
  is only used when the compiler writes `--dep-file` (the probe stays `superset` for the current binary).

### F6 enclosing-declaration scanner: attacks
- **Scratch clone.** I made `git clone --shared --no-checkout`, sparse checkout of std/tests/tools/compiler at
  bed3d915, plus a commit with this task's tools. The main repository's refs are untouched. Driver:
  `scratchpad/qa437/synth.py <case>` makes a synthetic commit, runs `axtest.py --affected HEAD~1..HEAD --list`, and
  compares with an independent word grep of the expected names plus the module path over all non-selfhost tests.
  Results (ids selected / independent-grep files not covered / UNRESOLVED):
  - `string_brace`: body line of `begin_install_transaction`, after functions whose string literals hold unbalanced
    `{`/`}` -> 17 / 0 / 0.
  - `attribute_line`: new `@inline` above `format_update_journal` -> 17 / 0 / 0.
  - `where_clause`: the `where` part of `Arc.val` -> 414 / 1 / 0.
  - `use_line`: a new `use` line in `std/sync/arc.ax` (file-wide) -> 414 / 1 / 0.
  - `pure_deletion`: the first statement of `Mutex.lock` deleted (`@@ -43 +42,0`) -> 61 / 3 / 0.
  - `crlf_file`: `std/sync/mutex.ax` converted to CRLF in a base commit, then a body change -> 61 / 3 / 0.
  - `closure_in_body`: a change inside a closure in `Mutex.new` -> 61 / 3 / 0.
  - `char_brace_and_nested_mod`: a fn with `'{'` and `"}}"`, then a change inside `pub mod qa_inner { pub fn ... }`
    -> 58 / 0 / 0.
  - `trait_default_body` (lands in an `impl Iterator for Range<i32>` method) -> 357 / 0 / 0.

  Every "not covered" file mentions the name only in comments. I checked by hand:
  `layout_inspector_container_contracts_and_std_effects.ax`, `ui_read_write_and_write_write_races.ax` and
  `qa_arc_and_boundary_races.ax` have `Arc`/`Mutex` only in `//` lines. That is consistent with D2.
- **Scanner edge cases** (`scratchpad/qa437/decls.py`; a body change of the item that follows each snippet).
  Snippets: an escaped backslash before a quote, `'"'` and `'\''`, `'\u{7B}'`, nested block comments holding
  braces, `b'{'`, a multi-line string holding `{`, a multi-line `where` clause, and a doc comment holding `{`. All 8
  derive `target`. A file with unbalanced braces gives `unresolved=1`, which makes the selection the whole
  `tests/std` group plus every file label.

### Gate run (inside the snapshot)
- `python tools/axtest.py --smoke --check` -> `SMOKE-CHECK OK`; `python tools/axtest_affected.py --check-map` ->
  `MAP-CHECK OK`.
- `python tools/taskgate.py --task T437a --compiler build/axiomc2.exe --build-dir build --exclude-requires
  axiom0-internal -j 2 --json-out ...`:
  - wall 218.2 s (axtest 7.7 s); change set 15 files; unmatched none; tool self-test dirs axtest, gatecheck and
    taskgate selected;
  - smoke `TOTAL 48 PASS 46 FAIL 2`; failing `hir/types.ax resolve/simple.ax`, both on the baseline (`BASELINE OK`);
  - cache: 19 hits, all verified by the S6 sample (seed 234831944), no mismatch;
  - tool self-tests: `tools/tests/axtest` PASS (138 tests), `tools/tests/taskgate` PASS (44), `tools/tests/gatecheck`
    KNOWN (its 1 failure also fails at HEAD);
  - archcheck clean (229 files, 0 violations); WEAK-NATIVE 0 in own/changed tests; `TASKGATE T437a exit=0`.

### Verdict reasoning
- Every round-0 and round-1 finding (F1-F6) is fixed and covered by my unmodified regression tests.
- The remaining weaknesses G1-G3 need either a test that reads repository files outside its own directory (none
  exists) or a test that is nondeterministic by its own construction.
- None of them lets the cache or the affected set hide a regression introduced by a change to the compiler, std or
  tests: every such change changes the key or is selected.
- G1 is also re-run fresh by the periodic `--no-cache` full run.
- They are recorded as accepted limitations with recommendations, as the round-2 instructions allow.

### Follow-ups for the architect
- **G1:** in axiom-testing, require `nocache:` or `cache-inputs:` for tests that read files outside their own
  directory.
- **G2:** seed the S4 traversal with the implicit prelude files (or rely on T437b's exact mode).
- **G3:** note in ADR-0041 that ASLR-dependent tests are out of scope.
- Apply the report's "Harness follow-up" text (taskgate command, periodic full run with `--no-cache`).
- Add the gatecheck self-test to the baseline file or create a fix task for it.

## Files changed
- tools/tests/axtest/test_cache_qa.py
- _workspaces/reports/T437a-qa.md

VERDICT: PASS round=2
