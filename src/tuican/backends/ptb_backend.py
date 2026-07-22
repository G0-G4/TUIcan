"""PTB backend implementation for the `MessageBackend` protocol.

All `telegram` imports are local to this module only.
"""

from __future__ import annotations

import asyncio
import html
import logging
from typing import Sequence

import telegram

from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate, UpdateKind

logger = logging.getLogger(__name__)


class PythonTelegramBotBackend:
    """Adapter that translates TUIcan-native calls to python-telegram-bot API.

    Receives a PTB `telegram.Bot` instance at construction and delegates all
    message operations to it, converting `TuicanUpdate` and `KeyboardButton`
    rows into the corresponding PTB types.
    """

    def __init__(self, bot: telegram.Bot) -> None:
        self._bot = bot

    async def send_keyboard_message(
        self,
        update: TuicanUpdate,
        text: str,
        keyboard_markup: Sequence[Sequence[KeyboardButton]],
        parse_mode: str = "HTML",
    ) -> None:
        """Send or edit a message with an inline keyboard."""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.error import BadRequest

        safe_text = html.escape(text)
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=html.escape(button.text),
                        callback_data=button.callback_data,
                    )
                    for button in row
                ]
                for row in keyboard_markup
            ]
        )

        try:
            if update.kind == UpdateKind.CALLBACK:
                if update.chat_id is None or update.message_id is None:
                    logger.debug(
                        "Skipping edit_message_text: chat_id or message_id is None"
                    )
                    return
                await self._bot.edit_message_text(
                    chat_id=update.chat_id,
                    message_id=update.message_id,
                    text=safe_text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
            else:
                if update.chat_id is None:
                    logger.debug("Skipping send_message: chat_id is None")
                    return
                await self._bot.send_message(
                    chat_id=update.chat_id,
                    text=safe_text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
        except BadRequest:
            logger.debug("BadRequest swallowed in send_keyboard_message", exc_info=True)

    async def send_plain_message(
        self,
        update: TuicanUpdate,
        text: str,
    ) -> None:
        """Send a plain text message."""
        from telegram.error import BadRequest

        safe_text = html.escape(text)

        try:
            if update.chat_id is None:
                logger.debug("Skipping send_message: chat_id is None")
                return
            await self._bot.send_message(
                chat_id=update.chat_id,
                text=safe_text,
            )
        except BadRequest:
            logger.debug("BadRequest swallowed in send_plain_message", exc_info=True)

    async def send_notification(
        self,
        update: TuicanUpdate,
        text: str,
        delete_after: float = 1.0,
    ) -> None:
        """Send a toast message that auto-deletes after ``delete_after`` seconds."""
        from telegram.error import BadRequest

        safe_text = html.escape(text)

        try:
            if update.chat_id is None:
                logger.debug("Skipping send_notification: chat_id is None")
                return
            message = await self._bot.send_message(
                chat_id=update.chat_id,
                text=safe_text,
            )
        except BadRequest:
            logger.debug("BadRequest swallowed in send_notification", exc_info=True)
            return

        if delete_after > 0 and message is not None:
            chat_id = update.chat_id
            message_id = message.message_id
            asyncio.create_task(
                self._delete_notification_later(chat_id, message_id, delete_after)
            )

    async def _delete_notification_later(
        self,
        chat_id: int,
        message_id: int,
        delay: float,
    ) -> None:
        from telegram.error import BadRequest

        try:
            await asyncio.sleep(delay)
            await self._bot.delete_message(chat_id=chat_id, message_id=message_id)
        except BadRequest:
            logger.debug(
                "BadRequest swallowed deleting notification %s",
                message_id,
                exc_info=True,
            )
        except Exception:
            logger.debug(
                "Failed to delete notification %s",
                message_id,
                exc_info=True,
            )

    async def delete_message(
        self,
        update: TuicanUpdate,
        message_id: int,
    ) -> None:
        """Delete a message by ID."""
        from telegram.error import BadRequest

        try:
            if update.chat_id is None:
                logger.debug("Skipping delete_message: chat_id is None")
                return
            await self._bot.delete_message(
                chat_id=update.chat_id,
                message_id=message_id,
            )
        except BadRequest:
            logger.debug("BadRequest swallowed in delete_message", exc_info=True)

    async def set_bot_commands(
        self,
        commands: dict[str, str],
    ) -> None:
        """Set the global bot command menu."""
        from telegram import BotCommand
        from telegram.error import BadRequest

        bot_commands = [BotCommand(command=c, description=d) for c, d in commands.items()]

        try:
            await self._bot.set_my_commands(bot_commands)
        except BadRequest:
            logger.debug("BadRequest swallowed in set_bot_commands", exc_info=True)
