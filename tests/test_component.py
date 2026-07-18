import pytest
from unittest.mock import MagicMock
from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate
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
    async def test_call_on_change_with_sync_handler(self, mock_screen):
        """call_on_change should work with synchronous handlers"""
        handler_called = False
        received_component = None

        def sync_handler(component):
            nonlocal handler_called, received_component
            handler_called = True
            received_component = component

        comp = self._make_component(callback_data="test_data", on_change=sync_handler)
        comp.parent_screen = mock_screen
        await comp.call_on_change()

        assert handler_called is True
        assert received_component is comp

    @pytest.mark.asyncio
    async def test_call_on_change_with_async_handler(self, mock_screen):
        """call_on_change should work with async handlers"""
        handler_called = False
        received_component = None

        async def async_handler(component):
            nonlocal handler_called, received_component
            handler_called = True
            received_component = component

        comp = self._make_component(callback_data="test_data", on_change=async_handler)
        comp.parent_screen = mock_screen
        await comp.call_on_change()

        assert handler_called is True
        assert received_component is comp

    @pytest.mark.asyncio
    async def test_call_on_change_no_handler(self, mock_screen):
        """call_on_change should not fail when no handler is set"""
        comp = self._make_component()
        comp.parent_screen = mock_screen
        await comp.call_on_change()
        # Should not raise

    @pytest.mark.asyncio
    async def test_call_on_change_with_update_handler(self, mock_screen):
        """call_on_change should pass update to handlers that accept (update)"""
        received_update = None

        def handler(update):
            nonlocal received_update
            received_update = update

        comp = self._make_component(on_change=handler)
        comp.parent_screen = mock_screen
        await comp.call_on_change()

        assert received_update is mock_screen.update

    @pytest.mark.asyncio
    async def test_call_on_change_with_update_and_component_handler(self, mock_screen):
        """call_on_change should pass (update, component) to handlers that accept both"""
        received_update = None
        received_component = None

        def handler(update, component):
            nonlocal received_update, received_component
            received_update = update
            received_component = component

        comp = self._make_component(on_change=handler)
        comp.parent_screen = mock_screen
        await comp.call_on_change()

        assert received_update is mock_screen.update
        assert received_component is comp

    @pytest.mark.asyncio
    async def test_call_on_change_with_zero_arg_handler(self, mock_screen):
        """call_on_change should call handlers that accept no arguments"""
        handler_called = False

        def handler():
            nonlocal handler_called
            handler_called = True

        comp = self._make_component(on_change=handler)
        comp.parent_screen = mock_screen
        await comp.call_on_change()

        assert handler_called is True

    def test_update_property_type(self, mock_screen):
        """update property should return TuicanUpdate from parent_screen"""
        comp = self._make_component()
        comp.parent_screen = mock_screen
        assert comp.update is mock_screen.update

    def test_update_property_none_when_no_parent(self):
        """update property should be None when no parent_screen is set"""
        comp = self._make_component()
        assert comp.update is None

    def test_context_property_removed(self):
        """Component should not have a context property"""
        comp = self._make_component()
        assert not hasattr(type(comp), 'context') or not isinstance(getattr(type(comp), 'context', None), property)

    def _make_component(self, callback_data="test_callback", component_id=None, on_change=None):
        class TestComp(Component):
            async def handle_callback(self):
                if self.update is None:
                    return False
                return self.update.callback_data == self.callback_data
            def render(self):
                return KeyboardButton(text="test", callback_data=self.callback_data)
        
        return TestComp(component_id=component_id, callback_data=callback_data, on_change=on_change)
