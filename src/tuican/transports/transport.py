from __future__ import annotations

from typing import Protocol, runtime_checkable

from tuican.application import Application
from tuican.backend import MessageBackend


@runtime_checkable
class Transport(Protocol):
    """Abstraction over a concrete Telegram transport (polling, webhook, etc.).

    A transport is responsible for:
    1. Building the underlying Telegram client (e.g. PTB ``Application``).
    2. Registering update handlers that convert native Telegram updates into
       ``TuicanUpdate`` and forward them to the TUIcan ``Application`` core.
    3. Providing a ``default_backend()`` wired to the built client so that
       ``Screen`` instances can send messages back to users.
    """

    async def start(self, core: Application) -> None:
        """Wire the transport to *core* and start listening for updates."""
        ...

    async def stop(self) -> None:
        """Gracefully shut down the transport."""
        ...

    def default_backend(self) -> MessageBackend:
        """Return a ``MessageBackend`` backed by the built transport client."""
        ...
