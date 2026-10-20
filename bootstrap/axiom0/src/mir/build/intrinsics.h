#ifndef AX_MIR_BUILD_INTRINSICS_H
#define AX_MIR_BUILD_INTRINSICS_H

/* The one intrinsic table (T134, ADR-0004 s1).
 *
 * Every `@intrinsic fn` axiom0 accepts is listed in intrinsics.c together with how it is lowered. The driver
 * (declaration guard, annotation of the `@intrinsic` attribute with the table reference), the MIR builder and
 * the LIR lowering consult this table instead of matching names by hand. typeck sits below the MIR layer and
 * does not include this header: the driver writes the encoded reference into the attribute (see
 * ax_intrinsic_encode) and typeck copies it onto the callee expression of every call.
 */

#include "kernel/str.h"
#include "types/types.h"

/* How an intrinsic reaches the executors. */
typedef enum AxIntrinsicClass {
    AX_INTR_BUILTIN,   /* typeck retypes the callee to an AX_TY_BUILTIN_* kind (size_of, ptr_copy, ...) */
    AX_INTR_HOST,      /* host call: lowered to a call of the Axiom function __ax_host_<name> (ADR-0002) */
    AX_INTR_MIR_OP,    /* expanded by the MIR builder into MIR operations (wrapping/bit intrinsics) */
    AX_INTR_MIR_TERM   /* MIR terminator on the abort path (assert, panic, unreachable) */
} AxIntrinsicClass;

typedef enum AxIntrinsicOp {
    AX_INTR_OP_NONE,
    AX_INTR_OP_WRAPPING_ADD,
    AX_INTR_OP_WRAPPING_SUB,
    AX_INTR_OP_WRAPPING_MUL,
    AX_INTR_OP_WRAPPING_NEG,
    AX_INTR_OP_ROTATE_LEFT,
    AX_INTR_OP_ROTATE_RIGHT,
    AX_INTR_OP_LEADING_ZEROS,
    AX_INTR_OP_TRAILING_ZEROS,
    AX_INTR_OP_COUNT_ONES,
    AX_INTR_OP_ASSERT,
    AX_INTR_OP_PANIC,
    AX_INTR_OP_UNREACHABLE
} AxIntrinsicOp;

/* Integer width suffix of a per-width family (`wrapping_add_u64` -> U64). */
typedef enum AxIntrinsicWidth {
    AX_INTR_W_NONE,
    AX_INTR_W_I8, AX_INTR_W_I16, AX_INTR_W_I32, AX_INTR_W_I64, AX_INTR_W_ISIZE,
    AX_INTR_W_U8, AX_INTR_W_U16, AX_INTR_W_U32, AX_INTR_W_U64, AX_INTR_W_USIZE
} AxIntrinsicWidth;

typedef struct AxIntrinsicDesc {
    const char *name;        /* exact name, or the family prefix when per_width */
    AxIntrinsicClass cls;
    AxIntrinsicOp op;
    AxTypeKind builtin_ty;   /* AX_TY_BUILTIN_* when cls == AX_INTR_BUILTIN, 0 otherwise */
    bool per_width;          /* name is `<name>_<width>` for the ten integer widths */
    uint8_t generics;        /* number of generic parameters the declaration must have */
    /* Signature alternatives separated by '|': `p1,p2>ret`. Tokens: W (the family width type), i32 u32
     * i64 u64 usize bool unit never, cp8 (*const u8) mp8 (*mut u8) mp64 (*mut u64), `*` (any type,
     * not checked). An empty parameter list is written `>ret`. */
    const char *sig;
} AxIntrinsicDesc;

typedef struct AxIntrinsicRef {
    const AxIntrinsicDesc *desc;
    AxIntrinsicWidth width;
} AxIntrinsicRef;

/* Looks `name` up in the table. Returns false when no entry matches. */
bool ax_intrinsic_lookup(StrView name, AxIntrinsicRef *out);

/* True when `name` is a host intrinsic (lowered to `__ax_host_<name>`). */
bool ax_intrinsic_is_host(StrView name);

/* Packs / unpacks a reference into the non-zero 32-bit value typeck records on a call's callee. */
uint32_t ax_intrinsic_encode(const AxIntrinsicRef *ref);
bool ax_intrinsic_decode(uint32_t code, AxIntrinsicRef *out);

/* Interned integer type of a width (t_i8 .. t_usize) and its unsigned counterpart of equal size. */
TypeId ax_intrinsic_width_type(AxIntrinsicWidth w, const TypeInterner *in);
TypeId ax_intrinsic_width_unsigned_type(AxIntrinsicWidth w, const TypeInterner *in);
uint32_t ax_intrinsic_width_bits(AxIntrinsicWidth w);
bool ax_intrinsic_width_signed(AxIntrinsicWidth w);

/* Does the declared signature (a fn type plus the declaration's generic parameter count) match the
 * table entry? */
bool ax_intrinsic_signature_ok(const AxIntrinsicRef *ref, const AxType *fn_ty, size_t generic_count,
                               const TypeInterner *in);

#endif /* AX_MIR_BUILD_INTRINSICS_H */
