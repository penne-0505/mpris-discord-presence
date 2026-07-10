from __future__ import annotations

from collections.abc import Mapping
import inspect
import json
import os
from pathlib import Path
import socket
import struct
import tempfile
import threading
import unittest

from mpris_discord_presence.discord_ipc import (
    BackoffPolicy,
    DiscordClosed,
    DiscordConnectionError,
    DiscordIPCClient,
    DiscordIPCError,
    DiscordProtocolError,
    DiscordRPCError,
    FrameTooLarge,
    IPCFrame,
    Opcode,
    ReconnectCoordinator,
    decode_json_payload,
    discover_ipc_sockets,
    encode_frame,
    ipc_path_candidates,
    read_frame,
    write_frame,
)


class ChunkedReader:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    def recv(self, length: int) -> bytes:
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if len(chunk) > length:
            self.chunks.insert(0, chunk[length:])
            return chunk[:length]
        return chunk


class FrameTests(unittest.TestCase):
    def test_ac004_partial_reads_are_reassembled(self) -> None:
        encoded = encode_frame(Opcode.FRAME, {"evt": "READY", "data": {}})
        reader = ChunkedReader([encoded[:2], encoded[2:7], encoded[7:9], encoded[9:]])

        frame = read_frame(reader)  # type: ignore[arg-type]

        self.assertEqual(frame.opcode, Opcode.FRAME)
        self.assertEqual(decode_json_payload(frame)["evt"], "READY")

    def test_ac004_truncated_frame_fails_closed(self) -> None:
        encoded = encode_frame(Opcode.FRAME, {"value": "truncated"})
        reader = ChunkedReader([encoded[:-2], b""])

        with self.assertRaises(DiscordClosed):
            read_frame(reader)  # type: ignore[arg-type]

    def test_ac004_incoming_length_is_bounded_before_payload_read(self) -> None:
        reader = ChunkedReader([struct.pack("<II", int(Opcode.FRAME), 4097)])

        with self.assertRaises(FrameTooLarge):
            read_frame(reader, max_frame_size=4096)  # type: ignore[arg-type]

    def test_ac004_outgoing_length_is_bounded(self) -> None:
        with self.assertRaises(FrameTooLarge):
            encode_frame(Opcode.FRAME, b"12345", max_frame_size=4)

    def test_ac004_unknown_opcode_fails_closed(self) -> None:
        reader = ChunkedReader([struct.pack("<II", 99, 2), b"{}"])

        with self.assertRaises(DiscordProtocolError):
            read_frame(reader)  # type: ignore[arg-type]


class SocketDiscoveryTests(unittest.TestCase):
    def test_ac004_candidate_order_matches_discord_prefix_order(self) -> None:
        candidates = ipc_path_candidates(
            {
                "XDG_RUNTIME_DIR": "/run/user/1000",
                "TMPDIR": "/custom/tmp",
                "TMP": "/custom/tmp",
                "TEMP": "/last/tmp",
            },
            socket_count=2,
        )

        self.assertEqual(
            candidates,
            (
                Path("/run/user/1000/discord-ipc-0"),
                Path("/run/user/1000/discord-ipc-1"),
                Path("/custom/tmp/discord-ipc-0"),
                Path("/custom/tmp/discord-ipc-1"),
                Path("/last/tmp/discord-ipc-0"),
                Path("/last/tmp/discord-ipc-1"),
                Path("/tmp/discord-ipc-0"),
                Path("/tmp/discord-ipc-1"),
            ),
        )

    def test_ac005_discovery_accepts_only_same_uid_unix_socket(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            socket_path = Path(directory) / "discord-ipc-0"
            plain_path = Path(directory) / "discord-ipc-1"
            listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            listener.bind(str(socket_path))
            plain_path.write_text("not a socket", encoding="utf-8")
            self.addCleanup(listener.close)

            found = discover_ipc_sockets(
                candidates=[socket_path, plain_path],
                expected_uid=os.getuid(),
            )
            wrong_uid = discover_ipc_sockets(
                candidates=[socket_path],
                expected_uid=os.getuid() + 1,
            )

        self.assertEqual(found, (socket_path,))
        self.assertEqual(wrong_uid, ())


class FakeDiscordServer:
    def __init__(self, handler: object) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self._temporary_directory.name) / "discord-ipc-0"
        self._listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._listener.bind(str(self.path))
        self._listener.listen(1)
        self._handler = handler
        self.error: BaseException | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            stream, _ = self._listener.accept()
            with stream:
                self._handler(stream)  # type: ignore[operator]
        except BaseException as exc:
            self.error = exc

    def close(self) -> None:
        self._listener.close()
        self._thread.join(timeout=2)
        self._temporary_directory.cleanup()
        if self._thread.is_alive():
            raise AssertionError("fake Discord server did not exit")
        if self.error is not None:
            raise self.error


class ClientIntegrationTests(unittest.TestCase):
    def test_ac004_handshake_ping_set_activity_and_clear(self) -> None:
        received: list[dict[str, object]] = []

        def handler(stream: socket.socket) -> None:
            handshake = read_frame(stream)
            self.assertEqual(handshake.opcode, Opcode.HANDSHAKE)
            self.assertEqual(
                decode_json_payload(handshake),
                {"v": 1, "client_id": "123456789012345678"},
            )
            write_frame(stream, Opcode.PING, b'{"probe":true}')
            pong = read_frame(stream)
            self.assertEqual(pong, IPCFrame(Opcode.PONG, b'{"probe":true}'))
            write_frame(stream, Opcode.PONG, b"{}")
            write_frame(stream, Opcode.FRAME, {"cmd": "DISPATCH", "evt": "READY"})
            for _ in range(2):
                request = decode_json_payload(read_frame(stream))
                received.append(request)
                write_frame(
                    stream,
                    Opcode.FRAME,
                    {"cmd": "SET_ACTIVITY", "nonce": request["nonce"], "data": None},
                )

        server = FakeDiscordServer(handler)
        client = DiscordIPCClient(
            "123456789012345678",
            pid=4242,
            socket_paths=[server.path],
        )
        try:
            client.connect()
            client.set_activity({"type": 2, "details": "Track"})
            client.clear()
            client.close()
        finally:
            server.close()

        self.assertEqual(
            received[0]["args"],
            {"pid": 4242, "activity": {"type": 2, "details": "Track"}},
        )
        self.assertEqual(received[1]["args"], {"pid": 4242, "activity": None})

    def test_ac004_error_event_is_reported(self) -> None:
        def handler(stream: socket.socket) -> None:
            read_frame(stream)
            write_frame(stream, Opcode.FRAME, {"evt": "READY"})
            request = decode_json_payload(read_frame(stream))
            write_frame(
                stream,
                Opcode.FRAME,
                {
                    "evt": "ERROR",
                    "nonce": request["nonce"],
                    "data": {"code": 4000, "message": "rejected"},
                },
            )

        server = FakeDiscordServer(handler)
        client = DiscordIPCClient("123456789012345678", socket_paths=[server.path])
        try:
            client.connect()
            with self.assertRaisesRegex(DiscordRPCError, "rejected") as caught:
                client.set_activity({"type": 2})
            self.assertEqual(caught.exception.code, 4000)
            client.close()
        finally:
            server.close()

    def test_ac004_close_opcode_is_reported(self) -> None:
        def handler(stream: socket.socket) -> None:
            read_frame(stream)
            write_frame(stream, Opcode.FRAME, {"evt": "READY"})
            read_frame(stream)
            write_frame(stream, Opcode.CLOSE, {"message": "restart"})

        server = FakeDiscordServer(handler)
        client = DiscordIPCClient("123456789012345678", socket_paths=[server.path])
        try:
            client.connect()
            with self.assertRaisesRegex(DiscordClosed, "restart"):
                client.set_activity({"type": 2})
            client.close()
        finally:
            server.close()

    def test_ac004_valid_but_unexpected_opcode_is_reported(self) -> None:
        def handler(stream: socket.socket) -> None:
            read_frame(stream)
            write_frame(stream, Opcode.FRAME, {"evt": "READY"})
            read_frame(stream)
            write_frame(stream, Opcode.HANDSHAKE, {"v": 1})

        server = FakeDiscordServer(handler)
        client = DiscordIPCClient("123456789012345678", socket_paths=[server.path])
        try:
            client.connect()
            with self.assertRaisesRegex(DiscordProtocolError, "after handshake"):
                client.set_activity({"type": 2})
            client.close()
        finally:
            server.close()

    def test_ac005_peer_uid_is_rechecked_after_connect(self) -> None:
        def handler(stream: socket.socket) -> None:
            return None

        server = FakeDiscordServer(handler)
        client = DiscordIPCClient(
            "123456789012345678",
            socket_paths=[server.path],
            peer_uid_getter=lambda _stream: os.getuid() + 1,
        )
        try:
            with self.assertRaisesRegex(DiscordConnectionError, "peer UID"):
                client.connect()
        finally:
            server.close()

    def test_inv004_public_application_id_is_only_credential_surface(self) -> None:
        parameters = inspect.signature(DiscordIPCClient).parameters
        sensitive = {"token", "user_token", "secret", "client_secret", "rpc_token"}

        self.assertTrue(sensitive.isdisjoint(parameters))
        with self.assertRaises(ValueError):
            DiscordIPCClient("not-a-snowflake")
        with self.assertRaises(ValueError):
            DiscordIPCClient("١٢٣٤٥٦٧٨٩")

        client = DiscordIPCClient("123456789012345678")
        for field in (
            "secrets",
            "secret",
            "user_token",
            "oauth_token",
            "client_secret",
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "credential boundary"):
                    client.set_activity({"type": 2, field: "private"})


class FakeTransport:
    def __init__(
        self,
        *,
        connect_error: BaseException | None = None,
        poll_error: BaseException | None = None,
        send_error: BaseException | None = None,
    ) -> None:
        self.connect_error = connect_error
        self.poll_error = poll_error
        self.send_error = send_error
        self.connected = False
        self.closed = False
        self.sent: list[dict[str, object] | None] = []

    def connect(self) -> None:
        if self.connect_error is not None:
            raise self.connect_error
        self.connected = True

    def set_activity(self, activity: Mapping[str, object]) -> None:
        if self.send_error is not None:
            raise self.send_error
        self.sent.append(dict(activity))

    def clear(self) -> None:
        if self.send_error is not None:
            raise self.send_error
        self.sent.append(None)

    def poll(self) -> bool:
        if self.poll_error is not None:
            error = self.poll_error
            self.poll_error = None
            raise error
        return False

    def close(self) -> None:
        self.closed = True


class ReconnectCoordinatorTests(unittest.TestCase):
    def test_ac004_inv005_offline_updates_coalesce_to_latest_replay(self) -> None:
        first = FakeTransport(connect_error=DiscordConnectionError("offline"))
        second = FakeTransport()
        clients = iter([first, second])
        coordinator = ReconnectCoordinator(lambda: next(clients))

        coordinator.set_desired({"details": "old", "type": 2})
        self.assertFalse(coordinator.pump(0.0))
        coordinator.set_desired({"details": "latest", "type": 2})
        self.assertFalse(coordinator.pump(0.9))
        self.assertTrue(coordinator.pump(1.0))
        self.assertFalse(coordinator.pump(2.0))

        self.assertEqual(second.sent, [{"details": "latest", "type": 2}])

    def test_ac004_bounded_exponential_backoff_uses_no_sleep(self) -> None:
        created: list[FakeTransport] = []

        def factory() -> FakeTransport:
            client = FakeTransport(connect_error=OSError("offline"))
            created.append(client)
            return client

        coordinator = ReconnectCoordinator(
            factory,
            backoff=BackoffPolicy(
                initial_delay=1.0,
                multiplier=2.0,
                maximum_delay=4.0,
            ),
        )
        coordinator.set_desired({"details": "track"})

        self.assertFalse(coordinator.pump(0.0))
        self.assertEqual(coordinator.next_attempt_at, 1.0)
        self.assertFalse(coordinator.pump(0.5))
        self.assertEqual(len(created), 1)
        self.assertFalse(coordinator.pump(1.0))
        self.assertEqual(coordinator.next_attempt_at, 3.0)
        self.assertFalse(coordinator.pump(3.0))
        self.assertEqual(coordinator.next_attempt_at, 7.0)
        self.assertFalse(coordinator.pump(7.0))
        self.assertEqual(coordinator.next_attempt_at, 11.0)

    def test_inv005_disconnect_replays_only_newest_or_clear_state(self) -> None:
        active = FakeTransport()
        replacement = FakeTransport()
        clients = iter([active, replacement])
        coordinator = ReconnectCoordinator(lambda: next(clients))

        coordinator.set_desired({"details": "track-a"})
        self.assertTrue(coordinator.pump(0.0))
        active.poll_error = DiscordClosed("Discord restarted")
        coordinator.set_desired({"details": "track-b"})
        self.assertFalse(coordinator.pump(1.0))
        coordinator.set_desired(None)
        self.assertFalse(coordinator.pump(1.5))
        self.assertTrue(coordinator.pump(2.0))

        self.assertEqual(active.sent, [{"details": "track-a"}])
        self.assertEqual(replacement.sent, [None])
        self.assertTrue(active.closed)

    def test_inv006_duplicate_updates_and_ticks_do_not_send(self) -> None:
        transport = FakeTransport()
        coordinator = ReconnectCoordinator(lambda: transport)
        activity = {
            "details": "Track",
            "type": 2,
            "timestamps": {"start": 100, "end": 300},
        }

        self.assertTrue(coordinator.set_desired(activity))
        self.assertTrue(coordinator.pump(0.0))
        for now in (1.0, 2.0, 3.0):
            self.assertFalse(coordinator.set_desired(dict(reversed(activity.items()))))
            self.assertFalse(coordinator.pump(now))

        self.assertEqual(transport.sent, [activity])

    def test_inv006_burst_updates_flush_latest_at_conservative_rate(self) -> None:
        transport = FakeTransport()
        coordinator = ReconnectCoordinator(lambda: transport)
        coordinator.set_desired({"details": "track-0"})
        self.assertTrue(coordinator.pump(0.0))

        for index, now in enumerate((0.1, 0.2, 0.3, 0.4, 0.5), start=1):
            coordinator.set_desired({"details": f"track-{index}"})
            self.assertFalse(coordinator.pump(now))
        self.assertFalse(coordinator.pump(3.9))
        self.assertTrue(coordinator.pump(4.0))

        self.assertEqual(
            transport.sent,
            [{"details": "track-0"}, {"details": "track-5"}],
        )

    def test_inv003_clear_bypasses_publish_interval(self) -> None:
        transport = FakeTransport()
        coordinator = ReconnectCoordinator(lambda: transport)
        coordinator.set_desired({"details": "private track"})
        coordinator.pump(0.0)

        coordinator.set_desired(None)

        self.assertTrue(coordinator.pump(0.1))
        self.assertEqual(transport.sent, [{"details": "private track"}, None])

    def test_inv005_shutdown_clears_once_and_closes(self) -> None:
        transport = FakeTransport()
        coordinator = ReconnectCoordinator(lambda: transport)
        coordinator.set_desired({"details": "Track"})
        coordinator.pump(0.0)

        self.assertTrue(coordinator.shutdown())

        self.assertEqual(transport.sent, [{"details": "Track"}, None])
        self.assertTrue(transport.closed)


if __name__ == "__main__":
    unittest.main()
