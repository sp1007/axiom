# ADR-0006 — Bootstrap forms of early features, package manifest, std root discovery, console output

## Tóm tắt
Một số task dùng tính năng mà cơ chế tổng quát của nó chỉ xuất hiện ở task sau (Drop trước khi có
trait, `char.from_u32` trước khi có Option, `len` trước khi có method, `@derive(Copy)` trước khi có
derive, Option/Result trước khi có generic). Nếu để ngỏ, mỗi agent sẽ tự nghĩ ra một cú pháp tạm rồi
phải viết lại test. Quyết định: **luôn dùng cú pháp cuối cùng** và để compiler nhận dạng đúng một hình
dạng cố định cho tới khi cơ chế tổng quát thay thế nó — không phát minh cú pháp tạm. Ngoài ra chốt
luôn hai điều mà T060 đang để ngỏ: file manifest của package tên là `axiom.toml` (theo spec 0168), và
cách compiler tìm thư mục `std/` (`--std-root`, biến môi trường `AXIOM_STD`, rồi thư mục cạnh file
exe); đường dẫn tuyệt đối không bao giờ được ghi vào file kết quả, để stage 2 và stage 3 giống nhau
từng byte dù build ở hai thư mục khác nhau. Revisit: không.

Status: **Accepted** (architect, audit 2026-09-30: A3-07, A2-05, A1-14, A3-19, A3-21).
Date: 2026-10-01. Revisit: no.

## Context

- T049 needs a user destructor before traits exist (T053/T055); T034 specified
  `char.from_u32(n) -> Option<char>` before Option (T039) and methods on primitives (T053); T041 needs
  the length of a `Str` before methods; T046 classifies Copy types before derive (T056); T039 has
  Option/Result before generics (T054/T054b); T048b needs sub-range views before the Range type
  (T072). Each task text said "or the spec's equivalent", which invites five ad-hoc inventions.
- T060 said "decide name/format with architect if unclear" for the package manifest, and no task
  said how axiom0 and axiomc find `std/` (the runner uses `--compiler build-<ID>/axiom0.exe`, so a
  path relative to the executable alone does not work).

## Options

A. Temporary spellings (`@lang("drop") fn …`, `char_from_u32(n, out)`), replaced later: tests and
   std code must be rewritten when the general mechanism lands.
B. Final syntax from the first task; the compiler recognises one fixed shape (marked
   `BOOTSTRAP-SHORTCUT`) until the general mechanism subsumes it: no rewrite of tests.
C. Reorder the board so every general mechanism comes first: breaks the ladder order (0263 §51
   BOOT-17..25) and delays the first ownership results.

## Decision

Option B, with these fixed forms.

1. **Destructors (T049).** The surface form is the final one, `impl Drop for S { fn drop(self:
   mut_view<S>) { … } }`. Until traits exist, the compiler recognises exactly this shape — the trait
   name `Drop`, a nominal non-generic type, one method `drop` with that signature — and registers the
   function as the type's destructor; any other `impl` reports the stage diagnostic of T053/T055.
   `drop(x)` is a built-in function that moves its argument and runs its drop. T055 turns `Drop` into
   an ordinary lang-item trait; T054b adds generic `Drop` impls and per-instance drop glue.
2. **`char` from an integer (T034).** `u8 as char` is always valid. `u32 as char` is a **checked
   cast**: it panics (SPEC-03 panic path) when the value is not a Unicode scalar value. No intrinsic
   is needed: validity is the plain expression `n <= 0x10FFFF && !(n >= 0xD800 && n <= 0xDFFF)`.
   `char.from_u32(n) -> Option<char>` is library code in T069.
3. **Built-in helpers before methods.** `len(x)` for arrays, slices and `Str` is a built-in function
   (T036, T041, T048b); std later wraps it as `.len()` methods (T069/T071). `@derive(Copy)` is
   recognised as a built-in marker by T046; T056 makes it one case of the general derive.
4. **Option/Result.** Built-in, non-generic lang items in T039 (`BOOTSTRAP-SHORTCUT`). T054b replaces
   them with real generic enums in `std/core/option.ax` and `std/core/result.ax`, exported by the
   prelude module whose loading mechanism T060 delivers. `if let`/`while let` tests over Option belong
   to T039; T038/T038b test patterns with user-defined enums.
5. **Sub-range views.** `s[a..b]`, `s[a..]`, `s[..b]` on arrays and slices are built-in index forms
   in T048b; the `Range` types and `for` arrive in T072 and do not change these forms.
6. **View receivers.** Method receivers (`self: view<T>` / `mut_view<T>`, automatic ephemeral
   capability at the call) belong to T053, not T048.
7. **Package manifest (T060).** The manifest is `axiom.toml` at the package root (0168 §3). axiom0
   reads only `[package] name`, `version` and `kind` (`exe` in the core); unknown keys are ignored
   with a warning; dependencies, features and workspaces are E20.1/E20.2. A file `a/b.ax` under the
   package `src/` is module `a.b`; a single-file compile needs no manifest.
8. **Std root discovery (T060).** Order: `--std-root <dir>`, then environment `AXIOM_STD`, then
   `<exe dir>/../std`, then `<exe dir>/std`; otherwise `AX_DRIVER_NO_STD`. `tools/axtest.py` always
   passes `--std-root std`. Absolute paths never reach an artifact: object files, images and
   diagnostics in `--json` use paths relative to the package root or the form `<std>/core/…`.

9. **Console output before std.io (T042).** The startup stub calls `SetConsoleOutputCP(65001)` when
   stdout is a console (`GetConsoleMode` succeeds) and restores the previous code page before
   `ExitProcess`; program output always goes through `WriteFile` with the raw UTF-8 bytes. Rejected:
   `WriteConsoleW` with a UTF-8 → UTF-16 loop in generated machine code (throw-away machine code,
   against R7). `std.io` (T074), written in Axiom, uses `WriteConsoleW` with T071c conversion for
   console handles and `WriteFile` for pipes and files; the code-page switch stays only as the
   fallback of the built-in `print` intrinsic.

## Consequences

- Scope/acceptance lines in T003 (cast table), T034, T036, T038, T038b, T039, T041, T042, T046, T048,
  T048b, T049, T053, T054b, T056, T060, T069, T074; T060 keeps `model: sonnet`.
- T087 can build stage 2 and stage 3 in different directories and still compare bytes.
- Every recognised fixed shape carries a `BOOTSTRAP-SHORTCUT` comment naming the task that retires it.

## Sources
0178 §8 (custom Drop form), 0168 §3 (manifest `axiom.toml`), tasks/0327 (numeric model; the corpus
does not define an integer → `char` cast, so item 2 is an architect decision), 0263 §42 §51,
tasks/0260 §3, ROADMAP R7/R8; audit A3-07, A2-05, A1-14, A3-19, A3-21.
