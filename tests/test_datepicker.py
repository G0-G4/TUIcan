from datetime import date

import pytest
from tuican.components.datepicker import DatePicker


class TestDatePicker:
    def test_init_default(self):
        picker = DatePicker()
        assert picker.selected_date is None

    def test_init_with_initial_date(self):
        d = date(2024, 6, 15)
        picker = DatePicker(initial_date=d)
        assert picker._current_month == d

    def test_components_returns_all_buttons(self):
        picker = DatePicker()
        comps = picker.components
        assert len(comps) == 34  # 3 header + 31 day buttons

    def test_get_layout_structure(self):
        picker = DatePicker(initial_date=date(2024, 6, 1))
        layout = picker.get_layout()
        assert len(layout) >= 6  # header + day names + 4-6 weeks
        assert len(layout[0]) == 3  # prev, header, next
        assert len(layout[1]) == 1  # day names label

    def test_month_label(self):
        picker = DatePicker(initial_date=date(2024, 6, 1))
        assert picker._month_label() == "June 2024"

    @pytest.mark.asyncio
    async def test_select_valid_day(self, mock_screen):
        picker = DatePicker(initial_date=date(2024, 6, 1))
        btn = picker._day_buttons[14]  # Day 15
        btn.parent_screen = mock_screen
        await btn.click()
        assert picker.selected_date == date(2024, 6, 15)

    @pytest.mark.asyncio
    async def test_select_invalid_day_noop(self, mock_screen):
        picker = DatePicker(initial_date=date(2024, 2, 1))  # Feb, no day 30
        btn = picker._day_buttons[29]  # Day 30
        btn.parent_screen = mock_screen
        await btn.click()
        assert picker.selected_date is None

    @pytest.mark.asyncio
    async def test_select_triggers_on_change(self, mock_screen):
        handler_called = False

        async def handler():
            nonlocal handler_called
            handler_called = True

        picker = DatePicker(initial_date=date(2024, 6, 1), on_change=handler)
        btn = picker._day_buttons[0]  # Day 1
        btn.parent_screen = mock_screen
        await btn.click()
        assert handler_called is True

    @pytest.mark.asyncio
    async def test_prev_month(self, mock_screen):
        picker = DatePicker(initial_date=date(2024, 6, 1))
        picker._prev_btn.parent_screen = mock_screen
        await picker._prev_month()
        assert picker._current_month == date(2024, 5, 1)
        assert picker._month_label() == "May 2024"

    @pytest.mark.asyncio
    async def test_next_month(self, mock_screen):
        picker = DatePicker(initial_date=date(2024, 6, 1))
        picker._next_btn.parent_screen = mock_screen
        await picker._next_month()
        assert picker._current_month == date(2024, 7, 1)
        assert picker._month_label() == "July 2024"

    @pytest.mark.asyncio
    async def test_prev_month_year_wrap(self, mock_screen):
        picker = DatePicker(initial_date=date(2024, 1, 1))
        picker._prev_btn.parent_screen = mock_screen
        await picker._prev_month()
        assert picker._current_month == date(2023, 12, 1)

    @pytest.mark.asyncio
    async def test_next_month_year_wrap(self, mock_screen):
        picker = DatePicker(initial_date=date(2024, 12, 1))
        picker._next_btn.parent_screen = mock_screen
        await picker._next_month()
        assert picker._current_month == date(2025, 1, 1)
