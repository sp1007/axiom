# ADR-0011 — Diagnostic code taxonomy, severities, ordering and invariant ids

## Tóm tắt
Tài liệu gốc mâu thuẫn về mã chẩn đoán. Về dạng mã: `ETYPE_MISMATCH` (tasks/0360), `AX_TYPE_0001`
(0146), `AX_NAME_0001` (0172), `AX1401` (tasks/0262). Về danh sách vùng: 27 vùng (0146) so với 18
vùng (tasks/0360). Về mức độ: Error/Warning/Info/Hint so với Error/Warning/Note/Help. ADR-0001 và
SPEC-02 còn dùng `AX_ADDR_…`, trong khi ADDR không thuộc danh sách vùng cố định. Quyết định:
1. Mã có dạng `AX_<VÙNG>_<TÊN MÔ TẢ>`, không đánh số.
2. Đúng 18 vùng cố định, mỗi vùng một file đăng ký. Thêm vùng phải sửa spec trước.
3. `AX_ADDR_UNSUPPORTED_STAGE0` đổi thành `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (payload ghi `@at`), và
   `AX_ADDR_HOSTED` đổi thành `AX_UNSAFE_AT_HOSTED`. Mã cho cấu trúc nằm ngoài tập con của axiom0 luôn
   có đuôi `_UNSUPPORTED_IN_BOOTSTRAP`.
4. Schema có bốn mức độ, axiom0 chỉ phát `error`/`warning`; ICE là một vùng riêng (mã thoát 3).
5. Thứ tự in ra theo file → byte bắt đầu → thứ tự đăng ký của mã.
6. Có "rào chắn giai đoạn": giai đoạn nào đã báo lỗi thì các giai đoạn sau không chạy.
7. Cả định dạng người đọc lẫn JSON đều ghi ra stderr.
8. Bất biến dùng mã riêng `INV-*` vì số ADIAG trong tài liệu gốc trùng nhau.
9. T009 đăng ký sẵn toàn bộ mã gieo cho P1–P4.
10. Bất biến có trường `since:` để gatecheck biết khi nào phép kiểm tra phải tồn tại.
Revisit: chỉ điểm 6, xét lại ở E19.4.

Status: **Accepted** (architect, T002). Date: 2026-10-04. Revisit: item 6 only (at E19.4, diagnostics UX 2.0).

## Context

| Topic | Positions in the sources |
|---|---|
| Code shape | tasks/0360 §3 (frozen): `ETYPE_MISMATCH`, `EOWN_USE_AFTER_MOVE`; 0146 §4: `AX_TYPE_0001`; 0172 §10: `AX_NAME_0001`; tasks/0262 §46: `AX1401`; SPEC-01/02 and the board (T001, ADR-0005, tasks): `AX_LEX_COLON_COLON`, `AX_TYPE_MISMATCH` |
| Namespaces | 0146 §54: 27 prefixes plus `AXC_INTERNAL_`; tasks/0360 §38: 18 categories (`ELEX` … `EINTERNAL`); T002 scope and ADR-0005 §2: a fixed list of 18 areas, one registry file each, locked by name |
| `@at` codes | ADR-0001 and SPEC-02 AXS-GRM-037: `AX_ADDR_UNSUPPORTED_STAGE0`, `AX_ADDR_HOSTED`; ADR-0004 §2 / ADR-0010 §9: `static` gets `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`; axiom-c-stage0: `AX_*_UNSUPPORTED_STAGE0` |
| Severities | tasks/0360 §2, 0146 §3: error, warning, info, hint; 0172 §10: Error, Warning, Note, Help |
| Order | tasks/0360 §41: file, position, severity, code, identity; T009 scope: (file, offset, code); SPEC-01 AXS-LEX-101: source order, ties in the order of its code table (not alphabetical) |
| Invariant ids | `ADIAG-20…` exist in 0146 §65, 0153 §37 and tasks/0360 §51 with different meanings |
| Invariant checks | T002/T022: each invariant names a test dir or tool, gatecheck checks it "exists"; many checks only appear in P4–P10 |

## Options

1. Code shape: (a) numeric `AX_TYPE_0001`: stable, but meaningless in tests and agent loops;
   (b) `E<AREA>_<NAME>` of tasks/0360: descriptive, but collides with the `AX_` prefix already used by
   SPEC-01/02, the board and the skills; (c) `AX_<AREA>_<NAME>`: descriptive, prefixed, already used.
   **Chosen: (c).** It keeps tasks/0360's descriptive identity under the project's prefix.
2. Areas: (a) 0146's 27; (b) tasks/0360's 18 categories; (c) the fixed 18 of T002/ADR-0005.
   **Chosen: (c)**, because tasks already lock these file names. The corpus prefixes map onto the areas (diagnostics §3).
   Async, concurrency and GPU areas are added when their epics are planned.
3. `@at` codes: (a) add an `ADDR` area (a 19th area would break the fixed list and need another file);
   (b) put the stage-0 rejection in `UNSAFE`; (c) reuse `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`, as `static`
   already does, with a `construct` payload. **Chosen: (c)** for stage 0: one code covers every
   semantic-level out-of-subset construct, and TYPE.def is the file the relevant tasks lock. The
   post-T087 semantic errors of fixed-address declarations go to `UNSAFE` (`AX_UNSAFE_AT_HOSTED` …).
4. Severities: (a) error/warning/note/help; (b) the four of tasks/0360. **Chosen: (b)** (it is frozen),
   with notes and helps as attachments, and only error/warning emitted by axiom0.
5. Ordering tie-break: alphabetical code order contradicts SPEC-01 AXS-LEX-101. **Chosen:** the
   registry ordinal, with append-only area files.
6. Cascades: (a) run every stage and rely on poisoning alone; (b) a stage barrier plus poisoning.
   **Chosen: (b)**: simplest to implement deterministically in C, and ui tests stay one-root-cause.
   Revisit at E19.4 (an IDE wants more diagnostics per run).
7. Stream: (a) JSON to stdout; (b) everything to stderr. **Chosen: (b)**, because `run` and `inspect` use stdout.
8. Invariant ids: (a) reuse corpus ids; (b) own namespace `INV-<GROUP>-NNN`, citing corpus ids as
   sources. **Chosen: (b)**, because corpus ids are ambiguous.
9. Registering codes: (a) each task adds its codes; (b) T009 registers the whole P1–P4 seed list.
   **Chosen: (b)**, so T018 and T021 need no registry locks; later codes are appended under a lock.
10. Invariants whose check does not exist yet: (a) list only checkable invariants; (b) add a
    `since: <task>` field; gatecheck requires the target to exist only once that task is done.
    **Chosen: (b)**, so the catalogue covers the whole core now (0264 §23-24).

## Decision

§1–§10 above, written out normatively in `spec/diagnostics.md` (AXD-010…AXD-063, seed list §10,
fixed names §11) and `spec/invariants.md` (format §1, rules IG-1…IG-4). Exit codes stay as in T016:
0 ok, 1 errors, 2 usage, 3 ICE.

## Consequences

- **Spellings superseded** (the ADR wins over older text; fix the text at the next edit of each file):
  SPEC-02 AXS-GRM-037 and ADR-0001 (`AX_ADDR_UNSUPPORTED_STAGE0` → `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`,
  `AX_ADDR_HOSTED` → `AX_UNSAFE_AT_HOSTED`); `.claude/skills/axiom-syntax/SKILL.md` (same);
  `.claude/skills/axiom-c-stage0/SKILL.md` (`AX_*_UNSUPPORTED_STAGE0` → `AX_*_UNSUPPORTED_IN_BOOTSTRAP`).
- **T003 codes**: T003 asked for `AX_INTERP_*`. INTERP is not an area, so the names become
  `AX_DRIVER_INTERP_STEP_LIMIT`, `AX_DRIVER_INTERP_STACK_LIMIT` and `AX_UNSAFE_INTERP_UB`. Its TYPE and
  CONST names are accepted as they are.
- **T006** (archcheck) must also implement INV-LAYER-005 (the back end never includes front-end layers)
  and INV-LAYER-008 (no C sources under `std/`), besides the rules already in its scope.
- **T009** implements the ordering key AXD-060 (registry ordinal, not alphabetical), registers the
  whole seed list, and adds a golden list of registered codes (INV-DIAG-002).
- **T022** (gatecheck) implements rules IG-1…IG-4, including `since:`.
- **T016** writes diagnostics to stderr in both formats (AXD-061).
- No test exists yet that uses the old spellings.

## Sources
tasks/0360 §1-§51; 0146 §3-§5, §19-§21, §50-§58, §65; 0153 §37; 0171 §40; 0172 §10-§12; tasks/0262
§46; SPEC-01 AXS-LEX-100/101; SPEC-02 AXS-GRM-037, AXS-GRM-101; ADR-0001; ADR-0004 §2; ADR-0005 §2;
ADR-0010 §9; 0264 §23-24; T002, T009, T016, T022 task texts.
