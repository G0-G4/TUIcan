from __future__ import annotations

import asyncio
import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Coroutine, TYPE_CHECKING

from ..keyboard_button import KeyboardButton
from ..update import TuicanUpdate

if TYPE_CHECKING:
    from .screen import Screen

CallBack = Callable[..., None] | Callable[..., Coroutine[Any, Any, None]]


def _invoke_callback(
    callback: CallBack,
    update: TuicanUpdate | None,
    component: Any,
) -> None | Coroutine[Any, Any, None]:
    """Invoke a callback passing only the parameters it actually accepts.

    Supported signatures (0-3 positional params, ignoring *args/**kwargs):
      - ()
      - (component)
      - (update)
      - (update, component)
    """
    sig = inspect.signature(callback)
    params = [
        p
        for p in sig.parameters.values()
        if p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]
    count = len(params)

    args: list[Any]
    if count == 0:
        args = []
    elif count == 1:
        param_name = params[0].name
        if param_name == "update":
            args = [update]
        else:
            args = [component]
    elif count == 2:
        args = [update, component]
    else:
        raise TypeError(
            f"Callback {callback!r} must accept 0-3 positional parameters, got {count}"
        )

    return callback(*args)


class Component(ABC):
    def __init__(
        self,
        component_id: str | None = None,
        callback_data: str | None = None,
        on_change: CallBack | None = None,
        hidden: bool = False,
        data: Any = None,
    ):
        self._component_id = component_id or str(id(self))
        self._callback_data = callback_data or self.component_id
        self.on_change = on_change
        self._hidden = hidden
        self._data = data
        self._parent_screen: Screen | None = None

    @property
    def update(self) -> TuicanUpdate | None:
        return self._parent_screen.update if self._parent_screen is not None else None

    async def call_on_change(self) -> None:
        if not self.on_change:
            return
        result = _invoke_callback(self.on_change, self.update, self)
        if inspect.isawaitable(result):
            await result

    @abstractmethod
    async def handle_callback(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def render(self) -> KeyboardButton:
        raise NotImplementedError

    @property
    def callback_data(self) -> str:
        return self._callback_data

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def hidden(self) -> bool:
        return self._hidden

    @hidden.setter
    def hidden(self, hidden: bool) -> None:
        self._hidden = hidden

    @property
    def data(self) -> Any:
        return self._data

    @data.setter
    def data(self, data: Any) -> None:
        self._data = data

    @property
    def parent_screen(self) -> Screen | None:
        return self._parent_screen

    @parent_screen.setter
    def parent_screen(self, screen: Screen | None) -> None:
        self._parent_screen = screen


class MessageHandlingComponent(Component, ABC):
    @abstractmethod
    async def handle_message(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self) -> None:
        raise NotImplementedError

    def accept_focus(self) -> None:
        """Mark this component as accepting messages without side effects.

        Called by ``Screen.set_focus``. Override to flip internal active state.
        Must not clear values or fire ``on_change``.
        """

