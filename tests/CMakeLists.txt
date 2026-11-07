add_executable(settings_io_tests
    settings_io_test.cpp
    ${CMAKE_SOURCE_DIR}/src/libs/settings/settings_io.cpp
)

target_include_directories(settings_io_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/src/libs/settings
)
target_link_libraries(settings_io_tests PRIVATE nlohmann_json::nlohmann_json)
add_test(NAME settings_io_tests COMMAND settings_io_tests)

add_executable(extension_events_tests extension_events_test.cpp)
target_link_libraries(extension_events_tests PRIVATE extension_events)
add_test(NAME extension_events_tests COMMAND extension_events_tests)

# Read-only display refresh enumeration guard (no GPU changes).
add_executable(display_refresh_tests display_refresh_test.cpp)
target_include_directories(display_refresh_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/src/2ez-dll/ddraw
)
target_link_libraries(display_refresh_tests PRIVATE user32)
add_test(NAME display_refresh_tests COMMAND display_refresh_tests)

# Fail-closed window mode safety policy (no game hooks, no binaries).
add_executable(presentation_policy_tests presentation_policy_test.cpp)
target_include_directories(presentation_policy_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/src/common/include
)
add_test(NAME presentation_policy_tests COMMAND presentation_policy_tests)

# Does not call a display driver on CI; validates no-interaction JSON path.
add_test(NAME dx7_probe_selftest COMMAND 2EZDx7Probe --self-test)

# Pure startup policy test; does not launch or inject any arcade title.
add_executable(startup_diagnostic_policy_tests startup_diagnostic_policy_test.cpp)
target_include_directories(startup_diagnostic_policy_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/src/common/include
)
add_test(NAME startup_diagnostic_policy_tests COMMAND startup_diagnostic_policy_tests)
