# ADR-0002 — Oracle host interface: how the MIR interpreter runs heap and OS code

## Tóm tắt
Bộ thông dịch MIR (oracle) trước đây không chạy được chương trình nào dùng heap hay gọi hệ điều
hành, vì std lấy bộ nhớ và làm I/O qua FFI (kernel32) mà oracle không gọi được FFI. Hậu quả: toàn bộ
std (P9) và mọi task port compiler (P10) chỉ chạy được ở chế độ native, mất phép đối chứng ba tầng.
Quyết định: thêm một **tập nhỏ intrinsic "host"** (cấp phát/giải phóng heap, ghi/đọc file, tham số
dòng lệnh, biến môi trường, thoát, đồng hồ, liệt kê thư mục…). Oracle cài chúng bằng C trên mô hình bộ
nhớ của nó; bản native gọi các hàm Axiom trong `std/sys/windows` (viết bằng Axiom, dùng FFI tới
kernel32). FFI trực tiếp của người dùng vẫn chỉ chạy native. Không cần cầu FFI trong oracle, không
cần marshalling con trỏ, và axiomc port lại dễ (oracle viết bằng Axiom chỉ việc gọi std).
Task mới: T061c (phụ thuộc T061b, T060). T070 (heap), T074 (io/args/env/exit), T074b (fs/thư
mục/đồng hồ) cài phần native và phụ thuộc T061c. Revisit: không.

Status: **Accepted** (architect, audit 2026-09-30, findings A1-01 / A3-08).
Date: 2026-09-30. Revisit: no.

## Context

- The MIR interpreter is the semantic oracle (0263 §25, tasks/0262 §10, ABOOT-48/76) and every run
  test is executed in interp and native mode (axiom-testing; T029 differential).
- std gets memory from the OS heap and does I/O through kernel32/shell32 via FFI (T065, T070, T074).
- The interpreter memory model for raw pointers is abstract (allocation id, offset) (T061a); it cannot
  hand a real buffer to `WriteFile`, and no task gave it a way to execute an `extern` call.
- Without a fix, T069–T075, T073a and every port task T077–T085 would be native-only, silently
  dropping the oracle exactly where the self-hosted compiler lives.
- ROADMAP R8: "C provides only compiler intrinsics and FFI to the OS" — both options below comply.

## Options

1. **Interp FFI bridge** — `LoadLibraryW/GetProcAddress` plus a call thunk in the interpreter;
   marshal interp allocations to real memory for every pointer argument. Works for any extern fn,
   but: host-dependent behaviour inside the oracle, marshalling of abstract pointers is complex and
   error-prone, and axiomc (T083) must port the bridge (thunks written in Axiom need inline machine
   code or FFI trampolines).
2. **Host-interface intrinsics** — a small fixed set of `@intrinsic` operations that the std platform
   layer calls. The interpreter implements them in C over its own memory model; native code lowers
   each to a call of an ordinary Axiom function in `std/sys/windows` that uses FFI. Direct FFI stays
   native-only.
3. Accept native-only std tests. Rejected: loses the oracle for all real programs.

## Decision

Option 2.

1. **Intrinsic set** (final names/signatures fixed in SPEC-04 by T003a; all integer/pointer
   arguments, no floats, UTF-8 at the boundary):
   `host.heap_alloc(size, align) -> *mut u8`, `host.heap_realloc(p, old, new, align)`,
   `host.heap_free(p, size, align)`, `host.write(handle, p, len) -> isize`,
   `host.read(handle, p, len) -> isize`, `host.open(path_p, path_len, mode) -> handle`,
   `host.close(handle)`, `host.file_size(handle)`, `host.remove(path)`, `host.mkdir(path)`,
   `host.metadata(path, out)`, `host.dir_next(dir_handle, buf) -> len` (+ open/close),
   `host.args_count()`, `host.arg(i, buf) -> len`, `host.env_get(name, buf) -> len`,
   `host.exit(code) -> never`, `host.monotonic_ns() -> u64`, `host.stdio(which) -> handle`.
   Adding an intrinsic later needs an SPEC-04 edit, not an ADR.
2. **Interpreter**: implements each intrinsic in C (`src/interp/host`) using Windows W APIs
   internally; pointer arguments must lie inside a live interp allocation (bounds-checked, like any
   access); heap intrinsics create/free interp allocations; results are deterministic except where
   the OS is observable (time, directory contents — tests sort or ignore them).
3. **Native**: a call to `host.X` lowers to a direct call of the Axiom function `__ax_host_X`
   defined in `std/sys/windows/*.ax` (heap: T070; io/env/args/exit: T074; fs/dir/clock: T074b),
   implemented with `extern "system"` kernel32 calls and T071c UTF-8↔UTF-16 conversion. The
   compiler adds the std host module to every program that uses a host intrinsic (std root, T060).
   No machine-code runtime helpers are written in C.
4. **Direct FFI** (`extern` fns declared by user or std code other than the host module) is
   native-only; such run tests use `// modes: native` with the reason "direct FFI is native-only
   (ADR-0002)". This is the only accepted reason for a native-only std test.
5. **Pointer ↔ integer casts in the interpreter**: each allocation gets a synthetic, stable base
   address (aligned to 16, deterministic per run order) so `ptr as usize` alignment arithmetic
   (arenas, T073a) works; `usize as ptr` succeeds only for an address inside a live allocation,
   otherwise the oracle reports an invalid-pointer error (T061a).
6. **axiomc**: the interpreter port (T083) implements the same intrinsics by calling std directly.

## Consequences

- New task T061c (interp host implementation + intrinsic declarations `std/core/host.ax` +
  lowering to `__ax_host_*` calls); T070 and T074 depend on it (T074b through T074). Its tests live
  in `tests/run/host/{heap,io,fs}` and carry `native-after: T070` (heap), `native-after: T074`
  (stdio, files, args, env, exit) or `native-after: T074b` (remove, mkdir, metadata, directory
  listing, clock) until the matching native implementation exists.
- T070/T074/T074b paths gain `std/sys/windows/...` and their `tests/run/host/...` directory; their
  acceptance runs in both modes.
- T016 gives `axiom0 run [--interp] file.ax -- <args>` so `host.arg` is testable in both modes.
- axiom-testing states the only allowed reason for native-only std tests.
- SPEC-04 (T003a) lists the intrinsic set; the TypeKind/MIR reserve nothing new (intrinsic calls are
  ordinary calls with an intrinsic id).

## Sources
0263 §25, §47; tasks/0262 §10; tasks/0260 ABOOT-48, ABOOT-76; ROADMAP R8; audit
`_workspaces/audit/2026-09-30/A1-selfhost.md` A1-01, `A3-executability.md` A3-08.
