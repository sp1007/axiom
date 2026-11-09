#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/std/channel (T412).

Generates in-tree test bundles for std.sync.channel primitives by concatenating
verbatim standard library source files from HEAD with test harness logic.
Ensures zero test divergence from live std/sync/channel/*.ax implementations.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

BASIC_PREREQS = [
    "std/sync/atomic.ax",
    "std/sys/windows/heap.ax",
    "std/sync/channel/mod.ax",
]

THREAD_PREREQS = [
    "std/sync/atomic.ax",
    "std/sys/windows/heap.ax",
    "std/sys/windows/time.ax",
    "std/sys/windows/thread.ax",
    "std/time/time.ax",
    "std/text/utf8.ax",
    "std/text/string.ax",
    "std/thread/mod.ax",
    "std/sync/channel/mod.ax",
]

# -----------------------------------------------------------------------------
# Test Definitions
# -----------------------------------------------------------------------------

# 1. Bounded Basic
BOUNDED_BASIC_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-007 REQ-CONC-103 REQ-CONC-115
// stdout: OK channel_bounded_basic 10 20 30 40 50 60 70\\n
"""

BOUNDED_BASIC_SOURCES = THREAD_PREREQS

BOUNDED_BASIC_MAIN = """module main

use std.core.result.Result
use std.sync.channel.channel_bounded
use std.sync.channel.Sender
use std.sync.channel.Receiver
use std.sync.channel.SendError
use std.sync.channel.TrySendError
use std.sync.channel.RecvError
use std.sync.channel.TryRecvError

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub fn main() -> i32 {
    let chan = channel_bounded<i64>(2usize);
    let tx = chan.tx;
    let rx = chan.rx;

    check(view(tx).capacity() == 2usize);
    check(view(rx).capacity() == 2usize);

    // Initial state: empty
    match view(rx).try_recv() {
        Result.Err(TryRecvError.Empty) => {},
        _ => check(false),
    }

    // Send 10: length becomes 1
    match view(tx).send(10i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }

    // Receive 10
    let v10 = match view(rx).try_recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(v10 == 10i64);

    // Try_send 20 and 30 into capacity 2
    match view(tx).try_send(20i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }
    match view(tx).try_send(30i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }

    // Queue is full now (len == 2) -> try_send(40) must return Full(40)
    let v40 = match view(tx).try_send(40i64) {
        Result.Err(TrySendError.Full(v)) => v,
        _ => { check(false); 0i64 },
    };
    check(v40 == 40i64);

    // Dequeue 20
    let v20 = match view(rx).recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(v20 == 20i64);

    // Now space is freed -> try_send(50) succeeds
    match view(tx).try_send(50i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }

    // Dequeue 30 and 50
    let v30 = match view(rx).recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(v30 == 30i64);

    let v50 = match view(rx).recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(v50 == 50i64);

    // Queue is empty again
    match view(rx).try_recv() {
        Result.Err(TryRecvError.Empty) => {},
        _ => check(false),
    }

    // Explicit close on sender
    view(tx).close();

    // try_send and send on closed channel return disconnected
    let v60 = match view(tx).try_send(60i64) {
        Result.Err(TrySendError.Disconnected(v)) => v,
        _ => { check(false); 0i64 },
    };
    check(v60 == 60i64);

    let v70 = match view(tx).send(70i64) {
        Result.Err(err) => err.val,
        _ => { check(false); 0i64 },
    };
    check(v70 == 70i64);

    // Receiver sees disconnected on closed & empty channel
    match view(rx).try_recv() {
        Result.Err(TryRecvError.Disconnected) => {},
        _ => check(false),
    }

    match view(rx).recv() {
        Result.Err(RecvError.Disconnected) => {},
        _ => check(false),
    }

    print("OK channel_bounded_basic ");
    print_int(v10); print(" ");
    print_int(v20); print(" ");
    print_int(v30); print(" ");
    print_int(v40); print(" ");
    print_int(v50); print(" ");
    print_int(v60); print(" ");
    print_int(v70); print("\\n");
    0
}
"""

# 2. Unbounded Basic
UNBOUNDED_BASIC_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-007 REQ-CONC-103 REQ-CONC-115
// stdout: OK channel_unbounded_basic 45 10\\n
"""

UNBOUNDED_BASIC_SOURCES = THREAD_PREREQS

UNBOUNDED_BASIC_MAIN = """module main

use std.core.result.Result
use std.sync.channel.channel_unbounded
use std.sync.channel.UnboundedSender
use std.sync.channel.UnboundedReceiver
use std.sync.channel.SendError
use std.sync.channel.TrySendError
use std.sync.channel.RecvError
use std.sync.channel.TryRecvError

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub fn main() -> i32 {
    let chan = channel_unbounded<i64>();
    let tx = chan.tx;
    let rx = chan.rx;

    match view(rx).try_recv() {
        Result.Err(TryRecvError.Empty) => {},
        _ => check(false),
    }

    // Send 10 items (0..9)
    let mut i: i64 = 0i64;
    while i < 10i64 {
        if i % 2i64 == 0i64 {
            match view(tx).send(i) {
                Result.Ok(_) => {},
                _ => check(false),
            }
        } else {
            match view(tx).try_send(i) {
                Result.Ok(_) => {},
                _ => check(false),
            }
        }
        i = i + 1i64;
    }

    // Dequeue all 10 items in FIFO order
    let mut sum: i64 = 0i64;
    let mut count: i64 = 0i64;
    let mut expected: i64 = 0i64;
    while count < 10i64 {
        let val = match view(rx).try_recv() {
            Result.Ok(v) => v,
            _ => { check(false); 0i64 },
        };
        check(val == expected);
        sum = sum + val;
        count = count + 1i64;
        expected = expected + 1i64;
    }
    check(sum == 45i64);
    check(count == 10i64);

    match view(rx).try_recv() {
        Result.Err(TryRecvError.Empty) => {},
        _ => check(false),
    }

    // Close unbounded channel
    view(tx).close();

    match view(tx).send(999i64) {
        Result.Err(err) => check(err.val == 999i64),
        _ => check(false),
    }

    match view(tx).try_send(888i64) {
        Result.Err(TrySendError.Disconnected(v)) => check(v == 888i64),
        _ => check(false),
    }

    match view(rx).try_recv() {
        Result.Err(TryRecvError.Disconnected) => {},
        _ => check(false),
    }

    match view(rx).recv() {
        Result.Err(RecvError.Disconnected) => {},
        _ => check(false),
    }

    print("OK channel_unbounded_basic ");
    print_int(sum); print(" ");
    print_int(count); print("\\n");
    0
}
"""

# 3. SPSC Threads
SPSC_THREADS_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-007 REQ-CONC-041 REQ-CONC-042 REQ-CONC-043 REQ-CONC-185
// stdout: OK channel_spsc_threads 1275 50\\n
"""

SPSC_THREADS_SOURCES = THREAD_PREREQS

SPSC_THREADS_MAIN = """module main

use std.core.result.Result
use std.thread.spawn
use std.sync.channel.channel_bounded
use std.sync.channel.Sender
use std.sync.channel.Receiver
use std.sync.channel.RecvError

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub fn main() -> i32 {
    // Capacity 2 forces producer to block and wait for consumer backpressure
    let chan = channel_bounded<i64>(2usize);
    let tx = chan.tx;
    let rx = chan.rx;

    let h = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 50i64 {
            match view(tx).send(i) {
                Result.Ok(_) => {},
                _ => loop {},
            }
            i = i + 1i64;
        }
        drop(tx);
        50i64
    });

    let mut sum: i64 = 0i64;
    let mut count: i64 = 0i64;
    while true {
        match view(rx).recv() {
            Result.Ok(val) => {
                sum = sum + val;
                count = count + 1i64;
            },
            Result.Err(RecvError.Disconnected) => {
                break;
            },
        }
    }

    let _ = h.join();
    check(count == 50i64);
    check(sum == 1275i64);

    print("OK channel_spsc_threads ");
    print_int(sum); print(" ");
    print_int(count); print("\\n");
    0
}
"""

# 4. MPSC Threads
MPSC_THREADS_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-007 REQ-CONC-041 REQ-CONC-043 REQ-CONC-104 REQ-CONC-185
// stdout: OK channel_mpsc_threads 100 251300\\n
"""

MPSC_THREADS_SOURCES = THREAD_PREREQS

MPSC_THREADS_MAIN = """module main

use std.core.result.Result
use std.thread.spawn
use std.sync.channel.channel_bounded
use std.sync.channel.Sender
use std.sync.channel.Receiver
use std.sync.channel.RecvError

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub fn main() -> i32 {
    let chan = channel_bounded<i64>(4usize);
    let tx = chan.tx;
    let rx = chan.rx;

    let tx1 = view(tx).clone();
    let tx2 = view(tx).clone();
    let tx3 = view(tx).clone();
    let tx4 = tx; // move the original into the 4th thread

    let h1 = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 25i64 {
            let _ = view(tx1).send(1000i64 + i);
            i = i + 1i64;
        }
        drop(tx1);
        25i64
    });

    let h2 = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 25i64 {
            let _ = view(tx2).send(2000i64 + i);
            i = i + 1i64;
        }
        drop(tx2);
        25i64
    });

    let h3 = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 25i64 {
            let _ = view(tx3).send(3000i64 + i);
            i = i + 1i64;
        }
        drop(tx3);
        25i64
    });

    let h4 = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 25i64 {
            let _ = view(tx4).send(4000i64 + i);
            i = i + 1i64;
        }
        drop(tx4);
        25i64
    });

    let mut count: i64 = 0i64;
    let mut sum: i64 = 0i64;
    while true {
        match view(rx).recv() {
            Result.Ok(val) => {
                count = count + 1i64;
                sum = sum + val;
            },
            Result.Err(RecvError.Disconnected) => {
                break;
            },
        }
    }

    let _ = h1.join();
    let _ = h2.join();
    let _ = h3.join();
    let _ = h4.join();

    check(count == 100i64);
    // Sum: 25*(1000+2000+3000+4000) + 4 * (25*26/2) = 25*10000 + 4*325 = 250000 + 1300 = 251300?
    // Wait: 10000 * 25 / 1? Wait: (1000..1025) sum is 25*1000 + 325 = 25325.
    // 25325 + 50325 + 75325 + 100325 = 251300.
    check(sum == 251300i64);

    print("OK channel_mpsc_threads ");
    print_int(count); print(" ");
    print_int(sum); print("\\n");
    0
}
"""

# 5. MPMC Threads
MPMC_THREADS_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-007 REQ-CONC-041 REQ-CONC-104 REQ-CONC-185
// stdout: OK channel_mpmc_threads 100 251300\\n
"""

MPMC_THREADS_SOURCES = THREAD_PREREQS

MPMC_THREADS_MAIN = """module main

use std.core.result.Result
use std.thread.spawn
use std.sync.channel.channel_bounded
use std.sync.channel.Sender
use std.sync.channel.Receiver
use std.sync.channel.RecvError

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub fn main() -> i32 {
    let chan = channel_bounded<i64>(4usize);
    let tx = chan.tx;
    let rx = chan.rx;

    let tx1 = view(tx).clone();
    let tx2 = view(tx).clone();
    let tx3 = view(tx).clone();
    let tx4 = tx;

    let rx1 = view(rx).clone();
    let rx2 = rx;

    // 4 Producers
    let hp1 = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 25i64 {
            let _ = view(tx1).send(1000i64 + i);
            i = i + 1i64;
        }
        drop(tx1);
        25i64
    });

    let hp2 = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 25i64 {
            let _ = view(tx2).send(2000i64 + i);
            i = i + 1i64;
        }
        drop(tx2);
        25i64
    });

    let hp3 = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 25i64 {
            let _ = view(tx3).send(3000i64 + i);
            i = i + 1i64;
        }
        drop(tx3);
        25i64
    });

    let hp4 = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 25i64 {
            let _ = view(tx4).send(4000i64 + i);
            i = i + 1i64;
        }
        drop(tx4);
        25i64
    });

    // 2 Consumers
    let hc1 = spawn(|| -> i64 {
        let mut local_sum: i64 = 0i64;
        while true {
            match view(rx1).recv() {
                Result.Ok(val) => {
                    local_sum = local_sum + val;
                },
                Result.Err(RecvError.Disconnected) => {
                    break;
                },
            }
        }
        drop(rx1);
        local_sum
    });

    let hc2 = spawn(|| -> i64 {
        let mut local_sum: i64 = 0i64;
        while true {
            match view(rx2).recv() {
                Result.Ok(val) => {
                    local_sum = local_sum + val;
                },
                Result.Err(RecvError.Disconnected) => {
                    break;
                },
            }
        }
        drop(rx2);
        local_sum
    });

    let _ = hp1.join();
    let _ = hp2.join();
    let _ = hp3.join();
    let _ = hp4.join();

    let s1 = match hc1.join() {
        Result.Ok(v) => v,
        _ => 0i64,
    };
    let s2 = match hc2.join() {
        Result.Ok(v) => v,
        _ => 0i64,
    };

    let total_sum = s1 + s2;
    check(total_sum == 251300i64);

    print("OK channel_mpmc_threads 100 ");
    print_int(total_sum);
    print("\\n");
    0
}
"""

# 6. Move Only & Drop Accounting
MOVE_ONLY_DROP_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-007 REQ-CONC-011 REQ-CONC-116 REQ-CONC-143
// stdout: OK channel_move_only_drop 5 11 18\\n
"""

MOVE_ONLY_DROP_SOURCES = THREAD_PREREQS

MOVE_ONLY_DROP_MAIN = """module main

use std.core.result.Result
use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.sync.channel.channel_bounded
use std.sync.channel.channel_bounded_with_size
use std.sync.channel.channel_bounded_with_drop
use std.sync.channel.channel_unbounded
use std.sync.channel.channel_unbounded_with_size
use std.sync.channel.channel_unbounded_with_drop
use std.sync.channel.Sender
use std.sync.channel.Receiver
use std.sync.channel.UnboundedSender
use std.sync.channel.UnboundedReceiver

@intrinsic fn size_of<T>() -> usize { 0 }
@intrinsic unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }
@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

@intrinsic unsafe fn drop_in_place<T>(p: *mut T) {}

fn drop_tracked_glue(p: *mut u8) -> () {
    if (p as usize) != 0usize {
        unsafe {
            drop_in_place<Tracked>(p as *mut Tracked);
        }
    }
}

struct Tracked {
    pub p_counter: *mut Atomic<usize>,
}
impl !Copy for Tracked {}
unsafe impl Send for Tracked {}
impl Drop for Tracked {
    fn drop(self: mut_view<Tracked>) {
        if (self.p_counter as usize) != 0usize {
            unsafe {
                (*self.p_counter).fetch_add(1usize, Ordering.Relaxed);
            }
        }
    }
}

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub fn main() -> i32 {
    let mut drop_counter: Atomic<usize> = Atomic.new(0usize);
    let p_dc: *mut Atomic<usize> = unsafe { address_of_mut(drop_counter) };

    // -------------------------------------------------------------
    // Part 1: Bounded normal send, receive, then drop received
    // -------------------------------------------------------------
    {
        let chan = channel_bounded_with_size<Tracked>(4usize, size_of<Tracked>());
        let tx = chan.tx;
        let rx = chan.rx;

        let mut i: i64 = 0i64;
        while i < 5i64 {
            let item = Tracked { p_counter: p_dc };
            if i < 4i64 {
                let _ = view(tx).send(item);
            } else {
                let _ = view(tx).try_send(item);
            }
            if i >= 1i64 {
                let r = view(rx).recv();
                match r {
                    Result.Ok(rec) => drop(rec), // drops item
                    _ => check(false),
                }
            }
            i = i + 1i64;
        }
        // Drain remaining
        let r_last = view(rx).recv();
        match r_last {
            Result.Ok(rec) => drop(rec),
            _ => check(false),
        }
    }
    let c1 = unsafe { (*p_dc).load(Ordering.Relaxed) };
    check(c1 == 5usize);

    // -------------------------------------------------------------
    // Part 2: Bounded teardown: drop Receiver with unread items in queue
    // -------------------------------------------------------------
    {
        let chan2 = channel_bounded_with_drop<Tracked>(10usize, drop_tracked_glue);
        let tx2 = chan2.tx;
        let rx2 = chan2.rx;

        let mut j: i64 = 0i64;
        while j < 5i64 {
            let it = Tracked { p_counter: p_dc };
            let _ = view(tx2).send(it);
            j = j + 1i64;
        }
        check(unsafe { (*p_dc).load(Ordering.Relaxed) } == 5usize);

        // Dropping rx2 MUST immediately drop all 5 items queued in the channel!
        drop(rx2);
        check(unsafe { (*p_dc).load(Ordering.Relaxed) } == 10usize);

        // Send into closed channel returns rejected item in SendError(val)
        let reject_item = Tracked { p_counter: p_dc };
        match view(tx2).send(reject_item) {
            Result.Err(err) => {
                // Dropping err drops reject_item!
                drop(err);
            },
            _ => check(false),
        }
        check(unsafe { (*p_dc).load(Ordering.Relaxed) } == 11usize);
    }
    let c2 = unsafe { (*p_dc).load(Ordering.Relaxed) };
    check(c2 == 11usize);

    // -------------------------------------------------------------
    // Part 3: Unbounded teardown: drop Receiver with unread items in queue
    // -------------------------------------------------------------
    {
        let uchan = channel_unbounded_with_drop<Tracked>(drop_tracked_glue);
        let utx = uchan.tx;
        let urx = uchan.rx;

        let mut k: i64 = 0i64;
        while k < 7i64 {
            let it = Tracked { p_counter: p_dc };
            let _ = view(utx).send(it);
            k = k + 1i64;
        }
        check(unsafe { (*p_dc).load(Ordering.Relaxed) } == 11usize);

        // Dropping urx MUST drain and drop all 7 items in the linked list!
        drop(urx);
        check(unsafe { (*p_dc).load(Ordering.Relaxed) } == 18usize);
    }
    let c3 = unsafe { (*p_dc).load(Ordering.Relaxed) };
    check(c3 == 18usize);

    print("OK channel_move_only_drop ");
    print_int(c1 as i64); print(" ");
    print_int(c2 as i64); print(" ");
    print_int(c3 as i64); print("\\n");
    0
}
"""

# 7. Big Struct
BIG_STRUCT_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-007 REQ-CONC-041 REQ-CONC-043
// stdout: OK channel_big_struct 10 10\\n
"""

BIG_STRUCT_SOURCES = THREAD_PREREQS

BIG_STRUCT_MAIN = """module main

use std.core.result.Result
use std.thread.spawn
use std.sync.channel.channel_bounded
use std.sync.channel.channel_bounded_with_size
use std.sync.channel.channel_bounded_with_drop
use std.sync.channel.channel_unbounded
use std.sync.channel.channel_unbounded_with_size
use std.sync.channel.channel_unbounded_with_drop
use std.sync.channel.Sender
use std.sync.channel.Receiver
use std.sync.channel.UnboundedSender
use std.sync.channel.UnboundedReceiver
use std.sync.channel.RecvError

@intrinsic fn size_of<T>() -> usize { 0 }
@intrinsic unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }
@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

struct BigItem {
    pub a: i64,
    pub b: i64,
    pub c: i64,
    pub d: i64,
}
impl !Copy for BigItem {}

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub fn main() -> i32 {
    // 1. Bounded channel with 32-byte struct across threads
    let chan = channel_bounded_with_size<BigItem>(2usize, size_of<BigItem>());
    let tx = chan.tx;
    let rx = chan.rx;

    let h = spawn(|| -> i64 {
        let mut i: i64 = 1i64;
        while i <= 10i64 {
            let item = BigItem { a: i, b: i * 2i64, c: i * 3i64, d: i * 4i64 };
            let _ = unsafe { view(tx).send_from_ptr(address_of<BigItem>(item), 32usize) };
            i = i + 1i64;
        }
        drop(tx);
        10i64
    });

    let mut bounded_count: i64 = 0i64;
    while true {
        let mut item = BigItem { a: 0i64, b: 0i64, c: 0i64, d: 0i64 };
        match unsafe { view(rx).recv_into_ptr(address_of_mut<BigItem>(item), 32usize) } {
            Result.Ok(_) => {
                bounded_count = bounded_count + 1i64;
                check(item.a == bounded_count);
                check(item.b == bounded_count * 2i64);
                check(item.c == bounded_count * 3i64);
                check(item.d == bounded_count * 4i64);
            },
            Result.Err(RecvError.Disconnected) => {
                break;
            },
        }
    }
    let _ = h.join();
    check(bounded_count == 10i64);

    // 2. Unbounded channel with 32-byte struct
    let uchan = channel_unbounded_with_size<BigItem>(size_of<BigItem>());
    let utx = uchan.tx;
    let urx = uchan.rx;

    let mut k: i64 = 1i64;
    while k <= 10i64 {
        let item = BigItem { a: k * 10i64, b: k * 20i64, c: k * 30i64, d: k * 40i64 };
        let _ = unsafe { view(utx).send_from_ptr(address_of<BigItem>(item), 32usize) };
        k = k + 1i64;
    }
    view(utx).close();

    let mut unbounded_count: i64 = 0i64;
    while true {
        let mut item = BigItem { a: 0i64, b: 0i64, c: 0i64, d: 0i64 };
        match unsafe { view(urx).recv_into_ptr(address_of_mut<BigItem>(item), 32usize) } {
            Result.Ok(_) => {
                unbounded_count = unbounded_count + 1i64;
                check(item.a == unbounded_count * 10i64);
                check(item.b == unbounded_count * 20i64);
                check(item.c == unbounded_count * 30i64);
                check(item.d == unbounded_count * 40i64);
            },
            Result.Err(RecvError.Disconnected) => {
                break;
            },
        }
    }
    check(unbounded_count == 10i64);

    print("OK channel_big_struct ");
    print_int(bounded_count); print(" ");
    print_int(unbounded_count); print("\\n");
    0
}
"""


# 8. Boundary Edge (T412 QA)
BOUNDARY_EDGE_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-007 REQ-CONC-103 REQ-CONC-115 REQ-CONC-116
// stdout: OK channel_boundary_edge cap1=1 close_drain=3 partial_drop=999 uclose=77\\n
"""

BOUNDARY_EDGE_SOURCES = THREAD_PREREQS

BOUNDARY_EDGE_MAIN = """module main

use std.core.result.Result
use std.sync.channel.channel_bounded
use std.sync.channel.channel_unbounded
use std.sync.channel.Sender
use std.sync.channel.Receiver
use std.sync.channel.UnboundedSender
use std.sync.channel.UnboundedReceiver
use std.sync.channel.SendError
use std.sync.channel.TrySendError
use std.sync.channel.RecvError
use std.sync.channel.TryRecvError

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub fn main() -> i32 {
    // -------------------------------------------------------------
    // Seam 1: Capacity-1 bounded channel backpressure & handoff
    // -------------------------------------------------------------
    let chan1 = channel_bounded<i64>(1usize);
    let tx1 = chan1.tx;
    let rx1 = chan1.rx;
    check(view(tx1).capacity() == 1usize);

    match view(tx1).try_send(42i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }

    match view(tx1).try_send(43i64) {
        Result.Err(TrySendError.Full(v)) => check(v == 43i64),
        _ => check(false),
    }

    let r1 = match view(rx1).recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(r1 == 42i64);

    match view(rx1).try_recv() {
        Result.Err(TryRecvError.Empty) => {},
        _ => check(false),
    }

    match view(tx1).send(100i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }

    let r2 = match view(rx1).try_recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(r2 == 100i64);

    // -------------------------------------------------------------
    // Seam 2: Explicit close() on bounded channel drains buffered items
    // -------------------------------------------------------------
    let chan2 = channel_bounded<i64>(5usize);
    let tx2 = chan2.tx;
    let rx2 = chan2.rx;

    match view(tx2).send(10i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }
    match view(tx2).send(20i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }
    match view(tx2).send(30i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }

    view(tx2).close();

    match view(tx2).send(40i64) {
        Result.Err(SendError { val }) => check(val == 40i64),
        _ => check(false),
    }
    match view(tx2).try_send(50i64) {
        Result.Err(TrySendError.Disconnected(val)) => check(val == 50i64),
        _ => check(false),
    }

    let d1 = match view(rx2).try_recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(d1 == 10i64);

    let d2 = match view(rx2).recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(d2 == 20i64);

    let d3 = match view(rx2).recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(d3 == 30i64);

    match view(rx2).try_recv() {
        Result.Err(TryRecvError.Disconnected) => {},
        _ => check(false),
    }
    match view(rx2).recv() {
        Result.Err(RecvError.Disconnected) => {},
        _ => check(false),
    }

    // -------------------------------------------------------------
    // Seam 3: Cloned sender partial drop vs final sender drop
    // -------------------------------------------------------------
    let uchan = channel_unbounded<i64>();
    let utx_a = uchan.tx;
    let urx = uchan.rx;
    let utx_b = view(utx_a).clone();

    drop(utx_a);

    match view(urx).try_recv() {
        Result.Err(TryRecvError.Empty) => {},
        _ => check(false),
    }

    match view(utx_b).send(999i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }

    drop(utx_b);

    let uv = match view(urx).recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(uv == 999i64);

    match view(urx).try_recv() {
        Result.Err(TryRecvError.Disconnected) => {},
        _ => check(false),
    }
    match view(urx).recv() {
        Result.Err(RecvError.Disconnected) => {},
        _ => check(false),
    }

    // -------------------------------------------------------------
    // Seam 4: Explicit close() on unbounded channel drains buffered items
    // -------------------------------------------------------------
    let uchan2 = channel_unbounded<i64>();
    let utx2 = uchan2.tx;
    let urx2 = uchan2.rx;

    match view(utx2).send(77i64) {
        Result.Ok(_) => {},
        _ => check(false),
    }
    view(urx2).close();

    match view(utx2).send(88i64) {
        Result.Err(SendError { val }) => check(val == 88i64),
        _ => check(false),
    }

    let u2_val = match view(urx2).recv() {
        Result.Ok(v) => v,
        _ => { check(false); 0i64 },
    };
    check(u2_val == 77i64);

    match view(urx2).recv() {
        Result.Err(RecvError.Disconnected) => {},
        _ => check(false),
    }

    print("OK channel_boundary_edge cap1=1 close_drain=3 partial_drop=999 uclose=77\\n");
    0
}
"""

BUNDLES = {
    "channel_bounded_basic.ax": (BOUNDED_BASIC_HEADER, BOUNDED_BASIC_SOURCES, BOUNDED_BASIC_MAIN),
    "channel_unbounded_basic.ax": (UNBOUNDED_BASIC_HEADER, UNBOUNDED_BASIC_SOURCES, UNBOUNDED_BASIC_MAIN),
    "channel_spsc_threads.ax": (SPSC_THREADS_HEADER, SPSC_THREADS_SOURCES, SPSC_THREADS_MAIN),
    "channel_mpsc_threads.ax": (MPSC_THREADS_HEADER, MPSC_THREADS_SOURCES, MPSC_THREADS_MAIN),
    "channel_mpmc_threads.ax": (MPMC_THREADS_HEADER, MPMC_THREADS_SOURCES, MPMC_THREADS_MAIN),
    "channel_move_only_drop.ax": (MOVE_ONLY_DROP_HEADER, MOVE_ONLY_DROP_SOURCES, MOVE_ONLY_DROP_MAIN),
    "channel_big_struct.ax": (BIG_STRUCT_HEADER, BIG_STRUCT_SOURCES, BIG_STRUCT_MAIN),
    "channel_boundary_edge.ax": (BOUNDARY_EDGE_HEADER, BOUNDARY_EDGE_SOURCES, BOUNDARY_EDGE_MAIN),
}


def read_source(rel_path):
    if rel_path.startswith("std/sync/channel"):
        path = os.path.join(ROOT, rel_path.replace("/", os.sep))
        with open(path, "r", encoding="utf-8") as f:
            return f.read().replace("\r\n", "\n")
    import subprocess
    try:
        res = subprocess.run(["git", "show", f"HEAD:{rel_path}"], cwd=ROOT, capture_output=True, text=True, check=True)
        return res.stdout.replace("\r\n", "\n")
    except Exception:
        path = os.path.join(ROOT, rel_path.replace("/", os.sep))
        with open(path, "r", encoding="utf-8") as f:
            return f.read().replace("\r\n", "\n")


def build_bundle(header, sources, main_code):
    parts = [header.rstrip("\n")]
    for src in sources:
        content = read_source(src).strip()
        parts.append(content)
    parts.append(main_code.strip())
    return "\n\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify test bundles are up to date")
    args = parser.parse_args()

    mismatches = []
    for fname, (header, sources, main_code) in BUNDLES.items():
        expected = build_bundle(header, sources, main_code)
        target_path = os.path.join(HERE, fname)
        if args.check:
            if not os.path.exists(target_path):
                mismatches.append(f"{fname}: does not exist")
                continue
            with open(target_path, "r", encoding="utf-8") as f:
                actual = f.read().replace("\r\n", "\n")
            if actual != expected:
                mismatches.append(f"{fname}: content out of date (length actual={len(actual)} vs expected={len(expected)})")
        else:
            with open(target_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(expected)
            print(f"Generated {fname}")

    if args.check:
        if mismatches:
            print("ERROR: channel test bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            print("Run `python tests/std/channel/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK channel bundles match live std/sync/channel\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
