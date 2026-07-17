import pytest
from unittest.mock import MagicMock
from tuican.components.component import Component, CallBack


class TestComponent:
    def test_callback_data_defaults_to_component_id(self):
        """callback_data should default to component_id when not provided"""
        comp = self._make_component(callback_data=None, component_id="my_id")
        assert comp.callback_data == "my_id"

    def test_callback_data_uses_explicit_value(self):
        """callback_data should use explicit value when provided"""
        comp = self._make_component(callback_data="explicit_data", component_id="my_id")
        assert comp.callback_data == "explicit_data"

    def test_callback_data_falls_back_to_id_when_empty(self):
        """callback_data should fall back to component_id when empty/None"""
        comp = self._make_component(callback_data=None)
        assert comp.callback_data == comp.component_id

    def test_component_id_auto_generated(self):
        """component_id should be auto-generated when not provided"""
        comp = self._make_component()
        assert comp.component_id is not None
        assert isinstance(comp.component_id, str)

    def test_hidden_default_false(self):
        comp = self._make_component()
        assert comp.hidden is False

    def test_hidden_setter(self):
        comp = self._make_component()
        comp.hidden = True
        assert comp.hidden is True

    def test_data_default_none(self):
        comp = self._make_component()
        assert comp.data is None

    def test_data_setter(self):
        comp = self._make_component()
        comp.data = "test_value"
        assert comp.data == "test_value"

    def test_parent_screen_default_none(self):
        comp = self._make_component()
        assert comp.parent_screen is None

    def test_parent_screen_setter(self):
        comp = self._make_component()
        screen = MagicMock()
        comp.parent_screen = screen
        assert comp.parent_screen is screen

    @pytest.mark.asyncio
    async def test_call_on_change_with_sync_handler(self, mock_update, mock_context):
        """call_on_change should work with synchronous handlers"""
        handler_called = False
        received_component = None

        def sync_handler(update, context, component):
            nonlocal handler_called, received_component
            handler_called = True
            received_component = component

        comp = self._make_component(callback_data="test_data", on_change=sync_handler)
        await comp.call_on_change(mock_update, mock_context)

        assert handler_called is True
        assert received_component is comp

    @pytest.mark.asyncio
    async def test_call_on_change_with_async_handler(self, mock_update, mock_context):
        """call_on_change should work with async handlers"""
        handler_called = False
        received_component = None

        async def async_handler(update, context, component):
            nonlocal handler_called, received_component
            handler_called = True
            received_component = component

        comp = self._make_component(callback_data="test_data", on_change=async_handler)
        await comp.call_on_change(mock_update, mock_context)

        assert handler_called is True
        assert received_component is comp

    @pytest.mark.asyncio
    async def test_call_on_change_no_handler(self, mock_update, mock_context):
        """call_on_change should not fail when no handler is set"""
        comp = self._make_component()
        await comp.call_on_change(mock_update, mock_context)
        # Should not raise

    def _make_component(self, callback_data="test_callback", component_id=None, on_change=None):
        class TestComp(Component):
            async def handle_callback(self, update, context):
                return True
            def render(self, update, context):
                from telegram import InlineKeyboardButton
                return InlineKeyboardButton("test", callback_data=self.callback_data)
        
        return TestComp(component_id=component_id, callback_data=callback_data, on_change=on_change)
