from typing import Any, Callable

from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from src.components.component import Component


class Button(Component):
    def __init__(self, text: str = "", callback_data: Any = None, component_id: str = None,
                 on_change: Callable[[Any, Update, ContextTypes.DEFAULT_TYPE], None] = None):
        super().__init__(component_id, on_change)
        self._text = text
        self._callback_data = callback_data

    async def click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.on_change:
            await self.call_on_change(update, context)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> bool:
        if callback_data == self._callback_data:
            await self.click(update, context)
            return True
        return False

    def render(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            self._text,
            callback_data=self._callback_data
        )

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
