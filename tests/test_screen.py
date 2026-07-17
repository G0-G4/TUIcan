import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from tuican.components import Screen, Input


class TwoInputScreen(Screen):
    def __init__(self):
        self.input_a = Input[str](validation_function=lambda x: x, text="A:", callback_data="a")
        self.input_b = Input[int](validation_function=int, text="B:", callback_data="b")
        super().__init__([self.input_a, self.input_b], message="test")

    async def get_layout(self, update, context):
        return [
            [self.input_a.render(update, context)],
            [self.input_b.render(update, context)],
        ]


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.callback_query = None
    update.message = None
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    return context


class TestScreenFocus:
    @pytest.mark.asyncio
    async def test_set_focus_deactivates_other_inputs(self, mock_update, mock_context):
        """set_focus should deactivate all other active MessageHandlingComponents"""
        screen = TwoInputScreen()

        await screen.input_b.activate(mock_update, mock_context)
        assert screen.input_b.active is True

        await screen.set_focus(screen.input_a, mock_update, mock_context)

        assert screen.input_a.active is False  # input_a was not active, stays inactive
        assert screen.input_b.active is False    # input_b was active but not focused, so it was deactivated

    @pytest.mark.asyncio
    async def test_activate_input_deactivates_other_active_input(self, mock_update, mock_context):
        """Activating one input should automatically deactivate another active input via set_focus"""
        screen = TwoInputScreen()

        await screen.input_b.activate(mock_update, mock_context)
        assert screen.input_b.active is True

        await screen.input_a.activate(mock_update, mock_context)

        assert screen.input_a.active is True
        assert screen.input_b.active is False

    @pytest.mark.asyncio
    async def test_toggle_input_deactivates_other_active_input(self, mock_update, mock_context):
        """Toggling one input on should deactivate another active input via set_focus"""
        screen = TwoInputScreen()

        await screen.input_b.activate(mock_update, mock_context)
        assert screen.input_b.active is True

        await screen.input_a.toggle(mock_update, mock_context)

        assert screen.input_a.active is True
        assert screen.input_b.active is False

    @pytest.mark.asyncio
    async def test_parent_screen_set_on_registration(self, mock_update, mock_context):
        """Components should have parent_screen set when registered to a Screen"""
        screen = TwoInputScreen()

        assert screen.input_a.parent_screen is screen
        assert screen.input_b.parent_screen is screen

    @pytest.mark.asyncio
    async def test_set_focus_ignores_inactive_components(self, mock_update, mock_context):
        """set_focus should not call deactivate on components that are already inactive"""
        screen = TwoInputScreen()

        screen.input_a.deactivate = AsyncMock()
        screen.input_b.deactivate = AsyncMock()

        await screen.set_focus(screen.input_a, mock_update, mock_context)

        screen.input_a.deactivate.assert_not_awaited()
        screen.input_b.deactivate.assert_not_awaited()
