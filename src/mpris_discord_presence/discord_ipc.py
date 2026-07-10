"""Minimal Discord IPC v1 transport and reconnect coordination.

The module intentionally implements only unauthenticated Rich Presence.  A
Discord Application ID is public metadata; user tokens, OAuth credentials, and
the Social SDK are outside this transport's boundary.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import IntEnum
import json
import os
from pathlib import Path
import select
import socket
import stat
import struct
from types import TracebackType
from typing import Any, Protocol, Self
import uuid


IPC_VERSION = 1
IPC_SOCKET_COUNT = 10
MAX_FRAME_SIZE = 1024 * 1024
MINIMUM_PUBLISH_INTERVAL = 4.0
_HEADER = struct.Struct("<II")
_PEER_CREDENTIALS = struct.Struct("3i")
_NO_STATE = object()


class Opcode(IntEnum):
    HANDSHAKE = 0
    FRAME = 1
    CLOSE = 2
    PING = 3
    PONG = 4


class DiscordIPCError(RuntimeError):
    """Base error for recoverable Discord IPC failures."""


class DiscordConnectionError(DiscordIPCError):
    """No eligible Discord IPC endpoint could be connected."""


class DiscordClosed(DiscordIPCError):
    """Discord closed the IPC stream."""


class DiscordProtocolError(DiscordIPCError):
    """Discord sent a malformed or unexpected IPC frame."""


class DiscordRPCError(DiscordIPCError):
    """Discord returned an RPC ERROR event."""

    def __init__(self, message: str, *, code: int | str | None = None) -> None:
        super().__init__(message)
        self.code = code


class FrameTooLarge(DiscordProtocolError):
    """An IPC payload exceeded the configured allocation limit."""


@dataclass(frozen=True, slots=True)
class IPCFrame:
    opcode: Opcode
    payload: bytes


def encode_frame(
    opcode: Opcode,
    payload: Mapping[str, Any] | bytes,
    *,
    max_frame_size: int = MAX_FRAME_SIZE,
) -> bytes:
    """Encode one little-endian Discord IPC frame."""

    if isinstance(payload, bytes):
        encoded = payload
    else:
        try:
            encoded = json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise DiscordProtocolError("IPC payload is not JSON serializable") from exc
    if len(encoded) > max_frame_size:
        raise FrameTooLarge(
            f"IPC payload is {len(encoded)} bytes; limit is {max_frame_size}"
        )
    return _HEADER.pack(int(opcode), len(encoded)) + encoded


def _read_exact(stream: socket.socket, length: int) -> bytes:
    chunks: list[bytes] = []
    remaining = length
    while remaining:
        try:
            chunk = stream.recv(remaining)
        except (OSError, TimeoutError) as exc:
            raise DiscordClosed("Discord IPC read failed") from exc
        if not chunk:
            raise DiscordClosed("Discord IPC stream closed during a frame")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_frame(
    stream: socket.socket,
    *,
    max_frame_size: int = MAX_FRAME_SIZE,
) -> IPCFrame:
    """Read exactly one frame, tolerating partial socket reads."""

    header = _read_exact(stream, _HEADER.size)
    raw_opcode, payload_length = _HEADER.unpack(header)
    if payload_length > max_frame_size:
        raise FrameTooLarge(
            f"incoming IPC payload is {payload_length} bytes; limit is {max_frame_size}"
        )
    try:
        opcode = Opcode(raw_opcode)
    except ValueError as exc:
        raise DiscordProtocolError(f"unexpected IPC opcode {raw_opcode}") from exc
    return IPCFrame(opcode=opcode, payload=_read_exact(stream, payload_length))


def write_frame(
    stream: socket.socket,
    opcode: Opcode,
    payload: Mapping[str, Any] | bytes,
    *,
    max_frame_size: int = MAX_FRAME_SIZE,
) -> None:
    try:
        stream.sendall(encode_frame(opcode, payload, max_frame_size=max_frame_size))
    except (OSError, TimeoutError) as exc:
        raise DiscordClosed("Discord IPC write failed") from exc


def decode_json_payload(frame: IPCFrame) -> dict[str, Any]:
    try:
        decoded = json.loads(frame.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiscordProtocolError("IPC frame does not contain valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise DiscordProtocolError("IPC JSON payload must be an object")
    return decoded


def ipc_path_candidates(
    env: Mapping[str, str] | None = None,
    *,
    socket_count: int = IPC_SOCKET_COUNT,
) -> tuple[Path, ...]:
    """Return official Linux/macOS IPC path candidates in prefix order."""

    environment = os.environ if env is None else env
    prefixes: list[str] = []
    for variable in ("XDG_RUNTIME_DIR", "TMPDIR", "TMP", "TEMP"):
        value = environment.get(variable)
        if value and value not in prefixes:
            prefixes.append(value)
    if "/tmp" not in prefixes:
        prefixes.append("/tmp")
    return tuple(
        Path(prefix) / f"discord-ipc-{index}"
        for prefix in prefixes
        for index in range(socket_count)
    )


def discover_ipc_sockets(
    env: Mapping[str, str] | None = None,
    *,
    candidates: Iterable[Path] | None = None,
    expected_uid: int | None = None,
) -> tuple[Path, ...]:
    """Keep only Unix sockets owned by the current user.

    Ownership is checked again against ``SO_PEERCRED`` after connecting, so a
    path replacement between discovery and connection cannot cross the UID
    boundary.
    """

    uid = os.getuid() if expected_uid is None else expected_uid
    eligible: list[Path] = []
    for path in ipc_path_candidates(env) if candidates is None else candidates:
        path = Path(path)
        try:
            details = path.stat()
        except (FileNotFoundError, NotADirectoryError, PermissionError, OSError):
            continue
        if stat.S_ISSOCK(details.st_mode) and details.st_uid == uid:
            eligible.append(path)
    return tuple(eligible)


def _peer_uid(stream: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise DiscordConnectionError("SO_PEERCRED is unavailable on this platform")
    try:
        raw = stream.getsockopt(
            socket.SOL_SOCKET,
            socket.SO_PEERCRED,
            _PEER_CREDENTIALS.size,
        )
    except OSError as exc:
        raise DiscordConnectionError("could not validate Discord IPC peer UID") from exc
    _pid, uid, _gid = _PEER_CREDENTIALS.unpack(raw)
    return uid


class DiscordIPCConnection:
    """Framed I/O over an already connected Unix stream socket."""

    def __init__(
        self,
        stream: socket.socket,
        *,
        max_frame_size: int = MAX_FRAME_SIZE,
    ) -> None:
        self._stream = stream
        self._max_frame_size = max_frame_size

    @property
    def stream(self) -> socket.socket:
        return self._stream

    def send(self, opcode: Opcode, payload: Mapping[str, Any] | bytes) -> None:
        write_frame(
            self._stream,
            opcode,
            payload,
            max_frame_size=self._max_frame_size,
        )

    def receive(self) -> IPCFrame:
        return read_frame(self._stream, max_frame_size=self._max_frame_size)

    def readable(self) -> bool:
        try:
            ready, _, _ = select.select([self._stream], [], [], 0)
        except (OSError, ValueError) as exc:
            raise DiscordClosed("could not poll Discord IPC stream") from exc
        return bool(ready)

    def close(self) -> None:
        try:
            self._stream.close()
        except OSError:
            pass


_DISALLOWED_ACTIVITY_KEYS = frozenset(
    {
        "access_token",
        "authorization",
        "client_token",
        "client_secret",
        "oauth_token",
        "refresh_token",
        "rpc_token",
        "secret",
        "secrets",
        "token",
        "user_token",
    }
)


def _validate_activity_boundary(value: object) -> None:
    """Reject credential/invite-secret fields without inspecting metadata values."""

    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key).casefold()
            if key in _DISALLOWED_ACTIVITY_KEYS:
                raise ValueError(f"activity field {raw_key!r} is outside the credential boundary")
            _validate_activity_boundary(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _validate_activity_boundary(child)


class DiscordIPCClient:
    """Synchronous unauthenticated Rich Presence client.

    The constructor deliberately accepts only the public Application ID; it
    has no OAuth, user-token, or SDK authentication surface.
    """

    def __init__(
        self,
        application_id: str,
        *,
        pid: int | None = None,
        env: Mapping[str, str] | None = None,
        socket_paths: Iterable[Path] | None = None,
        socket_timeout: float = 2.0,
        max_frame_size: int = MAX_FRAME_SIZE,
        peer_uid_getter: Callable[[socket.socket], int] = _peer_uid,
    ) -> None:
        if not application_id or not application_id.isascii() or not application_id.isdecimal():
            raise ValueError("application_id must be a decimal Discord Application ID")
        if socket_timeout <= 0:
            raise ValueError("socket_timeout must be positive")
        self.application_id = application_id
        self.pid = os.getpid() if pid is None else pid
        self._env = dict(env) if env is not None else None
        self._socket_paths = tuple(socket_paths) if socket_paths is not None else None
        self._socket_timeout = socket_timeout
        self._max_frame_size = max_frame_size
        self._peer_uid_getter = peer_uid_getter
        self._connection: DiscordIPCConnection | None = None

    @property
    def connected(self) -> bool:
        return self._connection is not None

    def connect(self) -> None:
        if self._connection is not None:
            return
        paths = discover_ipc_sockets(
            self._env,
            candidates=self._socket_paths,
        )
        if not paths:
            raise DiscordConnectionError("no same-UID Discord IPC socket found")

        failures: list[str] = []
        for path in paths:
            stream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            stream.settimeout(self._socket_timeout)
            connection = DiscordIPCConnection(
                stream,
                max_frame_size=self._max_frame_size,
            )
            try:
                stream.connect(str(path))
                peer_uid = self._peer_uid_getter(stream)
                if peer_uid != os.getuid():
                    raise DiscordConnectionError(
                        f"Discord IPC peer UID {peer_uid} does not match current UID"
                    )
                connection.send(
                    Opcode.HANDSHAKE,
                    {"v": IPC_VERSION, "client_id": self.application_id},
                )
                self._wait_for_ready(connection)
            except (DiscordIPCError, OSError, TimeoutError) as exc:
                failures.append(f"{path}: {exc}")
                connection.close()
                continue
            self._connection = connection
            return
        raise DiscordConnectionError(
            "could not establish Discord IPC connection: " + "; ".join(failures)
        )

    def set_activity(self, activity: Mapping[str, Any]) -> None:
        copied = deepcopy(dict(activity))
        _validate_activity_boundary(copied)
        self._set_activity(copied)

    def clear(self) -> None:
        self._set_activity(None)

    def _set_activity(self, activity: Mapping[str, Any] | None) -> None:
        connection = self._require_connection()
        nonce = uuid.uuid4().hex
        connection.send(
            Opcode.FRAME,
            {
                "cmd": "SET_ACTIVITY",
                "args": {"pid": self.pid, "activity": activity},
                "nonce": nonce,
            },
        )
        self._wait_for_response(connection, nonce)

    def poll(self) -> bool:
        """Process pending control frames without blocking.

        Returns ``True`` if at least one frame was handled.  A CLOSE, ERROR, or
        malformed frame raises a recoverable ``DiscordIPCError`` so a caller
        can schedule reconnection.
        """

        connection = self._require_connection()
        handled = False
        while connection.readable():
            handled = True
            payload = self._handle_control_frame(connection, connection.receive())
            if payload is not None and payload.get("evt") == "ERROR":
                self._raise_rpc_error(payload)
        return handled

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _require_connection(self) -> DiscordIPCConnection:
        if self._connection is None:
            raise DiscordConnectionError("Discord IPC client is not connected")
        return self._connection

    def _wait_for_ready(self, connection: DiscordIPCConnection) -> None:
        for _ in range(64):
            payload = self._handle_control_frame(connection, connection.receive())
            if payload is None:
                continue
            if payload.get("evt") == "ERROR":
                self._raise_rpc_error(payload)
            if payload.get("evt") == "READY":
                return
        raise DiscordProtocolError("READY was not received within 64 IPC frames")

    def _wait_for_response(
        self,
        connection: DiscordIPCConnection,
        nonce: str,
    ) -> dict[str, Any]:
        for _ in range(64):
            payload = self._handle_control_frame(connection, connection.receive())
            if payload is None:
                continue
            if payload.get("evt") == "ERROR":
                self._raise_rpc_error(payload)
            if payload.get("nonce") == nonce:
                return payload
        raise DiscordProtocolError("RPC response was not received within 64 IPC frames")

    @staticmethod
    def _handle_control_frame(
        connection: DiscordIPCConnection,
        frame: IPCFrame,
    ) -> dict[str, Any] | None:
        if frame.opcode is Opcode.PING:
            connection.send(Opcode.PONG, frame.payload)
            return None
        if frame.opcode is Opcode.PONG:
            return None
        if frame.opcode is Opcode.CLOSE:
            detail = _best_effort_message(frame.payload, "Discord closed the IPC session")
            raise DiscordClosed(detail)
        if frame.opcode is not Opcode.FRAME:
            raise DiscordProtocolError(
                f"unexpected IPC opcode {int(frame.opcode)} after handshake"
            )
        return decode_json_payload(frame)

    @staticmethod
    def _raise_rpc_error(payload: Mapping[str, Any]) -> None:
        data = payload.get("data")
        if not isinstance(data, Mapping):
            raise DiscordRPCError("Discord returned an RPC error")
        message = data.get("message")
        code = data.get("code")
        raise DiscordRPCError(
            str(message) if message else "Discord returned an RPC error",
            code=code if isinstance(code, (int, str)) else None,
        )


def _best_effort_message(payload: bytes, fallback: str) -> str:
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return fallback
    if isinstance(decoded, Mapping) and decoded.get("message"):
        return str(decoded["message"])
    return fallback


class PresenceTransport(Protocol):
    def connect(self) -> None: ...

    def set_activity(self, activity: Mapping[str, Any]) -> None: ...

    def clear(self) -> None: ...

    def poll(self) -> bool: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class BackoffPolicy:
    initial_delay: float = 1.0
    multiplier: float = 2.0
    maximum_delay: float = 30.0

    def __post_init__(self) -> None:
        if self.initial_delay <= 0:
            raise ValueError("initial_delay must be positive")
        if self.multiplier < 1:
            raise ValueError("multiplier must be at least 1")
        if self.maximum_delay < self.initial_delay:
            raise ValueError("maximum_delay must not be less than initial_delay")


class ReconnectCoordinator:
    """Drive latest-only publishing without sleeping or owning an event loop.

    Callers provide monotonic ``now`` values to :meth:`pump`.  This keeps retry
    behavior deterministic and lets the daemon integrate with GLib without a
    second scheduler.
    """

    def __init__(
        self,
        client_factory: Callable[[], PresenceTransport],
        *,
        backoff: BackoffPolicy = BackoffPolicy(),
        minimum_publish_interval: float = MINIMUM_PUBLISH_INTERVAL,
    ) -> None:
        if minimum_publish_interval < 0:
            raise ValueError("minimum_publish_interval must be non-negative")
        self._client_factory = client_factory
        self._backoff = backoff
        self._minimum_publish_interval = minimum_publish_interval
        self._client: PresenceTransport | None = None
        self._desired: Mapping[str, Any] | None | object = _NO_STATE
        self._desired_signature: str | object = _NO_STATE
        self._sent_signature: str | object = _NO_STATE
        self._next_attempt_at = 0.0
        self._next_delay = backoff.initial_delay
        self._next_publish_at = 0.0
        self._last_error: BaseException | None = None

    @property
    def connected(self) -> bool:
        return self._client is not None

    @property
    def next_attempt_at(self) -> float:
        return self._next_attempt_at

    @property
    def last_error(self) -> BaseException | None:
        return self._last_error

    @property
    def desired(self) -> Mapping[str, Any] | None:
        if self._desired is _NO_STATE:
            return None
        return deepcopy(self._desired)

    def set_desired(self, activity: Mapping[str, Any] | None) -> bool:
        copied = None if activity is None else deepcopy(dict(activity))
        if copied is not None:
            _validate_activity_boundary(copied)
        signature = _activity_signature(copied)
        if signature == self._desired_signature:
            return False
        self._desired = copied
        self._desired_signature = signature
        return True

    def pump(self, now: float) -> bool:
        """Poll, reconnect when due, and publish at most one desired state."""

        if self._desired is _NO_STATE:
            return False
        if self._client is not None:
            try:
                self._client.poll()
            except (DiscordIPCError, OSError, TimeoutError) as exc:
                self._drop_and_schedule(now, exc)

        if self._client is None:
            if now < self._next_attempt_at:
                return False
            candidate = self._client_factory()
            try:
                candidate.connect()
            except (DiscordIPCError, OSError, TimeoutError) as exc:
                try:
                    candidate.close()
                finally:
                    self._schedule_retry(now, exc)
                return False
            self._client = candidate
            self._sent_signature = _NO_STATE
            # A replacement Discord connection needs the latest state
            # immediately; any limiter state belonged to the old session.
            self._next_publish_at = now

        if self._sent_signature == self._desired_signature:
            return False
        # Discord documents at most five game-status updates per 20 seconds.
        # intent: INV-006 (Core/mpris-discord-presence) — retain the newest
        # desired activity while connected and flush at a conservative 4s
        # cadence. A privacy clear remains immediate.
        if self._desired is not None and now < self._next_publish_at:
            return False
        assert self._client is not None
        try:
            if self._desired is None:
                self._client.clear()
            else:
                self._client.set_activity(self._desired)
        except (DiscordIPCError, OSError, TimeoutError) as exc:
            self._drop_and_schedule(now, exc)
            return False

        self._sent_signature = self._desired_signature
        self._last_error = None
        self._next_attempt_at = now
        self._next_delay = self._backoff.initial_delay
        self._next_publish_at = now + self._minimum_publish_interval
        return True

    def shutdown(self) -> bool:
        """Best-effort immediate clear on an existing connection, then close."""

        cleared = False
        if self._client is not None:
            try:
                if self._sent_signature != _activity_signature(None):
                    self._client.clear()
                    cleared = True
            except (DiscordIPCError, OSError, TimeoutError) as exc:
                self._last_error = exc
            finally:
                self._client.close()
                self._client = None
        self._desired = None
        self._desired_signature = _activity_signature(None)
        self._sent_signature = _NO_STATE
        return cleared

    def _drop_and_schedule(self, now: float, error: BaseException) -> None:
        assert self._client is not None
        try:
            self._client.close()
        finally:
            self._client = None
            self._sent_signature = _NO_STATE
        self._schedule_retry(now, error)

    def _schedule_retry(self, now: float, error: BaseException) -> None:
        self._last_error = error
        self._next_attempt_at = now + self._next_delay
        self._next_delay = min(
            self._backoff.maximum_delay,
            self._next_delay * self._backoff.multiplier,
        )


def _activity_signature(activity: Mapping[str, Any] | None) -> str:
    try:
        return json.dumps(
            activity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("activity must be JSON serializable") from exc
