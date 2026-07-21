import pytest
from tuican.components.pagination import PageNavigator


class TestPageNavigator:
    def test_init_default_values(self):
        nav = PageNavigator(total_pages=5)
        assert nav.current_page == 0
        assert nav.total_pages == 5
        assert nav.components

    def test_init_total_pages_at_least_one(self):
        nav = PageNavigator(total_pages=0)
        assert nav.total_pages == 1

    def test_components_returns_three_items(self):
        nav = PageNavigator(total_pages=5)
        comps = nav.components
        assert len(comps) == 3

    def test_get_layout_returns_one_row(self):
        nav = PageNavigator(total_pages=5)
        layout = nav.get_layout()
        assert len(layout) == 1
        assert len(layout[0]) == 3

    def test_page_label_format(self):
        nav = PageNavigator(total_pages=5)
        assert nav._info_label.text == "📄 1 / 5"

    @pytest.mark.asyncio
    async def test_next_page_increments(self, mock_screen):
        nav = PageNavigator(total_pages=5)
        nav._next_btn.parent_screen = mock_screen
        await nav._next_page()
        assert nav.current_page == 1
        assert nav._info_label.text == "📄 2 / 5"

    @pytest.mark.asyncio
    async def test_next_page_stops_at_last(self, mock_screen):
        nav = PageNavigator(total_pages=3)
        nav._next_btn.parent_screen = mock_screen
        await nav._next_page()
        await nav._next_page()
        await nav._next_page()
        assert nav.current_page == 2

    @pytest.mark.asyncio
    async def test_prev_page_decrements(self, mock_screen):
        nav = PageNavigator(total_pages=5)
        nav.current_page = 2
        nav._prev_btn.parent_screen = mock_screen
        await nav._prev_page()
        assert nav.current_page == 1
        assert nav._info_label.text == "📄 2 / 5"

    @pytest.mark.asyncio
    async def test_prev_page_stops_at_first(self, mock_screen):
        nav = PageNavigator(total_pages=5)
        nav._prev_btn.parent_screen = mock_screen
        await nav._prev_page()
        assert nav.current_page == 0

    @pytest.mark.asyncio
    async def test_on_change_fires_on_next(self, mock_screen):
        handler_called = False

        async def handler():
            nonlocal handler_called
            handler_called = True

        nav = PageNavigator(total_pages=5, on_change=handler)
        nav._next_btn.parent_screen = mock_screen
        await nav._next_page()
        assert handler_called is True

    @pytest.mark.asyncio
    async def test_on_change_fires_on_prev(self, mock_screen):
        handler_called = False

        async def handler():
            nonlocal handler_called
            handler_called = True

        nav = PageNavigator(total_pages=5, on_change=handler)
        nav.current_page = 2
        nav._prev_btn.parent_screen = mock_screen
        await nav._prev_page()
        assert handler_called is True

    @pytest.mark.asyncio
    async def test_on_change_not_fired_when_at_bound(self, mock_screen):
        from unittest.mock import AsyncMock
        handler = AsyncMock()
        nav = PageNavigator(total_pages=3, on_change=handler)
        nav.current_page = 2
        nav._next_btn.parent_screen = mock_screen
        await nav._next_page()
        handler.assert_not_called()

    def test_current_page_setter(self):
        nav = PageNavigator(total_pages=5)
        nav.current_page = 3
        assert nav.current_page == 3
        assert nav._info_label.text == "📄 4 / 5"

    def test_current_page_setter_clamps(self):
        nav = PageNavigator(total_pages=5)
        nav.current_page = 100
        assert nav.current_page == 4
        nav.current_page = -10
        assert nav.current_page == 0

    def test_total_pages_setter(self):
        nav = PageNavigator(total_pages=5)
        nav.total_pages = 3
        assert nav.total_pages == 3
        assert nav.current_page == 0

    def test_total_pages_setter_adjusts_current_page(self):
        nav = PageNavigator(total_pages=10)
        nav.current_page = 9
        nav.total_pages = 5
        assert nav.current_page == 4
