#!/bin/bash
# Purpose: Back up an Obsidian vault to a timestamped compressed archive on macOS.
# Usage:   bash ./backup-obsidian-vault-macos.sh --vault "$HOME/vault" --destination "$HOME/Backups/Obsidian"
# Cadence: Daily via launchd, cron, or a manual terminal run.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  backup-obsidian-vault-macos.sh --destination <directory> [options]

Options:
  -v, --vault <directory>        Obsidian vault path. Defaults to $VAULT_PATH, then $HOME/vault.
  -d, --destination <directory>  Directory where the backup archive will be written. Required.
  -r, --retention-days <days>    Delete matching backups older than this many days. 0 disables retention. Default: 0.
  -h, --help                     Show this help.

Archive naming:
  yyyymmdd-HHMMSS-<vault-name>.zip
EOF
}

vault_path="${VAULT_PATH:-$HOME/vault}"
destination_directory=""
retention_days=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        -v|--vault)
            [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; exit 2; }
            vault_path="$2"
            shift 2
            ;;
        -d|--destination)
            [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; exit 2; }
            destination_directory="$2"
            shift 2
            ;;
        -r|--retention-days)
            [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; exit 2; }
            retention_days="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ -z "$destination_directory" ]; then
    echo "Missing required --destination argument." >&2
    usage >&2
    exit 2
fi

case "$retention_days" in
    ''|*[!0-9]*)
        echo "--retention-days must be a whole number." >&2
        exit 2
        ;;
esac

require_directory() {
    path="$1"
    label="$2"

    if [ ! -d "$path" ]; then
        echo "$label not found: $path" >&2
        exit 1
    fi
}

resolve_directory() {
    path="$1"
    mkdir -p "$path"
    cd "$path" >/dev/null 2>&1
    pwd -P
}

require_command() {
    command_name="$1"

    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Required command not found: $command_name" >&2
        exit 1
    fi
}

require_command ditto
require_command find

require_directory "$vault_path" "Vault path"
resolved_vault_path="$(cd "$vault_path" >/dev/null 2>&1 && pwd -P)"
resolved_destination="$(resolve_directory "$destination_directory")"

if [ ! -d "$resolved_vault_path/.obsidian" ]; then
    echo "$resolved_vault_path does not look like an Obsidian vault. Missing .obsidian directory." >&2
    exit 1
fi

case "$resolved_destination/" in
    "$resolved_vault_path"/*)
        echo "Destination directory must not be inside the vault. That would include backups inside future backups." >&2
        exit 1
        ;;
esac

vault_name="$(basename "$resolved_vault_path")"
timestamp="$(date '+%Y%m%d-%H%M%S')"
archive_name="$timestamp-$vault_name.zip"
archive_path="$resolved_destination/$archive_name"
temporary_archive_path="$resolved_destination/$timestamp-$vault_name.incomplete.zip"

rm -f "$temporary_archive_path"

echo "Vault:       $resolved_vault_path"
echo "Destination: $archive_path"
echo "Tool:        ditto"

cleanup() {
    rm -f "$temporary_archive_path"
}

trap cleanup EXIT

ditto -c -k --sequesterRsrc --keepParent "$resolved_vault_path" "$temporary_archive_path"
mv -f "$temporary_archive_path" "$archive_path"

if [ "$retention_days" -gt 0 ]; then
    find "$resolved_destination" \
        -maxdepth 1 \
        -type f \
        -name "*-$vault_name.zip" \
        -mtime +"$retention_days" \
        -print \
        -exec rm -f {} +
fi

trap - EXIT
echo "Backup complete: $archive_path"
