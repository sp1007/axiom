# T453b QA Gate Report

## Round 0

### 1. Code review (`compiler/target/x64/frame.ax`)
- Verified `x64_encode_mi_inst_mc` is completely removed: `git grep -n "x64_encode_mi_inst_mc" compiler/` returned 0 hits (exit 1).
- Verified `x64_emit_mi_body_mc` (`compiler/target/x64/frame.ax:5602-5713`) resolves intra-function `X64_MI_JMP`, `X64_MI_JCC`, and `X64_MI_ASSERT` fixups (emitting `x64_emit_panic_sequence` with zeroed `SymbolId { v: 0u32 }` relocation slots) and routes all other instructions through `x64_encode_mi_inst`.
- Verified `x64_encode_mi_inst` handles external `X64_MI_CALL` (`x64_call_sym(..., SymbolId { v: 0u32 })` -> `e8 00 00 00 00`) and `X64_MI_TLS_ADDR` (26-byte Win64 `gs:[0x58]` + `_tls_index` + SECREL sequence matching `x64_emit_tls_addr_obj` in `compiler/target/x64/encode.ax:1988-2027` byte-for-byte with zeroed `disp32` reloc slots).
- Verified `x64_encode_mi_inst_obj` (`compiler/target/x64/frame.ax:5560-5584`) still intercepts `X64_MI_CALL`, `X64_MI_LEA` (sym), and `X64_MI_TLS_ADDR` before delegating to `x64_encode_mi_inst`, so COFF object emission is unaffected.
- Cross-checked `driver_emit_build_mi_body_obj` (`compiler/driver/pipeline.ax:3946-4113`) against `x64_emit_mi_body_mc`: prologue, fixup resolution, inline `X64_MI_ASSERT` panic emission, and instruction encoding match.

### 2. Changed goldens & selfhost templates verification
- `tests/mc/frame/main_42.mc`: diffed against HEAD; only change is `48 89 08` -> `89 08` (4-byte `i32` store width fix, 220 -> 217 bytes).
- `tests/selfhost/isel/qa_frame_layout_and_verify.ax.in`: `MAIN_42_MC` updated `[221]u8` -> `[218]u8` (`MAIN_42_MC_LEN` 220 -> 217) for the same `48 89 08` -> `89 08` fix.
- `tests/selfhost/isel/qa_isel_diff_golden.ax.in`: verified programmatically against HEAD that all 4 `exp_mi` slices (indices 0, 2, 4, 6: 225B, 779B, 6666B, 225B) are byte-for-byte unchanged, and only the 4 `exp_mc` slices (indices 1, 3, 5, 7) updated to the unified object-path encoder output.
- `tests/selfhost/backend/harness_backend_diff_mi_mc.ax.in`: `exp_mi` checks intact; `--emit=mc` validates well-formed lowercase hex lines, function count, prologue/epilogue, plus exact 217-byte unified parity on `tests/mc/frame/main_42.ax`.
- `tests/selfhost/backend/harness_backend_unit.ax.in`: `exp_lir` and `exp_mi` byte-for-byte checks intact; `exp_mc` updated for the 3 MIR cases (`add.mir`, `qa_edge_cond_br.mir`, `qa_multi_branch.mir`) with exact unified-encoder bytes.
- `tests/selfhost/driver/gen_driver_tests.py`: `_unified_emit_mc_override` applies for both `axiom0 is None` and `axiom0 is not None` (`main_42.ax` from `main_42.mc`, `const.mir` with 2-byte `66 89 08` `i16` store).
- Determinism check inside `build-snap-T453b/`: `python .claude/skills/axiom-tasks/scripts/bundles.py check --root .` -> `bundles check: 36 generator(s), 0 file(s), 29s` (exit 0).

### 3. Stage-2/3 fixed-point build (inside `build-snap-T453b/`)
- `python tools/build_axiomc.py --out build --root . --stage 2`:
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == c8ee82a28dbd484d3d777bac02c881d2ed3c0d77151bfc512b0b4892f081c9e4` (8,973,824 bytes, seeded B==C)
  - `STAGE0-GUARD OK` (6 smoke programs byte-identical, incl. Xin chào thế giới)

### 4. Boundary cross-check & liveness proof
- Inspected `tests/mc/emit_mc_parity/emit_mc_parity.py`: parses COFF `.text` symbol table (`0x8664`), slices `[start : start + len(mc_bytes)]`, compares byte-for-byte with `inspect --emit=mc`, checks 16-byte `0x90` NOP padding to next symbol, and asserts non-vacuous opcode presence (`66 89`, `88`, `0f 9x` SETcc, `0f 4x` CMOVcc, `85`/`f7` TEST, ADC/SBB).
- **Liveness spot-proof** (inside `build-snap-T453b/` only): mutated 1 byte of `mc_bytes` (`mc_bytes[0] ^ 1`, `0x55 -> 0x54`) before `if obj_slice != mc_bytes:` in `emit_mc_parity.py` -> exited `1` with `FAIL [widths_O0] fn 'load_store_1' bytes differ`, then restored cleanly.
- **Adversarial parity test added**: `tests/mc/emit_mc_parity/qa_emit_mc_adversarial.py` + `qa_emit_mc_adversarial.test` covering:
  - `@thread_local static mut` (`X64_MI_TLS_ADDR` 26-byte Win64 `gs:[0x58]` sequence with zeroed relocs), direct call (`e8 00 00 00 00`), indirect function-pointer call (`ff d0..d7`), and `assert(...)` (`X64_MI_ASSERT` + inline panic sequence).
  - Signed 1/2/4/8-byte loads/stores (`i8`/`i16`/`i32`/`i64`), signed `div`/`rem`/`mul`/shifts/`not`, and multi-branch `match`.
  - `const` global table RIP-relative LEA (`48 8d ... 00 00 00 00`), `extern "C"` call (`e8 00 00 00 00`), 6-arg Win64 stack call, and `u64` div/rem/shift loop with `break`.
  - Verified byte-for-byte parity at both `-O0` and `-O1`: `QA-EMIT-MC-ADVERSARIAL PASS 36 functions (6 cases)`.

### 5. Test runs (inside `build-snap-T453b/`, `-j 2`)
- `tests/inspect`: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache --filter "inspect/" -j 2 --verbose` -> `TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- Full `taskgate` (`python tools/taskgate.py --task T453b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T453b.json`):

```markdown
### taskgate T453b (`tools/taskgate.py`)

- root `D:/projects/compiler/new lang/build-snap-T453b`, HEAD `49e3f9424001`, compiler `D:/projects/compiler/new lang/build-snap-T453b/build/axiomc2.exe`, `-j 2`
- change set: 19 file(s) (working tree of build-snap-T453b vs HEAD)
- wall time: 814.6 s (axtest 804.5 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 47 | 47 | 36 | 0 | 11 | 0 | 0 |
| affected | 124 | 147 | 135 | 0 | 12 | 0 | 0 |
| smoke | 33 | 56 | 56 | 0 | 0 | 0 | 0 |
| **total (dedup)** | 154 | 198 | 186 | 0 | 12 | 0 | 0 |

- unmatched changed files: none
- WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests
- Baseline: BASELINE OK
- Failing ids: none
- archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations
- smoke-check (tests/smoke.list): OK; est. worst-case draw 27 s
- axtest: `TOTAL 198 PASS 186 FAIL 0 SKIP 12 XFAIL 0` (exit 0)
- TASKGATE T453b exit=0
```

### 6. Hygiene checks
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T453b`: 0 `REFUSED` lines (12 staged files incl. QA-added tests + QA report).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

### Findings
none

## Files changed
- tests/mc/emit_mc_parity/qa_emit_mc_adversarial.py
- tests/mc/emit_mc_parity/qa_emit_mc_adversarial.test

VERDICT: PASS round=0
