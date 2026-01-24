from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from src.tuican.components.component import CallBack, Component


class Button(Component):
    def __init__(
            self,
            text: str = "",
            component_id: str = None,
            callback_data: str | None = None,
            on_change: CallBack | None = None):
        super().__init__(component_id, callback_data, on_change)
        self._text = text

    async def click(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        if self.on_change:
            await self.call_on_change(update, context, callback_data)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              callback_data: str | None) -> bool:
        if callback_data != self.callback_data:
            return False
        await self.click(update, context, callback_data)
        return True

    def render(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            self._text,
            callback_data=self.callback_data
        )

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
