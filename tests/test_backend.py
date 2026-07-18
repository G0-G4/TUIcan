import html
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.error import BadRequest

from tuican.backend import PythonTelegramBotBackend
from tuican.keyboard_button import KeyboardButton


class TestPythonTelegramBotBackend:
    @pytest.fixture
    def backend(self):
        return PythonTelegramBotBackend()

    @pytest.fixture
    def mock_update_message(self):
        update = MagicMock(spec=Update)
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        update.effective_chat = MagicMock()
        update.effective_chat.id = 12345
        return update

    @pytest.fixture
    def mock_update_callback(self):
        update = MagicMock(spec=Update)
        update.message = None
        update.callback_query = MagicMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_chat = MagicMock()
        update.effective_chat.id = 12345
        return update

    @pytest.fixture
    def mock_context(self):
        context = MagicMock()
        context.bot = MagicMock()
        context.bot.send_message = AsyncMock()
        context.bot.delete_message = AsyncMock()
        context.bot.set_my_commands = AsyncMock()
        return context

    @pytest.mark.asyncio
    async def test_send_keyboard_message_message_path(self, backend, mock_update_message, mock_context):
        """send_keyboard_message should reply via update.message when callback_query is absent."""
        keyboard = [[KeyboardButton(text="Btn", callback_data="cb")]]
        await backend.send_keyboard_message(
            mock_update_message, mock_context, "Hello", keyboard
        )
        mock_update_message.message.reply_text.assert_awaited_once()
        call_kwargs = mock_update_message.message.reply_text.call_args.kwargs
        assert call_kwargs["text"] == html.escape("Hello")
        assert call_kwargs["parse_mode"] == "HTML"
        assert "reply_markup" in call_kwargs

    @pytest.mark.asyncio
    async def test_send_keyboard_message_callback_query_path(self, backend, mock_update_callback, mock_context):
        """send_keyboard_message should edit message via callback_query when present."""
        keyboard = [[KeyboardButton(text="Btn", callback_data="cb")]]
        await backend.send_keyboard_message(
            mock_update_callback, mock_context, "Hello", keyboard
        )
        mock_update_callback.callback_query.edit_message_text.assert_awaited_once()
        call_kwargs = mock_update_callback.callback_query.edit_message_text.call_args.kwargs
        assert call_kwargs["text"] == html.escape("Hello")
        assert call_kwargs["parse_mode"] == "HTML"
        assert "reply_markup" in call_kwargs

    @pytest.mark.asyncio
    async def test_send_keyboard_message_html_escaping(self, backend, mock_update_message, mock_context):
        """send_keyboard_message should escape HTML in both text and button labels."""
        keyboard = [[KeyboardButton(text="<b>Bold</b>", callback_data="cb")]]
        await backend.send_keyboard_message(
            mock_update_message, mock_context, "<script>alert(1)</script>", keyboard
        )
        call_kwargs = mock_update_message.message.reply_text.call_args.kwargs
        assert call_kwargs["text"] == html.escape("<script>alert(1)</script>")
        markup = call_kwargs["reply_markup"]
        assert markup.inline_keyboard[0][0].text == html.escape("<b>Bold</b>")

    @pytest.mark.asyncio
    async def test_send_keyboard_message_bad_request_swallowed(self, backend, mock_update_message, mock_context):
        """send_keyboard_message should swallow BadRequest and log at debug level."""
        mock_update_message.message.reply_text = AsyncMock(
            side_effect=BadRequest("Message is not modified")
        )
        keyboard = [[KeyboardButton(text="Btn", callback_data="cb")]]
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            await backend.send_keyboard_message(
                mock_update_message, mock_context, "Hello", keyboard
            )
            mock_logger.debug.assert_called_once()
            assert "No modifications needed" in mock_logger.debug.call_args.args[0]

    @pytest.mark.asyncio
    async def test_send_plain_message_effective_chat_none(self, backend, mock_context):
        """send_plain_message should return early when effective_chat is None."""
        update = MagicMock(spec=Update)
        update.effective_chat = None
        await backend.send_plain_message(update, mock_context, "Hello")
        mock_context.bot.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_plain_message_sends_text(self, backend, mock_update_message, mock_context):
        """send_plain_message should send text to effective_chat.id."""
        await backend.send_plain_message(mock_update_message, mock_context, "Hello")
        mock_context.bot.send_message.assert_awaited_once_with(chat_id=12345, text="Hello")

    @pytest.mark.asyncio
    async def test_delete_message_effective_chat_none(self, backend, mock_context):
        """delete_message should return early when effective_chat is None."""
        update = MagicMock(spec=Update)
        update.effective_chat = None
        await backend.delete_message(update, mock_context, message_id=42)
        mock_context.bot.delete_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_message_deletes_by_id(self, backend, mock_update_message, mock_context):
        """delete_message should call bot.delete_message with correct chat_id and message_id."""
        await backend.delete_message(mock_update_message, mock_context, message_id=42)
        mock_context.bot.delete_message.assert_awaited_once_with(chat_id=12345, message_id=42)

    @pytest.mark.asyncio
    async def test_set_bot_commands(self, backend, mock_update_message, mock_context):
        """set_bot_commands should call bot.set_my_commands with BotCommand list."""
        await backend.set_bot_commands(
            mock_update_message, mock_context, commands={"start": "Start the bot", "help": "Get help"}
        )
        mock_context.bot.set_my_commands.assert_awaited_once()
        commands = mock_context.bot.set_my_commands.call_args.args[0]
        assert len(commands) == 2
        assert commands[0].command == "start"
        assert commands[0].description == "Start the bot"
        assert commands[1].command == "help"
        assert commands[1].description == "Get help"
