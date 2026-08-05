# Purpose: Register a daily scheduled backup of an Obsidian vault.
#          Optionally installs 7-Zip via winget for smaller, faster archives.
# Usage:   .\install-backup-schedule.ps1 -VaultPath "C:\Users\You\YourVault" -DestinationDirectory "D:\Backups\Obsidian"
# Run:     Once, from PowerShell. Does not need to be run again unless you change the settings.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$VaultPath,

    [Parameter(Mandatory = $true)]
    [string]$DestinationDirectory,

    [Parameter(Mandatory = $false)]
    [string]$TaskTime = '08:00',

    [Parameter(Mandatory = $false)]
    [ValidateRange(0, 3650)]
    [int]$RetentionDays = 30,

    [Parameter(Mandatory = $false)]
    [switch]$Install7Zip
)

$ErrorActionPreference = 'Stop'

# ── Optional: install 7-Zip ───────────────────────────────────────────────────

if ($Install7Zip) {
    $sevenZipInstalled = (
        (Test-Path 'C:\Program Files\7-Zip\7z.exe') -or
        (Test-Path 'C:\Program Files (x86)\7-Zip\7z.exe') -or
        ($null -ne (Get-Command '7z.exe' -ErrorAction SilentlyContinue))
    )

    if ($sevenZipInstalled) {
        Write-Host '7-Zip is already installed. Skipping.'
    } else {
        Write-Host 'Installing 7-Zip via winget...'
        winget install --id 7zip.7zip --silent --accept-package-agreements --accept-source-agreements
        Write-Host '7-Zip installed.'
    }
}

# ── Resolve paths ─────────────────────────────────────────────────────────────

if (-not (Test-Path -LiteralPath $VaultPath -PathType Container)) {
    throw "Vault path not found: $VaultPath"
}

$resolvedVault = (Resolve-Path -LiteralPath $VaultPath).Path

if (-not (Test-Path -LiteralPath $DestinationDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null
    Write-Host "Created destination directory: $DestinationDirectory"
}

$resolvedDestination = (Resolve-Path -LiteralPath $DestinationDirectory).Path

# ── Locate the backup script ──────────────────────────────────────────────────

$backupScript = Join-Path $PSScriptRoot 'backup-obsidian-vault.ps1'

if (-not (Test-Path -LiteralPath $backupScript -PathType Leaf)) {
    throw "Backup script not found: $backupScript`nExpected alongside this installer in the same folder."
}

# ── Build the scheduled task ──────────────────────────────────────────────────

$taskName = 'Obsidian Vault Backup'

$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$backupScript`" " +
             "-VaultPath `"$resolvedVault`" " +
             "-DestinationDirectory `"$resolvedDestination`" " +
             "-RetentionDays $RetentionDays"

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument $arguments

$trigger = New-ScheduledTaskTrigger -Daily -At $TaskTime

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Remove any existing task with the same name before registering
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed existing scheduled task: $taskName"
}

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Limited `
    -Force | Out-Null

Write-Host ''
Write-Host "Scheduled task registered: $taskName"
Write-Host "  Vault:       $resolvedVault"
Write-Host "  Destination: $resolvedDestination"
Write-Host "  Time:        $TaskTime daily"
Write-Host "  Retention:   $RetentionDays days"
Write-Host ''
Write-Host 'Running a test backup now to confirm everything works...'

Start-ScheduledTask -TaskName $taskName
Start-Sleep -Seconds 5

$lastResult = (Get-ScheduledTaskInfo -TaskName $taskName).LastTaskResult
if ($lastResult -eq 0) {
    Write-Host 'Test backup completed successfully.'
} else {
    Write-Warning "Test backup finished with result code $lastResult. Check $resolvedDestination for output."
}

Write-Host ''
Write-Host 'Setup complete. Your vault will be backed up automatically each day.'
