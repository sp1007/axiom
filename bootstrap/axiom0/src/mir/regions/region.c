#include "mir/regions/region.h"

AxMirRegion ax_mir_region_relate(const AxMirPlace *a, const AxMirPlace *b) {
    if (a->local.v != b->local.v) {
        return AX_MIR_REGION_DISJOINT;
    }
    
    size_t min_len = a->proj_count < b->proj_count ? a->proj_count : b->proj_count;
    for (size_t i = 0; i < min_len; i++) {
        AxMirProjection pa = a->projs[i];
        AxMirProjection pb = b->projs[i];
        if (pa.kind != pb.kind) {
            return AX_MIR_REGION_UNKNOWN;
        }
        if (pa.kind == AX_MIR_PROJ_FIELD) {
            if (pa.field_idx != pb.field_idx) {
                return AX_MIR_REGION_DISJOINT;
            }
        } else if (pa.kind == AX_MIR_PROJ_INDEX) {
            if (pa.index_local.v != pb.index_local.v) {
                return AX_MIR_REGION_UNKNOWN;
            }
        } else if (pa.kind == AX_MIR_PROJ_DOWNCAST) {
             if (pa.variant_idx != pb.variant_idx) {
                 return AX_MIR_REGION_DISJOINT;
             }
        } else if (pa.kind == AX_MIR_PROJ_DEREF) {
             // same deref
        } else {
             return AX_MIR_REGION_UNKNOWN;
        }
    }
    
    if (a->proj_count == b->proj_count) {
        return AX_MIR_REGION_SAME;
    } else {
        return AX_MIR_REGION_OVERLAPS; 
    }
}
