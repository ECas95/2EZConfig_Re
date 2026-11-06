#Requires -Version 5.1
<#
.SYNOPSIS
  Read-only GPU inventory for EZ2AC/EZ2DJ compatibility investigations.
.DESCRIPTION
  Reports vendor-neutral Windows video adapter names/driver versions without
  unique hardware IDs, user paths, registry paths or device serials.
  No GPU switching, driver installation, game execution or networking.
.EXAMPLE
  .\tools\gpu_compatibility_report.ps1
.EXAMPLE
  .\tools\gpu_compatibility_report.ps1 -FixturePath .\tools\tests\fixtures\synthetic_gpu_adapters.json
#>
[CmdletBinding()]
param([string] $FixturePath = '')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Sanitize-Label {
    param([object] $Value)
    if ($null -eq $Value) { return 'unknown' }
    $label = ([string] $Value) -replace '[\x00-\x1F\x7F]', ' '
    $label = $label.Trim()
    if (-not $label) { return 'unknown' }
    if ($label.Length -gt 120) { $label = $label.Substring(0, 120) }
    return $label
}

function Convert-GpuInventory {
    param([object[]] $RawAdapters)
    $items = New-Object 'System.Collections.Generic.List[object]'
    foreach ($adapter in $RawAdapters) {
        if ($null -eq $adapter) { continue }
        if ($items.Count -ge 32) { break } # Bound untrusted WMI/fixture data.
        $name = Sanitize-Label $adapter.Name
        $version = Sanitize-Label $adapter.DriverVersion
        if ($version -notmatch '^[0-9.]{1,40}$') { $version = 'unknown' }
        $status = Sanitize-Label $adapter.Status
        # Do not include AdapterRAM, PNPDeviceID, DeviceID, VideoProcessor,
        # InstallDate, InfFilename, Registry paths or machine/user details.
        [void] $items.Add([pscustomobject]@{
            name = $name
            driver_version = $version
            status = $status
        })
    }
    $adapters = @($items.ToArray() | Sort-Object name, driver_version)
    $notes = @(
        'All GPU vendors are handled as reported by Windows; no GPU-specific patches or preference changes.',
        'A listed adapter does not prove it drives the monitor or renders a legacy DirectDraw/Direct3D7 game.',
        'Windows per-app graphics preference may be ignored by old DirectDraw/Direct3D7 applications.',
        'This inventory does not verify actual GPU selection, DirectX7 features or stable game presentation.'
    )
    if ($adapters.Count -gt 1) {
        $notes += 'Multiple adapters reported; compare GPU preference and monitor routing, one change at a time.'
    }
    if ($adapters.Count -eq 0) {
        $notes += 'No adapters reported; check local Windows CIM/WMI availability.'
    }
    return [pscustomobject]@{
        schema_version = 1
        report = '2ez_gpu_compatibility_inventory'
        read_only = $true
        modifies_gpu_preference = $false
        validates_game_compatibility = $false
        adapter_count = $adapters.Count
        multiple_adapters_detected = ($adapters.Count -gt 1)
        adapters = @($adapters)
        notes = @($notes)
    }
}

if ($FixturePath) {
    if (-not (Test-Path -LiteralPath $FixturePath -PathType Leaf)) {
        throw 'Fixture does not exist.'
    }
    $file = Get-Item -LiteralPath $FixturePath
    if ($file.Length -gt 1MB) { throw 'Fixture exceeds 1 MiB test limit.' }
    $raw = @(Get-Content -LiteralPath $FixturePath -Encoding UTF8 -Raw | ConvertFrom-Json)
} else {
    # A modern Windows host provides Win32_VideoController through CIM.
    # This is intentionally separate from the XP-compatible game launcher.
    $raw = @(Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop |
             Select-Object Name, DriverVersion, Status)
}

Convert-GpuInventory -RawAdapters $raw | ConvertTo-Json -Depth 6
