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


# Include the common build rules for C shared utility
if(${use_installed_dependencies})
    include(deps/azure-c-shared-utility/configs/azure_iot_build_rules.cmake)
else()
    include(${SHARED_UTIL_FOLDER}/configs/azure_iot_build_rules.cmake)
endif()

set_platform_files(${SHARED_UTIL_FOLDER})

set(run_unittests ${original_run_unittests})

if(${memory_trace})
    add_definitions(-DGB_MEASURE_MEMORY_FOR_THIS -DGB_DEBUG_ALLOC)
endif()


include_directories(${CMAKE_CURRENT_LIST_DIR}/inc)

if(WIN32)
    include_directories($ENV{OpenSSLDir}/include)
endif()

set(uamqp_h_files
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
setTargetBuildProperties(uamqp)

target_link_libraries(uamqp)


if (${run_unittests})
    add_subdirectory(tests)
endif()

# The following "set" statetement exports across the project a global variable
set(UAMQP_INC_FOLDER ${CMAKE_CURRENT_LIST_DIR}/inc CACHE INTERNAL "This is the include folder for UAMQP" FORCE)
set(UAMQP_SRC_FOLDER ${CMAKE_CURRENT_LIST_DIR}/src CACHE INTERNAL "This is the lib folder for UAMQP" FORCE)

# Set CMAKE_INSTALL_LIBDIR if not defined
include(GNUInstallDirs)

if(${use_installed_dependencies})
    # Install uamqp
    set(package_location "cmake")

    if(NOT DEFINED CMAKE_INSTALL_LIBDIR)
        set(CMAKE_INSTALL_LIBDIR "lib")
    endif()

    install(TARGETS uamqp EXPORT uamqpTargets
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        RUNTIME DESTINATION ${CMAKE_INSTALL_LIBDIR}/../bin
        INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/azureiot
    )
    install(FILES ${uamqp_h_files} DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/azureiot/azure_uamqp_c)

    include(CMakePackageConfigHelpers)

    write_basic_package_version_file(
        "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}/${PROJECT_NAME}ConfigVersion.cmake"
        VERSION ${UAMQP_VERSION}
        COMPATIBILITY SameMajorVersion
    )

    configure_file("configs/${PROJECT_NAME}Config.cmake"
        "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}/${PROJECT_NAME}Config.cmake"
        COPYONLY
    )

    install(EXPORT uamqpTargets
        FILE
            "${PROJECT_NAME}Targets.cmake"
        DESTINATION
            ${package_location}
    )

    install(
        FILES
            "configs/${PROJECT_NAME}Config.cmake"
            "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}/${PROJECT_NAME}ConfigVersion.cmake"
        DESTINATION
            ${package_location}
    )
else()
    set(install_staticlibs
        uamqp
    )
    install(FILES ${uamqp_h_files}
        DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/azure_uamqp_c)
    install(TARGETS ${install_staticlibs}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
endif()

compileTargetAsC99(uamqp)
