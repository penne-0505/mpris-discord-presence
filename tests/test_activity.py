from __future__ import annotations

import unittest

from mpris_discord_presence.activity import build_activity, public_https_url, truncate_text
from mpris_discord_presence.config import parse_config
from mpris_discord_presence.models import ActivityType, PlaybackStatus, PlayerState, TrackMetadata


def state(**metadata) -> PlayerState:
    return PlayerState(
        instance="vivaldi.instance1",
        player_name="vivaldi",
        generation=1,
        status=PlaybackStatus.PLAYING,
        metadata=TrackMetadata(**metadata),
        position_us=30_000_000,
    )


class ActivityMappingTest(unittest.TestCase):
    def test_ac002_maps_fields_type_and_progress_timestamps(self) -> None:
        config = parse_config({"activity_types": {"vivaldi*": "watching"}})

        activity = build_activity(
            state(
                title="Example video",
                artists=("Example creator",),
                album="Example series",
                length_us=120_000_000,
                url="https://example.com/watch/1",
                art_url="https://cdn.example.com/art.png",
            ),
            config,
            wall_clock=lambda: 1_000.0,
        )
        payload = activity.to_rpc_dict()

        self.assertEqual(activity.activity_type, ActivityType.WATCHING)
        self.assertEqual(payload["details"], "Example video")
        self.assertEqual(payload["state"], "Example creator を再生中")
        self.assertEqual(payload["status_display_type"], 1)
        self.assertEqual(payload["timestamps"], {"start": 970, "end": 1090})
        self.assertEqual(payload["assets"]["large_image"], "https://cdn.example.com/art.png")
        self.assertEqual(payload["assets"]["large_text"], "Example series")
        self.assertEqual(payload["buttons"][0]["url"], "https://example.com/watch/1")

    def test_missing_metadata_uses_player_label(self) -> None:
        activity = build_activity(state(), parse_config({}), wall_clock=lambda: 1_000.0)

        self.assertEqual(activity.details, "vivaldi")
        self.assertEqual(activity.state, "vivaldi を再生中")

    def test_ac008_compact_status_formats_artist_playing_state(self) -> None:
        payload = build_activity(
            state(
                title="Example track",
                artists=("Example artist",),
                album="Example album",
            ),
            parse_config({}),
        ).to_rpc_dict()

        self.assertEqual(payload["status_display_type"], 1)
        self.assertEqual(payload["state"], "Example artist を再生中")
        self.assertEqual(payload["details"], "Example track")

    def test_inv008_compact_status_state_has_metadata_fallbacks(self) -> None:
        album_payload = build_activity(
            state(album="Example album"),
            parse_config({}),
        ).to_rpc_dict()
        player_payload = build_activity(state(), parse_config({})).to_rpc_dict()

        self.assertEqual(album_payload["state"], "Example album を再生中")
        self.assertEqual(album_payload["status_display_type"], 1)
        self.assertEqual(player_payload["state"], "vivaldi を再生中")
        self.assertEqual(player_payload["status_display_type"], 1)

    def test_local_or_private_artwork_uses_fallback_asset(self) -> None:
        config = parse_config({"fallback_art_asset": "default-art"})

        for art_url in [
            "file:///tmp/private.png",
            "http://example.com/art.png",
            "https://localhost/art.png",
            "https://127.0.0.1/art.png",
        ]:
            with self.subTest(art_url=art_url):
                activity = build_activity(
                    state(art_url=art_url),
                    config,
                    wall_clock=lambda: 1_000.0,
                )
                self.assertEqual(activity.large_image, "default-art")

    def test_inv007_content_does_not_change_default_activity_type(self) -> None:
        activity = build_activity(
            state(title="YouTube Music", url="https://youtube.com/watch?v=private"),
            parse_config({}),
        )

        self.assertEqual(activity.activity_type, ActivityType.LISTENING)

    def test_text_is_unicode_safe_and_bounded(self) -> None:
        value = "曲" * 200
        truncated = truncate_text(value)

        self.assertEqual(len(truncated), 128)
        self.assertTrue(truncated.endswith("…"))

    def test_public_https_url_rejects_non_public_targets(self) -> None:
        self.assertEqual(public_https_url("https://example.com/a"), "https://example.com/a")
        self.assertIsNone(public_https_url("https://192.168.1.10/a"))
        self.assertIsNone(public_https_url("file:///tmp/a"))

    def test_button_url_honors_discord_512_character_limit(self) -> None:
        prefix = "https://example.com/"
        accepted = prefix + "a" * (512 - len(prefix))
        rejected = accepted + "b"

        accepted_payload = build_activity(
            state(url=accepted),
            parse_config({}),
        ).to_rpc_dict()
        rejected_payload = build_activity(
            state(url=rejected),
            parse_config({}),
        ).to_rpc_dict()

        self.assertEqual(accepted_payload["buttons"][0]["url"], accepted)
        self.assertNotIn("buttons", rejected_payload)
        self.assertNotIn("details_url", rejected_payload)

    def test_position_is_clamped_to_duration_and_empty_art_assets_are_omitted(self) -> None:
        player_state = state(length_us=10_000_000)
        player_state = PlayerState(
            instance=player_state.instance,
            player_name=player_state.player_name,
            generation=player_state.generation,
            status=player_state.status,
            metadata=player_state.metadata,
            position_us=30_000_000,
        )

        payload = build_activity(
            player_state,
            parse_config({}),
            wall_clock=lambda: 1_000.0,
        ).to_rpc_dict()

        self.assertEqual(payload["timestamps"], {"start": 990, "end": 1000})
        self.assertNotIn("assets", payload)


if __name__ == "__main__":
    unittest.main()
