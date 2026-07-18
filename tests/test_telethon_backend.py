"""Tests for TelethonBackend.

Skipped when telethon is not installed.
"""

from __future__ import annotations

from typing import Sequence
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("telethon")

from tuican.backends.telethon_backend import TelethonBackend
from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate, UpdateKind


class TestTelethonBackend:
    @pytest.fixture
    def client(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def backend(self, client: AsyncMock) -> TelethonBackend:
        return TelethonBackend(client)

    @pytest.fixture
    def callback_update(self) -> TuicanUpdate:
        return TuicanUpdate.from_callback(
            user_id=123,
            chat_id=456,
            callback_data="cb_data",
            message_id=1,
        )

    @pytest.fixture
    def command_update(self) -> TuicanUpdate:
        return TuicanUpdate.from_command(
            user_id=123,
            chat_id=456,
            message_text="/start",
            message_id=2,
        )

    @pytest.fixture
    def keyboard(self) -> Sequence[Sequence[KeyboardButton]]:
        return [
            [KeyboardButton(text="A", callback_data="a")],
            [KeyboardButton(text="B & C", callback_data="b")],
        ]

    # ---- send_keyboard_message ----

    @pytest.mark.asyncio
    async def test_send_keyboard_message_on_callback_uses_edit_message(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
        callback_update: TuicanUpdate,
        keyboard: Sequence[Sequence[KeyboardButton]],
    ) -> None:
        with patch(
            "tuican.backends.telethon_backend.Button.inline",
            side_effect=lambda text, data: MagicMock(text=text, data=data),
        ) as mock_inline:
            await backend.send_keyboard_message(
                callback_update, "Hello", keyboard, parse_mode="HTML"
            )

        client.edit_message.assert_awaited_once()
        call = client.edit_message.await_args
        assert call is not None
        assert call.args == (callback_update.chat_id, callback_update.message_id)
        assert call.kwargs["message"] == "Hello"
        assert call.kwargs["parse_mode"] == "html"
        assert len(call.kwargs["buttons"]) == 2
        assert len(call.kwargs["buttons"][0]) == 1
        assert len(call.kwargs["buttons"][1]) == 1
        mock_inline.assert_any_call("A", data=b"a")
        mock_inline.assert_any_call("B &amp; C", data=b"b")
        client.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_keyboard_message_on_command_uses_send_message(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
        command_update: TuicanUpdate,
        keyboard: Sequence[Sequence[KeyboardButton]],
    ) -> None:
        with patch(
            "tuican.backends.telethon_backend.Button.inline",
            side_effect=lambda text, data: MagicMock(text=text, data=data),
        ) as mock_inline:
            await backend.send_keyboard_message(
                command_update, "Hello", keyboard, parse_mode="HTML"
            )

        client.send_message.assert_awaited_once()
        call = client.send_message.await_args
        assert call is not None
        assert call.kwargs["entity"] == command_update.chat_id
        assert call.kwargs["message"] == "Hello"
        assert call.kwargs["parse_mode"] == "html"
        assert len(call.kwargs["buttons"]) == 2
        assert len(call.kwargs["buttons"][0]) == 1
        assert len(call.kwargs["buttons"][1]) == 1
        mock_inline.assert_any_call("A", data=b"a")
        mock_inline.assert_any_call("B &amp; C", data=b"b")
        client.edit_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_keyboard_message_escapes_html(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
        callback_update: TuicanUpdate,
    ) -> None:
        keyboard = [[KeyboardButton(text="<script>", callback_data="x")]]
        with patch(
            "tuican.backends.telethon_backend.Button.inline",
            side_effect=lambda text, data: MagicMock(text=text, data=data),
        ) as mock_inline:
            await backend.send_keyboard_message(
                callback_update, "<b>bold</b>", keyboard, parse_mode="HTML"
            )

        call = client.edit_message.await_args
        assert call is not None
        assert call.kwargs["message"] == "&lt;b&gt;bold&lt;/b&gt;"
        mock_inline.assert_any_call("&lt;script&gt;", data=b"x")

    @pytest.mark.asyncio
    async def test_send_keyboard_message_encodes_callback_data_as_bytes(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
        callback_update: TuicanUpdate,
    ) -> None:
        keyboard = [[KeyboardButton(text="Btn", callback_data="cd")]]
        with patch(
            "tuican.backends.telethon_backend.Button.inline",
            side_effect=lambda text, data: MagicMock(text=text, data=data),
        ) as mock_inline:
            await backend.send_keyboard_message(
                callback_update, "Hi", keyboard, parse_mode="HTML"
            )

        mock_inline.assert_called_once_with("Btn", data=b"cd")

    @pytest.mark.asyncio
    async def test_send_keyboard_message_swallows_message_not_modified_error(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
        callback_update: TuicanUpdate,
    ) -> None:
        from telethon.errors import MessageNotModifiedError

        client.edit_message.side_effect = MessageNotModifiedError(
            request=None  # type: ignore[arg-type]
        )
        keyboard = [[KeyboardButton(text="Btn", callback_data="cd")]]

        with patch(
            "tuican.backends.telethon_backend.Button.inline",
            side_effect=lambda text, data: MagicMock(text=text, data=data),
        ):
            await backend.send_keyboard_message(
                callback_update, "Hi", keyboard, parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_send_keyboard_message_swallows_rpc_not_modified(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
        callback_update: TuicanUpdate,
    ) -> None:
        from telethon.errors import RPCError

        err = RPCError(request=None, message="The message was not modified")  # type: ignore[arg-type]
        client.edit_message.side_effect = err
        keyboard = [[KeyboardButton(text="Btn", callback_data="cd")]]

        with patch(
            "tuican.backends.telethon_backend.Button.inline",
            side_effect=lambda text, data: MagicMock(text=text, data=data),
        ):
            await backend.send_keyboard_message(
                callback_update, "Hi", keyboard, parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_send_keyboard_message_re_raises_other_rpc_errors(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
        callback_update: TuicanUpdate,
    ) -> None:
        from telethon.errors import RPCError

        err = RPCError(request=None, message="SOME_OTHER_ERROR")  # type: ignore[arg-type]
        client.edit_message.side_effect = err
        keyboard = [[KeyboardButton(text="Btn", callback_data="cd")]]

        with patch(
            "tuican.backends.telethon_backend.Button.inline",
            side_effect=lambda text, data: MagicMock(text=text, data=data),
        ), pytest.raises(RPCError):
            await backend.send_keyboard_message(
                callback_update, "Hi", keyboard, parse_mode="HTML"
            )

    # ---- send_plain_message ----

    @pytest.mark.asyncio
    async def test_send_plain_message(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
        callback_update: TuicanUpdate,
    ) -> None:
        await backend.send_plain_message(callback_update, "plain text")
        client.send_message.assert_awaited_once_with(
            callback_update.chat_id, message="plain text"
        )

    # ---- delete_message ----

    @pytest.mark.asyncio
    async def test_delete_message(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
        callback_update: TuicanUpdate,
    ) -> None:
        await backend.delete_message(callback_update, message_id=99)
        client.delete_messages.assert_awaited_once_with(
            callback_update.chat_id, [99]
        )

    # ---- set_bot_commands ----

    @pytest.mark.asyncio
    async def test_set_bot_commands_is_no_op(
        self,
        backend: TelethonBackend,
        client: AsyncMock,
    ) -> None:
        await backend.set_bot_commands({"start": "Start bot"})
        client.assert_not_awaited()
