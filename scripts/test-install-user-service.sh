#!/usr/bin/env bash
set -euo pipefail

project_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
test_root="$(mktemp -d)"
home="$test_root/home"
config_home="$home/.config"
data_home="$home/.local/share"
fake_bin="$test_root/bin"
systemctl_log="$test_root/systemctl.log"
mkdir -p "$home" "$fake_bin"

cat > "$fake_bin/systemctl" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$SYSTEMCTL_LOG"
EOF
chmod +x "$fake_bin/systemctl"

run_installer() {
  HOME="$home" \
  XDG_CONFIG_HOME="$config_home" \
  XDG_DATA_HOME="$data_home" \
  SYSTEMCTL_BIN="$fake_bin/systemctl" \
  SYSTEMCTL_LOG="$systemctl_log" \
  PYTHON_BIN="$(command -v python)" \
    "$project_root/scripts/install-user-service.sh" "$@"
}

assert_contains() {
  local file="$1"
  local expected="$2"
  grep -F -- "$expected" "$file" >/dev/null || {
    printf 'Expected %s to contain: %s\n' "$file" "$expected" >&2
    exit 1
  }
}

assert_not_contains() {
  local file="$1"
  local unexpected="$2"
  if grep -F -- "$unexpected" "$file" >/dev/null; then
    printf 'Expected %s not to contain: %s\n' "$file" "$unexpected" >&2
    exit 1
  fi
}

# Seed the checkout-based unit shape so the migration recovery path is covered.
mkdir -p "$config_home/systemd/user" "$config_home/mpris-discord-presence"
printf 'sentinel-pre-migration-unit\n' > \
  "$config_home/systemd/user/mpris-discord-presence.service"
printf 'sentinel-pre-migration-environment\n' > \
  "$config_home/mpris-discord-presence/environment"
chmod 0600 "$config_home/mpris-discord-presence/environment"

# AC-001 / INV-001 / INV-004: install into a system-site-packages venv and
# render a checkout-independent unit.
run_installer
venv="$data_home/mpris-discord-presence/venv"
unit="$config_home/systemd/user/mpris-discord-presence.service"
config="$config_home/mpris-discord-presence/config.toml"
[[ -L "$venv" ]]
[[ -x "$venv/bin/mpris-discord-presence" ]]
"$venv/bin/mpris-discord-presence" --help >/dev/null
assert_contains "$venv/pyvenv.cfg" 'include-system-site-packages = true'
assert_contains "$unit" "$venv/bin/mpris-discord-presence"
assert_not_contains "$unit" "$project_root"
assert_not_contains "$unit" 'PYTHONPATH'
[[ "$(stat -c '%a' "$config")" == "600" ]]
assert_contains \
  "$config_home/systemd/user/mpris-discord-presence.service.previous" \
  'sentinel-pre-migration-unit'

# Recovery from the first migration restores the original unit/environment.
run_installer --rollback
assert_contains "$unit" 'sentinel-pre-migration-unit'
assert_contains \
  "$config_home/mpris-discord-presence/environment" \
  'sentinel-pre-migration-environment'

# AC-003 / INV-002: reinstall preserves user configuration.
printf 'sentinel-user-config\n' > "$config"
chmod 0600 "$config"
first_release="$(readlink -f -- "$venv")"
run_installer
[[ "$(<"$config")" == 'sentinel-user-config' ]]
second_release="$(readlink -f -- "$venv")"
[[ "$first_release" != "$second_release" ]]
[[ "$(readlink -f -- "$data_home/mpris-discord-presence/previous-venv")" == "$first_release" ]]

# INV-003: a staging failure does not replace the active runtime or unit.
cp "$unit" "$test_root/unit-before-failure"
failing_python="$fake_bin/failing-python"
cat > "$failing_python" <<'EOF'
#!/usr/bin/env bash
exit 23
EOF
chmod +x "$failing_python"
if HOME="$home" XDG_CONFIG_HOME="$config_home" XDG_DATA_HOME="$data_home" \
  SYSTEMCTL_BIN="$fake_bin/systemctl" SYSTEMCTL_LOG="$systemctl_log" \
  PYTHON_BIN="$failing_python" "$project_root/scripts/install-user-service.sh"; then
  printf 'Expected staging failure\n' >&2
  exit 1
fi
[[ "$(readlink -f -- "$venv")" == "$second_release" ]]
cmp "$unit" "$test_root/unit-before-failure"

# Rollback switches back to the last complete release.
run_installer --rollback
[[ "$(readlink -f -- "$venv")" == "$first_release" ]]
assert_contains "$systemctl_log" '--user restart mpris-discord-presence.service'

printf 'PASS user-local installer integration\n'
printf 'Test artifacts retained at: %s\n' "$test_root"
