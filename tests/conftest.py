import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, CallbackQuery, InlineKeyboardButton
from telegram.ext import ContextTypes


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
def make_component():
    """Factory for creating mock components with callback_data"""
    def _make(callback_data="test_callback_data", component_id=None):
        from tuican.components.component import Component
        
        class MockComponent(Component):
            async def handle_callback(self, update, context):
                return update.callback_query.data == self.callback_data
            
            def render(self, update, context):
                return InlineKeyboardButton("test", callback_data=self.callback_data)
        
        return MockComponent(component_id=component_id, callback_data=callback_data)
    return _make
