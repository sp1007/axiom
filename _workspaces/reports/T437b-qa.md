# T437b QA gate

## Round 0

Gate model: opus. Snapshot `build-snap-T437b` (HEAD `7d84ada3` + the task's change set). Implementation report
`_workspaces/reports/T437b-report.md` (ends `STATUS: COMPLETE round=0`).

### Compiler under test
- `build-snap-T437b/build/axiomc2.exe` sha256 `1b79d78a...c2f155` (matches the report). It was built at base `349083e`;
  the snapshot is now at `7d84ada3`. `git diff --stat 349083e 7d84ada3 -- compiler std tools bootstrap` touches only
  `std/async/{executor,group,mod,task,waker}.ax`; nothing under `compiler/` references `std.async`/`std/async` and the
  driver loads std implicitly only from `core/` and `future/`, so the binary corresponds to the snapshot sources. The
  four changed source files (opts.ax, pipeline.ax, axtest_cache.py, axtest_affected.py) are byte-identical in the main
  tree and the snapshot. Not rebuilt.

### Change set (`taskctl.py changes T437b`)
- Before my tests: 33 staged paths, no `REFUSED` line. After adding the QA tests below, the 4 new files are reported as
  unlisted until this QA file lists them (`## Files changed` below).

### taskgate (one command, inside the snapshot, `--no-cache` because the task changes the dirlist digest and makes
the exact dependency path live = first gate after a cache-format change)
`python tools/taskgate.py --task T437b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --no-cache --baseline _workspaces/baseline-failures.txt --json-out _workspaces/artifacts/taskgate-T437b.json`

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 13 | 13 | 12 | 1 | 0 | 0 | 0 |
| affected | 48 | 71 | 56 | 15 | 0 | 0 | 0 |
| smoke | 30 | 51 | 49 | 2 | 0 | 0 | 0 |
| **total (dedup)** | 75 | 117 | 100 | 17 | 0 | 0 | 0 |

- Wall 7299 s (axtest 7046 s). `TOTAL 117 PASS 100 FAIL 17`. archcheck clean (229 files, 0 violations). Tool
  self-tests: `tools/tests/axtest` SELFTEST 138/0 failures, `tools/tests/taskgate` SELFTEST 44/0 failures.
- Affected-set derivation (audited): `compiler/driver` map row -> `tests/driver`, `tests/inspect`, `tests/modules`,
  `tests/unit/driver`, `tests/selfhost/driver`; changed bundles select themselves (all 6 `selfhost/driver` and both
  `selfhost/obj_link_driver` bundles); `selfhost/obj_link_driver/bundles_current.test` via "generator check of a bundle
  embedding compiler.driver.opts"; tools changes -> `tools/tests/axtest`, `tools/tests/taskgate`. UNMATCHED: the 5
  fixture files under `tests/driver/dep_file/fixtures/**` (they are read by the dep_file tests of the same directory,
  which are selected anyway; no gap). No UNRESOLVED, MAP-NOTE or DEFERRED entries. Cache line:
  `CACHED 0, miss 39, uncacheable 36, stored 35, dep_source exact` (no CACHE-MISMATCH).
- Smoke seed 2533319380 (always: `run/str/hello.ax` = Xin chào thế giới, `ui/typeck/type_unknown.ax`,
  `diff/002-arithmetic.ax`; one pick per group, listed in the taskgate JSON).
- Failing ids: `driver/build_emit_obj.test` (baseline T431), `hir/types.ax`, `resolve/simple.ax` (baseline T434),
  `modules/prelude_implicit` (baseline T432), `selfhost/driver/qa_driver_commands_b.ax`,
  `selfhost/driver/qa_driver_inspect_diff_b.ax` (baseline T436), `selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`,
  `qa_obj_link_driver_smoke.ax` (baseline T442) -- all inside the baseline; plus two outside:
  - `driver/dep_file/qa_cache_e2e_rtread.test`: my adversarial test, fails because of finding F1 (caused by the task).
  - `selfhost/driver/qa_driver_commands_a.ax`: re-run alone in the snapshot,
    `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build -j 2 --no-cache selfhost/driver/qa_driver_commands_a.ax`
    -> `TOTAL 3 PASS 3` (37.5 min wall). The gate run had two heavy bundle compiles in parallel on the shared machine;
    taskgate's JSON keeps no per-id message, so the failure kind (most likely a 1200 s step timeout under load) could
    not be read back. It passes alone at scale 1, so per the load rule it does not count as failing; the missing
    per-id message is a tooling follow-up (below).
- WEAK-NATIVE (taskgate exit reason): the 8 regenerated bundles' native legs have no `stdout:`/`exit:` directive (they
  were assert-based before this task; only the embedded opts/pipeline text changed). T134 is done (native `assert`
  exits 101), so assert-only native legs are acceptable per step 4a; not a finding against this task (pre-existing,
  see follow-ups).

### Native-evidence spot-proof (step 4a)
- `selfhost/driver/qa_driver_boundary_edges.ax` mutated in the snapshot only (`// modes: native`, `// exit: 7`
  added): `FAIL [native]: exit code 0, expected 7` and `FAIL [native-O1]: exit code 0, expected 7`; restored, `cmp`
  identical to the main tree. The native legs compare an observable result.
- The new `tests/driver/dep_file/*` tests are `cmd:` tests (no native leg).

### Generators and bundles (check 3)
- All 36 generators `tests/selfhost/*/gen_*.py --check`: rc=0 for every one, every output line "up to date", no
  `differs` line (log in the QA scratch; second pass filtering out "up to date" printed nothing). Includes `lir`.
- Bundles embedding the edited modules: all 8 ran in the gate (see above): `qa_driver_boundary_edges`,
  `qa_driver_cli_and_project`, `qa_driver_inspect_diff_a` PASS; `qa_driver_commands_a` PASS alone; the 4 others are
  baseline ids (T436, T442). `selfhost/driver/bundles_current.test` and `selfhost/obj_link_driver/bundles_current.test`
  PASS.

### `--dep-file` behaviour (check 1), ad-hoc probes in the snapshot
- Every command writes the list, also on a failing compile (3 unresolved-name errors: list still written, rc 1) and on
  `run --interp` of a program exiting 7 (list written before the process ends).
- SHA-256 of the driver checked against Python `hashlib` on files of 0, 1, 55, 56, 57, 63, 64, 65, 119, 120, 128 and
  1000 bytes (padding block boundaries, passed as `build` object inputs): all equal.
- CRLF source and UTF-8 BOM source: hashed over the raw bytes (equal to hashlib); the dep file itself has no CR.
- Absolute path with spaces and Vietnamese letters (`.../thư mục có dấu/chào thế giới.ax`, dep file `dép.txt`):
  written correctly, `parse_dep_file` accepts it.
- Backslash input `build\qa_t437b\plain.ax` is written with `/`; `./`-prefixed input and `--std-root ./std` are written
  as `./...` (the runner normalises with `c.rel(c.abs())`, so no effect on the key).
- Alternative std root (copy without `future/`): `altstd/future/{mod,block_on}.ax -` absence facts; package with an
  empty module file: `e3b0c442...` (correct empty hash, no false `-`).
- Sorted, unique, LF in every probe.

### Runner soundness (check 2), end-to-end adversarial tests (new, `tests/driver/dep_file/qa_cache_e2e*.test`)
Each case builds a private root (std copy + one `modes: interp` run test) and drives the real `tools/axtest.py --root`
with a private `--cache-dir`: run 1 stores, run 2 must hit, then an input changes and run 3 must not be a hit.
- `stdedit` (comment appended to the implicitly loaded prelude): run 3 `hits 0 stored 1` -> OK.
- `newstd` (create `std/future/{mod,block_on}.ax` where the compiler had recorded absence facts): run 3 `hits 0` -> OK.
- `rtread` (program reads `data.txt` of its own test directory at run time): **FAIL** (finding F1).
- G2: `cache_g2.test` passes (superset and exact reasons as in the report); `exact_deps_nondet` covers the prelude in
  the dep list. `IMPLICIT_STD_FILES` seeding verified by reading `StdIndex.nondet_reason`.

### Findings

**F1 (blocking, soundness, caused by activating the exact path) -- false cache hit and missed `--affected`
selection for a file of the test's own directory read at run time.**
- Where: `tools/axtest.py` `CacheGlue.prepare`/`guard_deps` (exact mode keys only the compiler-reported files plus the
  test directory LISTING, not its file contents) and `tools/axtest_affected.py:987-1019` (`grep_ok` drops rule 2a "a
  changed file in the test's directory selects its tests" for every test with an exact entry).
- Expected: ADR-0041 §4 S4 addendum says only tests that read files OUTSIDE their own directory need `cache-inputs:` /
  `nocache:`; superset mode keys the whole test-directory tree. A change of a file in the test's directory must be a
  miss and must be selected by `--affected`.
- Actual (repro, snapshot, private cache dir): a `modes: interp` run test printing `tests/.../data.txt` via
  `std.core.host.open/read` (deterministic bindings -> cacheable): run 1 `STORED 1`, run 2 `HITS 1`, then `data.txt`
  changed to `data-v2`: run 3 `CACHED 1 HITS 1 ... TOTAL 1 PASS 1` while `--no-cache` gives
  `FAIL ... actual: data-v2\n`. Same scenario with the superset compiler (`build-snap-T452/build/axiomc2.exe`, no
  flag): run 3 `MISS 1`, `FAIL` -> correct. `--affected tests/.../data.txt` with the exact entry present selects 0 tests;
  with an empty cache it selects the test via rule 2a. Regression test: `tests/driver/dep_file/qa_cache_e2e_rtread.test`
  (`python tests/driver/dep_file/qa_cache_e2e.py {tmp} rtread {compiler}`), fails now with 3 failures.
- Suggested fix (architect: `tools/axtest.py` is outside this task's `paths:`/`locks:`; add it to the locks of the
  fix round): in exact mode also key the test directory tree (`["tree", tdir]`, as `superset_deps` does, minus std) or
  at least every non-`.ax` file in it, and keep rule 2a (`test: ... is in the test's directory`) for exact entries in
  `--affected`. Existing in-tree example of the pattern: `tests/selfhost/opt/qa_opt_pipeline.ax` reads
  `tests/selfhost/opt/pipeline_input.ax` at run time (currently uncacheable by S4, so not yet hit).

**F2 (acceptance, report) -- the implementation report is incomplete.** `_workspaces/reports/T437b-report.md:159`
still reads `GATE_PLACEHOLDER` under "## Gate (taskgate, snapshot)". Acceptance item 4 asks for the gate result; fill
it in (or drop the section and point to this QA file).

**F3 (acceptance item 2, needs a decision) -- the complete `tests/selfhost` group was not measured.** The criterion
asks for a cold and a warm run of the `tests/selfhost` group; the report measured 3 subgroups (12 ids) and argues from a
static S4 classification that 151/154 ids are uncacheable. The argument is plausible (the gate saw the bundles as
`UNCACHEABLE`), but the criterion is not met as written: either run it in the fix round or have the architect waive it
explicitly in the task file.

### Notes (not blocking)
- `--dep-file=` with an empty value and a dep path in a non-existent directory are both silently ignored (rc 0, no
  message); the runner then stores nothing, so it is safe, but a usage error/warning would be clearer (`--dep-file`
  with no value is already a usage error 2).
- The dep list hashes `pkg/axiom.toml` by re-reading it at write time (probe), not from the bytes the manifest parser
  read; a concurrent edit is caught by the runner's after-run re-hash, so no soundness issue.

### Follow-ups (architect inbox)
- `tools/taskgate.py`: the JSON/Markdown output keeps no per-id failure message or state (FAIL vs TIMEOUT vs CRASH), so
  a load timeout cannot be told from a real failure without a 37-minute re-run; record `state` + first message line per
  failing id.
- The 8 `selfhost/driver` / `selfhost/obj_link_driver` bundles are assert-only on their native legs (WEAK-NATIVE 16 in
  the gate); generators could emit `// stdout:` of a final marker line so taskgate's WEAK-NATIVE check stops blocking
  every task that regenerates them.

VERDICT: FAIL round=0 (superseded by Round 1 below)

## Round 1

Gate model: opus. Re-gate after fix round 1. Implementation report ends `STATUS: COMPLETE round=1`. The snapshot
`build-snap-T437b` was refreshed by the orchestrator (HEAD `7d84ada3` + change set).

### What did not change since round 0 (proof; the 8 selfhost bundle runs are not repeated)
- `build-snap-T437b/build/axiomc2.exe` sha256 `1b79d78ab28ecc60d371b86b635d9783065bf441b491ef0f08fa7d27c4c2f155`, the
  same as in round 0 (mtime 2026-11-13 19:11, before the round-0 verdict at 23:51).
- `compiler/driver/opts.ax` (sha256 prefix `fe2fed3b571118b7`), `compiler/driver/pipeline.ax` (`e36b2134da86b89f`)
  and all 8 bundles (`tests/selfhost/driver/qa_driver_{boundary_edges,cli_and_project,commands_a,commands_b,
  inspect_diff_a,inspect_diff_b}.ax`, `tests/selfhost/obj_link_driver/qa_obj_link_driver_{diff,smoke}.ax`) are
  byte-identical between the main tree and the snapshot, and their mtimes (opts 18:01, pipeline 17:34, bundles
  18:08) all precede the round-0 compiler build (19:11) and verdict (23:51). So no compiler source, bundle or
  generator byte changed in the fix round; the round-0 evidence for the `--dep-file` output, the 36 generator
  `--check` runs and the 8 driver bundle runs stands. I deliberately did NOT re-run the 8 bundles (~37 min each).
  The fix round changed only `tools/axtest.py`, `tools/axtest_affected.py`, `tools/axtest_cache.py` and
  `tools/tests/axtest/{stubcc,test_cache}.py` (plus the report); these are byte-identical between main tree and
  snapshot. Round-0 taskgate JSON kept as `_workspaces/artifacts/taskgate-T437b-r0.json` (main tree).

### F1 -- fixed (verified independently)
Code read: `CacheGlue.guard_deps` now returns `dirlist(tdir)` + `superset_deps(test, with_std=False)` (test dir
tree, input's dir when outside, every `cache-inputs:` path as `tree`/`file?`, ancestor `axiom.toml` probes); these are
hashed before (memo) and after the run and stored in the exact record. `--affected`: rule 2a now applies to exact
entries, new rule 2c selects a test from a changed file at/under one of its `cache-inputs:` paths.

My end-to-end repro with the real compiler (`tests/driver/dep_file/qa_cache_e2e.py <tmp> <case>
build/axiomc2.exe`, snapshot, private root + private cache dir, run 1 store / run 2 hit / change / run 3):

| case | change | run 3 | `--affected` | result |
|---|---|---|---|---|
| rtread | `tests/qa/rt/data.txt` (own dir, run-time read) | hits 0, FAIL 1 | selects | OK |
| rtsub (new) | `tests/qa/rt/in/deep.txt` (subdir of own dir) | hits 0, FAIL 1 | UNMATCHED (see note N1) | OK |
| rtdecl (new) | `data/in.txt` outside, `cache-inputs:` | hits 0, FAIL 1 | selects (rule 2c) | OK |
| rtcreate (new) | `data/later.txt` declared, absent at store, then created | hits 0, FAIL 1 | selects | OK |
| stdunused (new) | `std/core/cmp.ax` edited, not in the dep list | **hits 1**, PASS 1 (exact gain kept) | - | OK |
| stdedit | `std/core/prelude.ax` (loaded) | hits 0, PASS 1, stored 1 | - | OK |
| newstd | `std/future/*` created at absence facts | hits 0, PASS 1 | - | OK |

Stored exact record of `stdunused` (deps): `dirlist std/core, std/future, tests/qa/rt`; `file` for the 6 implicit
std files + the test; `file?` for the 4 ancestor `axiom.toml`; `tree tests/qa/rt` -- no std tree, so the exact gain
is real. Compiler paths like `D:/.../build/../std/core/host.ax` are normalised to repo-relative paths.

Mutation proof that the tests detect the old logic (scratch copies of `tools/`, snapshot untouched):
- mutant A (round-0 `guard_deps`: dirlist + ancestor toml only): `test_cache.ExactRuntimeInputTests` 4 of 7 FAIL
  (own dir, subdir, declared input, declared dir with new file); e2e `rtread`/`rtsub`/`rtdecl`/`rtcreate` all FAIL
  (run 3 `hits 1, pass 1` = the false hit).
- mutant B (rule 2a gated by `grep_ok` again): `test_affected_rule_2a_selects_an_exact_entry` FAILs.
- mutant C (rule 2c `aff.add` removed): the 2 cache-inputs `--affected` tests FAIL.

Further false-hit hunting in the new exact key (no defect caused by the task found):
- The exact key is the superset key minus the std tree plus the compiler-reported files and their directory
  listings. The only input class the superset mode covered and the exact mode does not is an UNDECLARED run-time
  read of a std file the compiler did not load. ADR-0041 S4 already requires `cache-inputs:` for reads outside the
  test directory; `grep -rlE '"[^"]*std/[a-z_]+' tests --include=*.ax` finds no test program naming a std path in a
  string literal. Note N2 (not blocking).
- Undeclared run-time reads of other directories via relative paths are equally unkeyed in both modes (S4 rule,
  pre-existing). env: `AXIOM*`/`AX_*` program env is in the pre-key in both modes; other env/clock reads are caught by
  the S4 nondeterminism scan (unchanged). Path case/`..`: the dep list's `D:/.../build/../std` paths normalise
  correctly (verified in the stored record). A file created at an absent declared path: `file?` -> miss (rtcreate).

### Required runs (snapshot, one at a time, -j 2)
- `python tools/tests/axtest/run_selftests.py` -> `SELFTEST 145 tests, 0 failures, 0 errors` (166 s).
- `python tools/tests/taskgate/run_selftests.py` -> `SELFTEST 44 tests, 0 failures, 0 errors`.
- taskgate (`--no-cache`: the runner files changed, so every round-0 entry is invalid anyway). Change set: the
  round-1 delta (`--changed @_workspaces/artifacts/T437b-r1-changed.txt`: the 5 tool files, my new tests,
  `qa_cache_e2e.py`, the report). `--extra`: all 38 non-selfhost round-0 affected ids (tests/driver/**,
  inspect, modules incl. the whole dep_file group) + both `bundles_current.test` generator checks. The 8 bundles
  are excluded as justified above.
  `python tools/taskgate.py --task T437b --changed @_workspaces/artifacts/T437b-r1-changed.txt --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --no-cache --baseline _workspaces/baseline-failures.txt --json-out _workspaces/artifacts/taskgate-T437b-r1.json --extra <38 ids> selfhost/driver/bundles_current.test selfhost/obj_link_driver/bundles_current.test`

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 44 | 54 | 50 | 4 | 0 | 0 | 0 |
| affected | 17 | 17 | 17 | 0 | 0 | 0 | 0 |
| smoke | 30 | 47 | 45 | 2 | 0 | 0 | 0 |
| **total (dedup)** | 71 | 98 | 92 | 6 | 0 | 0 | 0 |

  - `TASKGATE T437b exit=0`, wall 5 min 15 s. `BASELINE OK`. Failing ids: `driver/build_emit_obj.test` (baseline
    T431), `hir/basic.ax`, `resolve/simple.ax` (baseline T434), `modules/prelude_implicit` (baseline T432) -- all in
    `_workspaces/baseline-failures.txt`, none outside.
  - Derivation audited: all 17 `driver/dep_file/*` tests via rule 2c (`cache-inputs: tests/driver/dep_file`), tool
    self-tests `tools/tests/{axtest,gatecheck,taskgate}` (axtest 145/0, gatecheck 39/0, taskgate 44/0); report no-op;
    UNMATCHED none; no UNRESOLVED/MAP-NOTE/DEFERRED; cache line `miss 42, uncacheable 29, stored 39, dep_source exact`,
    no CACHE-MISMATCH. WEAK-NATIVE 0 in own/changed tests.
  - Smoke seed 2830002601 (always `run/str/hello.ax` = Xin chào thế giới, `ui/typeck/type_unknown.ax`,
    `diff/002-arithmetic.ax`; one pick per group, list in the taskgate JSON).
  - archcheck: 229 files scanned, 0 violations.
- All 17 `tests/driver/dep_file` tests (incl. the 7 `qa_cache_e2e_*`) PASS inside that run.
- Native evidence: my new tests are `cmd:` tests with `exit: 0` + `stdout-contains: qa-cache-e2e <case>: OK`; the
  mutation runs above show they FAIL against the old logic (live).

### F2 -- fixed
`grep -c GATE_PLACEHOLDER _workspaces/reports/T437b-report.md` -> 0; the "## Gate" section summarises round 0 and points
to this file. The "Fix round 1" claims (guard_deps = superset minus std + dirlist, before/after hashing, rule 2a for
exact entries, rule 2c) match the code diff. The deferred `--dep-file=` empty-value note is recorded in the
architect inbox (acceptable, round-0 note only).

### F3
Waived by the orchestrator (round-0 decision); not re-checked.

### `taskctl.py changes T437b`
Before this file lists my 4 new tests: `REFUSED 4 ... qa_cache_e2e_{rtcreate,rtdecl,rtsub,stdunused}.test` (only my
new files); they are listed below, which resolves it. `WARN _workspaces/architect-inbox.txt` outside paths/locks:
accepted by the orchestrator (implementer's inbox lines).

### Notes / follow-ups (architect; not caused by this task)
- N1: `--affected` rule 2a maps a changed file to the tests of its own directory only (`Corpus.owner_ids` ->
  `ids_in_dir_of`, T437a, unchanged here): a data file in a test-less subdirectory of a test directory
  (`tests/x/in/deep.txt`) selects nothing and is reported `UNMATCHED` (visible, not silent). The cache side is sound
  (tree key). Suggest: walk up to the nearest ancestor directory with tests. `qa_cache_e2e_rtsub` asserts
  "selected or UNMATCHED" and will keep passing when this is improved.
- N2: the exact key drops the std tree; a test that reads a std file at run time without declaring it would now
  false-hit where the superset key did not. No such test exists today (grep above); S4 already requires the
  declaration. Consider stating it in ADR-0041 S4 / axiom-testing.

## Files changed
- tests/driver/dep_file/qa_cache_e2e.py
- tests/driver/dep_file/qa_cache_e2e_rtread.test
- tests/driver/dep_file/qa_cache_e2e_stdedit.test
- tests/driver/dep_file/qa_cache_e2e_newstd.test
- tests/driver/dep_file/qa_cache_e2e_rtsub.test
- tests/driver/dep_file/qa_cache_e2e_rtdecl.test
- tests/driver/dep_file/qa_cache_e2e_rtcreate.test
- tests/driver/dep_file/qa_cache_e2e_stdunused.test

VERDICT: PASS round=1
