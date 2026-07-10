from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any, Protocol

from .activity import build_activity
from .arbiter import ActivePlayerArbiter, ArbiterDecision
from .config import AppConfig
from .models import PlaybackStatus, PlayerState, TrackMetadata


class Coordinator(Protocol):
    @property
    def last_error(self) -> BaseException | None: ...

    def set_desired(self, activity: Mapping[str, Any] | None) -> bool: ...

    def pump(self, now: float) -> bool: ...

    def shutdown(self) -> bool: ...


class PresenceController:
    """Connect normalized source events to arbitration and Discord publishing.

    The controller owns no event loop. Source callbacks and the periodic
    ``tick`` therefore remain on the GLib thread, while all decision logic can
    be tested without a D-Bus session or Discord process.
    """

    def __init__(
        self,
        config: AppConfig,
        coordinator: Coordinator,
        *,
        monotonic_clock: Any = time.monotonic,
        wall_clock: Any = time.time,
    ) -> None:
        self._config = config
        self._coordinator = coordinator
        self._monotonic_clock = monotonic_clock
        self._wall_clock = wall_clock
        self._arbiter = ActivePlayerArbiter(config, clock=monotonic_clock)
        self._pending_initial: dict[str, PlayerState] = {}
        self._initialized = False

    @property
    def active(self) -> PlayerState | None:
        return self._arbiter.active

    @property
    def last_transport_error(self) -> BaseException | None:
        return self._coordinator.last_error

    def on_source_event(self, event: object) -> None:
        raw_kind = getattr(event, "kind", "updated")
        kind = str(getattr(raw_kind, "value", raw_kind))
        snapshot = getattr(event, "snapshot", None)

        if snapshot is None:
            return
        if not self._config.sharing_enabled:
            return
        state = player_state_from_snapshot(snapshot)

        # intent: INV-002 (Core/mpris-discord-presence) — fold every event
        # observed during synchronous startup into one complete set before the
        # deterministic tie-break. This also covers a vanish race during
        # Playerctl's initial enumeration.
        if not self._initialized:
            if kind in {"vanished", "removed"}:
                self._pending_initial.pop(state.instance, None)
            else:
                self._pending_initial[state.instance] = state
            return

        if kind in {"vanished", "removed"}:
            decision = self._arbiter.remove(state.instance)
        else:
            decision = self._arbiter.upsert(state)
        self._apply(decision)

    def complete_initialization(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        states = self._pending_initial.values() if self._config.sharing_enabled else ()
        decision = self._arbiter.initialize(states)
        self._pending_initial.clear()
        if not self._config.sharing_enabled:
            decision = self._arbiter.disable()
        self._apply(decision)
        if not decision.publish and not decision.clear:
            # A fresh daemon with no active source must clear a presence left by
            # a previous process before entering its normal retry loop.
            self._coordinator.set_desired(None)

    def tick(self) -> bool:
        if not self._initialized:
            self.complete_initialization()
        self._apply(self._arbiter.poll())
        return self._coordinator.pump(self._monotonic_clock())

    def shutdown(self) -> bool:
        return self._coordinator.shutdown()

    def _apply(self, decision: ArbiterDecision) -> None:
        if decision.clear:
            self._coordinator.set_desired(None)
        elif decision.publish and decision.active is not None:
            activity = build_activity(
                decision.active,
                self._config,
                wall_clock=self._wall_clock,
            )
            self._coordinator.set_desired(activity.to_rpc_dict())


def player_state_from_snapshot(snapshot: object) -> PlayerState:
    identity = getattr(snapshot, "identity")
    raw_status = getattr(snapshot, "playback_status")
    status = _playback_status(raw_status)

    return PlayerState(
        instance=str(getattr(identity, "instance")),
        player_name=str(getattr(identity, "base_name")),
        generation=int(getattr(snapshot, "generation")),
        status=status,
        metadata=TrackMetadata(
            title=_optional_text(getattr(snapshot, "title", None)),
            artists=tuple(str(item) for item in getattr(snapshot, "artists", ()) if str(item)),
            album=_optional_text(getattr(snapshot, "album", None)),
            url=_optional_text(getattr(snapshot, "url", None)),
            art_url=_optional_text(getattr(snapshot, "artwork_url", None)),
            length_us=_optional_int(getattr(snapshot, "length_us", None)),
        ),
        position_us=_optional_int(getattr(snapshot, "position_us", None)),
    )


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _playback_status(value: object) -> PlaybackStatus:
    if isinstance(value, PlaybackStatus):
        return value
    raw = str(getattr(value, "value", value)).strip().casefold()
    return {
        "playing": PlaybackStatus.PLAYING,
        "paused": PlaybackStatus.PAUSED,
        "stopped": PlaybackStatus.STOPPED,
        "unknown": PlaybackStatus.STOPPED,
    }[raw]
