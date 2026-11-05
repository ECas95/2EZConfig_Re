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
