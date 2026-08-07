#!/bin/bash
# Purpose: Register a daily scheduled backup of an Obsidian vault via launchd.
# Usage:   bash install-backup-schedule.sh --vault "$HOME/YourVault" --destination "$HOME/Backups/Obsidian"
# Run:     Once, from Terminal. Does not need to be run again unless you change the settings.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  install-backup-schedule.sh --vault <directory> --destination <directory> [options]

Options:
  -v, --vault <directory>        Obsidian vault path. Required.
  -d, --destination <directory>  Backup destination directory. Required.
  -t, --time <HH:MM>             Daily run time in 24-hour format. Default: 08:00.
  -r, --retention-days <days>    Delete backups older than this many days. Default: 30.
  -h, --help                     Show this help.
EOF
}

vault_path=""
destination_directory=""
task_time="08:00"
retention_days=30

while [ "$#" -gt 0 ]; do
    case "$1" in
        -v|--vault)
            vault_path="$2"; shift 2 ;;
        -d|--destination)
            destination_directory="$2"; shift 2 ;;
        -t|--time)
            task_time="$2"; shift 2 ;;
        -r|--retention-days)
            retention_days="$2"; shift 2 ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done

if [ -z "$vault_path" ] || [ -z "$destination_directory" ]; then
    echo "Missing required arguments: --vault and --destination are both required." >&2
    usage >&2
    exit 2
fi

# ── Resolve paths ──────────────────────────────────────────────────────────────

if [ ! -d "$vault_path" ]; then
    echo "Vault path not found: $vault_path" >&2
    exit 1
fi

resolved_vault="$(cd "$vault_path" && pwd -P)"
mkdir -p "$destination_directory"
resolved_destination="$(cd "$destination_directory" && pwd -P)"

script_dir="$(cd "$(dirname "$0")" && pwd -P)"
backup_script="$script_dir/backup-obsidian-vault-macos.sh"

if [ ! -f "$backup_script" ]; then
    echo "Backup script not found: $backup_script" >&2
    echo "Expected alongside this installer in the same folder." >&2
    exit 1
fi

# ── Parse time ────────────────────────────────────────────────────────────────

task_hour="${task_time%%:*}"
task_minute="${task_time##*:}"

# Strip leading zeros to avoid octal interpretation
task_hour="${task_hour#0}"
task_minute="${task_minute#0}"
task_hour="${task_hour:-0}"
task_minute="${task_minute:-0}"

# ── Write plist ───────────────────────────────────────────────────────────────

plist_label="au.com.zentelligence.obsidian-backup"
plist_path="$HOME/Library/LaunchAgents/$plist_label.plist"

cat > "$plist_path" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$plist_label</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$backup_script</string>
        <string>--vault</string>
        <string>$resolved_vault</string>
        <string>--destination</string>
        <string>$resolved_destination</string>
        <string>--retention-days</string>
        <string>$retention_days</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>$task_hour</integer>
        <key>Minute</key>
        <integer>$task_minute</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/obsidian-backup.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/obsidian-backup.err</string>
</dict>
</plist>
EOF

echo "Wrote: $plist_path"

# ── Load (or reload) the task ─────────────────────────────────────────────────

# Unload silently if already registered
launchctl unload "$plist_path" 2>/dev/null || true
launchctl load "$plist_path"

echo ""
echo "Scheduled task registered: $plist_label"
echo "  Vault:       $resolved_vault"
echo "  Destination: $resolved_destination"
echo "  Time:        $task_time daily"
echo "  Retention:   $retention_days days"
echo ""
echo "Running a test backup now to confirm everything works..."

launchctl start "$plist_label"
sleep 5

if [ -s /tmp/obsidian-backup.err ]; then
    echo "Warning: test backup produced errors. Check /tmp/obsidian-backup.err:"
    cat /tmp/obsidian-backup.err
else
    echo "Test backup completed. Check $resolved_destination for the archive."
fi

echo ""
echo "Setup complete. Your vault will be backed up automatically each day."
