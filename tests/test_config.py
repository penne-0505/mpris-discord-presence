from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mpris_discord_presence.config import ConfigError, load_config, parse_config
from mpris_discord_presence.models import ActivityType


class ConfigTest(unittest.TestCase):
    def test_ac003_share_all_default_and_playerctld_deny(self) -> None:
        config = parse_config({})

        self.assertTrue(config.sharing_enabled)
        self.assertFalse(config.is_denied("vivaldi.instance1", "vivaldi"))
        self.assertTrue(config.is_denied("playerctld", "playerctld"))

    def test_inv003_denylist_matches_instance_or_base_name(self) -> None:
        config = parse_config({"deny_players": ["firefox*", "private-player"]})

        self.assertTrue(config.is_denied("firefox.instance42", "firefox"))
        self.assertTrue(config.is_denied("private-player.instance1", "private-player"))
        self.assertFalse(config.is_denied("vivaldi.instance1", "vivaldi"))

    def test_inv007_activity_type_uses_explicit_player_rule(self) -> None:
        config = parse_config(
            {
                "default_activity_type": "listening",
                "activity_types": {"vivaldi*": "watching"},
            }
        )

        self.assertEqual(
            config.activity_type_for("vivaldi.instance1", "vivaldi"),
            ActivityType.WATCHING,
        )
        self.assertEqual(
            config.activity_type_for("waydroid_mpris", "waydroid_mpris"),
            ActivityType.LISTENING,
        )

    def test_inv004_rejects_non_public_application_id_shape(self) -> None:
        with self.assertRaisesRegex(ConfigError, "decimal digits"):
            parse_config({"application_id": "not-a-secret-or-id"})
        with self.assertRaisesRegex(ConfigError, "decimal digits"):
            parse_config({"application_id": "١٢٣٤٥٦٧٨٩"})

    def test_reconnect_backoff_bounds_are_validated(self) -> None:
        with self.assertRaisesRegex(ConfigError, "at least"):
            parse_config({"reconnect_initial_seconds": 5, "reconnect_max_seconds": 1})

    def test_inv003_unknown_privacy_key_is_rejected_instead_of_defaulting(self) -> None:
        with self.assertRaisesRegex(ConfigError, "sharing_enable"):
            parse_config({"sharing_enable": False})

    def test_inv004_missing_file_still_validates_environment_application_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.toml"
            with patch.dict(
                os.environ,
                {"MPRIS_DISCORD_APPLICATION_ID": "not-a-number"},
                clear=False,
            ):
                with self.assertRaisesRegex(ConfigError, "decimal digits"):
                    load_config(missing)


if __name__ == "__main__":
    unittest.main()
