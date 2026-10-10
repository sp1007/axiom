#define AX_UNIT_STANDALONE
#include "unit.h"
#include "mir/mir.h"
#include "mir/cap/cap.h"
#include "mir/regions/region.h"

static void test_region_relate(void) {
    AxMirPlace a = { .local = {1}, .proj_count = 0, .projs = NULL };
    AxMirPlace b = { .local = {1}, .proj_count = 0, .projs = NULL };
    AxMirPlace c = { .local = {2}, .proj_count = 0, .projs = NULL };
    
    AX_CHECK_EQ_INT(ax_mir_region_relate(&a, &b), AX_MIR_REGION_SAME);
    AX_CHECK_EQ_INT(ax_mir_region_relate(&a, &c), AX_MIR_REGION_DISJOINT);
    
    AxMirProjection proj_f1 = { .kind = AX_MIR_PROJ_FIELD, .field_idx = 1 };
    AxMirProjection proj_f2 = { .kind = AX_MIR_PROJ_FIELD, .field_idx = 2 };
    
    AxMirPlace a_f1 = { .local = {1}, .proj_count = 1, .projs = &proj_f1 };
    AxMirPlace a_f2 = { .local = {1}, .proj_count = 1, .projs = &proj_f2 };
    
    AX_CHECK_EQ_INT(ax_mir_region_relate(&a_f1, &a_f2), AX_MIR_REGION_DISJOINT);
    
    AxMirProjection projs_a_f1_f2[] = { proj_f1, proj_f2 };
    AxMirPlace a_f1_f2 = { .local = {1}, .proj_count = 2, .projs = projs_a_f1_f2 };
    
    AX_CHECK_EQ_INT(ax_mir_region_relate(&a_f1, &a_f1_f2), AX_MIR_REGION_OVERLAPS);
    AX_CHECK_EQ_INT(ax_mir_region_relate(&a_f1_f2, &a_f1), AX_MIR_REGION_OVERLAPS);
}

static void test_cap_tracker(void) {
    AxArena arena;
    ax_arena_init(&arena, 0);
    AxMirCapTracker *tracker = ax_mir_cap_tracker_new(&arena);
    
    AxMirPlace a = { .local = {1}, .proj_count = 0, .projs = NULL };
    
    // add READ view
    ax_mir_cap_tracker_add(tracker, &a, AX_MIR_VIEW_READ);
    
    // another READ view should NOT conflict
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &a, AX_MIR_VIEW_READ) == false);
    
    // MUT view SHOULD conflict
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &a, AX_MIR_VIEW_MUT) == true);
    
    // pop the READ view
    ax_mir_cap_tracker_pop(tracker);
    
    // now MUT view should NOT conflict
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &a, AX_MIR_VIEW_MUT) == false);
    
    ax_mir_cap_tracker_add(tracker, &a, AX_MIR_VIEW_MUT);
    
    // now anything should conflict
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &a, AX_MIR_VIEW_READ) == true);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &a, AX_MIR_VIEW_MUT) == true);
    
    AxMirPlace b = { .local = {2}, .proj_count = 0, .projs = NULL };
    // different local should NOT conflict
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &b, AX_MIR_VIEW_MUT) == false);
    
    ax_arena_destroy(&arena);
}

int main(void) {
    test_region_relate();
    test_cap_tracker();
    return ax_unit_exit_code();
}
