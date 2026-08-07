# Utility Scripts

General-purpose scripts that may be called by people, scheduled tasks, or multiple vault workflows.

| Script | Platform | What it does |
| --- | --- | --- |
| [backup-obsidian-vault.ps1](backup-obsidian-vault.ps1) | Windows 11 | Backs up an Obsidian vault to a timestamped archive in a specified destination directory. Prefers 7-Zip when available, otherwise uses Windows `tar.exe`. |
| [backup-obsidian-vault-macos.sh](backup-obsidian-vault-macos.sh) | macOS | Backs up an Obsidian vault to a timestamped ZIP archive using native `ditto`. |

## Windows Task Scheduler Example

Program:

```text
powershell.exe
```

Arguments:

```text
-NoProfile -ExecutionPolicy Bypass -File "C:\Users\YourName\vault\scripts\utility\backup-obsidian-vault.ps1" -VaultPath "C:\Users\YourName\vault" -DestinationDirectory "D:\Backups\Obsidian" -RetentionDays 30
```

The archive basename is `yyyyMMdd-HHmmss-<vault-name>`, for example `20260518-213000-MyVault.7z`.

## macOS launchd Example

Command:

```bash
/bin/bash /Users/yourname/vault/scripts/utility/backup-obsidian-vault-macos.sh --vault /Users/yourname/vault --destination /Users/yourname/Backups/Obsidian --retention-days 30
```

The archive basename is `yyyyMMdd-HHMMSS-<vault-name>`, for example `20260518-213000-MyVault.zip`.
