#include "mir/cap/cap.h"
#include "mir/regions/region.h"
#include <string.h>

AxMirCapTracker* ax_mir_cap_tracker_new(AxArena *arena) {
    AxMirCapTracker *tracker = ax_arena_alloc(arena, sizeof(AxMirCapTracker), _Alignof(AxMirCapTracker));
    tracker->arena = arena;
    tracker->capacity = 16;
    tracker->count = 0;
    tracker->caps = ax_arena_alloc(arena, tracker->capacity * sizeof(AxMirCap), _Alignof(AxMirCap));
    return tracker;
}

bool ax_mir_cap_tracker_check_conflict(const AxMirCapTracker *tracker, const AxMirPlace *place, AxMirView view) {
    for (size_t i = 0; i < tracker->count; i++) {
        AxMirCap *existing = &tracker->caps[i];
        AxMirRegion rel = ax_mir_region_relate(&existing->place, place);
        
        if (rel == AX_MIR_REGION_DISJOINT) {
            continue;
        }
        
        if (view == AX_MIR_VIEW_MUT || existing->view == AX_MIR_VIEW_MUT) {
            return true;
        }
    }
    return false;
}

void ax_mir_cap_tracker_add(AxMirCapTracker *tracker, const AxMirPlace *place, AxMirView view) {
    if (tracker->count >= tracker->capacity) {
        size_t new_cap = tracker->capacity * 2;
        AxMirCap *new_caps = ax_arena_alloc(tracker->arena, new_cap * sizeof(AxMirCap), _Alignof(AxMirCap));
        for (size_t i = 0; i < tracker->count; i++) {
            new_caps[i] = tracker->caps[i];
        }
        tracker->caps = new_caps;
        tracker->capacity = new_cap;
    }
    
    AxMirPlace new_place = *place;
    if (new_place.proj_count > 0) {
        new_place.projs = ax_arena_alloc(tracker->arena, new_place.proj_count * sizeof(AxMirProjection), _Alignof(AxMirProjection));
        memcpy(new_place.projs, place->projs, new_place.proj_count * sizeof(AxMirProjection));
    } else {
        new_place.projs = NULL;
    }
    
    tracker->caps[tracker->count].place = new_place;
    tracker->caps[tracker->count].view = view;
    tracker->count++;
}

void ax_mir_cap_tracker_pop(AxMirCapTracker *tracker) {
    if (tracker->count > 0) {
        tracker->count--;
    }
}

