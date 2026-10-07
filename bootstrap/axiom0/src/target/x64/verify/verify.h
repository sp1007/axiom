#ifndef AX_TARGET_X64_VERIFY_VERIFY_H
#define AX_TARGET_X64_VERIFY_VERIFY_H

#include "target/x64/mir/mi.h"
#include "target/x64/frame/frame.h"

void ax_x64_verify(const AxX64MIBody *body, const AxX64FrameLayout *layout);

#endif
