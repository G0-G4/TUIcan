import pytest
from unittest.mock import AsyncMock, MagicMock

from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate, UpdateKind


@pytest.fixture
def mock_update():
    """Create a TuicanUpdate for callback scenarios"""
    return TuicanUpdate.from_callback(
        user_id=123,
        chat_id=456,
        callback_data="test_callback_data",
        message_id=1,
    )


@pytest.fixture
def mock_message_update():
    """Create a TuicanUpdate for message scenarios"""
    return TuicanUpdate.from_message(
        user_id=123,
        chat_id=456,
        message_text="hello world",
        message_id=2,
    )


@pytest.fixture
def mock_screen(mock_update):
    """Create a mock Screen that provides update to components"""
    screen = MagicMock()
    screen.update = mock_update
    screen.set_focus = AsyncMock()
    return screen


@pytest.fixture
def make_component(mock_screen):
    """Factory for creating mock components with callback_data"""
    def _make(callback_data="test_callback_data", component_id=None):
        from tuican.components.component import Component
        
        class MockComponent(Component):
            async def handle_callback(self):
                if self.update is None:
                    return False
                return self.update.callback_data == self.callback_data
            
            def render(self):
                return KeyboardButton(text="test", callback_data=self.callback_data)
        
        comp = MockComponent(component_id=component_id, callback_data=callback_data)
        comp.parent_screen = mock_screen
        return comp
    return _make
