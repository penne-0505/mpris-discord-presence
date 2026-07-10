from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .config import AppConfig
from .models import PlaybackStatus, PlayerState


Clock = Callable[[], float]


@dataclass(frozen=True, slots=True)
class ArbiterDecision:
    active: PlayerState | None
    publish: bool = False
    clear: bool = False
    grace_pending: bool = False


@dataclass(slots=True)
class _Entry:
    state: PlayerState
    playing_sequence: int = 0


class ActivePlayerArbiter:
    def __init__(self, config: AppConfig, *, clock: Clock | None = None) -> None:
        self._config = config
        self._clock = clock or time.monotonic
        self._entries: dict[str, _Entry] = {}
        self._active_instance: str | None = None
        self._sequence = 0
        self._clear_deadline: float | None = None

    @property
    def active(self) -> PlayerState | None:
        entry = self._entries.get(self._active_instance or "")
        return entry.state if entry is not None else None

    @property
    def next_deadline(self) -> float | None:
        return self._clear_deadline

    def initialize(self, states: Iterable[PlayerState]) -> ArbiterDecision:
        self._entries.clear()
        self._active_instance = None
        self._clear_deadline = None
        for state in states:
            if not self._config.is_denied(state.instance, state.player_name):
                self._entries[state.instance] = _Entry(state=state)
        selected = self._startup_candidate()
        if selected is None:
            return ArbiterDecision(active=None)
        self._active_instance = selected.state.instance
        return ArbiterDecision(active=selected.state, publish=True)

    def upsert(self, state: PlayerState) -> ArbiterDecision:
        if self._config.is_denied(state.instance, state.player_name):
            return self.remove(state.instance)

        previous = self._entries.get(state.instance)
        transitioned_to_playing = (
            state.status is PlaybackStatus.PLAYING
            and (previous is None or previous.state.status is not PlaybackStatus.PLAYING)
        )
        sequence = previous.playing_sequence if previous is not None else 0
        if transitioned_to_playing:
            self._sequence += 1
            sequence = self._sequence
        self._entries[state.instance] = _Entry(state=state, playing_sequence=sequence)

        if transitioned_to_playing:
            self._active_instance = state.instance
            self._clear_deadline = None
            return ArbiterDecision(active=state, publish=True)

        if self._active_instance == state.instance:
            if state.status is PlaybackStatus.PLAYING:
                self._clear_deadline = None
                metadata_changed = previous is None or previous.state != state
                return ArbiterDecision(active=state, publish=metadata_changed)
            return self._fallback_or_grace()

        return ArbiterDecision(active=self.active)

    def remove(self, instance: str) -> ArbiterDecision:
        was_active = self._active_instance == instance
        self._entries.pop(instance, None)
        if not was_active:
            return ArbiterDecision(active=self.active)
        return self._fallback_or_grace()

    def poll(self) -> ArbiterDecision:
        if self._clear_deadline is None or self._clock() < self._clear_deadline:
            return ArbiterDecision(active=self.active, grace_pending=self._clear_deadline is not None)
        candidate = self._runtime_candidate()
        self._clear_deadline = None
        if candidate is not None:
            self._active_instance = candidate.state.instance
            return ArbiterDecision(active=candidate.state, publish=True)
        self._active_instance = None
        return ArbiterDecision(active=None, clear=True)

    def disable(self) -> ArbiterDecision:
        self._active_instance = None
        self._clear_deadline = None
        return ArbiterDecision(active=None, clear=True)

    def _fallback_or_grace(self) -> ArbiterDecision:
        candidate = self._runtime_candidate(exclude=self._active_instance)
        if candidate is not None:
            self._active_instance = candidate.state.instance
            self._clear_deadline = None
            return ArbiterDecision(active=candidate.state, publish=True)
        if self._config.clear_grace_seconds == 0:
            self._active_instance = None
            self._clear_deadline = None
            return ArbiterDecision(active=None, clear=True)
        if self._clear_deadline is None:
            self._clear_deadline = self._clock() + self._config.clear_grace_seconds
        return ArbiterDecision(active=self.active, grace_pending=True)

    def _startup_candidate(self) -> _Entry | None:
        candidates = [entry for entry in self._entries.values() if entry.state.status is PlaybackStatus.PLAYING]
        if not candidates:
            return None
        return min(candidates, key=self._stable_priority_key)

    def _runtime_candidate(self, *, exclude: str | None = None) -> _Entry | None:
        candidates = [
            entry
            for entry in self._entries.values()
            if entry.state.status is PlaybackStatus.PLAYING and entry.state.instance != exclude
        ]
        if not candidates:
            return None
        highest_sequence = max(entry.playing_sequence for entry in candidates)
        recent = [entry for entry in candidates if entry.playing_sequence == highest_sequence]
        return min(recent, key=self._stable_priority_key)

    def _stable_priority_key(self, entry: _Entry) -> tuple[int, str]:
        state = entry.state
        return (self._config.priority_rank(state.instance, state.player_name), state.instance)
