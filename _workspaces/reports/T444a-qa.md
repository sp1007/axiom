# T444a QA Gate Report

## Round 0

Snapshot: `build-snap-T444a/` refreshed on `HEAD 8e74a337` (`T447`) + `T444a`'s 7 changed files + regenerated selfhost bundles.

### 1. Code & hygiene audit
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T444a`: exit 0, 0 `REFUSED`, 7 staged files matching `_workspaces/reports/T444a-report.md` (`STATUS: COMPLETE round=0`):
  - `_workspaces/reports/T444a-report.md`
  - `compiler/types/layout.ax`
  - `tests/run/enum_payload_mixed/nested_pointer_iflet_size.ax`
  - `tests/run/enum_payload_mixed/pointer_and_struct.ax`
  - `tests/run/enum_payload_mixed/three_field_orders.ax`
  - `tests/run/enum_payload_mixed/two_field_orders.ax`
  - `tests/selfhost/types/qa_types_layout.ax.in`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: exit 0, `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/bundles.py check --root build-snap-T444a`: exit 0 (`bundles check: 36 generator(s), 0 file(s), 28s`).
- `compiler/types/layout.ax` diff review:
  - `place_variant_fields` is the single source of truth for both `type_enum_field_offset` and `type_size` on `TY_ENUM`.
  - Handles `count == 0` (`field_offset = 0u32`, `end = SIZE_4`), field sorting via `sort_fields`, per-field alignment via `align_up_u32` starting from `SIZE_4` (discriminant at `[0, 4)`), and proper `heap_free`.
  - `type_size` on `TY_ENUM` computes `max_align = type_align(TypeId { v: self_v }, ti)`, tracks `max_end = max(SIZE_4, placed.end)` across all variants, and rounds up via `align_up_u32(max_end, max_align)`.
  - `tests/selfhost/types/qa_types_layout.ax.in:194` (`assert_true(type_size(...) == 24u32, 31)`) is mathematically sound for `enum { V0, V1(u8, u64) }`: tag `[0, 4)`, `u64` at `[8, 16)`, `u8` at `[16, 17)`, `align_up(17, 8) = 24` (lines 195–196 already asserted field offsets `8u32` and `16u32`).
  - Minor style note (non-blocking): comment at `compiler/types/layout.ax:138-139` mentions writing to `*out_end`, whereas `place_variant_fields` returns `VariantPlacement { field_offset, end }` by value.

### 2. Fresh stage-3 bootstrap rebuild (`8e74a337 + T444a`)
- Command (inside `build-snap-T444a/`): `python tools/build_axiomc.py --out build --stage 3`
- Exit code: 0
- `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == dedfb9d5d3d542b771c79274304a776097ee1b0e9aaa03e8ec97fb9fc8b458a8` (binary size `8582144` bytes).
- `STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on 6 smoke program(s) (O1, incl. Xin chào thế giới)`.

### 3. Own tests & unpatched HEAD regression proof (`--no-cache -j 2`)
- Patched `build-snap-T444a/build/axiomc2.exe`:
  - `python tools/axtest.py --filter run/enum_payload_mixed --compiler build/axiomc2.exe --no-cache -j 2`
  - Result: exit 0, `WEAK-NATIVE 0`, `TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0`.
- Unpatched HEAD `8e74a337` compiler (`_workspaces/artifacts/compiler-cache/axiomc2_O1_5bcfd5c76d73ba4b.exe`, `sha256=ec180b94cdc1fa69`):
  - `python tools/axtest.py --filter run/enum_payload_mixed --compiler "...\axiomc2_O1_5bcfd5c76d73ba4b.exe" --no-cache -j 2`
  - Result: exit 1, `TOTAL 12 PASS 0 FAIL 12 SKIP 0 XFAIL 0` (all 4 tests fail in `interp`, `native`, and `native-O1`, reproducing truncated `u8` fields and buggy `size_of` = 16).

### 4. Native-evidence & mutation spot-proof (`axiom-qa.md` §4a)
- All 4 new tests in `tests/run/enum_payload_mixed/` run in `interp`, `native`, and `native-O1` with exact `// stdout:` expectations (`WEAK-NATIVE 0`).
- Direct native compilation & execution (`build/axiomc2.exe build` at O0 and `-O1`):
  - `tests/run/enum_payload_mixed/two_field_orders.ax`: O0 `build_exit=0 run_exit=0`, `-O1` `build_exit=0 run_exit=0`, exact stdout verified.
  - `tests/run/enum_payload_mixed/nested_pointer_iflet_size.ax`: O0 `build_exit=0 run_exit=0`, `-O1` `build_exit=0 run_exit=0`, exact stdout verified (`size 24 32 8`, nested/ptr/iflet lines).
- Mutation spot-proof in `build-snap-T444a/tests/run/enum_payload_mixed/two_field_orders.ax` (mutated `// stdout: 7 9\` -> `// stdout: 8 9\`):
  - `python tools/axtest.py --filter run/enum_payload_mixed/two_field_orders.ax --compiler build/axiomc2.exe --no-cache -j 2`
  - Result: exit 1, `TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1` all failed with stdout mismatch at byte 0).
  - Restored byte-for-byte (`RESTORED_EXACT=True`).

### 5. Adversarial tests (temporary in `build-snap-T444a/tests/run/_qa_t444a_adv/`, removed after run)
- `quad_and_array.ax`: 4-field mixed-size variant `Quad(u8, u64, u16, u32)` + struct-bearing variant `Big(u32, PairStruct, u8)` + `Empty`, passed by value, stored in `[3]E`, copied out, matched one binding per arm, checking every field and `size_of<E>() == 32`, `size_of<PairStruct>() == 16`.
- `generic_enum.ax`: generic `enum GChoice<A, B> { GPair(A, B), GTriple(u8, A, B), GNone }` instantiated as `GChoice<u8, u64>` and `GChoice<u64, u8>`, checking every field binding and `size_of == 24` for both instantiations.
- Command: `python tools/axtest.py --filter run/_qa_t444a_adv --compiler build/axiomc2.exe --no-cache -j 2`
- Result: exit 0, `WEAK-NATIVE 0`, `TOTAL 6 PASS 6 FAIL 0 SKIP 0 XFAIL 0`.
- Cleaned up `build-snap-T444a/tests/run/_qa_t444a_adv/` prior to `taskgate`.

### 6. Full `taskgate` (`build-snap-T444a/`)
Command:
`python tools/taskgate.py --task T444a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T444a.json`

### taskgate T444a (`tools/taskgate.py`)

- root `D:/projects/compiler/new lang/build-snap-T444a`, HEAD `8e74a337dad9`, compiler `D:/projects/compiler/new lang/build-snap-T444a/build/axiomc2.exe`, `-j 2`
- change set: 31 file(s) (working tree of build-snap-T444a vs HEAD)
  - `_workspaces/reports/T444a-report.md`
  - `compiler/types/layout.ax`
  - `tests/run/enum_payload_mixed/nested_pointer_iflet_size.ax`
  - `tests/run/enum_payload_mixed/pointer_and_struct.ax`
  - `tests/run/enum_payload_mixed/three_field_orders.ax`
  - `tests/run/enum_payload_mixed/two_field_orders.ax`
  - `tests/selfhost/abi/qa_abi_classify_and_seam.ax`
  - `tests/selfhost/abi/qa_abi_lir_lower.ax`
  - `tests/selfhost/backend/qa_backend_interp.ax`
  - `tests/selfhost/backend/qa_backend_native.ax`
  - `tests/selfhost/driver/qa_driver_full_interp.ax`
  - `tests/selfhost/driver/qa_driver_full_native.ax`
  - `tests/selfhost/drop/qa_drop_all.ax`
  - `tests/selfhost/interp/qa_interp_all.ax`
  - `tests/selfhost/interp_opt/qa_interp_opt_interp.ax`
  - `tests/selfhost/interp_opt/qa_interp_opt_native.ax`
  - `tests/selfhost/isel/qa_isel_all.ax`
  - `tests/selfhost/lir/qa_lir_from_ax.ax`
  - `tests/selfhost/lir/qa_lir_from_mir_and_seam.ax`
  - `tests/selfhost/mir/qa_mir_builder_and_drop.ax`
  - `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
  - `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`
  - `tests/selfhost/opt/qa_opt_pipeline.ax`
  - `tests/selfhost/own_mir_verify/qa_own_mir_diff_interp.ax`
  - `tests/selfhost/own_mir_verify/qa_own_mir_diff_native.ax`
  - `tests/selfhost/traits/qa_traits_solver_mono.ax`
  - `tests/selfhost/typeck/qa_typeck_all.ax`
  - `tests/selfhost/typeck_traits/qa_typeck_traits_all.ax`
  - `tests/selfhost/types/qa_types_layout.ax`
  - `tests/selfhost/types/qa_types_layout.ax.in`
  - `tests/selfhost/verify/qa_verify_pipeline.ax`
- wall time: 1112.1 s (axtest 1098.2 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 4 | 12 | 12 | 0 | 0 | 0 | 0 |
| affected | 79 | 138 | 137 | 0 | 1 | 0 | 0 |
| smoke | 31 | 52 | 52 | 0 | 0 | 0 | 0 |
| **total (dedup)** | 108 | 188 | 187 | 0 | 1 | 0 | 0 |

Counts per group:

| group | ids | failing | parts |
|---|---|---|---|
| conformance | 1 | 0 | smoke |
| diff | 2 | 0 | smoke |
| driver | 1 | 0 | smoke |
| encode | 1 | 0 | smoke |
| fuzz | 1 | 0 | smoke |
| hir | 1 | 0 | smoke |
| inspect | 1 | 0 | smoke |
| lex | 1 | 0 | smoke |
| link | 1 | 0 | smoke |
| link2 | 1 | 0 | smoke |
| lir | 1 | 0 | smoke |
| mc | 1 | 0 | smoke |
| mir | 1 | 0 | smoke |
| modules | 1 | 0 | smoke |
| obj | 1 | 0 | smoke |
| opt | 1 | 0 | smoke |
| opt2 | 1 | 0 | smoke |
| parse | 1 | 0 | smoke |
| perf | 1 | 0 | smoke |
| programs | 1 | 0 | smoke |
| resolve | 1 | 0 | smoke |
| run | 6 | 0 | affected, own, smoke |
| selfhost | 44 | 0 | affected, smoke |
| std | 1 | 0 | smoke |
| typeck | 18 | 0 | affected, smoke |
| ui | 15 | 0 | affected, smoke |
| unit | 1 | 0 | smoke |
| verify | 1 | 0 | smoke |

Affected-set derivation summary:
- 4 own tests in `run/enum_payload_mixed/*` (exact dependency)
- 43 affected `selfhost/*` tests (bundle generator checks embedding `compiler.types.layout` + changed regenerated bundles + `selfhost/types/*`)
- 18 `typeck/*` tests (`compiler/types -> tests/typeck`)
- 14 `ui/typeck/*` tests (`compiler/types -> tests/ui/typeck`)
- no-op: `_workspaces/reports/T444a-report.md`
- unmatched changed files: none

Smoke: seed=3927409512, always `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax` + 28 per-group picks.
Cache: CACHED 0, miss 47, uncacheable 61, stored 46, dep_source exact, verification sample seed=None n=0 of 0 hits, mismatch none, rejected {}, producer snapshot
WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests
Baseline (`D:\projects\compiler\new lang\build-snap-T444a\_workspaces\baseline-failures.txt`): BASELINE OK
Failing ids: none
archcheck: clean (exit 0) archcheck: 229 files scanned, 0 violations
axtest: `TOTAL 188 PASS 187 FAIL 0 SKIP 1 XFAIL 0` (exit 0)

TASKGATE T444a exit=0

### Findings
None.

## Files changed

## Verdict
VERDICT: PASS round=0
