import pytest
from tuican.components.stepper import Stepper


class TestStepper:
    def test_init_default_values(self):
        stepper = Stepper()
        assert stepper.value == 0
        assert stepper.components

    def test_init_custom_values(self):
        stepper = Stepper(initial=5, min_value=1, max_value=10, step=2)
        assert stepper.value == 5

    def test_components_returns_three_items(self):
        stepper = Stepper()
        comps = stepper.components
        assert len(comps) == 3

    def test_get_layout_returns_one_row(self):
        stepper = Stepper()
        layout = stepper.get_layout()
        assert len(layout) == 1
        assert len(layout[0]) == 3

    @pytest.mark.asyncio
    async def test_increment_increases_value(self, mock_screen):
        stepper = Stepper(initial=5)
        stepper._inc_btn.parent_screen = mock_screen
        await stepper._increment()
        assert stepper.value == 6

    @pytest.mark.asyncio
    async def test_decrement_decreases_value(self, mock_screen):
        stepper = Stepper(initial=5)
        stepper._dec_btn.parent_screen = mock_screen
        await stepper._decrement()
        assert stepper.value == 4

    @pytest.mark.asyncio
    async def test_increment_respects_max_value(self, mock_screen):
        stepper = Stepper(initial=10, max_value=10)
        stepper._inc_btn.parent_screen = mock_screen
        await stepper._increment()
        assert stepper.value == 10

    @pytest.mark.asyncio
    async def test_decrement_respects_min_value(self, mock_screen):
        stepper = Stepper(initial=0, min_value=0)
        stepper._dec_btn.parent_screen = mock_screen
        await stepper._decrement()
        assert stepper.value == 0

    @pytest.mark.asyncio
    async def test_increment_with_step(self, mock_screen):
        stepper = Stepper(initial=0, step=5)
        stepper._inc_btn.parent_screen = mock_screen
        await stepper._increment()
        assert stepper.value == 5

    @pytest.mark.asyncio
    async def test_decrement_with_step(self, mock_screen):
        stepper = Stepper(initial=10, step=5)
        stepper._dec_btn.parent_screen = mock_screen
        await stepper._decrement()
        assert stepper.value == 5

    @pytest.mark.asyncio
    async def test_on_change_fires_on_increment(self, mock_screen):
        handler_called = False

        async def handler():
            nonlocal handler_called
            handler_called = True

        stepper = Stepper(initial=0, on_change=handler)
        stepper._inc_btn.parent_screen = mock_screen
        await stepper._increment()
        assert handler_called is True

    @pytest.mark.asyncio
    async def test_on_change_fires_on_decrement(self, mock_screen):
        handler_called = False

        async def handler():
            nonlocal handler_called
            handler_called = True

        stepper = Stepper(initial=5, on_change=handler)
        stepper._dec_btn.parent_screen = mock_screen
        await stepper._decrement()
        assert handler_called is True

    @pytest.mark.asyncio
    async def test_on_change_not_fired_when_at_bound(self, mock_screen):
        from unittest.mock import AsyncMock
        handler = AsyncMock()
        stepper = Stepper(initial=0, min_value=0, on_change=handler)
        stepper._dec_btn.parent_screen = mock_screen
        await stepper._decrement()
        handler.assert_not_called()

    def test_value_setter(self):
        stepper = Stepper(initial=0)
        stepper.value = 42
        assert stepper.value == 42
        assert stepper._display.text == "42"
