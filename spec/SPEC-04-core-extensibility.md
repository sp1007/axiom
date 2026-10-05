# SPEC-04 — Core extensibility contract

## Tóm tắt
Tài liệu này chốt **hợp đồng mở rộng của lõi C `axiom0`**: axiom0 chỉ cài tập con self-host (SPEC-00
§9), nhưng mọi mô hình dữ liệu lõi — TypeKind, HIR/THIR, MIR, LIR/Machine IR, mô tả target, mô hình
object/artifact, chẩn đoán — phải **dành chỗ ngay từ đầu** cho mọi epic sau này (P11–P22), để khi viết
lại bằng Axiom (axiomc) chỉ cần "cắm thêm", không phải thiết kế lại ("cài sau ≠ thiết kế sau", 0263 §42).
- Ba cơ chế: **giá trị enum dành sẵn** (có tên, không bao giờ đổi số), **bảng mở rộng** gắn theo ID
  (axiom0 để trống), **hook của target** (bảng hàm/bảng dữ liệu; axiom0 chỉ có x86_64-windows).
- Gặp cấu trúc ngoài tập con: pha đầu tiên nhìn thấy nó báo `AX_PARSE_/AX_TYPE_/AX_DRIVER_
  UNSUPPORTED_IN_BOOTSTRAP` kèm `construct` và `epic` — không bao giờ crash, không bao giờ dịch sai im lặng;
  pha sau gặp biến thể dành sẵn là lỗi nội bộ có chẩn đoán (`AX_ICE`).
- **Loại artifact là dữ liệu**: obj/exe/static lib/dynamic lib (+ import lib) tách khỏi định dạng
  object/archive/image; lõi chỉ xuất `.obj`/`.exe`, E18.7 và E16.10 thêm writer mà không thiết kế lại.
- Chốt **tên và chữ ký cuối cùng** của các intrinsic: wrapping/bit, bộ nhớ/con trỏ, và giao diện
  host (ADR-0002) — thêm `host.exe_path` để axiomc tìm thư mục `std/` (ADR-0013).
- Hợp đồng registry (ADR-0005 §2): mã chẩn đoán theo vùng, lệnh/emitter của driver theo file, bảng
  option thuộc lệnh/stage; giao diện const-evaluator; parser MIR dạng text chỉ là hạ tầng test bằng C.
- Bảng phủ epic: mọi epic P11–P22 chạm tới mô hình dữ liệu lõi đều có điểm mở rộng có mã `AXS-EXT-…`.
Quyết định: ADR-0013 (cùng ADR-0001, ADR-0002, ADR-0004, ADR-0005, ADR-0006).

Status: canonical (T003a, 2026-10-05). Rule ids `AXS-EXT-NNN` are stable (never renumbered).
Decisions: ADR-0013 (this spec and the self-host subset closure), ADR-0001 (fixed addresses),
ADR-0002 (host interface), ADR-0003 (ABI lowering on LIR), ADR-0004 (subset additions), ADR-0005 §2
(registries), ADR-0006 (bootstrap forms). Subset: `spec/SPEC-00-bootstrap.md` §9 and
`spec/selfhost-subset.tsv`. Semantics: `spec/SPEC-03-core-semantics.md`. Plan frame:
`spec/ROADMAP.md` (R6, R7). Consumers: T010–T087 (every axiom0 data model), T076 (re-audit),
planning tasks T211–T222 (where each epic plugs in).

---

## 1. Principles

**AXS-EXT-001 — Implement later ≠ design later.** Each core data model of axiom0 contains, from
the task that creates it, every variant and field this spec lists, including those whose semantics
arrive only in a post-T087 epic. Creating such a variant is *required*; implementing its semantics in
axiom0 is *forbidden* (SPEC-00 AXS-BOOT-001, ROADMAP R7). [0263 §42; 0054 §23-27; 0152 §5]

**AXS-EXT-002 — Variant sets are normative, spellings are not.** The variant/field *sets* below are
normative: a task that creates the model includes all of them, and the axiomc port (T077–T085) keeps
the same set so differential dumps agree. C identifiers are the engineer's choice (TYPE A); the
`inspect --emit=…` dumps print the names used in this spec.

**AXS-EXT-003 — Append-only enumerations.** Every enumeration of a core model (type kinds, HIR/MIR
node kinds, intrinsic ids, relocation kinds, …) is append-only: values are never renumbered, removed
or reused. Reserved values are declared with their final name and a comment
`/* RESERVED <epic> (SPEC-04 AXS-EXT-nnn) */`. Nothing in axiom0 depends on the numeric value of an
enumerator except serialisation inside one run.

**AXS-EXT-004 — Three extension mechanisms.**
1. **Reserved enum value** — a named variant in an existing enum (`Float` in TypeKind).
2. **Extension table** — a side table keyed by an existing ID (`ItemId → Placement`), empty in axiom0.
   Absent entry = the default behaviour. Side tables keep hot structs small and let an epic add
   information without touching every node.
3. **Target hook** — data in the target description (`TargetDesc`, §7) plus a table of functions per
   target (`TargetHooks` in C; an enum + `match` in axiomc). axiom0 has exactly one instance.
[0163 §1; 0056 §119-121]

**AXS-EXT-005 — No hidden state.** Every phase is a function of explicit context structs and input
IDs to output tables (axiom-c-stage0). No mutable globals outside `driver/`. This is the extension
point of the query engine, incremental and parallel compilation (E18.1–E18.3): they change *who calls*
the phases, never the phases' data. [0054 §45; 0056 §85-86; tasks/0533]

**AXS-EXT-006 — Determinism is part of the contract.** Every table that is iterated for output is
ordered by stable IDs or sorted; reserved fields default to a fixed value; no artifact contains an
absolute path (ADR-0006 §8), a timestamp or a pointer value. Fingerprinting (E18.2) and reproducible
bootstrap (T087) rely on it.

## 2. Behaviour on encountering out-of-subset constructs

**AXS-EXT-010 — First seeing phase rejects.** A construct that is valid Axiom but outside the
self-host subset is rejected by the *first* axiom0 phase that can recognise it, with exactly one
diagnostic, and compilation continues with an error node (`Error` type, error expression) so further
diagnostics are not cascades:

| Phase that sees it | Code | Examples |
|---|---|---|
| parser (S1 grammar, SPEC-02 AXS-GRM-003) | `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` | `async fn`, `.await`, `comptime fn`, `comptime { }` |
| HIR lowering (attribute registry, §10) / type checking | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | `f32`, `1.5`, `i128`, `static`, `dyn Trait`, `@at`, `@export` |
| driver (options, manifest values) | `AX_DRIVER_UNSUPPORTED_IN_BOOTSTRAP` (ADR-0013 §5) | manifest `kind = "dll"` |
| driver (target triple) | `AX_DRIVER_UNKNOWN_TARGET` | `--target x86_64-linux` (data `epic = "E16.9"`) |

Every such diagnostic carries `data.construct` (the spelling, e.g. `"f64"`, `"@at"`, `"dyn"`) and
`data.epic` (the roadmap epic that delivers it, from the tables of §3–§9). [spec/diagnostics.md
AXD-013; ADR-0011 §3; ADR-0013 §5]

**AXS-EXT-011 — Later phases never see reserved variants.** Because of AXS-EXT-010, a phase after the
rejecting one never receives a reserved variant. If it does, that is an internal invariant failure:
it reports `AX_ICE(...)` (a diagnostic with location, then a controlled abort — spec/diagnostics.md
AXD-042), never undefined behaviour, a segfault or a silent miscompile. Every `switch` over a core
enumeration has an explicit case or a `default:` that raises `AX_ICE`.

**AXS-EXT-012 — Not-yet versus never-in-axiom0.** A construct *inside* the subset whose delivering
task is not done yet gets the transient `AX_<AREA>_NOT_YET_SUPPORTED` / `AX_DRIVER_NOT_YET_SUPPORTED`
(AXD-014, SPEC-00 AXS-BOOT-006) with `data.task`. A construct *outside* the subset gets the permanent
`_UNSUPPORTED_IN_BOOTSTRAP` code with `data.epic`. The two are never mixed: `data.task` names a P0–P10
task, `data.epic` an epic `E11.1`…`E22.4` (or `E23.x`).

**AXS-EXT-013 — Dumps show reserved names.** `inspect --emit=hir|thir|mir|lir|mc` print variant
names from this spec. A reserved variant never appears in a dump of an accepted program; a test may
only observe it through the diagnostic of AXS-EXT-010.

## 3. Types — TypeKind

**AXS-EXT-020 — TypeKind variants.** Types are hash-consed (`TypeId`, equality = id equality). The
variant set:

| Variant | Fields | axiom0 | Epic / task | axiom0 behaviour |
|---|---|---|---|---|
| `Int` | width (8/16/32/64/ptr), signed | implemented | T017, T034 | — |
| `Int128` | signed | **reserved** | E12.1 | `i128`/`u128` → `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` |
| `Float` | width (32/64; 16 reserved) | **reserved** | E12.2 | `f32`/`f64`/float literal → `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (T034) |
| `Bool`, `Char`, `Unit`, `Never` | — | implemented | T017, T034 | — |
| `Str` | — | implemented | T041 (folded into views by T048b) | — |
| `Tuple` | element types | implemented | T035 | — |
| `Array` | element, length (const value) | implemented | T036 | — |
| `Slice` | element (dynamic `[T]`, only behind a view or pointer) | implemented | T048b | — |
| `Adt` | AdtId (struct/enum/union kind, §3.1), generic args | implemented (union reserved) | T035, T038, T054 | — |
| `View` | capability (`view` / `mut_view`), referent, region var | implemented | T048 | — |
| `RawPtr` | mutability, pointee, **address space** (0 = generic) | implemented; address space reserved | T061a; E13.2, E22.2 | non-zero address space is never produced in axiom0 |
| `FnDef` | FnId, generic args | implemented | T032, T054 | — |
| `FnPtr` | signature (§3.2) | implemented | T057 | — |
| `Closure` | ClosureId, captured-environment type | implemented | T057 | — |
| `Param` | generic parameter index (type kind; const kind reserved, AXS-EXT-031) | implemented | T054 | — |
| `Infer` | type variable / integer variable | implemented | T017 | — |
| `Error` | — | implemented | T017 | stops cascades (AXS-EXT-010) |
| `Vector` | element scalar, lane count | **reserved** | E12.3 | lang type names → `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` |
| `Mask` | lane count | **reserved** | E12.3 | as above |
| `Dyn` | trait list (principal + auto traits), region var | **reserved** | E14.4 | `dyn Trait` → `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (T017; T015b keeps the HIR node) |
| `Coroutine` | CoroutineId, resume/yield/return types | **reserved** | E11.4 (async), E14.3 (generators) | `async fn` rejected by the parser; never constructed |

`Option`/`Result` are ordinary `Adt`s (lang items) — built-in non-generic until T054b (ADR-0006 §4).
`Atomic<T>`, `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>` are **lang-item ADTs** of std
(E11.2, E13.2/E13.6), not TypeKinds: the lang-item table (§3.3) marks them, and field access through
them lowers to the MIR ops of AXS-EXT-043. [0054 §26-27; 0161 §30-31; ADR-0001 §2]

**AXS-EXT-021 — ADT kinds and repr (§3.1).** `AdtKind = Struct | Enum | Union`; `Union` is reserved
(E13.2; `union` is a reserved keyword, SPEC-02 AXS-GRM-038). `Repr = Axiom | C | Packed(n) |
Align(n) | Transparent`; axiom0 implements `Axiom` (T035) and `C` (T065); `Packed`, `Align` and
`Transparent` are reserved (E13.2): `@align(16)` → `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`. Enum
discriminants are implicit (0, 1, 2, … — SPEC-03 AXS-SEM-062); the layout record has a
`discriminant` field per variant so explicit discriminants (E13.2) need no model change.

**AXS-EXT-022 — Function signatures (§3.2).** A signature is `{params, ret, abi, is_unsafe, domain,
target_features}`. `abi = Axiom | C | System` implemented (T032, T065); reserved: `Interrupt` (E13.x
freestanding), `ThisCall`/`StdCall`/`FastCall` (i686 epic candidate, ADR-0001 §5), `GpuKernel`
(E22.1). `domain = Host` implemented; `Device(kind)` reserved (E22.1). `target_features` is an empty
set in axiom0 (E12.5). `is_unsafe` implemented (T061a).

**AXS-EXT-023 — Lang-item table (§3.3).** A table `LangItem → DefId` filled from `std` attributes or
known paths: implemented entries `Option`, `Result`, `Drop`, `Copy`, `Clone`, `Eq`, `PartialEq`,
`Ord`, `Hash`, operator traits, `Iterator`, `Range`, `RangeInclusive` (T039, T054b, T055–T056, T072);
reserved entries `Future`, `Waker` (E11.4), `Send`, `Share` (E11.1, auto traits), `Atomic` (E11.2),
`Volatile`, `Mmio`, `MmioRO`, `MmioWO` (E13.2/E13.6), `Generator` (E14.3), `DynMetadata` (E14.4).
Absent entries are simply unset in axiom0.

**AXS-EXT-024 — Constant values.** `ConstValue = Int(u64 bits + type) | Bool | Char | Str(bytes id) |
Aggregate(const allocation id) | FnRef(FnId) | Unit`; reserved: `Float` (E12.2), `Int128` (E12.1),
`StaticRef(SymbolId)` (E13.3), `Vector` (E12.3). See also §12 (const-evaluator interface).

**AXS-EXT-025 — Layout queries.** `layout_of(TypeId) → {size, align, fields[] offsets, variants[]
(discriminant, payload offset), abi_class}`. `abi_class` is target data (§7), so an XMM class for
floats (E12.2) or vector classes (E12.3) are new values, not a new query.

## 4. HIR and THIR

**AXS-EXT-030 — Item kinds.** `Fn`, `Struct`, `Enum`, `TypeAlias`, `Const`, `Use`, `Module`, `Impl`,
`Trait`, `ExternBlock`, `ExternFn` — implemented (T015, T015b, T060, T065). Reserved: `Static`
(E13.3; parsed, HIR node exists, rejected — T061 has the ui test), `ExternStatic` (E13.3), `Union`
(E13.2). Every item has an `ItemId` = (ModuleId, index in module), stable across runs.

**AXS-EXT-031 — Item and generic flags.** Function flags: `is_unsafe`, `is_extern(abi)` implemented;
`is_async` (E11.4), `is_comptime` (E14.1), `is_generator` (E14.3) reserved — the parser rejects the
modifier (S1) and HIR lowering never sets them in axiom0. Generic parameters: `GenericParamKind =
Type` implemented; `Const` reserved (E14.1, SPEC-02 §12). Trait flags: `is_auto` reserved (E11.1),
`is_unsafe` reserved (E13.1).

**AXS-EXT-032 — Attribute side table.** Attributes are kept as data per item/field/variant (T015b).
Interpreted attributes become entries of extension tables keyed by `ItemId`:
- `Placement { kind: Overlay | Place, address: ConstExprId | ImageRel { module: StrId (or Self), offset:
  ConstExprId }, region: Option<StrId> }` — reserved (E13.6, E13.7; ADR-0001 §4-5). axiom0 lowers
  nothing: `@at(...)` → `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` with `construct = "@at"`, `epic = "E13.6"`
  (`"E13.7"` when the argument uses `image(...)`/`image_self()`).
- `Export { name }` (E18.7), `Entry` (E13.3), `TargetFeature { features }` (E12.5), `Cfg { predicate
  }` (E16.8), `Align` (E13.2), `Domain` (E22.1), `ThreadLocal` (E11.3) — reserved.
- `Repr`, `Link { library }` (T065), `Derive { traits }` (T046 Copy marker, T056 general), `Intrinsic`
  (T034 built-ins, T061a/T061c declarations), `Inline` (accepted and ignored; hint for E15.4) —
  implemented. The full registry is AXS-EXT-091.

**AXS-EXT-033 — Expression kinds.** Implemented: every S0 expression form of SPEC-02 (literals,
paths, calls, method calls, fields, tuple index, index and sub-range index, unary/binary operators,
casts, blocks, `if`, `match`, `loop`, `while`, `for` (desugared by T072), `break`/`continue` with
labels and values, `return`, `?`, closures, struct/array/tuple literals, repeat literals, `view(x)`,
`mut_view(x)`, `unsafe { }`, raw deref `*p`, `p->f`). Reserved: `Await` (E11.4), `ComptimeBlock`
(E14.1), `Yield` (E14.3), `AsyncBlock` (E11.4). The parser rejects their syntax (S1 or reserved
keyword); the HIR kinds exist so axiomc adds lowering without a model change.

**AXS-EXT-034 — Patterns.** Implemented: wildcard, binding (`mut`), literal (integer, `char`, `bool`,
byte), range (integer, `char`), or, tuple, struct, variant, `..` rest in structs (T011, T012, T038,
T038b). Reserved: float literal patterns (E12.2), slice patterns, binding-at, string literal patterns
(planning T214; SPEC-02 §12).

**AXS-EXT-035 — THIR coercions and adjustments.** Implemented: `NeverToAny`, view reborrow
(`mut_view` → `view`), integer-literal fixing (SPEC-03 AXS-SEM-020), `Str` → `view<[u8]>` where
SPEC-11 allows. Reserved: `Unsize` (to `dyn`, E14.4), `IntToFloat` literal fixing (E12.2),
`ClosureToFnPtr` beyond non-capturing closures (T057 decides; reserved for E14.x if excluded).

## 5. MIR

**AXS-EXT-040 — Bodies.** `BodyKind = Fn | Const | DropGlue | ClosureBody` implemented (T018, T054b,
T057, T061); reserved `Coroutine` (E11.4/E14.3: a body whose locals live across `Suspend`) and
`Kernel` (E22.1: a device entry). Each body has `locals[]` with types, `blocks[]`, and a
`var_debug_info[]` table (name, local, span) — filled by T019 because diagnostics need names, emitted
as debug info only by E17.1/E17.2.

**AXS-EXT-041 — Places.** `Place = base + projections`.
- Bases: `Local` (T018), `ConstAlloc(const allocation id)` (constant tables, T061); reserved
  `Static(SymbolId)` (E13.3) and `FixedStatic(SymbolId)` (E13.6, ADR-0001 §4).
- **Provenance** of a place is derived from its base: `local`, `const`, `heap/raw` (through a raw
  pointer deref, T061a), and reserved `static` and `fixed` (E13.3, E13.6). Views of `fixed` places have
  static lifetime (ADR-0001 §3); capability analysis (T048) reads provenance through one query, so the
  new provenances need no new analysis entry point.
- Projections: `Field(i)`, `Index(local)`, `ConstIndex(n)`, `Subslice(from, to)`, `Deref`,
  `Downcast(variant)` — implemented (T018, T036, T038, T048b, T061a). Nothing reserved.

**AXS-EXT-042 — Rvalues.** Implemented: `Use(Copy|Move|Const)`, `BinaryOp(op)` (the checked forms
are `BinaryOp` + an `Assert` terminator, SPEC-03 AXS-SEM-030), `UnaryOp`, `WrappingOp`/`BitOp`
(ADR-0004 §1), `Cast(kind)`, `Aggregate(kind)`, `View`, `MutView`, `Len`, `Discriminant`,
`AddressOf(mutability)` (T061a), `NullaryOp(SizeOf | AlignOf | NeedsDrop)`. Reserved:
- `BinaryOp` operators `SatAdd`, `SatSub`, `SatMul` (E12.1); float operands of the existing operators
  (E12.2);
- `Cast` kinds `IntToFloat`, `FloatToInt`, `FloatConvert` (E12.2), `Unsize` (E14.4),
  `PtrAddrSpace` (E13.2/E22.2);
- `VectorOp { op, lanes }`, `Splat`, `Extract`, `Insert`, `Shuffle`, `Reduce` (E12.3).

**AXS-EXT-043 — Statements.** Implemented: `Assign`, `StorageLive`, `StorageDead`, `SetDiscriminant`,
`DropFlagSet` (T018/T049), `Nop`. Reserved:
- `Atomic { op: Load | Store | Rmw(op) | CmpXchg | Fence, ordering, place, operands }` with
  `Ordering = Relaxed | Acquire | Release | AcqRel | SeqCst` (E11.2, 0161 §30) — never lowered to a
  plain load/store in MIR;
- `VolatileLoad { dst, place, width }`, `VolatileStore { place, value, width }` (E13.2, E13.6:
  generated for every read/write of a `Volatile`/`Mmio` field, ADR-0001 §2).

**AXS-EXT-044 — Terminators.** Implemented: `Goto`, `SwitchInt`, `Call { callee, args, dest, target
}`, `Return`, `Drop { place, target }`, `Assert { cond, kind, target }` (kinds: overflow, divzero,
shift, bounds, char, assert — SPEC-00 AXS-BOOT-007), `Unreachable`. `callee = Direct(FnId+args) |
FnPtr(operand) | Intrinsic(IntrinsicId)`. Reserved:
- `callee = Virtual { receiver, slot }` (E14.4, 0161 §31);
- `Suspend { value, resume: BlockId, drop: BlockId }` (E11.4/E14.3, 0161 §29);
- field `cleanup: Option<BlockId>` on `Call`, `Drop`, `Assert` — always `None` in axiom0 (panic =
  abort, SPEC-03 AXS-SEM-071); used by E13.5 when unwinding is chosen for a profile.

**AXS-EXT-045 — Pass slots.** MIR passes run through one ordered pass list owned by the driver
pipeline (T043 `-O1`, `--verify-each`): every pass is `verified MIR → verified MIR`, and the verifier
runs between passes in `--verify-each`. E15.x passes, E17.6 instrumentation and E18.5 pass contracts
add entries to this list; OptIR (E15.1) is a separate IR built *from* verified MIR, not a MIR change.
[0161 §19-20, §41; 0054 §35-36]

## 6. LIR and machine IR

**AXS-EXT-050 — LIR values and types.** Virtual registers have a register class. Classes: `Gpr`
implemented; reserved `Xmm` (scalar float, E12.2), `Vec128`, `Vec256`, `Vec512` (E12.3/E12.4),
`Mask` (E12.4), `Pred` (E16.x targets with predicate registers). LIR scalar types `i8 i16 i32 i64
ptr` implemented; reserved `i128` (lowered to pairs, E12.1), `f32 f64` (E12.2), `v128 v256 v512`
(E12.3). [0162 §5-7]

**AXS-EXT-051 — Memory operations.** `Load/Store { width, align, addr_space, flags }`; `addr_space`
is 0 in axiom0 (reserved E13.2/E22.2); `flags` is a bit set whose bits `volatile` (E13.2/E13.6) and
`nontemporal` (E12.4) are reserved (always 0 in axiom0). Reserved ops: `AtomicLoad`, `AtomicStore`,
`AtomicRmw`, `AtomicCmpXchg`, `Fence` with an ordering (E11.2). [0162 §9-12, §32]

**AXS-EXT-052 — Calls and ABI.** LIR calls carry an abstract ABI placeholder rewritten by the `abi`
pass (ADR-0003). `CallConv = Win64` implemented (T025); reserved `SysV64` (E16.9), `Aapcs64`
(E16.3/E16.4/E16.12), `Wasm` (E16.6), `RiscV` (E16.7), `Interrupt` (E13.x), `GpuKernel` (E22.3).
ABI argument classification is a table in the target description (§7), so XMM argument passing
(E12.2) adds rows, not code paths. LIR op `check_ovf <kind>` is implemented (SPEC-00 AXS-BOOT-007).

**AXS-EXT-053 — Machine IR.** Machine instructions name registers as `Reg { class, index,
is_virtual }` from day one. axiom0 maps virtual registers with the baseline strategy of T025/T025b
(fixed registers and stack slots, marked `BOOTSTRAP-SHORTCUT`); linear-scan allocation (E15.8, or the
conditional pull-in of ADR-0005 §7) is one pass inserted between instruction selection and frame
lowering, with no change to the instruction model. The encoder (T024) is table-driven by opcode map;
the legacy and `0F` maps are implemented, `0F38`, `0F3A`, VEX and EVEX prefixes are reserved
(E12.4).

**AXS-EXT-054 — Frame and debug records.** Frame lowering (T025b) records a `FrameLayout` per
function (prologue size, pushed callee-saved registers, stack allocation, frame register) as data;
axiom0 uses it only for the machine verifier. E17.3 serialises it into `.pdata`/`.xdata`. Every LIR
and machine instruction keeps the source span of its MIR origin; the encoder can emit a
`(code offset, span)` table — E17.1/E17.2 turn it into line tables. Function attributes `naked`
(E13.x), `target_features` (E12.5) and `domain` (E22.1) are reserved fields.

## 7. Target description

**AXS-EXT-060 — TargetDesc is data.** One record per target: triple (`arch`, `os`, `env`), pointer
width, endianness, object format id, image format id, default `CallConv`, register file (names,
encodings, classes, aliases), caller/callee-saved sets, stack alignment, shadow space / red zone,
ABI classification table, feature set, and the target hooks (`isel`, `abi_lower`, `frame_lower`,
`encode`, `object_writer`, `image_writer`). axiom0 contains exactly one record, `x86_64-windows`
(MS x64 ABI, COFF, PE32+). [0163 §1-7; ROADMAP R6, E16.1]

**AXS-EXT-061 — Target names.** `--target` accepts `x86_64-windows` (default). Every other triple of
the roadmap (`x86_64-linux` E16.9, `aarch64-linux` E16.3, `aarch64-macos` E16.4, `aarch64-android`
E16.5, `wasm32` E16.6, `riscv64-linux` E16.7, `aarch64-windows` E16.12) is a *known* name that axiom0
rejects with `AX_DRIVER_UNKNOWN_TARGET` and `data.epic`; unknown names get the same code without
`epic`. Target-dependent code in frontend or MIR is forbidden: the only target queries above LIR are
pointer width, endianness and `layout_of` (0056 §119).

**AXS-EXT-062 — Profiles and panic strategy.** The driver carries `Profile = Hosted | Freestanding |
Kernel | System` (only `Hosted` in axiom0; the rest E13.3/E13.4) and `PanicStrategy = Abort |
Unwind` (only `Abort`; `Unwind` E13.5). They are fields of the compilation session, not globals.

## 8. Object model, artifact kinds, linker

**AXS-EXT-070 — Artifact kind is data (REQ-OWNER-006).** The driver plans a build as
`{ artifact: ArtifactKind, target: TargetDesc, object_format, archive_format, image_format }`:

| Dimension | Values implemented in axiom0 | Reserved (epic) |
|---|---|---|
| `ArtifactKind` | `Object` (`.obj`, T026/T028), `Executable` (`.exe`, T027/T028) | `StaticLib` (E18.7, E16.10), `DynLib` = image + import library (E18.7, E16.2, E16.10), `Universal` = composition of per-target artifacts (E16.11) |
| `ObjectFormat` | `Coff` | `Elf` (E16.9), `MachO` (E16.4), `Wasm` (E16.6), `SpirV` (E22.3) |
| `ArchiveFormat` | — (none needed) | `CoffAr` (E18.7: `!<arch>` with MS long-name member), `GnuAr` (E16.9), `BsdAr` (E16.4) |
| `ImageFormat` | `Pe32Plus` console executable | `Pe32PlusDll` (E18.7), `ElfExec`, `ElfDyn` (E16.9, E16.2), `MachO` (E16.4), `RawBinary` (E13.6 freestanding images) |
| Linker inputs | our COFF objects + synthesised import tables (`@link`, T065) | archives and import libraries (E18.6, E18.7), foreign objects (E18.6) |

The four dimensions are independent: an epic adds a writer/reader for one value without touching the
others (E18.7 adds `CoffAr` + `Pe32PlusDll`; E16.10 combines them per target). axiom0 has no CLI or
manifest spelling for the reserved kinds: manifest `[package] kind` other than `exe` →
`AX_DRIVER_UNSUPPORTED_IN_BOOTSTRAP` (`epic = "E18.7"`; ADR-0006 §7, ADR-0013 §5).

**AXS-EXT-071 — Sections.** `Section { name, kind, flags, align, bytes, relocs, pinned_vma:
Option<u64>, comdat: Option<SymbolId> }`. Kinds `Text`, `RData`, `Data`, `Bss` implemented (T024,
T026, T042, T061d); reserved `Tls` (E11.3), `PData`, `XData` (E17.3), `Debug` (E17.1/E17.2),
`BaseReloc` (E18.7), `Custom(name)` (E18.4 `.axmeta` sections). `pinned_vma` (E13.6 placement) and
`comdat` (E15.6/E18.6 section GC) are always `None` in axiom0.

**AXS-EXT-072 — Symbols.** `Symbol { name, section: Index(i) | Undefined | Absolute, value, binding:
Local | Global | Weak, kind: Func | Data | Section, export: bool, import: Option<{dll, name}> }`.
Implemented: section index, `Undefined`, `Local`/`Global`, `Func`/`Data`/`Section`, imports (T027,
T065). Reserved: `Absolute` (E13.6 overlays: COFF `IMAGE_SYM_ABSOLUTE`, ELF `SHN_ABS`), `Weak`
(E18.6), `export = true` (E18.7 `@export`). Symbol order in every output is by name (determinism).

**AXS-EXT-073 — Relocations.** Target-neutral kinds with a per-format mapping: `Rel32` (+ addend),
`Addr64`, `Addr32Nb` implemented (T024, T026); reserved `SecRel`, `SectionIndex` (CodeView, E17.1),
`GotPcRel`, `Plt32`, `Pc64`, `Abs32` (E16.9/E16.2), `TlsRel` (E11.3), AArch64 page/offset kinds
(E16.3), `LoadTimeSlot` (E13.7: a slot filled by module-init code, ADR-0001 §5).

**AXS-EXT-074 — Linker contract.** The PE linker (T027) consumes a *list* of objects and resolves by
name, so separate compilation (E18.6) adds inputs, not a new design. It never depends on MIR/HIR
(0263 §46). Startup code is generated by the linker (no CRT, SPEC-00 X-CRT); module initialisers
(E13.7, E18.7 `DllMain`) are an ordered list of init functions, empty in axiom0.

## 9. Diagnostics

**AXS-EXT-080 — Diagnostic model.** `Diagnostic { code, severity, primary span, labels[], notes[],
helps[], fixits[], data }` (T009). Severities `error`, `warning` implemented; `info`, `hint` reserved
for tooling (E19.1, AXD-040). `fixits` carry machine-applicable edits (E19.4 reuses them unchanged);
`data` is the key/value map used by AXS-EXT-010 (`construct`, `epic`, `task`). New areas for later
epics (`ASYNC`, `CONC`, `GPU`, …) are added by AXD-022, never by reusing an existing area.

**AXS-EXT-081 — Registry contracts (ADR-0005 §2, §14).**
1. **Per-area code files.** `bootstrap/axiom0/src/diag/codes/<AREA>.def`, one X-macro file per area
   of spec/diagnostics.md §3, included by `codes.def`; a task appends codes only to the area files in
   its `locks:`; `codes.def` is edited only by an AXD-022 task.
2. **Command and emitter registration.** One file per command (`src/driver/cmd_<name>.c`) and per
   inspect emitter (`src/driver/emit_<name>.c`), collected by the CMake-generated table (T004);
   adding one never edits a shared file.
3. **Pipeline stages.** `src/driver/pipeline.c` is the ordered stage list (T016); a stage task adds
   one registration line and lists the file in `locks:`.
4. **Option tables.** Options are declared in a table next to the command or stage that owns them
   (T016): `--stack-reserve` (T027/T028), `--std-root` (T060), `--verify-each` (T043), `--step-limit`
   (T021). No central option parser is edited by a later task.
5. **axiomc.** The port keeps the same registries as Axiom data: one module per command/emitter, a
   constant table of `(name, CommandKind)` dispatched with `match` (no function pointers in constant
   tables, ADR-0013 §3), area code tables as `const` aggregate tables.

## 10. Driver, attributes, pipeline

**AXS-EXT-090 — Session and pipeline.** A compilation session holds the source DB, diagnostic sink,
target, profile, panic strategy, options and the per-phase output tables, all keyed by stable IDs
(FileId, ModuleId, ItemId, BodyId, TypeId). The pipeline runs stages eagerly in order. The query
engine (E18.1) replaces the eager order by demand-driven queries over the same keys; stage outputs
are deterministic and therefore fingerprintable (E18.2). Reserved session fields: `fingerprints`
(E18.2), `jobs` (E18.3); absent in axiom0.

**AXS-EXT-091 — Attribute registry.** The registry is a table `name → {allowed positions, argument
shape, status}`; T015b looks names up while lowering attributes to HIR. An unknown name is an error
of T015b (it registers the NAME-area code, AXD-032). Status per name:

| Attribute | Positions | Status in axiom0 | Delivering task / epic |
|---|---|---|---|
| `@derive(...)` | struct, enum | implemented | T046 (`Copy` marker), T056 (`Copy, Clone, Eq, PartialEq, Ord, Hash`) |
| `@repr(C)` | struct, enum | implemented | T065 |
| `@link("lib")` | extern block | implemented | T065 |
| `@intrinsic` | body-less fn in `std/core` | implemented | T034 (built-ins), T061a, T061c |
| `@inline` | fn | accepted, no effect | hint for E15.4 |
| `@at(...)` | static, fn, extern fn | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | E13.6 / E13.7 |
| `@export(...)` | fn, static | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | E18.7 |
| `@entry` | fn | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (the entry is `main`, SPEC-03 AXS-SEM-080) | E13.3 |
| `@align(n)` | struct, field | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | E13.2 |
| `@cfg(...)` | any item, field | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | E16.8 |
| `@target_feature(...)` | fn | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | E12.5 |
| `@thread_local` | static | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | E11.3 |

Before the delivering task of an implemented attribute is done, a stage that meets it reports
`AX_NAME_NOT_YET_SUPPORTED` / `AX_TYPE_…` per AXS-EXT-012. Adding an attribute later is an edit of
this table (architect) plus the delivering task.

## 11. Intrinsics

**AXS-EXT-100 — Declaration and identity.** An intrinsic is a body-less function declared with
`@intrinsic` in `std/core/intrinsics.ax` or `std/core/host.ax`; the compiler maps the declaration by
module and name to an `IntrinsicId` (append-only enum). A call is an ordinary MIR `Call` with
`callee = Intrinsic(id)` (ADR-0002 Consequences: the TypeKind/MIR reserve nothing for them). Until
T060 provides std loading, the T034/T036/T041 intrinsics are built-in prelude names with the same
signatures (BOOTSTRAP-SHORTCUT, ADR-0006 §3). A new intrinsic needs an edit of this section, not an
ADR (ADR-0002 §1). The names below are final.

**AXS-EXT-101 — Core and numeric intrinsics.** (`T` = any of the ten integer types; semantics
SPEC-03.)

| Intrinsic | Signature | Oracle / native task |
|---|---|---|
| `wrapping_add`, `wrapping_sub`, `wrapping_mul` | `fn(a: T, b: T) -> T` | T034 / T037 |
| `wrapping_neg` | `fn(a: T) -> T` | T034 / T037 |
| `rotate_left`, `rotate_right` | `fn(x: T, n: u32) -> T` | T034 / T037 |
| `leading_zeros`, `trailing_zeros`, `count_ones` | `fn(x: T) -> u32` | T034 / T037 |
| `panic` | `fn(msg: Str) -> never` | T041 / T042 (compiler-inserted checks: T021 / T028, T037) |
| `assert` | `fn(cond: bool)` | T034 / T037 |
| `unreachable` | `fn() -> never` | T034 / T037 |
| `len` | built-in over `[N]T`, `view<[T]>`, `Str` → `usize` | T036, T041, T048b / T037, T042, T051 |
| `print` | `fn(s: Str)` (bootstrap output; std.io replaces it for programs, ADR-0006 §9) | T041 / T042 |
| `print_int` | `fn(n: i64)` | T041 / T042 |
| `drop` | `fn<T>(x: T)` (moves and drops) | T049 / T051 |

`checked_*` and `overflowing_*` are library code in T069 over these intrinsics and comparisons;
saturating operations are E12.1. No float intrinsic exists in axiom0.

**AXS-EXT-102 — Memory and pointer intrinsics** (T061a oracle, T061b native; all `unsafe fn` except
`size_of`, `align_of`, `needs_drop`, `null`, `null_mut`, `is_null`, `forget`).

| Intrinsic | Signature |
|---|---|
| `size_of`, `align_of` | `fn<T>() -> usize` |
| `needs_drop` | `fn<T>() -> bool` |
| `forget` | `fn<T>(x: T)` |
| `drop_in_place` | `unsafe fn<T>(p: *mut T)` |
| `ptr_copy` | `unsafe fn<T>(src: *const T, dst: *mut T, count: usize)` (overlap-safe) |
| `ptr_copy_nonoverlapping` | `unsafe fn<T>(src: *const T, dst: *mut T, count: usize)` |
| `ptr_write_bytes` | `unsafe fn<T>(dst: *mut T, byte: u8, count: usize)` |
| `address_of` | built-in over a place: `address_of(place) -> *const T` (in `unsafe`) |
| `address_of_mut` | built-in over a mutable place: `address_of_mut(place) -> *mut T` (in `unsafe`) |
| `null`, `null_mut` | `fn<T>() -> *const T`, `fn<T>() -> *mut T` |
| `is_null` | built-in over `*const T` / `*mut T` → `bool` |
| `ptr_add`, `ptr_sub` | built-in over `*const T` / `*mut T`: `(p, n: usize) -> same pointer type`, by element count (in `unsafe`; the oracle checks the result stays inside the allocation or one past it) |

Dereference `*p`, `p->field` and assignment through them are syntax (SPEC-02), not intrinsics.
`transmute` is **not** in the subset (ADR-0013 §2): pointer casts (SPEC-03 AXS-SEM-060) and reads
through a cast pointer cover every self-host need.

**AXS-EXT-110 — Host-interface intrinsics** (ADR-0002; module `std/core/host.ax`, referred to as
`host.<name>`; oracle T061c; native `__ax_host_<name>` in `std/sys/windows/*.ax`). Conventions:
- No floats; text is UTF-8 `(ptr, len)` at the boundary; the native side converts to UTF-16 (T071c).
- Handles are `i64`. `stdio(0|1|2)` returns the handles of stdin, stdout, stderr. In the oracle,
  handles are small integers (0–2 for stdio, then 3, 4, … in opening order — deterministic).
- A fallible call returns `i64`: `>= 0` success value, `< 0` a negated **host error kind**:
  `-1` NotFound, `-2` PermissionDenied, `-3` AlreadyExists, `-4` InvalidInput (bad handle, bad mode,
  invalid UTF-8), `-9` Other. The OS error number is not observable (determinism, SPEC-03 AXS-SEM-003).
- Buffer-returning calls take `(buf: *mut u8, cap: usize)` and return the **full** length `n`; they
  write `min(n, cap)` bytes; the caller retries with a larger buffer when `n > cap`.
- Every pointer argument must lie inside a live allocation (oracle bounds check →
  `AX_UNSAFE_INTERP_UB`). Calls taking pointers are `unsafe fn`.

| Intrinsic | Signature | Native module / task |
|---|---|---|
| `heap_alloc` | `unsafe fn(size: usize, align: usize) -> *mut u8` (null on exhaustion; `size > 0`, `align` a power of two ≤ 4096) | `heap.ax` / T070 |
| `heap_realloc` | `unsafe fn(p: *mut u8, old_size: usize, new_size: usize, align: usize) -> *mut u8` (null on failure, old block intact) | `heap.ax` / T070 |
| `heap_free` | `unsafe fn(p: *mut u8, size: usize, align: usize)` | `heap.ax` / T070 |
| `stdio` | `fn(which: u32) -> i64` | `io.ax` / T074 |
| `open` | `unsafe fn(path: *const u8, path_len: usize, mode: u32) -> i64` (`0` read, `1` write+create+truncate, `2` append+create) | `io.ax` / T074 |
| `read` | `unsafe fn(h: i64, buf: *mut u8, cap: usize) -> i64` (bytes read; 0 = end of file) | `io.ax` / T074 |
| `write` | `unsafe fn(h: i64, p: *const u8, len: usize) -> i64` (bytes written; console handles use `WriteConsoleW`, ADR-0006 §9) | `io.ax` / T074 |
| `close` | `fn(h: i64) -> i64` | `io.ax` / T074 |
| `file_size` | `fn(h: i64) -> i64` | `io.ax` / T074 |
| `args_count` | `fn() -> usize` | `process.ax` / T074 |
| `arg` | `unsafe fn(i: usize, buf: *mut u8, cap: usize) -> i64` (`-4` when `i >= args_count()`) | `process.ax` / T074 |
| `env_get` | `unsafe fn(name: *const u8, name_len: usize, buf: *mut u8, cap: usize) -> i64` (`-1` when unset) | `process.ax` / T074 |
| `exe_path` | `unsafe fn(buf: *mut u8, cap: usize) -> i64` (absolute path of the running executable; in the oracle: of the interpreter executable) — **added by ADR-0013 §1** | `process.ax` / T074 |
| `exit` | `fn(code: i32) -> never` | `process.ax` / T074 |
| `remove` | `unsafe fn(path: *const u8, path_len: usize) -> i64` (files only) | `fs.ax` / T074b |
| `mkdir` | `unsafe fn(path: *const u8, path_len: usize) -> i64` (one level; `-3` if it exists) | `fs.ax` / T074b |
| `metadata` | `unsafe fn(path: *const u8, path_len: usize, out: *mut u64) -> i64` (writes `out[0]` = kind 1 file / 2 directory / 3 other, `out[1]` = size in bytes; no timestamps) | `fs.ax` / T074b |
| `dir_open` | `unsafe fn(path: *const u8, path_len: usize) -> i64` | `fs.ax` / T074b |
| `dir_next` | `unsafe fn(h: i64, buf: *mut u8, cap: usize) -> i64` (length of the next entry name without `.`/`..`; 0 at the end; when `n > cap` the entry is not consumed) | `fs.ax` / T074b |
| `dir_close` | `fn(h: i64) -> i64` | `fs.ax` / T074b |
| `monotonic_ns` | `fn() -> u64` (non-decreasing; origin unspecified) | `time.ax` / T074b |

Directory order is unspecified (std sorts, T074b); time is the only other non-deterministic result.
Thread, socket, memory-mapping and async-IO host calls are appended by E11.3, E21.4, E21.6 and E11.6.
Every host call is the single OS boundary of std, which is also the record/replay point of E17.7.

## 12. Const evaluation and test infrastructure

**AXS-EXT-120 — Const-evaluator interface (ADR-0004 §8).** `types` declares `ConstEvaluator {
eval(session, body: BodyId, expected: TypeId, limits) -> Result<ConstValue, Diagnostic> }`; the
driver wires the MIR interpreter into it; `types` never includes `interp` (archcheck, T006). Const
items (T061) and array lengths use it. Reserved: an `args: [ConstValue]` parameter for `comptime fn`
calls (E14.1) and const generic arguments (E14.1) — the interface already takes a body id, so E14.1
adds callers, not a new evaluator.

**AXS-EXT-121 — Constant tables.** A `const` aggregate used as a place is materialised once
(`ConstAlloc` base, AXS-EXT-041; interpreter allocation in T061, `.rdata` in T061d). Allowed leaf
types: integers, `bool`, `char`, `Str`, fieldless enums; composed by structs, tuples and fixed arrays
of these (ADR-0004 §2 as extended by ADR-0013 §3). Function values, raw pointers, views other than
`Str` and enums with payloads are rejected in constant tables with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`
(`epic = "E14.1"`).

**AXS-EXT-122 — MIR text parser is C-only.** The MIR text parser (T018) exists only to write
verifier/interpreter tests by hand. It is outside the self-host subset, is not ported to axiomc
(T076/T083 do not list it), and production code never calls it (ADR-0004 §9).

## 13. Epic coverage

**AXS-EXT-130 — Every P11–P22 epic has its extension point.** Each roadmap epic either names the
rules above that reserve its representation, or states that it touches no core data model (library,
tooling or process only). Planning tasks T211–T222 start from this table.

| Epic | Core models touched | Extension point |
|---|---|---|
| E11.1 Concurrency semantics | traits, closures | auto-trait flag AXS-EXT-031; lang items `Send`/`Share` AXS-EXT-023 |
| E11.2 Atomics & ordering | MIR, LIR, oracle | `Atomic` statement AXS-EXT-043; LIR atomics AXS-EXT-051; lang item `Atomic` |
| E11.3 Threads & sync | items, object model | `@thread_local` AXS-EXT-091; section `Tls` AXS-EXT-071; reloc `TlsRel` AXS-EXT-073; host calls AXS-EXT-110 |
| E11.4 Async/await | HIR, types, MIR | `Await`/`AsyncBlock` AXS-EXT-033; `is_async` AXS-EXT-031; `Coroutine` AXS-EXT-020/040; `Suspend` AXS-EXT-044 |
| E11.5 Executors & fibers | — (library) | intrinsic table append AXS-EXT-100 |
| E11.6 Async IO | — (library) | host-interface append AXS-EXT-110 |
| E12.1 Integer model completion | types, MIR, LIR | `Int128` AXS-EXT-020; `Sat*` ops AXS-EXT-042; LIR `i128` AXS-EXT-050 |
| E12.2 Floating point | types, consts, MIR, LIR, ABI | `Float` AXS-EXT-020/024; float casts AXS-EXT-042; `Xmm` class AXS-EXT-050; ABI table AXS-EXT-052 |
| E12.3 SIMD & vector types | types, MIR, LIR | `Vector`/`Mask` AXS-EXT-020; `VectorOp` AXS-EXT-042; vector classes AXS-EXT-050 |
| E12.4 SIMD backend | machine IR, encoder | opcode maps/VEX/EVEX AXS-EXT-053; `nontemporal` flag AXS-EXT-051 |
| E12.5 CPU features & multiversioning | signatures, target | `target_features` AXS-EXT-022/054; `@target_feature` AXS-EXT-091; feature set AXS-EXT-060 |
| E13.1 Unsafe & UB model | MIR, oracle | provenance AXS-EXT-041; trait `is_unsafe` AXS-EXT-031; oracle memory model (T061a) |
| E13.2 Raw memory, volatile, layout | types, MIR, LIR | `Union`/`Repr` AXS-EXT-021; address space AXS-EXT-020/051; volatile ops AXS-EXT-043; `@align` AXS-EXT-091 |
| E13.3 Runtime composition, freestanding | items, places, driver | `Static` AXS-EXT-030/041; `Profile` AXS-EXT-062; `@entry` AXS-EXT-091; init list AXS-EXT-074 |
| E13.4 Safety profiles | driver | `Profile` AXS-EXT-062; attribute registry AXS-EXT-091 |
| E13.5 Panic & unwinding | MIR, driver | `cleanup` edges AXS-EXT-044; `PanicStrategy` AXS-EXT-062; `FrameLayout` AXS-EXT-054 |
| E13.6 Fixed-address declarations | HIR, MIR, object model, linker | `Placement` AXS-EXT-032; `FixedStatic` + `fixed` provenance AXS-EXT-041; volatile ops AXS-EXT-043; `Absolute` symbols AXS-EXT-072; `pinned_vma` AXS-EXT-071; `RawBinary` AXS-EXT-070 |
| E13.7 Module-relative bindings | HIR, object model | `ImageRel` address AXS-EXT-032; `LoadTimeSlot` AXS-EXT-073; init list AXS-EXT-074 |
| E14.1 Comptime completion | HIR, generics, const eval | `ComptimeBlock` AXS-EXT-033; `is_comptime`, const generic params AXS-EXT-031; evaluator `args` AXS-EXT-120 |
| E14.2 Reflection & derive | attributes | derive registry AXS-EXT-091; attribute side table AXS-EXT-032 |
| E14.3 Generators | HIR, types, MIR | `Yield` AXS-EXT-033; `Coroutine` AXS-EXT-020/040; `Suspend` AXS-EXT-044 |
| E14.4 dyn Trait & vtables | types, THIR, MIR, object model | `Dyn` AXS-EXT-020; `Unsize` AXS-EXT-035/042; `Virtual` callee AXS-EXT-044; vtables are `RData` constants with relocations AXS-EXT-071/073 |
| E15.1 OptIR | — (new IR from verified MIR) | pass slots AXS-EXT-045 |
| E15.2 Alias & escape analysis | — (OptIR) | pass slots AXS-EXT-045 |
| E15.3 Loops & BCE | — (OptIR) | pass slots AXS-EXT-045 |
| E15.4 Inlining & specialization | MIR passes | pass slots AXS-EXT-045; `@inline` AXS-EXT-091 |
| E15.5 Auto-vectorization | — (needs E12.3) | vector types AXS-EXT-020/042 |
| E15.6 LTO, section GC, PGO | object model | `comdat` AXS-EXT-071; `Custom` sections AXS-EXT-071 |
| E15.7 Performance contract | — (process) | `--time-passes` (T016) |
| E15.8 Register allocation | machine IR | virtual registers + allocator pass slot AXS-EXT-053 |
| E16.1 Target description as data | target | TargetDesc AXS-EXT-060 |
| E16.2 Linux ELF dynamic | object model, image | `ElfDyn`, `DynLib` AXS-EXT-070; GOT/PLT relocs AXS-EXT-073 |
| E16.3 AArch64 Linux | target, LIR, object model | TargetDesc AXS-EXT-060; `Aapcs64` AXS-EXT-052; AArch64 relocs AXS-EXT-073 |
| E16.4 macOS + Mach-O | object model | `MachO`, `BsdAr` AXS-EXT-070 |
| E16.5 Android AArch64 | target | TargetDesc AXS-EXT-060; `ElfDyn` AXS-EXT-070 |
| E16.6 WASM32 | target, object model | TargetDesc AXS-EXT-060; `Wasm` CallConv/format AXS-EXT-052/070 |
| E16.7 RISC-V64 | target | TargetDesc AXS-EXT-060; `RiscV` AXS-EXT-052 |
| E16.8 Cross-compilation | driver | target names AXS-EXT-061; `@cfg` AXS-EXT-091 |
| E16.9 Linux x86-64 static | target, object model | `SysV64` AXS-EXT-052; `Elf`, `GnuAr`, `ElfExec` AXS-EXT-070; ELF relocs AXS-EXT-073 |
| E16.10 Artifact kinds & library matrix | object model, driver | artifact dimensions AXS-EXT-070 |
| E16.11 Universal artifacts | driver | `Universal` artifact AXS-EXT-070 |
| E16.12 Windows on ARM64 | target | TargetDesc AXS-EXT-060; `Aapcs64` AXS-EXT-052 |
| E17.1 Debug IR + CodeView/PDB | MIR, LIR, object model | `var_debug_info` AXS-EXT-040; span table AXS-EXT-054; `Debug` sections AXS-EXT-071; `SecRel` AXS-EXT-073 |
| E17.2 DWARF | object model | as E17.1 |
| E17.3 Unwinding & backtraces | frame, object model | `FrameLayout` AXS-EXT-054; `PData`/`XData` AXS-EXT-071 |
| E17.4 Debugger contract | symbols | symbol model AXS-EXT-072; mangling scheme (T054b) |
| E17.5 Profiler | — (tooling) | pass slots AXS-EXT-045 for instrumentation |
| E17.6 Sanitizers | MIR passes, oracle | pass slots AXS-EXT-045; oracle UB detection (SPEC-03 AXS-SEM-092) |
| E17.7 Trace & replay | — (std) | host boundary AXS-EXT-110 |
| E18.1 Query engine | driver | session and stable keys AXS-EXT-005/090 |
| E18.2 Incremental compilation | driver | determinism AXS-EXT-006; `fingerprints` AXS-EXT-090 |
| E18.3 Parallel compilation | driver | no globals AXS-EXT-005; `jobs` AXS-EXT-090 |
| E18.4 Artifact format & interfaces | object model | `Custom` sections AXS-EXT-071 |
| E18.5 Pass contracts | MIR passes | verifier between passes AXS-EXT-045 |
| E18.6 Separate compilation | linker, symbols | object list AXS-EXT-074; `Weak`, `comdat` AXS-EXT-071/072; archives AXS-EXT-070 |
| E18.7 Windows .lib/.dll | object model, linker | `StaticLib`/`DynLib`/`CoffAr`/`Pe32PlusDll` AXS-EXT-070; `export` AXS-EXT-072; `BaseReloc` AXS-EXT-071; init list AXS-EXT-074 |
| E19.1 LSP | diagnostics | severities AXS-EXT-080; spans + source DB |
| E19.2 Formatter | — (spans, full source text) | spans on every AST node (SPEC-02 AXS-GRM-002) |
| E19.3 Refactoring | HIR | stable `ItemId` AXS-EXT-030 |
| E19.4 Diagnostics UX 2.0 | diagnostics | `fixits`, `data` AXS-EXT-080 |
| E19.5 Docs & test UX | — (tooling) | none in the core |
| E20.1 Build graph | driver | manifest keys ignored with a warning (ADR-0006 §7); session AXS-EXT-090 |
| E20.2 Package manager | — (tooling) | manifest (ADR-0006 §7) |
| E20.3 Registry | — (tooling) | none in the core |
| E20.4 Hermetic builds | driver | determinism AXS-EXT-006 |
| E20.5 ABI stability | symbols | mangling scheme version (T054b) AXS-EXT-072 |
| E20.6 SDK/sysroot | driver | std root discovery (ADR-0006 §8) |
| E20.7 Axiom dynamic components | object model | `DynLib` AXS-EXT-070; `Custom` metadata sections AXS-EXT-071 |
| E21.1–E21.9 std completion | — (library) | host-interface append AXS-EXT-110; intrinsic append AXS-EXT-100 |
| E22.1 Execution domains | signatures, MIR | `domain` AXS-EXT-022/054; `Kernel` body AXS-EXT-040; `GpuKernel` ABI AXS-EXT-022 |
| E22.2 Device memory | types, LIR | address spaces AXS-EXT-020/051; `PtrAddrSpace` cast AXS-EXT-042 |
| E22.3 GPU codegen | target, object model | TargetDesc AXS-EXT-060; `SpirV` AXS-EXT-070; `GpuKernel` CallConv AXS-EXT-052 |
| E22.4 Host runtime | — (library) | host-interface append AXS-EXT-110 |

## 14. Conformance tests

**AXS-EXT-140 — Required tests.** Each row is a test of the named task (paths under its test dirs):

| Id | Program / check | Expected | Task |
|---|---|---|---|
| EXT-T01 | `fn main() -> i32 { let x = 1.5 ↵ 0 }` | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` at `1.5`, `epic = "E12.2"` | T034 |
| EXT-T02 | `fn f(x: f64) {}` | same code at `f64` | T034 |
| EXT-T03 | `fn f(x: i128) {}` | same code, `epic = "E12.1"` | T017 |
| EXT-T04 | `fn f(d: view<dyn Draw>) {}` (with `trait Draw {}`) | same code at `dyn`, `epic = "E14.4"` | T017 (after T015b) |
| EXT-T05 | `static N: i32 = 1` | same code, `epic = "E13.3"` | T061 |
| EXT-T06 | `@at(0x4000_1000) unsafe static R: u32` | same code, `construct = "@at"`, `epic = "E13.6"` | T015b |
| EXT-T07 | `@export("f") fn f() {}`, `@entry fn main() {}`, `@align(16) struct S {}`, `@cfg(x) fn g() {}` | same code per attribute, epics of AXS-EXT-091 | T015b |
| EXT-T08 | `async fn f() {}`, `comptime fn g() {}` | `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` | T012 |
| EXT-T09 | `axiom0 build --target x86_64-linux x.ax` | `AX_DRIVER_UNKNOWN_TARGET`, exit 2, `epic = "E16.9"` | T016 |
| EXT-T10 | `axiom.toml` with `kind = "dll"` | `AX_DRIVER_UNSUPPORTED_IN_BOOTSTRAP`, `epic = "E18.7"` | T060 |
| EXT-T11 | `const T: [1]fn() = [f]` | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`, `epic = "E14.1"` | T061 |
| EXT-T12 | fuzz corpus contains every construct above | no crash, no ICE | T013 |

Example (EXT-T01, canonical syntax):

```axiom
fn main() -> i32 {
    let x = 1.5    //~ ERROR AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP
    0
}
```

QA also checks, per task that creates a model, that the reserved variants of this spec exist in the
C enum with the `RESERVED` comment (AXS-EXT-003) — a missing reserved variant is a FAIL of that task.

## Sources
0263 §42, §44-46; 0152 §5, §68, §80-81; 0054 §23-47; 0056 §84-122; 0161 §7, §19-20, §29-33, §41;
0162 §5-12, §19-21, §30-34; 0163 §1-7; tasks/0260 §3-4; tasks/0494 §62; tasks/0533; ROADMAP R6-R8 and
§3 (E11–E22); REQ-OWNER-003, REQ-OWNER-005, REQ-OWNER-006 (`spec/requirements/OWNER.md`); ADR-0001,
ADR-0002, ADR-0003, ADR-0004, ADR-0005 §2/§7/§14, ADR-0006, ADR-0011 §3, ADR-0013;
spec/diagnostics.md AXD-013/014/022/032/040/042; SPEC-02 AXS-GRM-003/024/037/038, §12; SPEC-03.
