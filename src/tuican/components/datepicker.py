import inspect
from calendar import monthcalendar
from datetime import date

from .button import Button
from .component import CallBack, Component, _invoke_callback
from .label import Label


class DatePicker:
    """Inline calendar for selecting a date.

    Renders a month grid with day buttons and month navigation.

    Example:
        self.calendar = DatePicker(on_change=self.on_date_selected)
        super().__init__(self.calendar.components)

        def get_layout(self):
            return self.calendar.get_layout()

        async def on_date_selected(self, picker):
            print(f"Selected: {picker.selected_date}")
    """

    def __init__(
        self,
        on_change: CallBack | None = None,
        initial_date: date | None = None,
    ):
        self._current_month = initial_date or date.today()
        self._selected_date: date | None = None
        self._on_change = on_change
        self._prev_btn = Button("◀", on_change=self._prev_month)
        self._next_btn = Button("▶", on_change=self._next_month)
        self._header_label = Label(self._month_label())
        self._day_buttons: list[Button] = []
        self._build_day_buttons()

    def _month_label(self) -> str:
        return self._current_month.strftime("%B %Y")

    def _build_day_buttons(self) -> None:
        self._day_buttons = []
        for day in range(1, 32):
            btn = Button(str(day), on_change=self._make_day_handler(day))
            self._day_buttons.append(btn)

    def _make_day_handler(self, day: int) -> CallBack:
        async def handler() -> None:
            try:
                selected = date(self._current_month.year, self._current_month.month, day)
            except ValueError:
                return
            self._selected_date = selected
            if self._on_change:
                result = _invoke_callback(self._on_change, None, self)
                if inspect.isawaitable(result):
                    await result
        return handler

    async def _prev_month(self) -> None:
        year = self._current_month.year
        month = self._current_month.month - 1
        if month < 1:
            month = 12
            year -= 1
        self._current_month = date(year, month, 1)
        self._header_label.text = self._month_label()

    async def _next_month(self) -> None:
        year = self._current_month.year
        month = self._current_month.month + 1
        if month > 12:
            month = 1
            year += 1
        self._current_month = date(year, month, 1)
        self._header_label.text = self._month_label()

    @property
    def selected_date(self) -> date | None:
        return self._selected_date

    @property
    def components(self) -> list[Component]:
        result: list[Component] = [self._prev_btn, self._header_label, self._next_btn]
        result.extend(self._day_buttons)
        return result

    def get_layout(self) -> list[list[Component]]:
        rows: list[list[Component]] = []
        # Header row
        rows.append([self._prev_btn, self._header_label, self._next_btn])
        # Day names row (static label)
        rows.append([Label("Mo Tu We Th Fr Sa Su")])
        # Calendar grid
        cal = monthcalendar(self._current_month.year, self._current_month.month)
        for week in cal:
            row: list[Component] = []
            for day in week:
                if day == 0:
                    row.append(Label("  "))
                else:
                    row.append(self._day_buttons[day - 1])
            rows.append(row)
        return rows
