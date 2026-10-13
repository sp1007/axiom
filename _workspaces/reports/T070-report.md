# T070 Report: Allocator, Box<T>, Vec<T>

## Task Summary
Implemented memory allocator abstractions, `Box<T>`, `Vec<T>`, sorting, binary search, and deduplication for the standard library in Axiom. Added Win32 heap bindings for native execution and verified dual-mode execution (interpreter oracle leak check and native code generation).

## Files changed
- std/alloc/box.ax
- std/alloc/sort.ax
- std/alloc/vec.ax
- std/core/alloc/alloc.ax
- std/core/alloc/layout.ax
- std/sys/windows/heap.ax
- tests/run/host/heap/alloc.ax
- tests/run/host/heap/use_after_free.ax
- tests/std/alloc/qa_box.ax
- tests/std/alloc/qa_heap_ffi.ax
- tests/std/alloc/qa_search_dedup.ax
- tests/std/alloc/qa_sort_interp.ax
- tests/std/alloc/qa_sort_native.ax
- tests/std/alloc/qa_vec.ax
- tests/std/alloc/qa_vec_box.ax

## Key Deliverables & Validation
1. **Allocator Trait & Layout (`std/core/alloc/`)**:
   - `Layout` (`new`, `from_size_align_unchecked`, `for_type<T>`, `array<T>`).
   - `trait Allocator` with `allocate`, `deallocate`, `reallocate`.
   - `GlobalAlloc` default allocator binding to `host.heap_alloc`, `host.heap_realloc`, `host.heap_free`.

2. **Box<T> (`std/alloc/box.ax`)**:
   - `Box<T>` owning pointer with `_glue: DropGlue` elaboration hook.
   - `box_new<T>`, `box_into_raw<T>`, `box_from_raw<T>`.
   - `impl<T> Drop for Box<T>` invoking `drop_in_place<T>(p)` followed by `heap_free`.
   - Validated drop counting and memory reclamation under oracle leak detection and native Win32 heap.

3. **Vec<T> (`std/alloc/vec.ax`)**:
   - Growth policies starting at 4 elements with geometric doubling.
   - Push, pop, clear, reserve, element access.
   - `impl<T> Drop for Vec<T>` elaborating drops on all contained items before deallocating backing store.
   - Validated `Vec<Box<i32>>` nested dropping in both interpreter and native modes (`qa_vec_box.ax`).

4. **Sort, Search, and Dedup (`std/alloc/sort.ax`)**:
   - Deterministic and stable iterative merge sort (`sort_slice_by`) on slices/views.
   - Native 100k-element sort test (`qa_sort_native.ax`) with duplicate keys verifying key ordering and relative stability.
   - Interp 2k-element twin test (`qa_sort_interp.ax`) with duplicate keys verifying identical stability under interpreter oracle.
   - Binary search (`binary_search_by`) returning positive index when found, negative insertion index `-(low + 1)` when missing.
   - Contiguous duplicate removal (`dedup_slice_by`) in-place.

5. **Host Heap & FFI (`std/sys/windows/heap.ax`, `tests/std/alloc/qa_heap_ffi.ax`)**:
   - Win32 kernel32 bindings for `GetProcessHeap`, `HeapAlloc`, `HeapReAlloc`, `HeapFree`.
   - Exported symbols `__ax_host_heap_alloc`, `__ax_host_heap_realloc`, `__ax_host_heap_free`.
   - `grep -rn "native-after: T070" tests` confirmed empty.

STATUS: COMPLETE round=0
