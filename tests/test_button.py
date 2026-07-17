import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import InlineKeyboardButton
from tuican.components.button import Button


class TestButton:
    def test_init_default_values(self):
        """Button should initialize with default values"""
        button = Button()
        assert button.text == ""
        assert button.callback_data == button.component_id

    def test_init_with_callback_data(self):
        """Button should use explicit callback_data"""
        button = Button(text="Click me", callback_data="custom_data")
        assert button.text == "Click me"
        assert button.callback_data == "custom_data"

    def test_text_setter(self):
        """Button text should be changeable"""
        button = Button(text="Old")
        button.text = "New"
        assert button.text == "New"

    def test_render_returns_inline_keyboard_button(self, mock_update, mock_context):
        """render() should return an InlineKeyboardButton with correct callback_data"""
        button = Button(text="Test", callback_data="test_cb")
        result = button.render(mock_update, mock_context)

        assert isinstance(result, InlineKeyboardButton)
        assert result.text == "Test"
        assert result.callback_data == "test_cb"

    @pytest.mark.asyncio
    async def test_handle_callback_mismatch_returns_false(self, mock_update, mock_context):
        """handle_callback should return False when callback_data doesn't match"""
        button = Button(text="Test", callback_data="correct_data")
        mock_update.callback_query.data = "wrong_data"
        result = await button.handle_callback(mock_update, mock_context)
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_callback_match_returns_true(self, mock_update, mock_context):
        """handle_callback should return True and trigger click when callback_data matches"""
        handler_called = False
        received_component = None

        async def handler(update, context, component):
            nonlocal handler_called, received_component
            handler_called = True
            received_component = component

        button = Button(text="Test", callback_data="match_data", on_change=handler)
        mock_update.callback_query.data = "match_data"
        result = await button.handle_callback(mock_update, mock_context)

        assert result is True
        assert handler_called is True
        assert received_component is button

    @pytest.mark.asyncio
    async def test_click_triggers_on_change(self, mock_update, mock_context):
        """click() should trigger the on_change handler"""
        handler_called = False

        async def handler(update, context, component):
            nonlocal handler_called
            handler_called = True

        button = Button(text="Test", callback_data="test", on_change=handler)
        await button.click(mock_update, mock_context)

        assert handler_called is True

    @pytest.mark.asyncio
    async def test_click_no_handler(self, mock_update, mock_context):
        """click() should not fail when no handler is set"""
        button = Button(text="Test")
        await button.click(mock_update, mock_context)
        # Should not raise
