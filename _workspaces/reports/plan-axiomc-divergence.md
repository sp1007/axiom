# Plan — axiomc/axiom0 divergence registry (T085 QA finding 3)

## Tóm tắt
- Đầu vào: `known_divergent.txt` của T085 liệt kê 144/268 chương trình mà `axiomc` dịch ra không giống byte
  với axiom0 (58 same-behaviour, 22 different-behaviour, 64 no-image). Kiến trúc sư đã thăm dò **từng mục**
  bằng `build-snap-T085/build/axiom0.exe` và `axiomc.exe` do gate T085 build (so sánh object -O0 theo từng
  section/relocation/ký hiệu, đếm assert trong MIR, chạy thử ảnh, tìm stage bị crash). Không chạy suite nặng.
- Kết luận: cột "stage" của registry chỉ là gợi ý (nhiều khác biệt chỉ nằm ở dump); 10 nhóm nguyên nhân gốc.
  Nghiêm trọng nhất: ký hiệu chuỗi `.Lstr.<id>` trùng giữa các hàm + linker port gộp ký hiệu STATIC theo tên
  (15 chương trình drop in sai chuỗi), axiom0 đặt tên chuỗi theo địa chỉ heap (không tất định). Nhiều mục
  "same-behaviour" che giấu lỗi thật: mất kiểm tra biên slice, mất kiểm tra `as char`, `(*self).1` bị dịch thành
  `.0`, tham số `self` của destructor nằm ở RAX thay vì RCX.
- Quyết định (ADR-0035): đặt tên ký hiệu dữ liệu cục bộ tất định, linker phân giải theo chỉ số ký hiệu, **không
  chấp nhận loại khác biệt byte nào** (timestamp đã = 0), registry chỉ được xoá không được thêm, phải rỗng trước
  T086; dump và chẩn đoán cũng phải trùng.
- Task mới: T147 (AX0-FIX-05, sửa cả axiom0 lẫn port, priority 0), T148–T156 (sửa port theo chủ module);
  tất cả sau T146; T086 phụ thuộc cả 10 task. Mọi `different-behaviour` (22) đều có task chặn T086.

## Method
Probe script (scratchpad, not committed): for each registry entry, `axiom0 build --emit=obj` twice and
`axiomc build --emit=obj` once (`--std-root std`, -O0); determinism of axiom0; per-section data, relocation
targets (resolved to section+offset) and defined symbols compared, string-symbol names normalised; for
rejected programs the first axiomc diagnostic or crash code. Follow-ups by hand: MIR/LIR/MI dumps with type ids
normalised, assert counts, running both images, first crashing `inspect` stage, symbol tables (objdump), and the
linker/emitter source (`compiler/link/linker.ax` ~380, `build.c` 498/559, `emit_obj.c` 496,
`compiler/backend/session.ax` ~1358, `compiler/lex/scanner.ax` ~873, `isel.c` 23-55 vs `isel.ax` ~975-1017).
The two `objeq=True` entries were re-probed at -O1 and for exe output.

## Root-cause classes

| Task | Class | Module owner (paths) | Entries (sole cause) | different-behaviour | Fix scope |
|------|-------|----------------------|----------------------|---------------------|-----------|
| T147 | String/panic data-symbol naming; linker resolves STATIC by name (port) / by name only (axiom0); axiom0 names by heap address (non-deterministic) | axiom-backend: compiler/backend, compiler/driver/pipeline.ax, compiler/link, compiler/obj; axiom0 driver/build_native, emit_obj.c, link | 54 (24) | 15 (drop/*, string collision) | axiom0 + port (AX0-FIX-05) |
| T148 | `build`-path lowering differs from `build.c`: destructor `self` passed in RAX not RCX; axiom0 `inspect` ≠ `build` inputs | axiom-backend: compiler/driver, compiler/backend, compiler/lir, compiler/abi; axiom0 driver | 24 (0; all drop/* with T147) | 0 (latent) | port + axiom0 inspect path |
| T149 | Port MIR builder: slice bounds check and `as char` check missing, `for` step 0, `(*self).1`→`.0`, extra index temporaries | axiom-semantics: compiler/mir, compiler/hir | 22 (16) | 5 (for ranges 2, panic_char 3) | port |
| T150 | Port intrinsics/raw pointers: `address_of*`/`null*` rejected, `size_of`/`align_of`/`needs_drop` placeholder bodies compiled and called, pointer arithmetic rejected by verifier | axiom-semantics: compiler/types, typeck, mir, lir, verify | 26 (22) | 1 (ptr/layout_intrinsics) | port (axiom0 half = T134) |
| T151 | Port typeck generics (calls, literals, variant paths, `?`); typeck stack overflow 0xC00000FD on ranges / for-in-array / operator traits | axiom-semantics: compiler/types, typeck, typeck_traits, traits, resolve, hir, mir | 22 (22) | 0 | port |
| T152 | Closures/fn pointers: typing; closure bodies emitted under wrong/missing symbols (`x`, `__ax_fn_1073741825`) | axiom-semantics: compiler/types, typeck, mir, lir, own, driver, backend | 10 (10) | 0 | port |
| T153 | Trait items in build path: bare method symbols, default methods not instantiated, derive collisions, `Self.Item` unresolved | axiom-semantics: compiler/resolve, types, typeck_traits, traits, driver, backend | 4 (4) | 1 (trait2/test_default_override) | port (axiom0 if it shares a collision) |
| T154 | Backend: narrow-value extension `shr` vs `sar` (one side wrong), -O1 LIR path, const-table `.rdata` content | axiom-backend: compiler/target/x64, lir, opt, backend; axiom0 target/x64, lir, build_native | 7 (7) | 0 | whichever side is wrong; both if needed |
| T155 | Natively built axiomc lexer panics `arithmetic overflow` on 20-digit literals | axiom-frontend: compiler/lex, compiler/lexer | 8 (4) | 0 | port, or BLOCKED → AX0-FIX if axiom0 codegen |
| T156 | Dumps (`PathSegment @Sym`, type interning order) and diagnostic message texts; oracle extended to dumps; registry empty | axiom-frontend: compiler/resolve, resolve_hir, types, typeck, diag, hir, mir | 1 (1) | 0 | port + oracle |

Counts: 144 entries, 110 with one cause, 34 with two (T147+T148 24, T147+T149 6, T155+T150 4). "Entries" counts
every entry the class contributes to; a multi-cause entry is removed by whichever of its tasks lands last (the
oracle's XPASS line says when).

No class of acceptable ("benign") byte difference was found: COFF and PE `TimeDateStamp` are 0 in both compilers,
no path is embedded, symbol order is deterministic once names are deterministic. Every byte difference traced to a
real defect or a real divergence of the port from its reference, several of them hidden behind `same-behaviour`.

## Decisions and rationale
1. **ADR-0035 §1–§2 (naming + linking).** Object-local `.Lstr.<f>.<k>` / `.Lpanic.<n>`, defined once, and
   index-based resolution of same-object references in both linkers. Linking by index is the COFF semantics and
   makes correctness independent of names; deterministic names give byte identity and readable tools output.
   Alternative "object-wide counter" rejected only for cost (threads a counter through isel of both compilers).
2. **ADR-0035 §3 (zero tolerance).** Rejected a normalised comparison: the probe found miscompiles in exactly the
   "benign-looking" class, and T086's `--emit=obj` equality and T087's stage2 == stage3 need exact bytes. Dumps and
   diagnostic texts included because T086 runs the dump/ui goldens with axiomc1. Revisit flagged for message text.
3. **ADR-0035 §4 (registry maintenance).** The oracle already fails on XPASS/IMPROVED; the rule makes removal
   explicit, forbids additions, and is written into T134/T140/T141/T146 (which run first and may change entries).
4. **ADR-0035 §5 (`build` is the reference).** axiom0 has two lowering paths (`build.c` vs the `inspect`
   emitters pass different function types to LIR lowering); the port copied a mix. `build` is what ships, so the
   port follows it and axiom0's `inspect` is aligned (T148).
5. **Ordering.** All ten tasks depend on T146 (the last AX0-FIX task, whose paths cover all of `compiler/`,
   `std/`, `tests/`, and whose terminator sweep may change ported code). T147 is AX0-FIX-05 (priority 0, runs
   alone, ADR-0034 §2/§5). Real dependencies only: T148 after T147 (same drop entries, same build path), T152/T153 after T151 (generic closures and default methods need
   instantiation), T156 after all (closure, registry empty). Every task has `tests/selfhost` in `paths`, so the
   scheduler serialises them; priorities 116/117/118 keep them before T086 (120) and after T144/T145 (115).
6. **Path overlap with T134/T140/T141/T146.** All overlap on `tests/selfhost` and `compiler/*`; resolved by the
   dependency on T146 (transitively on T134 → T140 → T141). The AX0-FIX chain rule holds: T147 fixes axiom0 and the
   port together; T148/T154 include axiom0 paths for their lockstep part; T155 has no axiom0 path and must BLOCK
   with a repro if the cause is axiom0 codegen (expected candidates T134/T140, noted in T140).
7. **Regression tests.** Each task adds `tests/run/parity/<topic>/*.ax` with hand-derived `stdout:`/`exit:`
   (category A, ADR-0034 §1), run by axiom0 in interp and native, and automatically part of the e2e corpus, so the
   oracle shows axiomc's image behaves the same; T147 also adds a Python-generated COFF object for the linkers.
8. **Models.** sonnet for all but T151 (opus: inference/instantiation with design judgement); gate opus for all
   (behaviour bugs, and the final registry closure in T156).
9. **T086** depends on T147–T156 and gains "registry empty + `axiomc_e2e.test` passes" as acceptance.

## Classification of every registry entry
`*` columns: Stage and Behaviour as recorded in the registry; evidence from the -O0 object probe (`a0 nondet` =
two axiom0 builds differ; `.sec data A/B @off` = section sizes axiom0/axiomc and first differing offset;
`relocs` = relocation lists differ after resolving targets; `defsyms` = defined symbols differ).

| # | Program | Stage (registry) | Behaviour | Probe evidence (obj -O0) | Root-cause tasks |
|---|---------|------------------|-----------|--------------------------|------------------|
| 1 | `programs/expr_interp.ax` | resolved | same-behaviour | a0 nondet; .rdata data 1479/1425 @54,.text data 38196/37652 @8529,.text relocs 114/110,defsyms 57/55 | T147+T149 |
| 2 | `programs/json_parser.ax` | mir | same-behaviour | a0 nondet; .rdata data 1246/1248 @70,.text data 42708/43076 @97,.text relocs 93/93,defsyms 48/48 | T147+T149 |
| 3 | `programs/sorting.ax` | resolved | same-behaviour | a0 nondet; .rdata data 1534/838 @84,.text data 47556/38356 @13970,.text relocs 139/89,defsyms 62/37 | T147+T149 |
| 4 | `programs/tokenizer.ax` | resolved | same-behaviour | a0 nondet; .rdata data 1716/1156 @743,.text data 70292/62548 @97,.text relocs 133/93,defsyms 68/48 | T147+T149 |
| 5 | `programs/word_count.ax` | mir | same-behaviour | a0 nondet; .rdata data 205/212 @65,.text data 21876/21940 @97,.text relocs 16/16,defsyms 10/10 | T147+T149 |
| 6 | `run/array/array_basics.ax` | mir | same-behaviour | .text data 9284/9284 @1253 | T154 |
| 7 | `run/array/array_bounds.ax` | mir | same-behaviour | .text data 1180/1252 @98,.text relocs 2/2 | T149 |
| 8 | `run/array/array_bounds_neg.ax` | mir | same-behaviour | .text data 1503/1578 @98,.text relocs 4/4 | T149 |
| 9 | `run/array/qa_array_bounds_write.ax` | mir | same-behaviour | .text data 1071/1143 @98,.text relocs 2/2 | T149 |
| 10 | `run/array/qa_nested_array_bounds.ax` | mir | same-behaviour | .text data 2054/2201 @98,.text relocs 4/4 | T149 |
| 11 | `run/array/qa_nested_arrays.ax` | mir | same-behaviour | .text data 3353/3353 @3050 | T154 |
| 12 | `run/closure/capture_modes.ax` | mir | no-image | .text data 4976/4976 @1804,.text relocs 7/7,defsyms 8/8 | T152 |
| 13 | `run/closure/closure_types.ax` | obj | no-image | .text relocs 6/6,defsyms 7/7 | T152 |
| 14 | `run/closure/fn_pointers.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T152 |
| 15 | `run/closure/fn_traits.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T152 |
| 16 | `run/closure/generic_fns.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T152 |
| 17 | `run/closure/qa_fn_ptr_args.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T152 |
| 18 | `run/closure/qa_mixed_captures.ax` | mir | no-image | .text data 5023/5023 @3143,.text relocs 7/7,defsyms 7/7 | T152 |
| 19 | `run/closure/qa_move_capture.ax` | obj | no-image | .text relocs 2/2,defsyms 5/5 | T152 |
| 20 | `run/closure/syntax.ax` | mir | no-image | .text data 5477/5568 @2962,.text relocs 15/15,defsyms 13/13 | T152 |
| 21 | `run/comptime/qa_table_struct_str.ax` | obj | same-behaviour | .rdata data 264/264 @0 | T154 |
| 22 | `run/comptime/qa_table_u8_loop.ax` | mir | same-behaviour | .text data 2255/2330 @98,.text relocs 7/7 | T149 |
| 23 | `run/comptime/table_str.ax` | obj | same-behaviour | .rdata data 156/156 @0 | T154 |
| 24 | `run/drop/001.ax` | obj | different-behaviour | a0 nondet; .rdata data 6/16 @3,.text data 2547/2547 @1699,.text relocs 9/9 | T147+T148 |
| 25 | `run/drop/002.ax` | obj | different-behaviour | a0 nondet; .rdata data 6/16 @3,.text data 2030/2030 @1381,.text relocs 8/8 | T147+T148 |
| 26 | `run/drop/003.ax` | obj | same-behaviour | a0 nondet; .rdata data 3/8 @3,.text data 1985/1985 @1336,.text relocs 6/6 | T147+T148 |
| 27 | `run/drop/004_field_wise.ax` | obj | same-behaviour | a0 nondet; .rdata data 3/8 @3,.text data 1318/1318 @1141,.text relocs 4/4 | T147+T148 |
| 28 | `run/drop/005_explicit.ax` | obj | same-behaviour | a0 nondet; .rdata data 15/16 @15,.text relocs 4/4 | T147 |
| 29 | `run/drop/005_partial_move.ax` | obj | same-behaviour | a0 nondet; .rdata data 3/8 @3,.text data 1824/1824 @1281,.text relocs 6/6 | T147+T148 |
| 30 | `run/drop/006_conditional_reassignment.ax` | obj | same-behaviour | a0 nondet; .rdata data 3/8 @3,.text data 1824/1824 @1185,.text relocs 6/6 | T147+T148 |
| 31 | `run/drop/qa_array_drop.ax` | obj | same-behaviour | a0 nondet; .rdata data 3/8 @3,.text relocs 2/2 | T147 |
| 32 | `run/drop/qa_block_scope_drop.ax` | obj | different-behaviour | a0 nondet; .rdata data 13/24 @3,.text data 2143/2143 @1488,.text relocs 10/10 | T147+T148 |
| 33 | `run/drop/qa_cf_cleanup.ax` | obj | same-behaviour | a0 nondet; .rdata data 3/8 @3,.text data 1550/1550 @1088,.text relocs 5/5 | T147+T148 |
| 34 | `run/drop/qa_cf_continue.ax` | obj | same-behaviour | a0 nondet; .rdata data 31/36 @3,.text data 1878/1878 @1597,.text relocs 6/6,defsyms 5/5 | T147+T148 |
| 35 | `run/drop/qa_cf_nested_return.ax` | obj | different-behaviour | a0 nondet; .rdata data 6/16 @3,.text data 2370/2370 @1531,.text relocs 9/9 | T147+T148 |
| 36 | `run/drop/qa_conditional_drop.ax` | obj | different-behaviour | a0 nondet; .rdata data 10/16 @3,.text data 1852/1852 @1130,.text relocs 8/8 | T147+T148 |
| 37 | `run/drop/qa_conditional_drop_false.ax` | obj | same-behaviour | a0 nondet; .rdata data 10/16 @3,.text data 1852/1852 @1130,.text relocs 8/8 | T147+T148 |
| 38 | `run/drop/qa_copy_drop.ax` | obj | same-behaviour | a0 nondet; .rdata data 3/8 @3,.text data 1985/1985 @1336,.text relocs 6/6 | T147+T148 |
| 39 | `run/drop/qa_drop_nested_blocks.ax` | obj | different-behaviour | a0 nondet; .rdata data 35/40 @21,.text data 4131/4131 @2707,.text relocs 18/18 | T147+T148 |
| 40 | `run/drop/qa_drop_nested_struct.ax` | obj | different-behaviour | a0 nondet; .rdata data 14/16 @7,.text data 1738/1738 @1182,.text relocs 8/8 | T147+T148 |
| 41 | `run/drop/qa_drop_order.ax` | obj | different-behaviour | a0 nondet; .rdata data 6/16 @3,.text data 2030/2030 @1381,.text relocs 8/8 | T147+T148 |
| 42 | `run/drop/qa_explicit_field.ax` | obj | same-behaviour | a0 nondet; .rdata data 15/16 @15,.text relocs 4/4 | T147 |
| 43 | `run/drop/qa_explicit_multiple.ax` | obj | same-behaviour | a0 nondet; .rdata data 15/16 @15,.text relocs 4/4 | T147 |
| 44 | `run/drop/qa_explicit_temp.ax` | obj | same-behaviour | a0 nondet; .rdata data 15/16 @15,.text relocs 4/4 | T147 |
| 45 | `run/drop/qa_loop_break.ax` | obj | same-behaviour | a0 nondet; .rdata data 31/36 @3,.text data 2352/2352 @1881,.text relocs 7/7,defsyms 5/5 | T147+T148 |
| 46 | `run/drop/qa_param_drop.ax` | obj | different-behaviour | a0 nondet; .rdata data 37/40 @29,.text data 1020/1020 @932,.text relocs 8/8 | T147+T148 |
| 47 | `run/drop/qa_temp_drop.ax` | obj | different-behaviour | a0 nondet; .rdata data 15/16 @15,.text data 784/784 @634,.text relocs 6/6 | T147+T148 |
| 48 | `run/drop/qa_temp_drop2.ax` | obj | different-behaviour | a0 nondet; .rdata data 15/16 @15,.text data 1248/1248 @917,.text relocs 7/7 | T147+T148 |
| 49 | `run/drop/qa_temp_drop3.ax` | obj | different-behaviour | a0 nondet; .rdata data 15/16 @15,.text data 691/691 @603,.text relocs 5/5 | T147+T148 |
| 50 | `run/drop/qa_temp_drop_chained.ax` | obj | different-behaviour | a0 nondet; .rdata data 25/40 @9,.text data 1520/1520 @1012,.text relocs 10/10 | T147+T148 |
| 51 | `run/drop/qa_temp_drop_early_return.ax` | obj | different-behaviour | a0 nondet; .rdata data 63/76 @9,.text data 1984/1984 @1845,.text relocs 11/11,defsyms 7/7 | T147+T148 |
| 52 | `run/drop/qa_temp_drop_loop.ax` | obj | different-behaviour | a0 nondet; .rdata data 65/76 @9,.text data 1984/1984 @1835,.text relocs 12/12,defsyms 6/6 | T147+T148 |
| 53 | `run/ffi/repr_c_struct.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 54 | `run/ffi/write_file.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 55 | `run/for/test_for_array.ax` | resolved | no-image | axiomc crash 0xC00000FD | T151 |
| 56 | `run/for/test_for_custom_iter.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 57 | `run/for/test_for_range.ax` | mir | different-behaviour | .text data 23393/23393 @4576 | T149 |
| 58 | `run/for/test_range_standalone.ax` | mir | different-behaviour | .text data 8082/8082 @1371 | T149 |
| 59 | `run/generic/qa_basic_fn.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 60 | `run/generic/qa_pair.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 61 | `run/host/fs/clock.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 62 | `run/host/fs/dir.ax` | tokens | no-image | rc a0=0 ac=101; axiomc panic: arithmetic overflow | T155+T150 |
| 63 | `run/host/fs/file_io.ax` | tokens | no-image | rc a0=0 ac=101; axiomc panic: arithmetic overflow | T155+T150 |
| 64 | `run/host/fs/metadata.ax` | tokens | no-image | rc a0=0 ac=101; axiomc panic: arithmetic overflow | T155+T150 |
| 65 | `run/host/heap/alloc.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_VERIFY_TYPE_MISMATCH | T150 |
| 66 | `run/host/io/args.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 67 | `run/host/io/env.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 68 | `run/host/io/invalid_handle.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 69 | `run/host/io/write_stdout_stderr.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 70 | `run/method/builtins.ax` | obj | same-behaviour | a0 nondet; .rdata data 4/16 @2,.text relocs 8/8 | T147 |
| 71 | `run/method/inherent_methods.ax` | mir | same-behaviour | a0 nondet; .rdata data 122/152 @114,.text data 5365/5173 @658,.text relocs 31/31,defsyms 11/11 | T147+T149 |
| 72 | `run/method/qa_run.ax` | obj | same-behaviour | a0 nondet; .rdata data 2/8 @2,.text relocs 4/4 | T147 |
| 73 | `run/mono/qa_dedup_mangling.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 74 | `run/mono/qa_drop_count_generic.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 75 | `run/mono/qa_generic_enum_drop.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 76 | `run/mono/qa_test_basic.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 77 | `run/mono/qa_test_result_drop.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 78 | `run/native_const/qa_table_str_empty_and_multitables.ax` | obj | same-behaviour | .rdata data 472/472 @8 | T154 |
| 79 | `run/native_enum/01-simple.ax` | thir | same-behaviour | objeq=True | T156 |
| 80 | `run/native_own/str_moves.ax` | obj | same-behaviour | a0 nondet; .rdata data 4/16 @2,.text relocs 2/2 | T147 |
| 81 | `run/native_p7/qa_closure_capture.ax` | mir | no-image | .text data 1126/1126 @684,.text relocs 1/1,defsyms 4/4 | T152 |
| 82 | `run/native_ptr/overlap_copy.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 83 | `run/native_ptr/qa_mem_edge.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 84 | `run/native_ptr/write_bytes_1mb.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 85 | `run/native_str/hello.ax` | obj | same-behaviour | a0 nondet; .text relocs 2/2 | T147 |
| 86 | `run/native_str/qa_hello_edge.ax` | obj | same-behaviour | a0 nondet; .rdata data 10/16 @10,.text relocs 2/2 | T147 |
| 87 | `run/native_str/qa_hello_empty.ax` | obj | same-behaviour | a0 nondet; .rdata data 2/16 @2,.text relocs 5/5 | T147 |
| 88 | `run/native_str/qa_hello_tabs.ax` | obj | same-behaviour | a0 nondet; .rdata data 13/16 @13,.text relocs 2/2 | T147 |
| 89 | `run/native_str/qa_hello_very_long.ax` | obj | same-behaviour | a0 nondet; .rdata data 107/112 @107,.text relocs 2/2 | T147 |
| 90 | `run/native_str/qa_multiple_prints.ax` | obj | same-behaviour | a0 nondet; .rdata data 23/24 @23,.text relocs 6/6 | T147 |
| 91 | `run/native_str/qa_null_byte.ax` | obj | same-behaviour | a0 nondet; .rdata data 13/16 @13,.text relocs 2/2 | T147 |
| 92 | `run/native_str/qa_unicode_mix.ax` | obj | same-behaviour | a0 nondet; .rdata data 60/64 @60,.text relocs 2/2 | T147 |
| 93 | `run/numeric/boundary.ax` | tokens | no-image | rc a0=0 ac=101; axiomc panic: arithmetic overflow | T155 |
| 94 | `run/numeric/cast_char.ax` | mir | same-behaviour | .rdata data 110/56 @7,.text data 3956/3332 @98,.text relocs 15/11,defsyms 8/6 | T149 |
| 95 | `run/numeric/intrinsic_ops.ax` | tokens | no-image | rc a0=0 ac=101; axiomc panic: arithmetic overflow | T155+T150 |
| 96 | `run/numeric/panic_char_110000.ax` | mir | different-behaviour | .rdata data 54/1 @0,.text data 1123/406 @98,.text relocs 4/0,defsyms 5/3 | T149 |
| 97 | `run/numeric/panic_char_d800.ax` | mir | different-behaviour | .rdata data 54/1 @0,.text data 1123/406 @98,.text relocs 4/0,defsyms 5/3 | T149 |
| 98 | `run/numeric/qa_boundary_missing.ax` | tokens | no-image | rc a0=0 ac=101; axiomc panic: arithmetic overflow | T155 |
| 99 | `run/numeric/qa_cast_char_edges.ax` | mir | same-behaviour | .rdata data 162/1 @0,.text data 3172/1284 @98,.text relocs 15/3,defsyms 10/4 | T149 |
| 100 | `run/numeric/qa_overflow_u64.ax` | tokens | no-image | rc a0=0 ac=101; axiomc panic: arithmetic overflow | T155 |
| 101 | `run/numeric/qa_overflow_usize.ax` | tokens | no-image | rc a0=0 ac=101; axiomc panic: arithmetic overflow | T155 |
| 102 | `run/numeric/qa_panic_char_dfff.ax` | mir | different-behaviour | .rdata data 54/1 @0,.text data 883/244 @96,.text relocs 4/0,defsyms 5/3 | T149 |
| 103 | `run/own/reinit.ax` | obj | same-behaviour | a0 nondet; .rdata data 4/16 @2,.text relocs 2/2 | T147 |
| 104 | `run/pattern/qa_destructure.ax` | mir | same-behaviour | .text data 2545/2545 @423 | T154 |
| 105 | `run/ptr/arena_align.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 106 | `run/ptr/drop_in_place.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 107 | `run/ptr/field_write.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 108 | `run/ptr/layout_intrinsics.ax` | thir | different-behaviour | .text data 3429/3657 @183,.text relocs 0/11,defsyms 4/7 | T150 |
| 109 | `run/ptr/linked_list.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 110 | `run/ptr/mem_intrinsics.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 111 | `run/ptr/oracle_dangling.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 112 | `run/ptr/oracle_misaligned.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 113 | `run/ptr/oracle_null.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 114 | `run/ptr/oracle_oob.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 115 | `run/ptr/sum_walk.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T150 |
| 116 | `run/result/qa_test_try_chained.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 117 | `run/result/test_let_option.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 118 | `run/result/test_option.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 119 | `run/result/test_try_option.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_OPERATOR | T151 |
| 120 | `run/result/test_try_result.ax` | thir | no-image | rc a0=0 ac=1; axiomc AX_TYPE_MISMATCH | T151 |
| 121 | `run/slice/coerce.ax` | resolved | same-behaviour | .rdata data 28/1 @0,.text data 1909/1492 @98,.text relocs 2/0,defsyms 4/3 | T149 |
| 122 | `run/slice/disjoint_split.ax` | resolved | no-image | axiomc crash 0xC00000FD | T151 |
| 123 | `run/slice/qa_slice_bounds_panic.ax` | resolved | no-image | axiomc crash 0xC00000FD | T151 |
| 124 | `run/slice/qa_slice_chained_panic.ax` | thir | no-image | axiomc crash 0xC00000FD | T151 |
| 125 | `run/slice/qa_slice_inverted_panic.ax` | resolved | no-image | axiomc crash 0xC00000FD | T151 |
| 126 | `run/slice/qa_slice_len_empty.ax` | thir | no-image | axiomc crash 0xC00000FD | T151 |
| 127 | `run/slice/qa_slice_mutate.ax` | resolved | same-behaviour | .rdata data 196/168 @119,.text data 6108/5766 @4002,.text relocs 15/13,defsyms 11/10 | T149 |
| 128 | `run/slice/qa_slice_mutate_2.ax` | resolved | same-behaviour | .rdata data 84/28 @28,.text data 3025/2191 @98,.text relocs 6/2,defsyms 6/4 | T149 |
| 129 | `run/slice/qa_slice_open_ranges.ax` | resolved | no-image | axiomc crash 0xC00000FD | T151 |
| 130 | `run/slice/sub_range.ax` | resolved | no-image | axiomc crash 0xC00000FD | T151 |
| 131 | `run/slice/sum.ax` | resolved | same-behaviour | .rdata data 84/56 @7,.text data 3631/3292 @1314,.text relocs 7/5,defsyms 7/6 | T149 |
| 132 | `run/str/hello.ax` | obj | same-behaviour | a0 nondet; .text relocs 2/2 | T147 |
| 133 | `run/str/qa_hello_edge.ax` | obj | same-behaviour | a0 nondet; .rdata data 10/16 @10,.text relocs 2/2 | T147 |
| 134 | `run/str/qa_hello_empty.ax` | obj | same-behaviour | a0 nondet; .rdata data 2/16 @2,.text relocs 5/5 | T147 |
| 135 | `run/str/qa_hello_tabs.ax` | obj | same-behaviour | a0 nondet; .rdata data 13/16 @13,.text relocs 2/2 | T147 |
| 136 | `run/str/qa_hello_very_long.ax` | obj | same-behaviour | a0 nondet; .rdata data 107/112 @107,.text relocs 2/2 | T147 |
| 137 | `run/str/qa_multiple_prints.ax` | obj | same-behaviour | a0 nondet; .rdata data 23/24 @23,.text relocs 6/6 | T147 |
| 138 | `run/str/qa_unicode_mix.ax` | obj | same-behaviour | a0 nondet; .rdata data 60/64 @60,.text relocs 2/2 | T147 |
| 139 | `run/struct/simple.ax` | backend-build | same-behaviour | objeq=True | T154 |
| 140 | `run/trait2/test_assoc_items.ax` | resolved | no-image | rc a0=0 ac=1; axiomc AX_NAME_UNRESOLVED | T153 |
| 141 | `run/trait2/test_default_method.ax` | mir | no-image | .text data 854/758 @18,.text relocs 1/1,defsyms 4/3 | T153 |
| 142 | `run/trait2/test_default_override.ax` | mir | different-behaviour | .text data 1531/1435 @44,.text relocs 2/2,defsyms 5/4 | T153 |
| 143 | `run/trait2/test_derive.ax` | mir | no-image | .text data 24895/25247 @107,.text relocs 54/54,defsyms 34/34 | T153 |
| 144 | `run/trait2/test_ops.ax` | thir | no-image | axiomc crash 0xC00000FD | T151 |

## New tasks
- T147 AX0-FIX-05 deterministic object-local string/panic data symbols and index-based local-symbol linking (axiom0 + port) — axiom-backend, sonnet/opus, priority 0, depends T146
- T148 axiomc build path equals axiom0 build.c (destructor-call ABI, inspect reflects build) — axiom-backend, sonnet/opus, depends T147
- T149 Port MIR builder parity (checks, for step, field projection, temporaries) — axiom-semantics, sonnet/opus, depends T146
- T150 Port intrinsic table and raw-pointer typing — axiom-semantics, sonnet/opus, depends T146
- T151 Port typeck parity: generics and the typeck stack overflow — axiom-semantics, opus/opus, depends T146
- T152 Port closures and fn pointers parity — axiom-semantics, sonnet/opus, depends T151
- T153 Port trait items parity in the build path — axiom-semantics, sonnet/opus, depends T151
- T154 Backend parity: narrow extension, -O1 path, const tables — axiom-backend, sonnet/opus, depends T146
- T155 Natively built axiomc lexer panic on 20-digit literals — axiom-frontend, sonnet/opus, depends T146
- T156 Dump and diagnostic parity, oracle compares dumps, registry empty — axiom-frontend, sonnet/opus, depends T147–T155

Amended: T086 (depends + acceptance "registry empty"), T134, T140, T141, T146 (registry maintenance note, ADR-0035 §4).

## Checks
- `taskctl.py lint` on the 10 new and 5 amended task files: OK
- `taskctl.py validate`: OK (235 tasks)
- `harness_check.py`: HARNESS OK (only the standing optional-hook warning)
- `reqcov.py --strict`: COVERAGE OK, gaps 0

## Risks
- T151 (typeck generics + crash) may exceed one sitting; if so the engineer finishes a slice and the architect
  splits by entry group (generics / ranges+crash / Option-Result).
- T150/T151 fixes may expose second-order divergences in programs that so far stopped at `thir`; the rule is to
  update those entries in place and name the cause; T156 BLOCKs (never passes) if any entry remains.
- ADR-0035 §3 Revisit: byte-identical diagnostic texts may be costly; owner may relax to code + severity + span.

## Files changed
- spec/decisions/ADR-0035-axiomc-parity-symbols.md
- spec/ROADMAP.md
- _workspaces/tasks/todo/T147-ax0-fix-05-string-data-symbols-local-symbol-linking.md
- _workspaces/tasks/todo/T148-axiomc-build-path-call-abi-parity.md
- _workspaces/tasks/todo/T149-port-mir-builder-checks-for-step-field-projection.md
- _workspaces/tasks/todo/T150-port-intrinsics-raw-pointer-typing.md
- _workspaces/tasks/todo/T151-port-typeck-generics-and-typeck-crash.md
- _workspaces/tasks/todo/T152-port-closures-fn-pointers-parity.md
- _workspaces/tasks/todo/T153-port-trait-methods-build-path-parity.md
- _workspaces/tasks/todo/T154-backend-parity-narrow-extension-o1-const-tables.md
- _workspaces/tasks/todo/T155-native-axiomc-lexer-panic-20-digit-literals.md
- _workspaces/tasks/todo/T156-dump-diagnostic-parity-registry-empty.md
- _workspaces/tasks/todo/T086-stage-1-axiom0-builds-axiomc-axiomc-passes-the-ful.md
- _workspaces/tasks/todo/T134-ax0-fix-01-native-intrinsics-assert-panic.md
- _workspaces/tasks/todo/T140-ax0-fix-02-unsigned-div-mul-overflow-shift-width.md
- _workspaces/tasks/todo/T141-ax0-fix-03-drop-for-scalar-pointer-field-structs.md
- _workspaces/tasks/todo/T146-ax0-fix-04-statement-terminator-enforced.md
- _workspaces/reports/plan-axiomc-divergence.md
