from abc import ABC, abstractmethod
from typing import Sequence

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from src.components.component import Component, MessageHandlingComponent


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
    def get_layout(self, update, context) -> Sequence[Sequence[InlineKeyboardButton]]:
        raise NotImplementedError

    async def display(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_or_update_message(update, self._message, self.get_layout(update, context))

    async def dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        # TODO: optimisation make a map of components and remove iteration
        query = update.callback_query
        if query is not None:
            for component in self._components:
                if await component.handle_callback(update, context, query.data):
                    await self._send_or_update_message(update, self._message, self.get_layout(update, context))
                    return True
        return False

    async def message_dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        # TODO: optimisation make a map of components and remove iteration
        message = update.message
        if message is not None:
            for component in self._components:
                if isinstance(component, MessageHandlingComponent):
                    if await component.handle_message(update, context):
                        await self._send_or_update_message(update, self._message, self.get_layout(update, context))
                        return True
        return False

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


class MainScreen(Screen, ABC):
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.display(update, context)
