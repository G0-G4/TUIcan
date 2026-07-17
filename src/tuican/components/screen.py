import logging
from abc import ABC, abstractmethod
from typing import ClassVar, Protocol, Sequence

from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from ..backend import MessageBackend
from .component import Component, MessageHandlingComponent
from .registry import ComponentRegistry


class Screen(ABC):
    description: ClassVar[str | None] = None

    def __init__(self, components: list[Component], message: str | None = None, backend: MessageBackend | None = None):
        self._message = message
        self._update_to_display_on: Update | None = None
        self._backend = backend
        self._registry = ComponentRegistry(components, parent_screen=self)

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
    def backend(self) -> MessageBackend | None:
        return self._backend

    @backend.setter
    def backend(self, backend: MessageBackend | None):
        self._backend = backend

    @property
    def message(self) -> str | None:
        return self._message

    @message.setter
    def message(self, message):
        self._message = message

    @abstractmethod
    async def get_layout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Sequence[
        Sequence[InlineKeyboardButton | Component]]:
        raise NotImplementedError

    async def display(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        raw_layout = await self.get_layout(update, context)
        layout: list[list[InlineKeyboardButton]] = [
            [
                item.render(update, context) if isinstance(item, Component) else item
                for item in row
            ]
            for row in raw_layout
        ]
        await self._send_or_update_message(update, context, self._message or "", layout)

    async def dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return await self._registry.dispatcher(update, context)

    async def message_dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return await self._registry.message_dispatcher(update, context)

    async def set_focus(self, focused_component: MessageHandlingComponent | None, update: Update,
                        context: ContextTypes.DEFAULT_TYPE):
        await self._registry.set_focus(focused_component, update, context)

    def add_component(self, comp: Component):
        self._registry.add_component(comp)

    def add_components(self, comps: list[Component]):
        self._registry.add_components(comps)

    def delete_component(self, comp: Component):
        self._registry.delete_component(comp)

    def clear_active_message_component(self, component: MessageHandlingComponent):
        self._registry.clear_active_message_component(component)

    async def _send_or_update_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str,
                                      keyboard_markup: Sequence[Sequence[InlineKeyboardButton]]):
        if update.callback_query is not None:
            self._update_to_display_on = update
        target_update = self._update_to_display_on if self._update_to_display_on is not None else update
        if self._backend is not None:
            await self._backend.send_keyboard_message(target_update, context, text, keyboard_markup)
            return
        from telegram import InlineKeyboardMarkup
        from telegram.error import BadRequest
        try:
            if target_update.message:
                await target_update.message.reply_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard_markup),
                    parse_mode="HTML"
                )
            elif target_update.callback_query:
                await target_update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard_markup),
                    parse_mode="HTML"
                )
        except BadRequest as e:
            logging.getLogger(__name__).debug(f"No modifications needed: {e.message}")

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.display(update, context)

    def clear_update(self):
        self._update_to_display_on = None

    async def command_handler(self, args: list[str], update: Update, context: ContextTypes.DEFAULT_TYPE):
        ...

    async def send_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        if self._backend is not None:
            await self._backend.send_plain_message(update, context, text)
            return
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text=text)


class ScreenGroup(Screen):

    def __init__(self, home_screen: Screen):
        super().__init__([])
        self._home = home_screen
        self._screen_stack: list[Screen] = [home_screen]

    @property
    def backend(self) -> MessageBackend | None:
        return self._backend

    @backend.setter
    def backend(self, backend: MessageBackend | None):
        self._backend = backend
        for screen in self._screen_stack:
            screen.backend = backend

    async def go_to_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, new_screen: Screen):
        self._screen_stack.append(new_screen)
        if self._backend is not None:
            new_screen.backend = self._backend

    async def go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(self._screen_stack) <= 1:
            raise RuntimeError("can't go back")
        self._screen_stack.pop()

    async def go_home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._screen_stack = self._screen_stack[:1]

    async def get_layout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Sequence[
        Sequence[InlineKeyboardButton | Component]]:
        return await self._screen_stack[-1].get_layout(update, context)

    async def dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return await self._screen_stack[-1].dispatcher(update, context)

    async def message_dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return await self._screen_stack[-1].message_dispatcher(update, context)

    async def display(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self._screen_stack[-1].display(update, context)

    def clear_update(self):
        self._screen_stack[-1]._update_to_display_on = None

    @property
    def message(self) -> str | None:
        return self._screen_stack[-1].message

    @message.setter
    def message(self, message: str | None) -> None:
        self._screen_stack[-1].message = message

    async def command_handler(self, args: list[str], update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._home.command_handler(args, update, context)


class StartScreenProtocol(Protocol):
    description: ClassVar[str]

    def __call__(self) -> Screen:
        ...
