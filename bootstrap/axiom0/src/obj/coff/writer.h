#ifndef AX_OBJ_COFF_WRITER_H
#define AX_OBJ_COFF_WRITER_H

#include "objmodel/objmodel.h"
#include <stdbool.h>

/**
 * Write a deterministic COFF object file (.obj) from an object model.
 * 
 * @param obj The object model containing sections, symbols, and relocations.
 * @param path The output file path.
 * @return true on success, false on failure.
 */
bool ax_coff_write(ax_objmodel_t *obj, const char *path);

#endif /* AX_OBJ_COFF_WRITER_H */
