#Copyright (c) Microsoft. All rights reserved.
#Licensed under the MIT license. See LICENSE file in the project root for full license information.

cmake_minimum_required(VERSION 2.8.11)
project(uamqp)

FILE(READ ${CMAKE_CURRENT_LIST_DIR}/version.txt UAMQP_VERSION)

option(run_unittests "set run_unittests to ON to run unittests (default is OFF)" OFF)
option(use_installed_dependencies "set use_installed_dependencies to ON to use installed packages instead of building dependencies from submodules" OFF)
option(memory_trace "set memory_trace to ON if memory usage is to be used, set to OFF to not use it" OFF)
option(use_custom_heap "use externally defined heap functions instead of the malloc family" OFF)

if(${use_custom_heap})
    add_definitions(-DGB_USE_CUSTOM_HEAP)
endif()

if(${no_logging})
    add_definitions(-DNO_LOGGING)
endif()

#do not add or build any tests of the dependencies
set(original_run_unittests ${run_unittests})
set(run_unittests OFF)
set(run_unittests ${original_run_unittests})

if(${memory_trace})
    add_definitions(-DGB_MEASURE_MEMORY_FOR_THIS -DGB_DEBUG_ALLOC)
endif()


include_directories(${CMAKE_CURRENT_LIST_DIR}/inc)


set(uamqp_h_files
    ./inc/azure_uamqp_c/macro_utils.h
    ./inc/azure_uamqp_c/refcount.h
    ./inc/azure_uamqp_c/amqp_types.h
    ./inc/azure_uamqp_c/amqpvalue.h
)

set(uamqp_c_files
    ./src/amqpvalue.c
)

add_library(uamqp
    ${uamqp_c_files}
    ${uamqp_h_files}
    )

target_link_libraries(uamqp)


if (${run_unittests})
    add_subdirectory(tests)
endif()

# The following "set" statetement exports across the project a global variable
set(UAMQP_INC_FOLDER ${CMAKE_CURRENT_LIST_DIR}/inc CACHE INTERNAL "This is the include folder for UAMQP" FORCE)
set(UAMQP_SRC_FOLDER ${CMAKE_CURRENT_LIST_DIR}/src CACHE INTERNAL "This is the lib folder for UAMQP" FORCE)

# Set CMAKE_INSTALL_LIBDIR if not defined
include(GNUInstallDirs)

set(install_staticlibs
    uamqp
)
install(FILES ${uamqp_h_files}
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/azure_uamqp_c)
install(TARGETS ${install_staticlibs}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})

function(compileTargetAsC99 theTarget)
  if (CMAKE_VERSION VERSION_LESS "3.1")
    if (CMAKE_C_COMPILER_ID STREQUAL "GNU")
      set_target_properties(${theTarget} PROPERTIES COMPILE_FLAGS "--std=c99")
    endif()
  else()
    set_target_properties(${theTarget} PROPERTIES C_STANDARD 99)
    set_target_properties(${theTarget} PROPERTIES CXX_STANDARD 11)
  endif()
endfunction()

compileTargetAsC99(uamqp)
