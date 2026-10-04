# axiom0 - Stage-0 Axiom compiler (C11). Written once by T004; later tasks only add files:
#   src/**/*.c                    compiled into the core library (all but driver/main.c)
#   src/driver/cmd_<name>.c       command registry   (cmake/AxiomRegistry.cmake)
#   src/driver/emit_<name>.c      inspect emitters   (cmake/AxiomRegistry.cmake)
#   tests/unit/**/*.c             -> axiom0-unit      (cmake/AxiomTests.cmake)
#   tests/**/cdriver_*.c          -> one test exe each (cmake/AxiomTests.cmake)
# Nobody edits this file or the files in cmake/ after T004.

cmake_minimum_required(VERSION 3.20)
project(axiom0 VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Debug CACHE STRING "Debug or Release" FORCE)
endif()

option(AX_WERROR "Treat compiler warnings as errors" ON)
option(AX_SANITIZE "Build with AddressSanitizer + UndefinedBehaviorSanitizer (gcc/clang)" OFF)

set(AX_CMAKE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
set(AX_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src")
get_filename_component(AX_REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(AX_GENERATED_DIR "${CMAKE_BINARY_DIR}/generated")

include("${AX_CMAKE_DIR}/AxiomRegistry.cmake")
include("${AX_CMAKE_DIR}/AxiomTests.cmake")

# Warning policy shared by every target (core, driver, tests).
add_library(ax_flags INTERFACE)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(ax_flags INTERFACE -Wall -Wextra -Wpedantic)
  if(AX_WERROR)
    target_compile_options(ax_flags INTERFACE -Werror)
  endif()
  if(AX_SANITIZE)
    target_compile_options(ax_flags INTERFACE -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(ax_flags INTERFACE -fsanitize=address,undefined)
  endif()
else()
  message(FATAL_ERROR "axiom0 supports gcc and clang only (found ${CMAKE_C_COMPILER_ID})")
endif()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

file(GLOB_RECURSE AX_CORE_SOURCES CONFIGURE_DEPENDS "${AX_SRC_DIR}/*.c")
list(REMOVE_ITEM AX_CORE_SOURCES "${AX_SRC_DIR}/driver/main.c")
list(SORT AX_CORE_SOURCES)

ax_generate_registry("${AX_GENERATED_DIR}/registry.c" "${AX_SRC_DIR}")

add_library(axiom0_core STATIC ${AX_CORE_SOURCES} "${AX_GENERATED_DIR}/registry.c")
target_include_directories(axiom0_core PUBLIC "${AX_SRC_DIR}")
target_compile_definitions(axiom0_core PRIVATE AX_VERSION_STRING="${PROJECT_VERSION}")
target_link_libraries(axiom0_core PUBLIC ax_flags)

add_executable(axiom0 "${AX_SRC_DIR}/driver/main.c")
target_link_libraries(axiom0 PRIVATE axiom0_core)

enable_testing()
ax_add_c_tests(axiom0_core "${AX_REPO_ROOT}" "${AX_GENERATED_DIR}")
