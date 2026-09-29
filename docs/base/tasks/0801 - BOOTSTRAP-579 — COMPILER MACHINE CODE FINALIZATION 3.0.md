# BOOTSTRAP-579 — COMPILER MACHINE CODE FINALIZATION 3.0
## PROLOGUE/EPILOGUE, STACK FRAME FINALIZATION, FRAME POINTER ELIMINATION, STACK PROBING, STACK CLASH PROTECTION, TAIL CALLS, UNWIND CFI, TLS, SECURITY INSTRUMENTATION & FINAL MACHINE IR VERIFICATION

**Trạng thái: COMPLETED / LOCKED**

`579` là bước chốt **Machine IR trước Machine Code Encoding**. Sau task này, backend phải có một representation hoàn chỉnh về:

- physical registers;
- stack frame;
- spill slots;
- callee-saved registers;
- prologue/epilogue;
- dynamic stack;
- tail calls;
- panic/unwind;
- TLS;
- stack protection;
- security instrumentation;
- debug/unwind state.

---

# 579.1. Vị trí

```text id="b9n6t1"
Optimized Machine IR
        ↓
Register Allocation 577
        ↓
Instruction Scheduling 578
        ↓
Frame Analysis
        ↓
Stack Frame Finalization
        ↓
Prologue / Epilogue
        ↓
Security Instrumentation
        ↓
CFI / Unwind Generation
        ↓
Final Machine IR
        ↓
Machine Verification
        ↓
Encoder
```

---

# 579.2. Frame model

Mỗi function có canonical:

```text id="w3r8p2"
FrameLayout {
    size
    alignment
    locals
    spills
    outgoing_args
    callee_saved
    dynamic_area
}
```

---

# 579.3. Frame identity

Frame layout được xác định bởi:

```text id="v6m1k4"
MachineIR
ABI
target
calling convention
register allocation
stack policy
security policy
```

---

# 579.4. Stack alignment

Frame phải satisfy ABI-required alignment tại mọi call site.

---

# 579.5. Local stack slots

Local variables có thể được đặt vào stack frame khi register allocation/lowering yêu cầu.

---

# 579.6. Spill slots

Spill slots từ `577` được layout thành vùng stack hợp lệ.

---

# 579.7. Spill reuse

Non-overlapping spills có thể share slot.

---

# 579.8. Stack-slot coloring

Frame allocator phải minimize frame size thông qua lifetime-aware slot reuse.

---

# 579.9. Slot alignment

Mỗi slot giữ alignment của object hoặc ABI-required alignment.

---

# 579.10. Padding

Padding được chèn deterministic.

---

# 579.11. Frame size

Frame size phải được round theo required alignment.

---

# 579.12. Outgoing argument area

ABI có yêu cầu caller-allocated argument area phải được model trong frame.

---

# 579.13. Call frame optimization

Nếu target/ABI cho phép, outgoing argument area có thể reuse.

---

# 579.14. Dynamic stack

Dynamic stack allocation được biểu diễn explicit trong Machine IR.

---

# 579.15. Dynamic frame boundary

Dynamic allocation không được làm mất khả năng unwind/debug.

---

# 579.16. Stack pointer invariant

SP phải có trạng thái xác định tại các ABI-sensitive points.

---

# 579.17. Frame pointer

FP có thể được dùng hoặc eliminate tùy:

```text id="8d0m5w"
ABI
debug
unwind
dynamic stack
optimization
security
```

---

# 579.18. Frame-pointer elimination

FPE không được áp dụng nếu target/runtime contract yêu cầu frame pointer.

---

# 579.19. Debug frame pointer

Debug profile có thể giữ FP để tăng khả năng debug.

---

# 579.20. Unwind frame pointer

Unwind system phải biết chính xác FP policy.

---

# 579.21. Prologue generation

Prologue tạo:

- stack adjustment;
- callee-save preservation;
- frame setup;
- security setup.

---

# 579.22. Epilogue generation

Epilogue đảo ngược frame state chính xác.

---

# 579.23. Callee-saved registers

Mọi callee-saved register đã sử dụng phải được preserve.

---

# 579.24. Conditional save

Shrink wrapping có thể save register chỉ trên path cần thiết.

---

# 579.25. Conditional restore

Mọi exit path phải restore đúng state.

---

# 579.26. Panic path

Panic/unwind path phải restore state phù hợp với unwind contract.

---

# 579.27. Multiple exits

Các return blocks có thể share epilogue khi profitable.

---

# 579.28. Epilogue merging

Common epilogue có thể được tail-merged.

---

# 579.29. Tail call

Tail call có thể reuse caller frame nếu ABI cho phép.

---

# 579.30. Tail-call eligibility

Phải satisfy:

```text id="s2k7q9"
ABI
argument layout
return convention
stack state
callee/caller compatibility
unwind semantics
```

---

# 579.31. Tail-call elimination

Recursive tail call có thể lower thành loop khi semantics tương đương.

---

# 579.32. Sibling call

Compatible calls có thể trở thành sibling/tail calls.

---

# 579.33. Tail-call safety

Tail call không được phá return address/unwind semantics.

---

# 579.34. Stack probing

Large stack allocation có thể yêu cầu stack probing theo target/OS ABI.

---

# 579.35. Probe threshold

Threshold là target/platform policy.

---

# 579.36. Probe ordering

Probe phải xảy ra trước khi code có thể sử dụng vùng stack chưa committed theo platform rules.

---

# 579.37. Stack clash protection

Compiler có thể chèn guard/probe sequence để tránh bỏ qua guard pages.

---

# 579.38. Security policy

Stack-clash protection là target/security policy, không phải language semantic.

---

# 579.39. Stack canary

Nếu enabled, prologue tạo canary state.

---

# 579.40. Canary placement

Canary phải nằm giữa protected objects và control data theo target security model.

---

# 579.41. Canary check

Epilogue phải kiểm tra canary trước return.

---

# 579.42. Canary failure

Failure đi tới runtime abort/failure handler theo `441`.

---

# 579.43. Buffer-protection policy

Compiler có thể chọn function-level hoặc stronger protection.

---

# 579.44. Shadow stack

Target có hardware/software shadow-stack mechanism có thể được mô hình hóa.

---

# 579.45. Shadow-stack correctness

Call/return transformation không được phá shadow-stack contract.

---

# 579.46. CET-like features

Target-specific control-flow protection phải được biểu diễn trong target description.

---

# 579.47. Branch protection

Indirect branch/call protection có thể được chèn theo target security policy.

---

# 579.48. Return protection

Return sequence phải satisfy target return-protection requirements.

---

# 579.49. Control-flow integrity

Optional CFI instrumentation không được làm thay đổi defined program semantics.

---

# 579.50. Stack limits

Compiler không được assume unlimited stack.

---

# 579.51. Stack overflow behavior

Stack overflow detection/handling thuộc runtime/platform contract.

---

# 579.52. TLS

Thread-local storage accesses được lower theo target ABI.

---

# 579.53. TLS model

Backend hỗ trợ các model phù hợp target:

```text id="f0z4s8"
local-exec
initial-exec
general-dynamic
local-dynamic
```

khi target hỗ trợ.

---

# 579.54. TLS relocation

TLS access có thể tạo relocation/fixup cho linker.

---

# 579.55. TLS register

Target có thread pointer register phải khai báo trong register model.

---

# 579.56. TLS optimization

TLS access có thể được optimize khi linkage/visibility chứng minh model mạnh hơn.

---

# 579.57. TLS semantics

Optimization không được biến TLS thành ordinary global memory.

---

# 579.58. Stack address

Address of stack object là implementation-level address và phải respect `423`.

---

# 579.59. Escape

Stack object escape → compiler không được giả định lifetime kết thúc trước escape.

---

# 579.60. Dynamic lifetime

Dynamic stack object phải sống đúng scope semantics.

---

# 579.61. `defer`

Generated cleanup phải được đặt trong tất cả relevant exits.

---

# 579.62. Cleanup chain

Cleanup state phải có deterministic CFG representation.

---

# 579.63. Cleanup sharing

Common cleanup có thể được merge.

---

# 579.64. Cleanup correctness

Không được bỏ cleanup có observable resource effect.

---

# 579.65. Resource destruction

Drop/release phải preserve ownership semantics `423`.

---

# 579.66. Unwind cleanup

Unwind phải execute required cleanup.

---

# 579.67. Abort mode

Nếu panic policy là abort, unwind structures không cần được emit trừ khi platform yêu cầu.

---

# 579.68. Unwind mode

Nếu unwind enabled, function phải có valid unwind metadata.

---

# 579.69. CFI

Call Frame Information mô tả:

```text id="f7x2n6"
SP
FP
return address
callee-saved registers
```

---

# 579.70. CFI state

CFI phải match từng instruction range mà unwind engine có thể cần.

---

# 579.71. CFI generation

CFI được sinh từ final frame/prologue/epilogue state, không phải đoán từ source.

---

# 579.72. Unwind encoding

Target có thể dùng:

```text id="6r3p0w"
DWARF CFI
Windows unwind
AArch64 unwind
custom runtime
```

---

# 579.73. Platform unwind

Windows và Unix-like targets có thể có unwind formats khác nhau.

---

# 579.74. Multiple unwind formats

Một artifact có thể chứa nhiều unwind representation nếu target/package yêu cầu.

---

# 579.75. Unwind determinism

Unwind metadata phải deterministic.

---

# 579.76. Panic payload

Panic payload không được phụ thuộc vào register allocator internals.

---

# 579.77. Stack trace

Runtime có thể reconstruct stack trace từ unwind metadata.

---

# 579.78. Frame-pointer stack walking

Có thể fallback sang FP-based walking khi policy cho phép.

---

# 579.79. Async frames

Async state-machine frame không được nhầm với native call stack frame.

---

# 579.80. Async unwind

Nếu async runtime cần logical stack tracing, metadata phải distinguish logical/native frames.

---

# 579.81. Interrupt functions

Interrupt entry/exit có dedicated frame policy.

---

# 579.82. Signal handlers

Signal-handler ABI phải có target-specific frame rules.

---

# 579.83. Naked functions

Compiler không tự inject standard prologue/epilogue vào naked functions.

---

# 579.84. FFI entry points

FFI exported functions phải satisfy foreign ABI.

---

# 579.85. FFI callbacks

Callback functions phải có correct incoming register/stack state.

---

# 579.86. Varargs

Varargs frame/register-save area phải follow ABI.

---

# 579.87. Register save area

Target ABI có register-save area phải được frame model support.

---

# 579.88. Dynamic realignment

Stack realignment phải update CFI.

---

# 579.89. Realignment and FP

FP có thể cần giữ khi SP thay đổi động.

---

# 579.90. Stack maps

Nếu runtime cần stack maps, chúng được tạo từ final allocation.

---

# 579.91. Stack map safety

Stack maps không được đánh dấu location sai.

---

# 579.92. No mandatory GC

Axiom không yêu cầu GC stack maps trong core runtime.

---

# 579.93. Optional managed runtime

Managed runtime có thể request explicit stack-map ABI.

---

# 579.94. Security stack metadata

Security instrumentation phải integrate với frame layout.

---

# 579.95. Safe ordering

Security instrumentation phải được chèn tại machine stage mà không phá ABI.

---

# 579.96. Stack initialization

Optional stack initialization có thể được bật cho security-hardening.

---

# 579.97. Uninitialized stack

Compiler không được coi uninitialized stack memory là initialized program value.

---

# 579.98. Stack zeroing

Nếu security policy yêu cầu, compiler có thể zero sensitive stack regions.

---

# 579.99. Sensitive-data lifetime

Zeroing phải occur sau last semantic use nhưng trước lifetime end policy.

---

# 579.100. Zeroing optimization

Security-required zeroing không được DCE như ordinary store.

---

# 579.101. Explicit memory barriers

Security/atomic barriers phải được preserve.

---

# 579.102. Return address

Return address handling phải follow target ABI.

---

# 579.103. Link register

Targets dùng link register như AArch64 phải model LR preservation.

---

# 579.104. LR spill

Nếu LR cần preserve, frame allocator phải reserve storage.

---

# 579.105. Prologue scheduling

Một số prologue instructions có thể schedule nhưng CFI state phải tương ứng.

---

# 579.106. CFI instruction positions

CFI updates phải match actual machine state transition.

---

# 579.107. Epilogue scheduling

Không được move restore instructions qua point nơi unwind semantics thay đổi.

---

# 579.108. Exception edge

Exception edge phải target cleanup/landing pad với valid frame state.

---

# 579.109. Landing pad registers

Landing pad incoming register state phải được ABI/runtime contract xác định.

---

# 579.110. Call-site metadata

Call-site unwind metadata phải map đúng machine instruction ranges.

---

# 579.111. Debug line mapping

Final machine instructions giữ source mapping nếu available.

---

# 579.112. Prologue debug

Prologue instructions có thể mang synthetic source locations.

---

# 579.113. Epilogue debug

Epilogue cũng phải có valid debug mapping.

---

# 579.114. Machine location tracking

Compiler phải biết mỗi debug value đang ở:

```text id="x7b3n1v"
register
stack
constant
unavailable
```

---

# 579.115. Location validity

Location không được trỏ tới register/slot không tồn tại.

---

# 579.116. Frame layout API

```text id="2q7v8c"
compute_frame(function, target, abi, policy)
    → FrameLayout
```

---

# 579.117. Prologue API

```text id="s4k1d9"
emit_prologue(FrameLayout)
```

---

# 579.118. Epilogue API

```text id="q8m2w5"
emit_epilogue(FrameLayout)
```

---

# 579.119. CFI API

```text id="j6n4x0"
emit_unwind(function, FrameLayout)
```

---

# 579.120. Finalization transaction

```text id="p8c1v5"
MachineIR
 ↓
Frame candidate
 ↓
Prologue/Epilogue candidate
 ↓
Security candidate
 ↓
CFI candidate
 ↓
Verification
 ↓
Commit
```

---

# 579.121. Verification failure

Candidate bị rollback hoàn toàn.

---

# 579.122. Frame verifier

Kiểm tra:

```text id="g5h2z8"
frame size
alignment
offsets
overlap
```

---

# 579.123. Register verifier

Mọi physical register usage phải hợp lệ.

---

# 579.124. ABI verifier

Call/return state phải satisfy ABI.

---

# 579.125. CFI verifier

CFI state phải correspond actual frame state.

---

# 579.126. Stack verifier

Không có illegal stack access.

---

# 579.127. Unwind verifier

Mọi unwind path phải có valid recovery state.

---

# 579.128. Security verifier

Security-required instrumentation không được bị loại bỏ.

---

# 579.129. Tail-call verifier

Tail calls phải satisfy complete ABI/frame contract.

---

# 579.130. TLS verifier

TLS access phải dùng legal target model.

---

# 579.131. Relocation interface

Finalization không resolve relocation bytes; chỉ tạo relocation-ready machine instructions.

---

# 579.132. Encoder boundary

Sau finalization, encoder có thể giả định Machine IR đã legal.

---

# 579.133. No virtual registers

Final Machine IR không được còn virtual register.

---

# 579.134. No unresolved stack slot

Mọi stack reference phải resolve thành frame location.

---

# 579.135. No unresolved ABI constraint

ABI-sensitive constraints phải được resolved.

---

# 579.136. No unresolved security policy

Required security transformations phải complete.

---

# 579.137. No unresolved unwind state

Nếu unwind enabled, final metadata state phải complete.

---

# 579.138. Machine instruction legality

Mỗi instruction phải legal đối với target feature set.

---

# 579.139. Operand legality

Register classes, immediate ranges, addressing modes phải legal.

---

# 579.140. Addressing-mode finalization

Spill/frame references được fold vào target addressing modes nếu profitable.

---

# 579.141. Large offsets

Nếu frame offset vượt immediate range, compiler phải materialize address/register sequence.

---

# 579.142. Large-frame handling

Large frames không được tạo illegal stack instructions.

---

# 579.143. Stack probe interaction

Large frame allocation phải integrate stack probing.

---

# 579.144. Stack guard interaction

Guard/probe sequence phải preserve frame setup semantics.

---

# 579.145. Stack-clash verifier

Probe coverage phải satisfy target security policy.

---

# 579.146. Canary verifier

Canary load/store/check phải đầy đủ nếu enabled.

---

# 579.147. Shadow-stack verifier

Nếu enabled, call/return sequence phải satisfy target contract.

---

# 579.148. CFI policy

CFI có thể được bật/tắt bởi target security profile.

---

# 579.149. Security profiles

Ví dụ:

```text id="0h5q8n"
default
hardened
maximum
```

---

# 579.150. Security profile identity

Security profile trở thành build artifact identity.

---

# 579.151. Reproducibility

Cùng input/config/security policy phải tạo cùng final Machine IR.

---

# 579.152. Incremental compilation

Finalization cache chỉ reuse nếu exact Machine IR/frame/security identity khớp.

---

# 579.153. Distributed compilation

Remote worker finalization phải deterministic và verify locally/centrally.

---

# 579.154. Remote trust

Final Machine IR remote phải qua verification trước artifact acceptance.

---

# 579.155. Malicious artifact defense

Không trust frame/unwind/security metadata chỉ vì worker tuyên bố đã verify.

---

# 579.156. Final verifier

Local verifier là authority trước encoder.

---

# 579.157. Reference model

Backend có thể có abstract frame model để differential-test finalization.

---

# 579.158. Fuzzing

Random Machine IR + frame configurations phải không produce invalid frame state.

---

# 579.159. ABI corpus

Test phải cover từng supported ABI.

---

# 579.160. Target corpus

Ít nhất:

```text id="f8w4m3"
x86-64
AArch64
WASM
```

---

# 579.161. OS corpus

Native targets phải test platform-specific unwind/security behavior.

---

# 579.162. Large-frame tests

Test frames từ nhỏ tới rất lớn.

---

# 579.163. Dynamic-frame tests

Test dynamic allocation + calls + unwind.

---

# 579.164. Shrink-wrap tests

Test partial callee-save paths.

---

# 579.165. Tail-call tests

Test tail call + unwind + FFI.

---

# 579.166. TLS tests

Test TLS models và relocations.

---

# 579.167. Security tests

Test canary/probing/shadow-stack/CFI policies.

---

# 579.168. Debug tests

Test optimized stack locations và unwind stack traces.

---

# 579.169. Performance tests

Measure:

```text id="w8c2j6"
frame size
instruction count
prologue cost
epilogue cost
unwind size
```

---

# 579.170. Code-size tests

Security instrumentation overhead phải được tracked.

---

# 579.171. Compile-time tests

Frame finalization phải bounded.

---

# 579.172. No quadratic requirement

Frame/slot analysis phải có scalable implementation.

---

# 579.173. Deterministic slot assignment

Tie-breaking bằng stable slot IDs/lifetime IDs.

---

# 579.174. Deterministic callee-save order

Callee-saved registers được save/restore theo canonical target order.

---

# 579.175. Canonical prologue

Equivalent functions phải emit canonical prologue khi cùng policy.

---

# 579.176. Canonical epilogue

Equivalent functions phải emit canonical epilogue.

---

# 579.177. Platform exception

Target-specific canonical form được phép khác giữa targets.

---

# 579.178. Optimization freedom

Backend được phép chọn khác nhau nếu artifact policy không yêu cầu byte-identical output, nhưng semantic equivalence vẫn bắt buộc.

---

# 579.179. Byte reproducibility

Deterministic mode phải tạo byte-identical machine section với cùng compiler/build inputs.

---

# 579.180. Final Machine IR

Sau `579`, Machine IR phải đủ thông tin để encoder hoạt động mà không cần quay lại HIR/MIR.

---

# 579.181. Encoder isolation

Encoder không được tự làm semantic optimization.

---

# 579.182. Linker isolation

Linker không được sửa frame semantics của function ngoài relocation/linkage processing.

---

# 579.183. Runtime boundary

Runtime chỉ nhận đúng ABI contract đã final hóa.

---

# 579.184. No hidden runtime dependency

Stack/frame generation không được tự động yêu cầu runtime trừ khi policy explicitly bật.

---

# 579.185. Freestanding

Freestanding target phải có thể disable runtime-dependent security/unwind components nếu ABI cho phép.

---

# 579.186. Kernel/embedded

Kernel/embedded profiles có thể custom prologue/epilogue policy.

---

# 579.187. User-space default

Native user-space profile sử dụng platform ABI mặc định.

---

# 579.188. Artifact metadata

Final object phải ghi đủ metadata cần cho linker/unwind/debug/security.

---

# 579.189. Final semantic boundary

Sau finalization, mọi transformation tiếp theo chỉ được phép là byte/encoding/layout transformations đã được contract định nghĩa.

---

# 579.190. Machine verifier failure

Verifier failure là compiler-internal error, không được emit executable artifact.

---

# 579.191. Diagnostic

Compiler phải báo:

```text id="9s5m2h"
function
instruction
frame state
expected invariant
actual state
```

khi internal verification thất bại.

---

# 579.192. Regression capture

Mọi finalization verifier failure phải có thể serialize thành reduced Machine IR test case.

---

# 579.193. Optimization trace

Finalization trace phải ghi các quyết định frame/security chính.

---

# 579.194. AI query

AI tooling có thể hỏi:

```text id="n6p0x4"
why frame pointer was retained
why stack probing was inserted
why tail call was rejected
why callee-save register was used
```

---

# 579.195. AI authority boundary

AI chỉ được đọc/explain finalization facts; không được override verifier.

---

# 579.196. Cross-pass invariant

`577 → 578 → 579` phải tạo pipeline:

```text id="v3q8c1"
allocated
→ scheduled
→ framed
→ unwindable
→ security-valid
→ encodable
```

---

# 579.197. No semantic regression

Mọi thay đổi từ scheduling đến finalization phải giữ observable behavior.

---

# 579.198. Final backend gate

Chỉ khi tất cả final verifiers pass mới cho phép:

```text
Machine IR
    ↓
Machine Encoder
```

---

# 579.199. FINAL HARD INVARIANT

> **BOOTSTRAP-579 là cổng cuối trước encoding. Final Machine IR phải hoàn toàn resolved về physical registers, stack locations, ABI state, frame layout, prologue/epilogue, security instrumentation, TLS và unwind/CFI metadata. Không được emit machine code nếu bất kỳ register constraint, stack invariant, ABI rule, cleanup/unwind state hoặc security requirement nào chưa được chứng minh hợp lệ. Encoder và linker không được trở thành nơi sửa chữa semantic/backend errors.**

# 579.200. LOCK

**BOOTSTRAP-579: LOCKED.**

---

# NEXT — BOOTSTRAP-580

## MACHINE CODE ENCODING 4.0
### ISA ENCODER, INSTRUCTION BYTES, PREFIX/REX/EVEX, AArch64 ENCODING, WASM BINARY EMISSION, FIXUPS, RELAXATION, CONSTANT POOLS, LITERAL POOLS & VERIFIED MACHINE BYTE GENERATION

Pipeline sẽ chuyển sang:

```text id="x1f8q3"
Final Machine IR
       │
       ▼
Instruction Encoder
       │
       ├── x86-64
       ├── AArch64
       └── WASM
       │
       ▼
Fixup / Relocation
       │
       ▼
Constant / Literal Pools
       │
       ▼
Branch Relaxation
       │
       ▼
Final Machine Bytes
       │
       ▼
Byte-Level Verification
       │
       ▼
Object Writer / Linker
```

`580` sẽ đặc biệt khóa **cách Axiom tự encode instruction thành bytes mà không dựa vào LLVM/MC/assembler bên ngoài**, nối trực tiếp với nền tảng `420` và target backend `562`.