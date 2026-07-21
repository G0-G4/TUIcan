import inspect

from .button import Button
from .component import CallBack, Component, _invoke_callback
from .label import Label


class PageNavigator:
    """Pagination controls with prev/next buttons and a page indicator label.

    Use this helper to add pagination navigation to any screen layout.

    Example:
        self.nav = PageNavigator(total_pages=5, on_change=self.on_page_change)
        super().__init__(self.nav.components)

        def get_layout(self):
            content_rows = self._get_content_for_page(self.nav.current_page)
            return content_rows + self.nav.get_layout()
    """

    def __init__(
        self,
        total_pages: int,
        page_size: int | None = None,
        on_change: CallBack | None = None,
    ):
        self._total_pages = max(1, total_pages)
        self._page_size = page_size
        self._current_page = 0
        self._on_change = on_change
        self._prev_btn = Button("◀", on_change=self._prev_page)
        self._next_btn = Button("▶", on_change=self._next_page)
        self._info_label = Label(self._page_label())

    def _page_label(self) -> str:
        return f"📄 {self._current_page + 1} / {self._total_pages}"

    async def _prev_page(self) -> None:
        if self._current_page > 0:
            self._current_page -= 1
            self._info_label.text = self._page_label()
            if self._on_change:
                result = _invoke_callback(self._on_change, None, self)
                if inspect.isawaitable(result):
                    await result

    async def _next_page(self) -> None:
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self._info_label.text = self._page_label()
            if self._on_change:
                result = _invoke_callback(self._on_change, None, self)
                if inspect.isawaitable(result):
                    await result

    @property
    def current_page(self) -> int:
        return self._current_page

    @current_page.setter
    def current_page(self, page: int) -> None:
        self._current_page = max(0, min(page, self._total_pages - 1))
        self._info_label.text = self._page_label()

    @property
    def total_pages(self) -> int:
        return self._total_pages

    @total_pages.setter
    def total_pages(self, value: int) -> None:
        self._total_pages = max(1, value)
        self._current_page = min(self._current_page, self._total_pages - 1)
        self._info_label.text = self._page_label()

    @property
    def components(self) -> list[Component]:
        return [self._prev_btn, self._info_label, self._next_btn]

    def get_layout(self) -> list[list[Component]]:
        return [[self._prev_btn, self._info_label, self._next_btn]]
