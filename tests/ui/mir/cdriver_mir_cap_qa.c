#define AX_UNIT_STANDALONE
#include "unit.h"
#include "mir/mir.h"
#include "mir/cap/cap.h"
#include "mir/regions/region.h"

static void test_qa_region_relate_projections(void) {
    // 1. Index projections
    AxMirProjection proj_idx_1 = { .kind = AX_MIR_PROJ_INDEX, .index_local = {10} };
    AxMirProjection proj_idx_2 = { .kind = AX_MIR_PROJ_INDEX, .index_local = {10} };
    AxMirProjection proj_idx_other = { .kind = AX_MIR_PROJ_INDEX, .index_local = {20} };

    AxMirPlace p_idx_1 = { .local = {1}, .proj_count = 1, .projs = &proj_idx_1 };
    AxMirPlace p_idx_2 = { .local = {1}, .proj_count = 1, .projs = &proj_idx_2 };
    AxMirPlace p_idx_diff = { .local = {1}, .proj_count = 1, .projs = &proj_idx_other };

    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_idx_1, &p_idx_2), AX_MIR_REGION_SAME);
    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_idx_1, &p_idx_diff), AX_MIR_REGION_UNKNOWN);

    // 2. Downcast projections
    AxMirProjection proj_down_v0 = { .kind = AX_MIR_PROJ_DOWNCAST, .variant_idx = 0 };
    AxMirProjection proj_down_v0_b = { .kind = AX_MIR_PROJ_DOWNCAST, .variant_idx = 0 };
    AxMirProjection proj_down_v1 = { .kind = AX_MIR_PROJ_DOWNCAST, .variant_idx = 1 };

    AxMirPlace p_down_0 = { .local = {2}, .proj_count = 1, .projs = &proj_down_v0 };
    AxMirPlace p_down_0_b = { .local = {2}, .proj_count = 1, .projs = &proj_down_v0_b };
    AxMirPlace p_down_1 = { .local = {2}, .proj_count = 1, .projs = &proj_down_v1 };

    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_down_0, &p_down_0_b), AX_MIR_REGION_SAME);
    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_down_0, &p_down_1), AX_MIR_REGION_DISJOINT);

    // 3. Deref projections
    AxMirProjection proj_deref = { .kind = AX_MIR_PROJ_DEREF };
    AxMirProjection proj_deref_b = { .kind = AX_MIR_PROJ_DEREF };
    AxMirProjection proj_f = { .kind = AX_MIR_PROJ_FIELD, .field_idx = 0 };
    AxMirProjection deref_then_field[] = { proj_deref, proj_f };

    AxMirPlace p_deref_1 = { .local = {3}, .proj_count = 1, .projs = &proj_deref };
    AxMirPlace p_deref_2 = { .local = {3}, .proj_count = 1, .projs = &proj_deref_b };
    AxMirPlace p_deref_field = { .local = {3}, .proj_count = 2, .projs = deref_then_field };

    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_deref_1, &p_deref_2), AX_MIR_REGION_SAME);
    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_deref_1, &p_deref_field), AX_MIR_REGION_OVERLAPS);
    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_deref_field, &p_deref_1), AX_MIR_REGION_OVERLAPS);

    // 4. Mismatched projection kinds
    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_idx_1, &p_down_0), AX_MIR_REGION_DISJOINT); // different locals
    AxMirPlace p_mismatch_field = { .local = {1}, .proj_count = 1, .projs = &proj_f };
    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_idx_1, &p_mismatch_field), AX_MIR_REGION_UNKNOWN);

    // 5. Nested projections
    AxMirProjection projs_f1_f2[] = { { .kind = AX_MIR_PROJ_FIELD, .field_idx = 1 }, { .kind = AX_MIR_PROJ_FIELD, .field_idx = 2 } };
    AxMirProjection projs_f1_f3[] = { { .kind = AX_MIR_PROJ_FIELD, .field_idx = 1 }, { .kind = AX_MIR_PROJ_FIELD, .field_idx = 3 } };
    AxMirPlace p_f1_f2 = { .local = {4}, .proj_count = 2, .projs = projs_f1_f2 };
    AxMirPlace p_f1_f3 = { .local = {4}, .proj_count = 2, .projs = projs_f1_f3 };

    AX_CHECK_EQ_INT(ax_mir_region_relate(&p_f1_f2, &p_f1_f3), AX_MIR_REGION_DISJOINT);
}

static void test_qa_cap_tracker_growth_and_lifetimes(void) {
    AxArena arena;
    ax_arena_init(&arena, 0);
    AxMirCapTracker *tracker = ax_mir_cap_tracker_new(&arena);

    AX_CHECK(tracker != NULL);
    AX_CHECK_EQ_INT(tracker->count, 0);
    AX_CHECK_EQ_INT(tracker->capacity, 16);

    // Add 25 entries to trigger reallocation (16 -> 32)
    for (size_t i = 0; i < 25; i++) {
        AxMirProjection proj = { .kind = AX_MIR_PROJ_FIELD, .field_idx = (uint32_t)i };
        AxMirPlace p = { .local = {(uint32_t)(i + 1)}, .proj_count = 1, .projs = &proj };
        ax_mir_cap_tracker_add(tracker, &p, (i % 2 == 0) ? AX_MIR_VIEW_READ : AX_MIR_VIEW_MUT);
    }

    AX_CHECK_EQ_INT(tracker->count, 25);
    AX_CHECK(tracker->capacity >= 32);

    // Verify all places preserved and distinct
    for (size_t i = 0; i < 25; i++) {
        AX_CHECK_EQ_INT(tracker->caps[i].place.local.v, i + 1);
        AX_CHECK_EQ_INT(tracker->caps[i].place.proj_count, 1);
        AX_CHECK(tracker->caps[i].place.projs != NULL);
        AX_CHECK_EQ_INT(tracker->caps[i].place.projs[0].field_idx, i);
        AX_CHECK_EQ_INT(tracker->caps[i].view, (i % 2 == 0) ? AX_MIR_VIEW_READ : AX_MIR_VIEW_MUT);
    }

    // Pop 10 entries
    for (size_t i = 0; i < 10; i++) {
        ax_mir_cap_tracker_pop(tracker);
    }
    AX_CHECK_EQ_INT(tracker->count, 15);

    // Pop remaining 15 entries
    for (size_t i = 0; i < 15; i++) {
        ax_mir_cap_tracker_pop(tracker);
    }
    AX_CHECK_EQ_INT(tracker->count, 0);

    // Edge case: Pop when count == 0 should not underflow or crash
    ax_mir_cap_tracker_pop(tracker);
    ax_mir_cap_tracker_pop(tracker);
    AX_CHECK_EQ_INT(tracker->count, 0);

    ax_arena_destroy(&arena);
}

static void test_qa_cap_conflict_edge_cases(void) {
    AxArena arena;
    ax_arena_init(&arena, 0);
    AxMirCapTracker *tracker = ax_mir_cap_tracker_new(&arena);

    AxMirProjection proj_idx_i = { .kind = AX_MIR_PROJ_INDEX, .index_local = {10} };
    AxMirProjection proj_idx_j = { .kind = AX_MIR_PROJ_INDEX, .index_local = {11} };
    AxMirPlace p_arr_i = { .local = {5}, .proj_count = 1, .projs = &proj_idx_i };
    AxMirPlace p_arr_j = { .local = {5}, .proj_count = 1, .projs = &proj_idx_j };

    // Case 1: UNKNOWN overlap (dynamic indices) with READ views: no conflict
    ax_mir_cap_tracker_add(tracker, &p_arr_i, AX_MIR_VIEW_READ);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_arr_j, AX_MIR_VIEW_READ) == false);

    // Case 2: UNKNOWN overlap with MUT view: CONFLICT
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_arr_j, AX_MIR_VIEW_MUT) == true);
    ax_mir_cap_tracker_pop(tracker);

    // Case 3: UNKNOWN overlap when existing is MUT view: CONFLICT with READ and MUT
    ax_mir_cap_tracker_add(tracker, &p_arr_i, AX_MIR_VIEW_MUT);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_arr_j, AX_MIR_VIEW_READ) == true);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_arr_j, AX_MIR_VIEW_MUT) == true);
    ax_mir_cap_tracker_pop(tracker);

    // Case 4: Disjoint fields: no conflict even with MUT views
    AxMirProjection proj_f1 = { .kind = AX_MIR_PROJ_FIELD, .field_idx = 1 };
    AxMirProjection proj_f2 = { .kind = AX_MIR_PROJ_FIELD, .field_idx = 2 };
    AxMirPlace p_f1 = { .local = {6}, .proj_count = 1, .projs = &proj_f1 };
    AxMirPlace p_f2 = { .local = {6}, .proj_count = 1, .projs = &proj_f2 };

    ax_mir_cap_tracker_add(tracker, &p_f1, AX_MIR_VIEW_MUT);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_f2, AX_MIR_VIEW_MUT) == false);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_f2, AX_MIR_VIEW_READ) == false);
    ax_mir_cap_tracker_pop(tracker);

    // Case 5: Overlapping places (whole local vs field)
    AxMirPlace p_whole = { .local = {6}, .proj_count = 0, .projs = NULL };
    ax_mir_cap_tracker_add(tracker, &p_whole, AX_MIR_VIEW_READ);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_f1, AX_MIR_VIEW_READ) == false);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_f1, AX_MIR_VIEW_MUT) == true);
    ax_mir_cap_tracker_pop(tracker);

    ax_mir_cap_tracker_add(tracker, &p_whole, AX_MIR_VIEW_MUT);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_f1, AX_MIR_VIEW_READ) == true);
    AX_CHECK(ax_mir_cap_tracker_check_conflict(tracker, &p_f1, AX_MIR_VIEW_MUT) == true);
    ax_mir_cap_tracker_pop(tracker);

    ax_arena_destroy(&arena);
}

int main(void) {
    test_qa_region_relate_projections();
    test_qa_cap_tracker_growth_and_lifetimes();
    test_qa_cap_conflict_edge_cases();
    return ax_unit_exit_code();
}
