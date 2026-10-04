# Driver registries (ADR-0005 section 2).
#
# src/driver/cmd_<name>.c   defines `const AxCommand axcmd_<name>`
# src/driver/emit_<name>.c  defines `const AxEmitter axemit_<name>`
# The tables `ax_commands` / `ax_emitters` are generated at configure time. Because the glob uses
# CONFIGURE_DEPENDS, adding or deleting such a file re-runs CMake and regenerates the tables.
#
# ax_generate_registry(<out-file> <src-dir>)

function(ax_registry_collect prefix glob_dir out_decls out_table symbol_prefix type)
  file(GLOB files CONFIGURE_DEPENDS "${glob_dir}/${prefix}_*.c")
  list(SORT files)
  set(decls "")
  set(table "")
  foreach(f IN LISTS files)
    get_filename_component(stem "${f}" NAME_WE)
    string(REGEX REPLACE "^${prefix}_" "" name "${stem}")
    if(NOT name MATCHES "^[a-z0-9_]+$")
      message(FATAL_ERROR "${f}: <name> in ${prefix}_<name>.c must match [a-z0-9_]+")
    endif()
    string(APPEND decls "extern const ${type} ${symbol_prefix}_${name};\n")
    string(APPEND table "    &${symbol_prefix}_${name},\n")
  endforeach()
  set(${out_decls} "${decls}" PARENT_SCOPE)
  set(${out_table} "${table}" PARENT_SCOPE)
endfunction()

function(ax_generate_registry out_file src_dir)
  ax_registry_collect(cmd "${src_dir}/driver" AX_COMMAND_DECLS AX_COMMAND_TABLE axcmd AxCommand)
  ax_registry_collect(emit "${src_dir}/driver" AX_EMITTER_DECLS AX_EMITTER_TABLE axemit AxEmitter)
  # configure_file rewrites the output only when its content changes (no needless rebuilds).
  configure_file("${AX_CMAKE_DIR}/registry.c.in" "${out_file}" @ONLY)
endfunction()
