# Security policy and disclosure

2EZConfig_Re operates inside legacy game processes, handles Windows device IO and can apply memory patches. Use it only with software you are authorized to run or modify.

## Reporting vulnerabilities

**Please do not open a public issue containing an unpatched exploit, credential or sensitive memory dump.** If GitHub private vulnerability reporting is enabled for this repository, use **Security → Report a vulnerability**. Otherwise open a high-level issue with no exploit details and ask a maintainer for a private disclosure route. Do not assume a private contact address exists.

Include a minimal reproduction, affected game/build ID, operating system, whether the behavior is exploitable from an untrusted file or device, and a suggested mitigation. Never attach copyrighted game executables, account credentials or unique device serials.

## Security boundaries

- **Game DLL:** the new event export is disabled by default and writes locally only; do not call it from timing-critical code. It is not a secure authorization boundary against other code already running in the same process.
- **Local score companion:** development prototype. Submissions and player IDs are unverified; scores can be forged. By default the server is bound to 127.0.0.1. Remote binding requires a shared token but **plain HTTP does not encrypt it**.
- **Lobbies:** in-memory state and caller-supplied player IDs; not suitable for public matchmaking.
- **Song packs:** the validator checks manifest paths/metadata but does not audit audio codecs, content rights or malware.
- **Profile exports:** may reveal HID identifiers, game configuration or local paths. Review files before publishing.
- **Windows XP:** unsupported by modern security services; keep cabinets away from untrusted networks and use a modern host for networked companion services.
- **Hooks:** only load trusted, version-compatible DLLs and never apply unverified patch patterns or offsets.

## Supported versions

The default branch is actively maintained on a best-effort community basis. No formal security SLA, supported-version promise or code signing is provided. Hardware/XP compatibility is not fully verified. See [ROADMAP.md](documentation/ROADMAP.md) and [BUILDING.md](documentation/BUILDING.md).