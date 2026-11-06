#Requires -Version 5.1
<#
.SYNOPSIS
  Read-only, redacted Windows Application Error / EVTX summary for EZ2 games.
.DESCRIPTION
  Inspects Event ID 1000 from existing EVTX exports or the local Application
  log. Uses only built-in Windows PowerShell; does not load any game DLL,
  change drivers/settings, invoke games, or send data over the network.
  Omits full paths, computer names, usernames and report identifiers.
.EXAMPLE
  .\tools\windows_crash_report.ps1 -EvtxPath D:\logs\ez21.evtx,D:\logs\ez22.evtx
.EXAMPLE
  .\tools\windows_crash_report.ps1 -AppName EZ2DJ.exe -MaxEvents 200
#>
[CmdletBinding()]
param(
    [string[]] $EvtxPath = @(),
    [ValidateNotNullOrEmpty()][string] $AppName = 'EZ2AC.exe',
    [ValidateRange(1, 1000)][int] $MaxEvents = 200,
    # Test/interop path for one exported Windows Event XML document.
    [string] $XmlPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-NodeText {
    param([xml] $Document, [string] $LocalName)
    $node = $Document.SelectSingleNode("//*[local-name()='$LocalName']")
    if ($null -eq $node) { return '' }
    return [string] $node.InnerText
}

function Convert-ApplicationError {
    param([string] $XmlText, [string] $ExpectedApp)

    try { [xml] $document = $XmlText } catch { return $null }
    $idText = Get-NodeText -Document $document -LocalName 'EventID'
    if ($idText -ne '1000') { return $null }

    $fields = @{}
    foreach ($node in $document.SelectNodes("//*[local-name()='EventData']/*[local-name()='Data']")) {
        if ($null -eq $node.Attributes) { continue }
        $attribute = $node.Attributes['Name']
        if ($null -eq $attribute) { continue }
        $fields[[string] $attribute.Value] = [string] $node.InnerText
    }
    if (-not $fields.ContainsKey('AppName') -or
        [string] $fields['AppName'] -ine $ExpectedApp) { return $null }

    $created = $document.SelectSingleNode("//*[local-name()='TimeCreated']")
    if ($null -eq $created -or $null -eq $created.Attributes['SystemTime']) { return $null }
    $rawTime = [string] $created.Attributes['SystemTime'].Value
    try {
        $time = [datetime]::Parse(
            $rawTime, [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::AssumeUniversal
        ).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    } catch { return $null }

    $module = [string] $fields['ModuleName']
    $version = [string] $fields['ModuleVersion']
    $exception = [string] $fields['ExceptionCode']
    $offset = [string] $fields['FaultingOffset']
    $processId = [string] $fields['ProcessId']

    # Avoid printing binary/XML payloads or unexpected strings from event data.
    if ($module -notmatch '^[A-Za-z0-9_.-]{1,100}$') { $module = 'unknown' }
    if ($version -notmatch '^[0-9.]{1,32}$') { $version = 'unknown' }
    if ($exception -notmatch '^[0-9A-Fa-f]{1,16}$') { $exception = 'unknown' }
    if ($offset -notmatch '^[0-9A-Fa-f]{1,16}$') { $offset = 'unknown' }
    if ($processId -notmatch '^[0-9A-Fa-fx]{1,20}$') { $processId = '' }

    return [pscustomobject]@{
        time_utc = $time
        application = $ExpectedApp
        module = $module
        module_version = $version
        exception_code = $exception.ToLowerInvariant()
        fault_offset = $offset.ToLowerInvariant()
        process_id = $processId
    }
}

$files = @($EvtxPath)
if ($XmlPath) {
    if ($files.Count -gt 0) { throw 'Specify -XmlPath or -EvtxPath, not both.' }
    $files = @($XmlPath)
}

$observed = @{}
$events = New-Object 'System.Collections.Generic.List[object]'

if ($files.Count -gt 0) {
    foreach ($file in $files) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            throw 'Specified log file does not exist.'
        }
        if ($XmlPath) {
            $xmlEvents = @(Get-Content -LiteralPath $file -Raw -Encoding UTF8)
        } else {
            $xmlEvents = @(Get-WinEvent -Path $file -MaxEvents $MaxEvents -ErrorAction Stop |
                           ForEach-Object { $_.ToXml() })
        }
        foreach ($xml in $xmlEvents) {
            $event = Convert-ApplicationError -XmlText $xml -ExpectedApp $AppName
            if ($null -eq $event) { continue }
            $identity = @($event.time_utc, $event.application, $event.module,
                          $event.module_version, $event.exception_code,
                          $event.fault_offset, $event.process_id) -join '|'
            if (-not $observed.ContainsKey($identity)) {
                $observed[$identity] = $true
                [void] $events.Add($event)
            }
        }
    }
} else {
    # Local Windows Application log only; bounded read, no persistent access.
    $raw = @(Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000} -MaxEvents $MaxEvents -ErrorAction Stop)
    foreach ($record in $raw) {
        $event = Convert-ApplicationError -XmlText ($record.ToXml()) -ExpectedApp $AppName
        if ($null -eq $event) { continue }
        $identity = @($event.time_utc, $event.application, $event.module,
                      $event.module_version, $event.exception_code,
                      $event.fault_offset, $event.process_id) -join '|'
        if (-not $observed.ContainsKey($identity)) {
            $observed[$identity] = $true
            [void] $events.Add($event)
        }
    }
}

$ordered = @($events.ToArray() | Sort-Object time_utc)
$groups = @($ordered | Group-Object module, module_version, exception_code, fault_offset |
    ForEach-Object {
        $first = $_.Group[0]
        [pscustomobject]@{
            module = $first.module
            module_version = $first.module_version
            exception_code = $first.exception_code
            fault_offset = $first.fault_offset
            count = $_.Count
        }
    })

[pscustomobject]@{
    schema_version = 1
    report = '2ez_windows_app_crash_report'
    read_only = $true
    no_user_paths = $true
    application = $AppName
    unique_crashes = $ordered.Count
    groups = $groups
    crashes = $ordered
    caveat = 'A faulting module is not a complete root-cause analysis; compare driver, game and patch configurations.'
} | ConvertTo-Json -Depth 8
