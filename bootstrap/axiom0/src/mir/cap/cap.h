#ifndef AX_MIR_CAP_CAP_H
#define AX_MIR_CAP_CAP_H

#include "mir/mir.h"
#include <stdbool.h>

typedef struct AxMirCap {
    AxMirPlace place;
    AxMirView view;
} AxMirCap;

typedef struct AxMirCapTracker {
    AxArena *arena;
    AxMirCap *caps;
    size_t count;
    size_t capacity;
} AxMirCapTracker;

AxMirCapTracker* ax_mir_cap_tracker_new(AxArena *arena);
bool ax_mir_cap_tracker_check_conflict(const AxMirCapTracker *tracker, const AxMirPlace *place, AxMirView view);
void ax_mir_cap_tracker_add(AxMirCapTracker *tracker, const AxMirPlace *place, AxMirView view);
void ax_mir_cap_tracker_pop(AxMirCapTracker *tracker);

#endif // AX_MIR_CAP_CAP_H
