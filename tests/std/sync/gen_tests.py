#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/std/sync (T411).

Generates in-tree test bundles for std.sync primitives by concatenating
verbatim standard library source files from HEAD with test harness logic.
Ensures zero test divergence from live std/sync/*.ax implementations.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

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
# Test Definitions
# -----------------------------------------------------------------------------

RC_BASIC_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-070
// stdout: OK rc_basic 42 100 1 1 777\\n
"""

RC_BASIC_SOURCES = [
    "std/sys/windows/heap.ax",
    "std/sync/rc.ax",
]

RC_BASIC_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.rc.Rc

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub fn main() -> i32 {
    let rc1 = Rc.new(42i64);
    check(view(rc1).strong_count() == 1usize);
    check(view(rc1).weak_count() == 0usize);
    let val1 = unsafe { *(view(rc1).as_ptr()) };
    check(val1 == 42i64);

    let rc2 = view(rc1).clone();
    check(view(rc1).strong_count() == 2usize);
    check(view(rc2).strong_count() == 2usize);
    check(unsafe { *(view(rc2).as_ptr()) } == 42i64);

    let mut rc1_mut = rc1;
    let mut_p = mut_view(rc1_mut).as_mut_ptr();
    check((mut_p as usize) == 0usize);

    drop(rc2);
    check(view(rc1_mut).strong_count() == 1usize);

    let mut_p2 = mut_view(rc1_mut).as_mut_ptr();
    check((mut_p2 as usize) != 0usize);
    unsafe {
        *mut_p2 = 100i64;
    }
    let val_after_mut = unsafe { *(view(rc1_mut).as_ptr()) };
    check(val_after_mut == 100i64);

    let weak1 = view(rc1_mut).downgrade();
    check(view(rc1_mut).weak_count() == 1usize);
    check(view(weak1).strong_count() == 1usize);

    let rc3 = match view(weak1).upgrade() {
        Option.Some(r) => r,
        Option.None => loop {},
    };
    check(view(rc1_mut).strong_count() == 2usize);
    drop(rc3);

    {
        let rc_drop = Rc.new(42i64);
        check(view(rc_drop).strong_count() == 1usize);
        let rc_drop2 = view(rc_drop).clone();
        check(view(rc_drop).strong_count() == 2usize);
        drop(rc_drop2);
        check(view(rc_drop).strong_count() == 1usize);
    }

    let weak_survivor = {
        let rc_temp = Rc.new(999i64);
        view(rc_temp).downgrade()
    };
    match view(weak_survivor).upgrade() {
        Option.Some(_r) => check(false),
        Option.None => {},
    }
    check(view(weak_survivor).strong_count() == 0usize);

    let rc_unwrap = Rc.new(777i64);
    let unwrapped = match rc_unwrap.try_unwrap() {
        Result.Ok(v) => v,
        Result.Err(_r) => -1i64,
    };
    check(unwrapped == 777i64);

    print("OK rc_basic ");
    print_int(val1);
    print(" ");
    print_int(val_after_mut);
    print(" ");
    print_int(view(rc1_mut).strong_count() as i64);
    print(" ");
    print_int(view(rc1_mut).weak_count() as i64);
    print(" ");
    print_int(unwrapped);
    print("\\n");
    0
}
"""

ARC_MUTEX_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-010 REQ-CONC-015 REQ-CONC-044 REQ-CONC-045 REQ-CONC-071 REQ-CONC-105 REQ-CONC-106 REQ-CONC-180
// stdout: OK arc_mutex_threads 100 2 1 777\\n
"""

ARC_MUTEX_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/mutex.ax",
]

ARC_MUTEX_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.mutex.Mutex
use std.thread.spawn

fn check_id(id: i64, cond: bool) {
    if !cond {
        print_int(id);
        loop {}
    }
}

pub fn main() -> i32 {
    let m = Arc.new(Mutex.new(0i64));
    let m1 = view(m).clone();
    let m2 = view(m).clone();
    let m3 = view(m).clone();
    let m4 = view(m).clone();

    let h1 = spawn(|| -> i64 {
        let mut i: i64 = 0i64;
        let p_m1 = view(m1).as_ptr();
        while i < 25i64 {
            let mut g = Mutex.lock_ptr(p_m1);
            let cur_v = g.val();
            g.set(cur_v + 1i64);
            drop(g);
            i = i + 1i64;
        }
        25i64
    });

    let h2 = spawn(|| -> i64 {
        let mut i: i64 = 0i64;
        let p_m2 = view(m2).as_ptr();
        while i < 25i64 {
            let mut g = Mutex.lock_ptr(p_m2);
            let cur_v = g.val();
            g.set(cur_v + 1i64);
            drop(g);
            i = i + 1i64;
        }
        25i64
    });

    let h3 = spawn(|| -> i64 {
        let mut i: i64 = 0i64;
        let p_m3 = view(m3).as_ptr();
        while i < 25i64 {
            let mut g = Mutex.lock_ptr(p_m3);
            let cur_v = g.val();
            g.set(cur_v + 1i64);
            drop(g);
            i = i + 1i64;
        }
        25i64
    });

    let h4 = spawn(|| -> i64 {
        let mut i: i64 = 0i64;
        let p_m4 = view(m4).as_ptr();
        while i < 25i64 {
            let mut g = Mutex.lock_ptr(p_m4);
            let cur_v = g.val();
            g.set(cur_v + 1i64);
            drop(g);
            i = i + 1i64;
        }
        25i64
    });

    let _ = h1.join();
    let _ = h2.join();
    let _ = h3.join();
    let _ = h4.join();

    let p_m = view(m).as_ptr();
    let final_val = Mutex.lock_ptr(p_m).val();
    check_id(1i64, final_val == 100i64);

    // Test try_lock while locked vs unlocked
    {
        let g = Mutex.lock_ptr(p_m);
        match Mutex.try_lock_ptr(p_m) {
            Option.Some(_g2) => check_id(2i64, false),
            Option.None => {},
        }
        drop(g);
    }
    match Mutex.try_lock_ptr(p_m) {
        Option.Some(g) => {
            check_id(3i64, g.val() == 100i64);
            drop(g);
        },
        Option.None => check_id(2i64, false),
    }

    // Test downgrade and upgrade
    let weak = view(m).downgrade();
    check_id(4i64, view(m).strong_count() == 1usize);
    check_id(5i64, view(m).weak_count() == 1usize);

    let up = match view(weak).upgrade() {
        Option.Some(arc_up) => arc_up,
        Option.None => loop {},
    };
    let sc_up = view(m).strong_count();
    check_id(6i64, sc_up == 2usize);
    drop(up);
    let sc_after_up_drop = view(m).strong_count();
    check_id(7i64, sc_after_up_drop == 1usize);
    drop(weak);

    // Test try_unwrap
    let u = Arc.new(777i64);
    let unwrapped_val = match u.try_unwrap() {
        Result.Ok(v) => v,
        Result.Err(_e) => loop {},
    };
    check_id(8i64, unwrapped_val == 777i64);

    print("OK arc_mutex_threads ");
    print_int(final_val);
    print(" ");
    print_int(sc_up as i64);
    print(" ");
    print_int(sc_after_up_drop as i64);
    print(" ");
    print_int(unwrapped_val);
    print("\\n");
    0
}
"""

RWLOCK_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-010 REQ-CONC-046 REQ-CONC-047
// stdout: OK rwlock_readers_writer 42 100 1\\n
"""

RWLOCK_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/rwlock.ax",
]

RWLOCK_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.rwlock.RwLock
use std.thread.spawn

fn check_id(id: i64, cond: bool) {
    if !cond {
        print_int(id);
        loop {}
    }
}

pub fn main() -> i32 {
    let rw = Arc.new(RwLock.new(0i64));
    {
        let mut wg = RwLock.write_ptr(view(rw).as_ptr());
        wg.set(42i64);
        drop(wg);
    }
    let rw1 = view(rw).clone();
    let rw2 = view(rw).clone();
    let rw3 = view(rw).clone();

    // 1. Concurrent readers read initial value 42
    let h_r1 = spawn(|| -> i64 {
        let p_rw1 = view(rw1).as_ptr();
        let rg = RwLock.read_ptr(p_rw1);
        let val = rg.val();
        drop(rg);
        val
    });
    let h_r2 = spawn(|| -> i64 {
        let p_rw2 = view(rw2).as_ptr();
        let rg = RwLock.read_ptr(p_rw2);
        let val = rg.val();
        drop(rg);
        val
    });
    let r1_val = match h_r1.join() {
        Result.Ok(v) => v,
        Result.Err(_e) => 0i64,
    };
    let r2_val = match h_r2.join() {
        Result.Ok(v) => v,
        Result.Err(_e) => 0i64,
    };
    check_id(1i64, r1_val == 42i64);
    check_id(2i64, r2_val == 42i64);

    // 2. Writer thread updates value to 100
    let h_w = spawn(|| -> i64 {
        let p_rw3 = view(rw3).as_ptr();
        let mut wg = RwLock.write_ptr(p_rw3);
        wg.set(100i64);
        drop(wg);
        100i64
    });
    let _ = h_w.join();

    // 3. Reader verifies updated value
    let p_rw = view(rw).as_ptr();
    let post_val = {
        let rg = RwLock.read_ptr(p_rw);
        let v = rg.val();
        drop(rg);
        v
    };
    check_id(3i64, post_val == 100i64);

    // 4. Test try_read and try_write
    {
        let mut wg = RwLock.write_ptr(p_rw);
        match RwLock.try_read_ptr(p_rw) {
            Option.Some(_rg) => check_id(4i64, false),
            Option.None => {},
        }
        match RwLock.try_write_ptr(p_rw) {
            Option.Some(_wg) => check_id(5i64, false),
            Option.None => {},
        }
        drop(wg);
    }
    match RwLock.try_read_ptr(p_rw) {
        Option.Some(rg) => {
            check_id(6i64, rg.val() == 100i64);
            drop(rg);
        },
        Option.None => check_id(7i64, false),
    }

    print("OK rwlock_readers_writer ");
    print_int(r1_val);
    print(" ");
    print_int(post_val);
    print(" 1\\n");
    0
}
"""

CONDVAR_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-010 REQ-CONC-048 REQ-CONC-049
// stdout: OK condvar_signaling 42 1 1\\n
"""

CONDVAR_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/mutex.ax",
    "std/sync/condvar.ax",
]

CONDVAR_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.mutex.Mutex
use std.sync.condvar.Condvar
use std.sync.condvar.CondvarWaitResult
use std.thread.spawn

fn check_id(id: i64, cond: bool) {
    if !cond {
        print_int(id);
        loop {}
    }
}

pub fn main() -> i32 {
    let pair = Arc.new(Mutex.new(0i64));
    let cond = Arc.new(Condvar.new());

    let pair_c = view(pair).clone();
    let cond_c = view(cond).clone();

    // 1. Worker thread waits on condvar until pair data != 0
    let h = spawn(|| -> i64 {
        let p_m = view(pair_c).as_ptr();
        let p_cv = view(cond_c).as_ptr();

        let mut g = Mutex.lock_ptr(p_m);
        while g.val() == 0i64 {
            g = Condvar.wait_ptr(p_cv, g);
        }
        let out = g.val();
        drop(g);
        out
    });

    // 2. Main thread sets value to 42 and notifies worker
    {
        let p_m = view(pair).as_ptr();
        let p_cv = view(cond).as_ptr();
        let mut g = Mutex.lock_ptr(p_m);
        g.set(42i64);
        drop(g);
        Condvar.notify_one_ptr(p_cv);
    }

    let worker_res = match h.join() {
        Result.Ok(v) => v,
        Result.Err(_e) => -1i64,
    };
    check_id(1i64, worker_res == 42i64);

    // 3. Test wait_timeout_ms (timeout expired)
    let p_m2 = view(pair).as_ptr();
    let p_cv2 = view(cond).as_ptr();
    let g2 = Mutex.lock_ptr(p_m2);
    let wait_res = Condvar.wait_timeout_ms_ptr(p_cv2, g2, 5u64);
    let is_to = wait_res.is_timed_out();
    drop(wait_res.guard);
    check_id(2i64, is_to);

    print("OK condvar_signaling ");
    print_int(worker_res);
    print(" 1 1\\n");
    0
}
"""

ONCE_CELL_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-010 REQ-CONC-050 REQ-CONC-051
// stdout: OK once_cell_init 1 1 42\\n
"""

ONCE_CELL_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/mutex.ax",
    "std/sync/once.ax",
]

ONCE_CELL_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.sync.once.Once
use std.sync.once.OnceCell
use std.thread.spawn

fn check_id(id: i64, cond: bool) {
    if !cond {
        print_int(id);
        loop {}
    }
}

pub fn main() -> i32 {
    // -------------------------------------------------------------
    // Part 1: Once.call_once concurrent execution (exactly 1 runner)
    // -------------------------------------------------------------
    let once_obj = Arc.new(Once.new());
    let run_count = Arc.new(Atomic.new(0i64));

    let o1 = view(once_obj).clone();
    let o2 = view(once_obj).clone();
    let o3 = view(once_obj).clone();
    let o4 = view(once_obj).clone();

    let rc1 = view(run_count).clone();
    let rc2 = view(run_count).clone();
    let rc3 = view(run_count).clone();
    let rc4 = view(run_count).clone();

    let h1 = spawn(|| -> i64 {
        let p_o = view(o1).as_ptr();
        let p_rc = view(rc1).as_ptr();
        Once.call_once_ptr(p_o, || {
            let _ = unsafe { (*p_rc).fetch_add(1i64, Ordering.SeqCst) };
        });
        0i64
    });

    let h2 = spawn(|| -> i64 {
        let p_o = view(o2).as_ptr();
        let p_rc = view(rc2).as_ptr();
        Once.call_once_ptr(p_o, || {
            let _ = unsafe { (*p_rc).fetch_add(1i64, Ordering.SeqCst) };
        });
        0i64
    });

    let h3 = spawn(|| -> i64 {
        let p_o = view(o3).as_ptr();
        let p_rc = view(rc3).as_ptr();
        Once.call_once_ptr(p_o, || {
            let _ = unsafe { (*p_rc).fetch_add(1i64, Ordering.SeqCst) };
        });
        0i64
    });

    let h4 = spawn(|| -> i64 {
        let p_o = view(o4).as_ptr();
        let p_rc = view(rc4).as_ptr();
        Once.call_once_ptr(p_o, || {
            let _ = unsafe { (*p_rc).fetch_add(1i64, Ordering.SeqCst) };
        });
        0i64
    });

    let _ = h1.join();
    let _ = h2.join();
    let _ = h3.join();
    let _ = h4.join();

    let p_rc_main = view(run_count).as_ptr();
    let once_runs = unsafe { (*p_rc_main).load(Ordering.SeqCst) };
    check_id(1i64, once_runs == 1i64);
    let p_o_main = view(once_obj).as_ptr();
    check_id(2i64, Once.is_completed_ptr(p_o_main));

    // -------------------------------------------------------------
    // Part 2: OnceCell concurrent race to set value
    // -------------------------------------------------------------
    let cell = Arc.new(OnceCell.new());
    let win_count = Arc.new(Atomic.new(0i64));

    let c1 = view(cell).clone();
    let c2 = view(cell).clone();
    let c3 = view(cell).clone();
    let c4 = view(cell).clone();

    let wc1 = view(win_count).clone();
    let wc2 = view(win_count).clone();
    let wc3 = view(win_count).clone();
    let wc4 = view(win_count).clone();

    let th1 = spawn(|| -> i64 {
        let p_cell = view(c1).as_ptr();
        let p_wc = view(wc1).as_ptr();
        let res = OnceCell.set_ptr(p_cell, 42i64);
        match res {
            Result.Ok(_) => {
                let _ = unsafe { (*p_wc).fetch_add(1i64, Ordering.SeqCst) };
            },
            Result.Err(_v) => {},
        }
        0i64
    });

    let th2 = spawn(|| -> i64 {
        let p_cell = view(c2).as_ptr();
        let p_wc = view(wc2).as_ptr();
        let res = OnceCell.set_ptr(p_cell, 42i64);
        match res {
            Result.Ok(_) => {
                let _ = unsafe { (*p_wc).fetch_add(1i64, Ordering.SeqCst) };
            },
            Result.Err(_v) => {},
        }
        0i64
    });

    let th3 = spawn(|| -> i64 {
        let p_cell = view(c3).as_ptr();
        let p_wc = view(wc3).as_ptr();
        let res = OnceCell.set_ptr(p_cell, 42i64);
        match res {
            Result.Ok(_) => {
                let _ = unsafe { (*p_wc).fetch_add(1i64, Ordering.SeqCst) };
            },
            Result.Err(_v) => {},
        }
        0i64
    });

    let th4 = spawn(|| -> i64 {
        let p_cell = view(c4).as_ptr();
        let p_wc = view(wc4).as_ptr();
        let res = OnceCell.set_ptr(p_cell, 42i64);
        match res {
            Result.Ok(_) => {
                let _ = unsafe { (*p_wc).fetch_add(1i64, Ordering.SeqCst) };
            },
            Result.Err(_v) => {},
        }
        0i64
    });

    let _ = th1.join();
    let _ = th2.join();
    let _ = th3.join();
    let _ = th4.join();

    let p_wc_main = view(win_count).as_ptr();
    let wins = unsafe { (*p_wc_main).load(Ordering.SeqCst) };
    check_id(3i64, wins == 1i64);

    let p_cell_main = view(cell).as_ptr();
    let cell_val = match OnceCell.val_ptr(p_cell_main) {
        Option.Some(v) => v,
        Option.None => -1i64,
    };
    check_id(4i64, cell_val == 42i64);

    print("OK once_cell_init ");
    print_int(once_runs);
    print(" ");
    print_int(wins);
    print(" ");
    print_int(cell_val);
    print("\\n");
    0
}
"""

BARRIER_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-010 REQ-CONC-052
// stdout: OK barrier_rendezvous 1 1 4\\n
"""

BARRIER_SOURCES = COMMON_PREREQS + [
    "std/sync/arc.ax",
    "std/sync/mutex.ax",
    "std/sync/barrier.ax",
]

BARRIER_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.arc.Arc
use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.sync.barrier.Barrier
use std.sync.barrier.BarrierWaitResult
use std.thread.spawn

fn check_id(id: i64, cond: bool) {
    if !cond {
        print_int(id);
        loop {}
    }
}

pub fn main() -> i32 {
    let barrier = Arc.new(Barrier.new(4usize));
    let leader_count1 = Arc.new(Atomic.new(0i64));
    let leader_count2 = Arc.new(Atomic.new(0i64));
    let passed_count = Arc.new(Atomic.new(0i64));

    let b1 = view(barrier).clone();
    let b2 = view(barrier).clone();
    let b3 = view(barrier).clone();
    let b4 = view(barrier).clone();

    let l1_1 = view(leader_count1).clone();
    let l1_2 = view(leader_count1).clone();
    let l1_3 = view(leader_count1).clone();
    let l1_4 = view(leader_count1).clone();

    let l2_1 = view(leader_count2).clone();
    let l2_2 = view(leader_count2).clone();
    let l2_3 = view(leader_count2).clone();
    let l2_4 = view(leader_count2).clone();

    let p1 = view(passed_count).clone();
    let p2 = view(passed_count).clone();
    let p3 = view(passed_count).clone();
    let p4 = view(passed_count).clone();

    let h1 = spawn(|| -> i64 {
        let p_b = view(b1).as_ptr();
        let p_l1 = view(l1_1).as_ptr();
        let p_l2 = view(l2_1).as_ptr();
        let p_p = view(p1).as_ptr();

        let r1 = Barrier.wait_ptr(p_b);
        if r1.is_leader() {
            let _ = unsafe { (*p_l1).fetch_add(1i64, Ordering.SeqCst) };
        }

        let r2 = Barrier.wait_ptr(p_b);
        if r2.is_leader() {
            let _ = unsafe { (*p_l2).fetch_add(1i64, Ordering.SeqCst) };
        }
        let _ = unsafe { (*p_p).fetch_add(1i64, Ordering.SeqCst) };
        0i64
    });

    let h2 = spawn(|| -> i64 {
        let p_b = view(b2).as_ptr();
        let p_l1 = view(l1_2).as_ptr();
        let p_l2 = view(l2_2).as_ptr();
        let p_p = view(p2).as_ptr();

        let r1 = Barrier.wait_ptr(p_b);
        if r1.is_leader() {
            let _ = unsafe { (*p_l1).fetch_add(1i64, Ordering.SeqCst) };
        }

        let r2 = Barrier.wait_ptr(p_b);
        if r2.is_leader() {
            let _ = unsafe { (*p_l2).fetch_add(1i64, Ordering.SeqCst) };
        }
        let _ = unsafe { (*p_p).fetch_add(1i64, Ordering.SeqCst) };
        0i64
    });

    let h3 = spawn(|| -> i64 {
        let p_b = view(b3).as_ptr();
        let p_l1 = view(l1_3).as_ptr();
        let p_l2 = view(l2_3).as_ptr();
        let p_p = view(p3).as_ptr();

        let r1 = Barrier.wait_ptr(p_b);
        if r1.is_leader() {
            let _ = unsafe { (*p_l1).fetch_add(1i64, Ordering.SeqCst) };
        }

        let r2 = Barrier.wait_ptr(p_b);
        if r2.is_leader() {
            let _ = unsafe { (*p_l2).fetch_add(1i64, Ordering.SeqCst) };
        }
        let _ = unsafe { (*p_p).fetch_add(1i64, Ordering.SeqCst) };
        0i64
    });

    let h4 = spawn(|| -> i64 {
        let p_b = view(b4).as_ptr();
        let p_l1 = view(l1_4).as_ptr();
        let p_l2 = view(l2_4).as_ptr();
        let p_p = view(p4).as_ptr();

        let r1 = Barrier.wait_ptr(p_b);
        if r1.is_leader() {
            let _ = unsafe { (*p_l1).fetch_add(1i64, Ordering.SeqCst) };
        }

        let r2 = Barrier.wait_ptr(p_b);
        if r2.is_leader() {
            let _ = unsafe { (*p_l2).fetch_add(1i64, Ordering.SeqCst) };
        }
        let _ = unsafe { (*p_p).fetch_add(1i64, Ordering.SeqCst) };
        0i64
    });

    let _ = h1.join();
    let _ = h2.join();
    let _ = h3.join();
    let _ = h4.join();

    let p_l1_m = view(leader_count1).as_ptr();
    let leaders1 = unsafe { (*p_l1_m).load(Ordering.SeqCst) };
    check_id(1i64, leaders1 == 1i64);

    let p_l2_m = view(leader_count2).as_ptr();
    let leaders2 = unsafe { (*p_l2_m).load(Ordering.SeqCst) };
    check_id(2i64, leaders2 == 1i64);

    let p_p_m = view(passed_count).as_ptr();
    let passed = unsafe { (*p_p_m).load(Ordering.SeqCst) };
    check_id(3i64, passed == 4i64);

    print("OK barrier_rendezvous ");
    print_int(leaders1);
    print(" ");
    print_int(leaders2);
    print(" ");
    print_int(passed);
    print("\\n");
    0
}
"""

BIG_STRUCT_HEADER = """// test: run
// modes: interp native
// timeout: 60
// covers: REQ-CONC-044 REQ-CONC-046 REQ-CONC-050 REQ-CONC-070 REQ-CONC-071
// stdout: OK big_struct_sync 10 20 30 99 111 222 333 444 50 60 70 80 500 600 700 800 1 2 3 4\\n
"""

BIG_STRUCT_SOURCES = COMMON_PREREQS + [
    "std/sync/rc.ax",
    "std/sync/arc.ax",
    "std/sync/mutex.ax",
    "std/sync/rwlock.ax",
    "std/sync/once.ax",
]

BIG_STRUCT_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.rc.Rc
use std.sync.arc.Arc
use std.sync.mutex.Mutex
use std.sync.rwlock.RwLock
use std.sync.once.OnceCell
use std.thread.spawn

@intrinsic unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }
@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

@derive(Copy)
@repr(C)
pub struct BigStruct {
    pub a: i64,
    pub b: i64,
    pub c: i64,
    pub d: i64,
}

fn check_id(id: i64, cond: bool) {
    if !cond {
        print("CHECK FAILED: ");
        print_int(id);
        print("\\n");
        loop {}
    }
}

pub fn main() -> i32 {
    // -------------------------------------------------------------
    // 1. Rc<BigStruct>: multi-field struct > 24 bytes (32 bytes)
    // -------------------------------------------------------------
    let bs1 = BigStruct { a: 10i64, b: 20i64, c: 30i64, d: 40i64 };
    let mut rc: Rc<BigStruct> = Rc.new_from_ptr(unsafe { address_of(bs1) }, 32usize);
    check_id(101i64, view(rc).strong_count() == 1usize);
    let p_bs1 = view(rc).as_ptr();
    check_id(102i64, unsafe { (*p_bs1).a } == 10i64);
    check_id(103i64, unsafe { (*p_bs1).b } == 20i64);
    check_id(104i64, unsafe { (*p_bs1).c } == 30i64);
    check_id(105i64, unsafe { (*p_bs1).d } == 40i64);

    let rc2 = view(rc).clone();
    check_id(106i64, view(rc).strong_count() == 2usize);
    drop(rc2);
    check_id(107i64, view(rc).strong_count() == 1usize);

    let mut_p = mut_view(rc).as_mut_ptr();
    check_id(108i64, (mut_p as usize) != 0usize);
    unsafe {
        (*mut_p).d = 99i64;
    }
    let p_bs1_after = view(rc).as_ptr();
    check_id(109i64, unsafe { (*p_bs1_after).d } == 99i64);

    // -------------------------------------------------------------
    // 2. Arc<Mutex<BigStruct>>: concurrent access with 32-byte struct
    // -------------------------------------------------------------
    let m: Arc<Mutex<BigStruct>> = Arc.new(Mutex.new(BigStruct { a: 0i64, b: 0i64, c: 0i64, d: 0i64 }));
    let p_m = view(m).as_ptr();
    {
        let g = Mutex.lock_ptr(p_m);
        unsafe {
            *g.data_ptr = BigStruct { a: 100i64, b: 200i64, c: 300i64, d: 400i64 };
        }
        drop(g);
    }
    let m_clone = view(m).clone();

    let h_m = spawn(|| -> i64 {
        let p_m_c = view(m_clone).as_ptr();
        let g = Mutex.lock_ptr(p_m_c);
        let cur = unsafe { *g.data_ptr };
        check_id(201i64, cur.a == 100i64);
        check_id(202i64, cur.b == 200i64);
        unsafe {
            *g.data_ptr = BigStruct { a: 111i64, b: 222i64, c: 333i64, d: 444i64 };
        }
        drop(g);
        1i64
    });

    let _ = h_m.join();
    let g_final = Mutex.lock_ptr(p_m);
    let final_m_val = unsafe { *g_final.data_ptr };
    drop(g_final);
    check_id(203i64, final_m_val.a == 111i64);
    check_id(204i64, final_m_val.b == 222i64);
    check_id(205i64, final_m_val.c == 333i64);
    check_id(206i64, final_m_val.d == 444i64);

    // -------------------------------------------------------------
    // 3. RwLock<BigStruct>: readers and writer with 32-byte struct
    // -------------------------------------------------------------
    let rw: Arc<RwLock<BigStruct>> = Arc.new(RwLock.new(BigStruct { a: 0i64, b: 0i64, c: 0i64, d: 0i64 }));
    let p_rw = view(rw).as_ptr();
    {
        let mut wg = RwLock.write_ptr(p_rw);
        unsafe {
            *wg.data_ptr = BigStruct { a: 50i64, b: 60i64, c: 70i64, d: 80i64 };
        }
        drop(wg);
    }
    let rg = RwLock.read_ptr(p_rw);
    let r_init = unsafe { *rg.data_ptr };
    drop(rg);
    check_id(301i64, r_init.a == 50i64);
    check_id(302i64, r_init.b == 60i64);
    check_id(303i64, r_init.c == 70i64);
    check_id(304i64, r_init.d == 80i64);

    let rw_clone = view(rw).clone();
    let h_rw = spawn(|| -> i64 {
        let p_rw_c = view(rw_clone).as_ptr();
        let mut wg = RwLock.write_ptr(p_rw_c);
        unsafe {
            *wg.data_ptr = BigStruct { a: 500i64, b: 600i64, c: 700i64, d: 800i64 };
        }
        drop(wg);
        1i64
    });
    let _ = h_rw.join();

    let rg2 = RwLock.read_ptr(p_rw);
    let r_updated = unsafe { *rg2.data_ptr };
    drop(rg2);
    check_id(305i64, r_updated.a == 500i64);
    check_id(306i64, r_updated.b == 600i64);
    check_id(307i64, r_updated.c == 700i64);
    check_id(308i64, r_updated.d == 800i64);

    // -------------------------------------------------------------
    // 4. OnceCell<BigStruct>: initialization with 32-byte struct
    // -------------------------------------------------------------
    let cell: Arc<OnceCell<BigStruct>> = Arc.new(OnceCell.new());
    let p_cell = view(cell).as_ptr();

    let bs4 = BigStruct { a: 1i64, b: 2i64, c: 3i64, d: 4i64 };
    let ok = OnceCell.set_from_ptr(p_cell, unsafe { address_of(bs4) }, 32usize);
    check_id(402i64, ok);

    // Second set must fail
    let bs4_dup = BigStruct { a: 999i64, b: 999i64, c: 999i64, d: 999i64 };
    let ok_dup = OnceCell.set_from_ptr(p_cell, unsafe { address_of(bs4_dup) }, 32usize);
    check_id(403i64, !ok_dup);

    let p_val: *const BigStruct = OnceCell.as_ptr_ptr(p_cell);
    check_id(404i64, (p_val as usize) != 0usize);
    let cell_val = unsafe { *p_val };
    check_id(405i64, cell_val.a == 1i64);
    check_id(406i64, cell_val.b == 2i64);
    check_id(407i64, cell_val.c == 3i64);
    check_id(408i64, cell_val.d == 4i64);

    print("OK big_struct_sync ");
    print_int(unsafe { (*p_bs1_after).a });
    print(" ");
    print_int(unsafe { (*p_bs1_after).b });
    print(" ");
    print_int(unsafe { (*p_bs1_after).c });
    print(" ");
    print_int(unsafe { (*p_bs1_after).d });
    print(" ");
    print_int(final_m_val.a);
    print(" ");
    print_int(final_m_val.b);
    print(" ");
    print_int(final_m_val.c);
    print(" ");
    print_int(final_m_val.d);
    print(" ");
    print_int(r_init.a);
    print(" ");
    print_int(r_init.b);
    print(" ");
    print_int(r_init.c);
    print(" ");
    print_int(r_init.d);
    print(" ");
    print_int(r_updated.a);
    print(" ");
    print_int(r_updated.b);
    print(" ");
    print_int(r_updated.c);
    print(" ");
    print_int(r_updated.d);
    print(" ");
    print_int(cell_val.a);
    print(" ");
    print_int(cell_val.b);
    print(" ");
    print_int(cell_val.c);
    print(" ");
    print_int(cell_val.d);
    print("\\n");
    0
}
"""

BUNDLES = {
    "rc_basic.ax": (RC_BASIC_HEADER, RC_BASIC_SOURCES, RC_BASIC_MAIN),
    "arc_mutex_threads.ax": (ARC_MUTEX_HEADER, ARC_MUTEX_SOURCES, ARC_MUTEX_MAIN),
    "rwlock_readers_writer.ax": (RWLOCK_HEADER, RWLOCK_SOURCES, RWLOCK_MAIN),
    "condvar_signaling.ax": (CONDVAR_HEADER, CONDVAR_SOURCES, CONDVAR_MAIN),
    "once_cell_init.ax": (ONCE_CELL_HEADER, ONCE_CELL_SOURCES, ONCE_CELL_MAIN),
    "barrier_rendezvous.ax": (BARRIER_HEADER, BARRIER_SOURCES, BARRIER_MAIN),
    "big_struct_sync.ax": (BIG_STRUCT_HEADER, BIG_STRUCT_SOURCES, BIG_STRUCT_MAIN),
}


def read_source(rel_path):
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
            print("ERROR: sync test bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            print("Run `python tests/std/sync/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK sync bundles match live std/sync\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
