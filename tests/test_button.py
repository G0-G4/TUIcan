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

    def test_render_returns_inline_keyboard_button(self, mock_screen):
        """render() should return an InlineKeyboardButton with correct callback_data"""
        button = Button(text="Test", callback_data="test_cb")
        button.parent_screen = mock_screen
        result = button.render()

        assert isinstance(result, InlineKeyboardButton)
        assert result.text == "Test"
        assert result.callback_data == "test_cb"

    @pytest.mark.asyncio
    async def test_handle_callback_mismatch_returns_false(self, mock_screen):
        """handle_callback should return False when callback_data doesn't match"""
        button = Button(text="Test", callback_data="correct_data")
        button.parent_screen = mock_screen
        mock_screen.update.callback_query.data = "wrong_data"
        result = await button.handle_callback()
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_callback_match_returns_true(self, mock_screen):
        """handle_callback should return True and trigger click when callback_data matches"""
        handler_called = False
        received_component = None

        async def handler(component):
            nonlocal handler_called, received_component
            handler_called = True
            received_component = component

        button = Button(text="Test", callback_data="match_data", on_change=handler)
        button.parent_screen = mock_screen
        mock_screen.update.callback_query.data = "match_data"
        result = await button.handle_callback()

        assert result is True
        assert handler_called is True
        assert received_component is button

    @pytest.mark.asyncio
    async def test_click_triggers_on_change(self, mock_screen):
        """click() should trigger the on_change handler"""
        handler_called = False

        async def handler():
            nonlocal handler_called
            handler_called = True

        button = Button(text="Test", callback_data="test", on_change=handler)
        button.parent_screen = mock_screen
        await button.click()

        assert handler_called is True

    @pytest.mark.asyncio
    async def test_click_no_handler(self, mock_screen):
        """click() should not fail when no handler is set"""
        button = Button(text="Test")
        button.parent_screen = mock_screen
        await button.click()
        # Should not raise
