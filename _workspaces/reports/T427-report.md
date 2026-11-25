# T427 Report — E11.6 Unified AsyncRead/AsyncWrite, AsyncFile & loopback AsyncTcp/Udp sockets

## Summary
Implemented the completion-safe async I/O surface on top of the T426 reactor (SPEC-35 §2, §4, §5):

- `std/io/async_io.ax`: `IoBuf`/`IoResultBuf`, `AsyncRead`/`AsyncWrite` traits, buf/slice read and write futures (cancel-on-drop through `Reactor.cancel_op`, zombie buffer retention), `ReadExactFuture`/`WriteAllFuture` (`UnexpectedEof` / `BrokenPipe` semantics).
- `std/fs/async_file.ax`: `AsyncFile` (`open`/`create`/`open_rw`/`open_append` and `*_bytes` variants, positional `read_at`/`write_at`/`read_buf_at`/`write_buf_at` on `view<AsyncFile>`, `flush`, `file_size`, cursor-based `AsyncRead`/`AsyncWrite`, explicit fallible `close().await` distinct from deterministic `Drop`).
- `std/net/mod.ax`: `Ipv4Addr`, `SocketAddr`, `AsyncTcpListener` (ephemeral port resolved), `AsyncTcpStream`, `split() -> (TcpReadHalf, TcpWriteHalf)` over a shared refcounted socket (`tcp_rejoin` to merge), `shutdown`, `AsyncUdpSocket` (`send_to`/`recv_from`).
- `std/io/io.ax` (lock): `IoError` extended append-only (`TimedOut`, `Cancelled`, `ConnectionRefused`, `ConnectionReset`, `BrokenPipe`, `AddrInUse`, `UnexpectedEof`), `@derive(Copy)`, `io_error_from_code` mapping -5..-11.
- `std/sys/windows/iocp.ax` (lock): `bind`/`shutdown` resolved dynamically via `GetProcAddress` on ws2_32 (static `extern` `bind`/`shutdown` collided with stdlib method symbols in native link); wrappers `win_ws2_bind`/`win_ws2_shutdown`.

Tests (`tests/std/async/io/`, `modes: interp native`, each checks exact stdout): concurrent overlapped AsyncFile read/write, TCP loopback request/response, full-duplex `split()`, UDP datagrams, socket read timeout + cancellation.

## Verification (in build-snap-T427, axiomc2.exe)
- `axtest std/async/io std/async/reactor/iocp`: 18/18 PASS (interp, native, native-O1), WEAK-NATIVE 0.
- `archcheck.py`: 0 violations.
- `axtest std/` suite (-j 2): TOTAL 486, PASS 475, FAIL 4, XFAIL 7, WEAK-NATIVE 0. The 4 failures are
  `std/async/{executor/check_async_bundles,structured/check_structured_bundles,waker/check_waker_bundles,waker_qa/check_waker_qa_bundles}.test`
  ("test bundles are out of date"). They are pre-existing and unrelated to T427: running the same
  `gen_tests.py --check` on a pristine `git archive HEAD` extract fails identically (the committed
  bundles lag HEAD's std/sys/windows/thread.ax etc. after T423e/T538; none of T427's files are in the
  bundle source lists). Follow-up: the owner of those bundles (T421a/T422c generators) must regenerate them
  and they should be added to `_workspaces/baseline-failures.txt` until then.

## Design decisions (for the architect)
- Constructors take `*mut Reactor` (not `view<Reactor>` as written in SPEC-35 prose) because futures must hold a stable reactor reference across `.await`; views cannot be held across await (AX_ASYNC_VIEW_ACROSS_AWAIT).
- `split()` consumes the stream and shares the OS handle through a refcounted `TcpStreamShared`; the OS handle closes when both halves drop.
- Dynamic resolution of ws2_32 `bind`/`shutdown` is a workaround for a symbol collision between `extern` names and std method names in the native linker; follow-up: report to the backend owner that extern declarations named like methods (`bind`, `shutdown`) clash.

## Files changed
- std/io/io.ax
- std/io/async_io.ax
- std/fs/async_file.ax
- std/net/mod.ax
- std/sys/windows/iocp.ax
- tests/std/async/io/async_file_overlapped.ax
- tests/std/async/io/async_tcp_loopback.ax
- tests/std/async/io/async_tcp_split_duplex.ax
- tests/std/async/io/async_udp_datagrams.ax
- tests/std/async/io/async_socket_timeout_cancel.ax

STATUS: COMPLETE round=0
