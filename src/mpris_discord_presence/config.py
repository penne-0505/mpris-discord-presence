from __future__ import annotations

import fnmatch
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import ActivityType


class ConfigError(ValueError):
    pass


_ALLOWED_KEYS = frozenset(
    {
        "application_id",
        "sharing_enabled",
        "deny_players",
        "startup_priority",
        "default_activity_type",
        "activity_types",
        "clear_grace_seconds",
        "reconnect_initial_seconds",
        "reconnect_max_seconds",
        "fallback_art_asset",
    }
)


@dataclass(frozen=True, slots=True)
class ActivityTypeRule:
    pattern: str
    activity_type: ActivityType


@dataclass(frozen=True, slots=True)
class AppConfig:
    application_id: str | None = None
    sharing_enabled: bool = True
    deny_players: tuple[str, ...] = ("playerctld",)
    startup_priority: tuple[str, ...] = ()
    default_activity_type: ActivityType = ActivityType.LISTENING
    activity_type_rules: tuple[ActivityTypeRule, ...] = ()
    clear_grace_seconds: float = 1.5
    reconnect_initial_seconds: float = 0.5
    reconnect_max_seconds: float = 30.0
    fallback_art_asset: str | None = None
    config_path: Path | None = field(default=None, compare=False)

    def is_denied(self, instance: str, player_name: str) -> bool:
        return any(
            fnmatch.fnmatchcase(instance, pattern) or fnmatch.fnmatchcase(player_name, pattern)
            for pattern in self.deny_players
        )

    def priority_rank(self, instance: str, player_name: str) -> int:
        for index, pattern in enumerate(self.startup_priority):
            if fnmatch.fnmatchcase(instance, pattern) or fnmatch.fnmatchcase(player_name, pattern):
                return index
        return len(self.startup_priority)

    def activity_type_for(self, instance: str, player_name: str) -> ActivityType:
        # intent: INV-007 (Core/mpris-discord-presence) — why-not: classify only by explicit player rules, never by private title or URL contents.
        for rule in self.activity_type_rules:
            if fnmatch.fnmatchcase(instance, rule.pattern) or fnmatch.fnmatchcase(player_name, rule.pattern):
                return rule.activity_type
        return self.default_activity_type


def default_config_path() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "mpris-discord-presence" / "config.toml"


def load_config(path: str | Path | None = None) -> AppConfig:
    resolved = Path(path).expanduser() if path is not None else default_config_path()
    if not resolved.exists():
        return parse_config({}, config_path=resolved)
    try:
        with resolved.open("rb") as handle:
            raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as ex:
        raise ConfigError(f"failed to read {resolved}: {ex}") from ex
    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a table")
    return parse_config(raw, config_path=resolved)


def parse_config(raw: dict[str, Any], *, config_path: Path | None = None) -> AppConfig:
    # intent: INV-003 (Core/mpris-discord-presence) — reject privacy-key typos instead of silently falling back to share-all defaults.
    unknown_keys = sorted(set(raw) - _ALLOWED_KEYS)
    if unknown_keys:
        raise ConfigError(f"unknown configuration key(s): {', '.join(unknown_keys)}")
    application_id = raw.get("application_id") or _application_id_from_env()
    if application_id is not None:
        application_id = str(application_id).strip()
        if not application_id.isascii() or not application_id.isdecimal():
            raise ConfigError("application_id must contain only decimal digits")

    sharing_enabled = _boolean(raw, "sharing_enabled", True)
    deny_players = _string_tuple(raw, "deny_players", ("playerctld",))
    startup_priority = _string_tuple(raw, "startup_priority", ())
    default_type = _activity_type(raw.get("default_activity_type", "listening"), "default_activity_type")
    rules_raw = raw.get("activity_types", {})
    if not isinstance(rules_raw, dict):
        raise ConfigError("activity_types must be a table")
    rules = tuple(
        ActivityTypeRule(str(pattern), _activity_type(value, f"activity_types.{pattern}"))
        for pattern, value in rules_raw.items()
    )
    clear_grace = _positive_float(raw, "clear_grace_seconds", 1.5, allow_zero=True)
    reconnect_initial = _positive_float(raw, "reconnect_initial_seconds", 0.5)
    reconnect_max = _positive_float(raw, "reconnect_max_seconds", 30.0)
    if reconnect_max < reconnect_initial:
        raise ConfigError("reconnect_max_seconds must be at least reconnect_initial_seconds")
    fallback = raw.get("fallback_art_asset")
    if fallback is not None:
        fallback = str(fallback).strip() or None

    return AppConfig(
        application_id=application_id,
        sharing_enabled=sharing_enabled,
        deny_players=deny_players,
        startup_priority=startup_priority,
        default_activity_type=default_type,
        activity_type_rules=rules,
        clear_grace_seconds=clear_grace,
        reconnect_initial_seconds=reconnect_initial,
        reconnect_max_seconds=reconnect_max,
        fallback_art_asset=fallback,
        config_path=config_path,
    )


def _application_id_from_env() -> str | None:
    value = os.environ.get("MPRIS_DISCORD_APPLICATION_ID", "").strip()
    return value or None


def _boolean(raw: dict[str, Any], key: str, default: bool) -> bool:
    value = raw.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"{key} must be a boolean")
    return value


def _string_tuple(raw: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = raw.get(key, list(default))
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ConfigError(f"{key} must be an array of non-empty strings")
    return tuple(value)


def _positive_float(
    raw: dict[str, Any],
    key: str,
    default: float,
    *,
    allow_zero: bool = False,
) -> float:
    value = raw.get(key, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigError(f"{key} must be a number")
    number = float(value)
    if number < 0 or (number == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ConfigError(f"{key} must be {qualifier}")
    return number


def _activity_type(value: Any, key: str) -> ActivityType:
    try:
        return ActivityType(str(value).lower())
    except ValueError as ex:
        allowed = ", ".join(item.value for item in ActivityType)
        raise ConfigError(f"{key} must be one of: {allowed}") from ex
