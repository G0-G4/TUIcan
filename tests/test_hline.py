import pytest
from telegram import InlineKeyboardButton
from tuican.components.hline import Hline


class TestHline:
    def test_init(self):
        """Hline should initialize successfully"""
        hline = Hline()
        assert hline.callback_data == hline.component_id

    def test_render(self, mock_update, mock_context):
        """render() should return an InlineKeyboardButton with line characters"""
        hline = Hline()
        result = hline.render(mock_update, mock_context)

        assert isinstance(result, InlineKeyboardButton)
        assert "─" in result.text
        assert result.callback_data == hline.callback_data

    @pytest.mark.asyncio
    async def test_handle_callback_returns_false(self, mock_update, mock_context):
        """handle_callback returns False (no-op) to satisfy bool return type"""
        hline = Hline()
        result = await hline.handle_callback(mock_update, mock_context)
        assert result is False
