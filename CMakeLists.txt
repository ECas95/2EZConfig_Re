cmake_minimum_required(VERSION 3.20)

# Auto-provision MinGW toolchain (GCC 12.2.0, win32 threads, XP-safe)
set(TOOLCHAIN_DIR "${CMAKE_SOURCE_DIR}/toolchain/mingw32" CACHE PATH "Windows XP-compatible 32-bit MinGW toolchain directory")
if(NOT EXISTS "${TOOLCHAIN_DIR}/bin/gcc.exe")
    # On clean checkouts the archive parent directory does not exist yet.
    file(MAKE_DIRECTORY "${CMAKE_SOURCE_DIR}/toolchain")
    set(TOOLCHAIN_URL "https://github.com/ben-rnd/2EZConfig-V2/releases/download/toolchain/win32-mingw-gcc-12.2-toolchain.7z")
    set(TOOLCHAIN_ARCHIVE "${CMAKE_SOURCE_DIR}/toolchain/mingw-toolchain.7z")
    message(STATUS "Downloading MinGW toolchain...")
    file(DOWNLOAD "${TOOLCHAIN_URL}" "${TOOLCHAIN_ARCHIVE}"
        SHOW_PROGRESS STATUS dl_status TLS_VERIFY ON
        EXPECTED_HASH SHA256=d76daf7a176f6e65ff75adc26efbadba89787bb14265696b94dce302cf1f8115
    )
    list(GET dl_status 0 dl_code)
    if(NOT dl_code EQUAL 0)
        file(REMOVE "${TOOLCHAIN_ARCHIVE}")
        message(FATAL_ERROR "Toolchain download/integrity verification failed: ${dl_status}")
    endif()
    message(STATUS "Extracting toolchain...")
    execute_process(
        COMMAND ${CMAKE_COMMAND} -E tar xf "${TOOLCHAIN_ARCHIVE}"
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/toolchain"
        RESULT_VARIABLE extract_result
    )
    if(NOT extract_result EQUAL 0)
        # cmake tar doesn't handle 7z — fall back to 7z command
        execute_process(
            COMMAND 7z x "${TOOLCHAIN_ARCHIVE}" -o"${CMAKE_SOURCE_DIR}/toolchain" -y
            RESULT_VARIABLE extract_result
        )
        if(NOT extract_result EQUAL 0)
            message(FATAL_ERROR "Toolchain extraction failed")
        endif()
    endif()
    file(REMOVE "${TOOLCHAIN_ARCHIVE}")
    if(NOT EXISTS "${TOOLCHAIN_DIR}/bin/gcc.exe" OR NOT EXISTS "${TOOLCHAIN_DIR}/bin/g++.exe")
        message(FATAL_ERROR "Toolchain extraction completed but compiler binaries are missing in ${TOOLCHAIN_DIR}/bin")
    endif()
endif()

set(CMAKE_C_COMPILER "${TOOLCHAIN_DIR}/bin/gcc.exe" CACHE FILEPATH "" FORCE)
set(CMAKE_CXX_COMPILER "${TOOLCHAIN_DIR}/bin/g++.exe" CACHE FILEPATH "" FORCE)
set(CMAKE_RC_COMPILER "${TOOLCHAIN_DIR}/bin/windres.exe" CACHE FILEPATH "" FORCE)

project(2EZConfig VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Build date stamp (YYYY.MM.DD)
string(TIMESTAMP BUILD_DATE "%Y.%m.%d")

# Windows XP target
add_compile_definitions(
    _WIN32_WINNT=0x0501
    WINVER=0x0501
    WIN32_LEAN_AND_MEAN
    NOMINMAX
    UNICODE
    _UNICODE
    __USE_MINGW_ANSI_STDIO=1
    BUILD_DATE="${BUILD_DATE}"
)

# MinGW cross-compile flags
add_compile_options(
    -march=i686
    -mstackrealign
    -Wall
    -Wextra
    -Wno-unused-parameter
)

add_link_options(
    -static
    -static-libgcc
    -static-libstdc++
    -Wl,--disable-dynamicbase
    -Wl,--image-base=0x400000
    -Wl,--enable-stdcall-fixup
    -Wl,--major-subsystem-version,5
    -Wl,--minor-subsystem-version,1
    -Wl,--major-os-version,5
    -Wl,--minor-os-version,1
)

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(-O2 -ffunction-sections -fdata-sections)
    add_link_options(-s -Wl,--gc-sections)
endif()

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(-g -O0)
    add_compile_definitions(DEBUG)
endif()

# Dependencies
include(FetchContent)

# GLFW 3.3.x — last version supporting Windows XP
# PATCH_COMMAND: replace GetModuleHandleExW (Vista+) with runtime detection
# so the binary loads on XP SP3. See patches/glfw-xp-compat.patch.
FetchContent_Declare(glfw
    GIT_REPOSITORY https://github.com/glfw/glfw.git
    GIT_TAG        3.3.10
    GIT_SHALLOW    TRUE
    PATCH_COMMAND  ${CMAKE_COMMAND} -P ${CMAKE_SOURCE_DIR}/patches/apply-glfw-xp-compat.cmake
)
set(GLFW_BUILD_DOCS     OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_TESTS    OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(GLFW_INSTALL        OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(glfw)

# ImGui
FetchContent_Declare(imgui
    GIT_REPOSITORY https://github.com/ocornut/imgui.git
    GIT_TAG        v1.91.1
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(imgui)

add_library(imgui STATIC
    ${imgui_SOURCE_DIR}/imgui.cpp
    ${imgui_SOURCE_DIR}/imgui_draw.cpp
    ${imgui_SOURCE_DIR}/imgui_tables.cpp
    ${imgui_SOURCE_DIR}/imgui_widgets.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_glfw.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_opengl2.cpp
)
target_include_directories(imgui PUBLIC
    ${imgui_SOURCE_DIR}
    ${imgui_SOURCE_DIR}/backends
)
target_link_libraries(imgui PUBLIC glfw opengl32)
target_compile_options(imgui PRIVATE -w)

# nlohmann/json — JSON serialization library
FetchContent_Declare(nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        v3.11.3
    GIT_SHALLOW    TRUE
)
set(JSON_BuildTests OFF CACHE BOOL "" FORCE)
set(JSON_Install    OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(nlohmann_json)

# usb-hid-usage — two-file C library (Apache-2.0) — usage page/ID to human-readable name
FetchContent_Declare(usbhidusage
    GIT_REPOSITORY https://github.com/smokris/usb-hid-usage.git
    # Immutable revision: verify and update intentionally.
    GIT_TAG        1a9085449bacdcbf3581b2ca694c0c158c3a8085
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(usbhidusage)

# MinHook — unified inline hooking library
FetchContent_Declare(minhook
    GIT_REPOSITORY https://github.com/TsudaKageyu/minhook.git
    # Immutable revision: verify and update intentionally.
    GIT_TAG        8af6b4acae5a9388fd742b56fa79ece89d96f823
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(minhook)
target_compile_options(minhook PRIVATE -w)

add_subdirectory(src/libs/hooks)
add_subdirectory(src/libs/hypersonik)
add_subdirectory(src/libs/hardlock)
add_subdirectory(src/libs/injector)
add_subdirectory(src/libs/logger)
add_subdirectory(src/libs/utilities)
add_subdirectory(src/libs/patches)
add_subdirectory(src/libs/settings)
add_subdirectory(src/libs/input)
add_subdirectory(src/libs/bindings)
add_subdirectory(src/2ezconfig-exe)
add_subdirectory(src/2ez-dll)

