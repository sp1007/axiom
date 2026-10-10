#ifndef AX_DRIVER_MANIFEST_H
#define AX_DRIVER_MANIFEST_H

#include <stdbool.h>

typedef struct AxPackageManifest {
    char name[128];
    char version[64];
    char kind[32];
    bool is_present;
} AxPackageManifest;

/* Reads axiom.toml at manifest_path.
 * Returns true if valid manifest with [package] name, false otherwise. */
bool ax_manifest_read(const char *manifest_path, AxPackageManifest *out);

#endif /* AX_DRIVER_MANIFEST_H */
