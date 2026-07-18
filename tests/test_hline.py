import pytest
from tuican.keyboard_button import KeyboardButton
from tuican.components.hline import Hline
from tuican.components import HLine, Hline as HlineFromInit
from tuican.components.component import Component


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


class TestHLineRename:
    def test_hline_importable_from_package(self):
        """Both HLine and Hline should be importable from tuican.components"""
        assert HLine is not None
        assert HlineFromInit is not None

    def test_hline_is_alias(self):
        """Hline should be an alias for HLine"""
        assert HlineFromInit is HLine

    def test_hline_subclass_of_component(self):
        """HLine should be a subclass of Component"""
        assert issubclass(HLine, Component)

    def test_hline_instance_usable(self, mock_screen):
        """HLine instance should work identically to old Hline"""
        hline = HLine()
        hline.parent_screen = mock_screen
        result = hline.render()
        assert isinstance(result, KeyboardButton)
        assert "─" in result.text
