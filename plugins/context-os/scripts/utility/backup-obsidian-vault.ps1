# Purpose: Back up an Obsidian vault to a timestamped compressed archive.
# Usage:   .\backup-obsidian-vault.ps1 -VaultPath "$HOME\vault" -DestinationDirectory "D:\Backups\Obsidian"
# Cadence: Daily via Windows Task Scheduler.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$VaultPath = $(if ($env:VAULT_PATH) { $env:VAULT_PATH } else { Join-Path $HOME 'vault' }),

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$DestinationDirectory,

    [Parameter(Mandatory = $false)]
    [ValidateSet('Auto', '7Zip', 'Tar')]
    [string]$ArchiveTool = 'Auto',

    [Parameter(Mandatory = $false)]
    [string]$SevenZipPath,

    [Parameter(Mandatory = $false)]
    [ValidateRange(0, 3650)]
    [int]$RetentionDays = 0
)

$ErrorActionPreference = 'Stop'

function Resolve-ExistingDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "$Label not found: $Path"
    }

    return (Resolve-Path -LiteralPath $Path).Path
}

function Get-SevenZipCommand {
    param(
        [Parameter(Mandatory = $false)]
        [string]$ExplicitPath
    )

    if ($ExplicitPath) {
        if (Test-Path -LiteralPath $ExplicitPath -PathType Leaf) {
            return (Resolve-Path -LiteralPath $ExplicitPath).Path
        }

        throw "7-Zip not found at explicit path: $ExplicitPath"
    }

    $candidatePaths = @(
        @(
            (Join-Path $env:ProgramFiles '7-Zip\7z.exe'),
            (Join-Path ${env:ProgramFiles(x86)} '7-Zip\7z.exe')
        ) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
    )

    if ($candidatePaths.Count -gt 0) {
        return $candidatePaths[0]
    }

    $command = Get-Command '7z.exe' -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    return $null
}

function Test-PathInsideDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ChildPath,

        [Parameter(Mandatory = $true)]
        [string]$ParentPath
    )

    $normalisedChild = [System.IO.Path]::GetFullPath($ChildPath).TrimEnd('\')
    $normalisedParent = [System.IO.Path]::GetFullPath($ParentPath).TrimEnd('\')

    return $normalisedChild.StartsWith(
        $normalisedParent + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    ) -or ($normalisedChild -ieq $normalisedParent)
}

function Remove-ExpiredArchives {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DestinationPath,

        [Parameter(Mandatory = $true)]
        [string]$VaultName,

        [Parameter(Mandatory = $true)]
        [int]$Days
    )

    if ($Days -le 0) {
        return
    }

    $cutoff = (Get-Date).AddDays(-$Days)
    $pattern = "*-$VaultName.*"

    Get-ChildItem -LiteralPath $DestinationPath -File -Filter $pattern |
        Where-Object {
            $_.LastWriteTime -lt $cutoff -and
            $_.Name -match "^\d{8}-\d{6}-$([Regex]::Escape($VaultName))\.(7z|zip)$"
        } |
        ForEach-Object {
            Write-Host "Removing expired backup: $($_.FullName)"
            Remove-Item -LiteralPath $_.FullName -Force
        }
}

$resolvedVaultPath = Resolve-ExistingDirectory -Path $VaultPath -Label 'Vault path'
$resolvedDestination = if (Test-Path -LiteralPath $DestinationDirectory -PathType Container) {
    (Resolve-Path -LiteralPath $DestinationDirectory).Path
} else {
    New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null
    (Resolve-Path -LiteralPath $DestinationDirectory).Path
}

if (-not (Test-Path -LiteralPath (Join-Path $resolvedVaultPath '.obsidian') -PathType Container)) {
    throw "$resolvedVaultPath does not look like an Obsidian vault. Missing .obsidian directory."
}

if (Test-PathInsideDirectory -ChildPath $resolvedDestination -ParentPath $resolvedVaultPath) {
    throw 'DestinationDirectory must not be inside the vault. That would include backups inside future backups.'
}

$vaultItem = Get-Item -LiteralPath $resolvedVaultPath
$vaultName = $vaultItem.Name
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$parentPath = Split-Path -Parent $resolvedVaultPath

$sevenZipCommand = Get-SevenZipCommand -ExplicitPath $SevenZipPath
$selectedTool = $ArchiveTool

if ($selectedTool -eq 'Auto') {
    if ($sevenZipCommand) {
        $selectedTool = '7Zip'
    } else {
        $selectedTool = 'Tar'
    }
}

if ($selectedTool -eq '7Zip' -and -not $sevenZipCommand) {
    throw 'ArchiveTool was set to 7Zip, but 7z.exe was not found. Provide -SevenZipPath or use -ArchiveTool Tar.'
}

if ($selectedTool -eq 'Tar' -and -not (Get-Command 'tar.exe' -ErrorAction SilentlyContinue)) {
    throw 'tar.exe was not found. Install 7-Zip, provide -SevenZipPath, or confirm Windows system32 is on PATH.'
}

$extension = if ($selectedTool -eq '7Zip') { '7z' } else { 'zip' }
$archiveName = "$timestamp-$vaultName.$extension"
$archivePath = Join-Path $resolvedDestination $archiveName
$temporaryArchivePath = Join-Path $resolvedDestination "$timestamp-$vaultName.incomplete.$extension"

if (Test-Path -LiteralPath $temporaryArchivePath) {
    Remove-Item -LiteralPath $temporaryArchivePath -Force
}

Write-Host "Vault:       $resolvedVaultPath"
Write-Host "Destination: $archivePath"
Write-Host "Tool:        $selectedTool"

try {
    if ($selectedTool -eq '7Zip') {
        Push-Location -LiteralPath $parentPath
        try {
            & $sevenZipCommand a -t7z -mx=7 -ssw -y $temporaryArchivePath $vaultName
            if ($LASTEXITCODE -ne 0) {
                throw "7-Zip failed with exit code $LASTEXITCODE."
            }
        } finally {
            Pop-Location
        }
    } else {
        & tar.exe -a -cf $temporaryArchivePath -C $parentPath $vaultName
        if ($LASTEXITCODE -ne 0) {
            throw "tar.exe failed with exit code $LASTEXITCODE."
        }
    }

    Move-Item -LiteralPath $temporaryArchivePath -Destination $archivePath -Force
    Remove-ExpiredArchives -DestinationPath $resolvedDestination -VaultName $vaultName -Days $RetentionDays
    Write-Host "Backup complete: $archivePath"
} catch {
    if (Test-Path -LiteralPath $temporaryArchivePath) {
        Remove-Item -LiteralPath $temporaryArchivePath -Force
    }

    throw
}
