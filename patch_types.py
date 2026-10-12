import re
with open("bootstrap/axiom0/src/types/types.h", "r") as f:
    text = f.read()

text = text.replace("#define AX_TY_PARAM (AX_TY_INT_VAR + 12)",
"""#define AX_TY_PARAM (AX_TY_INT_VAR + 12)
#define AX_TY_VAR (AX_TY_INT_VAR + 13)""")

text = text.replace("} else if (k->kind == AX_TY_INT_VAR) {",
"""} else if (k->kind == AX_TY_INT_VAR || k->kind == AX_TY_VAR) {""")

text = text.replace("} else if (a->kind == AX_TY_INT_VAR) {",
"""} else if (a->kind == AX_TY_INT_VAR || a->kind == AX_TY_VAR) {""")

with open("bootstrap/axiom0/src/types/types.h", "w") as f:
    f.write(text)
