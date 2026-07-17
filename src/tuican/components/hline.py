from ..keyboard_button import KeyboardButton
from .component import Component


class Hline(Component):
    async def handle_callback(self) -> bool:
        return False

    def render(self) -> KeyboardButton:
        return KeyboardButton(
            text="───────────────",
            callback_data=self.callback_data
        )
