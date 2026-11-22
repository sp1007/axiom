# ADR-0048 — axiomc loads std modules on demand and adds host provider modules (ADR-0002 §3)

Status: accepted (2026-11-22, architect; owner-delegated decision). Type B (architecture clarification).

## Tóm tắt
- Thẩm định follow-up (triage-1122) xác nhận: `axiomc` chỉ nạp vài file std cố định (prelude, option/result,
  `core/host.ax`, các module `future`, `sync.atomic` khi cần). `use std.core.mem.swap`, `use std.core.cmp.min`,
  `use std.process.exit` báo `AX_NAME_UNRESOLVED_IMPORT`; test phải chép nguyên module std vào file test.
- Bản native gọi `std.core.host.X` thành `__ax_host_X`, nhưng compiler không thêm module cung cấp
  (`std/sys/windows/*.ax`) như ADR-0002 §3 yêu cầu, nên `exit`, `args_count`… báo `AX_LINK_UNDEFINED_SYMBOL`.
- Quyết định: driver dựng chỉ mục module std bằng cách đọc dòng `module …` của mọi file `.ax` dưới std root
  (tiêu đề module là chuẩn, không phải đường dẫn file — `std/async/*.ax` là `std.asyn.*`, `std/io/io.ax` là `std.io`);
  một `use std.a.b[.item]` nạp module dài nhất khớp, rồi nạp bắc cầu các `use std.…` của nó. Module đã có trong
  chương trình (file người dùng, bundle khai báo `module std.x`) luôn thắng, không nạp lại.
- Khi sinh mã native, mỗi intrinsic `host.X` được dùng kéo theo module `std.sys.windows.*` định nghĩa `__ax_host_X`
  (tra theo chỉ mục định nghĩa, không bảng cứng); interp không cần module này.
- Task: T423h (frontend, Opus). Revisit: không.

## Context
- ADR-0002 §3: "The compiler adds the std host module to every program that uses a host intrinsic (std root, T060)."
  axiom0 did; the axiomc port (`compiler/driver/pipeline.ax`) only special-cases `core/host.ax`, the `future`
  lang-item modules and `std.sync.atomic` (`pipe_append_std_extra_mod_if_needed`).
- ADR-0006 §7-8: package files map `a/b.ax` → module `a.b`; std root discovery. Nothing specified how a `use std.…` of a
  non-prelude std module finds its file. 19 of 85 std files do not follow `x/y.ax` ↔ `std.x.y`
  (`x/x.ax` → `std.x`, `async/` → `std.asyn`).
- Repro (triage-1122, cached stage-2 compiler of 2026-11-22): `use std.core.host.exit; exit(3)` runs in the interp (exit 3);
  `build` fails `AX_LINK_UNDEFINED_SYMBOL: __ax_host_exit`; same for `args_count`. `tests/run/host/io/exit7.ax` works only
  because it defines its own `__ax_host_exit`. (`_workspaces/reports/T423b-qa.md` follow-up 3.)

## Options
1. Path mapping only (`std.a.b` → `<root>/a/b.ax` or `<root>/a/b/mod.ax`): cheap, but needs renaming 19 std files
   (and every bundle generator that embeds them) or a list of exceptions.
2. Header index: read the `module` line of every `<root>/**/*.ax` once per compilation (85 small reads) and map module path
   → file. Exact for every existing file, no renames, deterministic.
3. Keep bundling std into tests and programs; only fix host providers with a hard-coded intrinsic → file table.

## Decision
Option 2, plus provider inclusion:
1. **Index.** When a compilation needs a std module that is not already present, the driver scans the std root (sorted
   directory walk, `/` separators) and records `module <path>` → file for every `.ax` file. Two files declaring the same
   module path is `AX_DRIVER_*` error (reuse an existing driver code if one fits; otherwise add one in the task).
2. **Resolution.** `use std.a.b.c` loads the longest module path that is a prefix of the use path (`std.a.b` if `c` is an
   item). Loaded modules' own `use std.…` are resolved transitively. A module path already provided by the program (a user
   file or a bundle that declares `module std.x`) wins and is never loaded from the std root.
3. **Host providers.** For a native build, every used `std.core.host.X` intrinsic adds the std module that defines
   `pub fn __ax_host_X` (found through the same index: the provider set is the modules under `std.sys.<target>`). A program
   that already defines `__ax_host_X` itself (current workaround tests) keeps working only if it is a module named
   `std.sys.windows.*`; the workaround definitions in root modules are removed by T423h. The interpreter never loads providers.
4. **Determinism and caching.** `--dep-file` lists every loaded std file and the scanned std directories as `<dir>/ dir`
   entries (ADR-0041 §4), so adding a std file invalidates cached results.

Option 1 renames files that dozens of selfhost bundle generators embed; option 3 leaves std unusable from user programs.

## Consequences
- T423h (axiom-frontend, opus): driver index + loader + host providers, tests under `tests/modules/std_on_demand` and
  `tests/run/host`; workaround `__ax_host_*` definitions in `tests/run/host/**` removed.
- Tests may now `use std.core.mem.swap` etc. directly; bundling stays valid (rule 2).
- No change to SPEC-02 syntax; ADR-0002 §3 is now implemented as written.

## Sources
ADR-0002 §3, ADR-0006 §7-8, ADR-0041 §4, `_workspaces/reports/T423b-qa.md`, `_workspaces/reports/triage-1122.md`.
