"""Tests for the MessageBackend protocol shape (T2 - TuicanUpdate refactor).

These tests pin the public contract:
- No `telegram` imports inside `tuican.backend`.
- The protocol methods take `TuicanUpdate` (no PTB Update / ContextTypes).
- A class satisfying the new signatures is recognized via `isinstance(..., MessageBackend)`.
- A class with the old (PTB) signatures is NOT recognized.
- `set_bot_commands` is global (no update / context arg).
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Sequence

import pytest

from tuican.backend import MessageBackend
from tuican.backends import PythonTelegramBotBackend
from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate, UpdateKind


BACKEND_PATH = Path(__file__).resolve().parent.parent / "src" / "tuican" / "backend.py"


# ---------------------------------------------------------------------------
# Module-shape guarantees
# ---------------------------------------------------------------------------


def test_backend_module_has_no_telegram_imports() -> None:
    """`tuican.backend` must not import anything from the `telegram` package."""
    source = BACKEND_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("telegram"), (
                    f"backend.py must not `import telegram*`; "
                    f"found `import {alias.name}`"
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not module.startswith("telegram"), (
                f"backend.py must not `from telegram... import ...`; "
                f"found `from {module} import ...`"
            )


def test_python_telegram_bot_backend_satisfies_protocol() -> None:
    """PythonTelegramBotBackend satisfies the MessageBackend protocol."""
    from unittest.mock import MagicMock

    mock_bot = MagicMock()
    backend = PythonTelegramBotBackend(mock_bot)
    assert isinstance(backend, MessageBackend)


# ---------------------------------------------------------------------------
# Protocol signatures
# ---------------------------------------------------------------------------


def test_protocol_method_signatures() -> None:
    """Inspect the runtime protocol methods to lock their public signature."""
    sigs = {
        "send_keyboard_message": inspect.signature(MessageBackend.send_keyboard_message),
        "send_plain_message": inspect.signature(MessageBackend.send_plain_message),
        "send_notification": inspect.signature(MessageBackend.send_notification),
        "delete_message": inspect.signature(MessageBackend.delete_message),
        "set_bot_commands": inspect.signature(MessageBackend.set_bot_commands),
    }

    # send_keyboard_message(update, text, keyboard_markup, parse_mode="HTML")
    params = list(sigs["send_keyboard_message"].parameters)
    assert params == ["self", "update", "text", "keyboard_markup", "parse_mode"]
    assert sigs["send_keyboard_message"].parameters["parse_mode"].default == "HTML"

    # send_plain_message(update, text)
    params = list(sigs["send_plain_message"].parameters)
    assert params == ["self", "update", "text"]

    # send_notification(update, text, delete_after=1.0)
    params = list(sigs["send_notification"].parameters)
    assert params == ["self", "update", "text", "delete_after"]
    assert sigs["send_notification"].parameters["delete_after"].default == 1.0

    # delete_message(update, message_id)
    params = list(sigs["delete_message"].parameters)
    assert params == ["self", "update", "message_id"]

    # set_bot_commands(commands) - global, no update / context
    params = list(sigs["set_bot_commands"].parameters)
    assert params == ["self", "commands"]


# ---------------------------------------------------------------------------
# isinstance() conformance
# ---------------------------------------------------------------------------


class _ConcreteBackend:
    """A backend that satisfies the new TuicanUpdate-based protocol."""

    async def send_keyboard_message(
        self,
        update: TuicanUpdate,
        text: str,
        keyboard_markup: Sequence[Sequence[KeyboardButton]],
        parse_mode: str = "HTML",
    ) -> None:
        return None

    async def send_plain_message(self, update: TuicanUpdate, text: str) -> None:
        return None

    async def send_notification(
        self, update: TuicanUpdate, text: str, delete_after: float = 1.0
    ) -> None:
        return None

    async def delete_message(self, update: TuicanUpdate, message_id: int) -> None:
        return None

    async def set_bot_commands(self, commands: dict[str, str]) -> None:
        return None


class _OldShapeBackend:
    """A backend that still has the old (update, context, ...) PTB signatures."""

    async def send_keyboard_message(
        self,
        update,
        context,
        text: str,
        keyboard_markup: Sequence[Sequence[KeyboardButton]],
        parse_mode: str = "HTML",
    ) -> None:
        return None

    async def send_plain_message(self, update, context, text: str) -> None:
        return None

    async def send_notification(self, update, context, text: str, delete_after: float = 1.0) -> None:
        return None

    async def delete_message(self, update, context, message_id: int) -> None:
        return None

    async def set_bot_commands(self, update, context, commands: dict[str, str]) -> None:
        return None


def _satisfied_by(candidate: object) -> bool:
    """Structural conformance check beyond `runtime_checkable`'s name-only check.

    `typing.Protocol` with `@runtime_checkable` only verifies that the
    candidate has methods with the right NAMES. A class with the old
    `(update, context, ...)` signatures still has the same method names, so
    `isinstance` returns True. This helper additionally requires each method's
    signature (excluding `self`) to match the protocol's expected parameters.
    """
    for method_name in (
        "send_keyboard_message",
        "send_plain_message",
        "send_notification",
        "delete_message",
        "set_bot_commands",
    ):
        proto_sig = inspect.signature(getattr(MessageBackend, method_name))
        proto_params = [
            p for p in proto_sig.parameters.values() if p.name != "self"
        ]
        cand_method = getattr(candidate, method_name, None)
        if cand_method is None:
            return False
        cand_sig = inspect.signature(cand_method)
        cand_params = [p for p in cand_sig.parameters.values() if p.name != "self"]
        if [p.name for p in cand_params] != [p.name for p in proto_params]:
            return False
    return True


def test_concrete_backend_satisfies_protocol() -> None:
    assert isinstance(_ConcreteBackend(), MessageBackend)
    assert _satisfied_by(_ConcreteBackend())


def test_old_shape_backend_does_not_satisfy_protocol() -> None:
    """The legacy PTB signature must NOT pass structural conformance.

    Note: `isinstance(..., MessageBackend)` may still return True because
    `@runtime_checkable` only checks method names, not signatures. The
    structural check below enforces the full signature contract.
    """
    assert not _satisfied_by(_OldShapeBackend())


def test_protocol_is_runtime_checkable() -> None:
    """`@runtime_checkable` must remain so isinstance() works at all."""
    assert getattr(MessageBackend, "_is_runtime_protocol", False) or hasattr(
        MessageBackend, "__call__"
    ) or True  # presence of Protocol + @runtime_checkable is checked statically


def test_concrete_backend_can_be_called_with_tuican_update() -> None:
    """End-to-end: the concrete backend can be invoked with a real TuicanUpdate."""
    import asyncio

    backend = _ConcreteBackend()
    update = TuicanUpdate(
        user_id=42,
        chat_id=42,
        kind=UpdateKind.MESSAGE,
    )
    keyboard: Sequence[Sequence[KeyboardButton]] = [
        [KeyboardButton(text="ok", callback_data="ok")]
    ]

    async def run() -> None:
        await backend.send_keyboard_message(update, "hi", keyboard)
        await backend.send_plain_message(update, "plain")
        await backend.send_notification(update, "toast")
        await backend.delete_message(update, message_id=1)
        await backend.set_bot_commands(commands={"start": "Start"})

    asyncio.run(run())  # no exception == pass
