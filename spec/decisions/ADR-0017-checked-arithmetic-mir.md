# ADR-0017 — Checked arithmetic in MIR without tuples

## Tóm tắt
Để giải quyết sự phụ thuộc vòng tròn giữa bộ tạo MIR (cần tuples cho kiểu trả về của `CheckedBinaryOp`) và T117 (thêm hỗ trợ tuples vào interpreter), chúng ta thay thế `AX_MIR_RVALUE_CHECKED_BINARY_OP` bằng `AX_MIR_RVALUE_OVERFLOWS_BINARY_OP` (trả về `bool`). Việc kiểm tra tràn số ở MIR sẽ được biểu diễn bằng cách tính `bool` tràn số trước, gọi terminator `Assert`, và sau đó thực hiện phép tính `AX_MIR_RVALUE_BINARY_OP` thông thường nếu assert thành công. Quyết định này giữ cho interpreter v0.1 đơn giản (không cần sửa đổi lớn về bộ nhớ) mà vẫn đạt được mục tiêu biểu diễn tường minh các nhánh panic trên đồ thị MIR.

## Context
Task T116 requires the MIR builder to lower checked arithmetic (addition, subtraction, multiplication, division, modulo, shifts, and unary negation) into explicit `Assert` terminators. This ensures the panic control flow is explicit in the MIR graph for the native backend (T023).

In Rust, this is traditionally represented via a `CheckedBinaryOp` Rvalue that returns a tuple of `(result, overflow_bool)`. The builder emits this operation, extracts the boolean, asserts on it, and extracts the result.

However, the current axiom0 interpreter (`interp.c`) uses a simple `uint64_t v` for all locals. It does not support tuples or aggregates (this is the goal of T117). Using `CheckedBinaryOp` would force T116 to implement the interpreter value model, but T116 is explicitly scoped to have "minimal interpreter support" and is a prerequisite for T117.

## Decision
We change the MIR representation of checked arithmetic to avoid tuples entirely:

1. **Replace `CHECKED_BINARY_OP`**:
   `AX_MIR_RVALUE_CHECKED_BINARY_OP` in `mir.h` is replaced by `AX_MIR_RVALUE_OVERFLOWS_BINARY_OP` (which takes the same fields: `op`, `lhs`, `rhs`). This new Rvalue evaluates the operation but returns a `bool`: `true` if it would overflow, `false` otherwise.

2. **Builder Lowering for `+`, `-`, `*`**:
   The MIR builder will emit the following sequence for checked operations:
   ```
   _temp_bool = OverflowsBinaryOp(Add, a, b);
   _cond = Not(_temp_bool); // Assert expects true for success
   Assert(_cond, expected=true) -> [success: L_ok, panic: L_panic];
   L_ok:
   _result = BinaryOp(Add, a, b);
   ```

3. **Builder Lowering for `/`, `%`, shifts, and unary `-`**:
   These do not need new intrinsic Rvalues. The builder can emit standard MIR comparisons to compute the boolean condition. For example, for division `a / b`:
   ```
   _is_zero = BinaryOp(Eq, b, 0);
   _cond_zero = Not(_is_zero);
   Assert(_cond_zero, expected=true) -> ...
   ```
   (and similarly checking for `a == MIN && b == -1`). Unary minus overflow is just `a == MIN`.

4. **Interpreter Semantics**:
   The interpreter implements `AX_MIR_RVALUE_OVERFLOWS_BINARY_OP` simply by returning the boolean result of the overflow check. The actual `AX_MIR_RVALUE_BINARY_OP` will still intrinsically trap if it overflows (as required by `SPEC-03`), but since it is guarded by `Assert`, this inner trap will never be hit.

## Consequences
- **Unblocks T116**: We no longer need tuple support in the interpreter to lower checked arithmetic.
- **Explicit CFG**: The panic edges are correctly represented in the MIR graph.
- **Double Evaluation**: In the interpreter, the operands and the operation might be evaluated twice (once for `Overflows`, once for `BinaryOp`), but since operands in MIR are trivial (`Copy` or `Move` of locals/constants), there are no side-effect concerns.
- **Backend Optimisation**: The native backend can either peephole optimize the `Overflows` + `Assert` + `BinaryOp` pattern back into a single hardware instruction (like `adds` or `jo`), or simply emit the check explicitly.

Revisit: yes (when the optimizer or native backend is implemented, we may consider re-fusing this or keeping the explicit check pattern based on lowering complexity).
