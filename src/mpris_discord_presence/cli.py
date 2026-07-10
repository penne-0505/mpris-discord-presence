from __future__ import annotations

import argparse
import logging
from pathlib import Path
import signal
import sys
from typing import Sequence

from .app import PresenceController
from .config import AppConfig, ConfigError, default_config_path, load_config
from .discord_ipc import (
    BackoffPolicy,
    DiscordIPCClient,
    DiscordRPCError,
    ReconnectCoordinator,
    discover_ipc_sockets,
)


LOGGER = logging.getLogger("mpris_discord_presence")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mpris-discord-presence",
        description="Publish the active Linux MPRIS player as Discord Rich Presence.",
    )
    parser.add_argument("--config", type=Path, help="TOML config path")
    parser.add_argument("--verbose", action="store_true", help="enable debug logs")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run", help="run the foreground presence daemon")
    subparsers.add_parser("doctor", help="check config and local runtime dependencies")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        parser.error(str(exc))

    if args.command == "doctor":
        return run_doctor(config)
    if args.command == "run":
        return run_daemon(config)
    parser.error(f"unknown command: {args.command}")


def run_doctor(config: AppConfig) -> int:
    failures = 0
    config_path = config.config_path or default_config_path()
    if config_path.exists():
        _check("PASS", f"config: {config_path}")
    else:
        failures += 1
        _check("FAIL", f"config is missing: {config_path}")

    if config.application_id:
        _check("PASS", "Discord Application ID is configured")
    else:
        failures += 1
        _check(
            "FAIL",
            "Discord Application ID is missing (config or MPRIS_DISCORD_APPLICATION_ID)",
        )

    try:
        import gi

        gi.require_version("Playerctl", "2.0")
        from gi.repository import Playerctl

        manager = Playerctl.PlayerManager()
        player_names = tuple(manager.props.player_names)
    except (ImportError, ValueError, RuntimeError) as exc:
        failures += 1
        _check("FAIL", f"Playerctl GI runtime is unavailable: {type(exc).__name__}")
    else:
        _check("PASS", f"Playerctl GI runtime; {len(player_names)} MPRIS player(s) visible")
        for name in sorted(_safe_player_name(item) for item in player_names):
            _check("INFO", f"MPRIS player: {name}")

    sockets = discover_ipc_sockets()
    if sockets:
        _check("PASS", f"same-user Discord IPC socket: {sockets[0]}")
    else:
        _check("WARN", "Discord IPC socket not found; the daemon will retry while Discord is offline")

    if config.sharing_enabled:
        _check("WARN", "sharing_enabled=true publishes metadata from every non-denied MPRIS player")
    else:
        _check("PASS", "sharing_enabled=false; the daemon will only clear Presence")
    _check("INFO", f"deny_players: {', '.join(config.deny_players) or '(empty)'}")
    return 1 if failures else 0


def run_daemon(config: AppConfig) -> int:
    if not config.application_id:
        LOGGER.error(
            "Discord Application ID is required; run doctor after editing %s",
            config.config_path or default_config_path(),
        )
        return 2

    try:
        import gi

        gi.require_version("GLib", "2.0")
        from gi.repository import GLib

        from .mpris_source import PlayerctlMprisSource
    except (ImportError, ValueError, RuntimeError) as exc:
        LOGGER.error("Playerctl/GLib runtime is unavailable: %s", type(exc).__name__)
        return 2

    coordinator = ReconnectCoordinator(
        lambda: DiscordIPCClient(config.application_id or ""),
        backoff=BackoffPolicy(
            initial_delay=config.reconnect_initial_seconds,
            maximum_delay=config.reconnect_max_seconds,
        ),
    )
    controller = PresenceController(config, coordinator)

    def handle_source_event(event: object) -> None:
        try:
            controller.on_source_event(event)
        except Exception:
            # Never include the event repr: it can contain private track metadata.
            LOGGER.exception("failed to process an MPRIS state event")

    # Config owns the deny policy. Keep Playerctl's synthetic player visible
    # here so removing it from deny_players has the documented effect.
    source = PlayerctlMprisSource(handle_source_event, ignore_playerctld=False)
    last_transport_error: tuple[type[BaseException], int | str | None] | None = None
    stop_requested = False

    def pump() -> bool:
        nonlocal last_transport_error
        try:
            published = controller.tick()
        except Exception:
            LOGGER.exception("presence loop iteration failed")
            return True

        error = controller.last_transport_error
        marker = _transport_error_marker(error)
        if marker != last_transport_error:
            if error is None and last_transport_error is not None:
                LOGGER.info("Discord IPC connection recovered")
            elif error is not None:
                LOGGER.warning(
                    "Discord IPC unavailable; retry scheduled: %s",
                    _transport_error_summary(error),
                )
            last_transport_error = marker
        if published:
            LOGGER.debug("Discord Presence state synchronized")
        return True

    def request_stop(signum: int, _frame: object) -> None:
        nonlocal stop_requested
        stop_requested = True
        LOGGER.info("received signal %s; clearing Presence", signum)
        source.stop()

    previous_handlers: dict[int, object] = {}
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, request_stop)
        source.start()
        controller.complete_initialization()
        if stop_requested:
            return 0
        pump()
        if stop_requested:
            return 0
        GLib.timeout_add(100, pump)
        LOGGER.info("MPRIS Discord Presence started")
        source.run()
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception:
        LOGGER.exception("daemon stopped after a runtime failure")
        return 1
    finally:
        clear_confirmed = False
        try:
            clear_confirmed = controller.shutdown()
        finally:
            source.close()
            for signum, previous in previous_handlers.items():
                signal.signal(signum, previous)
        if clear_confirmed:
            LOGGER.info("Discord Presence clear acknowledged; daemon stopped")
        elif controller.last_transport_error is not None:
            LOGGER.warning(
                "daemon stopped without a confirmed Presence clear: %s",
                _transport_error_summary(controller.last_transport_error),
            )
        else:
            LOGGER.info(
                "daemon stopped; no additional Presence clear acknowledgement was available"
            )


def _check(level: str, message: str) -> None:
    print(f"[{level}] {message}")


def _safe_player_name(player_name: object) -> str:
    instance = getattr(player_name, "instance", None)
    name = getattr(player_name, "name", None)
    return str(instance or name or "unknown")


def _transport_error_marker(
    error: BaseException | None,
) -> tuple[type[BaseException], int | str | None] | None:
    if error is None:
        return None
    code = error.code if isinstance(error, DiscordRPCError) else None
    return (type(error), code)


def _transport_error_summary(error: BaseException) -> str:
    if isinstance(error, DiscordRPCError) and error.code is not None:
        return f"DiscordRPCError code={error.code}"
    return type(error).__name__


if __name__ == "__main__":
    sys.exit(main())
