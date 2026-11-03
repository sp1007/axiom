# T221 — Plan phase P21: Standard library completion

## Tóm tắt
Hoàn tất lập kế hoạch giai đoạn **P21 (`P21-standard-library-completion`)** theo `spec/ROADMAP.md` §3–§4 và `.claude/agents/axiom-architect.md`. Đã mở rộng đầy đủ 9 epic của P21 (`E21.1`–`E21.9`) thành **36 task cụ thể** (`T900`–`T935`, mỗi epic 4 task: 1 spec task của `axiom-architect` cho `SPEC-120`..`SPEC-128`, 2 task cài đặt của `axiom-stdlib`, và 1 task kiểm thử hợp chuẩn của `axiom-qa` với `reviewer: axiom-architect`), bao gồm hạng mục kế thừa từ `ADR-0034` §8 (audit 2026-10-19 OI-13: kiểm thử tự động xuất chuỗi tiếng Việt `Xin chào thế giới` qua đường dẫn `WriteConsoleW` trên Windows pseudo-console / ConPTY trong `E21.3` — `T908`, `T910`, `T911`). Đã nối toàn bộ phụ thuộc với cổng P11 (`T311`), cổng P13 (`T313`) và cổng P21 (`T321`), đồng thời chuyển đổi toàn bộ **807 dòng `EPIC(E21.1)`** (`REQ-RT-001`..`REQ-RT-809`) và cập nhật 6 dòng `REQ-STD-171`..`REQ-STD-175`, `REQ-STD-177` trong `spec/requirements/CATALOG.md` sang mã task cụ thể (`T900`–`T935`).

## Summary

Expanded Phase **P21 (`P21-standard-library-completion`)** from the 9 epics in `spec/ROADMAP.md` §3 (`E21.1`–`E21.9`) into **36 concrete tasks** (`T900`–`T935`, 4 tasks per epic, all depending on `T221`, P11 gate `T311`, and P13 gate `T313`):

1. **E21.1 — Collections breadth & data-oriented storage (`T900`–`T903`)**:
   - `T900` (`axiom-architect`): `spec/SPEC-120-collections-data-oriented-storage.md` — `VecDeque<T>`, cache-line-tuned `BTreeMap<K, V>` / `BTreeSet<T>`, `BinaryHeap<T>`, `SmallVec<T, N>`, `BitSet`, generational `SlotMap<K, V>` / `DenseSlotMap<K, V>` / `SecondaryMap<K, V>`, and `SoA` multi-column projections (`0210`, `tasks/0348`, `tasks/0349`, `tasks/0608`).
   - `T901` (`axiom-stdlib`): `VecDeque`, `BTreeMap`, `BTreeSet`, `BinaryHeap` & `SmallVec` collections (`std/collections/deque`, `std/collections/btree`, `std/collections/heap`, `std/collections/small_vec`).
   - `T902` (`axiom-stdlib`): Generational `SlotMap`, dense `HandleArena`, `BitSet` & Structure-of-Arrays (`SoA`) storage (`std/collections/slot_map`, `std/collections/soa`, `std/collections/bit_set`).
   - `T903` (`axiom-qa`): Collections breadth, `SoA` layout & generational handle conformance suite (`tests/conformance/p21/e21_1_collections_soa`).

2. **E21.2 — Text & Unicode complete (`T904`–`T907`)**:
   - `T904` (`axiom-architect`): `spec/SPEC-121-text-unicode-complete.md` — `NFC`/`NFD`/`NFKC`/`NFKD` normalization, UAX #29 grapheme/word/sentence segmentation, locale-independent full case mapping/folding, tree-shakeable Unicode tables, and `OsStr`/`CStr` encoding bridges (`0089`, `tasks/0332`, `tasks/0608`).
   - `T905` (`axiom-stdlib`): Compact Unicode property tables, `NFC`/`NFD`/`NFKC`/`NFKD` normalization & full case mapping (`std/text/unicode/tables`, `std/text/unicode/norm`, `std/text/unicode/case_map`).
   - `T906` (`axiom-stdlib`): UAX #29 grapheme/word/sentence segmentation, `OsStr`/`CStr` & zero-copy text cursors (`std/text/unicode/segment`, `std/text/os_str`, `std/text/cursor`).
   - `T907` (`axiom-qa`): Unicode normalization, UAX #29 segmentation & case mapping conformance suite (`tests/conformance/p21/e21_2_text_unicode`).

3. **E21.3 — OS: fs, process, env, signals, IPC (`T908`–`T911`)**:
   - `T908` (`axiom-architect`): `spec/SPEC-122-os-fs-process-signals-ipc.md` — move-only OS handle semantics, positional `read_at`/`write_at`, file locks, atomic writes, `Command`/`ChildProcess` pipelines, safe signal channels, IPC pipes, and Windows `WriteConsoleW`/ConPTY console I/O (`tasks/0335`, `tasks/0443`, `tasks/0840`, `ADR-0034` §8 OI-13).
   - `T909` (`axiom-stdlib`): Complete `std.fs` & `std.path`: positional `read_at`/`write_at`, file locks, symlinks, tempfiles & fs watcher (`std/fs/ext`, `std/fs/watch`, `std/fs/tempfile`).
   - `T910` (`axiom-stdlib`): Process pipelines, signals, anonymous/named IPC & Windows `WriteConsoleW`/ConPTY runtime (`std/process/spawn`, `std/os/signal`, `std/os/ipc`, `std/os/console`).
   - `T911` (`axiom-qa`): OS filesystem, process, signals, IPC & ConPTY `WriteConsoleW` (`Xin chào thế giới`, `ADR-0034` §8 OI-13) conformance suite (`tests/conformance/p21/e21_3_os_fs_process_ipc`).

4. **E21.4 — Networking (`T912`–`T915`)**:
   - `T912` (`axiom-architect`): `spec/SPEC-123-networking-sockets-dns-http.md` — move-only sockets, IPv4/IPv6 addressing, synchronous/async DNS resolution, explicit TLS transport boundary, HTTP/1.1 framing, and typed RPC/service gateway contracts (`tasks/0461`, `tasks/0335`, `tasks/0838`, `tasks/0859`).
   - `T913` (`axiom-stdlib`): Blocking & async TCP/UDP sockets, IPv4/IPv6 addressing, socket options & DNS resolver (`std/net/addr`, `std/net/socket`, `std/net/dns`).
   - `T914` (`axiom-stdlib`): TLS transport boundary, HTTP client/server framing & typed RPC service gateway (`std/net/tls`, `std/net/http`, `std/net/rpc`).
   - `T915` (`axiom-qa`): Networking sockets, DNS, async IO, TLS boundary & HTTP/RPC conformance suite (`tests/conformance/p21/e21_4_networking`).

5. **E21.5 — Time & clocks (`T916`–`T919`)**:
   - `T916` (`axiom-architect`): `spec/SPEC-124-time-clocks-timers.md` — `Duration`, monotonic `Instant`, wall-clock `SystemTime`, checked/saturating temporal arithmetic, hierarchical timer wheels, and deterministic `MockClock` (`tasks/0440`, `tasks/0464`).
   - `T917` (`axiom-stdlib`): `Duration`, `Instant`, `SystemTime`, checked/saturating temporal math & RFC 3339/ISO 8601 civil time (`std/time/instant`, `std/time/system_time`, `std/time/calendar`).
   - `T918` (`axiom-stdlib`): Hierarchical timer wheels, `Deadline`, `Sleep`/`Interval` & deterministic `MockClock` (`std/time/timer_wheel`, `std/time/deadline`, `std/time/mock_clock`).
   - `T919` (`axiom-qa`): Monotonic/wall clocks, temporal arithmetic, timer wheels & `MockClock` conformance suite (`tests/conformance/p21/e21_5_time_clocks`).

6. **E21.6 — Virtual memory & memory mapping (`T920`–`T923`)**:
   - `T920` (`axiom-architect`): `spec/SPEC-125-virtual-memory-mmap.md` — two-phase virtual address reservation vs page commitment, W^X page permissions, guard pages, and capability-bounded `Mmap`/`MmapMut`/`MmapCow` (`tasks/0437`, `tasks/0840`).
   - `T921` (`axiom-stdlib`): `VirtualRegion` reserve/commit/decommit, page protection (`R`/`RW`/`RX`), guard pages & memory locking (`std/vmem/region`, `std/vmem/protect`).
   - `T922` (`axiom-stdlib`): File-backed & anonymous `Mmap`/`MmapMut`, copy-on-write, `flush_sync` & capability-bounded views (`std/vmem/mmap`, `std/vmem/advice`).
   - `T923` (`axiom-qa`): Virtual memory reservation, page protection, guard pages & `Mmap` conformance suite (`tests/conformance/p21/e21_6_vmem_mmap`).

7. **E21.7 — Serialization & binary data model (`T924`–`T927`)**:
   - `T924` (`axiom-architect`): `spec/SPEC-126-serialization-binary-data-model.md` — `Encode`/`Decode` contracts, explicit-endian wire framing, tagged schema evolution, validated zero-copy views, `CRC32C`/`XXH64`, `DEFLATE`/`LZ4` compression, and content-addressed storage (`tasks/0650`, `tasks/0742`, `tasks/0841`, `tasks/0842`, `tasks/0844`).
   - `T925` (`axiom-stdlib`): `Encode`/`Decode` traits, endian-explicit `WireReader`/`WireWriter`, varint & schema evolution codecs (`std/serde/core`, `std/serde/wire`, `std/serde/json`).
   - `T926` (`axiom-stdlib`): Zero-copy validated binary views, `CRC32C`/`XXH64` checksums, `DEFLATE`/`LZ4` compression & `CasStore` (`std/serde/zerocopy`, `std/compress`, `std/cas`).
   - `T927` (`axiom-qa`): Serialization, binary wire model, schema evolution, compression & CAS conformance suite (`tests/conformance/p21/e21_7_serde_binary_data`).

8. **E21.8 — Crypto primitives & secure memory (`T928`–`T931`)**:
   - `T928` (`axiom-architect`): `spec/SPEC-127-crypto-primitives-secure-memory.md` — constant-time operations, `ZeroizeOnDrop` `SecretBytes`, `OsRng` CSPRNG vs `ChaCha20Rng`, `SHA-256`/`SHA-512`/`BLAKE3`, `HMAC`/`HKDF`, `ChaCha20-Poly1305` AEAD, and `X25519`/`Ed25519` (`tasks/0467`, `tasks/0839`).
   - `T929` (`axiom-stdlib`): Constant-time `CtEq`/`CtSelect`, `ZeroizeOnDrop` `SecretBuf<T>`, OS CSPRNG & deterministic `ChaCha20Rng` (`std/crypto/ct`, `std/crypto/secret`, `std/crypto/rng`).
   - `T930` (`axiom-stdlib`): `SHA-256`/`SHA-512`/`BLAKE3` hashes, `HMAC`/`HKDF`, `ChaCha20-Poly1305` AEAD & `Ed25519`/`X25519` primitives (`std/crypto/hash`, `std/crypto/mac_kdf`, `std/crypto/aead`, `std/crypto/sign`).
   - `T931` (`axiom-qa`): Cryptographic hashes, CSPRNG, AEAD, `Ed25519` & constant-time secure memory conformance suite (`tests/conformance/p21/e21_8_crypto_secure_mem`).

9. **E21.9 — Allocators: pool, custom and concurrent allocators (`T932`–`T935`)**:
   - `T932` (`axiom-architect`): `spec/SPEC-128-allocators-pool-custom-concurrent.md` — first-class `Allocator` trait composition, `FixedPoolAllocator`, `SlabAllocator`, `ScratchScope`, `ThreadCacheAllocator`, and `TelemetryAllocator`/`FailAtAllocator` (`0106`, `0036`, `tasks/0280`, `tasks/0415`).
   - `T933` (`axiom-stdlib`): Parameterized `Allocator<A>` collections, `FixedPoolAllocator`, `SlabAllocator` & `ScratchScope` (`std/alloc/pool`, `std/alloc/slab`, `std/alloc/scratch`).
   - `T934` (`axiom-stdlib`): Thread-cached concurrent allocator, `TelemetryAllocator` & deterministic `FailAtAllocator` (`std/alloc/concurrent`, `std/alloc/telemetry`, `std/alloc/fail_inject`).
   - `T935` (`axiom-qa`): Pool, slab, custom, concurrent & fault-injecting allocators conformance suite (`tests/conformance/p21/e21_9_allocators`).

## Files changed

- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md
- ./_workspaces/tasks/todo/T321-phase-p21-gate-standard-library-completion.md
- ./_workspaces/tasks/todo/T521-e13-5-panic-unwinding-ffi-barrier-spec.md
- ./_workspaces/tasks/todo/T900-e21-1-collections-btree-soa-generational-storage-spec.md
- ./_workspaces/tasks/todo/T901-e21-1-vecdeque-btreemap-btreeset-binaryheap-smallvec.md
- ./_workspaces/tasks/todo/T902-e21-1-generational-slotmap-handle-arena-soa-storage.md
- ./_workspaces/tasks/todo/T903-e21-1-collections-soa-generational-handle-conformance.md
- ./_workspaces/tasks/todo/T904-e21-2-text-unicode-normalization-segmentation-spec.md
- ./_workspaces/tasks/todo/T905-e21-2-unicode-tables-nfc-nfd-nfkc-nfkd-case-mapping.md
- ./_workspaces/tasks/todo/T906-e21-2-uax29-grapheme-word-sentence-osstr-cstr.md
- ./_workspaces/tasks/todo/T907-e21-2-unicode-normalization-segmentation-conformance.md
- ./_workspaces/tasks/todo/T908-e21-3-os-fs-process-signals-ipc-console-spec.md
- ./_workspaces/tasks/todo/T909-e21-3-std-fs-positional-io-locks-symlinks-watcher.md
- ./_workspaces/tasks/todo/T910-e21-3-process-pipelines-signals-ipc-writeconsolew-conpty.md
- ./_workspaces/tasks/todo/T911-e21-3-os-fs-process-signals-ipc-conpty-conformance.md
- ./_workspaces/tasks/todo/T912-e21-4-networking-sockets-dns-tls-http-rpc-spec.md
- ./_workspaces/tasks/todo/T913-e21-4-tcp-udp-sockets-ipv4-ipv6-options-dns-resolver.md
- ./_workspaces/tasks/todo/T914-e21-4-tls-boundary-http-client-server-rpc-gateway.md
- ./_workspaces/tasks/todo/T915-e21-4-networking-sockets-dns-http-rpc-conformance.md
- ./_workspaces/tasks/todo/T916-e21-5-time-clocks-duration-instant-timers-spec.md
- ./_workspaces/tasks/todo/T917-e21-5-duration-instant-systemtime-rfc3339-calendar.md
- ./_workspaces/tasks/todo/T918-e21-5-timer-wheels-deadline-interval-mock-clock.md
- ./_workspaces/tasks/todo/T919-e21-5-time-clocks-timer-wheel-mockclock-conformance.md
- ./_workspaces/tasks/todo/T920-e21-6-virtual-memory-reserve-commit-mmap-spec.md
- ./_workspaces/tasks/todo/T921-e21-6-virtualregion-reserve-commit-protect-guard-pages.md
- ./_workspaces/tasks/todo/T922-e21-6-file-anonymous-mmap-cow-flush-capability-views.md
- ./_workspaces/tasks/todo/T923-e21-6-virtual-memory-mmap-protection-conformance.md
- ./_workspaces/tasks/todo/T924-e21-7-serialization-binary-wire-schema-cas-spec.md
- ./_workspaces/tasks/todo/T925-e21-7-encode-decode-wire-reader-writer-schema-codecs.md
- ./_workspaces/tasks/todo/T926-e21-7-zerocopy-views-crc32c-deflate-lz4-cas-store.md
- ./_workspaces/tasks/todo/T927-e21-7-serde-binary-wire-schema-cas-conformance.md
- ./_workspaces/tasks/todo/T928-e21-8-crypto-primitives-csprng-secure-memory-spec.md
- ./_workspaces/tasks/todo/T929-e21-8-constant-time-secretbuf-os-csprng-chacha20rng.md
- ./_workspaces/tasks/todo/T930-e21-8-sha2-blake3-hmac-hkdf-chacha20poly1305-ed25519.md
- ./_workspaces/tasks/todo/T931-e21-8-crypto-hashes-csprng-aead-ed25519-conformance.md
- ./_workspaces/tasks/todo/T932-e21-9-custom-pool-slab-concurrent-allocators-spec.md
- ./_workspaces/tasks/todo/T933-e21-9-parameterized-allocator-pool-slab-scratch.md
- ./_workspaces/tasks/todo/T934-e21-9-thread-cached-concurrent-telemetry-fail-allocator.md
- ./_workspaces/tasks/todo/T935-e21-9-pool-slab-custom-concurrent-allocators-conformance.md

## Tests

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P21-standard-library-completion --strict` → `813 rows` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `v1-full implemented=475  planned=8356`, `gaps: 0`, `COVERAGE OK` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T321` and `T900`–`T935` → `OK` (`37 files`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → `OK (571 tasks)`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T221` → `40 stage, 0 REFUSED`

## Spec deviations

None.

## Follow-ups

None.

STATUS: COMPLETE round=0
