import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import InlineKeyboardButton
from tuican.components.input import Input


class TestInput:
    def test_init_default_values(self):
        """Input should initialize with default values"""
        inp = Input[str](validation_function=lambda x: x)
        assert inp.text == ""
        assert inp.value is None
        assert inp.active is False
        assert inp.callback_data == inp.component_id

    def test_init_with_callback_data(self):
        """Input should use explicit callback_data"""
        inp = Input[str](validation_function=lambda x: x, callback_data="custom")
        assert inp.callback_data == "custom"

    def test_text_setter(self):
        """Input text should be changeable"""
        inp = Input[str](validation_function=lambda x: x, text="Old")
        inp.text = "New"
        assert inp.text == "New"

    def test_value_setter(self):
        """Input value should be changeable"""
        inp = Input[str](validation_function=lambda x: x)
        inp.value = "test"
        assert inp.value == "test"

    def test_render_inactive(self, mock_update, mock_context):
        """render() should show inactive state"""
        inp = Input[str](validation_function=lambda x: x, text="Name:")
        result = inp.render(mock_update, mock_context)

        assert isinstance(result, InlineKeyboardButton)
        assert "Name:" in result.text
        assert "Введите" not in result.text

    def test_render_active(self, mock_update, mock_context):
        """render() should show active state with prompt"""
        inp = Input[str](validation_function=lambda x: x, text="Name:")
        inp._active = True
        result = inp.render(mock_update, mock_context)

        assert isinstance(result, InlineKeyboardButton)
        assert "Введите" in result.text
        assert "Name:" in result.text

    def test_render_with_value(self, mock_update, mock_context):
        """render() should display current value"""
        inp = Input[int](validation_function=int, text="Age:", value=25)
        result = inp.render(mock_update, mock_context)

        assert isinstance(result, InlineKeyboardButton)
        assert "25" in result.text

    @pytest.mark.asyncio
    async def test_handle_callback_mismatch_returns_false(self, mock_update, mock_context):
        """handle_callback should return False when callback_data doesn't match"""
        inp = Input[str](validation_function=lambda x: x, callback_data="correct")
        mock_update.callback_query.data = "wrong"
        result = await inp.handle_callback(mock_update, mock_context)
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_callback_match_activates(self, mock_update, mock_context):
        """handle_callback should activate input when callback_data matches"""
        inp = Input[str](validation_function=lambda x: x, callback_data="match")
        assert inp.active is False

        mock_update.callback_query.data = "match"
        result = await inp.handle_callback(mock_update, mock_context)

        assert result is True
        assert inp.active is True

    @pytest.mark.asyncio
    async def test_activate_sets_active(self, mock_update, mock_context):
        """activate() should set active to True"""
        inp = Input[str](validation_function=lambda x: x)
        assert inp.active is False

        await inp.activate(mock_update, mock_context)
        assert inp.active is True

    @pytest.mark.asyncio
    async def test_deactivate_sets_inactive(self, mock_update, mock_context):
        """deactivate() should set active to False"""
        inp = Input[str](validation_function=lambda x: x)
        inp._active = True

        await inp.deactivate(mock_update, mock_context)
        assert inp.active is False

    @pytest.mark.asyncio
    async def test_toggle_flips_state(self, mock_update, mock_context):
        """toggle() should flip active state"""
        inp = Input[str](validation_function=lambda x: x)
        assert inp.active is False

        await inp.toggle(mock_update, mock_context)
        assert inp.active is True

        await inp.toggle(mock_update, mock_context)
        assert inp.active is False

    @pytest.mark.asyncio
    async def test_handle_message_when_inactive(self, mock_update, mock_context):
        """handle_message should return False when input is inactive"""
        inp = Input[str](validation_function=lambda x: x)
        mock_update.message = MagicMock()
        mock_update.message.text = "hello"

        result = await inp.handle_message(mock_update, mock_context)
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_message_no_text(self, mock_update, mock_context):
        """handle_message should return False when message has no text"""
        inp = Input[str](validation_function=lambda x: x)
        inp._active = True
        mock_update.message = MagicMock()
        mock_update.message.text = None

        result = await inp.handle_message(mock_update, mock_context)
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_message_validates_and_sets_value(self, mock_update, mock_context):
        """handle_message should validate input and set value"""
        inp = Input[int](validation_function=int, value=None)
        inp._active = True
        mock_update.message = MagicMock()
        mock_update.message.text = "42"

        result = await inp.handle_message(mock_update, mock_context)

        assert result is True
        assert inp.value == 42
        assert inp.active is False

    @pytest.mark.asyncio
    async def test_handle_message_triggers_on_change(self, mock_update, mock_context):
        """handle_message should trigger on_change; handler reads value from component"""
        handler_called = False
        received_component = None

        async def handler(update, context, component):
            nonlocal handler_called, received_component
            handler_called = True
            received_component = component

        inp = Input[int](validation_function=int, on_change=handler)
        inp._active = True
        mock_update.message = MagicMock()
        mock_update.message.text = "42"

        await inp.handle_message(mock_update, mock_context)

        assert handler_called is True
        assert received_component is inp
        assert received_component.value == 42

    def test_validate_input_with_function(self):
        """validate_input should apply validation function"""
        inp = Input[int](validation_function=int)
        result = inp.validate_input("42")
        assert result == 42

    def test_validate_input_without_function(self):
        """validate_input should return raw text when no function provided"""
        inp = Input[str](validation_function=lambda x: x)
        result = inp.validate_input("hello")
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_activate_calls_set_focus_on_parent_screen(self, mock_update, mock_context):
        """activate() should call parent_screen.set_focus to enforce single active input"""
        inp = Input[str](validation_function=lambda x: x)
        mock_screen = MagicMock()
        mock_screen.set_focus = AsyncMock()
        inp.parent_screen = mock_screen

        await inp.activate(mock_update, mock_context)

        assert inp.active is True
        mock_screen.set_focus.assert_awaited_once_with(inp, mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_toggle_on_calls_set_focus_on_parent_screen(self, mock_update, mock_context):
        """toggle() turning on should call parent_screen.set_focus"""
        inp = Input[str](validation_function=lambda x: x)
        mock_screen = MagicMock()
        mock_screen.set_focus = AsyncMock()
        inp.parent_screen = mock_screen

        await inp.toggle(mock_update, mock_context)

        assert inp.active is True
        mock_screen.set_focus.assert_awaited_once_with(inp, mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_toggle_off_does_not_call_set_focus(self, mock_update, mock_context):
        """toggle() turning off should not call parent_screen.set_focus"""
        inp = Input[str](validation_function=lambda x: x)
        inp._active = True
        mock_screen = MagicMock()
        mock_screen.set_focus = AsyncMock()
        inp.parent_screen = mock_screen

        await inp.toggle(mock_update, mock_context)

        assert inp.active is False
        mock_screen.set_focus.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_without_parent_screen_does_not_raise(self, mock_update, mock_context):
        """activate() should work when parent_screen is None (isolated component)"""
        inp = Input[str](validation_function=lambda x: x)
        assert inp.parent_screen is None

        await inp.activate(mock_update, mock_context)
        assert inp.active is True
