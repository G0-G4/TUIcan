"""Telethon adapter for the TUIcan ``MessageBackend`` protocol.

This module imports ``telethon`` types lazily at runtime so that Telethon
remains an optional dependency. If Telethon is not installed, importing this
module will raise ``ImportError`` at import time.
"""

from __future__ import annotations

import html
import logging
from typing import Sequence

from telethon import Button
from telethon.errors import MessageNotModifiedError, RPCError
from telethon.client.telegramclient import TelegramClient

from tuican.backend import MessageBackend
from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate, UpdateKind

logger = logging.getLogger(__name__)


class TelethonBackend(MessageBackend):
    """Telethon-backed implementation of ``MessageBackend``.

    Receives a ``telethon.TelegramClient`` at construction and uses it to
    send/edit/delete messages via the Telegram MTProto API.

    .. note::
        ``set_bot_commands`` is a no-op because Telethon does not expose a
        native helper for setting the bot command menu for *bot* accounts.
        The method logs a debug message and returns immediately.
    """

    def __init__(self, client: TelegramClient) -> None:
        self._client = client

    async def send_keyboard_message(
        self,
        update: TuicanUpdate,
        text: str,
        keyboard_markup: Sequence[Sequence[KeyboardButton]],
        parse_mode: str = "HTML",
    ) -> None:
        """Send or edit a message with an inline keyboard.

        Button text and message text are HTML-escaped before being handed to
        Telethon.  ``callback_data`` is encoded to bytes as required by
        ``Button.inline``.
        """
        buttons: list[list[Button]] = [
            [
                Button.inline(
                    html.escape(button.text),
                    data=button.callback_data.encode(),
                )
                for button in row
                if button.callback_data is not None
            ]
            for row in keyboard_markup
        ]

        safe_text = html.escape(text)

        try:
            if update.kind == UpdateKind.CALLBACK:
                await self._client.edit_message(
                    update.chat_id,
                    update.message_id,
                    text=safe_text,
                    buttons=buttons,
                    parse_mode="html",
                )
            else:
                await self._client.send_message(
                    entity=update.chat_id,
                    text=safe_text,
                    buttons=buttons,
                    parse_mode="html",
                )
        except MessageNotModifiedError:
            logger.debug("Message not modified, swallowing error")
        except RPCError as exc:
            if "not modified" in str(exc).lower():
                logger.debug("Message not modified, swallowing RPCError")
            else:
                raise

    async def send_plain_message(
        self,
        update: TuicanUpdate,
        text: str,
    ) -> None:
        """Send a plain text message."""
        await self._client.send_message(update.chat_id, text=text)

    async def delete_message(
        self,
        update: TuicanUpdate,
        message_id: int,
    ) -> None:
        """Delete a message by ID."""
        await self._client.delete_messages(update.chat_id, [message_id])

    async def set_bot_commands(
        self,
        commands: dict[str, str],
    ) -> None:
        """No-op: Telethon does not support ``set_bot_commands`` for bot accounts.

        Logs a debug-level message indicating the limitation.
        """
        logger.debug(
            "Telethon backend does not support set_bot_commands for bot accounts"
        )
