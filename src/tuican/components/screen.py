import html
import logging
from abc import ABC, abstractmethod
from typing import ClassVar, Protocol, Sequence

from ..backend import MessageBackend
from ..keyboard_button import KeyboardButton
from ..update import TuicanUpdate, UpdateKind
from .component import Component, MessageHandlingComponent
from .registry import ComponentRegistry


class Screen(ABC):
    description: ClassVar[str | None] = None

    def __init__(
        self,
        components: list[Component],
        backend: MessageBackend | None = None,
        message: str | None = None,
    ):
        self._message = message
        self._update_to_display_on: TuicanUpdate | None = None
        self._backend = backend
        self._registry = ComponentRegistry(components, parent_screen=self)
        self._current_update: TuicanUpdate | None = None

    @property
    def _components(self) -> list[Component]:
        return self._registry.components

    @property
    def _callback_map(self) -> dict[str, Component]:
        return self._registry.callback_map

    @property
    def _message_components(self) -> list[MessageHandlingComponent]:
        return list(self._registry._message_components)

    @property
    def _active_message_component(self) -> MessageHandlingComponent | None:
        return self._registry.active_message_component

    @property
    def backend(self) -> MessageBackend:
        if self._backend is None:
            raise RuntimeError("Backend not set on screen")
        return self._backend

    @backend.setter
    def backend(self, backend: MessageBackend) -> None:
        self._backend = backend

    @property
    def message(self) -> str | None:
        return self._message

    @message.setter
    def message(self, message: str | None) -> None:
        self._message = message

    @property
    def update(self) -> TuicanUpdate | None:
        return self._current_update

    @abstractmethod
    def get_layout(
        self,
    ) -> Sequence[Sequence[KeyboardButton | Component]]:
        raise NotImplementedError

    async def display(self, update: TuicanUpdate) -> None:
        self._current_update = update
        try:
            raw_layout = self.get_layout()
            layout: list[list[KeyboardButton]] = [
                [
                    item.render() if isinstance(item, Component) else item
                    for item in row
                ]
                for row in raw_layout
            ]
            await self._send_or_update_message(self.message or "", layout)
        finally:
            self._current_update = None

    async def dispatcher(self, update: TuicanUpdate) -> bool:
        self._current_update = update
        try:
            return await self._registry.dispatcher(update)
        finally:
            self._current_update = None

    async def message_dispatcher(self, update: TuicanUpdate) -> bool:
        self._current_update = update
        try:
            return await self._registry.message_dispatcher(update)
        finally:
            self._current_update = None

    async def set_focus(self, focused_component: MessageHandlingComponent | None) -> None:
        await self._registry.set_focus(focused_component)

    def add_component(self, comp: Component) -> None:
        self._registry.add_component(comp)

    def add_components(self, comps: list[Component]) -> None:
        self._registry.add_components(comps)

    def delete_component(self, comp: Component) -> None:
        self._registry.delete_component(comp)

    def delete_components(self, comps: list[Component]) -> None:
        self._registry.delete_components(comps)

    def clear_active_message_component(self, component: MessageHandlingComponent) -> None:
        self._registry.clear_active_message_component(component)

    async def _send_or_update_message(
        self,
        text: str,
        keyboard_markup: Sequence[Sequence[KeyboardButton]],
    ) -> None:
        update = self._current_update
        if update is None:
            return
        if update.kind == UpdateKind.CALLBACK:
            self._update_to_display_on = update
        target_update = self._update_to_display_on if self._update_to_display_on is not None else update
        await self.backend.send_keyboard_message(target_update, text, keyboard_markup)

    async def on_start(self, update: TuicanUpdate) -> None:
        await self.display(update)

    def clear_update(self) -> None:
        self._update_to_display_on = None

    async def on_command(self, args: list[str], update: TuicanUpdate) -> None:
        ...

    async def send_message(self, update: TuicanUpdate, text: str) -> None:
        await self.backend.send_plain_message(update, text)

    async def notify(
        self,
        text: str,
        delete_after: float = 1.0,
        *,
        update: TuicanUpdate | None = None,
    ) -> None:
        """Send a short-lived toast notification (auto-deletes by default).

        Uses the screen's current update when ``update`` is omitted.
        """
        target = update if update is not None else self.update
        if target is None:
            return
        await self.backend.send_notification(target, text, delete_after)


class ScreenGroup(Screen):

    def __init__(self, home_screen: Screen, backend: MessageBackend | None = None, max_depth: int = 50):
        super().__init__([], backend=backend)
        self._home = home_screen
        self._screen_stack: list[Screen] = [home_screen]
        self._max_depth = max_depth

    @property
    def backend(self) -> MessageBackend:
        if self._backend is None:
            raise RuntimeError("Backend not set on screen group")
        return self._backend

    @backend.setter
    def backend(self, backend: MessageBackend) -> None:
        self._backend = backend
        for screen in self._screen_stack:
            screen.backend = backend

    async def go_to_screen(self, update: TuicanUpdate, new_screen: Screen) -> None:
        if len(self._screen_stack) >= self._max_depth:
            raise RuntimeError(f"Screen stack exceeded maximum depth of {self._max_depth}")
        self._screen_stack.append(new_screen)
        new_screen.backend = self.backend

    async def go_back(self, update: TuicanUpdate) -> None:
        if len(self._screen_stack) <= 1:
            raise RuntimeError("can't go back")
        self._screen_stack.pop()

    async def go_home(self, update: TuicanUpdate) -> None:
        self._screen_stack = self._screen_stack[:1]

    def get_layout(
        self,
    ) -> Sequence[Sequence[KeyboardButton | Component]]:
        return self._screen_stack[-1].get_layout()

    async def dispatcher(self, update: TuicanUpdate) -> bool:
        return await self._screen_stack[-1].dispatcher(update)

    async def message_dispatcher(self, update: TuicanUpdate) -> bool:
        return await self._screen_stack[-1].message_dispatcher(update)

    async def display(self, update: TuicanUpdate) -> None:
        return await self._screen_stack[-1].display(update)

    def clear_update(self) -> None:
        self._screen_stack[-1].clear_update()

    @property
    def message(self) -> str | None:
        return self._screen_stack[-1].message

    @message.setter
    def message(self, message: str | None) -> None:
        self._screen_stack[-1].message = message

    async def on_command(self, args: list[str], update: TuicanUpdate) -> None:
        await self._home.on_command(args, update)


class StartScreenProtocol(Protocol):
    description: ClassVar[str]

    def __call__(self) -> Screen:
        ...
