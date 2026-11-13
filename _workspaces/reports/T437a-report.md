# T437a — Gate tooling: axtest result cache, --affected, --smoke, --baseline, longest-first, tools/taskgate.py

Owner: axiom-qa (implementation, round 0). Spec: ADR-0041 §4 (S1-S8) and §6, `.claude/agents/axiom-qa.md`
"Per-task gate scope" / "Periodic full run" / "Resource limits". Edits only under the task's `paths:`.

## Summary
- `tools/axtest_cache.py` (new) + wiring in `tools/axtest.py`: sound per-test result cache (S1-S8), dependency source
  `exact` (compiler `--dep-file`, probed once per binary hash) or `superset` (fallback), `--cache-dir`, `--no-cache`,
  `--gate`, `--verify-sample [SEED]`, `--cache-max-mb`, `CACHED n HITS h MISS m ...` line, `durations.json`,
  longest-first scheduling, `--baseline <file>`, `--id-file <file>`.
- `tools/axtest_affected.py` (new): `--affected <git-range | @file | path...>` with a printed derivation per id,
  `--smoke [--seed N]` and `--smoke --check`; `--check-map` CLI. `tools/affected_map.txt` (new): one row per
  `compiler/<mod>` directory (47 rows, validated). `tests/smoke.list` (new): `always:` + pools for all 28 groups.
- `tools/taskgate.py` (new): the per-task gate in one command, Markdown + JSON summary, documented exit codes.
- Self-tests: `tools/tests/axtest` 110 tests (80 existing, unmodified, + 30 new in `test_cache.py`; `stubcc.py`
  extended with `--dep-file` under `STUB_DEP_FILE=1`, ops `//@ dep`, `//@ append`), `tools/tests/taskgate` 23 new.
- Measured in `build-snap-T437a` with a real `axiomc2.exe`: smoke check OK (worst case 25 s), smoke run 9 s,
  `taskgate.py --task T437a` 188.6 s / 192.5 s (both exit 0), selfhost bundle `--time-passes` profile below.

## Design and soundness (ADR-0041 §4)
- **S1 key.** `prekey = sha256(canonical pre-material)`: schema 1, sha256 of the compiler binary, sha256 of every
  `tools/axtest*.py` (runner + its modules), test id, kind and the labels (modes) of the cached entries, compiler
  `--features`, behaviour-changing options (`--std-root`, `--timeout-scale`, `--exe-suffix`, `--exclude-requires`),
  environment (`AXIOM_STD` and every `AXIOM*`/`AX_*` variable of the program env), argv determinants (input
  argument, flags incl. `--target`/std root, program args, `cmd:`), test bytes (a project: its tree digest), every
  expectation file (golden siblings, `stdout-file:`), platform tag (`platform.system|version|machine`), dep source.
  `fullkey = sha256(prekey + dependency list with sha256 of each)`. The argv itself is a deterministic function of
  these (the runner's own source is in the key), so the temp paths never enter the key.
- **Cache unit = one test (all its modes).** A test is a hit only if every non-static entry has a valid PASS record;
  otherwise the whole test runs fresh. This keeps T139's interp-vs-native agreement check intact (a native leg is never
  run against a cached interp leg). Statically skipped entries (`native-after`, mode unavailable) are not part of the
  record and are re-evaluated each run.
- **S2.** Exact: every compiler invocation of the test gets `--dep-file=<tmp>/depsN.txt` (inserted after the
  subcommand; the probe runs `check --dep-file=<p> <probe.ax>` once per binary hash, recorded in `probe.json`). After
  the run each reported file is re-hashed and must equal the compiler-reported sha256; any missing/malformed dep file
  stores nothing. The exact list is extended by the name listing of every directory holding a dependency and of the
  test directory, and by `axiom.toml` presence in every ancestor directory (a file created next to a loaded module can
  change resolution — the ADR's `path sha256` format cannot express "probed and absent"; see follow-ups). Superset:
  test directory tree, the input's directory tree when `input:` leaves the test directory (e.g.
  `diff/002-arithmetic.ax` -> `../run/basic`), the whole std root tree, every `cache-inputs:` path, ancestor
  `axiom.toml` markers; digests computed before and after the run must be equal.
- **S3.** Only PASS stored (FAIL/SKIP/XFAIL/XPASS/CRASH/TIMEOUT never; `xfail:` tests never cached). Cached entries
  report the original PASS message, so output without the new flags is byte-identical except the extra `CACHED` line
  before `WEAK-NATIVE`/`TOTAL` (TOTAL stays the last line) and new JSON fields.
- **S4.** Never cached: `cmd:` tests without `cache-inputs:` (new multi directive; paths relative to the root, a
  directory = its tree), tests with `requires:` or `skip-unless:`, `nocache:` (new directive), tests whose own sources
  mention `async`/`await`/`spawn`/`std.{thread,sync,async,time}` or reach those std modules transitively (textual
  closure over `std.x.y` references, applied in both dependency modes), and in exact mode any dependency under
  `std/{thread,sync,async,time}/`.
- **S5.** Producer recorded per entry: origin, snapshot name, base commit (`git rev-parse HEAD` of the root), sha256
  of the change set (`git status` paths + content hashes). `origin: snapshot` iff the root directory is named
  `build-snap-*` and the compiler path lies inside a `build-snap-*` directory (the `tools/build_axiomc.py` output
  location, also when a binary is reused read-only from another snapshot); else `local`. `--gate` rejects local
  entries and entries whose base is not an ancestor of HEAD (`git merge-base --is-ancestor`), counted in
  `CACHE-REJECTED`.
- **S6.** `--gate` implies `--verify-sample`; sample = max(20, ceil(5 %)) of the hits (all hits when fewer), seed
  printed (`VERIFY-SAMPLE seed=S n=K of H hits`); a sampled hit runs fresh; any non-PASS result deletes its entry,
  re-runs every other hit fresh, stores nothing more and prints `CACHE-MISMATCH <ids>` (finding against the cache).
  Consequence: a gate with <= 20 hits re-runs all of them (no saving there); savings start above 20 hits (95 % of
  hits at large scale). This is ADR-mandated; recorded below.
- **S7.** One JSON file per entry `entries/<pk[:2]>/<prekey>/<fullkey>.json` (temp file + `os.replace`, retries on
  Windows sharing violations) holding the pre-material, deps, producer and `record_sha256`; an unreadable or
  inconsistent file is a miss and is deleted (`CACHE-CORRUPT-DELETED n`). Up to 8 candidates per prekey (different
  dependency states, e.g. several snapshots); LRU pruning by mtime (hits touch their file) to 80 % of `--cache-max-mb`
  (default 1024). Default location: `<main checkout>/_workspaces/artifacts/axtest-cache/` resolved through
  `git rev-parse --git-common-dir`, so every snapshot shares the main checkout's cache (git-ignored).
- **S8.** `CACHED n HITS h MISS m UNCACHEABLE u STORED s dep_source=...`; `--no-cache` never reports a cached result
  (decision: it still records fresh PASS results, so a phase gate warms the cache; nothing it reports comes from it).
- **Assumptions (recorded, guarded by S6):** A1 a result does not depend on the absolute checkout path (needed so
  snapshots share entries); A2 within one runner process a file whose size and mtime_ns are unchanged has unchanged
  content (hash memo).

## Selection (`--affected`, `--smoke`) and decisions
- Rules as in the task (1 exact, 2a tests, 2b std, 2c compiler, 2d tools, no-op for `spec/ _workspaces/ .claude/
  docs/`), order and texts documented in the `tools/axtest_affected.py` docstring; output `SELECT id <- rule`,
  `TOOL`, `GROUP g n`, `NOOP`, `UNMATCHED`, `DEFERRED`, `AFFECTED TOTAL`.
- Decision D1 (std names): only public **top-level** items (`pub ...` at column 0) count as "public names declared or
  changed in the diff". With methods included, bda2296a (new std/async files) selected 1579 ids (`len`, `new`,
  `poll` match most of the suite); top-level only: 90. Methods are reached through their type/module.
- Decision D2 (grep corpus): string/char literals and `//` comments are removed before matching (a diagnostic message
  "does not implement std.future.Future" selected 139 selfhost bundles); a std file that declares a name itself does
  not "reference" it. Matching uses a substring prefilter + per-subset regex (13-21 s for a derivation over the 260 MB
  corpus instead of minutes).
- Decision D3 (bundles): a bundle compiles the copy of a module embedded at generation time, so an un-regenerated
  compiler change reaches it only through the compiler binary, like every test. The bundle grep therefore selects the
  generator check manifest (`bundles_current.test`) of every directory whose bundles embed/list the changed module and
  the embedding bundles inside the module's own map targets (`compiler/mir -> tests/selfhost/mir`, as in axiom-qa.md);
  other embedding bundles are printed as `DEFERRED` (periodic full run). A regenerated bundle is a changed test file
  and is selected by rule 2a. Without D3 a typical compiler change selected 130-180 bundles (hours at -j 2).
- Decision D4: files directly in `tests/` (README.md, smoke.list) select nothing; deleted test-side files are NOOP.
  A changed tools file also selects the `tools/tests/<d>` whose sources name it (e.g. `affected_map.txt` ->
  `tools/tests/taskgate`). `bootstrap/` and other top-level files are UNMATCHED (the QA agent decides).
- Decision D5 (WEAK-NATIVE in taskgate): the exit condition counts WEAK-NATIVE only among the task's own tests and
  the changed test files (axiom-qa.md step 4a scope); the total over the run is printed for information (3 in the smoke
  set today, pre-existing).
- `--smoke`: per group `random.Random("<seed>:<group>").choice(sorted(pool))`; default seed = first 32 bits of the
  sha256 of the change set (sorted changed paths, or `git status` + content hashes). Groups whose every id is in the
  baseline (hir, parse except one, resolve) pool baseline ids; they are judged by the baseline rule.

## Measurements (build-snap-T437a, HEAD bed3d91 + this change set)
Compiler: `build-snap-T437a/build/axiomc2.exe`, a read-only copy of `build-snap-T452/build/axiomc2.exe`
(sha256 a21aee32889f…0e89; built 2026-11-13 01:03 in T452's snapshot — not rebuilt, owner resource rule; it may
contain T452's in-progress compiler changes, irrelevant for these tool measurements). It has no `--dep-file`, so
`dep_source=superset` everywhere below.
- Recording run (all 65 smoke candidate ids, -j 2, `--exclude-requires axiom0-internal --build-dir build`): 103
  results in 45 s; 4 FAIL, all baseline ids (`hir/basic.ax`, `hir/types.ax`, `resolve/R01_basic.ax`,
  `resolve/simple.ax`). Heaviest: `link/objdump_validate.test` 24.5 s, `link/lib/coff_lib.test` 4.2 s.
- `python tools/axtest.py --smoke --check` -> `SMOKE-CHECK worst-case estimate 25 s at -j 2 (bound 1200 s)`,
  `SMOKE-CHECK OK` (all 65 ids have recorded durations).
- `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2
  --smoke --no-cache` -> wall 9 s, `TOTAL 51 PASS 49 FAIL 2` (both baseline ids), seed 3472139840.
- `python tools/taskgate.py --task T437a --compiler build/axiomc2.exe --build-dir build --exclude-requires
  axiom0-internal -j 2 --json-out ...` (change set = the 10 files of this task; affected: no axtest ids, tool
  self-tests `tools/tests/axtest` + `tools/tests/taskgate`; smoke seed 852087393, 31 ids / 48 results):
  - run 1: wall 188.6 s (axtest 23.5 s, tool self-tests 108.7 s + 45.1 s), CACHED 0, hits 10 (all re-run by the
    S6 sample), stored 8, failing `hir/basic.ax resolve/R01_basic.ax`, BASELINE OK, archcheck clean, exit 0;
  - run 2 (identical): wall 192.5 s (axtest 25.4 s), hits 18 = every cacheable id (the 2 others are the failing
    baseline ids, never stored; 11 uncacheable: `cmd:`/requires tests), all 18 verified by the S6 sample (18 < 20),
    failing ids identical, exit 0.
  - A non-gate repeat of the same smoke ids reports them as `CACHED` (see "Cached repeat" below).
- Cached repeat (after the final runner edit, snapshot refreshed, so the runner hash changed and everything missed
  once): `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal
  -j 2 --smoke --seed 852087393 --baseline _workspaces/baseline-failures.txt`, twice:
  run 1 `CACHED 0 HITS 0 MISS 20 UNCACHEABLE 11 STORED 18`, `BASELINE OK`, `TOTAL 48 PASS 46 FAIL 2`;
  run 2 `CACHED 35 HITS 18 MISS 2 UNCACHEABLE 11 STORED 0`, `BASELINE OK`, `TOTAL 48 PASS 46 FAIL 2` (identical
  failing set; the 2 misses are the failing baseline ids, which are never stored).
- `--affected` on real past commits (current tree, `<c>^..<c>`):
  - `bda2296a` (T421, std/async + tests/std/async, 23 files): 90 ids (conformance 22, run 21, std 47), 0 unmatched,
    5 NOOP (`_workspaces/`), 13.2 s. Samples:
    `std/async/executor/local_executor_rc.ax <- std: ... references std.sync.atomic (std/sync/atomic.ax changed)`;
    `conformance/p11/e11_3_threads_sync/arc_mutex_8thread_stress.ax <- std: ... references std.sync.atomic
    (std/sync/atomic.ax references std.sync)`.
  - `fa86bbfc` (T406, compiler/{diag,mir,opt,types,verify} + prelude + atomic + regenerated bundles, 169 files):
    755 ids (conformance 192, run 167, selfhost 170 — 140+ of them regenerated bundles in the commit, mir 45, ui 72,
    verify 29, std 44, typeck 12, diff 10, opt 6, opt2 5, lir/modules/unit 1), 0 unmatched, 21.4 s. Samples:
    `mir/int128/saturating_roundtrip.test <- compiler: map compiler/mir -> tests/mir (compiler/mir/builder.ax)`;
    `conformance/p11/e11_1_concurrency/mir_happens_before_and_zero_cost_erasure.test <- std: ... references public
    name AtomicI32`; `selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax <- test: changed test file`.

## Profile of one heavy selfhost bundle (ADR-0041 §4, scope (d))
Bundle `tests/selfhost/opt/qa_opt_pipeline.ax` (80 195 lines, 3.4 MB), compiler as above, run one at a time inside
`build-snap-T437a`:
`axiomc2 run --interp --time-passes --std-root std <bundle>`, `axiomc2 build -O0|-O1 --time-passes --std-root std -o
<tmp>.exe <bundle>`. Times in seconds as printed by `--time-passes` (each mode: 11 `AX_NAME_SHADOW_MODULE` warnings,
0 errors; interp printed `OK opt pipeline`).

| stage | interp | -O0 | -O1 |
|---|---|---|---|
| source | 0.15 | 0.16 | 0.28 |
| lex | 0.67 | 0.64 | 0.66 |
| parse | 0.81 | 0.79 | 0.84 |
| resolve | 0.17 | 0.16 | 0.16 |
| hir | 0.32 | 0.27 | 0.29 |
| typeck | **14.39** (87 % of compile) | 15.29 (7.8 %) | 15.00 (7.5 %) |
| own | 0.00 (not run before interp) | **40.92** (20.8 %) | **37.41** (18.7 %) |
| mono | – | 0.00 | 0.00 |
| build (MIR build + opt + lowering + codegen + link, one timer) | – | **138.33** (70.4 %) | **144.97** (72.6 %) |
| run (interpreter executing the bundle) | 83.97 | – | – |
| compile total | 16.51 | 196.57 | 199.64 |
| wall (incl. process) | 101 s | 198 s | 200 s |

Architect candidates (> 30 % of compile time; not optimised here):
1. `build` stage of native compiles, 70-73 % (138-145 s). It is a single timer in `compiler/driver/pipeline.ax`
   (`format_pass_time(..., 9u32, ...)`); the first follow-up is to split it per pass (MIR build, opt passes, LIR,
   isel, regalloc, encode, link) so the dominating pass can be named.
2. `typeck` in interp mode, 87 % of the 16.5 s compile (14-15 s in every mode for 80 k lines).
3. `own` (ownership/capability analysis) 37-41 s in native modes — 2.5x typeck, below 30 % but the second largest
   native stage; worth checking for super-linear behaviour.
Super-linearity cannot be judged from one bundle size; the measurement to decide it is the same three commands on
a small and a large bundle of one family (e.g. `tests/selfhost/opt/qa_opt_unit.ax`, 1.5 MB, vs `qa_opt_pipeline.ax`,
3.4 MB).

## Self-tests
- `python tools/tests/axtest/run_selftests.py` -> `SELFTEST 110 tests, 0 failures, 0 errors` (80 existing unmodified
  + 30 in `test_cache.py`: hit on identical inputs; miss after one byte of the test, of a golden and a `stdout-file:`
  expectation, of an exact dependency, of a std file (superset) and a new std file, of a new helper in the test
  directory, of the compiler binary, of `axtest.py`/`axtest_cache.py`, of `--timeout-scale`/`AXIOM_*`/
  `--exclude-requires`, of the mode set; exact list hit when an unloaded std file changes and miss when a file appears
  next to a loaded one; probe per binary; FAIL/TIMEOUT/SKIP/XFAIL/XPASS never stored; S4 classes (requires, nocache,
  thread/indirect std.thread/async sources, `cmd:` without inputs, exact dep under std/time) never stored; `cmd:` with
  `cache-inputs:` cached and invalidated; truncated and altered entries = miss + deleted; 3 processes x `-j 4` on one
  cache: 24 valid entries, no temp leftovers, then all hits; `--gate` rejects local entries, accepts an ancestor base,
  rejects a non-ancestor base (orphan branch), prints the sample seed; verification mismatch disables the cache for the
  run; sample size max(20, 5 %); longest-first order with recorded/unknown durations; hits keep recorded durations;
  `--baseline` subset / new failure / now passing with unchanged exit status; `--id-file`).
- `python tools/tests/taskgate/run_selftests.py` -> `SELFTEST 23 tests, 0 failures, 0 errors` (temporary git
  fixture: std change via module path, transitive std module and public name; methods/strings/comments not
  references; compiler change = map rows + bundle grep + generator check, other bundles DEFERRED, regenerated bundle
  selected; test-only, helper, expectation, top-level tests/ files; tools change incl. `cmd:` users; spec-only = empty
  set; unmatched list; exact rule preferred over grep; compiler map applies despite an exact entry; map validation
  (missing row, missing target; `--affected` exit 2); smoke check (OK unverified, missing group, unknown id + missing
  always cases, over the bound); seeded draws; taskgate end-to-end Markdown/JSON, second run hits, new failure ->
  exit 1, baselined -> 0, archcheck -> 1, WEAK-NATIVE in own tests -> 1, `--range`, `--changed`, failing tool
  self-tests -> 1, unknown task -> 2).
- `python tools/archcheck.py` -> `archcheck: 229 files scanned, 0 violations`; `python tools/axtest_affected.py
  --check-map` -> `MAP-CHECK OK`.

## Harness follow-up (for the architect; exact text)
For `.claude/agents/axiom-qa.md`, section "Per-task gate scope", replace the sentence beginning "Once T437a is done"
with:

> Run the whole scope from inside the snapshot with one command and paste its Markdown block into the QA file:
> `python tools/taskgate.py --task <ID> --compiler build/axiomc2.exe --build-dir build --exclude-requires
> axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-<ID>.json` (inside `build-snap-<ID>`; the change set
> defaults to the snapshot's working-tree changes; use `--range <base>..<head>` or `--changed @file` otherwise;
> `--extra <ids>` adds own tests outside the task's `paths:`; `--seed N` repeats a smoke draw). Exit 0 = archcheck
> clean, no failing id outside `_workspaces/baseline-failures.txt`, tool self-tests pass, no WEAK-NATIVE among the
> task's own/changed tests (a tool self-test that also fails in the HEAD version of `tools/`, or whose id
> `tools/tests/<dir>::<unittest id>` is in the baseline, is printed as "known" and does not fail the gate). Check the
> printed derivation, the `UNMATCHED`, `UNRESOLVED` (an underivable std change; the whole `std` group was selected),
> `MAP-NOTE` (skipped map targets) and `DEFERRED` lists and the cache line (`CACHE-MISMATCH` is a finding against the
> cache: report it in Follow-ups). The native-evidence spot-proof (step 4a) and the adversarial tests (step 5) remain
> manual. Phase gates and the first gate after a cache-format change add `--no-cache`. A task that adds a
> `compiler/<mod>` directory adds its row to `tools/affected_map.txt`.

For `.claude/agents/axiom-qa.md`, section "Periodic full run", add (QA recommendation R1, adopted):

> The periodic full run uses `--no-cache` semantics: `python tools/axtest.py --no-cache -j 2 --baseline
> _workspaces/baseline-failures.txt --json ...` (every id executes; fresh passes are still recorded and re-validate the
> cache). A gate verifies only max(20, 5 %) of its hits, so the full run is what keeps a poisoned entry from
> persisting; any id whose fresh result differs from a cached PASS seen since the last full run is reported as a
> finding against the cache (ADR-0041 S6 revisit).

For `.claude/skills/axiom-testing/SKILL.md`, in the runner section after the existing `axtest.py` examples, add:

> ```
> python tools/axtest.py --affected <base>..<head> --list   # tests that can observe a change, with the rule per id
> python tools/axtest.py --smoke [--seed N]                 # always: ids + one id per group (tests/smoke.list)
> python tools/axtest.py --smoke --check                    # validate tests/smoke.list and its 20-minute bound
> python tools/axtest.py --baseline _workspaces/baseline-failures.txt ...   # BASELINE OK | NEW FAILURES: ...
> python tools/axtest.py --no-cache ...                     # never report cached results
> python tools/taskgate.py --task <ID> ...                  # the whole per-task gate (axiom-qa.md)
> ```
> Results are cached by default (ADR-0041 §4; `<main checkout>/_workspaces/artifacts/axtest-cache/`); the summary
> prints `CACHED n HITS h MISS m ...`. A test that must never be cached declares `// nocache: <reason>`; a `cmd:`
> manifest is cached only when it declares every input with `cache-inputs: <paths relative to the root>`. Keep
> `tests/smoke.list` pools light (`--smoke --check`); when a group gets its first test, add a pool line.

## Follow-ups
- T437b (`--dep-file`): emit `path sha256` lines for every loaded file as specified; additionally consider
  `path -` lines for probed-but-absent module paths (the runner treats an exact list as complete; it already guards
  sibling-file creation with directory listings, a `-` form would make that precise). The probe calls
  `<compiler> check --dep-file=<path> <file>`; the flag must be accepted right after the subcommand.
- Architect: `tests/smoke.list` pools for hir/resolve/parse are baseline ids; swap them for passing ids once T434
  lands.
- Architect candidates from the profile: see the profile section.
- Architect (round 1): add `tools/tests/gatecheck::test_gatecheck.<Class>.test_check_without_command_blocks` to
  `_workspaces/baseline-candidates.txt` / the baseline with a fix task — it fails identically at HEAD (QA round 0,
  `git archive bed3d915 tools`, `TypeError ... NoneType`). taskgate now reports it as "known" (fails at HEAD too) and
  does not fail the gate on it; the exact unittest id is printed by taskgate (see Round 1).
- Architect / T437b TODO (round 1): `tests/run/int128_interp` was removed from the `compiler/interp` row of
  `tools/affected_map.txt` because it is untracked (T452's in-progress work); add it back once T452 has landed it
  (T452's accept does not update the map). The TODO is also a comment in the map file.

## Round 1 (fixes for QA round 0, `_workspaces/reports/T437a-qa.md`)
- **F1 false cache HIT** — `tools/axtest_cache.py` `Hasher.tree` now hashes every file of the tree, dot-files,
  dot-directories and `__pycache__/` included; only a `.git` directory and `*.pyc` byte-code are skipped (the
  compiler never reads them; Python generators write them while tests run, which would otherwise only cost stores).
  The same digest is used for project test bytes. Regression: QA's 3 `TreeDigestSeesCompilerInputs` tests and
  `test_cache.HitMissTests.test_project_test_sees_dot_files_and_pycache` (project test, `src/.evil.ax`,
  `src/.hidden/x.ax`, `src/__pycache__/y.ax` each -> miss). Real compiler (snapshot, scratch cache):
  `modules/hello` PASS stored; add `src/.evil.ax` -> `CACHED 0 ... MISS 1`, `TOTAL 3 PASS 0 FAIL 3` (was CACHED 3).
- **F2 map target of another task** — `tests/run/int128_interp` dropped from the map (TODO above). `check_map` now
  returns problems only for unusable tables (tracked module dir without row, row for a non-directory, no targets,
  target outside tests/); a target that does not exist or is not tracked by git (`git ls-files`), and an untracked
  module directory without a row, are `MAP-NOTE` lines and the target is skipped by the selection. Regression: QA's
  `test_targets_are_tracked`, `test_taskgate.MapValidationTests.test_missing_or_untracked_target_is_a_note_and_skipped`
  (+ `test_missing_module_row_is_caught` now commits the module first). Snapshot: `--check-map` -> `MAP-CHECK OK`;
  `axtest.py --affected compiler/interp/interp.ax --list` -> exit 0, `AFFECTED TOTAL 31 ... 13 deferred`.
- **F3 timer/env bindings cached** — new S4 class built from a grep, not a hand list: every foreign (`fn ...;`) or
  `@intrinsic` function declared in a std host-binding file (a file with `@intrinsic`/`extern "..."`) whose name is
  about time/clock/tick/counter/monotonic/env/random/pid/perf (`nondet_name`, by name words, so
  `capability_grant_check_runtime` does not match). Today: `GetEnvironmentVariableW, QueryPerformanceCounter,
  QueryPerformanceFrequency, SetEnvironmentVariableW, env_get, monotonic_ns`. A test is never cached when its sources
  use such a binding, declare a foreign/intrinsic function with such a name (FFI `GetTickCount64`, `GetSystemTime`,
  `GetCurrentProcessId`), import one (`use ...monotonic_ns`), or reach a std file that calls one. Over the
  non-selfhost suite this flags 17 tests (incl. all 15 of QA's list). Regression: QA's 3 `TimerBindingsNeverCached`
  tests and `test_cache.NeverStoredTests.test_timer_env_bindings_never_cached` (clock, FFI-declared rng, env via a std
  wrapper, `GetTickCount64` never cached; an unrelated host binding still cached). Real compiler:
  `run/host/fs/clock.ax run/ffi/tick_count.ax` twice -> `UNCACHEABLE 2`, `CACHED 0` both times (was CACHED 5).
- **F4 impl-body changes derive no name** — `axtest_affected.derive_names` replaces the column-0-`pub`-only rule.
  Per hunk: public top-level items in `+`/`-` lines; the hunk header's enclosing declaration (`impl<T> Atomic<T> {` ->
  `Atomic`, `impl Future for Sleep {` -> `Sleep`, `struct/enum/trait X`); types/traits declared or implemented in the
  changed lines; types the file declares that a changed line mentions; re-exports (`pub use a.b.Name`). A hunk in a
  private top-level function (or one yielding nothing) falls back to every public top-level name and declared type of
  the file. A hunk that still yields nothing (and is not a new file, which can only be reached through its module path)
  is printed `UNRESOLVED <file>: hunk ... yields no name` and the whole `tests/std` group is selected (rule
  `unresolved std change: whole group std`); taskgate prints it in the derivation. Decision: types are taken only
  from names the changed file itself declares (all identifiers of changed lines would include `Vec`, `Some`, locals
  and select most of the suite). Regression: QA's 2 `ImplBodyChangeNamesType` tests;
  `test_taskgate.AffectedTests.test_impl_body_change_selects_users_of_the_type`,
  `test_private_helper_change_falls_back_to_file_names_and_unresolved_selects_group`. Re-derived: `bda2296a` 116 ids
  (was 90), `fa86bbfc` 755 ids (unchanged), 0 unmatched, 0 unresolved.
- **gatecheck self-test failing at HEAD** — taskgate parses the `FAIL:`/`ERROR:` lines of a failing tool self-test
  run into ids `tools/tests/<dir>::<unittest id>`; an id is "known" when it is in the baseline file or fails too when
  the same `run_selftests.py` runs on `git archive HEAD tools` in a temp dir; a run whose failures are all known is
  `KNOWN` (gate not failed, listed); any other failure is NEW (exit 1). Regression:
  `test_taskgate.TaskgateTests.test_tool_selftest_failing_at_head_is_known_not_new` (known at HEAD -> exit 0, an extra
  failure -> NEW exit 1, then baselined -> exit 0).
- **R1** adopted in the harness follow-up text (periodic full run with `--no-cache`). **R3**: S5 `origin: snapshot`
  is decided by directory names (`build-snap-*` root and compiler path), not by `tools/build_axiomc.py` provenance;
  sound because the compiler binary hash is part of every key — the origin only limits which entries a gate trusts.
- QA's `tools/tests/axtest/test_cache_qa.py` is unchanged and passes (9/9).
- Self-tests: `python tools/tests/axtest/run_selftests.py` -> `SELFTEST 121 tests, 0 failures, 0 errors`
  (80 + 32 own + 9 QA); `python tools/tests/taskgate/run_selftests.py` -> `SELFTEST 26 tests, 0 failures, 0 errors`;
  `python tools/archcheck.py` -> 229 files, 0 violations; `python tools/axtest_affected.py --check-map` -> `MAP-CHECK OK`.
- taskgate in the refreshed snapshot (`python tools/taskgate.py --task T437a --compiler build/axiomc2.exe
  --build-dir build --exclude-requires axiom0-internal -j 2 --json-out ...`, change set 13 files), twice:
  run 1 wall 218.1 s (axtest 23.7 s), 30 ids / 51 results, 49 PASS, failing `hir/basic.ax resolve/R01_basic.ax`
  (baseline), BASELINE OK, stored 19; tool self-tests `tools/tests/axtest` PASS (121), `tools/tests/taskgate` PASS
  (26), `tools/tests/gatecheck` **KNOWN** — known failure
  `tools/tests/gatecheck::test_gatecheck.GatecheckTest.test_check_without_command_blocks` (fails at HEAD too);
  archcheck clean; **exit 0**. Run 2: wall 218.9 s, 19 hits (every cacheable id; all 19 verified by the S6 sample
  since 19 < 20), miss 2 (the baseline failures), identical failing ids, same KNOWN failure, **exit 0**.
  Baseline candidate for the architect: `tools/tests/gatecheck::test_gatecheck.GatecheckTest.test_check_without_command_blocks
  undiagnosed:gatecheck-selftest <fix task>`.

## Round 2 (fixes for QA round 1, `_workspaces/reports/T437a-qa.md`)

QA's `tools/tests/axtest/test_cache_qa.py` is unchanged and all 14 tests pass, including the 5 round-1 tests
(`ThreadBindingsNeverCached` x3, `ContextLineDeclarationNamed` x2).

### F5: never-cache class is now derived structurally and denies by default (`tools/axtest_cache.py`)
- **Leaf bindings** are found by parsing source files (comments stripped, string literals kept):
  - functions declared inside an `extern "<abi>" { ... }` block (brace-matched);
  - body-less `extern "<abi>" fn X(...);`;
  - `@intrinsic` functions, in either the same-line or the attribute-line form;
  - host providers `fn __ax_host_<name>`, and any mention of `__ax_host_<name>`, normalised to `<name>`.
- **Deny by default.** A leaf binding counts as deterministic only when it is on the positive list
  `DETERMINISTIC_BINDINGS`, or matches the pure-arithmetic intrinsic pattern
  (`wrapping_add_u64`, `count_ones_u8`, ...). The list covers:
  - layout/memory intrinsics, heap, process exit;
  - console/file output, file system operations on the test's own files;
  - command-line arguments, a few pure C functions.

  Every other leaf binding, whatever its name and wherever it is declared, makes a test uncacheable. That includes
  threads, critical sections, futex/WaitOnAddress, Sleep/WaitForSingleObject, clocks/counters, environment, process
  ids, module handles/paths, VirtualProtect, randomness, and any binding added later. Today std declares 34
  nondeterministic leaves, all in `std/sys/windows/{thread,time,fs,io,process}.ax` and `std/core/host.ax`
  (`CreateThread`, `GetCurrentThreadId`, `Sleep`, `WaitOnAddress`, `__ax_host_thread_spawn`, `monotonic_ns`,
  `env_get`, `exe_path`, ...).
- **When a test is uncacheable:**
  1. its sources declare a non-listed leaf, use a nondeterministic std leaf or `__ax_host_<nondet>`, or import one;
  2. a std file it reaches transitively through `std.a.b` references *uses* a nondeterministic leaf. "Uses" means
     any mention other than the leaf's own `fn NAME` declaration: a call, a `use`/`pub use` re-export, an alias, a
     function value. So `std.core.host`, which only *declares* `monotonic_ns`, does not taint a heap-only user;
  3. exact dependency lists: a loaded std file that uses such a leaf (new `exact_deps_nondet(..., std_index, root)`),
     in addition to the std/{thread,sync,async,time} rule.

  The old word filter remains only as an extra net for imported names.
- **Decision (recorded):** classification is per leaf function, not per module. A module-level rule ("every binding
  module not classified pure taints") would taint `std/core/host.ax`, which declares `heap_alloc` and `write` next
  to `monotonic_ns`. It would also taint `std/sys/windows/io.ax` (the runtime keeps its file table in an env var).
  That would make every printing or allocating test uncacheable. Per function, deny-by-default stays sound and
  keeps the cache useful.
- **Real compiler, QA's repro shape.** I used `tests/run/qa_r2tmp/tid.ax` in the snapshot only, then removed it:
  FFI `GetCurrentThreadId`, even/odd output, `modes: native`. I ran
  `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build -j 1 --cache-dir <fresh> run/qa_r2tmp/`
  3 times: each run printed `CACHED 0 HITS 0 MISS 0 UNCACHEABLE 1 STORED 0`. The result is never stored and the
  flaky outcome stays visible (`PASS 1 FAIL 1` in that run).
- **Hit rate before/after.**
  - Static, over the 1698 non-selfhost `.ax` files: 150 uncacheable with the round-1 classifier, 156 with round 2.
    The +6 are all compile-only tests that declare made-up bindings: `hir/more.ax`, `resolve/more.ax` (`ext`),
    `parse/attributes.ax` (`GetProcessId`), `parse/qa_missing_body_extern.ax`, `ui/intrinsics/unknown_intrinsic.ax`,
    `ui/parse/terminator_members.ax`. No file lost its flag.
  - Selfhost: 151 of 168 flagged both before and after.
  - Real run in the snapshot (`lex/ run/str/`, fresh cache, `-j 2`, twice): run 1 `MISS 23 UNCACHEABLE 27
    STORED 23`; run 2 `CACHED 39 HITS 23 MISS 0 UNCACHEABLE 27`. That is 100 % of the cacheable ids. The 27
    uncacheable are 23 `ui/lex/*.test` `cmd:` manifests and 4 `selfhost/lex` ids, not deny-by-default verdicts.
- **Regression tests.** `test_cache.NeverStoredTests.test_timer_env_bindings_never_cached` was updated: its unknown
  intrinsic `heap_size` is now expected uncacheable (a deliberate reversal of round 1), and a classified
  `heap_alloc` stays cacheable. Self-audit: `tools/tests/axtest/test_cache_round2.py` (12 tests, see below).

### F6: changed lines are attributed to their enclosing declarations (`tools/axtest_affected.py`)
- **Scanner.** New `Decls` scanner:
  - comments and string/char contents are blanked first;
  - items are recognised only in item position: file top level and impl/trait/mod/extern bodies;
  - `fn`, `impl`, `trait`, `struct`, `enum`, `union`, `type`, `const`, `static`, `macro`, `mod` and `extern` blocks
    each get a line range;
  - brace-less items (`pub type X = Y` without `;`) end at the next item, or at an unindented non-item line;
  - trailing attribute and blank lines are given to the next item;
  - `ok = False` when the braces do not balance.

  All 257 std + compiler `.ax` files scan with balanced braces, and every non-blank line is attributed.
- **Per changed line.** `+` lines are located in the NEW file and `-` lines in the OLD file. `derive` now reads both
  sides with `git show` (range `a..b`: `a:path` / `b:path`; working tree: `HEAD:path` / disk), so a pure deletion is
  seen in the old file. The innermost containing item is the seed. A changed attribute line belongs to the item
  below it. A `use`/`module` line affects the whole file: every label of the file, plus a `pub use` re-export name.
  Blank and comment-only lines are ignored.
- **Labels and in-file closure.** The affected items are the seeds plus every item of the same file that
  transitively mentions one of their names (in-file callers). Their labels become the derived names:
  - a public top-level item: its own name;
  - an impl member: the impl's type and trait;
  - a trait member: the trait, its implementers in the file, and the member name, because a default body runs for
    every implementer.

  A private item with no labelled user falls back to every label of the file.
- **UNRESOLVED.** A code line outside every declaration (a top-level statement), unbalanced braces, or seeds without
  any label (outside a new file) produce an `UNRESOLVED` line, one per hunk. That selects the whole `tests/std` group
  plus every label of the file. Nothing is dropped silently.
- **Fallback.** `_derive_names_headers` (the round-1 header rule) remains only for direct callers that pass no file
  text.
- **Real prelude, QA's repro shape.** I appended a comment to the first body line of `pub fn is_lock_free` in
  `std/core/prelude.ax` (snapshot only, restored). git's header names the function itself here, but the selection
  no longer depends on the header. `axtest.py --affected std/core/prelude.ax --list` selected 139 ids, 0 UNRESOLVED,
  including both QA examples (`litmus_rmw_counter_wrapping_and_spinlock.ax`,
  `qa_signed_cas_const_ptr_and_sb_relaxed.ax`). Every one of the 63 non-selfhost test files that mention
  `is_lock_free` is selected; the one helper file is covered through its 4 `mir/atomics/*.test` manifests.
- **Past commits (snapshot, `--affected <c>~1..<c> --list`).** 0 unresolved, 0 unmatched in all five:
  - bda2296a: 461 ids (round 1: 116);
  - b433999e: 273 (273);
  - 7a8ef713: 859 (743);
  - e969c207: 524 (524);
  - fa86bbfc: 751 (round 1 rule at the same HEAD: 752).

  The only id that round 1 selected and round 2 does not is `modules/prelude_implicit`. Round 1 picked it from
  git's hunk header (`prelude_loaded`) for a pure insertion *after* that unchanged function. Otherwise round 2 is a
  superset, so no test is lost.

### Self-audit (my own adversarial cases, all run)
Cache classifier: `tools/tests/axtest/test_cache_round2.py`, 12 tests on a temp std plus the real std. 7 of them
fail against the round-1 classifier, which shows they discriminate (`python -m unittest` against round-1
`axtest_cache.py`: `FAILED (failures=6, errors=1)`).
- Binding reached only through a re-export alias (`pub use std.core.host.monotonic_ns as now` in a non-sys module,
  no call): uncacheable.
- Extern declared in a non-sys std module (`std.util.rng`, `BCryptGenRandom`): uncacheable.
- Transitive chain `std.a` -> `std.b` -> extern `__rdcycle`: uncacheable.
- Unknown `@intrinsic fn cpu_cycles`, whose name has no time/thread word: uncacheable (deny-by-default).
- Body-less `extern "C" fn rand();`: uncacheable.
- Host provider `__ax_host_thread_current_id()` called directly: uncacheable; `__ax_host_heap_alloc`: cacheable.
- `@test` / `#[test]` functions spawning through `std.thread`: uncacheable.
- Pure test (size_of, wrapping_add_u32, WriteFile/GetStdHandle FFI, heap via a std module): stays cacheable.
- A module that only declares a nondeterministic intrinsic does not taint a heap-only user; calling it through the
  module path does.
- Binding text inside a comment or string is not a binding.
- Exact dependency list containing a tainted std file: uncacheable; host + pure module deps: none;
  `std/thread/...`: uncacheable.
- Real std: the thread/sync/timer/env bindings are nondeterministic; heap/WriteFile/size_of/wrapping are not;
  `use std.sys.windows.thread` and `.time` are uncacheable, `.heap` is cacheable.

Affected selector: `tools/tests/taskgate/test_affected_round2.py`, 18 tests (14 on derive_names with real old/new
texts, 4 end-to-end through a git fixture).
- Hunk at file start: a `use` line gives the whole file's names, not UNRESOLVED.
- Hunk at file end: the last fn's body selects `last` only; an appended fn selects its new name.
- Generic trait default method body: `Shape`, the implementer `Square`, and `describe`.
- First body line of an impl method: `Square` + `Shape`.
- Private helper: reaches its public caller (`first`); a private fn used only by an inherent impl method selects
  that impl's type.
- Rename: old and new name.
- Deleted function: the old name from the old file.
- Changed `pub const` used by name: the const plus its in-file user.
- `pub macro` body: the macro's name.
- Where-clause line and attribute line (`@inline` -> `@inline(always)`): the function.
- Braces and `fn` inside a string literal do not confuse the scanner.
- Comment-only change: no names and not UNRESOLVED (module-path users are still selected by the module rule).
- Top-level statement: UNRESOLVED + whole group.
- Unbalanced braces: UNRESOLVED.
- Git end-to-end:
  - deleted function selects its callers;
  - file move selects users of the old module path, the new module path and the moved function;
  - working-tree change at the first body line;
  - an UNRESOLVED line is printed and selects `tests/std`.

Bug found by the self-audit and fixed: a brace-less `const` without `;` swallowed a following top-level
statement, so a stray statement was attributed to the const instead of being UNRESOLVED. The scanner now ends a
brace-less item at an unindented line that starts no item.

### Suites and gate (snapshot `build-snap-T437a`, HEAD ef323c3 + this change set)
- `python tools/tests/axtest/run_selftests.py` -> `SELFTEST 138 tests, 0 failures, 0 errors`
  (round 1's 121 + QA's 5 round-1 tests + my 12 new; run by taskgate on the final code, 118.3 s)
- `python tools/tests/taskgate/run_selftests.py` -> `SELFTEST 44 tests, 0 failures, 0 errors` (incl. 18 new, 68.6 s)
- `python tools/axtest.py --smoke --check` -> `SMOKE-CHECK OK` (worst case 23 s at -j 2)
- `python tools/archcheck.py` -> 229 files, 0 violations
- `python tools/axtest_affected.py --check-map` -> `MAP-CHECK OK`
- `python tools/taskgate.py --task T437a --compiler build/axiomc2.exe --build-dir build --exclude-requires
  axiom0-internal -j 2 --json-out <scratch>` (once):
  - **exit 0**, wall time 229.4 s (axtest 9.8 s);
  - change set 15 files;
  - smoke seed 2284676750: 31 ids / 48 results, 46 PASS, failing `hir/types.ax resolve/simple.ax` (both on the
    baseline, `BASELINE OK`);
  - cache: CACHED 0, miss 21, uncacheable 10, stored 19. There were no hits because the runner's own hash changed,
    so every key is new (S1);
  - WEAK-NATIVE 0 in own/changed tests;
  - tool self-tests: axtest PASS (138), taskgate PASS (44), gatecheck KNOWN (the HEAD failure from round 1);
  - archcheck clean.
- Processes: no axtest/axiomc2/python process of mine is left running.

## Files changed
- tools/axtest.py
- tools/axtest_cache.py
- tools/axtest_affected.py
- tools/affected_map.txt
- tools/taskgate.py
- tools/tests/axtest/stubcc.py
- tools/tests/axtest/test_cache.py
- tools/tests/axtest/test_cache_qa.py
- tools/tests/axtest/test_cache_round2.py
- tools/tests/taskgate/run_selftests.py
- tools/tests/taskgate/test_taskgate.py
- tools/tests/taskgate/test_affected_round2.py
- tests/smoke.list
- _workspaces/reports/T437a-report.md

STATUS: COMPLETE round=2
