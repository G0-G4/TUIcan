import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes

from tuican.keyboard_button import KeyboardButton


@pytest.fixture
def mock_update():
    """Create a mock Update with callback_query"""
    update = MagicMock(spec=Update)
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.data = "test_callback_data"
    update.message = None
    return update


@pytest.fixture
def mock_context():
    """Create a mock Context"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    return context


@pytest.fixture
def mock_screen(mock_update, mock_context):
    """Create a mock Screen that provides update/context to components"""
    screen = MagicMock()
    screen.update = mock_update
    screen.context = mock_context
    screen.set_focus = AsyncMock()
    return screen


@pytest.fixture
def make_component(mock_screen):
    """Factory for creating mock components with callback_data"""
    def _make(callback_data="test_callback_data", component_id=None):
        from tuican.components.component import Component
        
        class MockComponent(Component):
            async def handle_callback(self):
                query = self.update.callback_query if self.update else None
                return query is not None and query.data == self.callback_data
            
            def render(self):
                return KeyboardButton(text="test", callback_data=self.callback_data)
        
        comp = MockComponent(component_id=component_id, callback_data=callback_data)
        comp.parent_screen = mock_screen
        return comp
    return _make
