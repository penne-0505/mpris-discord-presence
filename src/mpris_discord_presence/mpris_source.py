"""Playerctl-backed MPRIS event source.

The adapter owns all GI objects and converts their signals into immutable,
plain-Python values before invoking the consumer callback.  Importing this
module does not require PyGObject, which keeps domain tests independent from a
desktop session.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
import logging
from typing import Any


class PlayerctlUnavailableError(RuntimeError):
    """Raised when the Playerctl GI runtime cannot be loaded."""


class MprisSourceError(RuntimeError):
    """Raised when the MPRIS source cannot be initialized."""


class PlaybackStatus(StrEnum):
    """Normalized MPRIS playback state."""

    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    UNKNOWN = "unknown"


class SourceEventKind(StrEnum):
    """Reason a source snapshot was emitted."""

    APPEARED = "appeared"
    PLAYBACK_STATUS = "playback-status"
    METADATA = "metadata"
    SEEKED = "seeked"
    VANISHED = "vanished"


@dataclass(frozen=True, slots=True)
class PlayerIdentity:
    """Stable Playerctl identity, retaining both base and instance names."""

    base_name: str
    instance: str


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    """Normalized player state that contains no GI-owned values."""

    identity: PlayerIdentity
    generation: int
    playback_status: PlaybackStatus
    title: str | None = None
    artists: tuple[str, ...] = ()
    album: str | None = None
    url: str | None = None
    artwork_url: str | None = None
    length_us: int | None = None
    position_us: int | None = None


@dataclass(frozen=True, slots=True)
class SourceEvent:
    """One immutable source observation delivered to the domain layer."""

    kind: SourceEventKind
    snapshot: SourceSnapshot
    initial: bool = False


@dataclass(frozen=True, slots=True)
class _PlayerctlBindings:
    manager_factory: Callable[[], Any]
    player_factory: Callable[[Any], Any]
    main_loop_factory: Callable[[], Any]


@dataclass(slots=True)
class _ManagedPlayer:
    player: Any
    generation: int
    snapshot: SourceSnapshot
    signal_ids: list[int] = field(default_factory=list)


EventCallback = Callable[[SourceEvent], None]


def _load_playerctl_bindings() -> _PlayerctlBindings:
    """Load GI lazily and provide an actionable failure at the CLI boundary."""

    try:
        import gi

        gi.require_version("Playerctl", "2.0")
        from gi.repository import GLib, Playerctl
    except (ImportError, ValueError, RuntimeError) as exc:
        raise PlayerctlUnavailableError(
            "Playerctl GI bindings are unavailable. On Arch/EndeavourOS install "
            "'python-gobject' and 'playerctl'; on Debian/Ubuntu install "
            "'python3-gi' and 'gir1.2-playerctl-2.0'. Then verify with: "
            "python -c \"import gi; gi.require_version('Playerctl', '2.0'); "
            "from gi.repository import Playerctl\""
        ) from exc

    return _PlayerctlBindings(
        manager_factory=Playerctl.PlayerManager.new,
        player_factory=Playerctl.Player.new_from_name,
        main_loop_factory=GLib.MainLoop,
    )


class PlayerctlMprisSource:
    """Monitor every Playerctl MPRIS player and publish normalized events.

    ``start`` attaches to the session bus without taking over the thread.
    ``run`` additionally owns a GLib main loop and blocks until ``stop`` is
    called.  Tests can inject factories and exercise the complete signal flow
    without importing GI or opening D-Bus.
    """

    def __init__(
        self,
        on_event: EventCallback,
        *,
        ignore_playerctld: bool = True,
        manager_factory: Callable[[], Any] | None = None,
        player_factory: Callable[[Any], Any] | None = None,
        main_loop_factory: Callable[[], Any] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._on_event = on_event
        self._ignore_playerctld = ignore_playerctld
        self._manager_factory = manager_factory
        self._player_factory = player_factory
        self._main_loop_factory = main_loop_factory
        self._logger = logger or logging.getLogger(__name__)

        self._manager: Any | None = None
        self._manager_signal_ids: list[int] = []
        self._records: dict[PlayerIdentity, _ManagedPlayer] = {}
        self._identity_by_object_id: dict[int, PlayerIdentity] = {}
        self._generations: dict[PlayerIdentity, int] = {}
        self._main_loop: Any | None = None
        self._started = False
        self._initializing = False

    @property
    def started(self) -> bool:
        return self._started

    def start(self) -> None:
        """Attach to Playerctl and emit deterministic initial snapshots."""

        if self._started:
            return

        self._resolve_factories()
        assert self._manager_factory is not None

        try:
            manager = self._manager_factory()
        except Exception as exc:
            raise MprisSourceError(
                "Could not initialize Playerctl.PlayerManager. Confirm that a "
                "user session D-Bus is available and run this command as the "
                "desktop user."
            ) from exc

        self._manager = manager
        self._started = True
        try:
            self._manager_signal_ids = [
                manager.connect("name-appeared", self._on_name_appeared),
                manager.connect("player-appeared", self._on_player_appeared),
                manager.connect("player-vanished", self._on_player_vanished),
            ]

            # intent: INV-002 (Core/mpris-discord-presence) — initial discovery
            # order is normalized before the domain observes startup players.
            initial_names = sorted(
                list(manager.props.player_names), key=_player_name_sort_key
            )
            self._initializing = True
            try:
                for player_name in initial_names:
                    self._manage_name(player_name)
            finally:
                self._initializing = False
        except Exception:
            self.close()
            raise

    def run(self) -> None:
        """Start the source and run a GLib main loop until stopped."""

        self.start()
        if self._main_loop_factory is None:
            self._resolve_factories()
        assert self._main_loop_factory is not None
        self._main_loop = self._main_loop_factory()
        try:
            self._main_loop.run()
        finally:
            self.close()

    def stop(self) -> None:
        """Stop a running main loop and detach all Playerctl callbacks."""

        if self._main_loop is not None:
            self._main_loop.quit()
        self.close()

    def close(self) -> None:
        """Disconnect signal handlers without publishing synthetic events."""

        manager = self._manager
        self._started = False
        self._initializing = False

        for record in list(self._records.values()):
            _disconnect_all(record.player, record.signal_ids)
        self._records.clear()
        self._identity_by_object_id.clear()

        if manager is not None:
            _disconnect_all(manager, self._manager_signal_ids)
        self._manager_signal_ids.clear()
        self._manager = None
        self._main_loop = None

    def snapshots(self) -> tuple[SourceSnapshot, ...]:
        """Return the latest normalized state in deterministic identity order."""

        return tuple(
            self._records[identity].snapshot
            for identity in sorted(
                self._records, key=lambda value: (value.base_name, value.instance)
            )
        )

    def _resolve_factories(self) -> None:
        if (
            self._manager_factory is not None
            and self._player_factory is not None
            and self._main_loop_factory is not None
        ):
            return

        bindings = _load_playerctl_bindings()
        if self._manager_factory is None:
            self._manager_factory = bindings.manager_factory
        if self._player_factory is None:
            self._player_factory = bindings.player_factory
        if self._main_loop_factory is None:
            self._main_loop_factory = bindings.main_loop_factory

    def _on_name_appeared(self, _manager: Any, player_name: Any) -> None:
        self._manage_name(player_name)

    def _manage_name(self, player_name: Any) -> None:
        identity = _identity_from_player_name(player_name)
        if self._should_ignore(identity):
            return

        assert self._player_factory is not None
        assert self._manager is not None
        try:
            player = self._player_factory(player_name)
            self._manager.manage_player(player)
            # Playerctl emits player-appeared synchronously from manage_player.
            # The fallback also supports small test doubles and compatible GI
            # implementations that defer that signal.
            if id(player) not in self._identity_by_object_id:
                self._attach_player(player)
        except Exception as exc:
            self._logger.warning(
                "Could not manage MPRIS player %s: %s",
                identity.instance,
                type(exc).__name__,
            )

    def _on_player_appeared(self, _manager: Any, player: Any) -> None:
        self._attach_player(player)

    def _attach_player(self, player: Any) -> None:
        identity = _identity_from_player(player)
        if self._should_ignore(identity):
            return

        existing_identity = self._identity_by_object_id.get(id(player))
        if existing_identity == identity:
            return

        previous = self._records.get(identity)
        if previous is not None:
            _disconnect_all(previous.player, previous.signal_ids)
            self._identity_by_object_id.pop(id(previous.player), None)

        generation = self._generations.get(identity, 0) + 1
        self._generations[identity] = generation
        snapshot = _snapshot_player(player, identity, generation)
        record = _ManagedPlayer(
            player=player,
            generation=generation,
            snapshot=snapshot,
        )
        self._records[identity] = record
        self._identity_by_object_id[id(player)] = identity

        record.signal_ids.extend(
            [
                player.connect(
                    "playback-status",
                    self._on_playback_status,
                    identity,
                    generation,
                ),
                player.connect(
                    "metadata", self._on_metadata, identity, generation
                ),
                player.connect("seeked", self._on_seeked, identity, generation),
            ]
        )
        self._publish(
            SourceEvent(
                kind=SourceEventKind.APPEARED,
                snapshot=snapshot,
                initial=self._initializing,
            )
        )

    def _on_player_vanished(self, _manager: Any, player: Any) -> None:
        identity = self._identity_by_object_id.get(id(player))
        if identity is None:
            return
        record = self._records.get(identity)
        if record is None or record.player is not player:
            return

        _disconnect_all(player, record.signal_ids)
        self._records.pop(identity, None)
        self._identity_by_object_id.pop(id(player), None)
        self._publish(
            SourceEvent(kind=SourceEventKind.VANISHED, snapshot=record.snapshot)
        )

    def _on_playback_status(
        self,
        player: Any,
        status: Any,
        identity: PlayerIdentity,
        generation: int,
    ) -> None:
        self._update(
            player,
            identity,
            generation,
            SourceEventKind.PLAYBACK_STATUS,
            playback_status=status,
        )

    def _on_metadata(
        self,
        player: Any,
        metadata: Any,
        identity: PlayerIdentity,
        generation: int,
    ) -> None:
        self._update(
            player,
            identity,
            generation,
            SourceEventKind.METADATA,
            metadata=metadata,
        )

    def _on_seeked(
        self,
        player: Any,
        position: Any,
        identity: PlayerIdentity,
        generation: int,
    ) -> None:
        self._update(
            player,
            identity,
            generation,
            SourceEventKind.SEEKED,
            position_us=position,
        )

    def _update(
        self,
        player: Any,
        identity: PlayerIdentity,
        generation: int,
        kind: SourceEventKind,
        *,
        playback_status: Any | None = None,
        metadata: Any | None = None,
        position_us: Any | None = None,
    ) -> None:
        record = self._records.get(identity)
        # A vanished GI object can still have queued callbacks.  Generation and
        # object identity prevent those callbacks from mutating a reappeared
        # player that reused the same MPRIS instance name.
        if (
            record is None
            or record.generation != generation
            or record.player is not player
        ):
            return

        snapshot = _snapshot_player(
            player,
            identity,
            generation,
            playback_status=playback_status,
            metadata=metadata,
            position_us=position_us,
        )
        record.snapshot = snapshot
        self._publish(SourceEvent(kind=kind, snapshot=snapshot))

    def _should_ignore(self, identity: PlayerIdentity) -> bool:
        return self._ignore_playerctld and identity.base_name.casefold() == "playerctld"

    def _publish(self, event: SourceEvent) -> None:
        try:
            self._on_event(event)
        except Exception as exc:
            # Metadata is deliberately excluded from this log boundary.
            self._logger.error(
                "MPRIS event consumer failed for player %s (%s): %s",
                event.snapshot.identity.instance,
                event.kind.value,
                type(exc).__name__,
            )


def _snapshot_player(
    player: Any,
    identity: PlayerIdentity,
    generation: int,
    *,
    playback_status: Any | None = None,
    metadata: Any | None = None,
    position_us: Any | None = None,
) -> SourceSnapshot:
    props = getattr(player, "props", None)
    status_value = (
        playback_status
        if playback_status is not None
        else _safe_property(props, "playback_status")
    )
    metadata_value = (
        metadata if metadata is not None else _safe_property(props, "metadata")
    )
    position_value = (
        position_us
        if position_us is not None
        else _safe_position(player, props)
    )
    normalized_metadata = _normalize_metadata(metadata_value)

    return SourceSnapshot(
        identity=identity,
        generation=generation,
        playback_status=_normalize_playback_status(status_value),
        title=normalized_metadata["title"],
        artists=normalized_metadata["artists"],
        album=normalized_metadata["album"],
        url=normalized_metadata["url"],
        artwork_url=normalized_metadata["artwork_url"],
        length_us=normalized_metadata["length_us"],
        position_us=_nonnegative_int(position_value),
    )


def _normalize_metadata(value: Any) -> dict[str, Any]:
    unpacked = _unpack_variant(value)
    metadata: Mapping[Any, Any]
    if isinstance(unpacked, Mapping):
        metadata = unpacked
    else:
        metadata = {}

    artists_value = _unpack_variant(metadata.get("xesam:artist"))
    artists: tuple[str, ...] = ()
    if isinstance(artists_value, Sequence) and not isinstance(
        artists_value, (str, bytes, bytearray)
    ):
        artists = tuple(
            artist
            for item in artists_value
            if (artist := _nonempty_string(_unpack_variant(item))) is not None
        )

    return {
        "title": _nonempty_string(_unpack_variant(metadata.get("xesam:title"))),
        "artists": artists,
        "album": _nonempty_string(_unpack_variant(metadata.get("xesam:album"))),
        "url": _nonempty_string(_unpack_variant(metadata.get("xesam:url"))),
        "artwork_url": _nonempty_string(
            _unpack_variant(metadata.get("mpris:artUrl"))
        ),
        "length_us": _nonnegative_int(
            _unpack_variant(metadata.get("mpris:length"))
        ),
    }


def _normalize_playback_status(value: Any) -> PlaybackStatus:
    if isinstance(value, PlaybackStatus):
        return value

    nick = getattr(value, "value_nick", None)
    if isinstance(nick, str):
        value = nick

    if isinstance(value, str):
        normalized = value.strip().casefold()
        for status in (
            PlaybackStatus.PLAYING,
            PlaybackStatus.PAUSED,
            PlaybackStatus.STOPPED,
        ):
            if normalized == status.value:
                return status

    if isinstance(value, int) and not isinstance(value, bool):
        return {
            0: PlaybackStatus.PLAYING,
            1: PlaybackStatus.PAUSED,
            2: PlaybackStatus.STOPPED,
        }.get(value, PlaybackStatus.UNKNOWN)

    return PlaybackStatus.UNKNOWN


def _safe_position(player: Any, props: Any) -> Any:
    position = _safe_property(props, "position")
    if position is not None:
        return position
    getter = getattr(player, "get_position", None)
    if getter is None:
        return None
    try:
        return getter()
    except Exception:
        return None


def _safe_property(props: Any, name: str) -> Any:
    if props is None:
        return None
    try:
        return getattr(props, name)
    except Exception:
        return None


def _unpack_variant(value: Any) -> Any:
    unpack = getattr(value, "unpack", None)
    if unpack is None:
        return value
    try:
        return unpack()
    except Exception:
        return None


def _nonempty_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _identity_from_player_name(player_name: Any) -> PlayerIdentity:
    return _normalize_identity(
        getattr(player_name, "name", None), getattr(player_name, "instance", None)
    )


def _identity_from_player(player: Any) -> PlayerIdentity:
    props = getattr(player, "props", None)
    return _normalize_identity(
        _safe_property(props, "player_name"),
        _safe_property(props, "player_instance"),
    )


def _normalize_identity(base_name: Any, instance: Any) -> PlayerIdentity:
    base = _nonempty_string(base_name)
    full_instance = _nonempty_string(instance)
    if base is None and full_instance is None:
        return PlayerIdentity(base_name="unknown", instance="unknown")
    if base is None:
        assert full_instance is not None
        base = full_instance.split(".", 1)[0]
    if full_instance is None:
        full_instance = base
    return PlayerIdentity(base_name=base, instance=full_instance)


def _player_name_sort_key(player_name: Any) -> tuple[str, str]:
    identity = _identity_from_player_name(player_name)
    return (identity.base_name.casefold(), identity.instance.casefold())


def _disconnect_all(owner: Any, signal_ids: Sequence[int]) -> None:
    disconnect = getattr(owner, "disconnect", None)
    if disconnect is None:
        return
    for signal_id in list(signal_ids):
        try:
            disconnect(signal_id)
        except Exception:
            continue


__all__ = [
    "MprisSourceError",
    "PlaybackStatus",
    "PlayerIdentity",
    "PlayerctlMprisSource",
    "PlayerctlUnavailableError",
    "SourceEvent",
    "SourceEventKind",
    "SourceSnapshot",
]
