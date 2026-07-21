import inspect

from .button import Button
from .component import CallBack, Component, _invoke_callback


class Select[T]:
    """Paginated dropdown selector for choosing from a list of options.

    Manages option buttons and prev/next navigation automatically.

    Example:
        self.city = Select(
            options=[("Moscow", "moscow"), ("SPb", "spb"), ("Kazan", "kazan")],
            page_size=2,
            on_change=self.on_city_selected,
        )
        super().__init__(self.city.components)

        def get_layout(self):
            return self.city.get_layout()

        async def on_city_selected(self, select):
            print(f"Selected: {select.selected_value}")
    """

    def __init__(
        self,
        options: list[tuple[str, T]],
        page_size: int = 5,
        on_change: CallBack | None = None,
    ):
        self._options: list[tuple[str, T]] = list(options)
        self._page_size = max(1, page_size)
        self._current_page = 0
        self._selected_value: T | None = None
        self._selected_label: str | None = None
        self._on_change = on_change
        self._prev_btn = Button("◀", on_change=self._prev_page)
        self._next_btn = Button("▶", on_change=self._next_page)
        self._option_btns: list[Button] = []
        self._build_option_buttons()

    def _build_option_buttons(self) -> None:
        self._option_btns = []
        for label, value in self._options:
            btn = Button(label, on_change=self._make_handler(value, label))
            self._option_btns.append(btn)

    def _make_handler(self, value: T, label: str) -> CallBack:
        async def handler() -> None:
            self._selected_value = value
            self._selected_label = label
            if self._on_change:
                result = _invoke_callback(self._on_change, None, self)
                if inspect.isawaitable(result):
                    await result
        return handler

    async def _prev_page(self) -> None:
        if self._current_page > 0:
            self._current_page -= 1
            # Screen will re-render because Button.handle_callback returns True

    async def _next_page(self) -> None:
        max_page = max(0, (len(self._options) - 1) // self._page_size)
        if self._current_page < max_page:
            self._current_page += 1
            # Screen will re-render because Button.handle_callback returns True

    @property
    def selected_value(self) -> T | None:
        return self._selected_value

    @property
    def selected_label(self) -> str | None:
        return self._selected_label

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def page_size(self) -> int:
        return self._page_size

    @property
    def components(self) -> list[Component]:
        result: list[Component] = [self._prev_btn, self._next_btn]
        result.extend(self._option_btns)
        return result

    def get_layout(self) -> list[list[Component]]:
        start = self._current_page * self._page_size
        end = min(start + self._page_size, len(self._option_btns))
        rows: list[list[Component]] = []
        for i in range(start, end):
            rows.append([self._option_btns[i]])
        nav_row: list[Component] = []
        if self._current_page > 0:
            nav_row.append(self._prev_btn)
        if end < len(self._option_btns):
            nav_row.append(self._next_btn)
        if nav_row:
            rows.append(nav_row)
        return rows
