from __future__ import annotations

import contextlib
import io
from pathlib import Path
import signal
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from mpris_discord_presence.cli import (
    _transport_error_summary,
    build_parser,
    run_daemon,
    run_doctor,
)
from mpris_discord_presence.config import AppConfig
from mpris_discord_presence.discord_ipc import DiscordRPCError


class CliTests(unittest.TestCase):
    def test_ac006_parser_requires_explicit_command(self) -> None:
        parser = build_parser()

        args = parser.parse_args(["--config", "/tmp/config.toml", "doctor"])

        self.assertEqual(args.command, "doctor")
        self.assertEqual(args.config, Path("/tmp/config.toml"))

    def test_ac006_run_refuses_missing_application_id(self) -> None:
        with self.assertLogs("mpris_discord_presence", level="ERROR"):
            self.assertEqual(run_daemon(AppConfig()), 2)

    def test_ac006_doctor_reports_missing_config_and_id_without_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = AppConfig(config_path=Path(directory) / "missing.toml")
            output = io.StringIO()
            with (
                patch("mpris_discord_presence.cli.discover_ipc_sockets", return_value=()),
                patch.dict(sys.modules, {"gi": None}),
                contextlib.redirect_stdout(output),
            ):
                result = run_doctor(config)

        self.assertEqual(result, 1)
        self.assertIn("[FAIL] config is missing", output.getvalue())
        self.assertIn("Application ID is missing", output.getvalue())

    def test_inv003_transport_error_log_summary_excludes_remote_message(self) -> None:
        marker = "private-track-title-7162"

        summary = _transport_error_summary(DiscordRPCError(marker, code=4000))

        self.assertEqual(summary, "DiscordRPCError code=4000")
        self.assertNotIn(marker, summary)

    def test_ac003_sigterm_path_requests_confirmed_shutdown_clear(self) -> None:
        coordinator = _FakeCoordinator()
        fake_gi = ModuleType("gi")
        fake_gi.require_version = lambda *_args: None  # type: ignore[attr-defined]
        fake_repository = ModuleType("gi.repository")
        fake_repository.GLib = _FakeGLib  # type: ignore[attr-defined]

        with (
            patch.dict(
                sys.modules,
                {"gi": fake_gi, "gi.repository": fake_repository},
            ),
            patch(
                "mpris_discord_presence.mpris_source.PlayerctlMprisSource",
                _SignalStoppingSource,
            ),
            patch(
                "mpris_discord_presence.cli.ReconnectCoordinator",
                return_value=coordinator,
            ),
            self.assertLogs("mpris_discord_presence", level="INFO") as logs,
        ):
            result = run_daemon(AppConfig(application_id="123456789012345678"))

        self.assertEqual(result, 0)
        self.assertEqual(coordinator.shutdown_calls, 1)
        self.assertIn("Presence clear acknowledged", "\n".join(logs.output))


class _FakeCoordinator:
    def __init__(self) -> None:
        self.last_error: BaseException | None = None
        self.desired = None
        self.shutdown_calls = 0

    def set_desired(self, activity):
        self.desired = activity
        return True

    def pump(self, _now):
        return True

    def shutdown(self):
        self.shutdown_calls += 1
        return True


class _FakeGLib:
    @staticmethod
    def timeout_add(_interval, _callback):
        return 1


class _SignalStoppingSource:
    def __init__(self, _callback, **_kwargs) -> None:
        self.stop_calls = 0

    def start(self) -> None:
        return None

    def run(self) -> None:
        signal.raise_signal(signal.SIGTERM)

    def stop(self) -> None:
        self.stop_calls += 1

    def close(self) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
