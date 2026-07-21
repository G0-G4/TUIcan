import pytest
from tuican.components.select import Select


class TestSelect:
    def test_init(self):
        select = Select(options=[("A", 1), ("B", 2)])
        assert select.selected_value is None
        assert select.current_page == 0
        assert select.page_size == 5

    def test_init_custom_page_size(self):
        select = Select(options=[("A", 1), ("B", 2)], page_size=2)
        assert select.page_size == 2

    def test_page_size_minimum_one(self):
        select = Select(options=[("A", 1)], page_size=0)
        assert select.page_size == 1

    def test_components_returns_all_buttons(self):
        select = Select(options=[("A", 1), ("B", 2)])
        comps = select.components
        assert len(comps) == 4  # 2 prev/next + 2 options

    def test_get_layout_first_page(self):
        select = Select(options=[("A", 1), ("B", 2), ("C", 3)], page_size=2)
        layout = select.get_layout()
        assert len(layout) == 3  # 2 options + 1 nav (next only)
        assert len(layout[0]) == 1  # Option A
        assert len(layout[1]) == 1  # Option B
        assert len(layout[2]) == 1  # Next only

    def test_get_layout_shows_prev_and_next(self):
        select = Select(options=[("A", 1), ("B", 2), ("C", 3), ("D", 4)], page_size=1)
        select._current_page = 1
        layout = select.get_layout()
        nav_row = layout[-1]
        assert len(nav_row) == 2  # prev + next

    def test_get_layout_last_page_no_next(self):
        select = Select(options=[("A", 1), ("B", 2)], page_size=1)
        select._current_page = 1
        layout = select.get_layout()
        nav_row = layout[-1]
        assert len(nav_row) == 1  # prev only

    @pytest.mark.asyncio
    async def test_select_option_sets_value(self, mock_screen):
        select = Select(options=[("A", 1), ("B", 2)])
        btn = select._option_btns[0]
        btn.parent_screen = mock_screen
        await btn.click()
        assert select.selected_value == 1
        assert select.selected_label == "A"

    @pytest.mark.asyncio
    async def test_select_option_triggers_on_change(self, mock_screen):
        handler_called = False
        received = None

        async def handler(component):
            nonlocal handler_called, received
            handler_called = True
            received = component

        select = Select(options=[("A", 1)], on_change=handler)
        btn = select._option_btns[0]
        btn.parent_screen = mock_screen
        await btn.click()
        assert handler_called is True
        assert received is select

    @pytest.mark.asyncio
    async def test_next_page(self, mock_screen):
        select = Select(options=[("A", 1), ("B", 2), ("C", 3)], page_size=1)
        select._next_btn.parent_screen = mock_screen
        await select._next_page()
        assert select.current_page == 1

    @pytest.mark.asyncio
    async def test_prev_page(self, mock_screen):
        select = Select(options=[("A", 1), ("B", 2)], page_size=1)
        select._current_page = 1
        select._prev_btn.parent_screen = mock_screen
        await select._prev_page()
        assert select.current_page == 0

    @pytest.mark.asyncio
    async def test_next_page_stops_at_last(self, mock_screen):
        select = Select(options=[("A", 1), ("B", 2)], page_size=1)
        select._current_page = 1
        select._next_btn.parent_screen = mock_screen
        await select._next_page()
        assert select.current_page == 1

    @pytest.mark.asyncio
    async def test_prev_page_stops_at_first(self, mock_screen):
        select = Select(options=[("A", 1), ("B", 2)], page_size=1)
        select._prev_btn.parent_screen = mock_screen
        await select._prev_page()
        assert select.current_page == 0

    def test_empty_options(self):
        select = Select(options=[])
        assert select.components == [select._prev_btn, select._next_btn]
        layout = select.get_layout()
        assert layout == []
