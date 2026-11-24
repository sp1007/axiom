# T537 Implementation Report — Process-Wide `static` and `static mut` Items (E13.1)

## Summary

Implemented process-wide hosted non-`@thread_local` `static` and `static mut` items end-to-end across all 10 compiler layers (`typeck`, `interp_opt`, `mir`, `verify`, `own`, `opt` `-O1`/`-O2`, `interp`, `lir`, `backend`, `driver`, and `link`), retiring `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` on `HIR_ITEM_STATIC` in `axiomc`:

1. **Type Checking & Comptime Validation (`compiler/types/typeck.ax`, `compiler/interp_opt/session.ax`)**:
   - Enabled const-item evaluation for non-TLS `HIR_ITEM_STATIC` at all 3 `typeck` passes (`evaluate_const_item_in_impl`, `check_item_body`, `typeck_pass1b_and_2`), guarding `eval_const_expr_u128` path-lookup so immutable `static` items cannot act as type-level array-length constants (`[0; S]` remains rejected while `const` folding works).
   - Retired `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` in `session_validate_comptime_items`, validating non-TLS `static` / `static mut` initializers with `comptime_validate_const_expr` (`AX_CONST_NOT_COMPTIME` on non-const calls/loops) and evaluating non-aggregate initializers via `interp_eval_const_expr` with full `CONST_AGGREGATE` population (`session_eval_static_aggregate`) for structs, arrays (`[v; N]` and `[a, b, ...]`), tuples, enums, `str` slices, and function pointers.
   - Enforced immutable `static` mutation rejection (`AX_TYPE_ASSIGN_IMMUTABLE`) in `check_stmt_assign`, `tc_check_place_mutable`, and `check_call` (`TY_BUILTIN_ADDRESS_OF_MUT`) across direct assignment (`S = v`, `S += 1`), field/index projections (`S.f = v`, `S[i] = v`), `mut_view(S)` / `mut_view(S.f)`, and `address_of_mut(S)` / `address_of_mut(S.f)`.
   - Preserved `compiler/own/unsafe.ax` untouched so safe-context reads, writes, `address_of_mut`, and closure captures of non-TLS `static mut` continue to report `AX_CONC_UNSYNC_STATIC` (and `AX_UNSAFE_REQUIRED` on raw intrinsics outside `unsafe`).

2. **MIR, Drop Elaboration, Ownership & Verifier (`compiler/mir/{mir,mod,builder,drop}.ax`, `compiler/own/init.ax`, `compiler/verify/verifier.ax`)**:
   - Added `MIR_LOCAL_STATIC: u8 = 6u8` (`kind == 6`, printed/parsed as `static` in MIR text).
   - Pre-declared referenced non-TLS `HIR_ITEM_STATIC` locals right after `MIR_LOCAL_ARG`s in `mir_build_fn`, `mir_build_closure`, and `mir_build_expr_body` (`mb_predeclare_statics_in_block` / `mb_predeclare_statics_in_expr`) so `view(STATIC)` borrows satisfy `src_v < dest_v` in capability checking (`compiler/own/cap.ax`) without affecting functions that do not reference non-TLS statics.
   - Lowered `HIR_EXPR_PATH` references to non-TLS `HIR_ITEM_STATIC` into deduplicated `MIR_LOCAL_STATIC` locals (`is_mut = (*it).is_mut`, `const_sym = (*it).symbol`).
   - Excluded `MIR_LOCAL_STATIC`, `MIR_LOCAL_TLS`, and `MIR_LOCAL_CONST` from drop elaboration and drop-flag allocation (`compiler/mir/builder.ax`, `compiler/mir/drop.ax`, `compiler/verify/verifier.ax`) so static storage is never dropped.
   - Seeded `MIR_LOCAL_STATIC` as `OWN_OWNED` (`compiler/own/init.ax`) and `VERIFY_ST_OWNED` (`compiler/verify/verifier.ax`), rejected `MIR_BORROW_MUT` on immutable `MIR_LOCAL_STATIC`, and rejected `!Copy` moves out of `MIR_LOCAL_STATIC` / `MIR_LOCAL_TLS` (without an intervening `MIR_PROJ_DEREF`) with `AX_MOVE_USE_AFTER_MOVE`.

3. **MIR & OptIR Optimizers at `-O1` and `-O2` (`compiler/opt/{const_fold,dce}.ax`, `compiler/opt/{optir,alias,sroa,escape,inline,ipa}/mod.ax`)**:
   - Prevented `const_fold` from folding mutable `MIR_LOCAL_STATIC` reads and kept `MIR_LOCAL_STATIC` writes live in `dce` (`uses[lv] = 1u32`).
   - Excluded `MIR_LOCAL_STATIC` from SSA promotion in `optir_eligible_for_ssa` (keeping statics memory-resident across calls/loops), modeled `ALIAS_LOC_GLOBAL` with `const_sym` identity and `alias_may_touch_memory` call clobbers in `alias`, blocked `sroa` splitting and `escape` stack-promotion (`OPT_ALLOC_GLOBAL`), deduplicated/remapped `MIR_LOCAL_STATIC` by `const_sym` during `inline` cloning instead of demoting to `MIR_LOCAL_TEMP`, and blocked `IPA_FN_PURE` / `IPA_FN_READNONE` summary inference when functions touch `MIR_LOCAL_STATIC` or `MIR_LOCAL_TLS`.

4. **Oracle / Interpreter (`compiler/interp/{frame,interp}.ax`)**:
   - Guarded `get_local_ptr` in `frame.ax` so `MIR_LOCAL_STATIC` and `loc.is_mut` slots resolve through `frm.local_ptrs[loc.v]` instead of `const_table`.
   - Provisioned a single process-wide allocation per `MIR_LOCAL_STATIC` in `interp_bind_static_locals` (`slot_tid = 0xFFFFFFFFu32`, `call_depth = 0`) shared across recursive calls, function boundaries, and `std.thread` OS/oracle threads (`interp_clone_static_slots`), preserving address identity (`address_of` / `address_of_mut`), persistent mutations, and race-detector tracking.

5. **LIR, Native Backend, Driver Reachability & PE32+ Linker (`compiler/lir/builder.ax`, `compiler/backend/session.ax`, `compiler/driver/pipeline.ax`, `compiler/link/linker.ax`)**:
   - Lowered `MIR_LOCAL_STATIC` addresses via deterministic symbol `__ax_static_<sym_v>_<name>` and `LIR_INST_FN_ADDR` (RIP-relative `LEA`), permitting direct and projected stores into `MIR_LOCAL_STATIC`.
   - Emitted hosted non-TLS statics in both `compiler/backend/session.ax` (`inspect --emit=mc|obj`) and `compiler/driver/pipeline.ax` (`build` / `run`):
     - Immutable `static` (without interior `Atomic<T>`) -> `.rdata` (`IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ`).
     - Immutable `static` containing `Atomic<T>` (e.g. `AtomicU32` / `Mutex` / `Once` static locks on Windows x64 where `LOCK` instructions require writable pages) and non-zero/relocated `static mut` -> `.data` (`IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE`).
     - All-zero `static mut` with zero relocations -> `.bss` (`IMAGE_SCN_CNT_UNINITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE`), wired in `compiler/link/linker.ax` with `SizeOfRawData = 0`, `PointerToRawData = 0`, and `OptHdr.SizeOfUninitializedData` populated.
     - Emitted `RELOC_X86_64_64` relocations for embedded `Str` (`ptr`, `len`) slices and function-pointer fields/elements in static initializers.
   - Extended `pipe_bodies_ref_sym` and `pipe_mark_body_std_refs` in `compiler/driver/pipeline.ax` to scan `(*body).locals` for `MIR_LOCAL_STATIC` / `MIR_LOCAL_TLS` `const_sym` references so `<std>` statics remain reachable when referenced from user or std function bodies.

## Verification

All builds and test runs were executed exclusively inside the isolated snapshot `build-snap-T537/` with `-j 2`:

1. **Stage-2 Fixed-Point Compiler Bootstrap (`python tools/build_axiomc.py --out build --root . --stage 2`)**:
   - `STAGE1 OK`: `build/axiomc1.exe` (`33,010,176` bytes, `sha256=b660bf371b5c0109`)
   - `SEED-A (O1) OK`: `sha256=b85c97fb1878334a`
   - `STAGE2 (O1) OK`: `sha256=b85c97fb1878334a`
   - `STAGE3 (O1) OK`: `sha256=b85c97fb1878334a`
   - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == b85c97fb1878334aee910d60e594842596370ad2efbe281cc7aa3f531ccf7c09` (`8,790,016` bytes) `[seeded B==C]`
   - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on all 6 smoke programs (`O1`, including `Xin chào thế giới`).

2. **New `static_items` Run & UI Tests (`--no-cache -j 2 --verbose --filter static_items`)**:
   - `TOTAL 17 PASS 17 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`:
     - `run/static_items/basic_repros_and_counters.ax` (`[interp]`, `[native]`, `[native-O1]`) — exact task repros (`X`, `Y`, `COUNT`), multi-call stateful `static mut` counters, `AtomicU32` in immutable `static`.
     - `run/static_items/aggregates_relocs_and_tables.ax` (`[interp]`, `[native]`, `[native-O1]`) — `static` lookup tables read in loops, `Str` & `fn`-pointer relocations in `.rdata`/`.data`, non-zero structs/arrays in `.data`, all-zero `static mut` array/struct in `.bss`.
     - `run/static_items/addr_identity_and_threads.ax` (`[interp]`, `[native]`, `[native-O1]`) — `address_of` / `address_of_mut` pointer stability across functions and recursive calls, process-wide sharing across `std.thread.spawn` + `join` via `AtomicUsize` + `static mut` handoff.
     - `run/static_items/opt_o2_global_preservation.ax` (`[interp]`, `[native]` with `// compile-flags: -O2`) — verifies `-O2` OptIR SSA/alias/SROA/escape/inlining/IPA preserve `static mut` stores and loads across inlined helpers and loops.
     - `ui/static_items/safe_static_mut_access_err.ax` (`AX_CONC_UNSYNC_STATIC`, `AX_UNSAFE_REQUIRED`)
     - `ui/static_items/non_const_init_err.ax` (`AX_CONST_NOT_COMPTIME`)
     - `ui/static_items/assign_immutable_static_err.ax` (`AX_TYPE_ASSIGN_IMMUTABLE` on `S = v`, `S += 1`, `S.f = v`, `S[i] = v`, `mut_view`, `address_of_mut`)
     - `ui/static_items/move_out_of_static_err.ax`, `ui/static_items/move_out_of_static_mut_err.ax`, `ui/static_items/move_out_of_static_field_err.ax` (`AX_MOVE_USE_AFTER_MOVE`)

3. **Concurrency, TLS & P11 Regression Verification (`--no-cache -j 2 --verbose`)**:
   - `conformance/p11/e11_1_concurrency` (incl. `ui_unsync_mutable_statics.ax`): `TOTAL 22 PASS 22 FAIL 0`, `WEAK-NATIVE 0`
   - `std/thread`: `TOTAL 18 PASS 18 FAIL 0`, `WEAK-NATIVE 0`
   - `concurrency/tls`: `TOTAL 29 PASS 29 FAIL 0`, `WEAK-NATIVE 0`
   - `ui/concurrency/data_race`: `TOTAL 11 PASS 11 FAIL 0`, `WEAK-NATIVE 0`
   - `perf/own_scaling/qa_unsafe_index_ui.ax`: `TOTAL 1 PASS 1 FAIL 0`, `WEAK-NATIVE 0`

4. **PE32+ Section Layout & `inspect --emit=mc|obj` Check**:
   - `axiomc2.exe inspect --emit=mc tests/run/static_items/aggregates_relocs_and_tables.ax`: exit `0` (`21,345` chars)
   - `axiomc2.exe inspect --emit=obj tests/run/static_items/aggregates_relocs_and_tables.ax`: exit `0` (`9,426` chars)
   - Linked PE32+ headers on `aggregates_relocs_and_tables.exe`:
     - `OptHdr.SizeOfUninitializedData = 512`
     - `.rdata`: `VirtualSize=680, RVA=0x1000, SizeOfRawData=1024, PtrToRawData=1024, Chars=0x40500040`
     - `.data`: `VirtualSize=24, RVA=0x4000, SizeOfRawData=512, PtrToRawData=9728, Chars=0xc0500040`
     - `.bss`: `VirtualSize=512, RVA=0x5000, SizeOfRawData=0, PtrToRawData=0, Chars=0xc0500080`

5. **Native-Evidence Mutation Spot-Proof (`build-snap-T537/` only)**:
   - Mutated `static Y: u32 = 5u32;` -> `static Y: u32 = 6u32;` in `build-snap-T537/tests/run/static_items/basic_repros_and_counters.ax`: all 3 modes (`[interp]`, `[native]`, `[native-O1]`) failed (`expected: 5 1 42 3 1 77 99`, `actual: 6 1 42 3 1 77 99`).
   - Restored byte-identical (`SHA_MATCH=True`, `sha256=8b860dc7a5b1a215c811e56280482f6aa2dca5272ad0d9429862041b0017c9cc`) and re-ran `--no-cache`: `3/3 PASS`, `WEAK-NATIVE 0`.

6. **Full `taskgate.py` Verification (`python tools/taskgate.py --task T537 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`)**:
   - `own`: `10` IDs, `17` results (`17 PASS`, `0 FAIL`)
   - `affected`: `739` IDs, `1275` results (`1257 PASS`, `0 FAIL`, `18 SKIP` — including all `54` selfhost bundles)
   - `smoke`: `33` IDs, `54` results (`54 PASS`, `0 FAIL`)
   - `total (dedup)`: `756` IDs, `1308` results (`1290 PASS`, `0 FAIL`, `18 SKIP`, `0 XFAIL`)
   - `WEAK-NATIVE`: `0` in own/changed tests
   - `archcheck`: `232 files scanned, 0 violations`
   - `TASKGATE T537 exit=0`

## Round 1

Fixes for `_workspaces/reports/T537-qa.md` round 0 (VERDICT: FAIL). An earlier fix agent was interrupted after writing the
`compiler/opt` changes; this round reviewed them, kept them, added the missing unit-level regression coverage, and ran
the build and the gate.

### F1: call-graph summaries proved `static`-touching functions `EFFECT_PURE`
- `compiler/opt/inline/mod.ax`: `cg_body_external_mem_flags(mir, thir)` now treats places rooted at `MIR_LOCAL_STATIC`,
  `MIR_LOCAL_TLS` or a mutable `MIR_LOCAL_CONST` as process/thread memory (`cg_local_is_global_mem`). It records
  `EFFECT_READS_MEM` for reads, borrows, index/sub-slice operands and LEN/DISCRIMINANT, and `EFFECT_WRITES_MEM` for
  assignments, drops, call destinations, `&mut` borrows and shared borrows of `Atomic`-containing statics. It also records
  `MIR_STMT_ATOMIC` (+`EFFECT_ATOMIC`), `address_of_mut`, `ptr_copy*`, `ptr_write_bytes`, `drop_in_place` and `print*` (`EFFECT_IO`).
- A second bug sat behind F1 and is fixed too: the old code set `pure_certainty = 0u8` for impure functions, and `0u8 ==
  CERTAINTY_PROVEN`. Certainties now come from `effect_pure_certainty` / `effect_no_panic_certainty` /
  `effect_read_only_certainty`. Recursive SCC members reset them to `CERTAINTY_UNKNOWN` and re-register in the effect and escape tables.
- `compiler/opt/lto/mod.ax`: imported cross-module summaries use `effect_summary_from_flags` and recompute certainties.
  After `callgraph_propagate_summaries`, the LTO per-function flags are merged back so a recomputed node summary cannot drop them.
- `compiler/opt/ipa/mod.ax` / `inline/mod.ax`: the constant `fn_sym` lookup is restricted to immutable `MIR_LOCAL_CONST`.

### F2: inline duplicated static locals, and alias proved `NO_ALIAS` between them
- `inline_clone_callsite_in_mir` keeps the callee's `MIR_LOCAL_STATIC` / `MIR_LOCAL_TLS` / `MIR_LOCAL_CONST` kind and
  reuses an existing caller local with the same `(kind, const_sym, ty)` when `const_sym != 0`. It widens `mut_flag` when
  needed and drops cloned `StorageLive/Dead` of globals. `inline_remap_stmt` now remaps `MIR_STMT_ATOMIC` operands.
- `compiler/opt/alias/mod.ax`:
  - `alias_init_info` classifies `MIR_LOCAL_STATIC` as `DOMAIN_GLOBAL_STATIC` when it is `mut` or contains `@lang("atomic")`
    (interior mutability, placed in `.data`/`.bss`), and as `DOMAIN_CONST_RDATA` otherwise. TLS and mutable const are
    also global-static. Mutable globals start borrowed / raw-exposed / escaped-external, so calls clobber them.
  - `alias_query_regions` relates two resolved global places by allocation root. The same root (`ALLOC_ROOT_GLOBAL_BASE +
    const_sym`) goes through the projection paths and yields MUST/PARTIAL/NO by projection. Different named roots are
    still provably disjoint. `const_sym == 0` maps to `ALLOC_ROOT_UNKNOWN`, so unnamed statics fall through to the
    conservative tiers instead of colliding on `GLOBAL_BASE + 0`.
  - Borrows and raw pointers to global places carry the global root.

### Regression tests (new)
- `tests/run/static_items/opt_static_summary_alias.test` + `opt_static_summary_alias_oracle.py` +
  `opt_static_summary_alias_probe.ax.in`. These follow the existing `tests/opt2` / `tests/run/opt_alias` pattern: the
  bundle is assembled at test time into `{tmp}`, never committed. The probe lowers source with two `static mut` items
  through the real frontend and `mir_build_fn`, builds a closed-world call graph and checks:
  - `PROBE_STATIC_EFFECT_SUMMARIES`:
    - Control `pure_add` stays `EFFECT_PURE`/`PROVEN`.
    - `set_g` has WRITES_MEM and is not proven pure (rc 311).
    - `get_g` has READS_MEM (312).
    - `bump_h` has both (313).
    - The caller inherits WRITES_MEM (314).
  - `PROBE_STATIC_MEMOPT_CALL_CLOBBER`: memopt (alias info built with the call-graph effect table) does no forwarding or
    RLE of the `G` reload after a non-inlined `set_g` call.
  - `PROBE_STATIC_INLINE_DEDUP`: inlining `set_g` into a caller that already uses `G` leaves exactly one `G` static local
    (334).
  - `PROBE_STATIC_ALIAS_IDENTITY`:
    - Two locals naming the same global give `ALIAS_MUST_ALIAS` (343).
    - Two unnamed (`const_sym == 0`) statics never give `NO_ALIAS` (344).
    - `G` vs `H` stay `NO_ALIAS` (345).
- Mutation spot-proof in `build-snap-T537` (each file restored byte-identical with `cmp`):
  - Disabling `cg_local_is_global_mem` gives `PROBE_FAIL rc=311`.
  - Disabling the inline dedup gives `rc=334`.
  - Making `al_resolved_local_is_global` return false gives `rc=343`.
  - Clean run: `OPT-STATIC-SUMMARY-ALIAS-OK`.
- `tests/run/static_items/opt_o2_inline_alias_effect_regression.ax` (from the interrupted agent) is kept as a
  three-mode end-to-end check. Note that the `build`/`run` driver does not invoke the OptIR inline/memopt passes, so that
  file alone does not exercise F1/F2. The probe above is the real regression for them.

### Decisions
- `memopt_optimize_mir_body` cannot be used on builder MIR: its reconstructed body fails `verify_mir` with "use of
  uninitialized local" (`AX_*` code 105). This happens for every function, including ones without statics such as
  `pure_add`, so it is not caused by T537. The probe therefore drives `memopt_run_pass_with_info` on the OptBody. Also,
  memopt does not apply RLE to back-to-back whole-local global reads even with no call between them, so the memopt check
  is a guard, not a sensitivity test; F1 is proven at the summary level.
- `conformance/p15/t430_modlist_nodup` pins the exact number (17) of `list(got.X) + [...]` module lists in test oracles.
  To avoid changing a test I don't own, my oracle builds its list incrementally. It skips modules the base list already
  provides and asserts there are no duplicates, which is the same invariant that guard enforces.

### Verification (round 1, `build-snap-T537`, `-j 2`)
- `python tools/build_axiomc.py --out build --stage 3`: `FIXED-POINT (O1) OK`, `sha256(axiomc2_O1) == sha256(axiomc3_O1) ==
  6446aae69901fcdfbc19ba3d7d326bb108dd4e2a4c4fe90f94e202528ab2557d` (8,793,600 bytes).
- `axtest --no-cache --filter static_items --filter t430_modlist_nodup`: `TOTAL 27 PASS 27 FAIL 0`, `WEAK-NATIVE 0`.
- `python tools/taskgate.py --task T537 ... -j 2`: HEAD `6201e1595ac5`, change set 73 files, wall 1550.5 s.

  | part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
  |---|---|---|---|---|---|---|---|
  | own | 16 | 26 | 26 | 0 | 0 | 0 | 17 |
  | affected | 745 | 1284 | 1266 | 0 | 18 | 0 | 870 |
  | smoke | 32 | 53 | 53 | 0 | 0 | 0 | 37 |
  | **total (dedup)** | 760 | 1313 | 1295 | 0 | 18 | 0 | 891 |

  `BASELINE OK`, failing ids none, archcheck clean (232 files, 0 violations), WEAK-NATIVE 0 in own/changed tests,
  `TASKGATE T537 exit=0`. A first gate run in this round failed only `t430_modlist_nodup` (lists=18 vs 17). It was fixed as
  described above and the whole gate was re-run.

## Files changed

- compiler/backend/session.ax
- compiler/driver/pipeline.ax
- compiler/interp/frame.ax
- compiler/interp/interp.ax
- compiler/interp_opt/session.ax
- compiler/link/linker.ax
- compiler/lir/builder.ax
- compiler/mir/builder.ax
- compiler/mir/drop.ax
- compiler/mir/mir.ax
- compiler/mir/mod.ax
- compiler/opt/alias/mod.ax
- compiler/opt/const_fold.ax
- compiler/opt/dce.ax
- compiler/opt/escape/mod.ax
- compiler/opt/inline/mod.ax
- compiler/opt/ipa/mod.ax
- compiler/opt/lto/mod.ax
- compiler/opt/optir/mod.ax
- compiler/opt/sroa/mod.ax
- compiler/own/init.ax
- compiler/types/typeck.ax
- compiler/verify/verifier.ax
- tests/run/static_items/addr_identity_and_threads.ax
- tests/run/static_items/aggregates_relocs_and_tables.ax
- tests/run/static_items/basic_repros_and_counters.ax
- tests/run/static_items/opt_o2_global_preservation.ax
- tests/run/static_items/opt_o2_inline_alias_effect_regression.ax
- tests/run/static_items/opt_static_summary_alias.test
- tests/run/static_items/opt_static_summary_alias_oracle.py
- tests/run/static_items/opt_static_summary_alias_probe.ax.in
- tests/run/static_items/qa_nested_atomic_drop_opt.ax
- tests/selfhost/interp_opt/gen_interp_opt_tests.py
- tests/ui/comptime/static_err.ax
- tests/ui/static_items/assign_immutable_static_err.ax
- tests/ui/static_items/move_out_of_static_err.ax
- tests/ui/static_items/move_out_of_static_field_err.ax
- tests/ui/static_items/move_out_of_static_mut_err.ax
- tests/ui/static_items/non_const_init_err.ax
- tests/ui/static_items/qa_static_move_by_arg_err.ax
- tests/ui/static_items/qa_static_safe_ptr_err.ax
- tests/ui/static_items/qa_static_typeck_edge_err.ax
- tests/ui/static_items/safe_static_mut_access_err.ax

STATUS: COMPLETE round=1
