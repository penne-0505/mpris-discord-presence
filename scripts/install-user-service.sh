#!/usr/bin/env bash
set -euo pipefail

project_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
unit_dir="$config_home/systemd/user"
config_dir="$config_home/mpris-discord-presence"
install_dir="$data_home/mpris-discord-presence"
releases_dir="$install_dir/releases"
venv_path="$install_dir/venv"
previous_venv_path="$install_dir/previous-venv"
unit_file="$unit_dir/mpris-discord-presence.service"
previous_unit_file="$unit_dir/mpris-discord-presence.service.previous"
config_file="$config_dir/config.toml"
environment_file="$config_dir/environment"
previous_environment_file="$config_dir/environment.previous"
python_bin="${PYTHON_BIN:-/usr/bin/python}"
systemctl_bin="${SYSTEMCTL_BIN:-systemctl}"
mode="install"

usage() {
  printf '%s\n' \
    'Usage: scripts/install-user-service.sh [--enable-now|--dry-run|--disable-now|--rollback]' \
    '' \
    '  --enable-now   install, enable, and start the user service' \
    '  --dry-run      print paths without changing files or systemd state' \
    '  --disable-now  stop and disable the installed service without deleting files' \
    '  --rollback     restore the previous installed runtime or pre-migration unit'
}

case "${1:-}" in
  "") ;;
  --enable-now) mode="enable-now" ;;
  --dry-run) mode="dry-run" ;;
  --disable-now) mode="disable-now" ;;
  --rollback) mode="rollback" ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

if [[ "$mode" == "dry-run" ]]; then
  printf 'source: %s\ninstall root: %s\nvenv: %s\nunit: %s\nconfig: %s\nenvironment: %s\npython: %s\n' \
    "$project_root" "$install_dir" "$venv_path" "$unit_file" "$config_file" \
    "$environment_file" "$python_bin"
  exit 0
fi

if [[ "$mode" == "disable-now" ]]; then
  "$systemctl_bin" --user disable --now mpris-discord-presence.service
  printf 'Disabled mpris-discord-presence.service; config and unit were retained.\n'
  exit 0
fi

if [[ "$mode" == "rollback" ]]; then
  if [[ -L "$previous_venv_path" ]]; then
    previous_release="$(readlink -f -- "$previous_venv_path")"
    [[ -x "$previous_release/bin/mpris-discord-presence" ]] || {
      printf 'Previous runtime is not usable: %s\n' "$previous_release" >&2
      exit 1
    }
    ln -sfnT "$previous_release" "$venv_path"
    "$systemctl_bin" --user daemon-reload
    "$systemctl_bin" --user restart mpris-discord-presence.service
    printf 'Rolled back runtime to: %s\n' "$previous_release"
    exit 0
  fi
  if [[ -f "$previous_unit_file" ]]; then
    install -m 0644 "$previous_unit_file" "$unit_file"
    if [[ -f "$previous_environment_file" ]]; then
      install -m 0600 "$previous_environment_file" "$environment_file"
    fi
    "$systemctl_bin" --user daemon-reload
    "$systemctl_bin" --user restart mpris-discord-presence.service
    printf 'Restored the pre-migration user unit.\n'
    exit 0
  fi
  printf 'No previous runtime or pre-migration unit is available.\n' >&2
  exit 1
fi

if [[ ! -x "$python_bin" ]]; then
  printf 'Python executable not found: %s\n' "$python_bin" >&2
  exit 1
fi

mkdir -p "$unit_dir" "$config_dir" "$releases_dir"
if [[ ! -e "$config_file" ]]; then
  install -m 0600 "$project_root/config.example.toml" "$config_file"
  printf 'Created config: %s\n' "$config_file"
fi

# intent: INV-003 (Core/user-local-install) — build a complete release before
# changing the current runtime symlink or the installed service unit.
release_id="$(date -u +%Y%m%dT%H%M%SZ)-$$"
release_dir="$releases_dir/$release_id"
"$python_bin" -m venv --system-site-packages "$release_dir"
"$release_dir/bin/python" -m pip install \
  --disable-pip-version-check --no-deps --no-build-isolation "$project_root"
"$release_dir/bin/mpris-discord-presence" --help >/dev/null

if [[ "$mode" == "enable-now" ]]; then
  printf 'Checking config and staged runtime before enabling the service...\n'
  "$release_dir/bin/mpris-discord-presence" --config "$config_file" doctor
fi

staged_unit="$install_dir/mpris-discord-presence.service.staged"
sed \
  -e "s|@EXECUTABLE@|$venv_path/bin/mpris-discord-presence|g" \
  -e "s|@CONFIG_FILE@|$config_file|g" \
  -e "s|@ENVIRONMENT_FILE@|$environment_file|g" \
  "$project_root/packaging/systemd/mpris-discord-presence.service.in" > "$staged_unit"
chmod 0644 "$staged_unit"

if [[ -L "$venv_path" ]]; then
  current_release="$(readlink -f -- "$venv_path")"
  if [[ -x "$current_release/bin/mpris-discord-presence" ]]; then
    ln -sfnT "$current_release" "$previous_venv_path"
  fi
elif [[ -e "$venv_path" ]]; then
  printf 'Install path exists but is not a managed symlink: %s\n' "$venv_path" >&2
  exit 1
fi

if [[ -f "$unit_file" && ! -f "$previous_unit_file" ]]; then
  install -m 0644 "$unit_file" "$previous_unit_file"
fi
if [[ -f "$environment_file" && ! -f "$previous_environment_file" ]]; then
  install -m 0600 "$environment_file" "$previous_environment_file"
fi

ln -sfnT "$release_dir" "$venv_path"
install -m 0644 "$staged_unit" "$unit_file"

"$systemctl_bin" --user daemon-reload

printf 'Installed runtime: %s\nInstalled user unit: %s\n' "$release_dir" "$unit_file"
if [[ "$mode" == "enable-now" ]]; then
  "$systemctl_bin" --user enable --now mpris-discord-presence.service
  printf 'Enabled and started mpris-discord-presence.service\n'
else
  printf 'Edit %s, then run: systemctl --user enable --now mpris-discord-presence.service\n' "$config_file"
fi
