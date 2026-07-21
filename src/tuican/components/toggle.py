from ..keyboard_button import KeyboardButton
from .component import CallBack, Component, _invoke_callback


class Toggle(Component):
    def __init__(
        self,
        text: str = "",
        on_text: str | None = None,
        off_text: str | None = None,
        on_change: CallBack | None = None,
        on: bool = False,
        component_id: str | None = None,
        callback_data: str | None = None,
    ):
        super().__init__(component_id, callback_data, on_change)
        self._text = text
        self._on = on
        self._on_text = on_text or text or "ON"
        self._off_text = off_text or text or "OFF"

    async def toggle(self) -> None:
        self._on = not self._on
        await self.call_on_change()

    async def set_on(self) -> None:
        if not self._on:
            await self.toggle()

    async def set_off(self) -> None:
        if self._on:
            await self.toggle()

    async def handle_callback(self) -> bool:
        update = self.update
        if update is None or update.callback_data is None or update.callback_data != self.callback_data:
            return False
        await self.toggle()
        return True

    def render(self) -> KeyboardButton:
        display_text = self._on_text if self._on else self._off_text
        prefix = "✅ " if self._on else "⬜ "
        return KeyboardButton(
            text=f"{prefix}{display_text}",
            callback_data=self.callback_data,
        )

    @property
    def on(self) -> bool:
        return self._on

    @on.setter
    def on(self, value: bool) -> None:
        """Low-level state override. Does NOT fire on_change. Use set_on()/set_off()/toggle() for side-effectful changes."""
        self._on = value

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = text
        self._on_text = text or "ON"
        self._off_text = text or "OFF"
