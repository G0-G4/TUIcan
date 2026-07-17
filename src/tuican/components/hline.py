from telegram import InlineKeyboardButton

from .component import Component


class Hline(Component):
    async def handle_callback(self) -> bool:
        return False

    def render(self) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            f"───────────────",
            callback_data=self.callback_data
        )
