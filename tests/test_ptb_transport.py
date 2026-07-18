"""Tests for `PtbTransport` in `tuican.transports.ptb_transport`.

Asserts that:
- `PtbTransport` builds a PTB `Application` via `ApplicationBuilder`
- Proxy env is applied when present
- Three handlers are registered (Command, CallbackQuery, Message)
- Each handler converts a PTB `Update` to `TuicanUpdate` with the correct `UpdateKind`
- `default_backend()` returns a `PythonTelegramBotBackend` wired to the built bot
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import Application as TgApplication, ApplicationBuilder

from tuican.update import TuicanUpdate, UpdateKind


class MockApplication:
    """Minimal stand-in for the TUIcan `Application` core."""

    def __init__(self) -> None:
        self.command_handler = AsyncMock()
        self.dispatcher = AsyncMock()
        self.message_dispatcher = AsyncMock()
        self.screens: dict[str, Any] = {"start": MagicMock()}
        self.state_store = MagicMock()
        self.state_store.load_all = AsyncMock(return_value={})
        self._user_commands: dict[int, str] = {}


@pytest.fixture
def mock_core() -> MockApplication:
    return MockApplication()


class TestPtbTransportLifecycle:
    @pytest.mark.asyncio
    async def test_start_builds_app_and_registers_three_handlers(
        self, mock_core: MockApplication
    ) -> None:
        from tuican.transports.ptb_transport import PtbTransport

        transport = PtbTransport("fake-token")
        mock_app = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        transport._app_builder = mock_builder

        transport.start(mock_core)

        assert mock_app.add_handler.call_count == 3

    @pytest.mark.asyncio
    async def test_start_applies_proxy_from_env(
        self, mock_core: MockApplication
    ) -> None:
        from tuican.transports.ptb_transport import PtbTransport

        transport = PtbTransport("fake-token")
        mock_app = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        transport._app_builder = mock_builder

        with patch.dict(os.environ, {"PROXY": "http://proxy:8080"}, clear=False):
            transport.start(mock_core)

        mock_builder.proxy.assert_called_once_with("http://proxy:8080")

    @pytest.mark.asyncio
    async def test_post_init_loads_state_and_sets_commands(
        self, mock_core: MockApplication
    ) -> None:
        from tuican.transports.ptb_transport import PtbTransport

        transport = PtbTransport("fake-token")
        mock_app = MagicMock()
        mock_app.bot = MagicMock()
        mock_app.bot.set_my_commands = AsyncMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        transport._app_builder = mock_builder

        mock_core.state_store.load_all = AsyncMock(return_value={"42": "start"})

        captured_post_init: Any = None

        def capture_post_init(fn: Any) -> Any:
            nonlocal captured_post_init
            captured_post_init = fn
            return mock_builder

        mock_builder.post_init.side_effect = capture_post_init

        transport.start(mock_core)

        assert captured_post_init is not None
        await captured_post_init(mock_app)

        mock_core.state_store.load_all.assert_awaited_once()
        mock_app.bot.set_my_commands.assert_awaited_once()


class TestPtbToTuicanConversion:
    @pytest.fixture
    def ptb_command_update(self) -> MagicMock:
        update = MagicMock(spec=Update)
        update.message = MagicMock()
        update.message.from_user = MagicMock()
        update.message.from_user.id = 123
        update.effective_chat = MagicMock()
        update.effective_chat.id = 456
        update.message.text = "/start"
        update.message.message_id = 1
        update.callback_query = None
        return update

    @pytest.fixture
    def ptb_callback_update(self) -> MagicMock:
        update = MagicMock(spec=Update)
        update.callback_query = MagicMock()
        update.callback_query.from_user = MagicMock()
        update.callback_query.from_user.id = 123
        update.effective_chat = MagicMock()
        update.effective_chat.id = 456
        update.callback_query.data = "cb_data"
        update.message = None
        return update

    @pytest.fixture
    def ptb_message_update(self) -> MagicMock:
        update = MagicMock(spec=Update)
        update.message = MagicMock()
        update.message.from_user = MagicMock()
        update.message.from_user.id = 123
        update.effective_chat = MagicMock()
        update.effective_chat.id = 456
        update.message.text = "hello"
        update.message.message_id = 2
        update.callback_query = None
        return update

    @pytest.mark.asyncio
    async def test_command_handler_converts_and_calls_on_command(
        self,
        mock_core: MockApplication,
        ptb_command_update: MagicMock,
    ) -> None:
        from tuican.transports.ptb_transport import PtbTransport

        transport = PtbTransport("fake-token")
        mock_app = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.post_init.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        transport._app_builder = mock_builder

        transport.start(mock_core)

        # Extract the CommandHandler callback
        from telegram.ext import CommandHandler

        command_handler_call = None
        for call in mock_app.add_handler.call_args_list:
            handler = call.args[0]
            if isinstance(handler, CommandHandler):
                command_handler_call = handler.callback
                break

        assert command_handler_call is not None
        context = MagicMock()
        await command_handler_call(ptb_command_update, context)

        mock_core.command_handler.assert_awaited_once()
        tuican_update: TuicanUpdate = mock_core.command_handler.await_args[0][0]
        assert isinstance(tuican_update, TuicanUpdate)
        assert tuican_update.user_id == 123
        assert tuican_update.chat_id == 456
        assert tuican_update.message_text == "/start"
        assert tuican_update.message_id == 1
        assert tuican_update.kind == UpdateKind.COMMAND

    @pytest.mark.asyncio
    async def test_callback_handler_converts_and_calls_on_callback(
        self,
        mock_core: MockApplication,
        ptb_callback_update: MagicMock,
    ) -> None:
        from tuican.transports.ptb_transport import PtbTransport

        transport = PtbTransport("fake-token")
        mock_app = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.post_init.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        transport._app_builder = mock_builder

        transport.start(mock_core)

        from telegram.ext import CallbackQueryHandler

        callback_handler_call = None
        for call in mock_app.add_handler.call_args_list:
            handler = call.args[0]
            if isinstance(handler, CallbackQueryHandler):
                callback_handler_call = handler.callback
                break

        assert callback_handler_call is not None
        context = MagicMock()
        await callback_handler_call(ptb_callback_update, context)

        mock_core.dispatcher.assert_awaited_once()
        tuican_update: TuicanUpdate = mock_core.dispatcher.await_args[0][0]
        assert isinstance(tuican_update, TuicanUpdate)
        assert tuican_update.user_id == 123
        assert tuican_update.chat_id == 456
        assert tuican_update.callback_data == "cb_data"
        assert tuican_update.kind == UpdateKind.CALLBACK

    @pytest.mark.asyncio
    async def test_message_handler_converts_and_calls_on_message(
        self,
        mock_core: MockApplication,
        ptb_message_update: MagicMock,
    ) -> None:
        from tuican.transports.ptb_transport import PtbTransport

        transport = PtbTransport("fake-token")
        mock_app = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.post_init.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        transport._app_builder = mock_builder

        transport.start(mock_core)

        from telegram.ext import MessageHandler

        message_handler_call = None
        for call in mock_app.add_handler.call_args_list:
            handler = call.args[0]
            if isinstance(handler, MessageHandler):
                message_handler_call = handler.callback
                break

        assert message_handler_call is not None
        context = MagicMock()
        await message_handler_call(ptb_message_update, context)

        mock_core.message_dispatcher.assert_awaited_once()
        tuican_update: TuicanUpdate = mock_core.message_dispatcher.await_args[0][0]
        assert isinstance(tuican_update, TuicanUpdate)
        assert tuican_update.user_id == 123
        assert tuican_update.chat_id == 456
        assert tuican_update.message_text == "hello"
        assert tuican_update.message_id == 2
        assert tuican_update.kind == UpdateKind.MESSAGE


class TestPtbTransportBackend:
    def test_default_backend_returns_python_telegram_bot_backend(self) -> None:
        from tuican.transports.ptb_transport import PtbTransport

        transport = PtbTransport("fake-token")
        mock_app = MagicMock()
        mock_app.bot = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.post_init.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        transport._app_builder = mock_builder

        transport.start(MockApplication())

        backend = transport.default_backend()
        from tuican.backends.ptb_backend import PythonTelegramBotBackend

        assert isinstance(backend, PythonTelegramBotBackend)


class TestPtbTransportRunModes:
    @pytest.mark.asyncio
    async def test_run_polling_delegates_to_ptb_app(
        self, mock_core: MockApplication
    ) -> None:
        from tuican.transports.ptb_transport import PtbTransport

        transport = PtbTransport("fake-token")
        mock_app = MagicMock()
        mock_app.run_polling = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.post_init.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        transport._app_builder = mock_builder

        transport.start(mock_core)
        transport.run()

        mock_app.run_polling.assert_called_once_with(allowed_updates=Update.ALL_TYPES)

    @pytest.mark.asyncio
    async def test_run_webhook_delegates_to_ptb_app(
        self, mock_core: MockApplication
    ) -> None:
        from tuican.transports.ptb_transport import PtbTransport

        transport = PtbTransport("fake-token")
        mock_app = MagicMock()
        mock_app.run_webhook = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.post_init.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        transport._app_builder = mock_builder

        transport.start(mock_core)
        transport.run_webhook("https://example.com/webhook", listen="127.0.0.1", port=5000)

        mock_app.run_webhook.assert_called_once_with(
            webhook_url="https://example.com/webhook",
            listen="127.0.0.1",
            port=5000,
            allowed_updates=Update.ALL_TYPES,
        )
