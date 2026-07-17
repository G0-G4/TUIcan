from ..keyboard_button import KeyboardButton
from .component import CallBack, Component


class CheckBox(Component):
    def __init__(
            self,
            text: str = "",
            selected: bool = False,
            component_id: str | None = None,
            callback_data: str | None = None,
            on_change: CallBack | None = None,
            group: "ExclusiveCheckBoxGroup | None" = None):
        super().__init__(component_id, callback_data, on_change)
        self._text = text
        self._selected = selected
        self._group = group
        if self._group:
            self._group.add(self)

    async def check(self) -> None:
        previous_state = self._selected
        self._selected = True
        if previous_state != self._selected:
            await self.call_on_change()

    async def uncheck(self) -> None:
        previous_state = self._selected
        self._selected = False
        if previous_state != self._selected:
            await self.call_on_change()

    async def toggle(self) -> None:
        self._selected = not self._selected
        await self.call_on_change()

    async def handle_callback(self) -> bool:
        query = self.update.callback_query if self.update else None
        if query is None or query.data is None or query.data != self.callback_data:
            return False
        await self.toggle()
        return True

    async def call_on_change(self) -> None:
        if self._group:
            self._group.notify(self)
        await super().call_on_change()

    def render(self) -> KeyboardButton:
        return KeyboardButton(
            text=f"{'✓ ' if self.selected else ''}{self.text}",
            callback_data=self.callback_data
        )

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = text

    @property
    def selected(self) -> bool:
        return self._selected


class ExclusiveCheckBoxGroup:
    def __init__(self, checkboxes: list[CheckBox] | None = None, sticky: bool = False):
        self._checkboxes = [] if checkboxes is None else checkboxes
        self._sticky = sticky

    def add(self, checkbox: CheckBox) -> None:
        self._checkboxes.append(checkbox)

    def add_all(self, checkboxes: list[CheckBox]) -> None:
        self._checkboxes.extend(checkboxes)

    def notify(self, notifier: CheckBox) -> None:
        if self._sticky and not notifier.selected:
            notifier._selected = True
            return
        for checkbox in self._checkboxes:
            if checkbox != notifier:
                checkbox._selected = False

    def get_selected(self) -> CheckBox | None:
        for checkbox in self._checkboxes:
            if checkbox.selected:
                return checkbox
        return None
