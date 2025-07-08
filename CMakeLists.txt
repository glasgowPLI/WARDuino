cmake_minimum_required(VERSION 3.15)

project(WARDuino VERSION 0.4.4)

# Define build options
option(BUILD_ESP "Build for ESP" OFF)
option(BUILD_EMULATOR "Build for emulator" OFF)
option(BUILD_UNITTEST "Build for testing" OFF)

# CHERI-related
option(BUILD_MORELLO_PURECAP "Compile for purecap Morello" OFF)
option(BUILD_MORELLO_HYBRID "Compile for hybrid Morello" OFF)
option(SOFTWARE_BOUND_CHECKS "Enable software-based bounds checks" OFF)
option(HARDWARE_BOUND_CHECKS "Enable hardware-based bounds checks" OFF)

# Language standards
set(CMAKE_CXX_STANDARD 17)

# Output version header
set(WARDUINO_VERSION_STRING "${PROJECT_VERSION}")
configure_file(src/config.h.in include/warduino/config.h)

# Warn if no top-level build target
if (NOT BUILD_ESP AND NOT BUILD_EMULATOR AND NOT BUILD_UNITTEST)
    message(WARNING "No top-level build target set. Nothing to do.")
endif()

# =========================
# CHERI CONFIGURATION
# =========================
if (BUILD_MORELLO_PURECAP)
    message(STATUS "Compiling for CHERI purecap (Morello)")
    add_compile_options(-march=morello -mabi=purecap)
    add_link_options(-march=morello -mabi=purecap)
    add_compile_definitions(PURECAP_MODE=1)
endif()

if (BUILD_MORELLO_HYBRID)
    message(STATUS "Compiling for CHERI hybrid (Morello)")
    add_compile_options(-march=morello -mabi=aapcs)
    add_link_options(-march=morello -mabi=aapcs)
    add_compile_definitions(PURECAP_MODE=0)
endif()

if (HARDWARE_BOUND_CHECKS)
    message(STATUS "Enabling CHERI hardware bound checks")
    add_compile_definitions(HARDWARE_BOUND_CHECKS=1)
endif()

if (SOFTWARE_BOUND_CHECKS)
    message(STATUS "Enabling software bound checks")
    add_compile_definitions(SOFTWARE_BOUND_CHECKS=1)
endif()

# =========================
# ESP-IDF Platform
# =========================
if (ESP_PLATFORM OR BUILD_ESP)
    if (NOT EXISTS $ENV{IDF_PATH}/tools/cmake/project.cmake)
        message(FATAL_ERROR "Can't find $IDF_PATH/tools/cmake/project.cmake. Make sure ESP-IDF is installed and \$IDF_PATH is set.")
    endif()
    set(EXTRA_COMPONENT_DIRS "platforms/ESP-IDF")
    include($ENV{IDF_PATH}/tools/cmake/project.cmake "${PROJECT_BINARY_DIR}/../include")
endif()

# =========================
# Emulator Build
# =========================
if (BUILD_EMULATOR)
    message(STATUS "Building emulator (CLI)")
    set(EXTERNAL_LIB_HEADERS lib/json/single_include)

    find_package(Threads REQUIRED)

    set(SOURCE_FILES
        src/WARDuino/WARDuino.cpp
        src/WARDuino/CallbackHandler.cpp
        src/Primitives/emulated.cpp
        src/Interpreter/instructions.cpp
        src/Interpreter/interpreter.cpp
        src/Memory/mem.cpp
        src/Utils/util.cpp
        src/Utils/util_arduino.cpp
        src/Utils/macros.cpp
        src/Utils/sockets.cpp
        src/Debug/debugger.cpp
        src/Edward/proxy.cpp
        src/Edward/proxy_supervisor.cpp
        src/Edward/RFC.cpp
    )

    add_definitions(-DINFO=0 -DDEBUG=0 -DTRACE=0 -DWARN=0)

    if (CMAKE_COMPILER_IS_GNUCXX)
        add_compile_options(-g -v -Wall -Wextra -Wunused -O3)
    endif()

    add_executable(wdcli platforms/CLI-Emulator/main.cpp ${SOURCE_FILES})
    target_link_libraries(wdcli PRIVATE Threads::Threads)
    target_include_directories(wdcli PRIVATE ${EXTERNAL_LIB_HEADERS} "${PROJECT_BINARY_DIR}/include")
endif()

# =========================
# Unit Test Build
# =========================
if (BUILD_UNITTEST)
    enable_testing()
    message(STATUS "Building unit tests")

    set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
    set(EXTERNAL_LIB_HEADERS lib/json/single_include)

    set(SOURCE_FILES
        src/WARDuino/WARDuino.cpp
        src/WARDuino/CallbackHandler.cpp
        src/Primitives/emulated.cpp
        src/Interpreter/instructions.cpp
        src/Interpreter/interpreter.cpp
        src/Memory/mem.cpp
        src/Utils/util.cpp
        src/Utils/util_arduino.cpp
        src/Utils/macros.cpp
        src/Utils/sockets.cpp
        src/Debug/debugger.cpp
        src/Edward/proxy.cpp
        src/Edward/proxy_supervisor.cpp
        src/Edward/RFC.cpp
    )

    if (CMAKE_COMPILER_IS_GNUCXX)
        add_compile_options(-g -v -Wall -Wextra -Wunused -O3)
    endif()

    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG release-1.12.1
    )
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)

    set(PATH_TO_UNIT_TEST ${PROJECT_SOURCE_DIR}/tests/unit)
    aux_source_directory(${PATH_TO_UNIT_TEST}/shared/ SHARED_SRC)
    file(GLOB TEST_SRC_FILES ${PATH_TO_UNIT_TEST}/*.cpp)

    foreach (TEST_FILE ${TEST_SRC_FILES})
        get_filename_component(TEST_NAME ${TEST_FILE} NAME_WE)
        add_executable(${TEST_NAME} ${TEST_FILE} ${SOURCE_FILES} ${SHARED_SRC})
        target_link_libraries(${TEST_NAME} gtest_main)
        target_include_directories(${TEST_NAME} PRIVATE ${EXTERNAL_LIB_HEADERS} "${PROJECT_BINARY_DIR}/include")
        add_test(${TEST_NAME} ${TEST_NAME})
    endforeach()
endif()
