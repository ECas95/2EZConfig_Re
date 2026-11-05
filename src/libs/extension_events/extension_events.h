#pragma once
#include <string>
// A small, disabled-by-default local JSONL extension interface.
// Not a per-title memory hook or online-score adapter.
namespace ExtensionEvents {
void configure(const std::string& gameDirectory, const std::string& gameId, bool enabled);
bool publish(const char* eventName, const char* jsonObjectPayload);
bool isEnabled();
}
