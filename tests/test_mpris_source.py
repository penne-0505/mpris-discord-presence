from __future__ import annotations

from dataclasses import FrozenInstanceError
import logging
from types import SimpleNamespace
import unittest
from unittest import mock

from mpris_discord_presence.mpris_source import (
    PlaybackStatus,
    PlayerIdentity,
    PlayerctlMprisSource,
    PlayerctlUnavailableError,
    SourceEventKind,
    _load_playerctl_bindings,
)


class FakeVariant:
    def __init__(self, value):
        self.value = value

    def unpack(self):
        return self.value


class FakePlayerName:
    def __init__(self, name: str, instance: str):
        self.name = name
        self.instance = instance


class FakePlayer:
    def __init__(
        self,
        name: str,
        instance: str,
        *,
        status="stopped",
        metadata=None,
        position=0,
    ):
        self.props = SimpleNamespace(
            player_name=name,
            player_instance=instance,
            playback_status=status,
            metadata={} if metadata is None else metadata,
            position=position,
        )
        self._next_signal_id = 1
        self._signals = {}

    def connect(self, signal_name, callback, *user_data):
        signal_id = self._next_signal_id
        self._next_signal_id += 1
        self._signals[signal_id] = (signal_name, callback, user_data)
        return signal_id

    def disconnect(self, signal_id):
        self._signals.pop(signal_id, None)

    def emit(self, signal_name, value):
        for registered_name, callback, user_data in list(self._signals.values()):
            if registered_name == signal_name:
                callback(self, value, *user_data)


class FakeManager:
    def __init__(self, player_names=()):
        self.props = SimpleNamespace(player_names=list(player_names))
        self._next_signal_id = 1
        self._signals = {}
        self.players = []

    def connect(self, signal_name, callback):
        signal_id = self._next_signal_id
        self._next_signal_id += 1
        self._signals[signal_id] = (signal_name, callback)
        return signal_id

    def disconnect(self, signal_id):
        self._signals.pop(signal_id, None)

    def manage_player(self, player):
        self.players.append(player)
        self.emit("player-appeared", player)

    def emit(self, signal_name, value):
        for registered_name, callback in list(self._signals.values()):
            if registered_name == signal_name:
                callback(self, value)

    def appear_name(self, player_name):
        self.emit("name-appeared", player_name)

    def vanish(self, player):
        self.emit("player-vanished", player)


class CapturingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


class PlayerctlMprisSourceTests(unittest.TestCase):
    def make_source(
        self,
        players,
        *,
        initial_names=(),
        ignore_playerctld=True,
        callback=None,
        logger=None,
    ):
        manager = FakeManager(initial_names)
        events = []

        def player_factory(player_name):
            return players[player_name.instance]

        source = PlayerctlMprisSource(
            events.append if callback is None else callback,
            ignore_playerctld=ignore_playerctld,
            manager_factory=lambda: manager,
            player_factory=player_factory,
            main_loop_factory=lambda: None,
            logger=logger,
        )
        return source, manager, events

    def test_ac001_initial_players_are_sorted_and_fully_normalized(self):
        names = [
            FakePlayerName("zeta", "zeta.instance2"),
            FakePlayerName("alpha", "alpha.instance1"),
        ]
        players = {
            "alpha.instance1": FakePlayer(
                "alpha", "alpha.instance1", status="Playing"
            ),
            "zeta.instance2": FakePlayer(
                "zeta", "zeta.instance2", status="Paused"
            ),
        }
        source, _manager, events = self.make_source(
            players, initial_names=names
        )

        source.start()

        self.assertEqual(
            [event.snapshot.identity.instance for event in events],
            ["alpha.instance1", "zeta.instance2"],
        )
        self.assertTrue(all(event.initial for event in events))
        self.assertEqual(events[0].kind, SourceEventKind.APPEARED)
        self.assertEqual(events[0].snapshot.playback_status, PlaybackStatus.PLAYING)
        self.assertEqual(events[1].snapshot.playback_status, PlaybackStatus.PAUSED)

    def test_ac001_lifecycle_and_player_signals_emit_plain_immutable_events(self):
        name = FakePlayerName("vivaldi", "vivaldi.instance7")
        player = FakePlayer(
            "vivaldi",
            "vivaldi.instance7",
            status="stopped",
            metadata={"xesam:title": "Before"},
            position=5,
        )
        source, manager, events = self.make_source(
            {name.instance: player}
        )
        source.start()

        manager.appear_name(name)
        player.props.playback_status = "playing"
        player.emit("playback-status", "playing")
        player.props.metadata = {"xesam:title": "After"}
        player.emit("metadata", player.props.metadata)
        player.props.position = 42
        player.emit("seeked", 42)
        manager.vanish(player)

        self.assertEqual(
            [event.kind for event in events],
            [
                SourceEventKind.APPEARED,
                SourceEventKind.PLAYBACK_STATUS,
                SourceEventKind.METADATA,
                SourceEventKind.SEEKED,
                SourceEventKind.VANISHED,
            ],
        )
        self.assertFalse(events[0].initial)
        self.assertEqual(events[1].snapshot.playback_status, PlaybackStatus.PLAYING)
        self.assertEqual(events[2].snapshot.title, "After")
        self.assertEqual(events[3].snapshot.position_us, 42)
        self.assertEqual(events[4].snapshot.position_us, 42)
        self.assertEqual(
            events[0].snapshot.identity,
            PlayerIdentity("vivaldi", "vivaldi.instance7"),
        )
        with self.assertRaises(FrozenInstanceError):
            events[2].snapshot.title = "mutated"

    def test_inv001_playback_transition_order_is_preserved(self):
        name = FakePlayerName("vlc", "vlc.instance1")
        player = FakePlayer("vlc", name.instance, status="stopped")
        source, manager, events = self.make_source({name.instance: player})
        source.start()
        manager.appear_name(name)

        for status in ("playing", "paused", "playing"):
            player.props.playback_status = status
            player.emit("playback-status", status)

        self.assertEqual(
            [event.snapshot.playback_status for event in events[1:]],
            [
                PlaybackStatus.PLAYING,
                PlaybackStatus.PAUSED,
                PlaybackStatus.PLAYING,
            ],
        )
        self.assertTrue(
            all(event.kind == "playback-status" for event in events[1:])
        )

    def test_ac002_metadata_missing_and_invalid_values_normalize_safely(self):
        name = FakePlayerName("browser", "browser.instance1")
        player = FakePlayer(
            "browser",
            "browser.instance1",
            status=object(),
            metadata=FakeVariant(
                {
                    "xesam:title": FakeVariant("  A title  "),
                    "xesam:artist": FakeVariant(
                        ["Artist", "", 17, FakeVariant(" Guest ")]
                    ),
                    "xesam:album": 123,
                    "xesam:url": FakeVariant(" https://example.test/track "),
                    "mpris:artUrl": FakeVariant("file:///tmp/art.png"),
                    "mpris:length": True,
                }
            ),
            position=-1,
        )
        source, _manager, events = self.make_source(
            {name.instance: player}, initial_names=[name]
        )

        source.start()
        snapshot = events[0].snapshot

        self.assertEqual(snapshot.playback_status, PlaybackStatus.UNKNOWN)
        self.assertEqual(snapshot.title, "A title")
        self.assertEqual(snapshot.artists, ("Artist", "Guest"))
        self.assertIsNone(snapshot.album)
        self.assertEqual(snapshot.url, "https://example.test/track")
        self.assertEqual(snapshot.artwork_url, "file:///tmp/art.png")
        self.assertIsNone(snapshot.length_us)
        self.assertIsNone(snapshot.position_us)

        player.props.metadata = "not-a-mapping"
        player.emit("metadata", player.props.metadata)
        empty = events[-1].snapshot
        self.assertIsNone(empty.title)
        self.assertEqual(empty.artists, ())
        self.assertIsNone(empty.artwork_url)

    def test_inv002_startup_order_does_not_change_snapshot_order(self):
        names = [
            FakePlayerName("bravo", "bravo.instance2"),
            FakePlayerName("alpha", "alpha.instance1"),
        ]
        players = {
            name.instance: FakePlayer(name.name, name.instance, status="playing")
            for name in names
        }

        observed_orders = []
        for initial_names in (names, list(reversed(names))):
            source, _manager, events = self.make_source(
                players, initial_names=initial_names
            )
            source.start()
            observed_orders.append(
                [event.snapshot.identity.instance for event in events]
            )
            source.close()

        self.assertEqual(observed_orders[0], observed_orders[1])

    def test_playerctld_is_ignored_by_default_but_can_be_included(self):
        name = FakePlayerName("playerctld", "playerctld")
        player = FakePlayer("playerctld", "playerctld", status="playing")

        source, manager, events = self.make_source(
            {name.instance: player}, initial_names=[name]
        )
        source.start()
        self.assertEqual(events, [])
        self.assertEqual(manager.players, [])

        included, included_manager, included_events = self.make_source(
            {name.instance: player},
            initial_names=[name],
            ignore_playerctld=False,
        )
        included.start()
        self.assertEqual(len(included_events), 1)
        self.assertEqual(included_manager.players, [player])

    def test_generation_ignores_callbacks_from_vanished_player(self):
        name = FakePlayerName("vlc", "vlc.instance1")
        old_player = FakePlayer("vlc", name.instance, status="playing")
        players = {name.instance: old_player}
        source, manager, events = self.make_source(players)
        source.start()
        manager.appear_name(name)
        old_callbacks = list(old_player._signals.values())
        manager.vanish(old_player)

        new_player = FakePlayer("vlc", name.instance, status="paused")
        players[name.instance] = new_player
        manager.appear_name(name)
        self.assertEqual(events[-1].snapshot.generation, 2)

        for signal_name, callback, user_data in old_callbacks:
            if signal_name == "playback-status":
                callback(old_player, "playing", *user_data)

        self.assertEqual(len(events), 3)
        self.assertEqual(events[-1].snapshot.generation, 2)
        self.assertEqual(events[-1].snapshot.playback_status, PlaybackStatus.PAUSED)

    def test_callbacks_and_error_logs_never_expose_raw_metadata(self):
        secret_marker = "private-track-title-7162"
        name = FakePlayerName("browser", "browser.instance1")
        player = FakePlayer(
            "browser",
            name.instance,
            metadata={"xesam:title": secret_marker},
        )
        handler = CapturingHandler()
        logger = logging.getLogger(f"test-mpris-source-{id(self)}")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        def failing_callback(_event):
            raise RuntimeError(secret_marker)

        source, _manager, _events = self.make_source(
            {name.instance: player},
            initial_names=[name],
            callback=failing_callback,
            logger=logger,
        )
        source.start()

        self.assertTrue(handler.messages)
        self.assertNotIn(secret_marker, "\n".join(handler.messages))

    def test_close_disconnects_manager_and_player_handlers(self):
        name = FakePlayerName("vlc", "vlc.instance1")
        player = FakePlayer("vlc", name.instance)
        source, manager, _events = self.make_source(
            {name.instance: player}, initial_names=[name]
        )
        source.start()

        source.close()

        self.assertFalse(source.started)
        self.assertEqual(manager._signals, {})
        self.assertEqual(player._signals, {})
        self.assertEqual(source.snapshots(), ())

    def test_gi_import_failure_is_actionable(self):
        real_import = __import__

        def failing_import(name, *args, **kwargs):
            if name == "gi":
                raise ImportError("missing gi")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=failing_import):
            with self.assertRaises(PlayerctlUnavailableError) as raised:
                _load_playerctl_bindings()

        message = str(raised.exception)
        self.assertIn("Playerctl GI bindings are unavailable", message)
        self.assertIn("python-gobject", message)
        self.assertIn("gir1.2-playerctl-2.0", message)


if __name__ == "__main__":
    unittest.main()
