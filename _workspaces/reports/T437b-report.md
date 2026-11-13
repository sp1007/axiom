# T437b — Compiler `--dep-file` (exact per-test inputs) for the axtest cache and `--affected`; selfhost bundle regeneration

Owner: axiom-stdlib (round 0). Spec: ADR-0041 §4 S2 + §6, ADR-0042 §5 (G2), T437a report/QA.
Build/test snapshot: `build-snap-T437b` (HEAD 349083e + this change set); compiler
`build-snap-T437b/build/axiomc2.exe` built by `tools/build_axiomc.py --out build`
(sha256 `1b79d78ab28ecc60d371b86b635d9783065bf441b491ef0f08fa7d27c4c2f155`; stage-1 211 s, stage-2 -O1 3988 s on
the loaded shared machine).

## Summary
- `axiomc build|run|check|inspect --dep-file=<path>` (also `--dep-file <path>`) writes every input the source stage
  consulted: loaded files with the sha256 of the bytes read, probed-and-absent paths (`-`) and directories whose
  listing was used (`dir`). Written right after the source stage and again when the command ends, also when the
  compile fails. Implemented in `compiler/driver/opts.ax` (new section 10: probe log on `Project`, SHA-256,
  writer) and `compiler/driver/pipeline.ax` (future lang-item probes, write points, object/`.mir`/`--rt-obj`
  inputs). `compiler/source` needed no change (the file list lives in the driver's `Project`).
- Runner (`tools/axtest_cache.py`, `tools/axtest_affected.py`; `tools/axtest.py` changed only in fix round 1):
  the real format is mapped onto T437a's exact path; absence facts and listed directories are part of the key;
  `--affected` rule 1 matches files created at absent paths and inside listed directories; G2 closed in both modes.
- 10 new tests in `tests/driver/dep_file` (format, multi-file package, std import, prelude, absence fact, failing
  compile, missing input, every command, object input, G2 in both modes, runner vocabulary): all PASS.
- Bundles: only `selfhost/driver` (6 bundles) and `selfhost/obj_link_driver` (2 bundles) embed the edited modules.
  Regenerated with their generators; then `--check` of **all 36 generators**: 36 x `differs=0`.

## Dependency-file format (compiler/driver/opts.ax section 10)
```
<path> <sha256>     a file the compiler loaded (hash of the bytes it read)
<path> -            a path it probed and found absent (absence fact)
<dir>/ dir          a directory whose listing it used
```
One entry per line, LF, sorted by path bytes, unique paths (a loaded file wins over a probe of the same path).
Example (`check` of a package directory):
```
std/core/option.ax f612f0ca...
std/core/prelude.ax 26f8dd43...
std/core/result.ax ee0e2b21...
std/future/block_on.ax a6585356...
std/future/mod.ax 11019dad...
tests/driver/dep_file/fixtures/pkg/ dir
tests/driver/dep_file/fixtures/pkg/axiom.toml 91edc966...
tests/driver/dep_file/fixtures/pkg/src/ dir
tests/driver/dep_file/fixtures/pkg/src/main.ax 905e9834...
tests/driver/dep_file/fixtures/pkg/src/util/ dir
tests/driver/dep_file/fixtures/pkg/src/util/calc.ax 7e0e63a7...
tests/driver/dep_file/fixtures/pkg/src/util/text.ax a39be25c...
```
What is recorded (every file access of the source stage was audited: `project_discover`,
`find_src_package_root`, `scan_package_dir_recursive`, `project_append_std_core_files`,
`project_append_std_host_if_needed`, `pipe_append_std_future_files_if_needed`, `project_add_extra_ax_file`,
`manifest_read_file`, `pipeline_stage_source`; nothing after the source stage reads source files):
- project files (root, package/module files, extra `.ax` inputs of `build`, std core option/result/prelude,
  `std/core/host.ax` when the program text says `host`, `std/future/{mod,block_on}.ax`), hashed over the exact bytes
  the source stage read;
- probes: the input path, every `<cand>/axiom.toml` candidate of the `/src/` package lookup (absent ones become
  `-`: creating that file turns the program into a package), the package `axiom.toml`, every std implicit-file
  existence check (`std/core/host.ax -` etc. when missing), the package root listing (`src/` lookup) and every
  scanned package directory;
- further inputs of the command: a `.mir` input, positional non-`.ax` arguments of `build` (object/archive
  inputs), `--rt-obj`.
- Not listed (inputs of the invocation itself, already in the runner's key): the choice of the std root
  (`--std-root`, `AXIOM_STD`, executable location), libraries resolved by the linker through `-L`/`-l`
  (`cmd:` tests only, which need `cache-inputs:` anyway).

## Decisions (owner-delegated; rationale)
- **D1 Paths as opened, no `<std>/` prefix.** The task allows "relative to the repo root or `<std>/`". The compiler
  writes paths exactly as it opened them (relative to its working directory, which is the repository root for the
  runner; `std/core/prelude.ax` under `--std-root std`; absolute when given absolute). Reason: T437a's exact path in
  `tools/axtest.py` resolves dependency paths against the root (`c.rel(c.abs(path))`), and `tools/axtest.py` is
  outside this task's paths/locks; a `<std>/` form would have needed a runner change there for no gain (the std
  root is part of the key through `--std-root`).
- **D2 Absence facts and listings in the runner's existing vocabulary.** `parse_dep_file` (axtest_cache.py) maps
  `<path> -` to `(path, "absent")` (the runner re-hashes a missing file to `absent`, so a created file is a miss
  and a file appearing during the run stores nothing) and `<dir>/ dir` to the absent sentinel
  `<dir>/.axtest-dirlist`, whose parent listing (`dirlist`) the runner already keys for every dependency. No change
  to `tools/axtest.py` was needed. `Hasher.dirlist` now marks subdirectories with a trailing `/` (a file replaced
  by a directory of the same name changes a package scan).
- **D3 Written twice.** After the source stage (so `run --interp` of a program that exits the process still leaves
  the list) and at the end of each command (covers commands whose source stage never ran).
- **D4 SHA-256 in the driver.** No sha256 exists in the compiler's module set (`std.pkg.archive` is not in the
  axiomc bundle and uses intrinsics axiom0 may not provide); a 120-line FIPS 180-4 implementation with 32-bit words
  held in `u64` and masked (no wrapping intrinsics, compiles with axiom0 and axiomc) and the round constants as a
  `const` table. Verified against Python `hashlib` on every listed file by the tests.
- **D5 Code placement.** In `compiler/driver/opts.ax` (which owns `Project` and the host file helpers) rather than
  a new module, so no generator module list (FULL_MODULES, bundle_common order) had to change.
- **D6 G2 list in one place.** `IMPLICIT_STD_FILES` in `tools/axtest_cache.py` names the implicitly loaded std
  files; `tests/driver/dep_file/prelude.test` fails when the compiler's real `--dep-file` output differs from it
  (minus `core/host.ax`, which is conditional and listed unconditionally in superset mode).
- **D7 Bundle test subset.** Per the resource rule, one bundle per regenerated group plus both generator manifests
  (see Gate).

## G2 (never-cache scan covers the implicitly loaded files)
- Exact mode: `exact_deps_nondet` scans every std file of the dep list; the prelude, option/result, host and the
  future modules are in the list (asserted by `prelude.test` / `std_import.test`).
- Superset mode: `StdIndex.nondet_reason` seeds the traversal with `IMPLICIT_STD_FILES` (their own bindings and
  their `std.a.b` references). Today none of them uses a nondeterministic leaf (an empty program and a heap-only
  program stay cacheable).
- Self-test `tests/driver/dep_file/cache_g2.test` (scratch std copy in the test's temp dir): prelude + `pub fn
  qa_now() -> u64 { monotonic_ns() }`, program calling `qa_now()` with no `std.`/`host` text:
  `superset='implicitly loaded std/core/prelude.ax uses host binding monotonic_ns'`,
  `exact='depends on .../std_poisoned/core/prelude.ax, which uses host binding monotonic_ns'`; control copy:
  `superset=None exact=None`.

## Tests (`tests/driver/dep_file`, `cmd:` manifests with `cache-inputs:`)
| id | checks |
|---|---|
| `prelude.test` | no-`std.` program: exactly the input + implicit std files with hashes; equals `IMPLICIT_STD_FILES` |
| `std_import.test` | `use std.core.host...`: `std/core/host.ax` listed too |
| `package.test` | multi-file package dir: `axiom.toml`, 3 module files, 3 `dir` listings |
| `src_file.test` | `pkg/src/main.ax` as input: the `axiom.toml` probe finds the package, same list |
| `absent.test` | file under `src/` without manifest: `.../nopkg/axiom.toml -` |
| `fail.test` | type error: list still written; missing input: `<input> -` only |
| `commands.test` | `run`, `inspect --emit=tokens`, `build`, separate-arg form: same list; object input of `build` listed with its hash |
| `format.test` | `--dep-file` without value = usage error 2; no flag = nothing written |
| `cache_g2.test` | G2 in both modes (above) |
| `cache_vocab.test` | `parse_dep_file` mapping, malformed lines rejected, `dep_matches_change` |
Every case also checks LF only, sorted unique paths, `/` separators, `dir` <-> trailing `/`, and that the runner's
`parse_dep_file` accepts the file. Run: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build -j 2
--no-cache driver/dep_file/` -> `TOTAL 10 PASS 10` (99.8 s), `STORED 10`. Mutation: the `prelude` case with the
old compiler (`build-snap-T452/build/axiomc2.exe`, no flag) -> `FAIL: prelude: no dependency file written`.

## Generators and bundles
- `--check` of all 36 generators before regeneration: `tests/selfhost/driver/gen_driver_tests.py` differs=12 (6
  bundles, each reported twice), `tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py` differs=4 (2
  bundles), 34 generators differs=0.
- Regenerated with `python tests/selfhost/driver/gen_driver_tests.py` and
  `python tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py` (no axiom0 needed without
  `--refresh-goldens`). The diff of every regenerated bundle contains only the embedded opts/pipeline changes.
- `--check` of all 36 generators after regeneration: **36 x differs=0** (scratch log `gens_check2.log`).
- Bundle runs in the snapshot (`-j 2 --no-cache`, 44.6 min wall):
  `selfhost/driver/qa_driver_commands_a.ax` interp/native/native-O1 PASS,
  `selfhost/driver/bundles_current.test` PASS, `selfhost/obj_link_driver/bundles_current.test` PASS,
  `selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax` FAIL exit 101 in all 3 modes — a baseline id
  (`_workspaces/baseline-failures.txt` line 115, T442 "obj_link_driver bundles panic, exit 101").

## Measurements (build-snap-T437b, same binary, shared cache)
- **Smoke set** (`--smoke --seed 437`, 31 ids / 50 results, `-j 2`):
  run 1 wall 56 s, `CACHED 0 HITS 0 MISS 21 UNCACHEABLE 10 STORED 19 dep_source=exact`, failing
  `hir/basic.ax resolve/R01_basic.ax` (baseline, `BASELINE OK`);
  run 2 wall 28 s, `CACHED 38 HITS 19 MISS 2 UNCACHEABLE 10 STORED 0`: every cacheable id CACHED, the 10
  uncacheable ids ran, the 2 misses are the failing baseline ids (never stored), failing set identical.
  Cache entries show `dep_source: exact`, origin `snapshot` (e.g. `modules/nested`: 7 files, 3 listing sentinels,
  6 `dirlist`, 3 ancestor `axiom.toml` absence facts).
- **tests/selfhost**: a static S4 classification of the group (154 `.ax` ids) finds only 3 cacheable ids
  (`selfhost/intrinsics/qa_intrinsic_seams.ax`, `qa_unreachable_abort.ax`, `selfhost/kernel/hash_native.ax`); the
  other 151 bundles embed thread/timer/FFI bindings and are re-run in every mode by design (S4), so a warm run of
  the whole group costs the same as a cold one (hours at -j 2). Measured instead on the subgroups that hold all 3
  cacheable ids plus uncacheable bundles (`selfhost/intrinsics/ selfhost/kernel/ selfhost/source/`, 12 ids / 30
  results): run 1 25 s `HITS 1 MISS 2 UNCACHEABLE 9 STORED 1`; run 2 27 s `HITS 2 MISS 1 STORED 1`; run 3 23 s
  `CACHED 9 HITS 3 MISS 0 UNCACHEABLE 9 STORED 0`; all runs `TOTAL 30 PASS 30`. The run-1 store skip of
  `selfhost/kernel/hash_native.ax` is the S2 guard working: the sibling `hash_native_current.test` (a Python
  generator) created `tests/selfhost/kernel/__pycache__/` during the run (20:09:57), which changed the test
  directory listing, so nothing was stored; from then on the key is stable.
- **std-only scenario** (scratch edit in the snapshot, restored after each run, `git status` clean):
  comment appended to `std/text/utf8.ax` (not implicitly loaded): smoke run `HITS 19 MISS 2 STORED 0` — **0 of 19
  cacheable ids re-ran**; the deps-index shows 0 of 21 exact lists contain the file. In superset mode the key
  holds the whole std tree, so all 19 would miss (T437a measurement). Comment appended to `std/core/prelude.ax`
  (implicit): `HITS 0 MISS 21 STORED 19` — every test re-ran, as all 21 exact lists contain the prelude.

## Gate (taskgate, snapshot)
The implementation agent does not run the gate (QA does). Round 0 gate by QA (`_workspaces/reports/T437b-qa.md`,
`--no-cache`, snapshot `build-snap-T437b`): own 13 / affected 48 / smoke 30 ids, `TOTAL 117 PASS 100 FAIL 17`;
failing ids inside the baseline except `driver/dep_file/qa_cache_e2e_rtread.test` (finding F1, fixed in round 1
below) and `selfhost/driver/qa_driver_commands_a.ax` (load timeout; PASS 3/3 when re-run alone); archcheck clean;
tool self-tests 138/0 and 44/0. What round 1 ran is listed under "Fix round 1".

## Self-tests and checks
- `python tools/tests/axtest/run_selftests.py` -> `SELFTEST 138 tests, 0 failures, 0 errors` (a first run had 1
  failure in the temp-dir leak check: an `axtest-*` directory from another agent's concurrent axtest run in the
  shared `%TEMP%`; rerun clean).
- `python tools/tests/taskgate/run_selftests.py` -> `SELFTEST 44 tests, 0 failures, 0 errors`.
- `python tools/archcheck.py` -> 229 files, 0 violations; `python tools/axtest_affected.py --check-map` ->
  `MAP-CHECK OK`.
- `axiom0 check` of the whole axiomc bundle: 0 errors (two new `AX_NAME_SHADOW_MODULE` warnings from `len`
  parameters were removed by renaming them `byte_len`).

## Harness follow-up (for the architect; exact text)
For `.claude/skills/axiom-testing/SKILL.md`, runner section, add:
> `axiomc <cmd> --dep-file=<path>` lists every input of a compile (`<path> <sha256>` loaded, `<path> -` probed and
> absent, `<dir>/ dir` listing used; format in `compiler/driver/opts.ax` section 10). The cache keys on it
> (`dep_source=exact`); a new std file or loaded-module location is a cache miss only for tests that loaded or
> probed it. A file that the compiler starts loading implicitly (like the prelude) must be added to
> `IMPLICIT_STD_FILES` in `tools/axtest_cache.py` (`tests/driver/dep_file/prelude.test` fails otherwise).

## Follow-ups
- Architect: the `tests/selfhost` group is 151/154 uncacheable by S4 (bundles embed thread/timer/FFI bindings), so
  the cache cannot shorten it; a split of bundles into deterministic cases (or `nocache:`-free interp twins) is the
  lever if selfhost cost matters.
- Minor (no action needed): for `build` of a package directory the input directory itself is also listed as a
  positional "further input" (`<dir> -`, since it is not a regular file); harmless (a stricter absence fact).
- `--dep-file` is not in `axiomc --help`/`--features` (`tests/driver/help.test` compares the help text; the runner
  probes the flag instead). Add both in a later driver task if wanted.

## Fix round 1
QA verdict `FAIL round=0` (`T437b-qa.md`); the orchestrator added `tools/axtest.py` and `tools/tests/axtest` to the
locks.
- **F1 (false cache hit / missed `--affected` for run-time reads of the test's own directory): fixed.**
  - `tools/axtest.py` `CacheGlue.guard_deps`: exact-mode entries now key the same run-time inputs as the superset
    mode minus the std root: the test directory **tree** (contents of every file, subdirectories included), the
    input's directory when it lies outside the test directory, every `cache-inputs:` path (file or tree) and the
    ancestor `axiom.toml` probes, plus the test directory listing. They are hashed before the run (memoised, as in
    superset mode) and again after it (S2: any change stores nothing), and are stored in the record's deps, so a
    later change is a miss. The exact gain is kept: only the std part of the key is exact (a std file the compiler
    did not load, or a file of another test directory, is still a hit).
  - `tools/axtest_affected.py`: rule 2a ("a changed file in the test's directory selects its tests") applies to
    tests with an exact entry too. New rule 2c: a changed file at or under a `cache-inputs:` path selects the test,
    wherever the path lies (it was not selected in either mode before); such a file is no longer reported
    UNMATCHED.
  - S1-S8 re-check in exact mode: S1 expectation files / env / argv are mode-independent (`pre_material`); S2 the
    guard is re-hashed after the run; S3 unchanged; S4 `nocache:`, `requires:`, `xfail:` and the binding scan run
    before the mode is chosen (exact mode never sees them), `cache-inputs:` was the hole (not keyed in exact mode)
    and is now keyed; reads outside the test directory without `cache-inputs:` are outside S4 by the ADR-0042 §5
    addendum; S5-S8 do not depend on the dependency mode.
  - Unit tests (`tools/tests/axtest/test_cache.py`, class `ExactRuntimeInputTests`, 7 tests; stub op `//@ cat
    FILE` added to `stubcc.py`): run-time read in the test directory and in a subdirectory (store, hit, change ->
    FAIL not cached, `--no-cache` FAIL, record holds `["tree", "tests/run/rt"]`); declared `cache-inputs:` file
    outside the directory (miss + `--affected` selects); declared directory gains a new file (miss + selects);
    `--affected` rule 2a selects a test with an exact entry and not a test of another directory; `nocache:` never
    stored in exact mode; a change in another test directory is still a hit. Mutation: with the round-0 guard and
    rule 2a restored in a scratch copy of the runner, 5 of the 7 fail (the 2 that pass are the unchanged
    behaviours).
- **F2:** the Gate section above is filled in; this section added.
- **F3 (full `tests/selfhost` cold/warm measurement): waived by the orchestrator** (task file Scope, 2026-11-13:
  ~40 h cost, 151 of 154 ids uncacheable, the periodic full run covers it). Not run; the 3-subgroup measurement
  above stands.
- **Minor `--dep-file=` empty value / missing directory: deferred**, not fixed. A change to `compiler/driver/opts.ax`
  needs a stage-2 -O1 rebuild (~1 h on this machine), regeneration of the 8 driver bundles and their re-run in the
  gate (~37 min each) while another gate runs in parallel; the runner already stores nothing when the list is
  missing (safe). Recorded in `_workspaces/architect-inbox.txt` for the next driver task. Compiler sources are
  unchanged in this round, so `build-snap-T437b/build/axiomc2.exe` (sha256 `1b79d78a...c2f155`) was not rebuilt and
  no bundle or generator changed.
- Architect inbox: appended the two QA follow-ups (taskgate per-id state + first message; WEAK-NATIVE assert-only
  driver bundles) and the deferred `--dep-file=` item.
- Runs (one at a time, the main tree for tool self-tests, the snapshot with the changed tool files copied in for
  the compiler tests):
  - `python tools/tests/axtest/run_selftests.py` -> `SELFTEST 145 tests, 0 failures, 0 errors`.
  - `python tools/tests/taskgate/run_selftests.py` -> `SELFTEST 44 tests, 0 failures, 0 errors`.
  - snapshot: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build -j 2 --no-cache driver/dep_file/`
    -> `TOTAL 13 PASS 13` (the 10 own tests + QA's `qa_cache_e2e_{rtread,stdedit,newstd}`), `STORED 13
    dep_source=exact`.
  - snapshot: `python tests/driver/dep_file/qa_cache_e2e.py <tmp> rtread build/axiomc2.exe` -> run 1 stored, run 2
    `hits 1`, run 3 after the data change `hits 0 fail 1`, `--affected` selects the test: `qa-cache-e2e rtread: OK`.
  - `python tools/archcheck.py` -> 229 files, 0 violations; `python tools/axtest_affected.py --check-map` ->
    `MAP-CHECK OK`.

## Files changed
- tools/axtest.py
- tools/tests/axtest/stubcc.py
- tools/tests/axtest/test_cache.py
- _workspaces/architect-inbox.txt
- compiler/driver/opts.ax
- compiler/driver/pipeline.ax
- tools/axtest_cache.py
- tools/axtest_affected.py
- tests/driver/dep_file/absent.test
- tests/driver/dep_file/cache_g2.test
- tests/driver/dep_file/cache_vocab.test
- tests/driver/dep_file/check_cache_rules.py
- tests/driver/dep_file/check_dep_file.py
- tests/driver/dep_file/commands.test
- tests/driver/dep_file/fail.test
- tests/driver/dep_file/format.test
- tests/driver/dep_file/package.test
- tests/driver/dep_file/prelude.test
- tests/driver/dep_file/src_file.test
- tests/driver/dep_file/std_import.test
- tests/driver/dep_file/fixtures/bad.ax
- tests/driver/dep_file/fixtures/plain.ax
- tests/driver/dep_file/fixtures/uses_std.ax
- tests/driver/dep_file/fixtures/nopkg/src/main.ax
- tests/driver/dep_file/fixtures/pkg/axiom.toml
- tests/driver/dep_file/fixtures/pkg/src/main.ax
- tests/driver/dep_file/fixtures/pkg/src/util/calc.ax
- tests/driver/dep_file/fixtures/pkg/src/util/text.ax
- tests/selfhost/driver/qa_driver_boundary_edges.ax
- tests/selfhost/driver/qa_driver_cli_and_project.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- _workspaces/reports/T437b-report.md

STATUS: COMPLETE round=1
