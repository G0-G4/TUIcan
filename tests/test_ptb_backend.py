"""Tests for `PythonTelegramBotBackend` in `tuican.backends.ptb_backend`.

Uses `unittest.mock.AsyncMock` to fake a `telegram.Bot` and asserts that:
- `send_keyboard_message` builds `InlineKeyboardMarkup` correctly
- `send_plain_message` calls `bot.send_message`
- `delete_message` calls `bot.delete_message`
- `set_bot_commands` calls `bot.set_my_commands`
- HTML escaping is applied to text and button labels
- `BadRequest` exceptions are swallowed at debug level
- `UpdateKind.CALLBACK` triggers `edit_message_text`
- `UpdateKind.COMMAND` and `UpdateKind.MESSAGE` trigger `send_message`
"""

from __future__ import annotations

import html
import logging
from typing import Sequence
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate, UpdateKind


class TestPythonTelegramBotBackend:
    @pytest.fixture
    def mock_bot(self):
        """Create a mocked telegram.Bot with AsyncMock methods."""
        bot = MagicMock()
        bot.send_message = AsyncMock()
        bot.edit_message_text = AsyncMock()
        bot.delete_message = AsyncMock()
        bot.set_my_commands = AsyncMock()
        return bot

    @pytest.fixture
    def backend(self, mock_bot):
        """Create the PTB backend with a mocked bot."""
        from tuican.backends.ptb_backend import PythonTelegramBotBackend

        return PythonTelegramBotBackend(mock_bot)

    @pytest.fixture
    def callback_update(self) -> TuicanUpdate:
        return TuicanUpdate.from_callback(
            user_id=123,
            chat_id=456,
            callback_data="cb_data",
            message_id=1,
        )

    @pytest.fixture
    def message_update(self) -> TuicanUpdate:
        return TuicanUpdate.from_message(
            user_id=123,
            chat_id=456,
            message_text="hello",
            message_id=2,
        )

    @pytest.fixture
    def command_update(self) -> TuicanUpdate:
        return TuicanUpdate.from_command(
            user_id=123,
            chat_id=456,
            message_text="/start",
            message_id=3,
        )

    @pytest.fixture
    def keyboard(self) -> Sequence[Sequence[KeyboardButton]]:
        return [
            [KeyboardButton(text="Btn 1", callback_data="cb1")],
            [KeyboardButton(text="Btn 2", callback_data="cb2")],
        ]

    # ------------------------------------------------------------------
    # send_keyboard_message
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_keyboard_message_callback_uses_edit(
        self,
        backend,
        mock_bot,
        callback_update: TuicanUpdate,
        keyboard: Sequence[Sequence[KeyboardButton]],
    ) -> None:
        await backend.send_keyboard_message(callback_update, "Hello", keyboard)

        mock_bot.edit_message_text.assert_awaited_once_with(
            chat_id=456,
            message_id=1,
            text="Hello",
            parse_mode="HTML",
            reply_markup=ANY,
        )
        mock_bot.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_keyboard_message_message_uses_send(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
        keyboard: Sequence[Sequence[KeyboardButton]],
    ) -> None:
        await backend.send_keyboard_message(message_update, "Hello", keyboard)

        mock_bot.send_message.assert_awaited_once_with(
            chat_id=456,
            text="Hello",
            parse_mode="HTML",
            reply_markup=ANY,
        )
        mock_bot.edit_message_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_keyboard_message_command_uses_send(
        self,
        backend,
        mock_bot,
        command_update: TuicanUpdate,
        keyboard: Sequence[Sequence[KeyboardButton]],
    ) -> None:
        await backend.send_keyboard_message(command_update, "Hello", keyboard)

        mock_bot.send_message.assert_awaited_once_with(
            chat_id=456,
            text="Hello",
            parse_mode="HTML",
            reply_markup=ANY,
        )
        mock_bot.edit_message_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_keyboard_message_escapes_html(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
        keyboard: Sequence[Sequence[KeyboardButton]],
    ) -> None:
        malicious_text = "<script>alert('xss')</script>"
        malicious_button = KeyboardButton(text="<b>bold</b>", callback_data="cb")
        malicious_keyboard: Sequence[Sequence[KeyboardButton]] = [[malicious_button]]

        await backend.send_keyboard_message(
            message_update, malicious_text, malicious_keyboard
        )

        call_kwargs = mock_bot.send_message.await_args[1]
        assert call_kwargs["text"] == html.escape(malicious_text)

        reply_markup = call_kwargs["reply_markup"]
        row = reply_markup.inline_keyboard[0]
        assert row[0].text == html.escape("<b>bold</b>")

    @pytest.mark.asyncio
    async def test_send_keyboard_message_bad_request_swallowed(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
        keyboard: Sequence[Sequence[KeyboardButton]],
    ) -> None:
        from telegram.error import BadRequest

        mock_bot.send_message.side_effect = BadRequest("message not found")

        with patch(
            "tuican.backends.ptb_backend.logger", level=logging.DEBUG
        ) as mock_logger:
            await backend.send_keyboard_message(message_update, "Hello", keyboard)

        mock_logger.debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_keyboard_message_custom_parse_mode(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
        keyboard: Sequence[Sequence[KeyboardButton]],
    ) -> None:
        await backend.send_keyboard_message(
            message_update, "Hello", keyboard, parse_mode="MarkdownV2"
        )

        call_kwargs = mock_bot.send_message.await_args[1]
        assert call_kwargs["parse_mode"] == "MarkdownV2"

    # ------------------------------------------------------------------
    # send_plain_message
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_plain_message_calls_send_message(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
    ) -> None:
        await backend.send_plain_message(message_update, "Plain text")

        mock_bot.send_message.assert_awaited_once_with(
            chat_id=456,
            text="Plain text",
        )

    @pytest.mark.asyncio
    async def test_send_plain_message_escapes_html(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
    ) -> None:
        malicious = "<img src=x onerror=alert(1)>"
        await backend.send_plain_message(message_update, malicious)

        call_kwargs = mock_bot.send_message.await_args[1]
        assert call_kwargs["text"] == html.escape(malicious)

    @pytest.mark.asyncio
    async def test_send_plain_message_bad_request_swallowed(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
    ) -> None:
        from telegram.error import BadRequest

        mock_bot.send_message.side_effect = BadRequest("message not found")

        with patch(
            "tuican.backends.ptb_backend.logger", level=logging.DEBUG
        ) as mock_logger:
            await backend.send_plain_message(message_update, "Hello")

        mock_logger.debug.assert_called_once()

    # ------------------------------------------------------------------
    # delete_message
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete_message_calls_delete_message(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
    ) -> None:
        await backend.delete_message(message_update, message_id=42)

        mock_bot.delete_message.assert_awaited_once_with(
            chat_id=456,
            message_id=42,
        )

    @pytest.mark.asyncio
    async def test_delete_message_bad_request_swallowed(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
    ) -> None:
        from telegram.error import BadRequest

        mock_bot.delete_message.side_effect = BadRequest("message not found")

        with patch(
            "tuican.backends.ptb_backend.logger", level=logging.DEBUG
        ) as mock_logger:
            await backend.delete_message(message_update, message_id=42)

        mock_logger.debug.assert_called_once()

    # ------------------------------------------------------------------
    # set_bot_commands
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_set_bot_commands_calls_set_my_commands(
        self,
        backend,
        mock_bot,
    ) -> None:
        commands = {"start": "Start the bot", "help": "Get help"}
        await backend.set_bot_commands(commands)

        mock_bot.set_my_commands.assert_awaited_once()
        call_args = mock_bot.set_my_commands.await_args[0]
        bot_commands = call_args[0]

        assert len(bot_commands) == 2
        assert bot_commands[0].command == "start"
        assert bot_commands[0].description == "Start the bot"
        assert bot_commands[1].command == "help"
        assert bot_commands[1].description == "Get help"

    @pytest.mark.asyncio
    async def test_set_bot_commands_bad_request_swallowed(
        self,
        backend,
        mock_bot,
    ) -> None:
        from telegram.error import BadRequest

        mock_bot.set_my_commands.side_effect = BadRequest("invalid commands")

        with patch(
            "tuican.backends.ptb_backend.logger", level=logging.DEBUG
        ) as mock_logger:
            await backend.set_bot_commands({"start": "Start"})

        mock_logger.debug.assert_called_once()

    # ------------------------------------------------------------------
    # Keyboard markup structure
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_keyboard_markup_structure(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
    ) -> None:
        keyboard: Sequence[Sequence[KeyboardButton]] = [
            [KeyboardButton(text="A", callback_data="a")],
            [
                KeyboardButton(text="B", callback_data="b"),
                KeyboardButton(text="C", callback_data="c"),
            ],
        ]

        await backend.send_keyboard_message(message_update, "Text", keyboard)

        call_kwargs = mock_bot.send_message.await_args[1]
        reply_markup = call_kwargs["reply_markup"]
        inline_keyboard = reply_markup.inline_keyboard

        assert len(inline_keyboard) == 2
        assert len(inline_keyboard[0]) == 1
        assert len(inline_keyboard[1]) == 2

        assert inline_keyboard[0][0].text == "A"
        assert inline_keyboard[0][0].callback_data == "a"
        assert inline_keyboard[1][0].text == "B"
        assert inline_keyboard[1][0].callback_data == "b"
        assert inline_keyboard[1][1].text == "C"
        assert inline_keyboard[1][1].callback_data == "c"

    @pytest.mark.asyncio
    async def test_keyboard_button_without_callback_data(
        self,
        backend,
        mock_bot,
        message_update: TuicanUpdate,
    ) -> None:
        keyboard: Sequence[Sequence[KeyboardButton]] = [
            [KeyboardButton(text="No CB")],
        ]

        await backend.send_keyboard_message(message_update, "Text", keyboard)

        call_kwargs = mock_bot.send_message.await_args[1]
        reply_markup = call_kwargs["reply_markup"]
        btn = reply_markup.inline_keyboard[0][0]

        assert btn.text == "No CB"
        assert btn.callback_data is None
