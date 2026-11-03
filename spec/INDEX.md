# Axiom canonical specification index

## Tóm tắt
Bản đồ của bộ spec chuẩn trong `spec/`: có những tài liệu nào (đã viết hay mới lên kế hoạch), mỗi tài
liệu gom những file nào trong `docs/base`, task nào sở hữu, trạng thái (bản nháp / chuẩn / đóng băng),
và ai dùng. Kèm danh sách ADR, các không gian mã (AXS-LEX, AXS-GRM, AXD, INV, mã chẩn đoán AX_…, REQ,
BOOT, epic E…), bảng chủ đề → nguồn chuẩn cho các vùng chưa có spec riêng, và các mâu thuẫn đã biết
trong tài liệu gốc.
Thứ tự ưu tiên khi các nguồn mâu thuẫn: ADR → spec chuẩn → skill axiom-syntax → tài liệu gốc mới hơn
hoặc đã đóng băng. Ba tài liệu nền là INDEX (file này), danh mục bất biến `spec/invariants.md` và
phân loại mã chẩn đoán `spec/diagnostics.md`.

Status: canonical (T002, 2026-10-04). Owner: axiom-architect. Updated by any architect task that has
`spec/INDEX.md` in its `paths:`/`locks:`, and at every phase-gate review.

## 1. Precedence and reading order

1. `spec/decisions/ADR-*.md`: resolved contradictions. They win over everything, including
   spec text written before them.
2. Canonical specs in `spec/` (table §2), with status `canonical` or `draft`. A draft is binding
   for its owner task and advisory for others until it is accepted.
3. `.claude/skills/axiom-syntax/SKILL.md`: binding surface syntax (`=` only, `.` only, `use`).
4. `docs/base/specs`, `docs/base/tasks`, `docs/base/others` (normative corpus). When they disagree,
   prefer the later document or the one marked FROZEN / "Audit & Freeze". `docs/base/discussions` is never normative.
5. Topic lookup in the corpus: skill `axiom-spec-index` (curated list, generated index).

Status values: **planned** (named by a board task, not written yet), **draft** (being written by a
task in `doing/`), **canonical** (accepted through a QA gate; changes need an architect task, and an
ADR when semantics change), **frozen** (v1.0 freeze at E23.2 / T091; nothing is frozen yet).

## 2. Canonical documents

| Document | Status | Owner task | Consolidates (docs/base) | Main consumers |
|---|---|---|---|---|
| `spec/ROADMAP.md` | canonical (binding baseline) | architect | 0152 §80-81, 0263 §51-52, tasks/0260, tasks/0262, all epic sources in its §3 | every planning task, gates |
| `spec/INDEX.md` (this file) | canonical | T002 | 0151 (contradiction audit), the curated list of axiom-spec-index | all agents |
| `spec/invariants.md` | canonical | T002 | 0153 §37, 0171 §40, 0172, tasks/0260 §45, tasks/0262 §42-49, tasks/0360 §51, 0151, 0263 §28/§46-47 | archcheck T006, gatecheck T022, QA, all engineers |
| `spec/diagnostics.md` | canonical | T002 | tasks/0360 (frozen), 0146 Part XXVII, 0153 §37, 0171 §40, 0172 §10-12, tasks/0262 §46 | T009, T016, T005, T006, every task that adds a code |
| `spec/SPEC-00-bootstrap.md` | draft | T003 (milestone ladder, manifests), T003a (exact self-host subset), T111 (coverage edits) | 0263, tasks/0262, tasks/0494, tasks/0260, 0152 | every core task (milestone blocks), gatecheck T022 |
| `spec/SPEC-01-lexical.md` | canonical | T001 | 0152 §12, 0154, 0155, 0173, 0243, 0109, tasks/0323, tasks/0324, tasks/0385, tasks/0476 | T010, T013, lexer port |
| `spec/SPEC-02-grammar.md` | canonical | T001 | tasks/0476 (v1.0 surface, frozen), 0155, 0174, 0243, tasks/0323, tasks/0386, 0109 | T011, T012, T013, T014/T015/T015b, parser port |
| `spec/SPEC-03-core-semantics.md` | draft | T003 | 0032, 0041, 0068, tasks/0327, 0010, 0263 | T017, T021, T030–T044 (types, literals, arithmetic, panics, exit codes) |
| `spec/SPEC-04-core-extensibility.md` | planned | T003a | 0056, 0054, 0161, 0162, 0163, 0263, tasks/0260, ROADMAP R7 | data-model tasks (HIR/types/MIR/LIR/objmodel), host intrinsics (ADR-0002) |
| `spec/selfhost-subset.tsv` | planned | T003a | tasks/0260, tasks/0494, ADR-0004, ADR-0006 | gatecheck T022 (rule d), T076 |
| `spec/SPEC-10-ownership.md` | planned | T045 | 0004, 0005, 0160, 0176, 0019, 0020, 0086, tasks/0394, 0263 | T018, T046, T047, T050 |
| `spec/SPEC-11-capability.md` | planned | T045 | 0177, 0021, 0028, tasks/0395, tasks/0541, tasks/0270 | T048, T048b, T050 |
| `spec/SPEC-12-drop.md` | planned | T045 | 0178, 0030, 0118, tasks/0674 | T049, T054b |
| `spec/SPEC-20-selfhost.md` | canonical | T076 | 0167, 0150, tasks/0260, tasks/0261, tasks/0371, tasks/0473 | T077–T087 |
| `spec/SPEC-21-query-engine-semantic-db.md` | draft | T752 | 0153, 0171, tasks/0384, tasks/0530, tasks/0532, tasks/0533, tasks/0781, tasks/0791 | T753, T754, T755 |
| `spec/SPEC-22-incremental-compilation.md` | draft | T756 | 0142, 0152 §78-79, 0153 §18/§30/§37, tasks/0564, tasks/0778, tasks/0788, tasks/0789, tasks/0792, SPEC-21 | T757, T758, T759 |
| `spec/SPEC-26-windows-artifact-kinds.md` | draft | T772 | SPEC-04, SPEC-56, ADR-0001 §5-6, ADR-0034 §4, OWNER.md REQ-OWNER-006, 0104, 0164, 0185, 0186, 0187, 0217, tasks/0356, tasks/0369, tasks/0562, tasks/0563 | T750, T751, T773 |
| `spec/SPEC-30-concurrency.md` | draft | T400 | 0033, 0040, 0079, 0091, 0105, 0126, 0136, tasks/0298, tasks/0488, tasks/0685, SPEC-10..12, SPEC-70 | T089, T401, T402, T403, T404, E11.2–E11.6 |
| `spec/SPEC-31-atomics.md` | draft | T405 | 0092, 0128, 0161 §30, 0162 §30, 0208, tasks/0328, tasks/0515, SPEC-04, SPEC-30 | T406, T407, T408, T409 |
| `spec/SPEC-32-threads-sync.md` | draft | T410 | 0136, 0203, 0206, 0207, 0209, tasks/0278, tasks/0329, tasks/0621, tasks/0623, tasks/0837, SPEC-04, SPEC-30, SPEC-31 | T090, T411, T412, T413, T414 |
| `spec/SPEC-33-async.md` | draft | T415 | 0093, 0127, 0135, 0159, 0161, 0201, 0202, 0248, tasks/0275, tasks/0297, tasks/0619, SPEC-04, SPEC-30, SPEC-31, SPEC-32 | T088, T416, T417, T418, T419, E11.5–E11.6 |
| `spec/SPEC-34-executors-fibers.md` | draft | T420 | 0202, 0204, 0205, tasks/0277, tasks/0278, tasks/0620, tasks/0621, tasks/0834, tasks/0835, tasks/0836, SPEC-04, SPEC-30, SPEC-31, SPEC-32, SPEC-33 | T421, T422, T423, T424, E11.6 |
| `spec/SPEC-35-async-io.md` | draft | T425 | 0221, tasks/0335, tasks/0438, tasks/0440, tasks/0441, tasks/0461, tasks/0464, SPEC-04, SPEC-30, SPEC-32, SPEC-33, SPEC-34 | T426, T427, T428 |
| `spec/SPEC-40-integers.md` | draft | T450 | 0157, 0175, 0245, tasks/0327 §84.1/§84.3/§84.10-16, tasks/0334, tasks/0341, tasks/0431 §172.1-14, SPEC-01, SPEC-03, SPEC-04, OWNER.md REQ-OWNER-007 | T451, T452, T453, T454, T455, T456, T457 |
| `spec/SPEC-41-floating-point.md` | draft | T456 | 0157, 0162, 0175, 0179, 0181, 0245, tasks/0327, tasks/0331, tasks/0334, tasks/0338, tasks/0345, tasks/0427, tasks/0431, tasks/0469, SPEC-01, SPEC-03, SPEC-04, SPEC-40, OWNER.md REQ-OWNER-007, CATALOG.md REQ-SIMD-108..110/163/186..189 | T457, T458, T459, T460, T461, T462 |
| `spec/SPEC-42-simd.md` | draft | T463 | 0095, tasks/0337, tasks/0341, tasks/0344, tasks/0347, tasks/0403, tasks/0426, tasks/0427, tasks/0472, SPEC-03, SPEC-04, SPEC-40, SPEC-41, CATALOG.md REQ-SIMD-001..008/086..092/096..097/166..168/171/333 | T464, T465, T466, T467, T468, E12.4, E12.5 |
| `spec/SPEC-43-simd-backend.md` | draft | T469 | 0095, 0162, 0179, 0181, tasks/0341, tasks/0344, tasks/0347, tasks/0403, tasks/0407, tasks/0427, tasks/0472, SPEC-04, SPEC-40, SPEC-41, SPEC-42, CATALOG.md REQ-SIMD-019..025/029..039/042..043/046..050 | T470, T471, T472, T473, T474, E12.5, E15.5 |
| `spec/SPEC-44-cpu-features-multiversioning.md` | draft | T475 | 0095, 0163, tasks/0341, tasks/0344, tasks/0347, tasks/0403, tasks/0407, tasks/0453, SPEC-04, SPEC-42, SPEC-43, SPEC-73, SPEC-75, CATALOG.md REQ-SIMD-011..013/051/079/094..095/217..224/243/256..257 | T476, T477, T478, T479, E15.4, E15.5, E15.6 |
| `spec/SPEC-50-unsafe-ub-ffi.md` | draft | T500 | 0044, 0071, 0104, 0138, 0181, tasks/0282, tasks/0339, tasks/0367, tasks/0395, tasks/0413, SPEC-03, SPEC-04, SPEC-10..12, ADR-0001, ADR-0034 §8, ADR-0036, OWNER.md REQ-OWNER-008 | T501, T502, T503, T504, T505, E13.6 T525–T529 |
| `spec/SPEC-51-raw-memory-volatile-mmio-layout.md` | draft | T506 | 0044, 0067, 0071, 0072, 0097, 0104, 0113, 0119, 0128, 0129, 0131, 0132, 0133, 0138, 0161, 0162, 0163, 1066, tasks/0328, tasks/0339, tasks/0367, tasks/0413, tasks/0434, tasks/0445, tasks/0452, tasks/0475, tasks/0486, tasks/0515, SPEC-03, SPEC-04, SPEC-31, SPEC-50, ADR-0001 | T507, T508, T509, T510, E13.6 T525–T529 |
| `spec/SPEC-52-freestanding-runtime-composition.md` | draft | T511 | 0097, 0104, 0111, 0119, 0129, 0131, 0138, 0143, 0163, 0230, tasks/0358, tasks/0359, tasks/0367, tasks/0370, tasks/0413, tasks/0445, tasks/0455, tasks/0465, tasks/0471, SPEC-03, SPEC-04, SPEC-50, SPEC-51 | T512, T513, T514, T515 |
| `spec/SPEC-53-safety-profiles-capability-security.md` | draft | T516 | 0124, 0129, 0177, tasks/0342, tasks/0420, tasks/0449, tasks/0451, tasks/0461, tasks/0462, tasks/0464, tasks/0465, tasks/0466, tasks/0467, tasks/0703, SPEC-03, SPEC-04, SPEC-10..12, SPEC-50..52, SPEC-70 | T517, T518, T519, T520 |
| `spec/SPEC-54-panic-unwinding.md` | draft | T521 | 0107, 0119, 0138, 0188, 0229, tasks/0351, tasks/0413, tasks/0445, tasks/0478, tasks/0517, tasks/0585, tasks/0700, SPEC-03, SPEC-12, SPEC-50, SPEC-52 | T522, T523, T524 |
| `spec/SPEC-55-fixed-address-declarations.md` | draft | T525 | ADR-0001 §1-4/§7, OWNER.md REQ-OWNER-003/008, 0044, 0071, 0072, 0097, tasks/0328, tasks/0339, tasks/0476, SPEC-02, SPEC-04, SPEC-50, SPEC-51, SPEC-52 | T526, T527, T528, T529, E13.7 T530–T533 |
| `spec/SPEC-56-module-relative-bindings.md` | draft | T530 | ADR-0001 §5-6/§7, OWNER.md REQ-OWNER-005/006/008, 0104, 0138, 0187, tasks/0336, tasks/0434, tasks/0444, tasks/0451, SPEC-02, SPEC-04, SPEC-50, SPEC-51, SPEC-55 | T531, T532, T533, E18.7 T751 |
| `spec/SPEC-60-comptime-2-0.md` | draft | T550 | 0102, 0111, 0115, 0120, 0131, 0140, tasks/0340, tasks/0346, tasks/0443, tasks/0453, tasks/0464, tasks/0509, tasks/0514, SPEC-03, SPEC-04, SPEC-53, SPEC-73, SPEC-75 | T551, T552, T553, T554, T555 |
| `spec/SPEC-61-reflection-derive.md` | draft | T556 | 0102, 0140, tasks/0296, tasks/0343, tasks/0433, tasks/0444, tasks/0509, SPEC-03, SPEC-04, SPEC-50, SPEC-51, SPEC-60 | T557, T558, T559, T560 |
| `spec/SPEC-62-generators.md` | draft | T561 | tasks/0512, tasks/0539, SPEC-02, SPEC-03, SPEC-10..12, SPEC-30, SPEC-33, SPEC-54, SPEC-60, SPEC-72 | T562, T563, T564, T565 |
| `spec/SPEC-63-dyn-trait-vtables.md` | draft | T566 | 0212, 0158, 0161, tasks/0389, tasks/0476, tasks/0539, SPEC-02, SPEC-03, SPEC-04, SPEC-10..12, SPEC-30, SPEC-50, SPEC-73 | T058, T567, T568, T569 |
| `spec/SPEC-70-optir-ssa-memoryssa.md` | draft | T600 | 0161 §17/§37, 0162 §40, 0165 §1-16, tasks/0315, tasks/0366, tasks/0398, tasks/0399, tasks/0545, tasks/0546, tasks/0547, tasks/0794-0797, SPEC-03, SPEC-04 §5 | T601, T602, T603, T604 |
| `spec/SPEC-71-alias-escape-promotion.md` | draft | T605 | 0131 §86, 0162 §29, 0165 §15-20, 0226 §1-26, tasks/0366, tasks/0395, tasks/0397, tasks/0429, tasks/0436, tasks/0438, tasks/0480, tasks/0486, tasks/0548, tasks/0615, SPEC-10..12, SPEC-70 | T606, T607, T608 |
| `spec/SPEC-72-loops-scev-bce.md` | draft | T609 | 0113 §94/§122, 0165 §2/§21-30, tasks/0366, tasks/0402, tasks/0416, tasks/0426, tasks/0470, tasks/0549, SPEC-03, SPEC-70, SPEC-71 | T610, T611, T612 |
| `spec/SPEC-73-inlining-specialization-devirt.md` | draft | T613 | 0131 §28-29/§73-76/§86/§88, 0152 §73-75, 0165 §13-16, tasks/0366, tasks/0400, tasks/0401, tasks/0551, SPEC-03, SPEC-04, SPEC-70, SPEC-71 | T064, T614, T615 |
| `spec/SPEC-75-lto-wpo-section-gc-pgo.md` | draft | T620 | tasks/0355, tasks/0366, tasks/0408, tasks/0409, tasks/0410, tasks/0580, tasks/0581, tasks/0594, tasks/0595, tasks/0597, SPEC-03, SPEC-04 §8, SPEC-70..73, SPEC-77 | T621, T622, T623, T624–T626 |
| `spec/SPEC-76-performance-contract.md` | draft | T624 | 0074, tasks/0355, tasks/0366, tasks/0408, tasks/0595, tasks/0706, SPEC-20, SPEC-70..75, SPEC-77 | T625, T626, T315 |
| `spec/SPEC-77-regalloc-machine-opt.md` | draft | T627 | 0162 §36-40, 0182, 0235, 0237, 0252, tasks/0406, tasks/0553, tasks/0557, tasks/0559, SPEC-04 §6-7 | T063, T628, T629 |
| `spec/BOOTSTRAP.md` | canonical | T087 | 0167, tasks/0473, 0150 | trust chain, freeze rule (INV-BOOT-004) |
| `spec/RELEASE-v1.md` | planned | T091 | 0150, 0151, tasks/0602, 0121 | v1.0 release |
| `spec/requirements/OWNER.md` | canonical | owner / architect | owner decisions (REQ-OWNER-*) | everyone; never dropped silently |
| `spec/requirements/raw/C01.md` … `C18.md` | planned | T092 … T109 | the 18 extraction chunks of `docs/base` (`spec/requirements/chunks`) | T110 |
| `spec/requirements/CATALOG.md`, `spec/COVERAGE.md` | planned | T110 (then T111, planning tasks) | `spec/requirements/raw` | `reqcov.py`, every gate |
| `spec/decisions/` | canonical (append-only) | architect tasks; numbers from `taskctl.py adr-next` | — | everyone |

Specs for later epics (P11+) are created by the first task of each epic (ROADMAP §4 step 2) and added
to this table at the next INDEX update.

## 3. Decision register

| ADR | Title | Main effect |
|---|---|---|
| ADR-0001 | Fixed-address declarations (`@at`) | owner requirement; E13.6/E13.7; axiom0 parses `@at` and rejects it with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (spelling per ADR-0011 §3) |
| ADR-0002 | Oracle host interface | interpreter runs heap/OS code through host intrinsics (T061c); direct FFI native-only |
| ADR-0003 | Back-end pipeline robustness | ABI lowering on LIR, machine-IR verifier, stack probes, stack reserve (T025b) |
| ADR-0004 | Self-host subset additions | wrapping/bit intrinsics, constant tables, stored views, HashMap order and hash, generic drop glue, const-eval interface |
| ADR-0005 | Plan structure corrections | `native-after`, per-area diagnostic files and `locks:`, gate rule PASS/BLOCKED, task splits, follow-up ids |
| ADR-0006 | Bootstrap forms, manifest, std root | `impl Drop`, `u32 as char`, `len`, `axiom.toml`, std-root discovery |
| ADR-0007 | Canonical spelling | `=` only, `.` only, `use`, `module` |
| ADR-0008 | Statement termination | newline or `;`, one fixed parser rule, `NL_BEFORE` flag |
| ADR-0009 | Lexical decisions v0.1 | ASCII identifiers (revisit), keywords, literals, operators |
| ADR-0010 | Grammar forms v0.1 | types, precedence, statements, items, patterns |
| ADR-0011 | Diagnostic code taxonomy | named codes, 18 fixed areas, `_UNSUPPORTED_IN_BOOTSTRAP`, severities, ordering, streams, `INV-*` namespace, invariant `since:` |

## 4. Identifier namespaces

| Prefix | Meaning | Defined in |
|---|---|---|
| `AXS-LEX-NNN` | lexical rules | SPEC-01 |
| `AXS-GRM-NNN` | grammar rules | SPEC-02 |
| `AXS-QRY-NNN` | demand-driven `CompilerDB` input/derived tables, `QueryStack` dependency DAG recording, `inspect --emit=query-graph`, active-stack cycle detection & canonical `SemanticKey` rotation, fallback recovery values, snapshot-bound diagnostic replay, and revision invalidation / green-node reuse rules | SPEC-21 |
| `AXS-INC-NNN` | four-tier 128-bit fingerprints (`Source`/`Ast`/`Interface`/`Abi`/`Body`/`Codegen`), red-green `try_mark_green` change propagation, private-body firewall, persistent `.axiom-cache` schema, hermetic `EnvironmentDigest`, `< 100 ms` no-op fast path, and clean-vs-incremental equivalence rules | SPEC-22 |
| `AXS-WLIB-NNN` | Windows x64 artifact kinds (`--kind exe\|obj\|lib\|dll`), deterministic COFF `.lib` archives & fixed-point extraction, PE32+ `.dll` emission (`.edata`, synthesized `DllMain`, `.reloc`), companion COFF short-import `.lib`, and `ADR-0034` §4 OI-07b `__imp_<name>` cross-linking rules | SPEC-26 |
| `AXS-CONC-NNN` | concurrency semantics, `Send`/`Share` auto-traits, closure/spawn captures, compile-time data-race verifier & `Happens-Before` memory model rules | SPEC-30 |
| `AXS-ATM-NNN` | atomic types (`Atomic<T>`), memory orderings (`Ordering`), fences, MIR/LIR atomic lowering, x86-64 TSO atomic codegen, oracle memory model & litmus conformance rules | SPEC-31 |
| `AXS-SYNC-NNN` | OS threads (`std.thread`), `@thread_local` TLS & `LocalKey<T>`, reference counting (`Rc`/`Arc`/`Weak`), synchronization primitives (`Mutex`, `RwLock`, `Condvar`, `Once`, `OnceCell`, `Barrier`), and ownership-transferring channels (`std.sync.channel`) | SPEC-32 |
| `AXS-ASY-NNN` | `async fn`, `async { }`, `.await`, `Future<T>`/`Poll<T>`/`Waker`/`Context`, `std.future.block_on`, live-across-await analysis, MIR state-machine lowering, per-state cancellation `Drop` glue & oracle async trace rules | SPEC-33 |
| `AXS-EXEC-NNN` | task control block & wake state machine (`Task`, `TaskHandle`), single-thread `LocalExecutor` (`spawn_local`), multi-thread work-stealing `Executor` (`spawn`), structured concurrency (`TaskGroup`, `CancellationToken`, `Deadline`/`Timeout`, `ResourceGovernor`), async synchronization (`AsyncMutex`, `AsyncRwLock`, `AsyncSemaphore`, async channels), and stackful `Fiber` (`std.fiber`, `host.fiber_*`) rules | SPEC-34 |
| `AXS-AIO-NNN` | unified Proactor/Reactor contract (`Reactor`, Windows IOCP / Linux `io_uring` & `epoll`), completion-safe buffer ownership (`IoBuf`), hierarchical `TimerWheel` (`sleep`, `sleep_until`, `Interval`), `AsyncRead`/`AsyncWrite`, `AsyncFile`, and `std.net` async sockets (`AsyncTcpListener`, `AsyncTcpStream` + `split()`, `AsyncUdpSocket`, `host.aio_*`) rules | SPEC-35 |
| `AXS-INT-NNN` | scalar integer model (`i8..i128`, `u8..u128`, `isize`, `usize`), 128-bit register-pair & Win64 ABI lowering, checked/wrapping/saturating/overflowing arithmetic families, bit & endian conversions, `COERCION`/`CAST`/`TRY_CAST`/`BITCAST` classes, and `REQ-OWNER-007` multi-width integer promotion lattice rules | SPEC-40 |
| `AXS-FLT-NNN` | IEEE-754 floating-point model (`f32`/`f64`), `FloatVar` literal inference, strict IEEE-754 arithmetic & rounding, `NaN`/`-0.0` semantics, saturating `FloatToInt` casts, `REQ-OWNER-007` 12-primitive mixed-type promotion lattice (`join_num` & Patterns A/B/C/D), SSE2/`Xmm` ABI lowering, `std.text.fmt.float`, and pure-Axiom `std.math` rules | SPEC-41 |
| `AXS-SIMD-NNN` | portable SIMD vectors (`Vector<T, N>`), masks (`Mask<N>`), lane operations, reductions, masked memory/gather/scatter safety, and data-oriented `TensorView`/`TensorMutView`/`MatrixView` rules | SPEC-42 |
| `AXS-SBE-NNN` | LIR vector types (`v128`/`v256`/`v512`), register classes (`Vec128`/`Vec256`/`Vec512`/`Mask`), `nontemporal`/prefetch memory ops, vector legalizer splitting/scalarization, Windows x64 vector ABI & `VZEROUPPER` hygiene, x86-64 `0F 38`/`0F 3A` & 2/3-byte `VEX` encoding, SSE2/SSE4.1/AVX2/FMA instruction selection, and `std.arch.x86_64` rules | SPEC-43 |
| `AXS-CPU-NNN` | x86-64 `TargetDesc` feature hierarchy & implication DAG (`--target-feature`), `@target_feature` call-site & inliner legality, `std.arch` runtime `CPUID`/`XGETBV` detection (`is_x86_feature_detected`, `--interp-cpu-features`), and `@multiversion` clone/dispatcher generation rules | SPEC-44 |
| `AXS-UNS-NNN` | unsafe boundary (`unsafe` blocks/`fn`/`trait`/`impl`, `MakeView`/`MakeMutView`), raw-pointer strict provenance, `UB-01..UB-12` taxonomy & `--interp` UB detector, `REQ-OWNER-008` address introspection & fixed-address placement (`fn_addr`, `static_addr`, `address_of`, `@addr`/`@at`), and physical representation / FFI / ABI (`@repr(C)`, `@repr(transparent)`, `@abi(stable)`, `extern "C"`, Win64 struct classification, external C DLL oracle) rules | SPEC-50 |
| `AXS-MEM-NNN` | raw memory access, volatile load/store/copy & hardware barriers (`MFENCE`/`SFENCE`/`LFENCE`), `Volatile<T>`/`Mmio<T>`/`MmioRO<T>`/`MmioWO<T>` register wrappers, untagged `union` types, `MaybeUninit<T>`/`ManuallyDrop<T>`, `bitcast`, `@repr(packed)`/`@align(N)` layout & unaligned access, and `@addr_space(N)` address-space rules | SPEC-51 |
| `AXS-FRE-NNN` | modular runtime composition, compilation profiles (`--profile hosted\|freestanding\|kernel\|system`), `std.core`/`std.alloc`/`std` layering, static initialization, `@entry`/`@panic_handler`/`@global_allocator`/`@naked`/`@section`/`@used`, `extern "interrupt"` calling conventions (`REQ-ABI-102`), `ForeignBox<T, A>`/`DmaBuffer<T>`, and compile-time `RuntimeCapabilityGraph` rules | SPEC-52 |
| `AXS-SEC-NNN` | safety profiles (`--safety-profile safe\|sandbox\|system`), `@forbid_unsafe`/`@allow_unsafe` policy attributes, resource authority capability tokens (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`) vs memory capabilities (`view<T>`/`mut_view<T>`), `sandbox`/`comptime` ambient-authority ban (`REQ-CAP-131`), raw-pointer/integer-address capability non-provenance (`REQ-CAP-010`, `REQ-CAP-123`), untrusted FFI boundaries (`REQ-FFI-117`), `Secret<T>`/`Zeroize` non-elidable zeroization, and `@constant_time` verification (`ct_eq`, `ct_select`) rules | SPEC-53 |
| `AXS-PAN-NNN` | per-profile panic strategy (`--panic abort\|unwind`), `std.panic.catch_unwind` / `resume_unwind`, deterministic reverse-order `Drop` cleanup across unwinding frames, double-panic immediate abort, `@no_panic` static call-graph verification, Windows x64 SEH `.pdata`/`.xdata` unwind metadata, and mandatory `extern "C"` FFI no-unwind abort barrier (`REQ-FFI-004`, `REQ-ABI-096`, `REQ-ABI-105`, `REQ-FFI-125`) rules | SPEC-54 |
| `AXS-ADR-NNN` | fixed-address `@at(<expr>)` and `@addr(<expr>)` overlay vs placement declarations (`REQ-OWNER-003`), ordinary-syntax MMIO `Volatile`/`Mmio`/`MmioRO`/`MmioWO` field access, `REQ-OWNER-008` address introspection (`fn_addr`, `static_addr`, `addr_of`, `address_of`, `address_of_mut`, `fn as usize`) & dynamic `base + offset` placement, alignment/overlap/layout verification, COFF `IMAGE_SYM_ABSOLUTE` / ELF `SHN_ABS` symbols, pinned VMA sections, `--format bin` raw binary output, and oracle simulated address space & scriptable device model rules | SPEC-55 |
| `AXS-MOD-NNN` | module-relative `@at(image("mod") + offset)` and `@at(image_self() + offset)` hosted overlays (`REQ-OWNER-005`), overlay-only restriction (`AX_UNSAFE_AT_FOREIGN_PLACEMENT`), open-world dynamic library optimization barrier (`REQ-ABI-095`, `REQ-FFI-119`), explicit DLL export surface (`REQ-FFI-042`), capability retention (`REQ-CAP-132`), dynamic linking vs hot reload separation (`REQ-ABI-032`, `REQ-ABI-033`), `LoadTimeSlot` indirect dispatch, `GetModuleHandleW`/`__ImageBase` load-time resolution, deterministic `DllMain` `FALSE` / EXE startup panic on missing module, and oracle `ProcessModuleMap` rules | SPEC-56 |
| `AXS-CTM-NNN` | Comptime 2.0 unified execution model (`const`, `comptime`, `runtime`), `comptime fn` / `comptime { ... }` blocks / `comptime` parameters, sandboxed authority (`AX_CTM_CAPABILITY_DENIED`), value lifting & resource no-escape barrier (`AX_CTM_RESOURCE_ESCAPE`), partial evaluation, `if comptime` & closure specialization, dependency-tracked `ComptimeCacheKey` caching, and `const` vs `static` vs `TLS` initialization & `.rdata`/`.data`/`.bss` materialization rules | SPEC-60 |
| `AXS-RFL-NNN` | compile-time reflection data model (`TypeInfo`, `StructInfo`, `EnumInfo`, `FieldInfo`, `VariantInfo`, `TraitInfo`), visibility & layout query contracts (`AX_REFLECT_*`), typed `@derive` expansion, provenance tracking (`GenProvenanceId`, `AX_DERIVE_*`), full semantic/MIR re-verification, and `std.reflect` / `std.derive` rules | SPEC-61 |
| `AXS-GEN-NNN` | synchronous generators (`gen fn`, `yield`), lazy pull-based iterator state machines, `LiveAcrossYield` ownership & capability rules (`AX_GEN_*`), HIR → MIR boundary & structural invariants (`AMIR-20..60`), per-state `Drop` cleanup, and `for-in` / `std.iter` lazy combinator rules | SPEC-62 |
| `AXS-DYN-NNN` | `dyn Trait` object-safety rules (`AX_DYN_NOT_OBJECT_SAFE`), 16-byte two-word fat-pointer representation (`data_ptr`, `vtable_ptr`), unsizing coercions (`view<dyn Trait>`, `mut_view<dyn Trait>`, `Box<dyn Trait>`), `.rdata` vtable layout & Win64 indirect call ABI, and vtable-driven dynamic `Drop` rules | SPEC-63 |
| `AXS-OPT-NNN` | OptIR, SSA/MemorySSA, pass-manager legality & scalar optimization rules | SPEC-70 |
| `AXS-ALIAS-NNN` | capability- & provenance-driven alias analysis and MemorySSA memory optimization rules | SPEC-71 |
| `AXS-ESC-NNN` | escape analysis, storage selection & allocation promotion rules | SPEC-71 |
| `AXS-LOOP-NNN` | CFG natural loop discovery, canonicalization, SCEV, LICM, loop transformations & iterator fusion rules | SPEC-72 |
| `AXS-BCE-NNN` | range analysis (`RangeInfo`) & bounds-check elimination (`BCE`) rules | SPEC-72 |
| `AXS-INL-NNN` | call-graph SCC, copy/move propagation, `SROA`, `RVO`/`NRVO`, function/closure inlining, call-site specialization, devirtualization & tail-call rules | SPEC-73 |
| `AXS-LTO-NNN` | Link-Time Optimization (`LTO`), whole-program closed-world reachability (`WPO`), generic deduplication, section GC (`COMDAT`) & safe Identical Code Folding (`ICF`) rules | SPEC-75 |
| `AXS-PGO-NNN` | Profile-Guided Optimization (`PGO`), `--pgo-gen`/`--pgo-use`, profile provenance/confidence/staleness & profitability-only rules | SPEC-75 |
| `AXS-PERF-NNN` | runtime performance contract, optimization profiles (`-O0`..`-Oz`), 3D binary footprint (`FileSize`/`MappedSize`/`WorkingSet`), `--time-passes`/`--size-report` telemetry, canonical benchmark suite & CI regression budget rules | SPEC-76 |
| `AXS-RA-NNN` | register allocation, liveness, spill/reload & frame integration rules | SPEC-77 |
| `AXS-MCOPT-NNN` | instruction selection, branchless if-conversion, microarchitectural cost & post-RA machine optimization rules | SPEC-77 |
| `AXD-NNN` | diagnostics rules | `spec/diagnostics.md` |
| `INV-<GROUP>-NNN` | architecture/semantic invariants | `spec/invariants.md` |
| `AX_<AREA>_<NAME>` | diagnostic codes (18 areas) | `spec/diagnostics.md` §3, §10–11; registry `bootstrap/axiom0/src/diag/codes/<AREA>.def` |
| `BOOT-NN` | milestone ladder entries | SPEC-00 (T003) |
| `REQ-…` | requirements (`REQ-OWNER-*` owner) | `spec/requirements/` |
| `E<phase>.<n>` | roadmap epics | ROADMAP §3 |
| `ADR-NNNN` | decisions | `spec/decisions/` |
| `Tnnn[a-z]` | board tasks | `_workspaces/tasks/` |
| `R01…`, `E01…`, `L01…`, `EX-nn` | example/conformance case numbers | local to SPEC-01/SPEC-02 |

Specs written later (SPEC-03, -04, -10, -11, -12, -20) declare their rule prefix in their header; the
prefix is added here at the next INDEX update. Prefix ids from the corpus (`AKERNEL-24`, `ABOOT-41`,
`ADIAG-22`, `ACAP-31` …) are cited only as sources, always together with the document number, because
the corpus reuses them (§6).

## 5. Topic → canonical source

| Topic | Canonical text today | Corpus sources (axiom-spec-index) |
|---|---|---|
| Plan, ladder, scope | ROADMAP, SPEC-00 | 0152, 0263, tasks/0260, tasks/0262, tasks/0494 |
| Surface syntax | SPEC-01, SPEC-02, axiom-syntax, ADR-0007..0010 | tasks/0476, 0154, 0155 |
| Kernel: IDs, arenas, interner, source DB, query engine, incremental compilation | invariants §2, §27–28; axiom-c-stage0; SPEC-21 (T752, `CompilerDB` input/derived tables, demand-driven query engine, cycle detection & canonical rotation, snapshot-bound diagnostics, revision invalidation); SPEC-22 (T756, four-tier 128-bit fingerprints, red-green `try_mark_green` change propagation, persistent `.axiom-cache`, `< 100 ms` no-op rebuild, clean-vs-incremental equivalence) | 0142, 0152 §78-79, 0153, 0171, 0172, tasks/0384, tasks/0479, tasks/0530, tasks/0532, tasks/0533, tasks/0564, tasks/0778, tasks/0781, tasks/0788, tasks/0789, tasks/0791, tasks/0792 |
| Diagnostics | `spec/diagnostics.md`; SPEC-21 §4 (snapshot-bound diagnostic replay & cascade suppression) | tasks/0360, tasks/0791, 0146 |
| Resolver, HIR, modules | SPEC-02 §4, axiom-syntax (DottedChain), ADR-0006 §8 (std root) | 0156, 0244, tasks/0387, tasks/0357, tasks/0497 |
| Types, literals, arithmetic, panics | SPEC-03 (draft); SPEC-40 (T450, 128-bit integers, overflow families, bit/endian APIs, `From`/`TryFrom`, `REQ-OWNER-007` integer promotion sub-lattice); SPEC-41 (T456, IEEE-754 `f32`/`f64`, full `REQ-OWNER-007` mixed-type promotion lattice, `std.text.fmt.float`, `std.math`); SPEC-42 (T463, portable SIMD `Vector<T, N>`/`Mask<N>`, lane ops, reductions, masked memory/gather/scatter, `TensorView`/`MatrixView`) | 0095, 0157, 0175, 0245, tasks/0388, tasks/0327, tasks/0331, tasks/0334, tasks/0337, tasks/0338, tasks/0341, tasks/0344, tasks/0345, tasks/0347, tasks/0403, tasks/0426, tasks/0427, tasks/0431, tasks/0469, tasks/0472, 0068 |
| Traits, generics | ADR-0004; task texts T053–T056; SPEC-63 (T566, `dyn Trait` object safety, 16-byte fat-pointer representation, unsizing coercions, `.rdata` vtable layout, and `Box<dyn Trait>` dynamic `Drop`); SPEC-73 (specialization, static vs `dyn` dispatch, devirtualization) | 0158, 0212, tasks/0389, tasks/0401, tasks/0476, tasks/0539, tasks/0551, tasks/0611 |
| Ownership, capability, drop, unsafe & provenance | invariants §8, §14, §16, §18, §19; SPEC-10/11/12 (T045); SPEC-50 (T500, unsafe boundary, raw pointer strict provenance, UB catalog, `MakeView`/`MakeMutView`); SPEC-51 (T506, volatile, `Mmio*<T>`, untagged `union`, `@repr(packed)`/`@align(N)`, `MaybeUninit<T>`, `bitcast`, `@addr_space(N)`); SPEC-53 (T516, `--safety-profile safe\|sandbox\|system`, `@forbid_unsafe`/`@allow_unsafe`, resource authority tokens `FsCap`/`NetCap`/`EnvCap`/`ProcessCap`/`ClockCap`, `sandbox`/`comptime` ambient-authority ban, `Secret<T>` zeroization & `@constant_time` verification); SPEC-54 (T521, `--panic abort\|unwind`, `catch_unwind`, reverse-order `Drop` unwinding, double-panic abort, `@no_panic` verification & `extern "C"` FFI no-unwind barrier) | 0044, 0067, 0071, 0072, 0104, 0107, 0124, 0160, 0176, 0177, 0178, 0188, 0229, tasks/0282, tasks/0328, tasks/0339, tasks/0342, tasks/0351, tasks/0394, tasks/0395, tasks/0420, tasks/0449, tasks/0461, tasks/0462, tasks/0464, tasks/0465, tasks/0466, tasks/0467, tasks/0515, tasks/0700, tasks/0703 |
| Concurrency, `Send`/`Share`, race verifier, memory model, atomics, threads, TLS, sync, channels, async (`async`/`await`, `Future`, state machines), executors (`LocalExecutor`, work-stealing `Executor`), structured concurrency (`TaskGroup`, `CancellationToken`, `Deadline`, `ResourceGovernor`), async sync, stackful fibers (`Fiber`), and unified async I/O (`Reactor`, `IoBuf`, `TimerWheel`, `AsyncFile`, `std.net` TCP/UDP sockets) | invariants §11; SPEC-30 (T400); SPEC-31 (T405); SPEC-32 (T410); SPEC-33 (T415); SPEC-34 (T420); SPEC-35 (T425) | 0033, 0040, 0079, 0091, 0092, 0093, 0105, 0126, 0127, 0128, 0135, 0136, 0159, 0161 §30, 0162 §30, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0209, 0221, 0248, tasks/0275, tasks/0277, tasks/0278, tasks/0297, tasks/0298, tasks/0328, tasks/0329, tasks/0335, tasks/0438, tasks/0440, tasks/0441, tasks/0461, tasks/0464, tasks/0488, tasks/0515, tasks/0619, tasks/0620, tasks/0621, tasks/0623, tasks/0685, tasks/0834, tasks/0835, tasks/0836, tasks/0837 |
| MIR, verifier, oracle, OptIR | invariants §6–7; ADR-0002; SPEC-10..12 MIR requirements; SPEC-50 (`--interp` UB detector `UB-01..UB-12`); SPEC-70 (OptIR, SSA/MemorySSA, pass contracts, scalar opt); SPEC-71 (AliasInfo, EscapeInfo, allocation promotion); SPEC-72 (loops, SCEV, BCE, LICM, iterator fusion); SPEC-73 (CallGraph/SCC, copy/move prop, SROA, RVO/NRVO, inlining, specialization, devirt, TCO); SPEC-75 (LTO, WPO, PGO); SPEC-76 (optimization profiles `-O0`..`-Oz`, performance contract) | 0074, 0161, 0165, 0226, 0227, 0247, 0027, 0025, 0031, 0145, tasks/0355, tasks/0366, tasks/0395, tasks/0397, tasks/0398, tasks/0399, tasks/0400, tasks/0401, tasks/0402, tasks/0408, tasks/0409, tasks/0545–0549, tasks/0551, tasks/0580, tasks/0581, tasks/0594, tasks/0597, tasks/0706, tasks/0794–0797 |
| LIR, ABI, FFI, x86-64, COFF, PE | ADR-0003; skill axiom-x64-backend; SPEC-04 (object model, artifact kinds); SPEC-26 (T772, `--kind exe\|obj\|lib\|dll`, COFF `.lib` archives, PE32+ `.dll` `.edata`/`DllMain`/`.reloc`, short-import `.lib`, `__imp_<name>` cross-linking); SPEC-43 (T469, LIR vector types & legalizer, Win64 vector ABI, `0F 38`/`0F 3A`/`VEX` encoding, SSE2/SSE4.1/AVX2/FMA isel, `std.arch.x86_64`); SPEC-44 (T475, `TargetDesc` x86-64 feature DAG, `@target_feature` legality, `std.arch` `CPUID`/`XGETBV` detection, `@multiversion` dispatcher); SPEC-50 (T500, `@repr(C)`, `@repr(transparent)`, `@abi(stable)`, `extern "C"` FFI, Win64 1..24-byte struct classification, external C DLL oracle); SPEC-52 (T511, `--profile freestanding\|kernel\|system`, `@entry`, `@naked`, `@section`, `@used`, `extern "interrupt"` `IRETQ`, CRT-free PE emission, `RuntimeCapabilityGraph`); SPEC-75 (section GC, COMDAT, safe ICF, binary layout); SPEC-76 (3D binary footprint `FileSize`/`MappedSize`/`WorkingSet`, startup layout, `--size-report`); SPEC-77 (RA, isel, machine opt) | 0095, 0097, 0104, 0138, 0143, 0162, 0163, 0164, 0179, 0181, 0182, 0184–0187, 0217, 0235, 0237, 0252, tasks/0355, tasks/0356, tasks/0358, tasks/0359, tasks/0367, tasks/0369, tasks/0370, tasks/0403, tasks/0406, tasks/0407, tasks/0410, tasks/0413, tasks/0453, tasks/0455, tasks/0471, tasks/0553, tasks/0557, tasks/0559, tasks/0562, tasks/0563, tasks/0594, tasks/0595, tasks/0706 |
| Tests and conformance | skill axiom-testing; ADR-0005 §1/§3; SPEC-76 (`tools/bench`, `tools/perf.py`, `--time-passes`, CI budgets) | 0074, 0166, 0017, 0022, 0026, 0114, tasks/0706 |
| Self-hosting | SPEC-20 (T076), BOOTSTRAP.md (T087) | 0167, 0150, tasks/0259–0262, tasks/0371 |
| Fixed addresses, module-relative bindings | ADR-0001, OWNER.md, SPEC-50 (T500, `REQ-OWNER-008` `fn_addr`/`static_addr`/`address_of`, `@addr`/`@at`), SPEC-51 (T506, `Volatile<T>`/`Mmio<T>`/`MmioRO<T>`/`MmioWO<T>` field lowering), SPEC-55 (T525, `@at`/`@addr` overlay vs placement, `REQ-OWNER-003`/`REQ-OWNER-008`, `FixedStatic`, overlap/alignment checks, `IMAGE_SYM_ABSOLUTE`, pinned VMA sections, `--format bin`, oracle device model), SPEC-56 (T530, `@at(image("mod") + off)` & `image_self()` overlays, `REQ-OWNER-005`, `LoadTimeSlot` indirect dispatch, `GetModuleHandleW`/`__ImageBase` `DllMain` init, oracle `ProcessModuleMap`) | 0071, 0044, 0097, 0104, 0187, tasks/0328, tasks/0336, tasks/0339 |
| Comptime 2.0, partial evaluation, specialization, `const` vs `static` vs `TLS`, compile-time reflection, typed `@derive`, and synchronous generators (`gen fn`, `yield`) | SPEC-60 (T550, `comptime fn`, `comptime { ... }`, `comptime` parameters, sandboxed capabilities, value lifting & `AX_CTM_RESOURCE_ESCAPE`, `if comptime` specialization, `ComptimeCacheKey`, `const` vs `static` vs `TLS` initialization & `.rdata`/`.data`/`.bss` emission); SPEC-61 (T556, compile-time `TypeInfo` reflection intrinsics, visibility & `@repr` layout query contracts, typed `@derive` & codegen boundary with `GenProvenanceId`, `std.reflect` & `std.derive`); SPEC-62 (T561, `gen fn`, `yield`, lazy pull-based iterator state machines, `LiveAcrossYield` ownership/capability rules, HIR → MIR structural & cleanup invariants, per-state `Drop`, `for-in` & lazy `std.iter` combinators) | 0102, 0111, 0115, 0120, 0131, 0140, tasks/0296, tasks/0340, tasks/0343, tasks/0346, tasks/0433, tasks/0444, tasks/0509, tasks/0512, tasks/0514, tasks/0539 |

## 6. Known inconsistencies in the corpus (already resolved)

| Issue | Sources | Resolution |
|---|---|---|
| Diagnostic code shape: `ETYPE_MISMATCH` vs `AX_TYPE_0001` vs `AX_NAME_0001` vs `AX1401` | tasks/0360 §3, 0146 §4, 0172 §10, tasks/0262 §46 | ADR-0011 §1: `AX_<AREA>_<NAME>` |
| Diagnostic namespaces differ (0146 §54 has 27, tasks/0360 §38 has 18) | 0146, tasks/0360 | ADR-0011 §2: 18 fixed areas, mapping in diagnostics §3 |
| `AX_ADDR_*` used by ADR-0001, SPEC-02 AXS-GRM-037 and axiom-syntax, but ADDR is not an area | ADR-0001, SPEC-02 | ADR-0011 §3: `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`data.construct = "@at"`), `AX_UNSAFE_AT_HOSTED` |
| Severity sets differ (Error/Warning/Info/Hint vs Error/Warning/Note/Help) | tasks/0360 §2, 0146 §3, 0172 §10 | ADR-0011 §4: four severities in the schema; note/help are attachments |
| `ADIAG-20…` numbers mean different things in 0146, 0153 and tasks/0360 | 0146 §65, 0153 §37, tasks/0360 §51 | ADR-0011 §8: own `INV-*` ids; corpus ids cited with the document number |
| Ladder numbering `BOOT-00…14` (summary list) vs `BOOT-00…37` (section headings) inside tasks/0262 | tasks/0262 §2 vs §3–§43 | SPEC-00 (T003) owns the BOOT map |
| Early docs: bootstrap via LLVM, ELF as the first target; later docs: no LLVM, Windows PE first | 0152 early sections vs 0263, 0172, 0181 | project decision (CLAUDE.md, axiom-spec-index): C11 axiom0, no LLVM, Windows x64 PE first |
| Async/GPU before self-hosting (0152 §80) vs core-first ladder | 0152 §80 vs 0263 §51, tasks/0262 | ROADMAP R2 |

## Sources
0151 (global contradiction audit); 0152; 0263; tasks/0260; tasks/0262; tasks/0360; 0146; 0153; 0171;
0172; skill axiom-spec-index; `spec/ROADMAP.md`; board task files (`paths:` and `spec:` fields of
T001, T002, T003, T003a, T045, T076, T087, T091, T092–T111).
