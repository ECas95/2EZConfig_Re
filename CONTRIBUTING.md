# Contributing to 2EZConfig_Re

This is a community fork of [ben-rnd/2EZConfig-V2](https://github.com/ben-rnd/2EZConfig-V2). Please retain upstream attribution, the [project license](LICENSE), and [third-party notices](THIRD_PARTY_LICENSES).

## Developer references

- [Development and test matrix](documentation/DEVELOPER_GUIDE.md)
- [Extension SDK and event contract](documentation/EXTENSION_EVENTS.md)
- [Proposed new hooks and compatibility registry](documentation/NEW_HOOKS.md)
- [Song pack manifest validation](documentation/CUSTOM_SONGS.md)
- [Score API and trust limits](documentation/SCORES_API.md)
- [Multiplayer protocol experiments](documentation/MULTIPLAYER.md)
- [Security disclosure](SECURITY.md) and [changelog](CHANGELOG.md)

Contributions that introduce new game hooks must identify the **exact executable fingerprint**, verify the callback timing and safely reject unsupported revisions. Never publish restricted media or commercial game assets to reproduce a bug. Companion API and offline utilities require tests, bounded input validation and explicit consent before network transfer.

## Changes and pull requests

1. Search issues and the [modernization roadmap](documentation/ROADMAP.md) before starting work.
2. Describe the problem, expected outcome, scope and risks.
3. Keep pull requests focused; avoid unrelated formatting or platform changes.
4. Include automated tests where possible and specific manual reproduction/verification steps.
5. List tested Windows versions, games, executables and hardware; explicitly identify **untested** combinations.
6. Preserve compatibility with saved configuration files and the XP target unless a deliberate, documented breaking change is agreed.

## Bug reports

Provide Windows version/architecture, game family and version, original/modified executable status, controller and connection method, enabled patches and graphics/audio options, exact steps, expected vs actual results, and sanitized diagnostic logs. Check [Troubleshooting](documentation/TROUBLESHOOTING.md) first.

Do not upload copyrighted game binaries/data, credentials, proprietary keys, unredacted personal paths, or unique device identifiers.

## Patch contributions

Follow [patch documentation](documentation/patches/README.md). Supply game/build applicability, expected behavior, timing, uniqueness assumptions, rollback/recovery instructions and tests. A JSON file parsing successfully does not establish a safe runtime patch.

## Building

See [BUILDING.md](documentation/BUILDING.md). Verify that dependency and compiler upgrades do not silently break the Windows XP-targeted build or legacy arcade hardware. A reproducible build is a priority before large functionality changes.