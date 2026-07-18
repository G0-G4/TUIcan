import asyncio
import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock

from tuican.update import TuicanUpdate
from tuican.components.component import _invoke_callback, Component, KeyboardButton


class DummyComponent(Component):
    async def handle_callback(self):
        return True

    def render(self):
        return KeyboardButton(text="dummy", callback_data=self.callback_data)


class TestInvokeCallback:
    @pytest.fixture
    def mock_update(self):
        return TuicanUpdate.from_callback(
            user_id=123, chat_id=456, callback_data="test_cb", message_id=1
        )

    @pytest.fixture
    def dummy_component(self):
        return DummyComponent(component_id="dummy")

    def test_zero_params(self, mock_update, dummy_component):
        called = False

        def callback():
            nonlocal called
            called = True

        result = _invoke_callback(callback, mock_update, dummy_component)
        assert called is True
        assert result is None

    def test_one_param_component(self, mock_update, dummy_component):
        received = None

        def callback(component):
            nonlocal received
            received = component

        result = _invoke_callback(callback, mock_update, dummy_component)
        assert received is dummy_component
        assert result is None

    def test_one_param_update(self, mock_update, dummy_component):
        received = None

        def callback(update):
            nonlocal received
            received = update

        result = _invoke_callback(callback, mock_update, dummy_component)
        assert received is mock_update
        assert result is None

    def test_two_params(self, mock_update, dummy_component):
        received_update = None
        received_component = None

        def callback(update, component):
            nonlocal received_update, received_component
            received_update = update
            received_component = component

        result = _invoke_callback(callback, mock_update, dummy_component)
        assert received_update is mock_update
        assert received_component is dummy_component
        assert result is None

    def test_more_than_three_params_raises(self, mock_update, dummy_component):
        def callback(a, b, c, d):
            pass

        with pytest.raises(TypeError, match="must accept 0-3 positional parameters"):
            _invoke_callback(callback, mock_update, dummy_component)

    def test_async_callback_returns_coroutine(self, mock_update, dummy_component):
        async def async_callback(component):
            return "done"

        result = _invoke_callback(async_callback, mock_update, dummy_component)
        assert inspect.isawaitable(result)
        assert asyncio.run(result) == "done"

    def test_async_callback_zero_params(self, mock_update, dummy_component):
        async def async_callback():
            return "done"

        result = _invoke_callback(async_callback, mock_update, dummy_component)
        assert inspect.isawaitable(result)
        assert asyncio.run(result) == "done"

    def test_async_callback_two_params(self, mock_update, dummy_component):
        async def async_callback(update, component):
            return "done"

        result = _invoke_callback(async_callback, mock_update, dummy_component)
        assert inspect.isawaitable(result)
        assert asyncio.run(result) == "done"

    def test_ignores_var_args(self, mock_update, dummy_component):
        called = False

        def callback(*args):
            nonlocal called
            called = True

        result = _invoke_callback(callback, mock_update, dummy_component)
        assert called is True
        assert result is None

    def test_ignores_kwargs(self, mock_update, dummy_component):
        received = None

        def callback(component, **kwargs):
            nonlocal received
            received = component

        result = _invoke_callback(callback, mock_update, dummy_component)
        assert received is dummy_component
        assert result is None

    def test_ignores_var_args_and_kwargs(self, mock_update, dummy_component):
        called = False

        def callback(*args, **kwargs):
            nonlocal called
            called = True

        result = _invoke_callback(callback, mock_update, dummy_component)
        assert called is True
        assert result is None
