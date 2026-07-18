import html
from typing import Protocol, Sequence, runtime_checkable

from telegram import Update
from telegram.ext import ContextTypes

from .keyboard_button import KeyboardButton


@runtime_checkable
class MessageBackend(Protocol):
    """Protocol for abstracting Telegram message operations."""

    async def send_keyboard_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        keyboard_markup: Sequence[Sequence[KeyboardButton]],
        parse_mode: str = "HTML",
    ) -> None:
        """Send a new message or update an existing one with an inline keyboard."""
        ...

    async def send_plain_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
    ) -> None:
        """Send a plain text message."""
        ...

    async def delete_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_id: int,
    ) -> None:
        """Delete a message by ID."""
        ...

    async def set_bot_commands(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        commands: dict[str, str],
    ) -> None:
        """Set bot command menu."""
        ...


class PythonTelegramBotBackend:
    """Default backend implementation using python-telegram-bot."""

    async def send_keyboard_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        keyboard_markup: Sequence[Sequence[KeyboardButton]],
        parse_mode: str = "HTML",
    ) -> None:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.error import BadRequest

        telegram_markup: list[list[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(text=html.escape(kb.text), callback_data=kb.callback_data)
                for kb in row
            ]
            for row in keyboard_markup
        ]

        safe_text = html.escape(text)
        try:
            if update.message:
                await update.message.reply_text(
                    text=safe_text,
                    reply_markup=InlineKeyboardMarkup(telegram_markup),
                    parse_mode=parse_mode,
                )
            elif update.callback_query:
                await update.callback_query.edit_message_text(
                    text=safe_text,
                    reply_markup=InlineKeyboardMarkup(telegram_markup),
                    parse_mode=parse_mode,
                )
        except BadRequest as e:
            # Log at debug level; often just means "message not modified"
            import logging

            logging.getLogger(__name__).debug("No modifications needed: %s", e.message)

    async def send_plain_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
    ) -> None:
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text=text)

    async def delete_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_id: int,
    ) -> None:
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

    async def set_bot_commands(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        commands: dict[str, str],
    ) -> None:
        from telegram import BotCommand

        await context.bot.set_my_commands(
            [BotCommand(c, d) for c, d in commands.items()]
        )
