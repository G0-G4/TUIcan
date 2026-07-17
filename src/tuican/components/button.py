from telegram import InlineKeyboardButton

from .component import CallBack, Component


class Button(Component):
    def __init__(
            self,
            text: str = "",
            component_id: str | None = None,
            callback_data: str | None = None,
            on_change: CallBack | None = None):
        super().__init__(component_id, callback_data, on_change)
        self._text = text

    async def click(self) -> None:
        if self.on_change:
            await self.call_on_change()

    async def handle_callback(self) -> bool:
        query = self.update.callback_query if self.update else None
        if query is None or query.data is None or query.data != self.callback_data:
            return False
        await self.click()
        return True

    def render(self) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            self._text,
            callback_data=self.callback_data
        )

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = text
