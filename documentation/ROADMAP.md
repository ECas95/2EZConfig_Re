# Static audit and modernization roadmap

**Status: proposed, not implemented.** This audit is based on reading the current fork source. It is not a report of executed builds, hardware tests or proven exploits. Each item requires independent reproduction and tests.

## P0 — Reliability and safety

| ID | Evidence | Proposed improvement | Definition of done |
| --- | --- | --- | --- |
| P0-01 | `src/libs/patches/patch_store.cpp`: raw memory writes without checking image boundaries or `VirtualProtect` success | Validate destination address, byte length, match counts and expected original bytes before writing | Invalid/ambiguous patches are rejected with explicit diagnostics |
| P0-02 | `src/libs/settings/settings.cpp`: JSON deserialization without recovery, direct overwriting | Schema validation, migration, atomic saves, rolling backups, restore UI | Corrupted JSON retains last good settings and offers recovery |
| P0-03 | `src/libs/injector/injector.cpp`: incomplete handle cleanup on failure, persistent remote allocation, unchecked remote-thread outcome | Audit process/handle lifecycle; propagate and display errors; bounded waits | Failure paths clean up resources, and launches report actionable outcomes |
| P0-04 | `src/2ez-dll/dll.cpp`: substantial setup and thread creation during DLL attach | Reduce loader-lock work; carefully stage post-load initialization | No startup regressions on supported game families or XP target |

## P1 — Engineering foundations

| ID | Evidence | Proposed improvement | Definition of done |
| --- | --- | --- | --- |
| P1-01 | Root CMake downloads to absent `toolchain/` directory and does not verify the archive checksum | Create directory, pin SHA-256, support local/offline toolchain | Clean configure is repeatable and integrity checked |
| P1-02 | `usb-hid-usage` and `minhook` reference moving `master` branches | Pin immutable commit IDs and document update policy | Repeated builds resolve identical source revisions |
| P1-03 | Release workflow publishes on every `master` push, ZIP omits notices/checksums | PR-only CI; controlled release trigger, package notices and SHA-256 | Pull requests build without releases; release assets are verifiable |
| P1-04 | `src/2ezconfig-exe/main.cpp` hosts extensive UI and launcher behavior | Split screens/settings/input/lights/patches into focused modules | Same UI behavior with isolated tests |
| P1-05 | No dedicated test suite in repository tree | CTest for JSON, game metadata and patch definitions plus Windows smoke tests | Pull requests run automated tests; XP/hardware checks documented |
| P1-06 | Unknown hashes default to first game selection | Explicitly mark unrecognized executables and request manual confirmation | Unknown executable is never presented as confidently auto-detected |

## P2 — Proposed new features

| New capability | Proposed behavior | Benefit |
| --- | --- | --- |
| **Cabinet Profile Manager** | Named presets per cabinet/game, export/import, diff and rollback | Quickly move between original IO, USB encoders, DIY controllers and testing |
| **Device Diagnostics Lab** | Live HID input monitor, axis graphs, output lighting tests and reconnect indicators | Debug hardware without running the game |
| **Visual IO Mapper** | Arcade control diagrams for EZ2DJ/AC, EZ2Dancer and Sabin | Map button/turntable/pedal/lighting hardware accurately |
| **Patch Compatibility Inspector** | Verify recognized executable, patch schema, byte guards, overlapping writes and expected match counts | Prevent incompatible settings from silently corrupting runtime state |
| **Setup Wizard** | Guided presets for Windows XP CRT cabinets and supported modern Windows setups | Reduce incompatible settings and setup errors |
| **Settings Health Center** | Automated backups, profile migrations, recovery, setting diffs and privacy-redacted support bundle | Prevent configuration loss |
| **HID Device Recovery** | Device reconnect and USB-port path-change remediation | More stable arcade operation |
| **Display / Audio Inspector** | Report measured refresh/display mode and available audio backend | Verify environment rather than assuming 60 Hz |
| **Accessibility / localization** | Adjustable UI scaling, English/Spanish interface, keyboard-first workflows | Better usability across different cabinets |

## Suggested milestones

1. **M0 — Baseline:** Fix clean builds, dependency pinning, release hygiene; establish regression matrix.
2. **M1 — Safety:** JSON backups/schema validation, patch preflight and improved diagnostics.
3. **M2 — Modularity:** Isolate portable core, add automated tests and refactor UI.
4. **M3 — Hardware tools:** Device Diagnostics Lab + Cabinet Profile Manager.
5. **M4 — Advanced UX:** Visual mapper, setup wizard, compatibility inspector and localization.

## Compatibility/test matrix

Track **pass / fail / not tested** per combination: Windows XP SP3 32-bit and modern Windows; EZ2DJ/EZ2AC, EZ2Dancer, Sabin; keyboard, HID, mouse axes and original arcade IO; original versus modified executables; patches enabled/disabled; CRT/60 Hz configurations; WASAPI on Vista+ only. Do not describe an untested combination as compatible.

Each roadmap item should become a focused issue and pull request with reproducible acceptance criteria. Preserve upstream licensing and attribution.