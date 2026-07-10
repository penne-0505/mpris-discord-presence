from __future__ import annotations

import ipaddress
import time
from collections.abc import Callable
from urllib.parse import urlparse

from .config import AppConfig
from .models import ActivityModel, PlayerState, StatusDisplayType


WallClock = Callable[[], float]
MAX_FIELD_LENGTH = 128
MAX_BUTTON_URL_LENGTH = 512


def build_activity(
    state: PlayerState,
    config: AppConfig,
    *,
    wall_clock: WallClock | None = None,
) -> ActivityModel:
    now = int((wall_clock or time.time)())
    metadata = state.metadata
    details = truncate_text(metadata.title or state.player_name)
    artist_text = ", ".join(metadata.artists)
    secondary_label = artist_text or metadata.album or state.player_name
    secondary = truncate_text(f"{secondary_label} を再生中")

    start_timestamp: int | None = None
    end_timestamp: int | None = None
    if state.position_us is not None and state.position_us >= 0:
        position_us = state.position_us
        if metadata.length_us is not None and metadata.length_us > 0:
            position_us = min(position_us, metadata.length_us)
        start_timestamp = now - int(position_us / 1_000_000)
        if metadata.length_us is not None and metadata.length_us > 0:
            end_timestamp = start_timestamp + int(metadata.length_us / 1_000_000)

    art_url = public_https_url(metadata.art_url) or config.fallback_art_asset
    track_url = public_https_url(metadata.url, max_length=MAX_BUTTON_URL_LENGTH)
    return ActivityModel(
        activity_type=config.activity_type_for(state.instance, state.player_name),
        details=details,
        state=secondary,
        # intent: INV-008 (Core/mpris-discord-presence) — select the formatted
        # artist state for compact status instead of the Application name.
        status_display_type=StatusDisplayType.STATE,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        large_image=art_url,
        large_text=(
            truncate_text(metadata.album or metadata.title or state.player_name)
            if art_url
            else None
        ),
        details_url=track_url,
        button_label="Open media" if track_url else None,
        button_url=track_url,
    )


def truncate_text(value: str, limit: int = MAX_FIELD_LENGTH) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    if limit <= 1:
        return normalized[:limit]
    return normalized[: limit - 1] + "…"


def public_https_url(value: str | None, *, max_length: int | None = None) -> str | None:
    if not value:
        return None
    if max_length is not None and len(value) > max_length:
        return None
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".local"):
        return None
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return value
    return value if address.is_global else None
