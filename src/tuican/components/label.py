from typing import Any

from ..keyboard_button import KeyboardButton
from .component import CallBack, Component


class Label(Component):
    def __init__(self, text: str = "", *, component_id: str | None = None,
                 on_change: CallBack | None = None, hidden: bool = False, data: Any = None):
        # Auto-suffix callback_data with id(self) so multiple Labels never collide
        super().__init__(component_id=component_id,
                         callback_data=f"label_{id(self)}",
                         on_change=on_change, hidden=hidden, data=data)
        self._text = text

    async def handle_callback(self) -> bool:
        return False

    def render(self) -> KeyboardButton:
        return KeyboardButton(text=self._text, callback_data=self.callback_data)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, v: str) -> None:
        self._text = v
