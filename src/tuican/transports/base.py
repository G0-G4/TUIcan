"""Base transport protocol and application-core protocol for TUIcan.

These protocols define the seam between a Telegram client transport
(e.g. Telethon) and the TUIcan application core.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from tuican.backend import MessageBackend
from tuican.update import TuicanUpdate


class ApplicationCore(Protocol):
    """Protocol for the application object that receives converted updates."""

    async def command_handler(self, update: TuicanUpdate) -> None:
        """Handle a command update (message starting with ``/``)."""
        ...

    async def dispatcher(self, update: TuicanUpdate) -> None:
        """Handle a callback-query update."""
        ...

    async def message_dispatcher(self, update: TuicanUpdate) -> None:
        """Handle a plain-text message update."""
        ...


@runtime_checkable
class Transport(Protocol):
    """Protocol for a Telegram client transport adapter."""

    def start(self, application_core: ApplicationCore) -> None:
        """Wire the transport to *application_core* and start listening."""
        ...

    def run(self) -> None:
        """Block until the transport disconnects."""
        ...

    def run_webhook(
        self,
        webhook_url: str,
        listen: str = "0.0.0.0",
        port: int = 8080,
        **kwargs: Any,
    ) -> None:
        """Run in webhook mode (may raise ``NotImplementedError``)."""
        ...

    def default_backend(self) -> MessageBackend:
        """Return the default ``MessageBackend`` for this transport."""
        ...
