"""Tests for TelethonTransport.

Skipped when telethon is not installed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("telethon")

from tuican.transports.telethon_transport import TelethonTransport
from tuican.update import TuicanUpdate, UpdateKind


class TestTelethonTransport:
    @pytest.fixture
    def client(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def transport(self, client: MagicMock) -> TelethonTransport:
        with patch(
            "tuican.transports.telethon_transport.TelegramClient",
            return_value=client,
        ) as tg_client_mock:
            t = TelethonTransport("test_token", api_id=1, api_hash="hash")
            # _ensure_client is called lazily (not in __init__); bind the mock
            # so that the patched TelegramClient is used whenever it is invoked.
            t._client = tg_client_mock.return_value
            return t

    @pytest.fixture
    def application_core(self) -> AsyncMock:
        return AsyncMock()

    def test_start_starts_client_and_registers_handlers(
        self,
        transport: TelethonTransport,
        client: MagicMock,
        application_core: AsyncMock,
    ) -> None:
        transport.start(application_core)

        client.start.assert_called_once_with(bot_token="test_token")
        assert client.add_event_handler.call_count == 2

        from telethon import events as telethon_events

        registered_events = [call.args[1] for call in client.add_event_handler.call_args_list]
        assert telethon_events.NewMessage in registered_events
        assert telethon_events.CallbackQuery in registered_events

    @pytest.mark.asyncio
    async def test_new_message_command_converts_to_tuican_update_and_calls_command_handler(
        self,
        transport: TelethonTransport,
        client: MagicMock,
        application_core: AsyncMock,
    ) -> None:
        transport.start(application_core)

        # The first registered handler is for NewMessage
        handler = client.add_event_handler.call_args_list[0].args[0]

        event = MagicMock()
        event.message.text = "/start"
        event.sender_id = 123
        event.chat_id = 456
        event.id = 789

        await handler(event)

        application_core.command_handler.assert_awaited_once()
        update = application_core.command_handler.await_args.args[0]
        assert isinstance(update, TuicanUpdate)
        assert update.kind == UpdateKind.COMMAND
        assert update.user_id == 123
        assert update.chat_id == 456
        assert update.message_text == "/start"
        assert update.message_id == 789
        assert update.callback_data is None

    @pytest.mark.asyncio
    async def test_new_message_text_converts_to_tuican_update_and_calls_message_dispatcher(
        self,
        transport: TelethonTransport,
        client: MagicMock,
        application_core: AsyncMock,
    ) -> None:
        transport.start(application_core)

        handler = client.add_event_handler.call_args_list[0].args[0]

        event = MagicMock()
        event.message.text = "hello world"
        event.sender_id = 123
        event.chat_id = 456
        event.id = 789

        await handler(event)

        application_core.message_dispatcher.assert_awaited_once()
        update = application_core.message_dispatcher.await_args.args[0]
        assert isinstance(update, TuicanUpdate)
        assert update.kind == UpdateKind.MESSAGE
        assert update.user_id == 123
        assert update.chat_id == 456
        assert update.message_text == "hello world"
        assert update.message_id == 789
        assert update.callback_data is None

    @pytest.mark.asyncio
    async def test_callback_query_converts_to_tuican_update_and_calls_dispatcher(
        self,
        transport: TelethonTransport,
        client: MagicMock,
        application_core: AsyncMock,
    ) -> None:
        transport.start(application_core)

        # The second registered handler is for CallbackQuery
        handler = client.add_event_handler.call_args_list[1].args[0]

        event = MagicMock()
        event.data = b"callback_data"
        event.sender_id = 123
        event.chat_id = 456
        event.message_id = 789

        await handler(event)

        application_core.dispatcher.assert_awaited_once()
        update = application_core.dispatcher.await_args.args[0]
        assert isinstance(update, TuicanUpdate)
        assert update.kind == UpdateKind.CALLBACK
        assert update.user_id == 123
        assert update.chat_id == 456
        assert update.callback_data == "callback_data"
        assert update.message_id == 789
        assert update.message_text is None

    @pytest.mark.asyncio
    async def test_new_message_without_message_does_not_crash(
        self,
        transport: TelethonTransport,
        client: MagicMock,
        application_core: AsyncMock,
    ) -> None:
        transport.start(application_core)

        handler = client.add_event_handler.call_args_list[0].args[0]

        event = MagicMock()
        event.message = None
        event.sender_id = 123
        event.chat_id = 456
        event.id = 789

        await handler(event)

        application_core.message_dispatcher.assert_awaited_once()
        update = application_core.message_dispatcher.await_args.args[0]
        assert update.message_text is None

    def test_run_calls_run_until_disconnected(
        self,
        transport: TelethonTransport,
        client: MagicMock,
    ) -> None:
        transport.run()
        client.run_until_disconnected.assert_called_once()

    def test_run_webhook_raises_not_implemented_error(
        self,
        transport: TelethonTransport,
    ) -> None:
        with pytest.raises(NotImplementedError, match="Telethon has no webhook mode"):
            transport.run_webhook("https://example.com")

    def test_default_backend_returns_telethon_backend_with_same_client(
        self,
        transport: TelethonTransport,
        client: MagicMock,
    ) -> None:
        from tuican.backends.telethon_backend import TelethonBackend

        backend = transport.default_backend()
        assert isinstance(backend, TelethonBackend)
        assert backend._client is client
