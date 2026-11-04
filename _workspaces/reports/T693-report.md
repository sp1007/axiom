STATUS: COMPLETE round=1

# T693 Report — E16.12 Windows ARM64 (`aarch64-pc-windows-msvc`) PE/COFF & ABI Specification (`SPEC-91`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-91-windows-arm64.md` (`AXS-WA64-001`..`AXS-WA64-036`, 36 quy tắc đánh số liên tục không trùng lặp toàn cục) và đăng ký đồng bộ vào `spec/INDEX.md`, `spec/diagnostics.md` (`AX_LINK_BAD_UNWIND_INFO` cùng bảng ánh xạ `E9100`–`E9119`), và `spec/invariants.md` (`INV-WARM-001`..`INV-WARM-005`, mục §45). Trong Round 1, toàn bộ 5 phát hiện QA (`Findings 1..5` trong `_workspaces/reports/T693-qa.md`) đã được khắc phục triệt để: chuẩn hóa ba phân đoạn nhúng `.axmeta`/`.axmir`/`.axlto` trên COFF với cờ `IMAGE_SCN_LNK_INFO | IMAGE_SCN_MEM_DISCARDABLE | IMAGE_SCN_MEM_READ` (`0x42000200`) và quy tắc tước bỏ khỏi ảnh cuối theo `SPEC-24 AXS-ART-021..022` & `SPEC-89 AXS-ARTM-028..029`; khôi phục tính nhất quán `--kind bin` (đồng nghĩa với `--kind exe` trên mọi đích theo `SPEC-89 AXS-ARTM-002..003`) và đồng bộ `AX_LINK_ABI_MISMATCH` giữa `SPEC-91` và `spec/diagnostics.md`; hiệu chỉnh toàn bộ tham chiếu quy tắc `SPEC-26` (`AXS-WLIB-021`, `023`, `030..032`); tách bạch kiểm chứng tiền mã hóa `verify_mc` (`REQ-TGT-162`) với kiểm chứng hậu mã hóa `verify_coff_obj` / `verify_coff_pe` + xuất nguyên tử (`REQ-TGT-307`, `SPEC-89 AXS-ARTM-030`) cũng như tương đương hành vi `REQ-TGT-157` so với bộ kiểm thử tuân thủ chung `REQ-TGT-197` (`tasks/0522 §159`), bổ sung đầy đủ `0097 §27` (`REQ-TOOL-001`) và `0107 §64` (`REQ-FFI-004`); và chuẩn hóa các mốc tham chiếu gốc `0187 §8–25, §40, AIMPORT-20..34`, `tasks/0563 §304.14–20, §304.33–45`, và `tasks/0453 §194.2–10, §194.18`.

## Round 1 QA Fixes (`_workspaces/reports/T693-qa.md` Findings 1–5)
1. **Finding 1 — Embedded `.axmeta`/`.axmir`/`.axlto` COFF flags & `SPEC-24` / `SPEC-89` citations (`SPEC-91:115, 117, 259`)**:
   - Updated the `AXS-WA64-012` section table and prose to include all three embedded containers (`.axmeta`, `.axmir`, `.axlto`) with exact COFF `Characteristics = IMAGE_SCN_LNK_INFO (0x00000200) | IMAGE_SCN_MEM_DISCARDABLE (0x02000000) | IMAGE_SCN_MEM_READ (0x40000000)` (`0x42000200`, `VirtualSize = 0`, no `ALIGN_*` bits) per `SPEC-24 AXS-ART-021` and `SPEC-89 AXS-ARTM-028`.
   - Replaced erroneous `SPEC-24 AXS-ART-024` / `SPEC-89 AXS-ARTM-030` stripping citations with `SPEC-24 AXS-ART-021..022` and `SPEC-89 AXS-ARTM-028..029` across `AXS-WA64-011`, `AXS-WA64-012`, `AXS-WA64-025`, and `spec/invariants.md` (`INV-WARM-003`, `INV-WARM-004`).
2. **Finding 2 — `--kind bin` synonym consistency & `SPEC-91` <-> `spec/diagnostics.md` symmetry (`diagnostics.md:168, 678, 689`; `SPEC-91:24, 249, 347`)**:
   - Removed the erroneous `` `bin` on hosted `aarch64-windows` `` clause, `/T695` task tag, and `SPEC-91` citation from `AX_DRIVER_INVALID_ARTIFACT_KIND` (`spec/diagnostics.md:678`), and explicitly noted `--kind exe` / synonym `--kind bin` -> `<stem>.exe` per `SPEC-89 AXS-ARTM-002..003` in `AXS-WA64-001` and `AXS-WA64-025`.
   - Synchronized `AX_LINK_ABI_MISMATCH` across `SPEC-91 AXS-WA64-025`, `AXS-WA64-033` (`E9116`), `spec/diagnostics.md:168` (`AXD-021`), and `spec/diagnostics.md:689`, and verified 100% bidirectional rule-level diagnostic coverage across all `24` `AX_*` codes cited for `SPEC-91`.
3. **Finding 3 — Exact `SPEC-26` `AXS-WLIB-*` rule IDs (`SPEC-91:159, 262, 271, 284, 290`; `invariants.md:1477, 1484`)**:
   - Updated `AXS-WA64-016` and `INV-WARM-003` from `AXS-WLIB-020..021` to `AXS-WLIB-030..031` (`IMPORT_OBJECT_HEADER` short-import `.lib` generation & consumption).
   - Updated `AXS-WA64-026` from `AXS-WLIB-020..023` to `AXS-WLIB-030..032` and `INV-WARM-004` to `AXS-WLIB-001..005, AXS-WLIB-020..023, AXS-WLIB-030..032`.
   - Updated `AXS-WA64-028` prose from `AXS-WLIB-004, 022` to `AXS-WLIB-004, 021` (`.edata` Export Directory) and added `AXS-WLIB-030` to its bracketed citation; updated `AXS-WA64-029` to cite `SPEC-26 AXS-WLIB-005, 023` (`.reloc` Base Relocation Table); and updated `INV-WARM-002` `SPEC-83` frame/probe citation to `AXS-A64-019..021`.
4. **Finding 4 — `REQ-TGT-307` vs `REQ-TGT-162`, `REQ-TGT-197` vs `REQ-TGT-157`, and `0097 §27` / `0107 §64` / `tasks/0522 §159` traceability (`SPEC-91:5-6, 93, 157, 161-163, 238-240, 249, 259, 436-447`; `INDEX.md:97`; `invariants.md:1469-1499`)**:
   - Specified both pre-encoding `verify_mc` (`REQ-TGT-162`, `tasks/0521 §156 AARM-68`) and post-encoding `verify_coff_obj` / `verify_archive` / `verify_coff_pe` structural verification + `<out>.tmp.<pid>` atomic publication (`REQ-TGT-307`, `SPEC-89 AXS-ARTM-030`, `tasks/0524 §112 ABACKEND-82`) in `AXS-WA64-017`, `AXS-WA64-025`, `INV-WARM-003`, and `INV-WARM-004`.
   - Fixed inline attribution in `INV-WARM-005` (`spec/invariants.md:1490`) and `AXS-WA64-035` so common target conformance suite passage cites `REQ-TGT-197` (`tasks/0522 §159 ABACKEND-51`) while cross-OS/cross-ISA observable behavioral equivalence cites `REQ-TGT-157` (`tasks/0521 §156 AARM-63`).
   - Added `0097 §27` (`REQ-TOOL-001`), `0107 §64` (`REQ-FFI-004`), `tasks/0522 §159`, `SPEC-44`, and `SPEC-75` consistently across `SPEC-91:5-6`, `spec/INDEX.md:97`, and `spec/invariants.md` §45 + `## Sources`.
5. **Finding 5 — Corpus anchors `AIMPORT-20..34`, `tasks/0563 §304.14–20`, and `tasks/0453 §194.2–10, §194.18` (`SPEC-91:249, 259, 262, 271`; `invariants.md:1463, 1484, 1491`)**:
   - Replaced non-existent `APE-40..55` with `0187 §8–25, §40, AIMPORT-20..34` in `AXS-WA64-026` and `invariants.md`.
   - Replaced `tasks/0563 §304.10–20` with `tasks/0563 §304.14–20, §304.33–45` (`AIMG-20..60`) across `SPEC-91` and `spec/invariants.md`.
   - Updated `INV-WARM-001` `source:` from `tasks/0453 §194.8, §194.29` to `tasks/0453 §194.2-10, §194.18` (and `INV-WARM-004`/`005` to `§194.20-28` / `§194.2-28, §194.42-44`).

## Architectural Decisions & Empirical Verification
1. **Collision-Free Rule, Diagnostic & Invariant Namespaces (`AXS-WA64-001`..`036`, `INV-WARM-001`..`005`, `AX_LINK_BAD_UNWIND_INFO`)**:
   - Registers `AXS-WA64-001`..`AXS-WA64-036` with zero gaps and zero collisions across `spec/*.md`.
   - Maps task-card shorthand `INV-WIN-ARM64-01..05` 1-to-1 onto canonical `INV-WARM-001`..`INV-WARM-005` in `spec/invariants.md` §45 (`WARM` group) satisfying `IG-1`..`IG-4`, anchored to `since: T694` (`INV-WARM-001`..`003`), `since: T695` (`INV-WARM-004`), and `since: T696` (`INV-WARM-005`).
   - Maps task-card shorthand `E9100–E9119` (`AXS-WA64-033`) per `ADR-0011` / `AXD-010` onto `DRIVER`, `TARGET`, `FFI`, `VERIFY`, `LINK`, and `ICE`, adding `AX_LINK_BAD_UNWIND_INFO` (`23 <= 48` chars) in `spec/diagnostics.md` §11 while reusing `23` existing canonical codes.
2. **Empirically Probed `aarch64-pc-windows-msvc` ABI & Unwind Contracts (LLVM 22 `clang`/`clang++` + `winnt.h`)**:
   - **Variadics (`AXS-WA64-006`)**: `V0..V7` and `HFA`/`HVA` are disabled across the entire variadic call (both fixed and `...` arguments use `X0..X7` + 8-byte stack slots, `> 16`B `HFA`s pass by 8-byte caller-copy pointer, and `VaList = *mut u8`).
   - **C POD vs C++ Return Lowering (`AXS-WA64-005`)**: C / `@repr(C)` POD `> 16`B returns via `X8`, whereas MSVC C++ non-POD free/static functions pass `sret` in `X0` (returning `X0`) and C++ instance methods returning any user-defined struct/class pass `this` in `X0` and `sret` in `X1` (returning `X0`).
   - **`__chkstk` Exact Instruction & Clobber Contract (`AXS-WA64-009`, `AXS-WA64-031`)**: `X15 = alloc_bytes >> 4`, `BL __chkstk` (after saving `X30`; clobbers only `X16, X17, X30, NZCV`, preserves `SP` and `X15`, reads `[X18, #0x10]` = `0xF9400A51`), followed immediately by `SUB SP, SP, X15, LSL #4` = `0xCB2F73FF`.
   - **Packed `.pdata` & `.xdata` Bitfields (`AXS-WA64-019`..`021`)**: Packed `RegF[15:13]` encodes `0` (`0` FP regs) or `RegF + 1` (`2..=8` FP regs `D8..D[8+RegF]`), requiring `.xdata` (`Flag = 0`) when saving `D8` alone; `save_r19r20_x` uses `z = off/8` vs `save_fplr_x` `z = off/8 - 1`, and `save_reg_x` / `save_freg_x` use 5-bit `z` (`8..256`B).

## Verification Summary
- Programmatic Round 1 audit (`verify_t693_r1.py`): `0` CRLF (`\r`) bytes, valid UTF-8, contiguous `AXS-WA64-001`..`AXS-WA64-036` (`0` gaps, `0` duplicates), `100%` verified external `AXS-*` rules/ranges and semantic titles, `100%` verified `REQ-*` IDs in `CATALOG.md`, `100%` verified corpus doc IDs/sections/rule anchors in `docs/base/`, `100%` bidirectional `SPEC-91` <-> `spec/diagnostics.md` rule-level diagnostic symmetry (`0` duplicate `AX_*` rows, all `<= 48` chars), `193` invariants passing `IG-1`..`IG-4`, and canonical Axiom syntax (`=`, `.`, `"Xin chào thế giới"`).
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit `0`).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T693`: `0` `REFUSED` paths; exact match with `## Files changed`.

## Files changed
- spec/SPEC-91-windows-arm64.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md
