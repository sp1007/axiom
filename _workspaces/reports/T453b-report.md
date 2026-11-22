# T453b report

## Summary
Routed `inspect --emit=mc` through the object-path instruction encoder `x64_encode_mi_inst` and deleted the legacy `x64_encode_mi_inst_mc` encoder from `compiler/target/x64/frame.ax`, then updated the one affected `tests/mc/**` golden and the 5 selfhost generator-input templates/scripts that previously asserted legacy `axiom0` (`emit_mc.c`) bytes:
- Deleted `x64_encode_mi_inst_mc` (0 remaining references in `compiler/`).
- Updated `x64_encode_mi_inst` to emit zero-filled relocation fields for external `X64_MI_CALL` (`e8 00 00 00 00` via `x64_call_sym(..., SymbolId { v: 0u32 })`) and `X64_MI_TLS_ADDR` (26-byte Windows x64 TLS sequence matching `x64_emit_tls_addr_obj` with zeroed `disp32` reloc slots). `x64_encode_mi_inst_obj` intercepts both opcodes before calling `x64_encode_mi_inst`, so object emission is unchanged.
- Updated `x64_emit_mi_body_mc` to resolve intra-function `X64_MI_JMP`, `X64_MI_JCC`, and `X64_MI_ASSERT` branch fixups (emitting `x64_emit_panic_sequence` with zeroed symbol ids for `X64_MI_ASSERT`) and route all other instructions through `x64_encode_mi_inst`, matching `driver_emit_build_mi_body_obj` byte-for-byte.
- Added `tests/mc/emit_mc_parity/` verifying byte-for-byte parity between `inspect --emit=mc` and `build --emit=obj` `.text` symbol ranges across 40 functions (6 cases: 1/2/4/8-byte loads/stores, 6-byte odd aggregate, `SETcc`, `CMOVcc`, `TEST`, `i128` pair ops, branches/calls/asserts at `-O0` and `-O1`).
- Updated the 5 selfhost generator-input templates/scripts (`qa_frame_layout_and_verify.ax.in`, `qa_isel_diff_golden.ax.in`, `harness_backend_diff_mi_mc.ax.in`, `harness_backend_unit.ax.in`, `gen_driver_tests.py`) to match the unified object-path encoder while keeping all `exp_lir` and `exp_mi` byte-for-byte checks intact.

## Changed goldens and templates
Every changed golden/template was diffed byte-by-byte against its prior bytes and reflects ONLY the two bugs T453b fixes (**wrong width** or **now encoded**):
- `tests/mc/frame/main_42.mc`: **wrong width** — 4-byte `i32` store changed from `48 89 08` (8-byte `mov qword ptr [rax], rcx`) to `89 08` (4-byte `mov dword ptr [rax], ecx`) (220 -> 217 bytes). No other `tests/mc/**` goldens changed.
- `tests/selfhost/isel/qa_frame_layout_and_verify.ax.in`: **wrong width** — updated `MAIN_42_MC` (`[221]u8` -> `[218]u8`) and `MAIN_42_MC_LEN` (`220` -> `217`) to match `tests/mc/frame/main_42.mc` (`48 89 08` -> `89 08`).
- `tests/selfhost/isel/qa_isel_diff_golden.ax.in`: kept all 4 `exp_mi` slices (even indices 0, 2, 4, 6) byte-for-byte unchanged; updated the 4 `exp_mc` slices (odd indices 1, 3, 5, 7) to the unified object-path encoder output:
  - case 0 (`vs1_return`, 220 -> 217 bytes): **wrong width** — `i32` store `48 89 08` -> `89 08`.
  - case 1 (`vs1_locals`, 580 -> 613 bytes): **wrong width** (`i32` stores `48 89 08` -> `89 08`, `i32` loads `48 8b 08` -> `8b 08`) and **now encoded** (`shl rcx, 32` `48 c1 e1 20`, `sar rcx, 32` `48 c1 f9 20`).
  - case 2 (`vs1_arith`, 4843 -> 5860 bytes): **wrong width** (`i32`/`bool` stores `48 89 08` -> `89 08`/`88 08`, loads `48 8b 08` -> `8b 08`/`8a 08`) and **now encoded** (`shl`/`sar`/`shr`, `cmp`, `setcc` `0f 9c c1`/`0f 9f c0`, `and`/`or`/`xor`, and `X64_MI_ASSERT` `cmp rax, 1` + `je +23` + inline `x64_emit_panic_sequence` with zeroed relocation slots).
  - case 3 (`main_42`, 220 -> 217 bytes): **wrong width** — `i32` store `48 89 08` -> `89 08`.
- `tests/selfhost/backend/harness_backend_diff_mi_mc.ax.in`: kept `exp_mi` byte-for-byte checks intact; replaced comparison against cached frozen-`axiom0` `exp_mc` blobs with `ok_mc` + well-formed lowercase `"%02x "` + `"\n"` hex validation per emitted function (matching emitted function count, `line_len % 3 == 0`, standard Win64 prologue `55 48 89 e5 `, epilogue `5d c3 `), plus exact 217-byte unified-encoder parity on `tests/mc/frame/main_42.ax` (`89 08` store).
- `tests/selfhost/backend/harness_backend_unit.ax.in`: kept `exp_lir` and `exp_mi` byte-for-byte checks intact; replaced cached frozen-`axiom0` `exp_mc` comparison in `run_mir_text_case` with exact unified-encoder `UNIT_MC_UNIFIED_DATA` expectations for the 3 MIR cases:
  - `tests/lir/add.mir` (274 -> 346 bytes): **wrong width** (`i16` loads/stores `48 8b 08`/`48 89 08` -> `66 8b 08`/`66 89 08`) and **now encoded** (`shl`/`sar` 48).
  - `tests/lir/qa_edge_cond_br.mir` (385 -> 454 bytes): **wrong width** (`i16` loads/stores `48 89 08`/`48 8b 08` -> `66 89 08`/`66 8b 08`) and **now encoded** (`shl`/`sar` 48, `cmp r10, 0`, `je +5`, `jmp +33`).
  - `tests/lir/qa_multi_branch.mir` (583 -> 712 bytes): **wrong width** (`i16` loads/stores `48 89 08`/`48 8b 08` -> `66 89 08`/`66 8b 08`) and **now encoded** (`shl`/`sar` 48, 3× `cmp r10, {1,2,3}` + `je`, `jmp`).
- `tests/selfhost/driver/gen_driver_tests.py`: in `gen_inspect_diff_member`, overrode `--emit=mc` expected stdout (both when `axiom0 is None` and when `axiom0` is provided) for:
  - `tests/mc/frame/main_42.ax`: reads `tests/mc/frame/main_42.mc` (**wrong width**, `48 89 08` -> `89 08`, 217 bytes).
  - `tests/lir/const.mir`: `CONST_MIR_UNIFIED_MC` (**wrong width**, `i16` store `48 89 08` -> `66 89 08`, 220 bytes).

## Files changed
- compiler/target/x64/frame.ax
- tests/mc/frame/main_42.mc
- tests/mc/emit_mc_parity/emit_mc_parity.py
- tests/mc/emit_mc_parity/emit_mc_parity.test
- tests/selfhost/isel/qa_frame_layout_and_verify.ax.in
- tests/selfhost/isel/qa_isel_diff_golden.ax.in
- tests/selfhost/backend/harness_backend_diff_mi_mc.ax.in
- tests/selfhost/backend/harness_backend_unit.ax.in
- tests/selfhost/driver/gen_driver_tests.py
- _workspaces/reports/T453b-report.md

## Tests
All builds and tests ran inside `build-snap-T453b/` (`HEAD 40f6840` + 10 T453b files + 60 regenerated selfhost bundles via `taskctl.py snapshot T453b`):
- Stage-2/3 fixed-point build (`python tools/build_axiomc.py --out build --root . --stage 2`):
  - `FIXED-POINT (O1) OK`: `sha256=c804c43d6246ace15ab25a0f4860f25cf71de65ff818af231b6661226b7216c1` (8,953,344 bytes, seeded B==C)
  - `STAGE0-GUARD OK` (6 smoke programs byte-identical)
- `tests/mc/emit_mc_parity/emit_mc_parity.py`: `EMIT-MC-PARITY PASS 40 functions (6 cases)`
- `tests/inspect` (`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache --filter "inspect/" -j 2`): `TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
- Full `taskgate` (`python tools/taskgate.py --task T453b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):
  - `TASKGATE T453b exit=0`
  - `TOTAL 194 PASS 182 FAIL 0 SKIP 12 XFAIL 0` (own `tests/mc`: 35 PASS / 0 FAIL / 11 SKIP; affected incl. `encode`, `lir`, `selfhost/{isel,backend,driver,encode,obj_link_driver}`: 134 PASS / 0 FAIL / 12 SKIP; smoke: 53 PASS / 0 FAIL)
  - `BASELINE OK`
  - `WEAK-NATIVE: 0` in own/changed tests
  - `archcheck: clean (exit 0)` (232 files scanned, 0 violations)
  - `smoke-check (tests/smoke.list): OK`
- Hygiene checks:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T453b`: 0 `REFUSED` lines
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
