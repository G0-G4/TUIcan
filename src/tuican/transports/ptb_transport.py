from __future__ import annotations

import logging
import os
from typing import Any

from telegram import BotCommand, Update
from telegram.ext import (
    Application as TgApplication,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from tuican.backend import MessageBackend
from tuican.backends.ptb_backend import PythonTelegramBotBackend
from tuican.update import TuicanUpdate, UpdateKind

logger = logging.getLogger(__name__)


class PtbTransport:
    """Transport implementation backed by ``python-telegram-bot``.

    Holds a PTB ``ApplicationBuilder``, builds the app on ``start()``, registers
    three update handlers that convert PTB ``Update`` objects into
    ``TuicanUpdate`` and forward them to the TUIcan ``Application`` core.
    """

    def __init__(self, token: str) -> None:
        self._token = token
        self._app_builder = ApplicationBuilder().token(token)
        self._app: TgApplication | None = None
        self._core: Any = None

    def start(self, core: Any) -> None:
        """Build the PTB app, register handlers, and wire to *core*."""
        self._core = core

        async def post_init(application: TgApplication) -> None:
            loaded = await core.state_store.load_all()
            core._user_commands.update({int(k): v for k, v in loaded.items()})
            await application.bot.set_my_commands(
                [BotCommand(c, s.description) for c, s in core.screens.items()]
            )

        if proxy := os.getenv("PROXY"):
            self._app_builder.proxy(proxy)

        self._app_builder.post_init(post_init)
        if self._app is None:
            self._app = self._app_builder.build()
        self._app.add_handler(
            CommandHandler(core.screens.keys(), self._command_handler)
        )
        self._app.add_handler(
            CallbackQueryHandler(self._callback_handler, pattern=".*")
        )
        self._app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, self._message_handler
            )
        )

    async def stop(self) -> None:
        if self._app is not None:
            await self._app.stop()

    def default_backend(self) -> MessageBackend:
        if self._app is None:
            self._app = self._app_builder.build()
        return PythonTelegramBotBackend(self._app.bot)

    async def _command_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if self._core is None:
            return
        tuican_update = self._ptb_to_tuican(update)
        await self._core.command_handler(tuican_update)

    async def _callback_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if self._core is None:
            return
        tuican_update = self._ptb_to_tuican(update)
        await self._core.dispatcher(tuican_update)

    async def _message_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if self._core is None:
            return
        tuican_update = self._ptb_to_tuican(update)
        await self._core.message_dispatcher(tuican_update)

    @staticmethod
    def _ptb_to_tuican(update: Update) -> TuicanUpdate:
        """Convert a PTB ``Update`` into a TUIcan-native ``TuicanUpdate``."""
        if update.message is not None:
            user_id = (
                update.message.from_user.id
                if update.message.from_user is not None
                else None
            )
            chat_id = (
                update.effective_chat.id
                if update.effective_chat is not None
                else None
            )
            message_text = update.message.text
            message_id = getattr(update.message, "message_id", None)
            if message_id is None:
                message_id = getattr(update.message, "id", None)
            if message_text is not None and message_text.startswith("/"):
                return TuicanUpdate.from_command(
                    user_id, chat_id, message_text, message_id
                )
            return TuicanUpdate.from_message(
                user_id, chat_id, message_text, message_id
            )
        elif update.callback_query is not None:
            user_id = (
                update.callback_query.from_user.id
                if update.callback_query.from_user is not None
                else None
            )
            chat_id = (
                update.effective_chat.id
                if update.effective_chat is not None
                else None
            )
            callback_data = update.callback_query.data
            message_id = None
            if update.callback_query.message is not None:
                message_id = getattr(
                    update.callback_query.message, "message_id", None
                )
                if message_id is None:
                    message_id = getattr(update.callback_query.message, "id", None)
            return TuicanUpdate.from_callback(
                user_id, chat_id, callback_data, message_id
            )
        else:
            return TuicanUpdate(
                user_id=None,
                chat_id=(
                    update.effective_chat.id
                    if update.effective_chat is not None
                    else None
                ),
            )

    def run(self) -> None:
        if self._app is None:
            raise RuntimeError("Transport must be started before run()")
        self._app.run_polling(allowed_updates=Update.ALL_TYPES)

    def run_webhook(
        self,
        webhook_url: str,
        listen: str = "0.0.0.0",
        port: int = 8080,
        **kwargs: Any,
    ) -> None:
        if self._app is None:
            raise RuntimeError("Transport must be started before run_webhook()")
        self._app.run_webhook(
            webhook_url=webhook_url,
            listen=listen,
            port=port,
            allowed_updates=Update.ALL_TYPES,
            **kwargs,
        )
