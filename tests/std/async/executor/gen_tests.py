#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/std/async/executor (T421).

Generates in-tree test bundles for std.asyn executors and async sync primitives
by concatenating verbatim standard library source files with test harness logic.
Ensures zero test divergence from live std/async/*.ax implementations.
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
# Test Definitions
# -----------------------------------------------------------------------------

LOCAL_RC_HEADER = """// test: run
// modes: interp native
// timeout: 60
// stdout: OK local_executor_rc 42 100 1\\n
"""

LOCAL_RC_SOURCES = COMMON_PREREQS + [
    "std/sync/rc.ax",
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
]

LOCAL_RC_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.sync.rc.Rc
use std.asyn.executor.LocalExecutor
use std.asyn.task.LocalTaskHandle
use std.asyn.task.TaskResult
use std.asyn.task.TaskHeader
use std.asyn.task.TaskControlBlock
use std.asyn.task.tcb_poll_fn

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

struct WorkerAdd {
    pub rc_val: Rc<i64>,
    pub bonus: i64,
    pub step: i32,
}

impl Future for WorkerAdd {
    type Output = i64;
    fn poll(self: mut_view<WorkerAdd>, cx: mut_view<Context>) -> Poll<i64> {
        let st = self.step;
        if st == 0i32 {
            self.step = 1i32;
            let mut w = cx.waker();
            view(w).wake_by_ref();
            return Poll.Pending;
        }
        let p = view(self.rc_val).as_ptr();
        let v1 = unsafe { *p };
        Poll.Ready(v1 + v1 + self.bonus)
    }
}

fn poll_worker_add(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<WorkerAdd, i64>;
    tcb_poll_fn<WorkerAdd, i64>(tcb, cx)
}

struct WorkerRead {
    pub rc_val: Rc<i64>,
    pub step: i32,
}

impl Future for WorkerRead {
    type Output = i64;
    fn poll(self: mut_view<WorkerRead>, cx: mut_view<Context>) -> Poll<i64> {
        let st = self.step;
        if st == 0i32 {
            self.step = 1i32;
            let mut w = cx.waker();
            view(w).wake_by_ref();
            return Poll.Pending;
        }
        let p = view(self.rc_val).as_ptr();
        Poll.Ready(unsafe { *p })
    }
}

fn poll_worker_read(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<WorkerRead, i64>;
    tcb_poll_fn<WorkerRead, i64>(tcb, cx)
}

pub fn main() -> i32 {
    let mut exec = LocalExecutor.new();
    let val_rc = Rc.new(42i64);
    let rc1 = view(val_rc).clone();
    let rc2 = view(val_rc).clone();

    check(view(val_rc).strong_count() == 3usize);

    let h1 = exec.spawn_local(WorkerAdd { rc_val: rc1, bonus: 16i64, step: 0i32 }, poll_worker_add);
    let h2 = exec.spawn_local(WorkerRead { rc_val: rc2, step: 0i32 }, poll_worker_read);

    exec.run();

    let r1 = match h1.join() {
        TaskResult.Completed(v) => v,
        _ => -1i64,
    };
    let r2 = match h2.join() {
        TaskResult.Completed(v) => v,
        _ => -1i64,
    };

    check(r1 == 100i64);
    check(r2 == 42i64);
    check(view(val_rc).strong_count() == 1usize);

    print("OK local_executor_rc ");
    print_int(r2);
    print(" ");
    print_int(r1);
    print(" ");
    print_int(view(val_rc).strong_count() as i64);
    print("\\n");
    0
}
"""

WORK_STEALING_HEADER = """// test: run
// modes: interp native
// timeout: 60
// stdout: OK work_stealing_executor 4 16 136\\n
"""

WORK_STEALING_SOURCES = COMMON_PREREQS + [
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
]

WORK_STEALING_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.asyn.executor.Executor
use std.asyn.task.TaskResult
use std.asyn.task.TaskHeader
use std.asyn.task.TaskControlBlock
use std.asyn.task.tcb_poll_fn

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

struct ComputeTask {
    pub val: i64,
    pub step: i32,
}

impl Future for ComputeTask {
    type Output = i64;
    fn poll(self: mut_view<ComputeTask>, cx: mut_view<Context>) -> Poll<i64> {
        let st = self.step;
        if st < 2i32 {
            self.step = st + 1i32;
            let mut w = cx.waker();
            view(w).wake_by_ref();
            return Poll.Pending;
        }
        Poll.Ready(self.val)
    }
}

fn poll_compute_task(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<ComputeTask, i64>;
    tcb_poll_fn<ComputeTask, i64>(tcb, cx)
}

pub fn main() -> i32 {
    let exec = Executor.new(4);
    check(exec.worker_count() == 4usize);

    let h1 = exec.spawn(ComputeTask { val: 1i64, step: 0i32 }, poll_compute_task);
    let h2 = exec.spawn(ComputeTask { val: 2i64, step: 0i32 }, poll_compute_task);
    let h3 = exec.spawn(ComputeTask { val: 3i64, step: 0i32 }, poll_compute_task);
    let h4 = exec.spawn(ComputeTask { val: 4i64, step: 0i32 }, poll_compute_task);
    let h5 = exec.spawn(ComputeTask { val: 5i64, step: 0i32 }, poll_compute_task);
    let h6 = exec.spawn(ComputeTask { val: 6i64, step: 0i32 }, poll_compute_task);
    let h7 = exec.spawn(ComputeTask { val: 7i64, step: 0i32 }, poll_compute_task);
    let h8 = exec.spawn(ComputeTask { val: 8i64, step: 0i32 }, poll_compute_task);
    let h9 = exec.spawn(ComputeTask { val: 9i64, step: 0i32 }, poll_compute_task);
    let h10 = exec.spawn(ComputeTask { val: 10i64, step: 0i32 }, poll_compute_task);
    let h11 = exec.spawn(ComputeTask { val: 11i64, step: 0i32 }, poll_compute_task);
    let h12 = exec.spawn(ComputeTask { val: 12i64, step: 0i32 }, poll_compute_task);
    let h13 = exec.spawn(ComputeTask { val: 13i64, step: 0i32 }, poll_compute_task);
    let h14 = exec.spawn(ComputeTask { val: 14i64, step: 0i32 }, poll_compute_task);
    let h15 = exec.spawn(ComputeTask { val: 15i64, step: 0i32 }, poll_compute_task);
    let h16 = exec.spawn(ComputeTask { val: 16i64, step: 0i32 }, poll_compute_task);

    let r1 = match h1.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r2 = match h2.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r3 = match h3.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r4 = match h4.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r5 = match h5.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r6 = match h6.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r7 = match h7.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r8 = match h8.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r9 = match h9.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r10 = match h10.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r11 = match h11.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r12 = match h12.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r13 = match h13.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r14 = match h14.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r15 = match h15.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r16 = match h16.join() { TaskResult.Completed(v) => v, _ => -1i64 };

    let sum = r1 + r2 + r3 + r4 + r5 + r6 + r7 + r8 + r9 + r10 + r11 + r12 + r13 + r14 + r15 + r16;
    check(sum == 136i64);

    exec.shutdown();

    print("OK work_stealing_executor ");
    print_int(exec.worker_count() as i64);
    print(" ");
    print_int(16i64);
    print(" ");
    print_int(sum);
    print("\\n");
    0
}
"""

SPAWN_TREE_HEADER = """// test: run
// modes: interp native
// timeout: 60
// stdout: OK work_stealing_spawn_tree 128 21184\\n
"""

SPAWN_TREE_SOURCES = WORK_STEALING_SOURCES

SPAWN_TREE_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.core.host.heap_alloc
use std.core.host.thread_yield
use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.asyn.executor.Executor
use std.asyn.task.TaskResult
use std.asyn.task.TaskHandle
use std.asyn.task.TaskHeader
use std.asyn.task.TaskControlBlock
use std.asyn.task.tcb_poll_fn

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

// Child tasks are spawned from inside a worker thread, so their first scheduling lands in that
// worker's local deque; the other workers obtain them by stealing or from the injection queue.
struct Child {
    pub val: i64,
    pub step: i32,
    pub total: *mut Atomic<i64>,
}

unsafe impl Send for Child {}

impl Future for Child {
    type Output = i64;
    fn poll(self: mut_view<Child>, cx: mut_view<Context>) -> Poll<i64> {
        let st = self.step;
        if st < 2i32 {
            self.step = st + 1i32;
            let mut w = cx.waker();
            view(w).wake_by_ref();
            return Poll.Pending;
        }
        unsafe {
            (*self.total).fetch_add(self.val, Ordering.AcqRel);
        }
        Poll.Ready(self.val)
    }
}

fn poll_child(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<Child, i64>;
    tcb_poll_fn<Child, i64>(tcb, cx)
}

struct Parent {
    pub exec: Executor,
    pub base: i64,
    pub count: i64,
    pub spawned: bool,
    pub total: *mut Atomic<i64>,
}

unsafe impl Send for Parent {}

impl Future for Parent {
    type Output = i64;
    fn poll(self: mut_view<Parent>, cx: mut_view<Context>) -> Poll<i64> {
        if !self.spawned {
            self.spawned = true;
            let mut k: i64 = 0i64;
            while k < self.count {
                let h: TaskHandle<i64> = self.exec.spawn(Child { val: self.base + k, step: 0i32, total: self.total }, poll_child);
                h.detach();
                k = k + 1i64;
            }
            let mut w = cx.waker();
            view(w).wake_by_ref();
            return Poll.Pending;
        }
        Poll.Ready(self.count)
    }
}

fn poll_parent(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<Parent, i64>;
    tcb_poll_fn<Parent, i64>(tcb, cx)
}

pub fn main() -> i32 {
    let exec = Executor.new(4);
    let raw_total = unsafe { heap_alloc(8, 8) };
    let total = raw_total as *mut Atomic<i64>;
    unsafe {
        *total = Atomic.new(0i64);
    }

    let h0 = exec.spawn(Parent { exec: exec, base: 0i64, count: 32i64, spawned: false, total: total }, poll_parent);
    let h1 = exec.spawn(Parent { exec: exec, base: 100i64, count: 32i64, spawned: false, total: total }, poll_parent);
    let h2 = exec.spawn(Parent { exec: exec, base: 200i64, count: 32i64, spawned: false, total: total }, poll_parent);
    let h3 = exec.spawn(Parent { exec: exec, base: 300i64, count: 32i64, spawned: false, total: total }, poll_parent);

    let r0 = match h0.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r1 = match h1.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r2 = match h2.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let r3 = match h3.join() { TaskResult.Completed(v) => v, _ => -1i64 };
    let parents = r0 + r1 + r2 + r3;
    check(parents == 128i64);

    // Children are detached: wait until every one of them has contributed to the shared total.
    while unsafe { (*total).load(Ordering.Acquire) } < 21184i64 {
        unsafe {
            thread_yield();
        }
    }
    let sum = unsafe { (*total).load(Ordering.Acquire) };
    check(sum == 21184i64);

    exec.shutdown();

    print("OK work_stealing_spawn_tree ");
    print_int(parents);
    print(" ");
    print_int(sum);
    print("\\n");
    0
}
"""

SEMAPHORE_HEADER = """// test: run
// modes: interp native
// timeout: 60
// stdout: OK async_semaphore_limits 2 5 2\\n
"""

SEMAPHORE_SOURCES = COMMON_PREREQS + [
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
    "std/async/sync.ax",
]

SEMAPHORE_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.core.prelude.Future
use std.core.prelude.Poll
use std.core.prelude.Context
use std.asyn.executor.LocalExecutor
use std.asyn.task.LocalTaskHandle
use std.asyn.task.TaskResult
use std.asyn.task.TaskHeader
use std.asyn.task.TaskControlBlock
use std.asyn.task.tcb_poll_fn
use std.asyn.sync.AsyncSemaphore
use std.asyn.sync.AsyncSemaphorePermit
use std.asyn.sync.AsyncSemaphoreAcquireFuture

@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

// Each worker takes one permit, holds it across an await (yield), then releases it. With two permits
// and five workers, at most two workers may ever be inside the critical section at once.
struct SemWorker {
    pub cur: *mut i64,
    pub max_seen: *mut i64,
    pub done: *mut i64,
    pub phase: i32,
    pub acq: AsyncSemaphoreAcquireFuture,
    pub permit: Option<AsyncSemaphorePermit>,
}

impl Future for SemWorker {
    type Output = i64;

    fn poll(self: mut_view<SemWorker>, cx: mut_view<Context>) -> Poll<i64> {
        if self.phase == 0i32 {
            match self.acq.poll(mut_view(*cx)) {
                Poll.Ready(p) => {
                    self.permit = Option.Some(p);
                    self.phase = 1i32;
                },
                Poll.Pending => {
                    return Poll.Pending;
                },
            }
        }
        if self.phase == 1i32 {
            unsafe {
                *self.cur = *self.cur + 1i64;
                if *self.cur > *self.max_seen {
                    *self.max_seen = *self.cur;
                }
            }
            self.phase = 2i32;
            let mut w = mut_view(*cx).waker();
            view(w).wake_by_ref();
            return Poll.Pending;
        }
        unsafe {
            *self.cur = *self.cur - 1i64;
            *self.done = *self.done + 1i64;
        }
        self.permit = Option.None;
        Poll.Ready(1i64)
    }
}

fn poll_sem_worker(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<SemWorker, i64>;
    tcb_poll_fn<SemWorker, i64>(tcb, cx)
}

fn none_permit() -> Option<AsyncSemaphorePermit> {
    Option.None
}

pub fn main() -> i32 {
    let mut exec = LocalExecutor.new();
    let sem = AsyncSemaphore.new(2usize);
    let mut cur: i64 = 0i64;
    let mut max_seen: i64 = 0i64;
    let mut done: i64 = 0i64;
    let p_cur = unsafe { address_of_mut(cur) };
    let p_max = unsafe { address_of_mut(max_seen) };
    let p_done = unsafe { address_of_mut(done) };

    let h1: LocalTaskHandle<i64> = exec.spawn_local(SemWorker { cur: p_cur, max_seen: p_max, done: p_done, phase: 0i32, acq: sem.acquire(), permit: none_permit() }, poll_sem_worker);
    let h2: LocalTaskHandle<i64> = exec.spawn_local(SemWorker { cur: p_cur, max_seen: p_max, done: p_done, phase: 0i32, acq: sem.acquire(), permit: none_permit() }, poll_sem_worker);
    let h3: LocalTaskHandle<i64> = exec.spawn_local(SemWorker { cur: p_cur, max_seen: p_max, done: p_done, phase: 0i32, acq: sem.acquire(), permit: none_permit() }, poll_sem_worker);
    let h4: LocalTaskHandle<i64> = exec.spawn_local(SemWorker { cur: p_cur, max_seen: p_max, done: p_done, phase: 0i32, acq: sem.acquire(), permit: none_permit() }, poll_sem_worker);
    let h5: LocalTaskHandle<i64> = exec.spawn_local(SemWorker { cur: p_cur, max_seen: p_max, done: p_done, phase: 0i32, acq: sem.acquire(), permit: none_permit() }, poll_sem_worker);

    exec.run();

    check(done == 5i64);
    check(max_seen == 2i64);
    check(cur == 0i64);
    let avail = sem.available_permits();
    check(avail == 2usize);

    print("OK async_semaphore_limits ");
    print_int(max_seen);
    print(" ");
    print_int(done);
    print(" ");
    print_int(avail as i64);
    print("\\n");
    0
}
"""

LOST_WAKE_HEADER = """// test: run
// modes: interp native
// timeout: 60
// stdout: OK lost_wake_prevention 50\\n
"""

LOST_WAKE_SOURCES = COMMON_PREREQS + [
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
]

LOST_WAKE_MAIN = """module main

use std.core.prelude.Context
use std.core.prelude.Future
use std.core.prelude.Poll
use std.sync.atomic.Atomic
use std.sync.atomic.Ordering
use std.core.option.Option
use std.core.result.Result
use std.core.host.heap_alloc
use std.core.host.heap_free
use std.asyn.waker.TaskHeader
use std.asyn.waker.TASK_POLLING
use std.asyn.waker.TASK_NOTIFIED
use std.asyn.waker.init_task_header_vtable
use std.asyn.waker.new_task_waker_vtable
use std.asyn.waker.task_wake
use std.asyn.executor.LocalExecutor
use std.asyn.task.TaskResult
use std.asyn.task.TaskControlBlock
use std.asyn.task.tcb_poll_fn

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

pub struct RacingFuture {
    pub poll_count: usize,
    pub target_count: usize,
}

impl Future for RacingFuture {
    type Output = usize;

    fn poll(self: mut_view<RacingFuture>, cx: mut_view<Context>) -> Poll<usize> {
        self.poll_count = self.poll_count + 1;
        if self.poll_count >= self.target_count {
            return Poll.Ready(self.poll_count);
        }
        let mut w = cx.waker();
        view(w).wake_by_ref();
        Poll.Pending
    }
}

fn poll_racing_task(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<RacingFuture, usize>;
    tcb_poll_fn<RacingFuture, usize>(tcb, cx)
}

pub fn main() -> i32 {
    let mut exec = LocalExecutor.new();

    // 1. Direct state-machine invariant test:
    let sz = 128usize;
    let raw = unsafe { heap_alloc(sz, 8usize) } as *mut TaskHeader;
    init_task_header_vtable(raw, new_task_waker_vtable());
    unsafe {
        (*raw).state = Atomic.new(TASK_POLLING);
        (*raw).ref_count = Atomic.new(1u32);
        (*raw).alloc_size = sz;
        (*raw).alloc_align = 8usize;
    }
    task_wake(raw);
    let st: u32 = unsafe { (*raw).state.load(Ordering.Acquire) } & 0x7u32;
    check(st == TASK_NOTIFIED);
    unsafe { heap_free(raw as *mut u8, sz, 8usize); }

    // 2. Full executor test with 50 racing poll/wake iterations
    let h = exec.spawn_local(RacingFuture { poll_count: 0, target_count: 50 }, poll_racing_task);
    while !view(h).is_finished() {
        exec.try_tick();
    }
    let res = match h.join() {
        TaskResult.Completed(v) => v,
        _ => 0usize,
    };
    check(res == 50usize);

    print("OK lost_wake_prevention ");
    print_int(res as i64);
    print("\\n");
    0
}
"""

ASYNC_MUTEX_HEADER = """// test: run
// modes: interp native
// timeout: 60
// stdout: OK async_mutex_across_await 40\\n
"""

ASYNC_MUTEX_SOURCES = COMMON_PREREQS + [
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
    "std/async/sync.ax",
]

ASYNC_MUTEX_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.core.prelude.Future
use std.core.prelude.Poll
use std.core.prelude.Context
use std.asyn.executor.LocalExecutor
use std.asyn.task.LocalTaskHandle
use std.asyn.task.TaskResult
use std.asyn.task.TaskHeader
use std.asyn.task.TaskControlBlock
use std.asyn.task.tcb_poll_fn
use std.asyn.sync.AsyncMutex
use std.asyn.sync.AsyncMutexGuard
use std.asyn.sync.AsyncMutexLockFuture

@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

// Each worker holds the mutex guard across an await (it yields while locked), so the other three
// workers queue up as waiters and are handed the lock one by one when the guard is released.
struct MutexWorker {
    pub mutex_ptr: *mut AsyncMutex<i64>,
    pub cur_iter: i64,
    pub target_iters: i64,
    pub phase: i32,
    pub lock_fut: AsyncMutexLockFuture<i64>,
    pub guard: Option<AsyncMutexGuard<i64>>,
    pub in_cs: *mut i64,
    pub violations: *mut i64,
    pub waited: *mut i64,
}

impl Future for MutexWorker {
    type Output = i64;

    fn poll(self: mut_view<MutexWorker>, cx: mut_view<Context>) -> Poll<i64> {
        while (self.cur_iter <= (self.target_iters - 1i64)) {
            if self.phase == 0i32 {
                match self.lock_fut.poll_lock(mut_view(*cx)) {
                    Poll.Ready(g) => {
                        // Critical section: runs while this worker owns the lock, then the guard is
                        // kept alive across the yield below (held across an await).
                        unsafe {
                            *self.in_cs = *self.in_cs + 1i64;
                            if *self.in_cs > 1i64 {
                                *self.violations = *self.violations + 1i64;
                            }
                        }
                        let cur_v = g.val();
                        let mut g_mut = g;
                        mut_view(g_mut).set(cur_v + 1i64);
                        self.guard = Option.Some(g_mut);
                        self.phase = 2i32;
                        let mut w = mut_view(*cx).waker();
                        view(w).wake_by_ref();
                        return Poll.Pending;
                    },
                    Poll.Pending => {
                        unsafe {
                            *self.waited = *self.waited + 1i64;
                        }
                        return Poll.Pending;
                    },
                }
            }
            if self.phase == 2i32 {
                unsafe {
                    *self.in_cs = *self.in_cs - 1i64;
                }
                self.guard = Option.None;
                self.lock_fut = unsafe { (*self.mutex_ptr).lock_async() };
                self.cur_iter = self.cur_iter + 1i64;
                self.phase = 0i32;
            }
        }
        Poll.Ready(self.cur_iter)
    }
}

fn poll_mutex_worker(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<MutexWorker, i64>;
    tcb_poll_fn<MutexWorker, i64>(tcb, cx)
}

fn none_guard() -> Option<AsyncMutexGuard<i64>> {
    Option.None
}

pub fn main() -> i32 {
    let mut exec = LocalExecutor.new();
    let mut mutex = AsyncMutex.new(0i64);
    let p_m = unsafe { address_of_mut(mutex) };
    let mut in_cs: i64 = 0i64;
    let mut violations: i64 = 0i64;
    let mut waited: i64 = 0i64;
    let p_in = unsafe { address_of_mut(in_cs) };
    let p_viol = unsafe { address_of_mut(violations) };
    let p_wait = unsafe { address_of_mut(waited) };

    let h1: LocalTaskHandle<i64> = exec.spawn_local(MutexWorker { mutex_ptr: p_m, cur_iter: 0i64, target_iters: 10i64, phase: 0i32, lock_fut: unsafe { (*p_m).lock_async() }, guard: none_guard(), in_cs: p_in, violations: p_viol, waited: p_wait }, poll_mutex_worker);
    let h2: LocalTaskHandle<i64> = exec.spawn_local(MutexWorker { mutex_ptr: p_m, cur_iter: 0i64, target_iters: 10i64, phase: 0i32, lock_fut: unsafe { (*p_m).lock_async() }, guard: none_guard(), in_cs: p_in, violations: p_viol, waited: p_wait }, poll_mutex_worker);
    let h3: LocalTaskHandle<i64> = exec.spawn_local(MutexWorker { mutex_ptr: p_m, cur_iter: 0i64, target_iters: 10i64, phase: 0i32, lock_fut: unsafe { (*p_m).lock_async() }, guard: none_guard(), in_cs: p_in, violations: p_viol, waited: p_wait }, poll_mutex_worker);
    let h4: LocalTaskHandle<i64> = exec.spawn_local(MutexWorker { mutex_ptr: p_m, cur_iter: 0i64, target_iters: 10i64, phase: 0i32, lock_fut: unsafe { (*p_m).lock_async() }, guard: none_guard(), in_cs: p_in, violations: p_viol, waited: p_wait }, poll_mutex_worker);

    exec.run();

    let final_val = match mutex.try_lock() {
        Option.Some(g) => g.val(),
        Option.None => -1i64,
    };
    check(final_val == 40i64);
    // The guard is held across an await: no two workers may be inside the critical section at once,
    // and the other workers must really have queued up as waiters.
    check(violations == 0i64);
    check(waited > 0i64);

    print("OK async_mutex_across_await ");
    print_int(final_val);
    print("\\n");
    0
}
"""

ASYNC_CHANNEL_HEADER = """// test: run
// modes: interp native
// timeout: 60
// stdout: OK async_channel_pipeline 55\\n
"""

ASYNC_CHANNEL_SOURCES = COMMON_PREREQS + [
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
    "std/async/sync.ax",
    "std/async/channel.ax",
]

ASYNC_CHANNEL_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.core.prelude.Future
use std.core.prelude.Poll
use std.core.prelude.Context
use std.asyn.executor.LocalExecutor
use std.asyn.task.LocalTaskHandle
use std.asyn.channel.AsyncSender
use std.asyn.channel.AsyncReceiver
use std.asyn.channel.async_channel_bounded
use std.asyn.channel.TrySendError
use std.asyn.channel.TryRecvError
use std.asyn.task.TaskResult
use std.asyn.task.TaskHeader
use std.asyn.task.TaskControlBlock
use std.asyn.task.tcb_poll_fn

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

struct ProducerTask {
    pub tx: AsyncSender<i64>,
    pub cur: i64,
    pub total: i64,
}

impl Future for ProducerTask {
    type Output = i64;

    fn poll(self: mut_view<ProducerTask>, cx: mut_view<Context>) -> Poll<i64> {
        while self.cur <= self.total {
            match view(self.tx).try_send(self.cur) {
                Result.Ok(_) => {
                    self.cur = self.cur + 1i64;
                    let mut w = mut_view(*cx).waker();
                    view(w).wake_by_ref();
                    return Poll.Pending;
                },
                Result.Err(_) => {
                    let mut w = mut_view(*cx).waker();
                    view(w).wake_by_ref();
                    return Poll.Pending;
                },
            }
        }
        mut_view(self.tx).close();
        Poll.Ready(self.total)
    }
}

fn poll_producer(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<ProducerTask, i64>;
    tcb_poll_fn<ProducerTask, i64>(tcb, cx)
}

struct ConsumerTask {
    pub rx: AsyncReceiver<i64>,
    pub sum: i64,
}

impl Future for ConsumerTask {
    type Output = i64;

    fn poll(self: mut_view<ConsumerTask>, cx: mut_view<Context>) -> Poll<i64> {
        loop {
            match view(self.rx).try_recv() {
                Result.Ok(val) => {
                    self.sum = self.sum + val;
                },
                Result.Err(err) => {
                    match err {
                        TryRecvError.Empty => {
                            let mut w = mut_view(*cx).waker();
                            view(w).wake_by_ref();
                            return Poll.Pending;
                        },
                        TryRecvError.Disconnected => {
                            return Poll.Ready(self.sum);
                        },
                    }
                },
            }
        }
    }
}

fn poll_consumer(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<ConsumerTask, i64>;
    tcb_poll_fn<ConsumerTask, i64>(tcb, cx)
}

pub fn main() -> i32 {
    let mut exec = LocalExecutor.new();
    let pair = async_channel_bounded<i64>(2usize);
    let tx = pair.tx;
    let rx = pair.rx;

    let hp: LocalTaskHandle<i64> = exec.spawn_local(ProducerTask { tx: tx, cur: 1i64, total: 10i64 }, poll_producer);
    let hc: LocalTaskHandle<i64> = exec.spawn_local(ConsumerTask { rx: rx, sum: 0i64 }, poll_consumer);

    exec.run();

    let res_c = match hc.join() {
        TaskResult.Completed(v) => v,
        _ => -1i64,
    };
    check(res_c == 55i64);

    print("OK async_channel_pipeline ");
    print_int(res_c);
    print("\\n");
    0
}
"""

# -----------------------------------------------------------------------------
# QA (T421 gate) boundary test: cancelling a waiting / already-granted lock or permit future must
# forward ownership to the next waiter and never lose the lock (scope bullet "wakes the next waiter on
# Drop/cancellation without losing lock ownership"). No executor: futures are polled by hand with a
# null waker, so the result is fully deterministic.
# -----------------------------------------------------------------------------

QA_CANCEL_HEADER = """// test: run
// modes: interp native
// timeout: 60
// stdout: OK qa_cancel_waiters 0\\n
"""

QA_CANCEL_SOURCES = COMMON_PREREQS + [
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
    "std/async/sync.ax",
]

QA_CANCEL_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.core.prelude.Future
use std.core.prelude.Poll
use std.core.prelude.Context
use std.core.prelude.Waker
use std.core.prelude.RawWaker
use std.core.prelude.RawWakerVTable
use std.asyn.sync.AsyncMutex
use std.asyn.sync.AsyncMutexGuard
use std.asyn.sync.AsyncMutexLockFuture
use std.asyn.sync.AsyncSemaphore
use std.asyn.sync.AsyncSemaphorePermit
use std.asyn.sync.AsyncSemaphoreAcquireFuture

@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

fn null_cx() -> Context {
    Context {
        waker_val: Waker {
            raw: RawWaker {
                data: 0 as *const u8,
                vtable: 0 as *const RawWakerVTable,
            },
        },
    }
}

// The readiness of each poll is reported through `flag` (inspecting the returned Option by pattern
// match would move/drop the guard and release the lock behind the test's back).
fn poll_m(f: mut_view<AsyncMutexLockFuture<i64>>, cx: mut_view<Context>, flag: *mut bool) -> Option<AsyncMutexGuard<i64>> {
    match f.poll_lock(mut_view(*cx)) {
        Poll.Ready(g) => {
            unsafe { *flag = true; }
            Option.Some(g)
        },
        Poll.Pending => {
            unsafe { *flag = false; }
            Option.None
        },
    }
}

fn poll_s(f: mut_view<AsyncSemaphoreAcquireFuture>, cx: mut_view<Context>, flag: *mut bool) -> Option<AsyncSemaphorePermit> {
    match f.poll(mut_view(*cx)) {
        Poll.Ready(p) => {
            unsafe { *flag = true; }
            Option.Some(p)
        },
        Poll.Pending => {
            unsafe { *flag = false; }
            Option.None
        },
    }
}

fn try_is_free(m: view<AsyncMutex<i64>>) -> bool {
    match m.try_lock() {
        Option.Some(_) => true,
        Option.None => false,
    }
}

pub fn main() -> i32 {
    let mut fails: i32 = 0i32;
    let mut cx = null_cx();
    let mut rdy: bool = false;
    let p_rdy = unsafe { address_of_mut(rdy) };

    // S1: a queued waiter is cancelled; the release goes to the next waiter.
    let m1 = AsyncMutex.new(0i64);
    {
        let g0 = m1.try_lock();
        let mut fb = m1.lock_async();
        let mut fc = m1.lock_async();
        let rb = poll_m(mut_view(fb), mut_view(cx), p_rdy);
        if rdy { fails = fails + 1i32; }
        let rc = poll_m(mut_view(fc), mut_view(cx), p_rdy);
        if rdy { fails = fails + 2i32; }
        {
            let fb_moved = fb;
        }
        {
            let g_moved = g0;
        }
        let rc2 = poll_m(mut_view(fc), mut_view(cx), p_rdy);
        if !rdy { fails = fails + 4i32; }
        if try_is_free(view(m1)) { fails = fails + 8i32; }
    }
    if !try_is_free(view(m1)) { fails = fails + 16i32; }

    // S2: the lock was already handed to B (granted) when B is cancelled before re-polling:
    // the grant must be forwarded to C, and with no C the mutex must become free.
    let m2 = AsyncMutex.new(0i64);
    {
        let g0 = m2.try_lock();
        let mut fb = m2.lock_async();
        let mut fc = m2.lock_async();
        let rb = poll_m(mut_view(fb), mut_view(cx), p_rdy);
        let rc = poll_m(mut_view(fc), mut_view(cx), p_rdy);
        {
            let g_moved = g0;
        }
        // lock now owned by B (granted); B is cancelled without polling again
        if try_is_free(view(m2)) { fails = fails + 32i32; }
        {
            let fb_moved = fb;
        }
        let rc2 = poll_m(mut_view(fc), mut_view(cx), p_rdy);
        if !rdy { fails = fails + 64i32; }
        if try_is_free(view(m2)) { fails = fails + 128i32; }
    }
    if !try_is_free(view(m2)) { fails = fails + 256i32; }

    let m3 = AsyncMutex.new(0i64);
    {
        let g0 = m3.try_lock();
        let mut fb = m3.lock_async();
        let rb = poll_m(mut_view(fb), mut_view(cx), p_rdy);
        {
            let g_moved = g0;
        }
        {
            let fb_moved = fb;
        }
    }
    if !try_is_free(view(m3)) { fails = fails + 512i32; }

    // S3: FIFO hand-off B then C: while B holds the guard C stays queued.
    let m4 = AsyncMutex.new(0i64);
    {
        let g0 = m4.try_lock();
        let mut fb = m4.lock_async();
        let mut fc = m4.lock_async();
        let rb = poll_m(mut_view(fb), mut_view(cx), p_rdy);
        let rc = poll_m(mut_view(fc), mut_view(cx), p_rdy);
        {
            let g_moved = g0;
        }
        let rc2 = poll_m(mut_view(fc), mut_view(cx), p_rdy);
        if rdy { fails = fails + 1024i32; }
        let rb2 = poll_m(mut_view(fb), mut_view(cx), p_rdy);
        if !rdy { fails = fails + 2048i32; }
        let rc3 = poll_m(mut_view(fc), mut_view(cx), p_rdy);
        if rdy { fails = fails + 4096i32; }
        {
            let gb = rb2;
        }
        let rc4 = poll_m(mut_view(fc), mut_view(cx), p_rdy);
        if !rdy { fails = fails + 8192i32; }
    }
    if !try_is_free(view(m4)) { fails = fails + 16384i32; }

    // S4: semaphore: cancelled queued waiter and cancelled granted waiter both forward the permit.
    let sem = AsyncSemaphore.new(1usize);
    {
        let p0 = sem.try_acquire();
        let mut fb = sem.acquire();
        let mut fc = sem.acquire();
        let rb = poll_s(mut_view(fb), mut_view(cx), p_rdy);
        let rc = poll_s(mut_view(fc), mut_view(cx), p_rdy);
        {
            let fb_moved = fb;
        }
        {
            let p_moved = p0;
        }
        let rc2 = poll_s(mut_view(fc), mut_view(cx), p_rdy);
        if !rdy { fails = fails + 32768i32; }
        if sem.available_permits() != 0usize { fails = fails + 65536i32; }
    }
    if sem.available_permits() != 1usize { fails = fails + 131072i32; }

    {
        let p0 = sem.try_acquire();
        let mut fb = sem.acquire();
        let rb = poll_s(mut_view(fb), mut_view(cx), p_rdy);
        {
            let p_moved = p0;
        }
        if sem.available_permits() != 0usize { fails = fails + 262144i32; }
        {
            let fb_moved = fb;
        }
    }
    if sem.available_permits() != 1usize { fails = fails + 524288i32; }

    if fails != 0i32 {
        print("FAIL qa_cancel_waiters ");
        print_int(fails as i64);
        print("\\n");
        return 1;
    }
    print("OK qa_cancel_waiters ");
    print_int(fails as i64);
    print("\\n");
    0
}
"""

QA_HANDLE_HEADER = """// test: run
// modes: interp native
// timeout: 60
// stdout: OK qa_handle_cancel_await 2 8\\n
"""

QA_HANDLE_SOURCES = COMMON_PREREQS + [
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
]

QA_HANDLE_MAIN = """module main

use std.core.option.Option
use std.core.result.Result
use std.asyn.executor.LocalExecutor
use std.asyn.task.LocalTaskHandle
use std.asyn.task.TaskResult
use std.asyn.task.TaskError
use std.asyn.task.TaskControlBlock
use std.asyn.task.tcb_poll_fn

@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

fn check(cond: bool) {
    if !cond {
        loop {}
    }
}

// A future that never completes and counts how often it is dropped.
struct DropProbe {
    pub counter: *mut i64,
}

impl Future for DropProbe {
    type Output = i64;
    fn poll(self: mut_view<DropProbe>, cx: mut_view<Context>) -> Poll<i64> {
        Poll.Pending
    }
}

impl Drop for DropProbe {
    fn drop(self: mut_view<DropProbe>) {
        unsafe { *self.counter = *self.counter + 1i64; }
    }
}

fn poll_probe(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<DropProbe, i64>;
    tcb_poll_fn<DropProbe, i64>(tcb, cx)
}

struct Yielder {
    pub step: i32,
}

impl Future for Yielder {
    type Output = i64;
    fn poll(self: mut_view<Yielder>, cx: mut_view<Context>) -> Poll<i64> {
        let st = self.step;
        if st < 3i32 {
            self.step = st + 1i32;
            let mut w = cx.waker();
            view(w).wake_by_ref();
            return Poll.Pending;
        }
        Poll.Ready(7i64)
    }
}

fn poll_yielder(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<Yielder, i64>;
    tcb_poll_fn<Yielder, i64>(tcb, cx)
}

// Awaits another task's handle (the TaskHandle Future impl + join-waker path).
struct Awaiter {
    pub h: LocalTaskHandle<i64>,
}

impl Future for Awaiter {
    type Output = i64;
    fn poll(self: mut_view<Awaiter>, cx: mut_view<Context>) -> Poll<i64> {
        match self.h.poll(mut_view(*cx)) {
            Poll.Ready(r) => {
                match r {
                    Result.Ok(v) => Poll.Ready(v + 1i64),
                    Result.Err(_) => Poll.Ready(-1i64),
                }
            },
            Poll.Pending => Poll.Pending,
        }
    }
}

fn poll_awaiter(raw: *mut u8, cx: *mut u8) -> u32 {
    let tcb = raw as *mut TaskControlBlock<Awaiter, i64>;
    tcb_poll_fn<Awaiter, i64>(tcb, cx)
}

pub fn main() -> i32 {
    let mut drops: i64 = 0i64;
    let p_drops = unsafe { address_of_mut(drops) };
    let mut exec = LocalExecutor.new();

    // Cancel before the first poll, and cancel after one poll (task idle): each future is dropped once.
    let hc1: LocalTaskHandle<i64> = exec.spawn_local(DropProbe { counter: p_drops }, poll_probe);
    view(hc1).cancel();
    let hc2: LocalTaskHandle<i64> = exec.spawn_local(DropProbe { counter: p_drops }, poll_probe);
    exec.try_tick();
    exec.try_tick();
    view(hc2).cancel();

    // Await-a-handle: inner yields 3 times and returns 7; the awaiter returns 7 + 1.
    let hin = exec.spawn_local(Yielder { step: 0i32 }, poll_yielder);
    let hout = exec.spawn_local(Awaiter { h: hin }, poll_awaiter);

    exec.run();

    let c1 = match hc1.join() {
        TaskResult.Cancelled => 1i64,
        _ => 0i64,
    };
    let c2 = match hc2.join() {
        TaskResult.Cancelled => 1i64,
        _ => 0i64,
    };
    check(c1 == 1i64);
    check(c2 == 1i64);
    let out = match hout.join() {
        TaskResult.Completed(v) => v,
        _ => -100i64,
    };
    check(out == 8i64);
    check(drops == 2i64);

    print("OK qa_handle_cancel_await ");
    print_int(drops);
    print(" ");
    print_int(out);
    print("\\n");
    0
}
"""

BUNDLES = {
    "qa_handle_cancel_await.ax": (QA_HANDLE_HEADER, QA_HANDLE_SOURCES, QA_HANDLE_MAIN),
    "qa_cancel_waiters.ax": (QA_CANCEL_HEADER, QA_CANCEL_SOURCES, QA_CANCEL_MAIN),
    "local_executor_rc.ax": (LOCAL_RC_HEADER, LOCAL_RC_SOURCES, LOCAL_RC_MAIN),
    "work_stealing_executor.ax": (WORK_STEALING_HEADER, WORK_STEALING_SOURCES, WORK_STEALING_MAIN),
    "work_stealing_spawn_tree.ax": (SPAWN_TREE_HEADER, SPAWN_TREE_SOURCES, SPAWN_TREE_MAIN),
    "async_semaphore_limits.ax": (SEMAPHORE_HEADER, SEMAPHORE_SOURCES, SEMAPHORE_MAIN),
    "lost_wake_prevention.ax": (LOST_WAKE_HEADER, LOST_WAKE_SOURCES, LOST_WAKE_MAIN),
    "async_mutex_across_await.ax": (ASYNC_MUTEX_HEADER, ASYNC_MUTEX_SOURCES, ASYNC_MUTEX_MAIN),
    "async_channel_pipeline.ax": (ASYNC_CHANNEL_HEADER, ASYNC_CHANNEL_SOURCES, ASYNC_CHANNEL_MAIN),
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
            print("ERROR: async executor test bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            print("Run `python tests/std/async/executor/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK async executor bundles match live std/async\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
