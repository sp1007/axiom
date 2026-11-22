# T498h QA report

## Round 0

### 1. Code review & spec check
- `compiler/abi/win64.ax`: Verified `lir_lower_abi_in_arena` lowers `usize`-typed `LIR_INST_ABI_ARG` on `ABI_LOC_INDIRECT` to `ABI_LOC_REG` (when passed in register) or `ABI_LOC_STACK` (when passed in stack slot), passing/receiving the Win64 hidden pointer directly without dereference-copying the aggregate.
- `compiler/lir/builder.ax`:
  - Indirect aggregate `MIR_LOCAL_ARG` parameters store the incoming hidden pointer (`usize`) in their slot (`param_is_indirect_ptr`), and `lower_place_addr` loads through it directly. Callee frame allocates 0 aggregate copy bytes.
  - `lb_compute_slot_remaps` coalesces single-def/single-use `MIR_LOCAL_TEMP` indirect aggregates (`mention_cnt == 2`, single predecessor for call-target coalescing, no aliasing with call arguments or address-taken destination) into the destination slot, making the follow-up copy a no-op.
  - `lb_can_elide_caller_copy` / `lb_local_dead_after_call` / `lb_local_addr_taken_reaching_bb` / `lb_flag_stays_zero_from`:
    - Elides caller copy at `-O0` for moves (`MIR_OP_MOVE`, non-`Copy` types, or `MIR_LOCAL_TEMP`), and at `-O1` also for last-use `Copy` bindings.
    - Correctly guards against: `sret` destination aliasing (`has_destination` mentions `loc_v` or `mapped_v`), duplicate argument aliasing (`args[arg_idx+1..arg_count]` mentions `loc_v` or `mapped_v`), reachable `MIR_RVALUE_REF` borrows (`lb_local_addr_taken_reaching_bb`), CFG back-edge liveness across loops (full CFG BFS in `lb_local_dead_after_call`), and unwind paths (`call_unwind`).
    - When a copy is required, `lb_acquire_call_copy_slot` reuses per-type call-site copy slots (`lb_reset_call_copy_slots` per call terminator) and materializes `emit_stack_addr` immediately before `LIR_INST_ABI_ARG`.
  - Direct `sret` destination (`dst_addr`) skips redundant `LIR_INST_ABI_RESULT` copy for indirect aggregates.
  - `emit_memcpy_bytes` emits scalar chunks (`8/4/2/1` B) for `<= 64` B and an 8-byte loop + scalar tail for `> 64` B; `MIR_RVALUE_REPEAT` uses a broadcasted 64-bit word loop + byte tail for 1-byte repeats `>= 64` elements.
- `compiler/target/x64/frame.ax`:
  - `x64_frame_lower_baseline_in_arena` / `x64_frame_lower_opt_in_arena` size `sret` slot 0 to 8 bytes and skip unreferenced indirect-aggregate slots (`frame_mark_used_slots`) at `-O1`.
  - `x64_regalloc_with_pgo_in_arena` sums candidate eviction weights only across `active` intervals that actually overlap `cur_iv` (`x64_intervals_overlap`) and evicts all overlapping holders of `stolen_reg`, preventing lifetime-hole mis-eviction under 12-GPR pressure.
- `tests/selfhost/backend/harness_backend_diff_mi_mc.ax.in`: All 28 non-indirect-aggregate `.ax` cases and all `.mir` cases retain byte-for-byte `axiom0` MI comparison; the 5 indirect-aggregate cases (`003-nested-struct.ax`, `004-large-struct.ax`, `03-nested.ax`, `04-large-payload.ax`, `05-nested-enum.ax`) use `validate_t498h_mi_output` (checking function count, returns, and direct hidden-pointer `rcx` reception on `003-nested-struct.ax`).
- `tests/run/array_copy/large_and_edge.ax`: Stale 256-byte interp comment updated cleanly.
- No edits outside `paths:`; no `bootstrap/axiom0`, `spec/`, or `docs/` edits.

### 2. Compiler build, fixed-point & frame-size verification (inside `build-snap-T498h/`)
- `python tools/build_axiomc.py --out build --root . --stage 2`:
  - `BUILD-AXIOMC OK`: `build/axiomc2.exe` (`8,325,120` bytes, `sha256=f3b3b95515c96f8dc4fff94700681e6a4ab032ffae78abbe598bdb3bef3e5070`)
  - Verified `sha256(axiomc2.exe) == sha256(axiomc2_O1.exe) == sha256(axiomc3_O1.exe) == f3b3b95515c96f8dc4fff94700681e6a4ab032ffae78abbe598bdb3bef3e5070`.
- Frame-size spot-check on `tests/run/agg_arg_copies/repro_256k_exact.ax` (`inspect --emit=mi` + `build` + `objdump -d -M intel`):
  - `huge` MI entry: stores incoming `rcx` hidden pointer directly into `[frame#1 + 0]` (0 aggregate copy).
  - `huge` frame (`-O0` and `-O1`): `sub rsp, 0x1c8` = **456 B** (matches report).
  - `main` frame (`-O0`): probe `0x800a8` = **524,456 B** (`512.16 KiB`); (`-O1`): probe `0x400a0` = **262,304 B** (`256.16 KiB`) — well within default 1 MB stack; both binaries exit 0 and print `10`.

### 3. Boundary cross-check & adversarial test (step 5)
- Added `tests/run/agg_arg_copies/qa_aliasing_and_odd_sizes.ax` (`modes: interp native`, exact `stdout:`, 67 bytes) covering:
  1. Aliased `sret` (`x = reverse_and_mutate(x)` and projected `w.buf = reverse_and_mutate(w.buf)`).
  2. Aliased duplicate `Copy` args when source is dead after the call (`dup3(a, a, a)` and `dup2_rev(b, b)`).
  3. Loop back-edge liveness (`while` calling `clobber128(a)` with no lexical use of `a` after the loop).
  4. `view(a)` kept live across `clobber128(a)` when `a` itself is dead after the call.
  5. Odd Win64 indirect sizes (`3, 5, 6, 7` B) and sizes straddling the 64-byte `emit_memcpy_bytes` loop threshold + 8-byte tail (`63, 64, 65, 71, 72, 73` B).
- Refreshed snapshot (`taskctl.py snapshot T498h`: 36 generators, 60 files, 25s) and ran `--no-cache`:
  - `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --filter run/agg_arg_copies/qa_aliasing_and_odd_sizes --no-cache --verbose -j 2`: `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1`, `WEAK-NATIVE 0`).

### 4. Native-evidence spot-proof (step 4a)
- Confirmed all 8 tests in `tests/run/agg_arg_copies/` and `tests/run/array_copy/large_and_edge.ax` assert exact `stdout:` (`WEAK-NATIVE: 0` in own/changed tests).
- Mutated expected stdout (`151 159` -> `999 159`) in `build-snap-T498h/tests/run/agg_arg_copies/qa_aliasing_and_odd_sizes.ax` only:
  - Mutated run (`--no-cache`): `TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0` (`MUTATED_EXIT=1`; `interp`, `native`, `native-O1` all failed with exact byte-0 diff).
  - Restored run (`--no-cache`): `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0` (`RESTORED_EXIT=0`).

### 5. Taskgate & harness checks
- `python tools/taskgate.py --task T498h --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T498h.json` (inside `build-snap-T498h/`):
  - `TASKGATE T498h exit=0` (wall 517.8 s)
  - `own`: 9 ids / 27 results (`27 PASS, 0 FAIL`)
  - `affected`: 166 ids / 256 results (`244 PASS, 0 FAIL, 12 SKIP`)
  - `smoke`: 33 ids / 56 results (`56 PASS, 0 FAIL`, seed `867566261`)
  - `total (dedup)`: 196 ids / 307 results (`TOTAL 307 PASS 295 FAIL 0 SKIP 12 XFAIL 0`)
  - `Cache`: `CACHED 88, miss 22, uncacheable 107, stored 20, dep_source exact, verification sample seed=2135686850 n=20 of 67 hits, mismatch none, rejected {}, producer snapshot`
  - `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`
  - `BASELINE OK` (`Failing ids: none`)
  - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
  - `smoke-check (tests/smoke.list): OK; est. worst-case draw 18 s`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T498h`: 0 `REFUSED` lines.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

### Findings
none

## Files changed
- tests/run/agg_arg_copies/qa_aliasing_and_odd_sizes.ax

VERDICT: PASS round=0
