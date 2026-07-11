# mpris-discord-presence

A resident tool for Linux desktops that selects one currently active MPRIS player and shares it as Discord Rich Presence. It handles Apple Music on Waydroid, browser videos, and native players through the same MPRIS interface.

> [!WARNING]
> By default, it publishes the title, artist, album, and public HTTPS URL (including queries) of all MPRIS players that do not match the denylist to your Discord profile. If you play private browser media, please configure `deny_players` before installation.

## Current Features

- Monitors the appearance, disappearance, playback state, metadata, and seeking of all MPRIS players
- Automatically selects the player that most recently transitioned to `Playing` as the active one
- Falls back to another `Playing` player or clears after 1.5 seconds when the active player is paused, stopped, or terminated
- Configurable `Listening` / `Watching` status per player glob
- Displays title, artist, album, position/duration, and public HTTPS artwork/link
- Displays `{artist} is playing` in the compact status of friend/member lists
- Reconnects after Discord is not running, restarts, or IPC disconnects, and re-sends only the latest state
- Player denylist, total sharing disable, and clear-on-exit functionality
- Diagnostic CLI and systemd user service

This project is in alpha. It supports Arch Linux / EndeavourOS desktop sessions and the official Discord Linux client.
It uses the official client's local IPC directly and does not use the Discord Social SDK or user tokens. Other distributions, Flatpak / Snap, and unofficial clients like Vesktop are not supported.

## Requirements

- Arch Linux or EndeavourOS desktop session and session D-Bus
- Python 3.11 or later
- PyGObject and Playerctl 2.0 typelib
- MPRIS-compatible player
- Discord desktop
- Application ID created via the Discord Developer Portal

OS packages:

```bash
sudo pacman -S git playerctl python-gobject python-pip
```

## Quick Setup

```bash
git clone https://github.com/penne-0505/mpris-discord-presence.git
cd mpris-discord-presence
./scripts/install-user-service.sh
${EDITOR:-nano} ~/.config/mpris-discord-presence/config.toml
~/.local/share/mpris-discord-presence/venv/bin/mpris-discord-presence \
  --config ~/.config/mpris-discord-presence/config.toml doctor
~/.local/share/mpris-discord-presence/venv/bin/mpris-discord-presence \
  --config ~/.config/mpris-discord-presence/config.toml run
```

The installer installs the package into a dedicated venv with `--system-site-packages`. The runtime after installation does not refer to the checkout.
Confirm that it displays and clears as expected in the foreground before enabling the service.

```bash
systemctl --user enable --now mpris-discord-presence.service
journalctl --user -u mpris-discord-presence.service -f
```

For details, refer to [Quickstart](QUICKSTART.md); for configuration and behavior, refer to the [Usage Guide](_docs/guide/Core/mpris-discord-presence/usage.md); and for implementation boundaries, refer to the [Reference](_docs/reference/Core/mpris-discord-presence/reference.md).

## Development

```bash
PYTHONPATH=src python -m unittest -v
python -m compileall -q src tests
./scripts/test-install-user-service.sh
./scripts/check-docs.sh
```

Design decisions can be found in [_docs/intent/Core/mpris-discord-presence/decision.md](_docs/intent/Core/mpris-discord-presence/decision.md), and verification plans and results are in [_docs/qa/Core/mpris-discord-presence/](_docs/qa/Core/mpris-discord-presence/).

## Privacy / security boundary

- Only the display metadata for the selected track is sent to Discord.
- Track metadata is not left in regular logs or test artifacts.
- The only Discord credential used is the public Application ID.
- No user tokens, OAuth tokens, client secrets, or join secrets are requested or stored.
- Local `file://` artwork is not published; it falls back to the configured static application asset.

## License

[MIT License](LICENSE.txt)
