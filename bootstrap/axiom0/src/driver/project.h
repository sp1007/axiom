#ifndef AX_DRIVER_PROJECT_H
#define AX_DRIVER_PROJECT_H

#include <stdbool.h>
#include <stddef.h>
#include "diag/diag.h"
#include "source/source.h"
#include "driver/manifest.h"

typedef struct AxProjectFile {
    char disk_path[1024];
    char display_path[512];
    char module_path[256];
    FileId fid;
    bool is_main;
    bool is_std;
} AxProjectFile;

typedef struct AxProject {
    char root_dir[1024];
    AxPackageManifest manifest;
    AxProjectFile *files;
    size_t file_count;
    size_t file_cap;
    bool is_package;
    const char *std_root;
} AxProject;

/* Discovers project structure from an input path (directory or .ax file).
 * If std_root is found, also includes <std_root>/core/prelude.ax.
 * Discovered project files are sorted lexicographically for determinism. */
bool ax_project_discover(const char *input_path, const char *explicit_std_root, AxProject *proj, AxDiagSink *sink);

void ax_project_free(AxProject *proj);

#endif /* AX_DRIVER_PROJECT_H */
