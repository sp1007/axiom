---
name: axiom-x64-backend
description: Backend knowledge for the Axiom compiler — LIR→x86-64 machine IR, instruction selection, register allocation (fixed-register bootstrap then linear scan), frame lowering, Windows x64 (MS) ABI and SysV ABI, direct machine-code encoding (REX/ModRM/SIB), COFF object writing, PE32+ linking with kernel32 imports, ELF64 writing/linking, and minimal CRT-free startup. Use for any task touching bootstrap/axiom0/src/{lir,abi,target,objmodel,obj,link}, native executables, calling conventions, relocations, or "exit code is wrong / exe crashes" debugging.
---

# x86-64 backend (Windows first, Linux second)

Pipeline (docs 0152, 0162, 0180, 0181): **Verified MIR → LIR → x64 Machine IR (virtual regs) →
ABI lowering → regalloc → frame lowering → encoder (bytes + relocations) → objmodel → COFF/ELF
writer → PE/ELF linker**. One x86 backend; only ABI + object format + linker + startup differ per OS.
Never emit assembly text; never call an external assembler/linker in the production path (tools are
test oracles only).

## Baseline first (doc 0152 §70-71)

Start dumb-but-correct: every MIR local gets a stack slot; each operation loads operands into fixed
scratch registers, computes, stores back. Mark it `BOOTSTRAP-SHORTCUT`. Linear-scan regalloc (T053)
comes only after native execution is green and differential tests exist to catch regressions.

## Windows x64 ABI (doc 0181, 0189)

- Integer/pointer args: RCX, RDX, R8, R9; float args XMM0–XMM3 (positional: arg 2 float → XMM1).
  Args 5+ on the stack at `[rsp+32]`, `[rsp+40]`… at the call instruction.
- Return: RAX / XMM0. Aggregates of size 1,2,4,8 returned in RAX; others via hidden pointer in RCX
  (then real args shift) and RAX returns that pointer. Aggregates >8 bytes or not power-of-2 are
  passed by pointer to a caller-made copy.
- Caller always reserves **32 bytes shadow space** above the return address, even for <4 args.
- RSP is 16-byte aligned **before** the `call` (so at function entry RSP ≡ 8 mod 16).
- Volatile: RAX RCX RDX R8 R9 R10 R11, XMM0–5. Non-volatile: RBX RBP RDI RSI RSP R12–R15, XMM6–15.
- Frame: `push rbp; mov rbp, rsp; sub rsp, N` (N keeps alignment and includes locals + spills +
  outgoing args + 32 shadow); epilogue `mov rsp, rbp; pop rbp; ret` / `leave; ret`. Unwind data
  (.pdata/.xdata, doc 0188) comes later; bootstrap uses `panic = abort`.
- The ABI description is data (`abi/win64.c`: arg regs, ret regs, volatile set, shadow size,
  alignment). Regalloc/isel read it; never hard-code ABI facts elsewhere.

SysV (Linux): args RDI RSI RDX RCX R8 R9 / XMM0–7, no shadow space, 128-byte red zone (do not
rely on it initially), callee-saved RBX RBP R12–R15.

## Encoding cheat-sheet (doc 0184)

`[legacy prefixes][REX][opcode][ModRM][SIB][disp][imm]`
- REX = `0100WRXB`: W=64-bit operand, R extends ModRM.reg, X extends SIB.index, B extends
  ModRM.rm / SIB.base / opcode reg. A REX (even `0x40`) is required to address SPL/BPL/SIL/DIL.
- ModRM = `mod(2) reg(3) rm(3)`; mod 11 = register direct; rm=100 → SIB follows; mod 00 & rm=101
  → RIP-relative disp32 in 64-bit mode.
- Special cases: base RSP/R12 always needs SIB (`0x24`); base RBP/R13 with no displacement must
  use mod 01 + disp8 0. Writes to 32-bit registers zero-extend to 64 bits; 8/16-bit writes do not.
- Common: `mov r32, imm32` = `B8+rd id`; `mov r/m64, r64` = `REX.W 89 /r`; `add r/m, r` = `01 /r`;
  `sub` = `29 /r`; `imul r, r/m` = `0F AF /r`; `cdq`/`cqo` + `idiv r/m` = `F7 /7`; `cmp` = `39 /r`;
  `setcc r/m8` = `0F 90+cc`; `movzx r32, r/m8` = `0F B6 /r`; `jcc rel32` = `0F 80+cc cd`;
  `jmp rel32` = `E9 cd`; `call rel32` = `E8 cd`; `ret` = `C3`; `lea r, m` = `8D /r`;
  `call [rip+disp32]` = `FF 15 cd` (import thunks via IAT).
- rel32 is relative to the **end of the instruction**. The encoder emits `Relocation{offset, kind,
  symbol, addend}` in target-neutral terms (REL32 with addend -4 when the field is last); the COFF
  writer maps to `IMAGE_REL_AMD64_REL32` (0x0004) / `ADDR64` (0x0001) / `ADDR32NB` (0x0003); the
  ELF writer to `R_X86_64_PC32`/`PLT32`/`64`.
- Validate every encoding form against GNU `as` (see axiom-testing). Division by zero and
  `INT_MIN / -1` trap in hardware — Axiom semantics decide what must happen (check before `idiv`).

## Objects and images

Read `references/pe-coff.md` when writing the COFF writer, the PE linker or the startup code; it has
the header layouts, field values and the minimal `ExitProcess` import recipe. For Linux read docs
0192/0053 (ELF64: `ET_REL` writer, `ET_EXEC` static linker, `_start` → `main` → `exit` syscall 60).

Startup (doc 0186, 0263 §10-12): Axiom `main` is not the OS entry. The linker (or a
compiler-generated startup object) provides `axiom_start` which calls `main`, then
`ExitProcess(eax)` on Windows (import from kernel32.dll via IAT) or `syscall exit` on Linux. No CRT.

## Debugging a native failure

1. Run the same program with `axiom0 run --interp` — if the oracle is also wrong, the bug is above
   the backend.
2. `axiom0 inspect --emit=lir|mc` and `objdump -d -M intel out.exe` to compare intended vs actual.
3. Check stack alignment at every call, shadow space, callee-saved restore, relocation addends.
4. Windows exit code of a crash is `0xC0000005` (access violation) — `$?` in bash shows it modulo
   256 as 5; treat unexpected 5/0xC0000005 as a crash, not a result.
