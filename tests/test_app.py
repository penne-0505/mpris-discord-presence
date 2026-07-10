from __future__ import annotations

from dataclasses import dataclass
import unittest

from mpris_discord_presence.app import PresenceController
from mpris_discord_presence.config import AppConfig
from mpris_discord_presence.models import ActivityType


@dataclass(frozen=True)
class Identity:
    base_name: str
    instance: str


@dataclass(frozen=True)
class Snapshot:
    identity: Identity
    generation: int = 1
    playback_status: str = "Playing"
    title: str | None = "Track"
    artists: tuple[str, ...] = ("Artist",)
    album: str | None = "Album"
    url: str | None = None
    artwork_url: str | None = None
    length_us: int | None = 180_000_000
    position_us: int | None = 30_000_000


@dataclass(frozen=True)
class Event:
    kind: str
    snapshot: Snapshot
    initial: bool = False


class FakeCoordinator:
    def __init__(self) -> None:
        self.last_error: BaseException | None = None
        self.desired: list[dict[str, object] | None] = []
        self.pump_times: list[float] = []
        self.shutdown_calls = 0

    def set_desired(self, activity: dict[str, object] | None) -> bool:
        if self.desired and self.desired[-1] == activity:
            return False
        self.desired.append(activity)
        return True

    def pump(self, now: float) -> bool:
        self.pump_times.append(now)
        return True

    def shutdown(self) -> bool:
        self.shutdown_calls += 1
        return True


class PresenceControllerTests(unittest.TestCase):
    def test_inv002_initial_set_is_selected_after_complete_enumeration(self) -> None:
        coordinator = FakeCoordinator()
        config = AppConfig(startup_priority=("preferred*",))
        controller = PresenceController(config, coordinator, wall_clock=lambda: 1000)

        controller.on_source_event(
            Event("updated", Snapshot(Identity("other", "other.instance")), initial=True)
        )
        controller.on_source_event(
            Event("updated", Snapshot(Identity("preferred", "preferred.instance")), initial=True)
        )
        self.assertEqual(coordinator.desired, [])

        controller.complete_initialization()

        self.assertEqual(controller.active.instance, "preferred.instance")
        self.assertEqual(coordinator.desired[-1]["details"], "Track")

    def test_inv003_denied_initial_metadata_never_reaches_payload(self) -> None:
        coordinator = FakeCoordinator()
        controller = PresenceController(AppConfig(deny_players=("private*",)), coordinator)
        controller.on_source_event(
            Event(
                "updated",
                Snapshot(Identity("private-browser", "private.instance"), title="Sensitive"),
                initial=True,
            )
        )

        controller.complete_initialization()

        self.assertEqual(coordinator.desired, [None])
        self.assertNotIn("Sensitive", repr(coordinator.desired))

    def test_inv002_vanish_during_initial_enumeration_is_folded_before_selection(self) -> None:
        coordinator = FakeCoordinator()
        controller = PresenceController(AppConfig(), coordinator)
        snapshot = Snapshot(Identity("temporary", "temporary.instance"))
        controller.on_source_event(Event("appeared", snapshot, initial=True))
        controller.on_source_event(Event("vanished", snapshot))

        controller.complete_initialization()

        self.assertIsNone(controller.active)
        self.assertEqual(coordinator.desired, [None])

    def test_ac003_disabled_sharing_requests_clear(self) -> None:
        coordinator = FakeCoordinator()
        controller = PresenceController(AppConfig(sharing_enabled=False), coordinator)
        controller.on_source_event(
            Event("updated", Snapshot(Identity("player", "player.instance")), initial=True)
        )

        controller.complete_initialization()

        self.assertIsNone(controller.active)
        self.assertEqual(coordinator.desired, [None])

    def test_inv003_disabled_sharing_ignores_runtime_playing_events(self) -> None:
        coordinator = FakeCoordinator()
        controller = PresenceController(AppConfig(sharing_enabled=False), coordinator)
        controller.complete_initialization()

        controller.on_source_event(
            Event("playback-status", Snapshot(Identity("player", "player.instance")))
        )

        self.assertIsNone(controller.active)
        self.assertEqual(coordinator.desired, [None])
        self.assertNotIn("Track", repr(coordinator.desired))

    def test_inv007_runtime_event_maps_explicit_type_only(self) -> None:
        coordinator = FakeCoordinator()
        config = AppConfig(default_activity_type=ActivityType.WATCHING)
        controller = PresenceController(config, coordinator, wall_clock=lambda: 1000)
        controller.complete_initialization()

        controller.on_source_event(
            Event("updated", Snapshot(Identity("browser", "browser.instance"), title="Music"))
        )

        self.assertEqual(coordinator.desired[-1]["type"], 3)

    def test_ac001_vanished_active_falls_back_to_remaining_playing(self) -> None:
        coordinator = FakeCoordinator()
        controller = PresenceController(AppConfig(), coordinator, wall_clock=lambda: 1000)
        first = Snapshot(Identity("first", "first.instance"), title="First")
        second = Snapshot(Identity("second", "second.instance"), title="Second")
        controller.on_source_event(Event("updated", first, initial=True))
        controller.on_source_event(Event("updated", second, initial=True))
        controller.complete_initialization()
        controller.on_source_event(
            Event("playback-status", Snapshot(first.identity, playback_status="Paused", title="First"))
        )
        controller.on_source_event(
            Event("playback-status", Snapshot(first.identity, playback_status="Playing", title="First"))
        )

        controller.on_source_event(Event("vanished", first))

        self.assertEqual(controller.active.instance, "second.instance")
        self.assertEqual(coordinator.desired[-1]["details"], "Second")

    def test_inv006_tick_without_semantic_change_does_not_replace_desired(self) -> None:
        coordinator = FakeCoordinator()
        clock_values = iter((0.0, 0.1))
        controller = PresenceController(
            AppConfig(),
            coordinator,
            monotonic_clock=lambda: next(clock_values),
        )
        controller.complete_initialization()

        controller.tick()

        self.assertEqual(coordinator.desired, [None])
        self.assertEqual(coordinator.pump_times, [0.0])

    def test_ac003_shutdown_delegates_immediate_clear(self) -> None:
        coordinator = FakeCoordinator()
        controller = PresenceController(AppConfig(), coordinator)

        self.assertTrue(controller.shutdown())
        self.assertEqual(coordinator.shutdown_calls, 1)


if __name__ == "__main__":
    unittest.main()
