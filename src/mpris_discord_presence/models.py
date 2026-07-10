from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum


class PlaybackStatus(StrEnum):
    PLAYING = "Playing"
    PAUSED = "Paused"
    STOPPED = "Stopped"


class ActivityType(StrEnum):
    PLAYING = "playing"
    LISTENING = "listening"
    WATCHING = "watching"
    COMPETING = "competing"

    @property
    def discord_value(self) -> int:
        return {
            ActivityType.PLAYING: 0,
            ActivityType.LISTENING: 2,
            ActivityType.WATCHING: 3,
            ActivityType.COMPETING: 5,
        }[self]


class StatusDisplayType(IntEnum):
    NAME = 0
    STATE = 1
    DETAILS = 2


@dataclass(frozen=True, slots=True)
class TrackMetadata:
    track_id: str | None = None
    title: str | None = None
    artists: tuple[str, ...] = ()
    album: str | None = None
    url: str | None = None
    art_url: str | None = None
    length_us: int | None = None


@dataclass(frozen=True, slots=True)
class PlayerState:
    instance: str
    player_name: str
    generation: int
    status: PlaybackStatus
    metadata: TrackMetadata
    position_us: int | None = None


@dataclass(frozen=True, slots=True)
class ActivityModel:
    activity_type: ActivityType
    details: str
    state: str | None = None
    status_display_type: StatusDisplayType | None = None
    start_timestamp: int | None = None
    end_timestamp: int | None = None
    large_image: str | None = None
    large_text: str | None = None
    details_url: str | None = None
    button_label: str | None = None
    button_url: str | None = None

    def to_rpc_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.activity_type.discord_value,
            "details": self.details,
        }
        if self.state:
            payload["state"] = self.state
        if self.status_display_type is not None:
            payload["status_display_type"] = int(self.status_display_type)
        if self.start_timestamp is not None or self.end_timestamp is not None:
            timestamps: dict[str, int] = {}
            if self.start_timestamp is not None:
                timestamps["start"] = self.start_timestamp
            if self.end_timestamp is not None:
                timestamps["end"] = self.end_timestamp
            payload["timestamps"] = timestamps
        if self.large_image or self.large_text:
            assets: dict[str, str] = {}
            if self.large_image:
                assets["large_image"] = self.large_image
            if self.large_text:
                assets["large_text"] = self.large_text
            payload["assets"] = assets
        if self.details_url:
            payload["details_url"] = self.details_url
        if self.button_label and self.button_url:
            payload["buttons"] = [{"label": self.button_label, "url": self.button_url}]
        return payload
