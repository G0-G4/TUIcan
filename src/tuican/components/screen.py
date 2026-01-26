from abc import ABC, abstractmethod
from typing import ClassVar, Protocol, Sequence, runtime_checkable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from .component import Component, MessageHandlingComponent


class Screen(ABC):

    def __init__(self, components: list[Component], message: str = None):
        self._message = message
        self._components = components
        self._update_to_display_on = None

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, message):
        self._message = message

    @abstractmethod
    async def get_layout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Sequence[
        Sequence[InlineKeyboardButton]]:
        raise NotImplementedError

    async def display(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_or_update_message(update, self._message, await self.get_layout(update, context))

    async def dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        # TODO: optimisation make a map of components and remove iteration
        query = update.callback_query
        if query is not None:
            for component in self._components:
                if await component.handle_callback(update, context, query.data):
                    return True
        return False

    async def message_dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        # TODO: optimisation make a map of components and remove iteration
        message = update.message
        if message is not None:
            for component in self._components:
                if isinstance(component, MessageHandlingComponent):
                    if await component.handle_message(update, context):
                        return True
        return False

    def add_component(self, comp: Component):
        self._components.append(comp)

    def add_components(self, comps: list[Component]):
        self._components.extend(comps)

    def delete_component(self, comp: Component):
        self._components.remove(comp)

    async def _send_or_update_message(self, update: Update, text: str,
                                      keyboard_markup: Sequence[Sequence[InlineKeyboardButton]]):
        # send new message with markup or update existing one
        if update.callback_query is not None:
            self._update_to_display_on = update
        update = self._update_to_display_on if self._update_to_display_on is not None else update
        try:
            if update.message:
                await update.message.reply_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard_markup),
                    parse_mode="HTML"
                )
            elif update.callback_query:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard_markup),
                    parse_mode="HTML"
                )
        except BadRequest as e:
            print(f"No modifications needed: {e.message}")

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.display(update, context)

    def clear_update(self):
        self._update_to_display_on = None


class ScreenGroup(Screen):

    def __init__(self, home_screen: Screen):
        super().__init__([])
        self._screen_stack: list[Screen] = [home_screen]

    async def go_to_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, new_screen: Screen):
        self._screen_stack.append(new_screen)

    async def go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(self._screen_stack) <= 1:
            raise RuntimeError("can't go back")
        self._screen_stack.pop()

    async def go_home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._screen_stack = self._screen_stack[:1]

    async def get_layout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Sequence[
        Sequence[InlineKeyboardButton]]:
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
    def message(self) -> str:
        return self._screen_stack[-1].message

    @message.setter
    def message(self, message):
        self._screen_stack[-1].message = message

class StartScreenProtocol(Protocol):

    description: ClassVar[str]
    def __call__(self) -> Screen:
        ...
