add_executable(2EZWindowMode WIN32 main.cpp)
target_link_libraries(2EZWindowMode PRIVATE user32 shell32)
# Standalone x86 Win32 helper; no third-party graphics libraries or game hooks.
