# T423h QA gate

## Round 0

Subject: `build-snap-T423h/` at HEAD `67764a6d` plus the task change set. Gate model: sonnet. Machine shared; `-j 2` throughout.

### Setup and change set
- `taskctl.py changes T423h`: 34 files staged, no `REFUSED` line. The two "ignored/not stageable" lines come from the report's prose under `## Files changed` (`tests/run/host/**`, `// stdout`) and are harmless. No selfhost bundle is listed.
- The snapshot had been created at an older HEAD than the engineer's own build (report sha `5d417da8…`). I rebuilt the compiler inside the snapshot with `python tools/build_axiomc.py --out build --root . --stage 2` (5 min): STAGE1/2/3 OK, `FIXED-POINT (O1) OK` (sha256 `f32d29dc…`), `STAGE0-GUARD OK`. All results below use this compiler.
- For before/after comparisons I used the HEAD stage-2 compiler from the compiler cache (`_workspaces/artifacts/compiler-cache/axiomc2_O1_e31647f37cf9de14.exe`, copied to `build/head.exe` in the snapshot and removed afterwards).

### Gate scope run (taskgate)
`python tools/taskgate.py --task T423h --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --extra <my 4 tests> --json-out _workspaces/artifacts/taskgate-T423h.json` (log `_workspaces/T423h_qa_taskgate.log`):
- `TASKGATE T423h exit=0`; axtest `TOTAL 409 PASS 407 FAIL 0 SKIP 2 XFAIL 0`; failing ids: none; BASELINE OK; archcheck clean (232 files, 0 violations); no UNMATCHED, UNRESOLVED, MAP-NOTE or DEFERRED entries; cache line: CACHED 0, mismatch none.
- Parts: own 29 ids/72 results, affected 209 ids/365 results, smoke 31 ids/52 results. Groups with ids: modules 22, run 20, driver 34, selfhost 80 (bundle groups embedding `compiler.diag.code`, `compiler/driver`), ui 51, std 1, conformance 6, unit 2, inspect 1, plus one smoke pick per other group.
- Affected-set derivation as printed by the tool: `compiler/diag` -> diag/UX2/explain/ui groups; `compiler/driver` -> `tests/driver`, `tests/modules`, `tests/inspect`, `tests/selfhost/driver`; exact dependency files for `run/host`; `cache-inputs` for the std_on_demand and host fixtures. `run/diag_ux2/{diag_ux2.test,qa_t497_code.test}` (explain count 39) PASS.
- WEAK-NATIVE: 3 in the whole run, 0 in the task's own and changed tests.
- Smoke always-included cases pass: `run/str/hello.ax` (Xin chào thế giới), `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`, archcheck.
- No load-related timeouts.

### Extra runs (focus list)
- `modules/std_on_demand` with my tests: TOTAL 39 PASS 36 FAIL 3 (the 3 are my `qa_parent_provided_child_module.ax`, finding F1; everything else passes in interp, native and native-O1; WEAK-NATIVE 0).
- `std/core/ std/alloc/ std/arena/ run/opt_escape std/thread std/channel` (legacy in-file `__ax_host_*` definitions, no duplicate symbols): TOTAL 109 PASS 109, `--no-cache`.
- Sample of 12 more legacy-workaround tests (`conformance/p15`, `conformance/p11/*`, `std/fiber/*`, `std/async/*`): TOTAL 34 PASS 34.
- `driver` and `modules` groups are in the taskgate affected set (all pass); `run/host` all pass.

### ADR-0048 conformance (focus 1-3)
1. Index from `module` headers: `std.asyn.waker` in `std/async/waker.ax` resolves (`asyn_header_not_path.ax`); `use std.process.exit` loads `std/process/process.ax` and its `use`s transitively (`transitive_process_exit.ax`, dep-file golden). `qa_time_native_provider.ax` (mine): `std.time` on demand, provider reached through the loaded module, native prints `time ok 1500 1`, exit 0.
2. Program-provided wins: `bundle_inline_wins.ax` (inline `module std.core.mem` with an item std's mem lacks) passes in three modes; `qa_shadow_std_process.ax` (mine; inline `std.process` with its own `exit`) exits 9 with the shadow output natively and in interp, on HEAD and new; duplicate std module: `duplicate_header.test` gives `AX_DRIVER_DUPLICATE_STD_MODULE` (170) naming both files in index order.
   - **Deviation: F1 below** (a provided parent module swallows a child module import).
3. Native providers: `host_exit_native` exits 3 with `exiting\n`; `host_args_count_native` prints `args 3`, exit 3; `qa_host_module_qualified.ax` (mine: `use std.core.host` + `host.exit(200)`) exit 200; `qa_host_two_providers.ax` (mine: `args_count`+`exit` in the process provider plus `heap_alloc/free` in the heap provider, each added once) prints `n=2 exiting`, exit 22; `run/host/heap/provider_native.ax` sum 136. HEAD fails all of these natively with `AX_LINK_UNDEFINED_SYMBOL` (verified with the HEAD compiler).
4. obj/lib outputs: `build --emit=obj` and `--kind=lib` of the `exit(3)` program are byte-for-size identical to HEAD and keep `__ax_host_exit` undefined (`objdump -t`); only exe/dll get providers. ADR-0048 §3 says "for a native build" and never mentions obj/lib. The choice (no duplicate definitions at the user's final link) is sensible and unchanged from HEAD; **note for the architect**: add one sentence to the ADR.
5. Looser provider-skip rule vs ADR §3: a provider is skipped when the program defines any `__ax_host_*` of that module in any module. Judged acceptable because it is documented (report decision 1 + Follow-up 2), keeps ~50 legacy files linking (verified above), and is no worse than HEAD. Limitation reproduced: a program that defines only `__ax_host_exit` itself and also uses `args_count` fails to link `__ax_host_args_count` (same failure at HEAD). The strict ADR rule would instead create duplicate symbols for those programs. Condition: the architect should file the task that removes the legacy workaround definitions and then tightens the rule, with an id (Follow-up 2 has no task id).

### Determinism and compile time (focus 4-5)
- Two builds of `transitive_process_exit.ax`: byte-identical exe; two `--dep-file` runs identical. Bundled tests (`std/alloc/qa_vec.ax`, `run/concurrency/tls/qa_tls_borrow_mut_in_shared_panic.ax`, `run/basic/t117_shifts.ax`): dep-file AND exe byte-identical between HEAD and new compilers.
- min of 5 wall times (head -> new): check no-`use std` `t117_shifts` 0.051 -> 0.049 s; build no-`use std` 0.042 -> 0.045 s; build bundled TLS test 0.601 -> 0.595 s; build bundled `qa_vec` 0.116 -> 0.118 s. On-demand programs (new only, HEAD cannot compile them): check `mem_swap` 0.072 s, build `std.time` 0.080 s, build `std.process.exit` 0.139 s. No regression.

### Native evidence (step 4a)
- New/touched native tests all check observable results (`exit:` non-zero or exact `stdout:`); taskgate WEAK-NATIVE 0 for own/changed.
- Mutation proof, in the snapshot only, restored afterwards (`cmp` against the main tree OK): `host_exit_native.ax` `// exit: 3` -> `4`: FAIL in interp, native and native-O1 ("exit code 3, expected 4"); `// stdout: exiting\n` -> `exiting2`: FAIL in all modes with the byte diff; restored: PASS 3/3.
- HEAD compiler on the new tests: `axtest` with `build/head.exe` TOTAL 18 PASS 4 FAIL 14 (native `AX_LINK_UNDEFINED_SYMBOL`, interp/native `AX_NAME_UNRESOLVED_IMPORT`).
- `std/core/qa_driver_std_discovery.ax` keeps its id, is now a positive run test (`hash.hash64` of `a` and `abc` vs the AXH64 vectors, `// stdout: hash ok a abc\n`, three modes); it was in the smoke set and passes.
- `tests/run/host/**` workarounds removed; the five formerly weak tests now check a stdout marker; `native_undefined_symbol.test` uses a provider-less fixture std root and still checks the link error.

### Spec / scope checks
- `compiler/diag/code.ax` 170 is unique and registered (name and default message). No `explain` entry (report decision 6, caused by the hard-coded count 39 in `diag_ux2` probes outside the task's paths): acceptable, follow-up for the owner of those probes.
- No `bootstrap/axiom0`, `spec/` or `docs/` edits; no shared-file violation (`tools/axtest.py`, CMake, pipeline-owner files untouched; `compiler/driver/pipeline.ax` is in the task's paths).
- Cache note (non-blocking): files read only for their header are not listed in the dep-file (ADR §4 wording), so editing the header of a std file that was not loaded does not invalidate cached results that depended on the index (e.g. an unresolved-import test). ADR text allows it; mention for the cache owner.

### Findings
- **F1 (FAIL, MAJOR)**: `compiler/driver/pipeline.ax` `pipe_std_resolve_use`, the "module itself or the module of an imported item is present" fast path (`parent` check, ~line 1275 of the snapshot file). When the program provides a module `P` (e.g. an inline bundle `module std.sync`), a use path `P.child` that names a different, not provided std module (`use std.sync.once`, a module import) returns early, so `std/sync/once.ax` is never loaded and the resolver reports `AX_NAME_UNRESOLVED_IMPORT`. ADR-0048 §2 requires the longest module path that prefixes the use path (`std.sync.once`) to be loaded unless that exact module is provided. Repro: `tests/modules/std_on_demand/qa_parent_provided_child_module.ax` (3 modes fail: interp exit 1 `AX_NAME_UNRESOLVED_IMPORT`, native and native-O1 build failed). With the equivalent bundle that inlines `std/sync/once.ax` the program prints `marker 5 once ok`, exit 5, natively and in interp, so the test is correct once fixed. Suggested fix: take the shortcut only when the path itself is provided; otherwise run the index lookup (the scan is ~20 ms and only happens for use paths not answered exactly), and treat an item import as before (the longest index prefix is then the parent module, already provided, so nothing is loaded).

### Tests added (main tree, byte-identical in the snapshot)
## Files changed
- tests/modules/std_on_demand/qa_time_native_provider.ax
- tests/modules/std_on_demand/qa_shadow_std_process.ax
- tests/modules/std_on_demand/qa_host_module_qualified.ax
- tests/modules/std_on_demand/qa_host_two_providers.ax
- tests/modules/std_on_demand/qa_parent_provided_child_module.ax

(I did not rerun `taskctl.py snapshot` after adding them; they were copied to the snapshot and verified with `cmp`. The engineer's next snapshot refresh picks them up from the main tree.)

### Follow-ups for the architect
1. (pre-existing compiler bug, not T423h) Type-checking is order dependent for generic std modules: `std/alloc/vec.ax` loaded after the main module fails with `AX_TYPE_MISMATCH` at `vec.ax:44` (`Vec { … }` returned as `-> Vec`), at HEAD too. Repro at HEAD: a file starting with the user program (`use std.alloc.vec.Vec` …) followed by `module std.alloc.vec` + the body of `std/alloc/vec.ax` fails; the same text with the std module first passes. On-demand loading appends std modules after user files, so `use std.alloc.vec.Vec` from a user program does not compile yet. A fix task is needed before std collections can be used on demand; I replaced my Vec test by the `std.time` test.
2. File the task that removes the legacy `__ax_host_*` definitions from ~50 test files and then tightens the provider-skip rule (report Follow-up 2); add the obj/lib sentence to ADR-0048 §3.
3. `AX_DRIVER_DUPLICATE_STD_MODULE` explain entry + `diag_ux2` probe count update (report Follow-up 1).
4. Cache: header-only std reads are not dependencies (see above).

VERDICT: FAIL round=0

## Round 1

Subject: `build-snap-T423h/` refreshed onto HEAD `48f3a0ade91f` (via `taskctl.py snapshot T423h`, 36 generators / 60 selfhost bundle files regenerated cleanly) plus T423h's round-1 change set and QA's round-1 adversarial test. Machine shared; `-j 2` throughout.

### Build & fixed-point verification
- `python tools/build_axiomc.py --out build --root . --stage 2` inside `build-snap-T423h/`:
  - `STAGE1 OK` (`axiomc1.exe`, 29,689,344 bytes, sha256 `1b336910bcf9e0db`)
  - `SEED-A (O1) OK`, `STAGE2 (O1) OK`, `STAGE3 (O1) OK`
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == f9913c7618fb531f90dd052f0b6a57fd73f0014f4881c2ef1ed2c497150c164e` (8,942,592 bytes)
  - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (O1, incl. `Xin chào thế giới`).

### Verification of Round 0 Finding F1
- Inspected `pipe_std_resolve_use`, `pipe_proj_mod_declares_item`, `pipe_text_mod_declares_item`, `pipe_scan_next_tok`, and `pipe_skip_pub_vis` in `compiler/driver/pipeline.ax`:
  - Exact module match (`path` in `provided`) returns early without scanning `<std-root>`.
  - Shorter prefix match (`prov_mod`) only skips `<std-root>` when `pipe_proj_mod_declares_item` confirms `prov_mod` declares the top-level item (or `enum` for 2-segment `Enum.Variant` imports), properly skipping comments (including nested `/* ... */`), strings/raw strings/char/numeric literals, nested `{}`/`()`/`[]` bodies, `*const`, and handling `extern` blocks and `pub[...]` re-exports.
  - Otherwise `project_std_index_scan` runs and loads the longest matching std module (`best_len > prov_len`), resolving F1.
  - `pipe_skip_pub_vis` handles `pub` and `pub(...)` visibility modifiers on `use std.…` lines.
- Non-on-demand `--dep-file` check (`build/axiomc2.exe check --std-root std --dep-file ...`):
  - `tests/run/basic/t117_shifts.ax` and `tests/run/concurrency/tls/qa_tls_borrow_mut_in_shared_panic.ax`: only implicit std files + input file; zero `std/ dir` probes.
- `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 --filter modules/std_on_demand`:
  - `TOTAL 48 PASS 48 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
  - `qa_parent_provided_child_module.ax`, `bug_parent_provided_child_item.ax`, `bug_std_parent_and_child_module.ax`, and the new `qa_pub_vis_and_decl_seam.ax` all PASS in `interp`, `native`, and `native-O1`.

### Native evidence spot-proof (step 4a)
- Mutated `tests/modules/std_on_demand/bug_parent_provided_child_item.ax` inside `build-snap-T423h/` only (`// exit: 11` -> `// exit: 12`), ran `axtest.py --no-cache --filter modules/std_on_demand/bug_parent_provided_child_item.ax`:
  - `TOTAL 3 PASS 0 FAIL 3` (`exit code 11, expected 12` in `interp`, `native`, `native-O1`).
- Restored and verified byte-identical against the main tree.

### Gate scope run (`taskgate.py`)
`python tools/taskgate.py --task T423h --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423h.json` inside `build-snap-T423h/`:
- `TASKGATE T423h exit=0`; wall time 1118.6 s (axtest 1112.6 s).
- `axtest`: `TOTAL 425 PASS 423 FAIL 0 SKIP 2 XFAIL 0` (`own` 32 ids / 84 PASS; `affected` 213 ids / 375 PASS / 2 SKIP; `smoke` 32 ids / 51 PASS; dedup 242 ids).
- `BASELINE OK`; `Failing ids: none`; `unmatched changed files: none`.
- `archcheck`: `clean (exit 0) archcheck: 232 files scanned, 0 violations`.
- `smoke-check (tests/smoke.list)`: `OK; est. worst-case draw 24 s`.
- `WEAK-NATIVE`: `3 in the run; 0 in the task's own/changed tests`.
- `Cache`: `CACHED 0, miss 73, uncacheable 166, stored 60, dep_source exact, verification sample seed=380661305 n=3 of 3 hits, mismatch none, rejected {}, producer snapshot`.
- Smoke always-included cases (`run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`) and `archcheck` all PASS.

### Change set & harness checks
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T423h`: 0 `REFUSED` lines, all Round 0 + Round 1 QA tests staged cleanly, no selfhost bundles listed.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

### Findings
- None. F1 from Round 0 is resolved.

### Tests added (Round 0 + Round 1)
## Files changed
- tests/modules/std_on_demand/qa_time_native_provider.ax
- tests/modules/std_on_demand/qa_shadow_std_process.ax
- tests/modules/std_on_demand/qa_host_module_qualified.ax
- tests/modules/std_on_demand/qa_host_two_providers.ax
- tests/modules/std_on_demand/qa_parent_provided_child_module.ax
- tests/modules/std_on_demand/qa_pub_vis_and_decl_seam.ax

VERDICT: PASS round=1
