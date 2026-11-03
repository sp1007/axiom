# T673 Report — E16.6 Canonical WASM32 Stack-Machine Backend, CFG Stackification, Binary `.wasm` & WASI Specification (`SPEC-86`)

## Tóm tắt

Hoàn thành đặc tả chuẩn `spec/SPEC-86-wasm32-backend.md` (34 quy tắc liên tục `AXS-WASM-001`..`034`, LF-only) cùng cập nhật đồng bộ ba tài liệu danh mục nền (`spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`) cho phân hệ `E16.6` (`T673`–`T676`, Phase `P16`), và xử lý triệt để toàn bộ 5 phát hiện QA từ Round 0 (`[F1]`..`[F5]`):
- Chuẩn hóa phân loại `TargetFamily.VirtualMachine` và hai hồ sơ đích cụ thể `TargetId.Wasm32Freestanding` (`wasm32-freestanding`, alias `wasm32-unknown-unknown`, `wasm32-none`, `wasm32 --profile freestanding`) và `TargetId.Wasm32Wasi` (`wasm32-wasi`, mặc định cho `--target wasm32`, alias `wasm32-unknown-wasi`, `wasm32-wasip1`), `DataLayout` 32-bit little-endian (trang 64 KiB, con trỏ béo 8 byte `{ptr: u32, meta: u32}`), đồ thị tính năng WASM tường minh, mô hình lưu trữ kép (local WASM có kiểu không lấy được địa chỉ vs `LinearMemory` shadow stack 16 byte `$__stack_pointer`), bảo toàn provenance, capability `view`/`mut_view`, `memory.grow`, chứng minh `BCE` (`Certainty.Proven`), thứ tự bộ nhớ `atomic.*` / `Send` / `Share`, căn chỉnh `memarg.align` (`@repr(packed)` `align = 0`) và phân vùng `.rodata`/`.data`/`.bss`/TLS theo hồ sơ (`AXS-WASM-001`..`010`).
- Chuẩn hóa thuật toán tái cấu trúc CFG tùy ý sau tối ưu hóa `OptIR`/`Axiom LIR` (`block`/`loop`/`if-else`/`br`/`br_if`/`br_table`), hợp thức hóa tất định chu trình đa điểm vào bất khả quy qua `$irr_state: i32` + một `loop` duy nhất `O(|S| + |E|)`, đẩy cây biểu thức SSA dùng một lần lên ngăn xếp toán hạng ảo theo rào cản tác dụng phụ, và gộp màu tất định local WASM theo kiểu (`i32`, `i64`, `f32`, `f64`, `v128`) (`AXS-WASM-011`..`018`).
- Chuẩn hóa quy ước gọi `CallConv.Wasm` (WebAssembly Basic C ABI: truyền vô hướng trực tiếp, tách tham số `i128`/`u128` thành `(lo: i64, hi: i64)`, trả về `i128`/`u128` và kiểu hợp thành đa trường qua `sret: i32` ở tham số `0`, biến tham `va_list: i32`), bảng hàm gián tiếp `__indirect_function_table` (khe `0 = null`), vtable `dyn Trait` 32-bit, `@wasm_import`/`@wasm_export`, và hạ bậc `panic` theo hồ sơ (`wasm32-freestanding` vs `wasm32-wasi` `fd_write(2)` + `proc_exit(101)`) (`AXS-WASM-019`..`024`).
- Chuẩn hóa bộ mã hóa nhị phân `.wasm` (`\0asm` v1, thứ tự section chuẩn W3C `1..9, 12 DataCount, 10 Code, 11 Data`), bộ kiểm định nội bộ bắt buộc trước khi ghi file `verify_wasm` (ngăn xếp kiểu đa hình), định dạng đối tượng khả định vị (`linking` v2 đứng trước `reloc.CODE`/`reloc.DATA` với header `(target_section_index: uleb32, reloc_count: uleb32)` và `addend: sleb32` cho `{3, 4, 5, 8, 9}` + kho lưu trữ GNU `ar` `.a` tất định), trình liên kết tĩnh `.wasm` thu gom rác theo gốc xuất, và tầng hệ thống `std.sys.wasi` (`wasi_snapshot_preview1`, `filestat.size` ở offset `+32` và ánh xạ `filetype` `4 -> 1`, `3 -> 2`, `_ -> 3`) thuần capability thư mục mở sẵn (`fd_prestat_get`, không có đường dẫn gốc ngầm định) cùng bộ cấp phát `memory.grow` 64 KiB thuần Axiom (`AXS-WASM-025`..`029`).

## Round 1 Fixes (`T673-qa.md` `[F1]`..`[F5]`)

1. **`[F1 — BLOCKER]` Fixed `wasi_snapshot_preview1` `__wasi_filestat_t` field offsets & `host.metadata` `filetype` mapping (`AXS-WASM-029`, `spec/invariants.md` `INV-WASM-002`)**:
   - Corrected `__wasi_filestat_t` (`64` bytes, `align = 8`) layout explicitly: `+0 dev: u64`, `+8 ino: u64`, `+16 filetype: u8` (`+17..+23` padding), `+24 nlink: u64`, **`+32 size: u64`**, `+40 atim: u64`, `+48 mtim: u64`, `+56 ctim: u64`.
   - Updated `host.file_size` to read `st.size` at **`+32`** (instead of `+40`), and specified `host.metadata(path, path_len, out)` (`path_filestat_get(dirfd, LOOKUPFLAGS_SYMLINK_FOLLOW = 1, ...)`) mapping `__wasi_filetype_t` (`u8` at `+16`) as `REGULAR_FILE (4)` $\to$ `out[0] = 1u64`, `DIRECTORY (3)` $\to$ `out[0] = 2u64`, all other `filetype` values $\to$ `out[0] = 3u64` (`SPEC-04` `AXS-EXT-110`), and writing `out[1] = st.size` (`u64` at **`+32`**).
2. **`[F2 — BLOCKER]` Fixed `.wasm` `reloc.*` binary header/ordering, `addend: sleb32` on `{3, 4, 5, 8, 9}`, canonical uppercase `reloc.CODE`/`reloc.DATA`, and W3C section ordering (`AXS-WASM-026`, `AXS-WASM-027`, `spec/invariants.md`, `spec/INDEX.md`)**:
   - Specified in `AXS-WASM-027` that every `reloc.<NAME>` custom section (`reloc.CODE`, `reloc.DATA`, `reloc.<debug_sec>`) MUST appear **after** the `linking` custom section and begins with binary header `(target_section_index: uleb32, reloc_count: uleb32)` prior to the `reloc_count` relocation entries.
   - Partitioned `R_WASM_*` entries explicitly into no-`addend` types `{0, 1, 2, 6, 7}` and mandatory trailing `addend: sleb32` types `{3, 4, 5, 8, 9}` (explicitly marking `+ addend: sleb32` on `R_WASM_FUNCTION_OFFSET_I32 = 8` and `R_WASM_SECTION_OFFSET_I32 = 9` alongside `3, 4, 5`).
   - Standardized uppercase `reloc.CODE` and `reloc.DATA` across `SPEC-86`, `spec/invariants.md`, and `spec/INDEX.md`, and replaced `"ascending section ordering"` in `AXS-WASM-026` with canonical W3C binary section order `1..9, 12 (DataCount), 10 (Code), 11 (Data)` (`DataCount = 12` before `Code = 10`, `reloc.*` after `linking`).
3. **`[F3 — MAJOR]` Made `AXS-WASM-001`..`034` strictly contiguous (`34` rules, `0` gaps) and aligned `REQ-TGT-264..265, 274..284` (`AWASM-75..76, 85..95`) to exact `CATALOG.md` / `0523 §155` semantics (`SPEC-86`, `spec/invariants.md`)**:
   - Populated `AXS-WASM-009` (`WASM memarg Alignment Hints vs Axiom Alignment & @repr(packed) Unaligned Access`, `0523 §68–69`) and `AXS-WASM-010` (`Static Segment Materialization (.rodata / .data / .bss) & Platform-Layered @thread_local TLS Lowering`, `0523 §83–85`) in §1 so `AXS-WASM-001`..`034` is 100% contiguous (`1..34`) and synchronized all rule ranges in `SPEC-86` and `spec/invariants.md`.
   - Aligned `AXS-WASM-022`, `AXS-WASM-030`, `AXS-WASM-034`, and `INV-WASM-003` (`spec/invariants.md`) to the exact `CATALOG.md` / `0523 §155` definitions of `AWASM-75` (`--interp` semantic equivalence), `AWASM-76` (target-opt invariance), `AWASM-85` (`TargetBackend` conformance), `AWASM-86` (native-vs-WASM agreement), `AWASM-87` (physical representation vs semantic equivalence), `AWASM-88` (no WASM-specific Core v1 syntax), `AWASM-89..93` (ownership, trait, `async`, numeric, and FFI safety non-contamination), `AWASM-94` (frontend-independent backend replaceability), and `AWASM-95` (`Axiom LIR` portability validation), citing `SPEC-81 AXS-TGTD-043` / `0524 §112 ABACKEND-89..92` for target-independent test authority vs WAT structural inspection and `AWASM-60..64` for validator/feature/determinism checks.
4. **`[F4 — MAJOR]` Fixed canonical Axiom examples (`AXS-WASM-032`, `AXS-WASM-033`) and `AXS-WASM-034` board task `paths:`/`locks:`**:
   - Replaced recursive `unreachable()` inside `@panic_handler fn freestanding_abort() -> never` (`AXS-WASM-032` Example 2) with `loop {}` (`SPEC-52` `AXS-FRE-011`).
   - Replaced `use std.collections.Vec` and `xs.get_view(0usize)` (`AXS-WASM-033` Example 1) with `use std.alloc.vec.Vec` and `let elem: view<i32> = view(xs[0usize])` (`std/alloc/vec.ax`, `SPEC-03` `AXS-SEM-047`, `SPEC-11`).
   - Updated `AXS-WASM-034` task rows for `T673`–`T676` to match the board YAML `paths:`/`locks:` verbatim, removing all fabricated `locks:` on `T674` and `T675`.
5. **`[F5 — MINOR]` Fixed `SPEC-40 AXS-INT-021` reference and `tasks/0523 §` / `tasks/0784 §562.*` corpus section citations (`SPEC-86`, `spec/invariants.md`)**:
   - Changed `SPEC-40 AXS-INT-011` $\to$ `SPEC-40 AXS-INT-021` (and `SPEC-03 AXS-SEM-032`) in `AXS-WASM-017`.
   - Audited and corrected every `tasks/0523 §` and `tasks/0784 §562.*` section citation across `SPEC-86` (`Consolidates`, `Tóm tắt`, `AXS-WASM-001`..`030`, `Sources`) and `spec/invariants.md` (`INV-WASM-001`..`003`) to match actual headings in `0523` (`§1–156`) and `0784` (`§562.5, §562.29–34, §562.77–99, §562.141–145, §562.153, §562.165, §562.174–186, §562.191–193, §562.200`, zero `§562.100–101`).

## Verification

- `python -X utf8 .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `requirements: 32308 ... gaps: 0, COVERAGE OK` (exit `0`).
- `python -X utf8 .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit `0`).
- `python -X utf8 .claude/skills/axiom-tasks/scripts/taskctl.py validate`: `OK (598 tasks)` (exit `0`).
- `python -X utf8 .claude/skills/axiom-tasks/scripts/taskctl.py changes T673`: exit `0` (`0 REFUSED`, exact 4 owned/locked spec files + report).
- Custom audit: `0` `\r` bytes across all modified files and report; `AXS-WASM-001`..`034` strictly contiguous (`34` rules, `0` gaps, `0` duplicates across `1,507` global `AXS-*` rules); `0` broken `AXS-*` references; `30/30` `AX_*` codes in `SPEC-86` registered in `spec/diagnostics.md` and `AXS-WASM-031`; `5/5` Axiom code blocks strictly follow `=` and `.` canonical syntax; `0` stale Round 0 strings.

## Files changed

- spec/SPEC-86-wasm32-backend.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Status

STATUS: COMPLETE round=1
