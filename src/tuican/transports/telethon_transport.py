"""Telethon transport adapter for TUIcan.

This module imports ``telethon`` types at import time so that Telethon
remains an optional dependency. If Telethon is not installed, importing
this module will raise ``ImportError``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from telethon import TelegramClient, events

from tuican.backends.telethon_backend import TelethonBackend
from tuican.transports.base import Transport
from tuican.update import TuicanUpdate, UpdateKind

if TYPE_CHECKING:
    from tuican.transports.base import ApplicationCore

logger = logging.getLogger(__name__)


class TelethonTransport(Transport):
    """TelegramClient wrapper that converts Telethon events to ``TuicanUpdate``
    and forwards them to an ``ApplicationCore``.

    Implements the ``Transport`` protocol.
    """

    def __init__(self, token: str, api_id: int | None = None, api_hash: str | None = None) -> None:
        self._token = token
        self._api_id = api_id
        self._api_hash = api_hash
        self._client: TelegramClient | None = None
        self._application_core: ApplicationCore | None = None

    def _ensure_client(self) -> TelegramClient:
        if self._client is None:
            self._client = TelegramClient("tuican_bot", self._api_id, self._api_hash)
        return self._client

    def start(self, application_core: ApplicationCore) -> None:
        """Start the client and register event handlers."""
        self._application_core = application_core
        client = self._ensure_client()
        client.start(bot_token=self._token)
        client.add_event_handler(
            self._on_new_message, events.NewMessage
        )
        client.add_event_handler(
            self._on_callback_query, events.CallbackQuery
        )
        logger.debug("TelethonTransport started and handlers registered")

    async def _on_new_message(self, event: events.NewMessage.Event) -> None:
        if self._application_core is None:
            return

        text = event.message.text if event.message is not None else None
        user_id = event.sender_id
        chat_id = event.chat_id
        message_id = event.message_id

        if text is not None and text.startswith("/"):
            update = TuicanUpdate.from_command(
                user_id=user_id,
                chat_id=chat_id,
                message_text=text,
                message_id=message_id,
            )
            await self._application_core.command_handler(update)
        else:
            update = TuicanUpdate.from_message(
                user_id=user_id,
                chat_id=chat_id,
                message_text=text,
                message_id=message_id,
            )
            await self._application_core.message_dispatcher(update)

    async def _on_callback_query(
        self, event: events.CallbackQuery.Event
    ) -> None:
        if self._application_core is None:
            return

        data = event.data.decode() if event.data is not None else None
        update = TuicanUpdate.from_callback(
            user_id=event.sender_id,
            chat_id=event.chat_id,
            callback_data=data,
            message_id=event.message_id,
        )
        await self._application_core.dispatcher(update)

    def run(self) -> None:
        """Block until the client disconnects."""
        self._ensure_client().run_until_disconnected()

    def run_webhook(
        self,
        webhook_url: str,
        listen: str = "0.0.0.0",
        port: int = 8080,
        **kwargs: Any,
    ) -> None:
        """Telethon does not support webhook mode (MTProto only)."""
        raise NotImplementedError(
            "Telethon has no webhook mode (MTProto only)"
        )

    def default_backend(self) -> TelethonBackend:
        """Return a ``TelethonBackend`` backed by the same client."""
        return TelethonBackend(self._ensure_client())
