import asyncio
import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock

from telegram import Update
from telegram.ext import ContextTypes

from tuican.components.component import _invoke_callback, Component, KeyboardButton


class DummyComponent(Component):
    async def handle_callback(self):
        return True

    def render(self):
        return KeyboardButton(text="dummy", callback_data=self.callback_data)


class TestInvokeCallback:
    @pytest.fixture
    def mock_update(self):
        return MagicMock(spec=Update)

    @pytest.fixture
    def mock_context(self):
        return MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.fixture
    def dummy_component(self):
        return DummyComponent(component_id="dummy")

    def test_zero_params(self, mock_update, mock_context, dummy_component):
        called = False

        def callback():
            nonlocal called
            called = True

        result = _invoke_callback(callback, mock_update, mock_context, dummy_component)
        assert called is True
        assert result is None

    def test_one_param(self, mock_update, mock_context, dummy_component):
        received = None

        def callback(component):
            nonlocal received
            received = component

        result = _invoke_callback(callback, mock_update, mock_context, dummy_component)
        assert received is dummy_component
        assert result is None

    def test_two_params(self, mock_update, mock_context, dummy_component):
        received_update = None
        received_context = None

        def callback(update, context):
            nonlocal received_update, received_context
            received_update = update
            received_context = context

        result = _invoke_callback(callback, mock_update, mock_context, dummy_component)
        assert received_update is mock_update
        assert received_context is mock_context
        assert result is None

    def test_three_params(self, mock_update, mock_context, dummy_component):
        received_update = None
        received_context = None
        received_component = None

        def callback(update, context, component):
            nonlocal received_update, received_context, received_component
            received_update = update
            received_context = context
            received_component = component

        result = _invoke_callback(callback, mock_update, mock_context, dummy_component)
        assert received_update is mock_update
        assert received_context is mock_context
        assert received_component is dummy_component
        assert result is None

    def test_more_than_three_params_raises(self, mock_update, mock_context, dummy_component):
        def callback(a, b, c, d):
            pass

        with pytest.raises(TypeError, match="must accept 0-3 positional parameters"):
            _invoke_callback(callback, mock_update, mock_context, dummy_component)

    def test_async_callback_returns_coroutine(self, mock_update, mock_context, dummy_component):
        async def async_callback(component):
            return "done"

        result = _invoke_callback(async_callback, mock_update, mock_context, dummy_component)
        assert inspect.isawaitable(result)
        assert asyncio.run(result) == "done"

    def test_async_callback_zero_params(self, mock_update, mock_context, dummy_component):
        async def async_callback():
            return "done"

        result = _invoke_callback(async_callback, mock_update, mock_context, dummy_component)
        assert inspect.isawaitable(result)
        assert asyncio.run(result) == "done"

    def test_async_callback_two_params(self, mock_update, mock_context, dummy_component):
        async def async_callback(update, context):
            return "done"

        result = _invoke_callback(async_callback, mock_update, mock_context, dummy_component)
        assert inspect.isawaitable(result)
        assert asyncio.run(result) == "done"

    def test_async_callback_three_params(self, mock_update, mock_context, dummy_component):
        async def async_callback(update, context, component):
            return "done"

        result = _invoke_callback(async_callback, mock_update, mock_context, dummy_component)
        assert inspect.isawaitable(result)
        assert asyncio.run(result) == "done"

    def test_ignores_var_args(self, mock_update, mock_context, dummy_component):
        called = False

        def callback(*args):
            nonlocal called
            called = True

        result = _invoke_callback(callback, mock_update, mock_context, dummy_component)
        assert called is True
        assert result is None

    def test_ignores_kwargs(self, mock_update, mock_context, dummy_component):
        received = None

        def callback(component, **kwargs):
            nonlocal received
            received = component

        result = _invoke_callback(callback, mock_update, mock_context, dummy_component)
        assert received is dummy_component
        assert result is None

    def test_ignores_var_args_and_kwargs(self, mock_update, mock_context, dummy_component):
        called = False

        def callback(*args, **kwargs):
            nonlocal called
            called = True

        result = _invoke_callback(callback, mock_update, mock_context, dummy_component)
        assert called is True
        assert result is None
