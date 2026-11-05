# Cabinet profiles: export, diff and controlled restore

**Implemented:** an offline Python 3.10+ tool for exporting, comparing and restoring existing 2EZConfig settings. **Not implemented:** built-in profile management in the game's GUI, automatic HID remapping, multi-cabinet cloud sync or versioned schema migrations.

## Intended use cases

- Preserve known-good setups before replacing HID/USB controllers.
- Compare original arcade IO and a custom input-encoder configuration.
- Carry per-game options to a test installation without copying game assets.
- Restore a working setup after patch, analog or graphics configuration changes.

Profiles contain format_version, exported_at_utc, game_settings and global_settings JSON objects. Global settings may contain device paths and unique HID metadata; **do not post an unreviewed profile publicly**.

## Export a named profile

In PowerShell, on a modern Windows host:

~~~powershell
python tools/cabinet_profiles.py export --game-dir "C:\Arcade\EZ2" --profile "D:\Backups\cabinet_original_io.json"
~~~

By default, shared settings are located at the APPDATA/2ezconfig/global-settings.json path. To point to another file, supply --global-file explicitly:

~~~powershell
python tools/cabinet_profiles.py export --game-dir "C:\Arcade\EZ2" --global-file "D:\Config\global-settings.json" --profile "D:\Backups\cabinet_usb_encoder.json"
~~~

Export refuses to overwrite an existing snapshot.

## Compare settings without replacing anything

~~~powershell
python tools/cabinet_profiles.py diff --game-dir "C:\Arcade\EZ2" --profile "D:\Backups\cabinet_original_io.json"
~~~

The output lists changed JSON paths and whether they would be added, removed or modified. **Values are not printed** in the default diff to reduce accidental disclosure of device details.

## Restore with a preview

~~~powershell
# Preview only; no changes are written.
python tools/cabinet_profiles.py apply --game-dir "C:\Arcade\EZ2" --profile "D:\Backups\cabinet_original_io.json"

# Explicitly commit changes after reviewing the differences.
python tools/cabinet_profiles.py apply --game-dir "C:\Arcade\EZ2" --profile "D:\Backups\cabinet_original_io.json" --apply
~~~

The tool validates JSON roots and profile format. Writes use same-directory temporary files, and a previous valid settings file is saved as *.bak. Existing invalid files are **not overwritten and treated as good backups**.

**Limits:** Game and global settings are saved separately, not as one transaction. If the second file fails, the two files may reflect different versions; preserve independent backups and verify both files afterward. Stop the game/configurator before restore.

## Next steps

- GUI profile selection with named presets, preview/diff and one-click restore.
- Per-family/mode templates and a compatibility check for missing devices.
- Remap device identities when USB ports or controller paths change.
- Versioned snapshots, migration and privacy-redacted support packages.
- A startup wizard for original IO / custom HID / keyboard-only configurations.

See [ROADMAP.md](ROADMAP.md) and [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
