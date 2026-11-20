# T444 report — layout through forward-referenced pointees (FU-1) and lang-item fields in std modules (FU-3)

## Root cause (both FU-1 and FU-3)

Not in `layout.ax`. `typeck_pass1a` registered struct/enum types strictly in item order (std/prelude items first, then user items). Any field type naming a struct or enum that was **not yet registered** resolved to the error type (`lookup_path_type` / `lookup_path_type_by_name` returned `t_error` when the item type was still `0`). The error type has size 0, so every field behind it landed at offset 0:

- **FU-1:** `struct W { id: usize, inner: *mut Inner }` declared before `struct Inner { count: usize, ptr: *mut u8 }` typed `inner` as `*mut <error>`; reading `(*(*w).inner).ptr` read offset 0 (interp `0` / native first word). Self-referential structs (`struct Node { next: *mut Node }`) and mutual pointer cycles failed the same way.
- **FU-3:** the prelude declares `RawWaker { data: *const u8, vtable: *const RawWakerVTable }` **before** `RawWakerVTable`, and a node struct in a `std.*` module is registered during the std/prelude pass (possibly before `Waker` itself). In a non-std module (`zz.yy`) all std types were already registered, which is why `zz.yy` worked. No special `@lang("waker")` handling was involved.
- A forward **enum** used as a field type was rejected with `AX_NAME_UNRESOLVED` (e.g., `struct HoldsE { e: Choice }` before `enum Choice`, or self-referential generic enum `enum GTree<T> { Branch(u64, *mut GTree<T>) }`).

## Fix

1. **On-demand struct/enum registration (`compiler/types/typeck.ax` — `tc_item_type_on_demand`):** all four struct/enum lookup sites in `lookup_path_type` (indexed + linear scan) and `lookup_path_type_by_name` (struct + enum) register an unregistered struct/enum item on demand instead of falling back to `t_error` (preserving the existing synthetic-unit-test guard when `str_in == 0 && db == 0`).
2. **Shell-first ADT registration (`compiler/types/typeck.ax` — `tc_register_single_struct`, `tc_register_single_enum`):** each function checks for already-registered items, saves/restores `current_fn`/`current_impl`/`self_ty`, interns a field-less shell (identity = `def` + `args`) and records it via `thir_set_item_type` *before* converting field/variant types, then fills `fields`/`field_count`/`is_repr_c` (or `variant_fields`/`variant_field_counts`/`variant_count`) into the interned `AxType` in place. Pointer/fn cycles (`L.next: *mut L`, `Ping <-> Pong`, `RawWaker -> *const RawWakerVTable -> fn(..) -> RawWaker`) resolve to the in-progress `TypeId`.
3. **Refresh of generic shells (`compiler/types/typeck.ax` — `tc_subst_ids`, `tc_refresh_adt_instances`):** called at the end of `typeck_pass1a` so any generic struct/enum instance interned while its definition was still an empty shell during a mutual generic cycle (e.g., `struct GA<T> { b: *mut GB<T> }` / `struct GB<T> { a: *mut GA<u8> }`) gets its fields/variants populated from the completed definition substituted with the instance's type arguments.
4. **Cycle-safe shell-first substitution in `compiler/types/types.ax` (`subst_adt_with_vars`)** (ADR-0043 §1, INV-SEM-008): struct/enum identity is `def + args` (`key_eq_type`), so non-generic ADTs or ADTs with unchanged args return unchanged; when args change, `typemap_get` checks for an existing instance by `def + new_args`, and otherwise interns a field-less shell first before substituting fields/variants and patching them in.
5. **Cycle-safe shell-first substitution in `compiler/traits/mono.ax` (`subst_ty_adt`, `subst_ty_enum_or_closure`)** (ADR-0043 §1, INV-SEM-008): same contract as `types.ax` — return the input `TypeId` unchanged when `arg_count == 0` or no generic argument changes; when arguments change, look up by `def + new_args` via `typemap_get`, intern a field-less shell if new, then substitute fields/variant payloads and patch them into the interned `AxType`. This prevents infinite recursion on both non-generic cycles (prelude `RawWaker`) and generic cycles whose arguments change (`GNode<T>`, `GTree<T>`, `async_channel_pipeline.ax`).

## Regression tests (`tests/run/layout_fwd_pointee/`)

All 4 tests run in `interp`, `native`, and `native-O1` with exact `// stdout:` (`WEAK-NATIVE 0`):

- `fwd_pointee_basic.ax` — FU-1 repro (`struct W` before `struct Inner`, heap-allocated reads/writes through `(*(*wp).inner)`).
- `std_module_waker_field.ax` — FU-3 repro (identical `Node` with `Waker` field in `std.asyn.zz` and `zz.yy`, verifying `.id`, `.waker.raw.data`, `.waker.raw.vtable`, `.tail`).
- `fwd_permutations.ax` — by-value later struct, self-referential node, mutual pointers (`Ping`/`Pong`), later generic struct behind pointer, later enum by value, 3-level reverse-declared pointer chain, and `size_of` checks.
- `fwd_generic_cycle.ax` — swapped FU-1 declaration order (`InnerS` before `WS`), generic self-referential struct `GNode<T>` instantiated with `u64` and `u32` via generic functions, mutual generic cycle `GA<T>` / `GB<T>` exercising `tc_refresh_adt_instances`, generic cyclic enum `GTree<T>`, and an additional `std.*` module path (`std.core.zz_waker_perm`) with a `Waker` field.

## Verification (in `build-snap-T444/`, HEAD `f0f98f33`)

- **Snapshot & bundles:** `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T444` -> refreshed `HEAD f0f98f3 + 8 changed`, 36 generator(s), 154 bundle file(s) regenerated cleanly.
- **Bootstrap stage 1–3 (`python tools/build_axiomc.py --out build --stage 3`):**
  - `STAGE1 OK`: `axiomc1.exe` (`27426304` bytes, `sha256=3200c81c5d7ca8b3`)
  - `STAGE2 (O1) OK` / `STAGE3 (O1) OK`: `axiomc2.exe` / `axiomc3.exe` (`8461312` bytes)
  - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 4d09bc6ee3d8ada64eb16a268afc1da58cf1e828bce5c36a22e1c999bc14b90c`
  - `STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on 6 smoke program(s) (O1, incl. Xin chào thế giới)`
- **T444 tests (`--no-cache`, `-j 2`, `--filter layout_fwd_pointee`):**
  - Baseline HEAD `f0f98f33` (`axiomc2_O1_8d0b29227c12f9d1.exe`, `sha256=e0299a23aed0c822`): `TOTAL 12 PASS 0 FAIL 12` (all 12 legs fail: zero/shifted reads on FU-1 & FU-3, `AX_NAME_UNRESOLVED` on forward/self-ref enums).
  - T444 (`build/axiomc2.exe`, `sha256=4d09bc6ee3d8ada6`): `TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- **Taskgate (`python tools/taskgate.py --task T444 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):**
  - `TASKGATE T444 exit=0`
  - `axtest: TOTAL 384 PASS 383 FAIL 0 SKIP 1 XFAIL 0` (own 4 ids / 12 pass; affected 157 ids / 335 pass, 1 skip; smoke 31 ids / 50 pass)
  - `WEAK-NATIVE: 15 in the run; 0 in the task's own/changed tests`
  - `Baseline: BASELINE OK`, `Failing ids: none`
  - `archcheck: clean (exit 0) archcheck: 229 files scanned, 0 violations`
- **`tests/std/async` (`--no-cache`, `--filter std/async`):**
  - 94/96 legs pass (including `std/async/executor/async_channel_pipeline.ax [interp]`, confirming the attempt-1 generic-cycle stack overflow is gone; `qa_wake_during_poll.ax` hit one load-sensitive stall under `-j 2` and passed 3/3 on 3 consecutive `-j 1` runs).
  - The remaining 2 failing legs are `std/async/executor/async_channel_pipeline.ax [native]` and `[native-O1]`, which fail **identically on HEAD `f0f98f33`** (see Follow-up F4 below).

## Follow-ups (pre-existing, outside T444 scope)

- **F4 (pre-existing HEAD regression from T489 `f0f98f33`, `compiler/mir/builder.ax`):** `tests/std/async/executor/async_channel_pipeline.ax` fails in `[native]` and `[native-O1]` with:
  `error[AX_LINK_UNDEFINED_SYMBOL]: undefined symbol 'close' (mangled: 'close') referenced by 'async_channel_pipeline.obj' in section '.text' (in function 'AsyncSender.drop')`
  Verified directly against cached compilers:
  - Pre-T489 HEAD `689f7dea` (`axiomc2_O1_74139d179be888d3.exe`): `TOTAL 3 PASS 3 FAIL 0`.
  - HEAD `f0f98f33` (`axiomc2_O1_8d0b29227c12f9d1.exe`, T489): `TOTAL 3 PASS 1 FAIL 2` (exact same `undefined symbol 'close'` in `AsyncSender.drop` on `[native]` and `[native-O1]`).
  - T444 (`build/axiomc2.exe`): `TOTAL 3 PASS 1 FAIL 2` (exact same error; `[interp]` passes with no stack overflow).
  Cause: T489 made inherent methods of generic impls (`impl<T> AsyncSender<T> { pub fn close(...) }`) generic in `compiler/mir/builder.ax:11167`, while `impl<T> Drop for AsyncSender<T>` is excluded from generic monomorphization (`mb_impl_is_lang_drop`), so `AsyncSender.drop` calls the un-monomorphized symbol `close` which is no longer emitted. (`compiler/mir/builder.ax` is outside T444's `paths`/`locks`.)
- **F1 / F2 (from attempt 1):** tracked as `T444b` / `T444a`; `fwd_permutations.ax` and `fwd_generic_cycle.ax` stay independent of them.

## Files changed
- compiler/traits/mono.ax
- compiler/types/typeck.ax
- compiler/types/types.ax
- tests/run/layout_fwd_pointee/fwd_generic_cycle.ax
- tests/run/layout_fwd_pointee/fwd_permutations.ax
- tests/run/layout_fwd_pointee/fwd_pointee_basic.ax
- tests/run/layout_fwd_pointee/std_module_waker_field.ax

## Status
STATUS: COMPLETE round=0
