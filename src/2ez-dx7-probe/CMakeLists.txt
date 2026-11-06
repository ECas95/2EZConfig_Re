# Isolated legacy API capability probe. No game injection, no wrappers.
add_executable(2EZDx7Probe main.cpp)
target_link_libraries(2EZDx7Probe PRIVATE dxguid user32)
