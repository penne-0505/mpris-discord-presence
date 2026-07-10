#!/usr/bin/env bash
set -euo pipefail

project_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
unit_dir="$config_home/systemd/user"
config_dir="$config_home/mpris-discord-presence"
unit_file="$unit_dir/mpris-discord-presence.service"
config_file="$config_dir/config.toml"
environment_file="$config_dir/environment"
python_bin="${PYTHON_BIN:-/usr/bin/python}"
mode="install"

usage() {
  printf '%s\n' \
    'Usage: scripts/install-user-service.sh [--enable-now|--dry-run|--disable-now]' \
    '' \
    '  --enable-now   install, enable, and start the user service' \
    '  --dry-run      print paths without changing files or systemd state' \
    '  --disable-now  stop and disable the installed service without deleting files'
}

case "${1:-}" in
  "") ;;
  --enable-now) mode="enable-now" ;;
  --dry-run) mode="dry-run" ;;
  --disable-now) mode="disable-now" ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

if [[ "$mode" == "dry-run" ]]; then
  printf 'project root: %s\nunit: %s\nconfig: %s\nenvironment: %s\npython: %s\n' \
    "$project_root" "$unit_file" "$config_file" "$environment_file" "$python_bin"
  exit 0
fi

if [[ "$mode" == "disable-now" ]]; then
  systemctl --user disable --now mpris-discord-presence.service
  printf 'Disabled mpris-discord-presence.service; config and unit were retained.\n'
  exit 0
fi

if [[ ! -x "$python_bin" ]]; then
  printf 'Python executable not found: %s\n' "$python_bin" >&2
  exit 1
fi

mkdir -p "$unit_dir" "$config_dir"
if [[ ! -e "$config_file" ]]; then
  install -m 0600 "$project_root/config.example.toml" "$config_file"
  printf 'Created config: %s\n' "$config_file"
fi

sed \
  -e "s|@PROJECT_ROOT@|$project_root|g" \
  -e "s|@PYTHON@|$python_bin|g" \
  -e "s|@CONFIG_FILE@|$config_file|g" \
  -e "s|@ENVIRONMENT_FILE@|$environment_file|g" \
  "$project_root/packaging/systemd/mpris-discord-presence.service.in" > "$unit_file"
chmod 0644 "$unit_file"

if [[ "$mode" == "enable-now" ]]; then
  printf 'Checking config and runtime before enabling the service...\n'
  PYTHONPATH="$project_root/src" "$python_bin" -m mpris_discord_presence \
    --config "$config_file" doctor
fi

systemctl --user daemon-reload

printf 'Installed user unit: %s\n' "$unit_file"
if [[ "$mode" == "enable-now" ]]; then
  systemctl --user enable --now mpris-discord-presence.service
  printf 'Enabled and started mpris-discord-presence.service\n'
else
  printf 'Edit %s, then run: systemctl --user enable --now mpris-discord-presence.service\n' "$config_file"
fi
