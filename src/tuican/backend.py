from typing import Protocol, Sequence, runtime_checkable

from .keyboard_button import KeyboardButton
from .update import TuicanUpdate


@runtime_checkable
class MessageBackend(Protocol):
    """Protocol for abstracting Telegram message operations.

    All methods are async and take a TUIcan-native `TuicanUpdate`. Adapters that
    talk to the real Telegram API (PTB, etc.) live in `tuican.backends.*` and
    translate between `TuicanUpdate` and the underlying transport.
    """

    async def send_keyboard_message(
        self,
        update: TuicanUpdate,
        text: str,
        keyboard_markup: Sequence[Sequence[KeyboardButton]],
        parse_mode: str = "HTML",
    ) -> None:
        """Send a new message or update an existing one with an inline keyboard."""
        ...

    async def send_plain_message(
        self,
        update: TuicanUpdate,
        text: str,
    ) -> None:
        """Send a plain text message."""
        ...

    async def send_notification(
        self,
        update: TuicanUpdate,
        text: str,
        delete_after: float = 1.0,
    ) -> None:
        """Send a short-lived notification that auto-deletes after ``delete_after`` seconds.

        Use for toasts (saved, errors, access denied). Pass ``delete_after=0``
        (or negative) to keep the message permanently.
        """
        ...

    async def delete_message(
        self,
        update: TuicanUpdate,
        message_id: int,
    ) -> None:
        """Delete a message by ID."""
        ...

    async def set_bot_commands(
        self,
        commands: dict[str, str],
    ) -> None:
        """Set the global bot command menu (no per-update context)."""
        ...



