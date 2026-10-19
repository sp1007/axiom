# ADR-0035 — axiomc/axiom0 parity before Stage-1: data-symbol naming, local-symbol linking, zero-tolerance divergence registry

Status: accepted (2026-10-20, architect; owner-delegated decision)

## Tóm tắt
- T085 cho thấy 144/268 chương trình của corpus mà `axiomc` (compiler viết bằng Axiom, do axiom0
  build) dịch ra **không giống byte** với axiom0; 22 chương trình chạy sai hẳn (ví dụ
  `tests/run/drop/qa_param_drop.ax` in `S drop` ba lần). Kiến trúc sư đã thăm dò từng mục của
  `known_divergent.txt`: nguyên nhân chính là (1) ký hiệu chuỗi `.Lstr.<id>` trùng tên giữa các hàm
  và linker bản port gộp ký hiệu STATIC theo tên; (2) axiom0 đặt tên chuỗi bằng địa chỉ heap nên
  không tất định; ngoài ra còn nhiều lỗi port thật (mất kiểm tra biên slice, mất kiểm tra `as char`,
  bước `for` bằng 0, sai chỉ số trường qua `*self`, intrinsic bị biên dịch thành thân giả, typeck
  thiếu generic/closure, tên ký hiệu phương thức trần, …).
- Quyết định: (1) ký hiệu dữ liệu do compiler sinh (`.Lstr`, `.Lpanic`) là cục bộ trong object, tên
  tất định `.Lstr.<f>.<k>` / `.Lpanic.<n>`, định nghĩa đúng một lần; (2) cả hai linker phân giải
  relocation tới ký hiệu đã định nghĩa trong cùng object theo **chỉ số** ký hiệu, ký hiệu STATIC không
  vào bảng toàn cục; (3) **không có loại khác biệt byte nào được chấp nhận**: "same-behaviour" không
  có nghĩa là vô hại (thăm dò tìm thấy lỗi thật ẩn trong các mục này), timestamp đã bằng 0, nên
  `known_divergent.txt` phải rỗng khi vào T086; (4) quy tắc bảo trì registry (chỉ được xoá, không
  được thêm); (5) axiom0 chỉ có một đường hạ tầng chuẩn là `build`, `inspect` phải phản ánh đúng nó.
- Task mới T147–T156 (T147 là AX0-FIX-05 sửa cả axiom0 lẫn port); T086 phụ thuộc tất cả.

## Context
T085 (`_workspaces/reports/T085-report.md`, QA `_workspaces/reports/T085-qa.md` finding 3) built the
end-to-end oracle `tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py`: for each of 268 corpus
programs it compares `build` and `build --emit=obj` at -O0/-O1 (exit code, diagnostics bytes, output
bytes) and the run result of both images. 144 programs are listed in `known_divergent.txt` with the
first differing `inspect --emit=` stage and a behaviour class (`same-behaviour` 58,
`different-behaviour` 22, `no-image` 64).

Architect probes (2026-10-20, `build-snap-T085/build/axiom0.exe` and the `axiomc.exe` built by the
running T085 gate; table in `_workspaces/reports/plan-axiomc-divergence.md`):
- The stage column is only a diagnosis aid: equality is decided on build outputs, and many first
  differences are dump-only (`(PathSegment @Sym(2) "i32")`, type-id numbering) while the byte
  difference has another cause.
- **String symbols.** `axiomc build` writes `.Lstr.<id>` as `IMAGE_SYM_CLASS_STATIC` where `<id>`
  restarts at 100000 in every function; the relocations reference the right symbol *indexes*, so the
  object is correct, but `compiler/link/linker.ax` registers STATIC symbols in the global name table
  (first definition wins), so every function gets the first function's literal. `axiom0 build`
  (`driver/build_native/build.c:498,559`) names them `.Lstr.<heap address>.<id>` (non-deterministic
  between runs), defines them GLOBAL and adds a second, undefined EXTERNAL symbol of the same name for
  every reference; its linker (`link/pe/linker.c`) resolves every relocation by name and ignores
  STATIC symbols. `inspect --emit=obj` (`driver/emit_obj.c:496`) uses a third convention
  (`.Lstr.<id>`, local, 8-byte padding). `.Lpanic_<n>` uses a process-wide `static int`.
- **Hidden miscompiles in `same-behaviour` entries.** `tests/run/slice/coerce.ax`: the slice index
  bounds check is missing from axiomc's MIR; `tests/run/numeric/cast_char.ax`: the `as char` validity
  check is missing; `tests/run/method/inherent_methods.ax`: `(*self).1` is lowered as `(*self).0`;
  `tests/run/drop/003.ax`: `axiomc build` passes the destructor's `self` in RAX instead of RCX. All
  four programs happen to print the expected output.
- COFF `TimeDateStamp` and PE `TimeDateStamp` are 0 in both compilers; no timestamp or path is
  embedded in the outputs.

## Options
Naming of compiler-generated data symbols:
1. Keep per-function ids and rely on the linker resolving by index. Rejected alone: names stay
   ambiguous in every tool (objdump, `inspect`, a future gcc/ld cross-link of E18.7).
2. One object-wide counter (`.Lstr.<n>`). Viable, but requires threading a counter through the
   isel string table of both compilers.
3. `.Lstr.<f>.<k>` with `f` = ordinal of the function body in the object's emission order and
   `k` = the per-function string index (chosen): deterministic, unique, no change to isel.

Linker resolution:
1. Keep resolving by name and make names unique. Rejected: correctness would depend on a naming
   convention; any colliding local symbol (two objects, or a future `static`) silently mislinks.
2. Resolve a relocation whose target is defined in the same object (SectionNumber > 0) by that
   symbol's index, keep STATIC out of the global table, resolve undefined EXTERNAL by name (chosen;
   this is the COFF/PE semantics, Microsoft PE/COFF spec §5.4.4 storage classes).

Byte differences:
1. Accept a class of "benign" differences (`same-behaviour`, padding, register choice, symbol order)
   and compare normalised outputs. Rejected: the probes found real miscompiles in exactly that class;
   the T087 fixed point (stage2 == stage3) and T086's `--emit=obj` equality criterion need exact
   bytes; there is no inherently variable field (timestamps are 0).
2. Zero tolerance (chosen): every listed program is fixed; an exception needs its own ADR naming the
   program and the reason.

## Decision
1. **Compiler-generated data symbols** (both compilers; `build`, `build --emit=obj` and
   `inspect --emit=obj`): string literal data is emitted into `.rdata` NUL-terminated and padded to 8
   bytes, one symbol per literal, named `.Lstr.<f>.<k>` (decimal; `f` = 0-based ordinal of the
   function body in the object's emission order, `k` = the literal's `sym_id` within that body),
   storage class `IMAGE_SYM_CLASS_STATIC`, defined exactly once (no undefined twin); references are
   relocations against that symbol's own index. Panic-message data uses `.Lpanic.<n>`, `n` = 0-based
   counter per object (reset per compilation, never a process-wide static). Other compiler-generated
   local data (const tables, ADR-0004) follow the same rule with their existing prefix and the
   ordinal suffix if a collision is possible.
2. **Local-symbol linking** (both `bootstrap/axiom0/src/link/pe/linker.c` and
   `compiler/link/linker.ax`): a relocation whose target symbol has SectionNumber > 0 resolves to that
   symbol's section and value through its symbol-table index, whatever its name or storage class;
   only `IMAGE_SYM_CLASS_EXTERNAL` definitions enter the global name table (duplicate EXTERNAL
   definitions stay an error); STATIC symbols never do; an undefined EXTERNAL reference resolves by
   name. Applies equally to the in-memory object-model path (`pe_link_objmodel_to_buf`).
3. **Zero tolerance.** No byte difference between `axiomc` and `axiom0` outputs is accepted:
   `same-behaviour` is not a justification. At the start of T086 `known_divergent.txt` contains no
   entry (the comment header stays). Diagnostics (code, severity, span **and** message text) and every
   `inspect --emit=<stage>` dump must also be identical, because the T086 suite runs the dump and ui
   goldens with `--compiler axiomc1`; REQ-TOOL-105 ("messages are not semantic identifiers") governs
   what tests may pin, not what the port may print differently. A future exception requires a
   separate ADR that names each program and why exact equality is impossible.
4. **Registry maintenance** (every task whose full suite runs `axiomc_e2e.test`, from T134 on):
   the oracle fails on XPASS and IMPROVED, so a task removes, by explicit line deletion in the same
   change, every entry its fix makes identical, and lists the removed paths in its report. An entry
   whose behaviour improves but is still not identical is updated in place (behaviour column); stage
   columns may be refreshed with `--update-registry` only if the resulting diff is limited to those
   columns and quoted in the report. **Adding** an entry is forbidden: a program that stops being
   identical is a regression and is fixed in the task that caused it.
5. **One production lowering path in axiom0.** `build` (`driver/build_native/build.c`) is the
   reference that `axiomc build` must equal. Until the T087 freeze, `inspect --emit=lir|mi|mc|obj`
   must show the same lowering as `build` (same function type passed to LIR lowering, same symbol
   naming); a disagreement between axiom0's own `inspect` and `build` paths is an axiom0 defect,
   fixed in lockstep (ADR-0034 §2) by the task that finds it.
6. **Ownership of fixes.** Each root-cause class gets one fix task owned by the module owner
   (T147–T156, table in `_workspaces/reports/plan-axiomc-divergence.md`). When the probe shows the
   defect also exists in axiom0, the task fixes both (ADR-0034 §2) and is named `AX0-FIX-<nn>`.
   Every fix task adds a regression test under `tests/run/parity/<topic>/` whose expected exit code
   and stdout are derived by hand from the source program (category A, ADR-0034 §1), never captured
   from either compiler; being under `tests/run/**` the test is also in the e2e corpus, so the oracle
   proves axiomc's image behaves the same.

## Consequences
- New tasks: T147 AX0-FIX-05 (data symbols + local-symbol linking, axiom0 + port), T148 (`build`
  path parity: call ABI of destructor calls, `inspect` == `build`), T149 (port MIR builder: bounds and
  `as char` checks, `for` step, field projection through deref, index temporaries), T150 (port
  intrinsics and raw-pointer typing, lockstep with T134's table), T151 (port typeck generics and the
  typeck stack-overflow crash), T152 (closures and fn pointers), T153 (traits and methods in the build
  path: method symbols, default methods, derive, associated types), T154 (backend parity: narrow-value
  extension, -O1 LIR path, const-table `.rdata` layout), T155 (lexer panic on 20-digit literals in the
  natively built axiomc), T156 (dump and diagnostic parity, oracle compares dumps, registry empty).
- Amended: T086 (depends on T147–T156; acceptance "registry empty"), T134/T140/T141/T146 (registry
  maintenance note, §4), T087 (no change; inherits the zero-tolerance rule).
- T085's in-process byte-blob bundles may include string programs once T147 lands (T147 adds one).
- Affected specs: none of SPEC-02/03/12 change; the object rule is recorded here and referenced from
  the tasks. Affected tests: `tests/selfhost/obj_link_driver/known_divergent.txt`, `tests/link`,
  `tests/obj` goldens that contain string symbols, `tests/run/parity/**` (new).

## Sources
`_workspaces/reports/T085-report.md` (findings 1–7), `_workspaces/reports/T085-qa.md` (finding 3),
`tests/selfhost/obj_link_driver/known_divergent.txt`, `_workspaces/reports/plan-axiomc-divergence.md`
(probe table); ADR-0034 §1–§2 (oracle categories, lockstep rule); ADR-0004 (const tables in
`.rdata`); ADR-0005 §3 (gate PASS/BLOCKED); REQ-CORE-3181 (deterministic valid objects),
REQ-BLD-030, REQ-BOOT-085, REQ-TST-089, REQ-TOOL-105; Microsoft PE/COFF specification (symbol table,
storage classes STATIC/EXTERNAL).

## Revisit
Partly: §3 (diagnostic message text and dumps must match byte for byte) is stricter than the
requirement catalogue demands; the owner may relax it to code + span + severity if porting message
texts proves costly. The rest follows from confirmed reproductions.
