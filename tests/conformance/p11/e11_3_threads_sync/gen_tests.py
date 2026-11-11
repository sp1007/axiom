#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/conformance/p11/e11_3_threads_sync (T414).

Generates in-tree multi-threaded stress and conformance test bundles by
concatenating verbatim standard library source files from HEAD with test harness
logic. Ensures zero test divergence from live std/ implementations.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

COMMON_PREREQS = [
    "std/sync/atomic.ax",
    "std/sys/windows/heap.ax",
    "std/sys/windows/time.ax",
    "std/sys/windows/thread.ax",
    "std/time/time.ax",
    "std/text/utf8.ax",
    "std/text/string.ax",
    "std/thread/local.ax",
    "std/thread/mod.ax",
]

# -----------------------------------------------------------------------------
# 1. 8-Thread Arc<Mutex<T>> Counter & Ring Mutation Stress
# -----------------------------------------------------------------------------
ARC_MUTEX_8THREAD_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-036 REQ-CONC-039 REQ-CONC-187
// stdout: OK arc_mutex_8thread_stress 160 160 720 1 1 999\\n
"""

ARC_MUTEX_8THREAD_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/mutex.ax",
]

ARC_MUTEX_8THREAD_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.mutex.Mutex
use std.thread.spawn

@intrinsic fn panic(msg: str) {}

fn check(cond: bool) {
    if !cond {
        panic("check failed");
    }
}

@repr(C)
struct RingState {
    pub count: i64,
    pub slots: [8]i64,
    pub checksum: i64,
}

pub fn main() -> i32 {
    let init_state = RingState {
        count: 0i64,
        slots: [0i64, 0i64, 0i64, 0i64, 0i64, 0i64, 0i64, 0i64],
        checksum: 0i64,
    };
    let m = Arc.new(Mutex.new(init_state));

    let m0 = view(m).clone();
    let m1 = view(m).clone();
    let m2 = view(m).clone();
    let m3 = view(m).clone();
    let m4 = view(m).clone();
    let m5 = view(m).clone();
    let m6 = view(m).clone();
    let m7 = view(m).clone();

    // 8 concurrent threads mutating counter and ring buffer
    let h0 = spawn(|| -> i64 {
        let p_m = view(m0).as_ptr();
        let mut i: i64 = 0i64;
        while i < 20i64 {
            let mut g = Mutex.lock_ptr(p_m);
            let ptr = g.get_mut_ptr();
            unsafe {
                let next_cnt = (*ptr).count + 1i64;
                let slot_idx = (next_cnt as usize) % 8usize;
                (*ptr).slots[slot_idx] = (*ptr).slots[slot_idx] + 1i64;
                (*ptr).checksum = (*ptr).checksum + 1i64;
                (*ptr).count = next_cnt;
            }
            drop(g);
            i = i + 1i64;
        }
        20i64
    });

    let h1 = spawn(|| -> i64 {
        let p_m = view(m1).as_ptr();
        let mut i: i64 = 0i64;
        while i < 20i64 {
            let mut g = Mutex.lock_ptr(p_m);
            let ptr = g.get_mut_ptr();
            unsafe {
                let next_cnt = (*ptr).count + 1i64;
                let slot_idx = (next_cnt as usize) % 8usize;
                (*ptr).slots[slot_idx] = (*ptr).slots[slot_idx] + 1i64;
                (*ptr).checksum = (*ptr).checksum + 1i64;
                (*ptr).count = next_cnt;
            }
            drop(g);
            i = i + 1i64;
        }
        20i64
    });

    let h2 = spawn(|| -> i64 {
        let p_m = view(m2).as_ptr();
        let mut i: i64 = 0i64;
        while i < 20i64 {
            let mut g = Mutex.lock_ptr(p_m);
            let ptr = g.get_mut_ptr();
            unsafe {
                let next_cnt = (*ptr).count + 1i64;
                let slot_idx = (next_cnt as usize) % 8usize;
                (*ptr).slots[slot_idx] = (*ptr).slots[slot_idx] + 1i64;
                (*ptr).checksum = (*ptr).checksum + 1i64;
                (*ptr).count = next_cnt;
            }
            drop(g);
            i = i + 1i64;
        }
        20i64
    });

    let h3 = spawn(|| -> i64 {
        let p_m = view(m3).as_ptr();
        let mut i: i64 = 0i64;
        while i < 20i64 {
            let mut g = Mutex.lock_ptr(p_m);
            let ptr = g.get_mut_ptr();
            unsafe {
                let next_cnt = (*ptr).count + 1i64;
                let slot_idx = (next_cnt as usize) % 8usize;
                (*ptr).slots[slot_idx] = (*ptr).slots[slot_idx] + 1i64;
                (*ptr).checksum = (*ptr).checksum + 1i64;
                (*ptr).count = next_cnt;
            }
            drop(g);
            i = i + 1i64;
        }
        20i64
    });

    let h4 = spawn(|| -> i64 {
        let p_m = view(m4).as_ptr();
        let mut i: i64 = 0i64;
        while i < 20i64 {
            let mut g = Mutex.lock_ptr(p_m);
            let ptr = g.get_mut_ptr();
            unsafe {
                let next_cnt = (*ptr).count + 1i64;
                let slot_idx = (next_cnt as usize) % 8usize;
                (*ptr).slots[slot_idx] = (*ptr).slots[slot_idx] + 1i64;
                (*ptr).checksum = (*ptr).checksum + 1i64;
                (*ptr).count = next_cnt;
            }
            drop(g);
            i = i + 1i64;
        }
        20i64
    });

    let h5 = spawn(|| -> i64 {
        let p_m = view(m5).as_ptr();
        let mut i: i64 = 0i64;
        while i < 20i64 {
            let mut g = Mutex.lock_ptr(p_m);
            let ptr = g.get_mut_ptr();
            unsafe {
                let next_cnt = (*ptr).count + 1i64;
                let slot_idx = (next_cnt as usize) % 8usize;
                (*ptr).slots[slot_idx] = (*ptr).slots[slot_idx] + 1i64;
                (*ptr).checksum = (*ptr).checksum + 1i64;
                (*ptr).count = next_cnt;
            }
            drop(g);
            i = i + 1i64;
        }
        20i64
    });

    let h6 = spawn(|| -> i64 {
        let p_m = view(m6).as_ptr();
        let mut i: i64 = 0i64;
        while i < 20i64 {
            let mut g = Mutex.lock_ptr(p_m);
            let ptr = g.get_mut_ptr();
            unsafe {
                let next_cnt = (*ptr).count + 1i64;
                let slot_idx = (next_cnt as usize) % 8usize;
                (*ptr).slots[slot_idx] = (*ptr).slots[slot_idx] + 1i64;
                (*ptr).checksum = (*ptr).checksum + 1i64;
                (*ptr).count = next_cnt;
            }
            drop(g);
            i = i + 1i64;
        }
        20i64
    });

    let h7 = spawn(|| -> i64 {
        let p_m = view(m7).as_ptr();
        let mut i: i64 = 0i64;
        while i < 20i64 {
            let mut g = Mutex.lock_ptr(p_m);
            let ptr = g.get_mut_ptr();
            unsafe {
                let next_cnt = (*ptr).count + 1i64;
                let slot_idx = (next_cnt as usize) % 8usize;
                (*ptr).slots[slot_idx] = (*ptr).slots[slot_idx] + 1i64;
                (*ptr).checksum = (*ptr).checksum + 1i64;
                (*ptr).count = next_cnt;
            }
            drop(g);
            i = i + 1i64;
        }
        20i64
    });

    let r0 = match h0.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let r1 = match h1.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let r2 = match h2.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let r3 = match h3.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let r4 = match h4.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let r5 = match h5.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let r6 = match h6.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let r7 = match h7.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };

    let total_spawned = r0 + r1 + r2 + r3 + r4 + r5 + r6 + r7;
    check(total_spawned == 160i64);

    let p_final = view(m).as_ptr();
    let g_final = Mutex.lock_ptr(p_final);
    let final_ptr = g_final.get_ptr();
    let final_count = unsafe { (*final_ptr).count };
    let final_checksum = unsafe { (*final_ptr).checksum };
    check(final_count == 160i64);
    check(final_checksum == 160i64);

    let mut slot_sum: i64 = 0i64;
    let mut s_idx: usize = 0usize;
    while s_idx < 8usize {
        let cnt = unsafe { (*final_ptr).slots[s_idx] };
        check(cnt == 20i64);
        slot_sum = slot_sum + cnt * (s_idx as i64 + 1i64);
        s_idx = s_idx + 1usize;
    }
    drop(g_final);

    // Verify try_lock semantics while lock is unheld
    match Mutex.try_lock_ptr(p_final) {
        Option.Some(g_try) => {
            check(unsafe { (*g_try.get_ptr()).count } == 160i64);
            drop(g_try);
        },
        Option.None => check(false),
    }

    // Verify Arc strong_count and weak_count
    let strong = view(m).strong_count();
    let weak = view(m).weak_count();
    check(strong == 1usize);
    check(weak == 0usize);

    print("OK arc_mutex_8thread_stress ");
    print_int(total_spawned);
    print(" ");
    print_int(final_count);
    print(" ");
    print_int(slot_sum);
    print(" ");
    print_int(strong as i64);
    print(" ");
    print_int(1i64);
    print(" 999\\n");
    0
}
"""

# -------------------------------------------------------------
# 2. Reader-Heavy and Writer-Heavy RwLock<T> Stress
# -------------------------------------------------------------
RWLOCK_READER_WRITER_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-036 REQ-CONC-039 REQ-CONC-187
// stdout: OK rwlock_reader_writer_stress 2 6 1 999\\n
"""

RWLOCK_READER_WRITER_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/rwlock.ax",
]

RWLOCK_READER_WRITER_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.rwlock.RwLock
use std.thread.spawn

@intrinsic fn panic(msg: str) {}

fn check(id: i64, cond: bool) {
    if !cond {
        panic("check failed");
    }
}

@repr(C)
struct DataInvariant {
    pub a: i64,
    pub b: i64,
    pub sum: i64,
    pub write_version: i64,
}

pub fn main() -> i32 {
    let init_data = DataInvariant {
        a: 10i64,
        b: 20i64,
        sum: 30i64,
        write_version: 1i64,
    };
    let rw = Arc.new(RwLock.new(init_data));
    let p_rw = view(rw).as_ptr();
    {
        let mut wg = RwLock.write_ptr(p_rw);
        unsafe {
            *wg.data_ptr = DataInvariant { a: 10i64, b: 20i64, sum: 30i64, write_version: 1i64 };
        }
        drop(wg);
    }

    // -------------------------------------------------------------
    // Phase 1: Reader-heavy concurrent access (4 concurrent readers)
    // -------------------------------------------------------------
    let r1 = view(rw).clone();
    let r2 = view(rw).clone();
    let r3 = view(rw).clone();
    let r4 = view(rw).clone();

    let hr1 = spawn(|| -> i64 {
        let p = view(r1).as_ptr();
        let rg = RwLock.read_ptr(p);
        let ptr = rg.data_ptr;
        let s = unsafe { (*ptr).sum };
        drop(rg);
        s
    });

    let hr2 = spawn(|| -> i64 {
        let p = view(r2).as_ptr();
        let rg = RwLock.read_ptr(p);
        let ptr = rg.data_ptr;
        let s = unsafe { (*ptr).sum };
        drop(rg);
        s
    });

    let hr3 = spawn(|| -> i64 {
        let p = view(r3).as_ptr();
        let rg = RwLock.read_ptr(p);
        let ptr = rg.data_ptr;
        let s = unsafe { (*ptr).sum };
        drop(rg);
        s
    });

    let hr4 = spawn(|| -> i64 {
        let p = view(r4).as_ptr();
        let rg = RwLock.read_ptr(p);
        let ptr = rg.data_ptr;
        let s = unsafe { (*ptr).sum };
        drop(rg);
        s
    });

    let s1 = match hr1.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let s2 = match hr2.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let s3 = match hr3.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    let s4 = match hr4.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
    check(1i64, s1 == 30i64 && s2 == 30i64 && s3 == 30i64 && s4 == 30i64);

    // -------------------------------------------------------------
    // Phase 2: Writers updating state
    // -------------------------------------------------------------
    let w1 = view(rw).clone();
    let hw1 = spawn(|| -> i64 {
        let p = view(w1).as_ptr();
        let mut wg = RwLock.write_ptr(p);
        let ptr = wg.data_ptr;
        unsafe {
            (*ptr).a = 50i64;
            (*ptr).sum = (*ptr).a + (*ptr).b;
            (*ptr).write_version = 2i64;
        }
        drop(wg);
        2i64
    });
    let _ = hw1.join();

    let rg_check1 = RwLock.read_ptr(p_rw);
    let v1 = unsafe { (*rg_check1.data_ptr).write_version };
    check(2i64, v1 == 2i64);
    check(3i64, unsafe { (*rg_check1.data_ptr).sum } == 70i64);
    drop(rg_check1);

    // -------------------------------------------------------------
    // Phase 3: Writer-heavy contention
    // 4 concurrent writers competing for exclusive write access
    // -------------------------------------------------------------
    let w_a = view(rw).clone();
    let w_b = view(rw).clone();
    let w_c = view(rw).clone();
    let w_d = view(rw).clone();

    let hwa = spawn(|| -> i64 {
        let p = view(w_a).as_ptr();
        let mut wg = RwLock.write_ptr(p);
        let ptr = wg.data_ptr;
        unsafe {
            (*ptr).a = (*ptr).a + 1i64;
            (*ptr).sum = (*ptr).a + (*ptr).b;
            (*ptr).write_version = (*ptr).write_version + 1i64;
        }
        drop(wg);
        1i64
    });

    let hwb = spawn(|| -> i64 {
        let p = view(w_b).as_ptr();
        let mut wg = RwLock.write_ptr(p);
        let ptr = wg.data_ptr;
        unsafe {
            (*ptr).b = (*ptr).b + 1i64;
            (*ptr).sum = (*ptr).a + (*ptr).b;
            (*ptr).write_version = (*ptr).write_version + 1i64;
        }
        drop(wg);
        1i64
    });

    let hwc = spawn(|| -> i64 {
        let p = view(w_c).as_ptr();
        let mut wg = RwLock.write_ptr(p);
        let ptr = wg.data_ptr;
        unsafe {
            (*ptr).a = (*ptr).a + 2i64;
            (*ptr).sum = (*ptr).a + (*ptr).b;
            (*ptr).write_version = (*ptr).write_version + 1i64;
        }
        drop(wg);
        1i64
    });

    let hwd = spawn(|| -> i64 {
        let p = view(w_d).as_ptr();
        let mut wg = RwLock.write_ptr(p);
        let ptr = wg.data_ptr;
        unsafe {
            (*ptr).b = (*ptr).b + 2i64;
            (*ptr).sum = (*ptr).a + (*ptr).b;
            (*ptr).write_version = (*ptr).write_version + 1i64;
        }
        drop(wg);
        1i64
    });

    let _ = hwa.join();
    let _ = hwb.join();
    let _ = hwc.join();
    let _ = hwd.join();

    let rg_check2 = RwLock.read_ptr(p_rw);
    let v2 = unsafe { (*rg_check2.data_ptr).write_version };
    check(4i64, v2 == 6i64);
    check(5i64, unsafe { (*rg_check2.data_ptr).a } == 53i64);
    check(6i64, unsafe { (*rg_check2.data_ptr).b } == 23i64);
    check(7i64, unsafe { (*rg_check2.data_ptr).sum } == 76i64);
    drop(rg_check2);

    // -------------------------------------------------------------
    // Phase 4: try_read and try_write while locked
    // -------------------------------------------------------------
    let wg_held = RwLock.write_ptr(p_rw);
    match RwLock.try_read_ptr(p_rw) {
        Option.Some(_rg) => check(8i64, false),
        Option.None => {},
    }
    match RwLock.try_write_ptr(p_rw) {
        Option.Some(_wg2) => check(9i64, false),
        Option.None => {},
    }
    drop(wg_held);

    // try_read while unlocked succeeds
    match RwLock.try_read_ptr(p_rw) {
        Option.Some(rg) => {
            check(10i64, unsafe { (*rg.data_ptr).write_version } == 6i64);
            drop(rg);
        },
        Option.None => check(11i64, false),
    }

    print("OK rwlock_reader_writer_stress ");
    print_int(v1);
    print(" ");
    print_int(v2);
    print(" 1 999\\n");
    0
}
"""

# -------------------------------------------------------------
# 3. Condvar Bounded Work Queue + Barrier Rendezvous
# -------------------------------------------------------------
CONDVAR_BARRIER_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-036 REQ-CONC-039 REQ-CONC-187
// stdout: OK condvar_barrier_work_queue 820 3 1 999\\n
"""

CONDVAR_BARRIER_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/mutex.ax",
    "std/sync/condvar.ax",
    "std/sync/barrier.ax",
]

CONDVAR_BARRIER_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.sync.mutex.Mutex
use std.sync.condvar.Condvar
use std.sync.condvar.CondvarWaitResult
use std.sync.barrier.Barrier
use std.thread.spawn

@intrinsic fn panic(msg: str) {}

fn check(cond: bool) {
    if !cond {
        panic("check failed");
    }
}

pub fn main() -> i32 {
    // -------------------------------------------------------------
    // Part 1: Condvar Work Signaling
    // Producer pushes items, Consumer waits and processes
    // -------------------------------------------------------------
    let work_val = Arc.new(Mutex.new(0i64));
    let cond = Arc.new(Condvar.new());

    let w_c = view(work_val).clone();
    let c_c = view(cond).clone();

    let h_worker = spawn(|| -> i64 {
        let p_m = view(w_c).as_ptr();
        let p_cv = view(c_c).as_ptr();

        let mut g = Mutex.lock_ptr(p_m);
        while g.val() == 0i64 {
            g = Condvar.wait_ptr(p_cv, g);
        }
        let out = g.val();
        drop(g);
        out
    });

    {
        let p_m = view(work_val).as_ptr();
        let p_cv = view(cond).as_ptr();
        let mut g = Mutex.lock_ptr(p_m);
        g.set(820i64);
        drop(g);
        Condvar.notify_one_ptr(p_cv);
    }

    let processed = match h_worker.join() {
        Result.Ok(v) => v,
        Result.Err(_e) => -1i64,
    };
    check(processed == 820i64);

    // Condvar timed wait
    let p_m = view(work_val).as_ptr();
    let p_cv = view(cond).as_ptr();
    let g_to = Mutex.lock_ptr(p_m);
    let wait_res = Condvar.wait_timeout_ms_ptr(p_cv, g_to, 5u64);
    check(wait_res.is_timed_out());
    drop(wait_res.guard);

    // -------------------------------------------------------------
    // Part 2: Barrier Rendezvous across 4 threads
    // -------------------------------------------------------------
    let barrier = Arc.new(Barrier.new(4usize));
    let leader_count = Arc.new(Atomic.new(0i64));

    let b1 = view(barrier).clone();
    let b2 = view(barrier).clone();
    let b3 = view(barrier).clone();
    let b4 = view(barrier).clone();

    let l1 = view(leader_count).clone();
    let l2 = view(leader_count).clone();
    let l3 = view(leader_count).clone();
    let l4 = view(leader_count).clone();

    let hb1 = spawn(|| -> i64 {
        let p_b = view(b1).as_ptr();
        let p_l = view(l1).as_ptr();
        let r1 = Barrier.wait_ptr(p_b);
        if r1.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        let r2 = Barrier.wait_ptr(p_b);
        if r2.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        let r3 = Barrier.wait_ptr(p_b);
        if r3.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        0i64
    });

    let hb2 = spawn(|| -> i64 {
        let p_b = view(b2).as_ptr();
        let p_l = view(l2).as_ptr();
        let r1 = Barrier.wait_ptr(p_b);
        if r1.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        let r2 = Barrier.wait_ptr(p_b);
        if r2.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        let r3 = Barrier.wait_ptr(p_b);
        if r3.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        0i64
    });

    let hb3 = spawn(|| -> i64 {
        let p_b = view(b3).as_ptr();
        let p_l = view(l3).as_ptr();
        let r1 = Barrier.wait_ptr(p_b);
        if r1.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        let r2 = Barrier.wait_ptr(p_b);
        if r2.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        let r3 = Barrier.wait_ptr(p_b);
        if r3.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        0i64
    });

    let hb4 = spawn(|| -> i64 {
        let p_b = view(b4).as_ptr();
        let p_l = view(l4).as_ptr();
        let r1 = Barrier.wait_ptr(p_b);
        if r1.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        let r2 = Barrier.wait_ptr(p_b);
        if r2.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        let r3 = Barrier.wait_ptr(p_b);
        if r3.is_leader() { let _ = unsafe { (*p_l).fetch_add(1i64, Ordering.SeqCst) }; }
        0i64
    });

    let _ = hb1.join();
    let _ = hb2.join();
    let _ = hb3.join();
    let _ = hb4.join();

    let total_leaders = unsafe { (*view(leader_count).as_ptr()).load(Ordering.SeqCst) };
    check(total_leaders == 3i64);

    print("OK condvar_barrier_work_queue ");
    print_int(processed);
    print(" ");
    print_int(total_leaders);
    print(" 1 999\\n");
    0
}
"""

# -------------------------------------------------------------
# 4. Once and OnceCell Concurrent Initialization Race
# -------------------------------------------------------------
ONCE_CONCURRENT_INIT_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-036 REQ-CONC-039 REQ-CONC-187
// stdout: OK once_concurrent_init_stress 1 424242 1 7 999\\n
"""

ONCE_CONCURRENT_INIT_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/once.ax",
]

ONCE_CONCURRENT_INIT_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.sync.once.Once
use std.sync.once.OnceCell
use std.thread.spawn

@intrinsic fn panic(msg: str) {}

fn check(cond: bool) {
    if !cond {
        panic("check failed");
    }
}

pub fn main() -> i32 {
    let once_run_count = Arc.new(Atomic.new(0usize));
    let once_pub_data = Arc.new(Atomic.new(0i64));

    // -------------------------------------------------------------
    // Part 1: Once.call_once across 8 racing threads
    // -------------------------------------------------------------
    let o = Arc.new(Once.new());
    let o0 = view(o).clone();
    let o1 = view(o).clone();
    let o2 = view(o).clone();
    let o3 = view(o).clone();
    let o4 = view(o).clone();
    let o5 = view(o).clone();
    let o6 = view(o).clone();
    let o7 = view(o).clone();

    let rc0 = view(once_run_count).clone();
    let rc1 = view(once_run_count).clone();
    let rc2 = view(once_run_count).clone();
    let rc3 = view(once_run_count).clone();
    let rc4 = view(once_run_count).clone();
    let rc5 = view(once_run_count).clone();
    let rc6 = view(once_run_count).clone();
    let rc7 = view(once_run_count).clone();

    let pd0 = view(once_pub_data).clone();
    let pd1 = view(once_pub_data).clone();
    let pd2 = view(once_pub_data).clone();
    let pd3 = view(once_pub_data).clone();
    let pd4 = view(once_pub_data).clone();
    let pd5 = view(once_pub_data).clone();
    let pd6 = view(once_pub_data).clone();
    let pd7 = view(once_pub_data).clone();

    let ho0 = spawn(|| -> i64 {
        let p = view(o0).as_ptr();
        let p_rc = view(rc0).as_ptr();
        let p_pd = view(pd0).as_ptr();
        Once.call_once_ptr(p, || {
            unsafe {
                (*p_rc).fetch_add(1usize, Ordering.SeqCst);
                (*p_pd).store(424242i64, Ordering.Release);
            }
        });
        1i64
    });

    let ho1 = spawn(|| -> i64 {
        let p = view(o1).as_ptr();
        let p_rc = view(rc1).as_ptr();
        let p_pd = view(pd1).as_ptr();
        Once.call_once_ptr(p, || {
            unsafe {
                (*p_rc).fetch_add(1usize, Ordering.SeqCst);
                (*p_pd).store(424242i64, Ordering.Release);
            }
        });
        1i64
    });

    let ho2 = spawn(|| -> i64 {
        let p = view(o2).as_ptr();
        let p_rc = view(rc2).as_ptr();
        let p_pd = view(pd2).as_ptr();
        Once.call_once_ptr(p, || {
            unsafe {
                (*p_rc).fetch_add(1usize, Ordering.SeqCst);
                (*p_pd).store(424242i64, Ordering.Release);
            }
        });
        1i64
    });

    let ho3 = spawn(|| -> i64 {
        let p = view(o3).as_ptr();
        let p_rc = view(rc3).as_ptr();
        let p_pd = view(pd3).as_ptr();
        Once.call_once_ptr(p, || {
            unsafe {
                (*p_rc).fetch_add(1usize, Ordering.SeqCst);
                (*p_pd).store(424242i64, Ordering.Release);
            }
        });
        1i64
    });

    let ho4 = spawn(|| -> i64 {
        let p = view(o4).as_ptr();
        let p_rc = view(rc4).as_ptr();
        let p_pd = view(pd4).as_ptr();
        Once.call_once_ptr(p, || {
            unsafe {
                (*p_rc).fetch_add(1usize, Ordering.SeqCst);
                (*p_pd).store(424242i64, Ordering.Release);
            }
        });
        1i64
    });

    let ho5 = spawn(|| -> i64 {
        let p = view(o5).as_ptr();
        let p_rc = view(rc5).as_ptr();
        let p_pd = view(pd5).as_ptr();
        Once.call_once_ptr(p, || {
            unsafe {
                (*p_rc).fetch_add(1usize, Ordering.SeqCst);
                (*p_pd).store(424242i64, Ordering.Release);
            }
        });
        1i64
    });

    let ho6 = spawn(|| -> i64 {
        let p = view(o6).as_ptr();
        let p_rc = view(rc6).as_ptr();
        let p_pd = view(pd6).as_ptr();
        Once.call_once_ptr(p, || {
            unsafe {
                (*p_rc).fetch_add(1usize, Ordering.SeqCst);
                (*p_pd).store(424242i64, Ordering.Release);
            }
        });
        1i64
    });

    let ho7 = spawn(|| -> i64 {
        let p = view(o7).as_ptr();
        let p_rc = view(rc7).as_ptr();
        let p_pd = view(pd7).as_ptr();
        Once.call_once_ptr(p, || {
            unsafe {
                (*p_rc).fetch_add(1usize, Ordering.SeqCst);
                (*p_pd).store(424242i64, Ordering.Release);
            }
        });
        1i64
    });

    let _ = ho0.join();
    let _ = ho1.join();
    let _ = ho2.join();
    let _ = ho3.join();
    let _ = ho4.join();
    let _ = ho5.join();
    let _ = ho6.join();
    let _ = ho7.join();

    let run_cnt = unsafe { (*view(once_run_count).as_ptr()).load(Ordering.SeqCst) };
    check(run_cnt == 1usize);

    let pub_data = unsafe { (*view(once_pub_data).as_ptr()).load(Ordering.Acquire) };
    check(pub_data == 424242i64);
    check(Once.is_completed_ptr(view(o).as_ptr()));

    // -------------------------------------------------------------
    // Part 2: OnceCell.set race across 8 threads
    // Exactly 1 winner, 7 losers receiving their value back in Err
    // -------------------------------------------------------------
    let cell_win_count = Arc.new(Atomic.new(0usize));
    let cell_err_count = Arc.new(Atomic.new(0usize));

    let wc0 = view(cell_win_count).clone();
    let wc1 = view(cell_win_count).clone();
    let wc2 = view(cell_win_count).clone();
    let wc3 = view(cell_win_count).clone();
    let wc4 = view(cell_win_count).clone();
    let wc5 = view(cell_win_count).clone();
    let wc6 = view(cell_win_count).clone();
    let wc7 = view(cell_win_count).clone();

    let ec0 = view(cell_err_count).clone();
    let ec1 = view(cell_err_count).clone();
    let ec2 = view(cell_err_count).clone();
    let ec3 = view(cell_err_count).clone();
    let ec4 = view(cell_err_count).clone();
    let ec5 = view(cell_err_count).clone();
    let ec6 = view(cell_err_count).clone();
    let ec7 = view(cell_err_count).clone();

    let cell: Arc<OnceCell<i64>> = Arc.new(OnceCell.new());
    let c0 = view(cell).clone();
    let c1 = view(cell).clone();
    let c2 = view(cell).clone();
    let c3 = view(cell).clone();
    let c4 = view(cell).clone();
    let c5 = view(cell).clone();
    let c6 = view(cell).clone();
    let c7 = view(cell).clone();

    let hc0 = spawn(|| -> i64 {
        let p = view(c0).as_ptr();
        let p_wc = view(wc0).as_ptr();
        let p_ec = view(ec0).as_ptr();
        match OnceCell.set_ptr(p, 100i64) {
            Result.Ok(_) => unsafe { (*p_wc).fetch_add(1usize, Ordering.SeqCst); },
            Result.Err(_rej) => unsafe { (*p_ec).fetch_add(1usize, Ordering.SeqCst); },
        }
        1i64
    });

    let hc1 = spawn(|| -> i64 {
        let p = view(c1).as_ptr();
        let p_wc = view(wc1).as_ptr();
        let p_ec = view(ec1).as_ptr();
        match OnceCell.set_ptr(p, 200i64) {
            Result.Ok(_) => unsafe { (*p_wc).fetch_add(1usize, Ordering.SeqCst); },
            Result.Err(_rej) => unsafe { (*p_ec).fetch_add(1usize, Ordering.SeqCst); },
        }
        1i64
    });

    let hc2 = spawn(|| -> i64 {
        let p = view(c2).as_ptr();
        let p_wc = view(wc2).as_ptr();
        let p_ec = view(ec2).as_ptr();
        match OnceCell.set_ptr(p, 300i64) {
            Result.Ok(_) => unsafe { (*p_wc).fetch_add(1usize, Ordering.SeqCst); },
            Result.Err(_rej) => unsafe { (*p_ec).fetch_add(1usize, Ordering.SeqCst); },
        }
        1i64
    });

    let hc3 = spawn(|| -> i64 {
        let p = view(c3).as_ptr();
        let p_wc = view(wc3).as_ptr();
        let p_ec = view(ec3).as_ptr();
        match OnceCell.set_ptr(p, 400i64) {
            Result.Ok(_) => unsafe { (*p_wc).fetch_add(1usize, Ordering.SeqCst); },
            Result.Err(_rej) => unsafe { (*p_ec).fetch_add(1usize, Ordering.SeqCst); },
        }
        1i64
    });

    let hc4 = spawn(|| -> i64 {
        let p = view(c4).as_ptr();
        let p_wc = view(wc4).as_ptr();
        let p_ec = view(ec4).as_ptr();
        match OnceCell.set_ptr(p, 500i64) {
            Result.Ok(_) => unsafe { (*p_wc).fetch_add(1usize, Ordering.SeqCst); },
            Result.Err(_rej) => unsafe { (*p_ec).fetch_add(1usize, Ordering.SeqCst); },
        }
        1i64
    });

    let hc5 = spawn(|| -> i64 {
        let p = view(c5).as_ptr();
        let p_wc = view(wc5).as_ptr();
        let p_ec = view(ec5).as_ptr();
        match OnceCell.set_ptr(p, 600i64) {
            Result.Ok(_) => unsafe { (*p_wc).fetch_add(1usize, Ordering.SeqCst); },
            Result.Err(_rej) => unsafe { (*p_ec).fetch_add(1usize, Ordering.SeqCst); },
        }
        1i64
    });

    let hc6 = spawn(|| -> i64 {
        let p = view(c6).as_ptr();
        let p_wc = view(wc6).as_ptr();
        let p_ec = view(ec6).as_ptr();
        match OnceCell.set_ptr(p, 700i64) {
            Result.Ok(_) => unsafe { (*p_wc).fetch_add(1usize, Ordering.SeqCst); },
            Result.Err(_rej) => unsafe { (*p_ec).fetch_add(1usize, Ordering.SeqCst); },
        }
        1i64
    });

    let hc7 = spawn(|| -> i64 {
        let p = view(c7).as_ptr();
        let p_wc = view(wc7).as_ptr();
        let p_ec = view(ec7).as_ptr();
        match OnceCell.set_ptr(p, 800i64) {
            Result.Ok(_) => unsafe { (*p_wc).fetch_add(1usize, Ordering.SeqCst); },
            Result.Err(_rej) => unsafe { (*p_ec).fetch_add(1usize, Ordering.SeqCst); },
        }
        1i64
    });

    let _ = hc0.join();
    let _ = hc1.join();
    let _ = hc2.join();
    let _ = hc3.join();
    let _ = hc4.join();
    let _ = hc5.join();
    let _ = hc6.join();
    let _ = hc7.join();

    let win_cnt = unsafe { (*view(cell_win_count).as_ptr()).load(Ordering.SeqCst) };
    let err_cnt = unsafe { (*view(cell_err_count).as_ptr()).load(Ordering.SeqCst) };
    check(win_cnt == 1usize);
    check(err_cnt == 7usize);

    let p_cell = view(cell).as_ptr();
    check(OnceCell.is_initialized_ptr(p_cell));
    let cell_val = match OnceCell.val_ptr(p_cell) {
        Option.Some(v) => v,
        Option.None => 0i64,
    };
    check(cell_val >= 100i64 && cell_val <= 800i64);

    print("OK once_concurrent_init_stress ");
    print_int(run_cnt as i64);
    print(" ");
    print_int(pub_data);
    print(" ");
    print_int(win_cnt as i64);
    print(" ");
    print_int(err_cnt as i64);
    print(" 999\\n");
    0
}
"""

# -------------------------------------------------------------
# 5. Channel MPMC Pipeline with Drop Destruction Stress
# -------------------------------------------------------------
CHANNEL_MPMC_DROP_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-038 REQ-CONC-187
// stdout: OK channel_mpmc_drop_stress 100 9 40 999\\n
"""

CHANNEL_MPMC_DROP_SOURCES = COMMON_PREREQS + [
    "std/sync/channel/mod.ax",
]

CHANNEL_MPMC_DROP_MAIN = """module main

use std.core.result.Result
use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.sync.channel.channel_bounded_with_drop
use std.sync.channel.channel_unbounded_with_drop
use std.sync.channel.RecvError
use std.thread.spawn

@intrinsic fn panic(msg: str) {}
@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }
@intrinsic unsafe fn drop_in_place<T>(p: *mut T) {}

fn check(id: i64, cond: bool) {
    if !cond {
        panic("check failed");
    }
}

@repr(C)
struct DropPayload {
    pub p_dc: usize,
    pub id: i64,
}
impl !Copy for DropPayload {}
unsafe impl Send for DropPayload {}

impl Drop for DropPayload {
    fn drop(self: mut_view<DropPayload>) {
        let p = self.p_dc as *mut Atomic<usize>;
        if (p as usize) != 0usize {
            unsafe {
                (*p).fetch_add(1usize, Ordering.Relaxed);
            }
        }
    }
}

fn drop_payload_glue(ptr: *mut u8) -> () {
    if (ptr as usize) != 0usize {
        unsafe {
            drop_in_place<DropPayload>(ptr as *mut DropPayload);
        }
    }
}

pub fn main() -> i32 {
    // -------------------------------------------------------------
    // Part 1: Bounded MPMC Pipeline (4 producers, 4 consumers, cap 4)
    // -------------------------------------------------------------
    let mut dc1: Atomic<usize> = Atomic.new(0usize);
    let p_dc1_u: usize = (unsafe { address_of_mut(dc1) }) as usize;

    {
        let chan1 = channel_bounded_with_drop<DropPayload>(4usize, drop_payload_glue);
        let tx = chan1.tx;
        let rx = chan1.rx;

        let tx0 = view(tx).clone();
        let tx1 = view(tx).clone();
        let tx2 = view(tx).clone();
        let tx3 = tx;

        let rx0 = view(rx).clone();
        let rx1 = view(rx).clone();
        let rx2 = view(rx).clone();
        let rx3 = rx;

        // 4 Producers sending 25 items each (total 100)
        let hp0 = spawn(|| -> i64 {
            let mut i: i64 = 1i64;
            while i <= 25i64 {
                let it = DropPayload { p_dc: p_dc1_u, id: 1000i64 + i };
                let _ = view(tx0).send(it);
                i = i + 1i64;
            }
            drop(tx0);
            25i64
        });

        let hp1 = spawn(|| -> i64 {
            let mut i: i64 = 1i64;
            while i <= 25i64 {
                let it = DropPayload { p_dc: p_dc1_u, id: 2000i64 + i };
                let _ = view(tx1).send(it);
                i = i + 1i64;
            }
            drop(tx1);
            25i64
        });

        let hp2 = spawn(|| -> i64 {
            let mut i: i64 = 1i64;
            while i <= 25i64 {
                let it = DropPayload { p_dc: p_dc1_u, id: 3000i64 + i };
                let _ = view(tx2).send(it);
                i = i + 1i64;
            }
            drop(tx2);
            25i64
        });

        let hp3 = spawn(|| -> i64 {
            let mut i: i64 = 1i64;
            while i <= 25i64 {
                let it = DropPayload { p_dc: p_dc1_u, id: 4000i64 + i };
                let _ = view(tx3).send(it);
                i = i + 1i64;
            }
            drop(tx3);
            25i64
        });

        // 4 Consumers receiving and dropping items
        let hc0 = spawn(|| -> i64 {
            let mut count: i64 = 0i64;
            while true {
                match view(rx0).recv() {
                    Result.Ok(item) => {
                        drop(item);
                        count = count + 1i64;
                    },
                    Result.Err(RecvError.Disconnected) => { break; },
                }
            }
            drop(rx0);
            count
        });

        let hc1 = spawn(|| -> i64 {
            let mut count: i64 = 0i64;
            while true {
                match view(rx1).recv() {
                    Result.Ok(item) => {
                        drop(item);
                        count = count + 1i64;
                    },
                    Result.Err(RecvError.Disconnected) => { break; },
                }
            }
            drop(rx1);
            count
        });

        let hc2 = spawn(|| -> i64 {
            let mut count: i64 = 0i64;
            while true {
                match view(rx2).recv() {
                    Result.Ok(item) => {
                        drop(item);
                        count = count + 1i64;
                    },
                    Result.Err(RecvError.Disconnected) => { break; },
                }
            }
            drop(rx2);
            count
        });

        let hc3 = spawn(|| -> i64 {
            let mut count: i64 = 0i64;
            while true {
                match view(rx3).recv() {
                    Result.Ok(item) => {
                        drop(item);
                        count = count + 1i64;
                    },
                    Result.Err(RecvError.Disconnected) => { break; },
                }
            }
            drop(rx3);
            count
        });

        let _ = hp0.join();
        let _ = hp1.join();
        let _ = hp2.join();
        let _ = hp3.join();

        let c0 = match hc0.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
        let c1 = match hc1.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
        let c2 = match hc2.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
        let c3 = match hc3.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };

        let total_recv = c0 + c1 + c2 + c3;
        check(1i64, total_recv == 100i64);
    }

    let p_dc1 = p_dc1_u as *mut Atomic<usize>;
    let drops1 = unsafe { (*p_dc1).load(Ordering.Relaxed) };
    check(2i64, drops1 == 100usize);

    // -------------------------------------------------------------
    // Part 2: Bounded Channel Teardown Drop (Queue holding unconsumed items)
    // -------------------------------------------------------------
    let mut dc2: Atomic<usize> = Atomic.new(0usize);
    let p_dc2_u: usize = (unsafe { address_of_mut(dc2) }) as usize;

    {
        let chan2 = channel_bounded_with_drop<DropPayload>(10usize, drop_payload_glue);
        let tx2 = chan2.tx;
        let rx2 = chan2.rx;

        let mut j: i64 = 0i64;
        while j < 8i64 {
            let it = DropPayload { p_dc: p_dc2_u, id: 5000i64 + j };
            let _ = view(tx2).send(it);
            j = j + 1i64;
        }

        // Receive 2 items and drop them (dc2 -> 2)
        match view(rx2).recv() {
            Result.Ok(it1) => drop(it1),
            _ => check(3i64, false),
        }
        match view(rx2).recv() {
            Result.Ok(it2) => drop(it2),
            _ => check(4i64, false),
        }
        let p_dc2 = p_dc2_u as *mut Atomic<usize>;
        check(5i64, unsafe { (*p_dc2).load(Ordering.Relaxed) } == 2usize);

        // Dropping rx2 with 6 items left in the queue MUST drain and drop all 6!
        drop(rx2);
        check(6i64, unsafe { (*p_dc2).load(Ordering.Relaxed) } == 8usize);

        // Sending into closed channel returns rejected item in SendError(val)
        let rejected = DropPayload { p_dc: p_dc2_u, id: 9999i64 };
        match view(tx2).send(rejected) {
            Result.Err(err) => {
                drop(err);
            },
            _ => check(7i64, false),
        }
        check(8i64, unsafe { (*p_dc2).load(Ordering.Relaxed) } == 9usize);
    }
    let p_dc2 = p_dc2_u as *mut Atomic<usize>;
    let drops2 = unsafe { (*p_dc2).load(Ordering.Relaxed) };
    check(9i64, drops2 == 9usize);

    // -------------------------------------------------------------
    // Part 3: Unbounded Pipeline (2 producers -> 2 workers -> 2 consumers)
    // -------------------------------------------------------------
    let mut dc3: Atomic<usize> = Atomic.new(0usize);
    let p_dc3_u: usize = (unsafe { address_of_mut(dc3) }) as usize;

    {
        let chan_in = channel_unbounded_with_drop<DropPayload>(drop_payload_glue);
        let tx_in = chan_in.tx;
        let rx_in = chan_in.rx;

        let chan_out = channel_unbounded_with_drop<DropPayload>(drop_payload_glue);
        let tx_out = chan_out.tx;
        let rx_out = chan_out.rx;

        let tx_in0 = view(tx_in).clone();
        let tx_in1 = tx_in;

        let rx_in0 = view(rx_in).clone();
        let rx_in1 = rx_in;

        let tx_out0 = view(tx_out).clone();
        let tx_out1 = tx_out;

        let rx_out0 = view(rx_out).clone();
        let rx_out1 = rx_out;

        // 2 Producers sending 20 items each (total 40 items)
        let hp_u0 = spawn(|| -> i64 {
            let mut i: i64 = 1i64;
            while i <= 20i64 {
                let it = DropPayload { p_dc: p_dc3_u, id: 6000i64 + i };
                let _ = view(tx_in0).send(it);
                i = i + 1i64;
            }
            drop(tx_in0);
            20i64
        });

        let hp_u1 = spawn(|| -> i64 {
            let mut i: i64 = 1i64;
            while i <= 20i64 {
                let it = DropPayload { p_dc: p_dc3_u, id: 7000i64 + i };
                let _ = view(tx_in1).send(it);
                i = i + 1i64;
            }
            drop(tx_in1);
            20i64
        });

        // 2 Workers forwarding from in to out
        let hw_u0 = spawn(|| -> i64 {
            let mut fwd: i64 = 0i64;
            while true {
                match view(rx_in0).recv() {
                    Result.Ok(item) => {
                        let _ = view(tx_out0).send(item);
                        fwd = fwd + 1i64;
                    },
                    Result.Err(RecvError.Disconnected) => { break; },
                }
            }
            drop(rx_in0);
            drop(tx_out0);
            fwd
        });

        let hw_u1 = spawn(|| -> i64 {
            let mut fwd: i64 = 0i64;
            while true {
                match view(rx_in1).recv() {
                    Result.Ok(item) => {
                        let _ = view(tx_out1).send(item);
                        fwd = fwd + 1i64;
                    },
                    Result.Err(RecvError.Disconnected) => { break; },
                }
            }
            drop(rx_in1);
            drop(tx_out1);
            fwd
        });

        // 2 Consumers reading and dropping
        let hc_u0 = spawn(|| -> i64 {
            let mut c: i64 = 0i64;
            while true {
                match view(rx_out0).recv() {
                    Result.Ok(item) => {
                        drop(item);
                        c = c + 1i64;
                    },
                    Result.Err(RecvError.Disconnected) => { break; },
                }
            }
            drop(rx_out0);
            c
        });

        let hc_u1 = spawn(|| -> i64 {
            let mut c: i64 = 0i64;
            while true {
                match view(rx_out1).recv() {
                    Result.Ok(item) => {
                        drop(item);
                        c = c + 1i64;
                    },
                    Result.Err(RecvError.Disconnected) => { break; },
                }
            }
            drop(rx_out1);
            c
        });

        let _ = hp_u0.join();
        let _ = hp_u1.join();
        let _ = hw_u0.join();
        let _ = hw_u1.join();

        let cu0 = match hc_u0.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
        let cu1 = match hc_u1.join() { Result.Ok(v) => v, Result.Err(_e) => -1i64 };
        check(10i64, cu0 + cu1 == 40i64);
    }

    let p_dc3 = p_dc3_u as *mut Atomic<usize>;
    let drops3 = unsafe { (*p_dc3).load(Ordering.Relaxed) };
    check(11i64, drops3 == 40usize);

    print("OK channel_mpmc_drop_stress ");
    print_int(drops1 as i64);
    print(" ");
    print_int(drops2 as i64);
    print(" ");
    print_int(drops3 as i64);
    print(" 999\\n");
    0
}
"""

# -------------------------------------------------------------
# 6. Scoped Threads Stack Borrowing and Panic Containment
# -------------------------------------------------------------
SCOPED_THREADS_PANIC_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-037 REQ-CONC-081 REQ-CONC-187
// stdout: OK scoped_threads_and_panic_containment 360 300 999 12345\\n
"""

SCOPED_THREADS_PANIC_SOURCES = COMMON_PREREQS

SCOPED_THREADS_PANIC_MAIN = """module main

use std.core.result.Result
use std.thread.spawn
use std.thread.scope

@intrinsic fn panic(msg: str) {}
@intrinsic fn assert(cond: bool) {}

fn check(id: i64, cond: bool) {
    if !cond {
        panic("check failed");
    }
}

pub fn main() -> i32 {
    // -------------------------------------------------------------
    // Part 1: Scoped threads borrowing stack data
    // -------------------------------------------------------------
    let stack_data: [8]i64 = [10i64, 20i64, 30i64, 40i64, 50i64, 60i64, 70i64, 80i64];
    let mut slot_a: i64 = 0i64;
    let mut slot_b: i64 = 0i64;

    let read_sum: i64 = scope(|s| -> i64 {
        let v_all = view(stack_data);
        let mv_a = mut_view(slot_a);
        let mv_b = mut_view(slot_b);

        // Readers borrowing shared view
        let r1 = s.spawn(|| -> i64 {
            let arr = *v_all;
            arr[0] + arr[1] + arr[2] + arr[3]
        });
        let r2 = s.spawn(|| -> i64 {
            let arr = *v_all;
            arr[4] + arr[5] + arr[6] + arr[7]
        });

        // Writers mutating disjoint stack slots - left unjoined to test automatic scope join!
        let _w1 = s.spawn(|| {
            *mv_a = 120i64;
        });
        let _w2 = s.spawn(|| {
            *mv_b = 180i64;
        });

        let s1 = match r1.join() {
            Result.Ok(v) => v,
            Result.Err(_e) => -1i64,
        };
        let s2 = match r2.join() {
            Result.Ok(v) => v,
            Result.Err(_e) => -1i64,
        };
        s1 + s2
    });

    check(1i64, read_sum == 360i64);
    let write_sum = slot_a + slot_b;
    check(2i64, write_sum == 300i64);

    // -------------------------------------------------------------
    // Part 2: Panic containment at JoinHandle boundary
    // -------------------------------------------------------------
    let h_panic = spawn(|| -> i64 {
        panic("worker panic containment test");
        0i64
    });
    let panic_tid = view(h_panic).thread().id();
    match h_panic.join() {
        Result.Ok(_v) => check(3i64, false),
        Result.Err(tp) => {
            check(4i64, view(tp).thread_id().eq(view(panic_tid)));
            check(5i64, len(view(tp).message()) > 0usize);
        },
    }

    // Sibling assert(false) panic alongside healthy worker
    let h_assert = spawn(|| -> i64 {
        assert(false);
        100i64
    });
    let assert_tid = view(h_assert).thread().id();

    let h_healthy = spawn(|| -> i64 {
        900i64 + 99i64
    });

    let healthy_res = match h_healthy.join() {
        Result.Ok(val) => val,
        Result.Err(_e) => -1i64,
    };
    check(6i64, healthy_res == 999i64);

    match h_assert.join() {
        Result.Ok(_v) => check(7i64, false),
        Result.Err(tp2) => {
            check(8i64, view(tp2).thread_id().eq(view(assert_tid)));
        },
    }

    // Subsequent spawn after panics still functions correctly
    let h_after = spawn(|| -> i64 {
        12345i64
    });
    let after_res = match h_after.join() {
        Result.Ok(val) => val,
        Result.Err(_e) => -1i64,
    };
    check(9i64, after_res == 12345i64);

    print("OK scoped_threads_and_panic_containment ");
    print_int(read_sum);
    print(" ");
    print_int(write_sum);
    print(" ");
    print_int(healthy_res);
    print(" ");
    print_int(after_res);
    print("\\n");
    0
}
"""

# -------------------------------------------------------------
# 7. @thread_local and LocalKey Multi-Thread Isolation & Drop Cleanup
# -------------------------------------------------------------
TLS_LOCAL_KEY_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-036 REQ-CONC-039 REQ-CONC-187
// stdout: DDDDOK tls_and_local_key_stress 5000 10042 40042 999\\n
"""

TLS_LOCAL_KEY_SOURCES = COMMON_PREREQS

TLS_LOCAL_KEY_MAIN = """module main

use std.core.result.Result
use std.thread.spawn
use std.thread.LocalKey
use std.thread.local_key_new_with_drop

@intrinsic fn panic(msg: str) {}

fn check(id: i64, cond: bool) {
    if !cond {
        panic("check failed");
    }
}

@thread_local static mut TLS_THREAD_COUNTER: i64 = 1000i64;
@thread_local static mut TLS_ACCUMULATOR: i64 = 0i64;

@repr(C)
struct DropGuard {
    pub dummy: i64,
}

fn init_guard() -> DropGuard {
    DropGuard { dummy: 42i64 }
}

fn drop_guard_glue(ptr: *mut u8) -> () {
    print("D");
}

@thread_local static GUARD_KEY: LocalKey<DropGuard> = LocalKey.new_with_drop(init_guard, drop_guard_glue);

pub fn main() -> i32 {
    check(1i64, TLS_THREAD_COUNTER == 1000i64);
    TLS_THREAD_COUNTER = 5000i64;
    check(2i64, TLS_THREAD_COUNTER == 5000i64);

    let th1 = spawn(|| -> i64 {
        check(10i64, TLS_THREAD_COUNTER == 1000i64);
        TLS_THREAD_COUNTER = 10042i64;
        let mut i: i64 = 0i64;
        while i < 20i64 {
            TLS_ACCUMULATOR = TLS_ACCUMULATOR + 1i64;
            i = i + 1i64;
        }
        GUARD_KEY.with(|g| {
            check(11i64, g.dummy == 42i64);
        });
        check(12i64, TLS_THREAD_COUNTER == 10042i64);
        check(13i64, TLS_ACCUMULATOR == 20i64);
        TLS_THREAD_COUNTER
    });

    let th2 = spawn(|| -> i64 {
        check(20i64, TLS_THREAD_COUNTER == 1000i64);
        TLS_THREAD_COUNTER = 20042i64;
        let mut i: i64 = 0i64;
        while i < 20i64 {
            TLS_ACCUMULATOR = TLS_ACCUMULATOR + 2i64;
            i = i + 1i64;
        }
        GUARD_KEY.with(|g| {
            check(21i64, g.dummy == 42i64);
        });
        check(22i64, TLS_THREAD_COUNTER == 20042i64);
        check(23i64, TLS_ACCUMULATOR == 40i64);
        TLS_THREAD_COUNTER
    });

    let th3 = spawn(|| -> i64 {
        check(30i64, TLS_THREAD_COUNTER == 1000i64);
        TLS_THREAD_COUNTER = 30042i64;
        let mut i: i64 = 0i64;
        while i < 20i64 {
            TLS_ACCUMULATOR = TLS_ACCUMULATOR + 3i64;
            i = i + 1i64;
        }
        GUARD_KEY.with(|g| {
            check(31i64, g.dummy == 42i64);
        });
        check(32i64, TLS_THREAD_COUNTER == 30042i64);
        check(33i64, TLS_ACCUMULATOR == 60i64);
        TLS_THREAD_COUNTER
    });

    let th4 = spawn(|| -> i64 {
        check(40i64, TLS_THREAD_COUNTER == 1000i64);
        TLS_THREAD_COUNTER = 40042i64;
        let mut i: i64 = 0i64;
        while i < 20i64 {
            TLS_ACCUMULATOR = TLS_ACCUMULATOR + 4i64;
            i = i + 1i64;
        }
        GUARD_KEY.with(|g| {
            check(41i64, g.dummy == 42i64);
        });
        check(42i64, TLS_THREAD_COUNTER == 40042i64);
        check(43i64, TLS_ACCUMULATOR == 80i64);
        TLS_THREAD_COUNTER
    });

    let r1 = match th1.join() {
        Result.Ok(v) => v,
        Result.Err(_e) => -1i64,
    };
    let r2 = match th2.join() {
        Result.Ok(v) => v,
        Result.Err(_e) => -1i64,
    };
    let r3 = match th3.join() {
        Result.Ok(v) => v,
        Result.Err(_e) => -1i64,
    };
    let r4 = match th4.join() {
        Result.Ok(v) => v,
        Result.Err(_e) => -1i64,
    };

    check(50i64, r1 == 10042i64);
    check(51i64, r2 == 20042i64);
    check(52i64, r3 == 30042i64);
    check(53i64, r4 == 40042i64);

    // Verify main thread TLS state was preserved
    check(60i64, TLS_THREAD_COUNTER == 5000i64);

    print("OK tls_and_local_key_stress ");
    print_int(TLS_THREAD_COUNTER);
    print(" ");
    print_int(r1);
    print(" ");
    print_int(r4);
    print(" 999\\n");
    0
}
"""

# -------------------------------------------------------------
# 8. QA Boundary: Condvar Broadcast, Barrier Single-Thread & Arc Weak Downgrade/Upgrade
# -------------------------------------------------------------
QA_CONDVAR_BROADCAST_WEAK_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-036 REQ-CONC-039 REQ-CONC-187
// stdout: OK qa_condvar_broadcast_weak_stress 4 1 777 0 999\\n
"""

QA_CONDVAR_BROADCAST_WEAK_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/mutex.ax",
    "std/sync/condvar.ax",
    "std/sync/barrier.ax",
]

QA_CONDVAR_BROADCAST_WEAK_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.arc.Weak
use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.sync.mutex.Mutex
use std.sync.condvar.Condvar
use std.sync.barrier.Barrier
use std.thread.spawn
use std.thread.yield_now

@intrinsic fn panic(msg: str) {}

fn check(id: i64, cond: bool) {
    if !cond {
        panic("check failed");
    }
}

pub fn main() -> i32 {
    // -------------------------------------------------------------
    // Part 1: Condvar.notify_all broadcast to 4 waiting threads
    // -------------------------------------------------------------
    let cv_state = Arc.new(Mutex.new(0i64));
    let cond = Arc.new(Condvar.new());
    let waiters_ready = Arc.new(Atomic.new(0i64));
    let woken_count = Arc.new(Atomic.new(0i64));

    let s0 = view(cv_state).clone();
    let s1 = view(cv_state).clone();
    let s2 = view(cv_state).clone();
    let s3 = view(cv_state).clone();

    let c0 = view(cond).clone();
    let c1 = view(cond).clone();
    let c2 = view(cond).clone();
    let c3 = view(cond).clone();

    let wr0 = view(waiters_ready).clone();
    let wr1 = view(waiters_ready).clone();
    let wr2 = view(waiters_ready).clone();
    let wr3 = view(waiters_ready).clone();

    let wk0 = view(woken_count).clone();
    let wk1 = view(woken_count).clone();
    let wk2 = view(woken_count).clone();
    let wk3 = view(woken_count).clone();

    let hw0 = spawn(|| -> i64 {
        let p_m = view(s0).as_ptr();
        let p_c = view(c0).as_ptr();
        let p_wr = view(wr0).as_ptr();
        let p_wk = view(wk0).as_ptr();

        let mut g = Mutex.lock_ptr(p_m);
        unsafe { (*p_wr).fetch_add(1i64, Ordering.SeqCst); }
        while g.val() == 0i64 {
            g = Condvar.wait_ptr(p_c, g);
        }
        check(10i64, g.val() == 42i64);
        drop(g);
        unsafe { (*p_wk).fetch_add(1i64, Ordering.SeqCst); }
        1i64
    });

    let hw1 = spawn(|| -> i64 {
        let p_m = view(s1).as_ptr();
        let p_c = view(c1).as_ptr();
        let p_wr = view(wr1).as_ptr();
        let p_wk = view(wk1).as_ptr();

        let mut g = Mutex.lock_ptr(p_m);
        unsafe { (*p_wr).fetch_add(1i64, Ordering.SeqCst); }
        while g.val() == 0i64 {
            g = Condvar.wait_ptr(p_c, g);
        }
        check(11i64, g.val() == 42i64);
        drop(g);
        unsafe { (*p_wk).fetch_add(1i64, Ordering.SeqCst); }
        1i64
    });

    let hw2 = spawn(|| -> i64 {
        let p_m = view(s2).as_ptr();
        let p_c = view(c2).as_ptr();
        let p_wr = view(wr2).as_ptr();
        let p_wk = view(wk2).as_ptr();

        let mut g = Mutex.lock_ptr(p_m);
        unsafe { (*p_wr).fetch_add(1i64, Ordering.SeqCst); }
        while g.val() == 0i64 {
            g = Condvar.wait_ptr(p_c, g);
        }
        check(12i64, g.val() == 42i64);
        drop(g);
        unsafe { (*p_wk).fetch_add(1i64, Ordering.SeqCst); }
        1i64
    });

    let hw3 = spawn(|| -> i64 {
        let p_m = view(s3).as_ptr();
        let p_c = view(c3).as_ptr();
        let p_wr = view(wr3).as_ptr();
        let p_wk = view(wk3).as_ptr();

        let mut g = Mutex.lock_ptr(p_m);
        unsafe { (*p_wr).fetch_add(1i64, Ordering.SeqCst); }
        while g.val() == 0i64 {
            g = Condvar.wait_ptr(p_c, g);
        }
        check(13i64, g.val() == 42i64);
        drop(g);
        unsafe { (*p_wk).fetch_add(1i64, Ordering.SeqCst); }
        1i64
    });

    // Wait until all 4 threads have acquired lock and entered wait
    let p_wr_main = view(waiters_ready).as_ptr();
    while unsafe { (*p_wr_main).load(Ordering.SeqCst) } < 4i64 {
        yield_now();
    }

    // Acquire lock, update condition value, and broadcast notify_all
    {
        let p_m_main = view(cv_state).as_ptr();
        let p_c_main = view(cond).as_ptr();
        let mut g_main = Mutex.lock_ptr(p_m_main);
        g_main.set(42i64);
        drop(g_main);
        Condvar.notify_all_ptr(p_c_main);
    }

    let _ = hw0.join();
    let _ = hw1.join();
    let _ = hw2.join();
    let _ = hw3.join();

    let total_woken = unsafe { (*view(woken_count).as_ptr()).load(Ordering.SeqCst) };
    check(20i64, total_woken == 4i64);

    // -------------------------------------------------------------
    // Part 2: Boundary case: Single-thread Barrier rendezvous
    // -------------------------------------------------------------
    let b1 = Arc.new(Barrier.new(1usize));
    let p_b1 = view(b1).as_ptr();
    let r1 = Barrier.wait_ptr(p_b1);
    check(25i64, r1.is_leader());
    let r2 = Barrier.wait_ptr(p_b1);
    check(26i64, r2.is_leader());
    drop(b1);

    // -------------------------------------------------------------
    // Part 3: Arc Weak reference downgrade, upgrade, and expiration
    // -------------------------------------------------------------
    let strong_data = Arc.new(777i64);
    let weak_data: Weak<i64> = view(strong_data).downgrade();
    check(30i64, view(strong_data).strong_count() == 1usize);
    check(31i64, view(strong_data).weak_count() == 1usize);

    // Upgrade succeeds while strong ref exists
    let upgraded_val: i64 = match view(weak_data).upgrade() {
        Option.Some(up) => {
            let v = view(up).val();
            drop(up);
            v
        },
        Option.None => 0i64,
    };
    check(32i64, upgraded_val == 777i64);

    // Drop the strong reference
    drop(strong_data);

    // Upgrade MUST fail after strong ref is dropped
    let post_drop_upgrade: i64 = match view(weak_data).upgrade() {
        Option.Some(up) => {
            drop(up);
            -1i64
        },
        Option.None => 0i64,
    };
    check(33i64, post_drop_upgrade == 0i64);
    check(34i64, view(weak_data).strong_count() == 0usize);

    drop(weak_data);

    print("OK qa_condvar_broadcast_weak_stress ");
    print_int(total_woken);
    print(" ");
    print_int(1i64);
    print(" ");
    print_int(upgraded_val);
    print(" ");
    print_int(post_drop_upgrade);
    print(" 999\\n");
    0
}
"""

BUNDLES = {
    "arc_mutex_8thread_stress.ax": (ARC_MUTEX_8THREAD_HEADER, ARC_MUTEX_8THREAD_SOURCES, ARC_MUTEX_8THREAD_MAIN),
    "rwlock_reader_writer_stress.ax": (RWLOCK_READER_WRITER_HEADER, RWLOCK_READER_WRITER_SOURCES, RWLOCK_READER_WRITER_MAIN),
    "condvar_barrier_work_queue.ax": (CONDVAR_BARRIER_HEADER, CONDVAR_BARRIER_SOURCES, CONDVAR_BARRIER_MAIN),
    "once_concurrent_init_stress.ax": (ONCE_CONCURRENT_INIT_HEADER, ONCE_CONCURRENT_INIT_SOURCES, ONCE_CONCURRENT_INIT_MAIN),
    "channel_mpmc_drop_stress.ax": (CHANNEL_MPMC_DROP_HEADER, CHANNEL_MPMC_DROP_SOURCES, CHANNEL_MPMC_DROP_MAIN),
    "scoped_threads_and_panic_containment.ax": (SCOPED_THREADS_PANIC_HEADER, SCOPED_THREADS_PANIC_SOURCES, SCOPED_THREADS_PANIC_MAIN),
    "tls_and_local_key_stress.ax": (TLS_LOCAL_KEY_HEADER, TLS_LOCAL_KEY_SOURCES, TLS_LOCAL_KEY_MAIN),
    "qa_condvar_broadcast_weak_stress.ax": (QA_CONDVAR_BROADCAST_WEAK_HEADER, QA_CONDVAR_BROADCAST_WEAK_SOURCES, QA_CONDVAR_BROADCAST_WEAK_MAIN),
}


def read_source(rel_path):
    full_path = os.path.join(ROOT, rel_path)
    with open(full_path, "r", encoding="utf-8") as f:
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
            print("ERROR: conformance test bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            print("Run `python tests/conformance/p11/e11_3_threads_sync/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK conformance bundles match live std sources\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
