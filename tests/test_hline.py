import pytest
from tuican.keyboard_button import KeyboardButton
from tuican.components.hline import Hline


class TestHline:
    def test_init(self):
        """Hline should initialize successfully"""
        hline = Hline()
        assert hline.callback_data == hline.component_id

    def test_render(self, mock_screen):
        """render() should return a KeyboardButton with line characters"""
        hline = Hline()
        hline.parent_screen = mock_screen
        result = hline.render()

        assert isinstance(result, KeyboardButton)
        assert "─" in result.text
        assert result.callback_data == hline.callback_data

    @pytest.mark.asyncio
    async def test_handle_callback_returns_false(self, mock_screen):
        """handle_callback returns False (no-op) to satisfy bool return type"""
        hline = Hline()
        hline.parent_screen = mock_screen
        result = await hline.handle_callback()
        assert result is False
