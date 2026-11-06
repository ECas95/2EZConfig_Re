# Final:EX compatibility and verification

## Distinguish research build from retail build

The current 2EZConfig game ID is **ez2ac_fn_ex**. The submitted RE package names its reccmp target EZ2AC_UNPACKED and documents an unpacked-image checksum. **That checksum is not interchangeable with the SHA-256 of a retail on-disk EZ2AC.exe.** The package does not supply a retail binary or independent cabinet validation.

An executable filename or ZIP title alone does not establish an exact compatible version. The original cabinet must continue working if an optional adapter is missing or incompatible.

## New SHA-256 preflight tool

Use the *read-only* checker on a modern computer:

~~~powershell
python tools/adapter_compatibility.py --exe "D:\OwnGame\EZ2AC.exe" --manifest examples/fnex/adapter-registry.example.json --json
~~~

The example registry contains an intentionally fake, all-zero checksum. It must not match a real executable. This tool:
- Validates the adapter manifest schema and unique IDs.
- Hashes the user-supplied file in chunks without modifying or launching it.
- Supports only fingerprint_type = on_disk_file.
- Checks declared capabilities and reports exact SHA-256 matches.
- Never installs hooks or interprets an unpacked-image checksum as a retail fingerprint.

A matching registry entry **is not proof that its hook code is safe**. It only establishes that an on-disk file matches a declared hash.

## Requirements before any real Final:EX hook

1. Record exact on-disk SHA-256, game revision, OS and CPU architecture.
2. Confirm the loaded memory representation and expected bytes for the hook target.
3. Reject targets with incorrect instruction bytes, unexpected signatures or multiple scan matches.
4. Validate calling convention, thread safety, memory bounds and failure behavior.
5. Compare the game with optional hooks disabled, enabled and intentionally version-mismatched.
6. Test shutdown, errors, missing companion, dropped network and repeated song transitions.
7. Verify the behavior on authorized hardware and a documented game build.

**Fail closed for the optional hook:** do not install it when verification is missing. **Fail open for the game:** leave the underlying game running normally.

## Evidence levels

| Level | What is demonstrated | Current status |
| --- | --- | --- |
| L0 | Source review of private research | Completed, claims not independently reproduced |
| L1 | Synthetic GDS, ranking and adapter-manifest tests | Implemented in CI |
| L2 | Read-only inspection of user-owned game files | Tooling available; real files not supplied |
| L3 | Simulated per-build hook and event integration | Not implemented |
| L4 | Exact retail game build with guarded hook | Not tested |
| L5 | Repeated XP and physical cabinet tests | Not tested |

Do not claim L4/L5 compatibility because the Python tests pass.

## Research regression matrix

| Domain | Successful case | Important failure case |
| --- | --- | --- |
| GDS | Correct file-order lane/Key/SongTrack mapping | Declared count mismatch, missing fields, invalid key range |
| Rankings | 5- or 99-entry read-only layout | Invalid length, unexpected score, player-name privacy |
| Executables | Exact on-disk hash matches declared adapter | Unknown hash, unpacked-only hash, invalid capability |
| Song event | One real confirmed selection per session | Preview cursor changes, unsupported chart, wrong revision |
| Score event | One final result per completed play | Intermediate counters, duplicate event, two-player association |
| Custom assets | Licensed test pack works on verified game build | Missing file, chart error, fallback/rollback |
| Multiplayer | Independent scores produce consistent match results | Network outage, conflicting version or chart checksum |
| XP cabinet | Tested and documented original/USB IO behavior | Device disconnect, unsupported display, offline service |

Only the top three rows have automated synthetic coverage.

## Distribution policy

The provided RE archive describes its own reconstructed game code as **private** and cautions about derivative-work and rights-holder risks despite its GPL declaration. **No reconstructed source, binary dump, disassembly bytes, protected materials or game assets from the archive are copied into this public fork.** Only independently written tools, original fixtures and high-level findings are included.

Keep game files on a user-owned installation and prefer a modern companion computer for any networking. Never publish private credentials, unique controller IDs or unreviewed rank names.

See [FORMATS.md](FORMATS.md), [HOOK_DESIGN.md](HOOK_DESIGN.md), [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) and [Security](../../SECURITY.md).
