from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from .component import Component


class Hline(Component):
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              callback_data: str | None) -> bool:
        ...

    def render(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            f"───────────────",
            callback_data=self.callback_data
        )
