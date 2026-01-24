from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from src.components.component import CallBack, Component


class CheckBox(Component):
    def __init__(
            self,
            text: str = "",
            selected: bool = False,
            component_id: str = None,
            callback_data: str | None = None,
            on_change: CallBack | None = None,
            group: "ExclusiveCheckBoxGroup | None" = None):
        super().__init__(component_id, callback_data, on_change)
        self._text = text
        self._selected = selected
        self._group = group
        if self._group:
            self._group.add(self)

    async def check(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        previous_state = self._selected
        self._selected = True
        if previous_state != self._selected:
            await self.call_on_change(update, context, callback_data)

    async def uncheck(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        previous_state = self._selected
        self._selected = False
        if previous_state != self._selected:
            await self.call_on_change(update, context, callback_data)

    async def toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        self._selected = not self._selected
        await self.call_on_change(update, context, callback_data)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              callback_data: str | None) -> bool:
        if callback_data != self.callback_data:
            return False
        await self.toggle(update, context, callback_data)
        return True

    async def call_on_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        if self._group:
            self._group.notify(self)
            await super().call_on_change(update, context, callback_data)

    def render(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            f"{'✓ ' if self.selected else ''}{self.text}",
            callback_data=self.callback_data
        )

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text):
        self._text = text

    @property
    def selected(self):
        return self._selected


class ExclusiveCheckBoxGroup:
    def __init__(self, checkboxes: list[CheckBox] | None = None):
        self._checkboxes = [] if checkboxes is None else checkboxes

    def add(self, checkbox: CheckBox):
        self._checkboxes.append(checkbox)

    def add_all(self, checkboxes: list[CheckBox]):
        self._checkboxes.extend(checkboxes)

    def notify(self, notifier: CheckBox):
        for checkbox in self._checkboxes:
            if checkbox != notifier:
                checkbox._selected = False
