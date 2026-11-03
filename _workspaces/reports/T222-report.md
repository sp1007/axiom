# T222 — Plan phase P22: GPU & heterogeneous computing

## Tóm tắt
Hoàn tất lập kế hoạch giai đoạn **P22 (`P22-gpu-heterogeneous-computing`)** theo `spec/ROADMAP.md` §3–§4 và `.claude/agents/axiom-architect.md`. Đã mở rộng đầy đủ 4 epic của P22 (`E22.1`–`E22.4`) thành **16 task cụ thể** (`T950`–`T965`, mỗi epic 4 task: 1 spec task của `axiom-architect` cho `SPEC-130`..`SPEC-133`, 2 task cài đặt của `axiom-semantics` / `axiom-backend` / `axiom-stdlib`, và 1 task kiểm thử hợp chuẩn của `axiom-qa` với `reviewer: axiom-architect`). Đã nối toàn bộ phụ thuộc của các task P22 với cổng P11 (`T311`), cổng P12 (`T312`), cổng P16 (`T316`) và cổng P22 (`T322`), đồng thời chuyển đổi toàn bộ **63 dòng `EPIC(E22.3)`** (`REQ-GPU-001`..`REQ-GPU-063`) và cập nhật 2 dòng `REQ-GPU-064`..`REQ-GPU-065` trong `spec/requirements/CATALOG.md` sang mã task cụ thể (`T950`–`T965`).

## Summary

Expanded Phase **P22 (`P22-gpu-heterogeneous-computing`)** from the 4 epics in `spec/ROADMAP.md` §3 (`E22.1`–`E22.4`) into **16 concrete tasks** (`T950`–`T965`, 4 tasks per epic, all depending on `T222`, P11 gate `T311`, P12 gate `T312`, and P16 gate `T316`):

1. **E22.1 — Execution domains & kernel model (`T950`–`T953`)**:
   - `T950` (`axiom-architect`): `spec/SPEC-130-execution-domains-kernel-model.md` — `ExecutionDomain` (`Host`, `Device(Gpu | Npu | Dsp | Custom)`), `FnExecCapability` (`HostOnly`, `DeviceOnly`, `HostDevice`, `KernelEntry`), `@kernel`/`@device`/`@host_device` legality rules, transitive call-graph checking (`AGPU-22`, `AGPU-26`), kernel parameter ABI representability (`AGPU-46`), SIMT hierarchy (`global_id`, `local_id`, `group_id`, `local_size`, `global_size`, `num_groups`), workgroup barrier uniformity (`workgroup.barrier()`), and hierarchical `AtomicScope` (`Thread`, `Workgroup`, `Device`, `System` orthogonal to `Ordering`, `AATOM-38`) (`0096`, `0120`, `0128`, `0139`, `tasks/0299`, `tasks/0470`, `tasks/0626`).
   - `T951` (`axiom-semantics`): `@kernel`/`@device` attributes, transitive execution-domain legality & kernel ABI checker (`compiler/hir/gpu_domain`, `compiler/semantics/gpu_legality`, `tests/ui/gpu_legality`).
   - `T952` (`axiom-semantics`): Kernel MIR body, SIMT grid/workgroup intrinsics, scoped atomics & oracle grid executor (`compiler/mir/gpu_kernel`, `compiler/interp/gpu_sim`, `std/gpu/kernel`, `tests/run/gpu_kernel_model`).
   - `T953` (`axiom-qa`): Execution domains, `@kernel` transitive legality, barrier uniformity & oracle SIMT conformance suite (`tests/conformance/p22/e22_1_execution_domains_kernel`).

2. **E22.2 — Device memory & ownership across devices (`T954`–`T957`)**:
   - `T954` (`axiom-architect`): `spec/SPEC-131-device-memory-cross-device-ownership.md` — semantic storage/address spaces (`Host = 0`, `Device = 1`, `Shared = 2`, `Constant = 3`, `Local = 4`, `Private = 5`, `External = 6`), unified CPU/GPU ownership & capability semantics (`AGPU-20`, `AGPU-57..59`), `DeviceBuffer<T>`, `DeviceView<T>`/`DeviceMutView<T>`, `SharedArray<T, N>`, `ConstantBuffer<T>`, `UnifiedBuffer<T>`, explicit host↔device and multi-GPU peer transfers (`AGPU-21`, `ATENSOR-29`, `APAR-63-64`), and in-flight `GpuEvent` resource lifetime retention (`AGPU-23`, `AGPU-33`) (`0120`, `0139`, `0162`, `tasks/0299`, `tasks/0459`, `tasks/0468`, `tasks/0470`, `tasks/0626`).
   - `T955` (`axiom-semantics`): Address-space typing, cross-domain capability isolation & in-flight `GpuEvent` lifetime verifier (`compiler/semantics/gpu_memory`, `compiler/mir/gpu_transfer`, `tests/ui/gpu_memory_ownership`).
   - `T956` (`axiom-stdlib`): `std.gpu.mem`: `DeviceBuffer`, `DeviceView`, `SharedArray`, `UnifiedBuffer`, explicit transfers & Multi-GPU peer domains (`std/gpu/mem`, `std/gpu/transfer`, `std/gpu/event`, `tests/run/gpu_device_memory`).
   - `T957` (`axiom-qa`): Device memory ownership, explicit transfers, address spaces & in-flight lifetime conformance suite (`tests/conformance/p22/e22_2_device_memory_ownership`).

3. **E22.3 — GPU codegen backend (SPIR-V first unless ADR decides otherwise) (`T958`–`T961`)**:
   - `T958` (`axiom-architect`): `spec/SPEC-132-gpu-ir-spirv-codegen-backend.md` — Axiom GPU IR (`AGIR`), `GpuKernelABI` descriptor/push-constant layout (`CallConv.GpuKernel`), proof-preserving `KernelFusion` & transfer elimination (`AGPU-19`, `AGPU-28`, `AGPU-51`), structured CFG (`OpLoopMerge`/`OpSelectionMerge`), SPIR-V 1.6 compute module format (`ObjectFormat.SpirV`), and internal SPIR-V validator (`0096`, `0139`, `0162`, `tasks/0626`).
   - `T959` (`axiom-backend`): `AGIR` lowering, kernel fusion, transfer optimization & structured CFG reconstruction (`compiler/gpu/agir`, `compiler/gpu/opt`, `compiler/gpu/structurize`, `tests/selfhost/gpu_agir`).
   - `T960` (`axiom-backend`): SPIR-V 1.6 binary emitter, descriptor reflection metadata & internal SPIR-V module validator (`compiler/target/spirv`, `compiler/obj/spirv`, `tests/obj/spirv`, `tests/mc/spirv`).
   - `T961` (`axiom-qa`): `AGIR` optimization, kernel fusion & SPIR-V 1.6 binary codegen conformance suite (`tests/conformance/p22/e22_3_spirv_codegen`).

4. **E22.4 — Host runtime (Vulkan/D3D12 compute) (`T962`–`T965`)**:
   - `T962` (`axiom-architect`): `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md` — hardware/GPU device discovery (`std.device`, `DeviceManager`, generational `DeviceId`, `REQ-GPU-064`), Vulkan 1.2/1.3 & Windows D3D12 compute backends, deterministic software compute fallback (`AGPU-23`), command recording / `ComputePipeline` / `RenderGraph` runtime (`std.gpu`, `std.gfx`, `REQ-GPU-065`), and `host.gpu_*` intrinsics (`0096`, `0139`, `tasks/0626`, `tasks/0843`, `tasks/0845`, `tasks/0846`).
   - `T963` (`axiom-stdlib`): Host GPU intrinsics, `DeviceManager` enumeration & Vulkan / D3D12 compute backend drivers (`std/device`, `std/sys/gpu/vulkan`, `std/sys/gpu/d3d12`, `std/sys/gpu/cpu_fallback`, `compiler/interp/host_gpu`, `tests/run/gpu_host_driver`).
   - `T964` (`axiom-stdlib`): High-level `std.gpu` & `std.gfx` command runtime: `ComputePipeline`, `CommandEncoder`, `RenderGraph` & async dispatch (`std/gpu/runtime`, `std/gpu/pipeline`, `std/gfx/command`, `tests/run/gpu_compute_runtime`).
   - `T965` (`axiom-qa`): End-to-end GPU kernel execution (Vulkan/D3D12 compute + oracle differential) conformance suite (`tests/conformance/p22/e22_4_host_runtime_compute`).

## Files changed

- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md
- ./_workspaces/tasks/todo/T222-plan-phase-p22-gpu-heterogeneous-computing.md
- ./_workspaces/tasks/todo/T322-phase-p22-gate-gpu-heterogeneous-computing.md
- ./_workspaces/tasks/todo/T525-e13-6-fixed-address-at-addr-declarations-spec.md
- ./_workspaces/tasks/todo/T550-e14-1-comptime-2-0-partial-eval-const-static-spec.md
- ./_workspaces/tasks/todo/T950-e22-1-execution-domains-kernel-legality-simt-spec.md
- ./_workspaces/tasks/todo/T951-e22-1-kernel-device-attributes-transitive-legality-abi.md
- ./_workspaces/tasks/todo/T952-e22-1-kernel-mir-simt-intrinsics-atomics-oracle-grid.md
- ./_workspaces/tasks/todo/T953-e22-1-execution-domains-kernel-simt-conformance.md
- ./_workspaces/tasks/todo/T954-e22-2-device-memory-ownership-async-lifetime-spec.md
- ./_workspaces/tasks/todo/T955-e22-2-address-space-typing-capability-event-lifetime-verifier.md
- ./_workspaces/tasks/todo/T956-e22-2-std-gpu-mem-device-buffer-view-transfers-events.md
- ./_workspaces/tasks/todo/T957-e22-2-device-memory-ownership-transfer-conformance.md
- ./_workspaces/tasks/todo/T958-e22-3-gpu-ir-agir-kernel-fusion-spirv-backend-spec.md
- ./_workspaces/tasks/todo/T959-e22-3-agir-lowering-kernel-fusion-cfg-structurization.md
- ./_workspaces/tasks/todo/T960-e22-3-spirv-binary-emitter-reflection-validator.md
- ./_workspaces/tasks/todo/T961-e22-3-agir-kernel-fusion-spirv-codegen-conformance.md
- ./_workspaces/tasks/todo/T962-e22-4-host-runtime-vulkan-d3d12-compute-device-spec.md
- ./_workspaces/tasks/todo/T963-e22-4-host-gpu-intrinsics-devicemanager-vulkan-d3d12-drivers.md
- ./_workspaces/tasks/todo/T964-e22-4-std-gpu-gfx-command-runtime-pipeline-rendergraph.md
- ./_workspaces/tasks/todo/T965-e22-4-gpu-kernel-execution-vulkan-d3d12-oracle-conformance.md

## Tests

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P22-gpu-heterogeneous-computing --strict` → `65 rows` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `v1-full implemented=479  planned=8352`, `post-v1 epic=17535  planned=78`, `gaps: 0`, `COVERAGE OK` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T322` and `T950`–`T965` → `OK` (`17 files`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → `OK (587 tasks)`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T222` → `21 stage, 0 REFUSED`

## Spec deviations

None.

## Follow-ups

None.

STATUS: COMPLETE round=0
