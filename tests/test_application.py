import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tuican.application import Application, get_user_id
from tuican.backend import MessageBackend
from tuican.backends import PythonTelegramBotBackend
from tuican.components import Screen
from tuican.errors import UserNotFoundError, ValidationError
from tuican.stores import InMemoryStateStore
from tuican.update import TuicanUpdate, UpdateKind


class MyBackend:
    """Custom backend for testing injection."""

    async def send_keyboard_message(self, update, text, keyboard_markup, parse_mode="HTML") -> None:
        pass

    async def send_plain_message(self, update, text) -> None:
        pass

    async def send_notification(self, update, text, delete_after=1.0) -> None:
        pass

    async def delete_message(self, update, message_id) -> None:
        pass

    async def set_bot_commands(self, commands) -> None:
        pass


class DummyScreen(Screen):
    description = "dummy screen"

    def __init__(self):
        super().__init__([], message="hello")

    def get_layout(self):
        return []

    async def on_start(self, update):
        await self.display(update)

    async def on_command(self, args, update):
        pass


class StartScreen(Screen):
    description = "start screen"

    def __init__(self):
        super().__init__([], message="start")

    def get_layout(self):
        return []

    async def on_start(self, update):
        await self.display(update)

    async def on_command(self, args, update):
        pass


class OnStartScreen(Screen):
    description = "on_start screen"

    def __init__(self):
        super().__init__([], message="on_start")
        self.on_start_called = False

    def get_layout(self):
        return []

    async def on_start(self, update):
        self.on_start_called = True
        await self.display(update)

    async def on_command(self, args, update):
        pass


class MockTransport:
    def __init__(self):
        self.start_calls = []
        self.run_calls = []
        self.run_webhook_calls = []

    def start(self, core):
        self.start_calls.append(core)

    def run(self):
        self.run_calls.append(True)

    def run_webhook(self, webhook_url, listen="0.0.0.0", port=8080, **kwargs):
        self.run_webhook_calls.append({
            "webhook_url": webhook_url,
            "listen": listen,
            "port": port,
            **kwargs,
        })

    def default_backend(self):
        mock_bot = MagicMock()
        return PythonTelegramBotBackend(mock_bot)


@pytest.fixture
def mock_update_message():
    return TuicanUpdate.from_command(
        user_id=123,
        chat_id=456,
        message_text="/start",
        message_id=1,
    )


@pytest.fixture
def mock_update_callback():
    return TuicanUpdate.from_callback(
        user_id=123,
        chat_id=456,
        callback_data="test_data",
        message_id=2,
    )


@pytest.fixture
def app():
    return Application("fake-token", {"start": StartScreen, "dummy": DummyScreen})


@pytest.fixture
def app_with_store():
    store = InMemoryStateStore()
    return Application("fake-token", {"start": StartScreen, "dummy": DummyScreen}, state_store=store)


class TestGetUserId:
    def test_from_message(self, mock_update_message):
        assert get_user_id(mock_update_message) == 123

    def test_from_callback_query(self, mock_update_callback):
        assert get_user_id(mock_update_callback) == 123

    def test_raises_when_no_user(self):
        update = TuicanUpdate(
            user_id=None,
            chat_id=456,
            callback_data=None,
            message_text=None,
            message_id=None,
            kind=UpdateKind.MESSAGE,
        )
        with pytest.raises(UserNotFoundError):
            get_user_id(update)


class TestMiddleware:
    @pytest.mark.asyncio
    async def test_middleware_registration(self, app):
        async def mw(update):
            return True

        app.middleware(mw)
        assert mw in app._middlewares

    @pytest.mark.asyncio
    async def test_middleware_execution(self, app, mock_update_message):
        called = []

        async def mw(update):
            called.append("mw")
            return True

        app.middleware(mw)
        result = await app._run_middlewares(mock_update_message)
        assert result is True
        assert called == ["mw"]

    @pytest.mark.asyncio
    async def test_middleware_abort_on_false(self, app, mock_update_message):
        called = []

        async def mw1(update):
            called.append("mw1")
            return False

        async def mw2(update):
            called.append("mw2")
            return True

        app.middleware(mw1)
        app.middleware(mw2)
        result = await app._run_middlewares(mock_update_message)
        assert result is False
        assert called == ["mw1"]

    @pytest.mark.asyncio
    async def test_command_handler_aborts_when_middleware_returns_false(self, app, mock_update_message):
        app.middleware(AsyncMock(return_value=False))
        with patch.object(app, "remove_current_screen", new=AsyncMock()) as mock_remove:
            await app.command_handler(mock_update_message)
            mock_remove.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dispatcher_aborts_when_middleware_returns_false(self, app, mock_update_callback):
        app.middleware(AsyncMock(return_value=False))
        with patch.object(app, "get_or_create_screen", new=AsyncMock()) as mock_get:
            await app.dispatcher(mock_update_callback)
            mock_get.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_message_dispatcher_aborts_when_middleware_returns_false(self, app, mock_update_message):
        app.middleware(AsyncMock(return_value=False))
        with patch.object(app, "get_or_create_screen", new=AsyncMock()) as mock_get:
            await app.message_dispatcher(mock_update_message)
            mock_get.assert_not_awaited()


class TestCommandHandler:
    @pytest.mark.asyncio
    async def test_full_flow(self, app, mock_update_message):
        app._backend = AsyncMock()
        await app.command_handler(mock_update_message)
        assert app._user_commands[123] == "start"
        assert ("start", 123) in app._user_screens

    @pytest.mark.asyncio
    async def test_on_start_override_called(self, mock_update_message):
        app = Application("fake-token", {"start": OnStartScreen})
        app._backend = AsyncMock()
        await app.command_handler(mock_update_message)
        screen = app._user_screens[("start", 123)]
        assert isinstance(screen, OnStartScreen)
        assert screen.on_start_called is True

    @pytest.mark.asyncio
    async def test_split_fix_multiple_args(self, app, mock_update_message):
        update = TuicanUpdate.from_command(
            user_id=123,
            chat_id=456,
            message_text="/dummy arg1 arg2",
            message_id=1,
        )
        app._backend = AsyncMock()
        await app.command_handler(update)
        assert app._user_commands[123] == "dummy"
        screen = app._user_screens[("dummy", 123)]
        assert isinstance(screen, DummyScreen)

    @pytest.mark.asyncio
    async def test_user_not_found_error(self, app):
        update = TuicanUpdate(
            user_id=None,
            chat_id=456,
            callback_data=None,
            message_text=None,
            message_id=None,
            kind=UpdateKind.MESSAGE,
        )
        await app.command_handler(update)

    @pytest.mark.asyncio
    async def test_key_error_unknown_command(self, app, mock_update_message):
        update = TuicanUpdate.from_command(
            user_id=123,
            chat_id=456,
            message_text="/unknown",
            message_id=1,
        )
        await app.command_handler(update)

    @pytest.mark.asyncio
    async def test_no_message_text(self, app, mock_update_message):
        update = TuicanUpdate.from_command(
            user_id=123,
            chat_id=456,
            message_text=None,
            message_id=1,
        )
        with patch.object(app, "remove_current_screen", new=AsyncMock()) as mock_remove:
            await app.command_handler(update)
            mock_remove.assert_awaited_once()


class TestDispatcher:
    @pytest.mark.asyncio
    async def test_callback_flow(self, app, mock_update_callback):
        app._backend = AsyncMock()
        await app.dispatcher(mock_update_callback)

    @pytest.mark.asyncio
    async def test_exception_handling(self, app, mock_update_callback):
        screen = MagicMock()
        screen.dispatcher = AsyncMock(side_effect=RuntimeError("boom"))
        screen.display = AsyncMock()
        app._user_screens[("start", 123)] = screen
        app._user_commands[123] = "start"
        app._backend = AsyncMock()

        await app.dispatcher(mock_update_callback)
        app._backend.send_notification.assert_awaited_once()


class TestMessageDispatcher:
    @pytest.mark.asyncio
    async def test_validation_flow(self, app, mock_update_message):
        screen = MagicMock()
        screen.message_dispatcher = AsyncMock(return_value=True)
        screen.display = AsyncMock()
        app._user_screens[("start", 123)] = screen
        app._user_commands[123] = "start"
        app._backend = AsyncMock()

        await app.message_dispatcher(mock_update_message)
        screen.display.assert_awaited_once()
        app._backend.delete_message.assert_awaited_once()
        call_args = app._backend.delete_message.await_args[0]
        assert isinstance(call_args[0], TuicanUpdate)
        assert call_args[1] == 1

    @pytest.mark.asyncio
    async def test_validation_error(self, app, mock_update_message):
        screen = MagicMock()
        screen.message_dispatcher = AsyncMock(side_effect=ValidationError("bad input"))
        app._user_screens[("start", 123)] = screen
        app._user_commands[123] = "start"
        app._backend = AsyncMock()

        await app.message_dispatcher(mock_update_message)
        app._backend.send_notification.assert_awaited_once()
        call_args = app._backend.send_notification.await_args
        assert isinstance(call_args.args[0], TuicanUpdate)
        assert call_args.args[1] == "bad input"

    @pytest.mark.asyncio
    async def test_generic_exception(self, app, mock_update_message):
        screen = MagicMock()
        screen.message_dispatcher = AsyncMock(side_effect=RuntimeError("boom"))
        app._user_screens[("start", 123)] = screen
        app._user_commands[123] = "start"
        app._backend = AsyncMock()

        await app.message_dispatcher(mock_update_message)
        app._backend.send_notification.assert_awaited_once()
        call_args = app._backend.send_notification.await_args
        assert isinstance(call_args.args[0], TuicanUpdate)
        assert call_args.args[1] == "An unexpected error occurred. Please try again later."


class TestGetOrCreateScreen:
    @pytest.mark.asyncio
    async def test_factory_eager_evaluation(self, app, mock_update_message):
        app._user_commands[123] = "start"
        screen1 = await app.get_or_create_screen(mock_update_message)
        screen2 = await app.get_or_create_screen(mock_update_message)
        assert screen1 is screen2

    @pytest.mark.asyncio
    async def test_backend_injection(self, app, mock_update_message):
        app._user_commands[123] = "start"
        screen = await app.get_or_create_screen(mock_update_message)
        assert screen.backend is app._backend

    @pytest.mark.asyncio
    async def test_not_initiated_fallback_to_start(self, app, mock_update_callback):
        app._backend = AsyncMock()
        screen = await app.get_or_create_screen(mock_update_callback)
        assert app._user_commands[123] == "start"
        assert isinstance(screen, StartScreen)

    @pytest.mark.asyncio
    async def test_unknown_command_keyerror(self, app, mock_update_message):
        app._user_commands[123] = "unknown"
        with pytest.raises(KeyError, match="Unknown command"):
            await app.get_or_create_screen(mock_update_message)

    @pytest.mark.asyncio
    async def test_passes_args_to_command_handler(self, app, mock_update_message):
        app._user_commands[123] = "start"
        screen = await app.get_or_create_screen(mock_update_message, args=["a", "b"])
        assert isinstance(screen, StartScreen)


class TestRemoveCurrentScreen:
    @pytest.mark.asyncio
    async def test_removes_screen_and_command(self, app_with_store, mock_update_message):
        app = app_with_store
        app._backend = AsyncMock()
        await app.command_handler(mock_update_message)
        assert ("start", 123) in app._user_screens
        assert 123 in app._user_commands

        await app.remove_current_screen(mock_update_message)
        assert ("start", 123) not in app._user_screens
        assert 123 not in app._user_commands

    @pytest.mark.asyncio
    async def test_user_not_found_error(self, app):
        update = TuicanUpdate(
            user_id=None,
            chat_id=456,
            callback_data=None,
            message_text=None,
            message_id=None,
            kind=UpdateKind.MESSAGE,
        )
        await app.remove_current_screen(update)

    @pytest.mark.asyncio
    async def test_no_command_set(self, app, mock_update_message):
        await app.remove_current_screen(mock_update_message)


class TestSetAndRemoveUserCommand:
    @pytest.mark.asyncio
    async def test_set_user_command_updates_state_store(self, app_with_store, mock_update_message):
        await app_with_store._set_user_command(mock_update_message, "dummy")
        assert app_with_store._user_commands[123] == "dummy"
        loaded = await app_with_store._state_store.load(123)
        assert loaded == "dummy"

    @pytest.mark.asyncio
    async def test_remove_user_command_deletes_from_state_store(self, app_with_store, mock_update_message):
        await app_with_store._set_user_command(mock_update_message, "dummy")
        await app_with_store._remove_user_command(mock_update_message)
        assert 123 not in app_with_store._user_commands
        loaded = await app_with_store._state_store.load(123)
        assert loaded is None


class TestEnforceLimits:
    def test_enforce_limits_on_user_screens(self, app):
        app._max_user_screens = 2
        app._user_screens = {
            ("a", 1): MagicMock(),
            ("b", 2): MagicMock(),
            ("c", 3): MagicMock(),
        }
        app._enforce_limits()
        assert len(app._user_screens) == 2

    def test_enforce_limits_on_user_commands(self, app):
        app._max_user_commands = 2
        app._user_commands = {
            1: "a",
            2: "b",
            3: "c",
        }
        app._enforce_limits()
        assert len(app._user_commands) == 2


class TestHandleException:
    @pytest.mark.asyncio
    async def test_sends_generic_message_not_str_e(self, app, mock_update_message):
        app._backend = AsyncMock()
        exc = RuntimeError("secret details")
        await app.handle_exception(exc, mock_update_message)
        app._backend.send_notification.assert_awaited_once()
        call_args = app._backend.send_notification.await_args
        assert isinstance(call_args.args[0], TuicanUpdate)
        assert call_args.args[1] == "An unexpected error occurred. Please try again later."


class TestRunAndRunWebhook:
    def test_run_delegates_to_transport(self):
        transport = MockTransport()
        app = Application("fake-token", {"start": StartScreen}, transport=transport)
        app.run()
        assert app._transport is transport
        assert len(transport.start_calls) == 1
        assert transport.start_calls[0] is app
        assert len(transport.run_calls) == 1

    def test_run_webhook_delegates_to_transport(self):
        transport = MockTransport()
        app = Application("fake-token", {"start": StartScreen}, transport=transport)
        app.run_webhook("https://example.com/webhook", listen="127.0.0.1", port=5000)
        assert len(transport.start_calls) == 1
        assert transport.start_calls[0] is app
        assert len(transport.run_webhook_calls) == 1
        assert transport.run_webhook_calls[0] == {
            "webhook_url": "https://example.com/webhook",
            "listen": "127.0.0.1",
            "port": 5000,
        }

    def test_transport_string_ptb(self):
        with patch("tuican.transports.ptb_transport.PtbTransport") as MockPtb:
            mock_transport = MockTransport()
            MockPtb.return_value = mock_transport
            app = Application("fake-token", {"start": StartScreen}, transport="ptb")
            assert app._transport is mock_transport
            MockPtb.assert_called_once_with("fake-token")

    def test_transport_string_telethon(self):
        with patch("tuican.transports.telethon_transport.TelethonTransport") as MockTele:
            mock_transport = MockTransport()
            MockTele.return_value = mock_transport
            app = Application("fake-token", {"start": StartScreen}, transport="telethon", api_id=1, api_hash="hash")
            assert app._transport is mock_transport
            MockTele.assert_called_once_with("fake-token", 1, "hash")

    def test_transport_instance_used_directly(self):
        transport = MockTransport()
        app = Application("fake-token", {"start": StartScreen}, transport=transport)
        assert app._transport is transport

    def test_backend_defaults_to_transport_default_backend(self):
        transport = MockTransport()
        app = Application("fake-token", {"start": StartScreen}, transport=transport)
        assert isinstance(app.backend, PythonTelegramBotBackend)

    def test_custom_backend_overrides_transport_default(self):
        custom = MyBackend()
        transport = MockTransport()
        app = Application("fake-token", {"start": StartScreen}, transport=transport, backend=custom)
        assert app.backend is custom


class TestBackendParameter:
    def test_custom_backend_injection(self):
        custom = MyBackend()
        app = Application("fake-token", {"start": StartScreen}, backend=custom)
        assert isinstance(app.backend, MyBackend)
        assert app.backend is custom

    def test_default_backend_is_python_telegram_bot(self):
        app = Application("fake-token", {"start": StartScreen})
        assert isinstance(app.backend, PythonTelegramBotBackend)

    @pytest.mark.asyncio
    async def test_get_or_create_screen_uses_injected_backend(self, mock_update_message):
        custom = MyBackend()
        app = Application("fake-token", {"start": StartScreen}, backend=custom)
        app._user_commands[123] = "start"
        screen = await app.get_or_create_screen(mock_update_message)
        assert screen.backend is custom

    @pytest.mark.asyncio
    async def test_command_handler_injects_custom_backend(self, mock_update_message):
        custom = MyBackend()
        app = Application("fake-token", {"start": StartScreen}, backend=custom)
        await app.command_handler(mock_update_message)
        screen = app._user_screens[("start", 123)]
        assert screen.backend is custom
