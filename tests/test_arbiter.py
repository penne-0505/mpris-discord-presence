from __future__ import annotations

import itertools
import unittest

from mpris_discord_presence.arbiter import ActivePlayerArbiter
from mpris_discord_presence.config import parse_config
from mpris_discord_presence.models import PlaybackStatus, PlayerState, TrackMetadata


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def player(instance: str, status: PlaybackStatus, title: str | None = None) -> PlayerState:
    base = instance.split(".instance", 1)[0]
    return PlayerState(
        instance=instance,
        player_name=base,
        generation=1,
        status=status,
        metadata=TrackMetadata(title=title or instance),
        position_us=1_000_000,
    )


class ActivePlayerArbiterTest(unittest.TestCase):
    def test_inv001_latest_playing_transition_wins_and_falls_back(self) -> None:
        arbiter = ActivePlayerArbiter(parse_config({}))
        arbiter.initialize([])

        first = arbiter.upsert(player("alpha", PlaybackStatus.PLAYING))
        second = arbiter.upsert(player("beta", PlaybackStatus.PLAYING))
        fallback = arbiter.upsert(player("beta", PlaybackStatus.PAUSED))

        self.assertEqual(first.active.instance, "alpha")
        self.assertEqual(second.active.instance, "beta")
        self.assertEqual(fallback.active.instance, "alpha")
        self.assertTrue(fallback.publish)

    def test_metadata_update_does_not_steal_active(self) -> None:
        arbiter = ActivePlayerArbiter(parse_config({}))
        arbiter.initialize([])
        arbiter.upsert(player("alpha", PlaybackStatus.PLAYING))
        arbiter.upsert(player("beta", PlaybackStatus.PLAYING))

        decision = arbiter.upsert(player("alpha", PlaybackStatus.PLAYING, "new title"))

        self.assertEqual(decision.active.instance, "beta")
        self.assertFalse(decision.publish)

    def test_active_pause_clears_after_grace_when_no_fallback(self) -> None:
        clock = FakeClock()
        arbiter = ActivePlayerArbiter(parse_config({"clear_grace_seconds": 1.5}), clock=clock)
        arbiter.initialize([player("alpha", PlaybackStatus.PLAYING)])

        paused = arbiter.upsert(player("alpha", PlaybackStatus.PAUSED))
        clock.advance(1.4)
        pending = arbiter.poll()
        clock.advance(0.1)
        cleared = arbiter.poll()

        self.assertTrue(paused.grace_pending)
        self.assertTrue(pending.grace_pending)
        self.assertTrue(cleared.clear)
        self.assertIsNone(cleared.active)

    def test_grace_is_cancelled_when_player_resumes(self) -> None:
        clock = FakeClock()
        arbiter = ActivePlayerArbiter(parse_config({}), clock=clock)
        arbiter.initialize([player("alpha", PlaybackStatus.PLAYING)])
        arbiter.upsert(player("alpha", PlaybackStatus.PAUSED))

        resumed = arbiter.upsert(player("alpha", PlaybackStatus.PLAYING))
        clock.advance(2.0)

        self.assertTrue(resumed.publish)
        self.assertFalse(arbiter.poll().clear)
        self.assertEqual(arbiter.active.instance, "alpha")

    def test_grace_deadline_is_not_extended_by_paused_metadata_updates(self) -> None:
        clock = FakeClock()
        arbiter = ActivePlayerArbiter(parse_config({"clear_grace_seconds": 1.5}), clock=clock)
        arbiter.initialize([player("alpha", PlaybackStatus.PLAYING)])
        arbiter.upsert(player("alpha", PlaybackStatus.PAUSED))
        original_deadline = arbiter.next_deadline
        clock.advance(1.0)

        arbiter.upsert(player("alpha", PlaybackStatus.PAUSED, "metadata changed"))
        clock.advance(0.5)

        self.assertEqual(arbiter.next_deadline, original_deadline)
        self.assertTrue(arbiter.poll().clear)

    def test_inv002_startup_selection_is_discovery_order_independent(self) -> None:
        states = [
            player("vivaldi.instance2", PlaybackStatus.PLAYING),
            player("waydroid_mpris", PlaybackStatus.PLAYING),
            player("alpha", PlaybackStatus.PLAYING),
        ]
        config = parse_config({"startup_priority": ["waydroid_mpris", "vivaldi*"]})
        selections = set()

        for permutation in itertools.permutations(states):
            arbiter = ActivePlayerArbiter(config)
            selections.add(arbiter.initialize(permutation).active.instance)

        self.assertEqual(selections, {"waydroid_mpris"})

    def test_inv003_denied_player_never_becomes_active(self) -> None:
        arbiter = ActivePlayerArbiter(parse_config({"deny_players": ["private*"]}))
        arbiter.initialize([])

        decision = arbiter.upsert(player("private.instance1", PlaybackStatus.PLAYING))

        self.assertIsNone(decision.active)
        self.assertIsNone(arbiter.active)

    def test_disable_clears_active(self) -> None:
        arbiter = ActivePlayerArbiter(parse_config({}))
        arbiter.initialize([player("alpha", PlaybackStatus.PLAYING)])

        decision = arbiter.disable()

        self.assertTrue(decision.clear)
        self.assertIsNone(arbiter.active)


if __name__ == "__main__":
    unittest.main()
