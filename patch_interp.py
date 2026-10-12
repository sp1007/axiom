import sys
import re

file = "bootstrap/axiom0/src/interp/interp.c"
with open(file, "r") as f:
    content = f.read()

content = re.sub(r'static bool execute_drop.*?return any_custom;\s*}', '', content, flags=re.DOTALL)

drop_handler = """                } else if (term->kind == AX_MIR_TERM_DROP) {
            if (term->drop_flag != 0) {
                AxMirPlace flag_place = {0};
                flag_place.local.v = term->drop_flag;
                TypeId flag_ty;
                uint8_t *flag_ptr = get_place_ptr(ctx, &frame, &flag_place, &flag_ty, NULL);
                if (*flag_ptr == 0) {
                    current_bb = term->drop.target;
                    continue;
                }
            }
            TypeId dest_ty;
            uint8_t *ptr = get_place_ptr(ctx, &frame, &term->drop.place, &dest_ty, NULL);
            execute_drop(ctx, &frame, dest_ty, ptr);
            current_bb = term->drop.target;"""

r = """                } else if (term->kind == AX_MIR_TERM_DROP) {
            AX_ICE("AX_MIR_TERM_DROP should have been elaborated away");
            current_bb = term->drop.target;"""

content = content.replace(drop_handler, r)

with open(file, "w") as f:
    f.write(content)
