import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update
from telegram.ext import Application as TgApplication, ApplicationBuilder, ContextTypes

from tuican.application import Application, get_user_id
from tuican.backend import MessageBackend, PythonTelegramBotBackend
from tuican.components import Screen
from tuican.errors import UserNotFoundError, ValidationError
from tuican.stores import InMemoryStateStore


class MyBackend:
    """Custom backend for testing injection."""

    async def send_keyboard_message(self, update, context, text, keyboard_markup, parse_mode="HTML") -> None:
        pass

    async def send_plain_message(self, update, context, text) -> None:
        pass

    async def delete_message(self, update, context, message_id) -> None:
        pass

    async def set_bot_commands(self, update, context, commands) -> None:
        pass


class DummyScreen(Screen):
    description = "dummy screen"

    def __init__(self):
        super().__init__([], message="hello")

    def get_layout(self):
        return []

    async def start_handler(self, update, context):
        await self.display(update, context)

    async def command_handler(self, args, update, context):
        pass


class StartScreen(Screen):
    description = "start screen"

    def __init__(self):
        super().__init__([], message="start")

    def get_layout(self):
        return []

    async def start_handler(self, update, context):
        await self.display(update, context)

    async def command_handler(self, args, update, context):
        pass


class OnStartScreen(Screen):
    description = "on_start screen"

    def __init__(self):
        super().__init__([], message="on_start")
        self.on_start_called = False

    def get_layout(self):
        return []

    async def on_start(self, update, context):
        self.on_start_called = True
        await self.display(update, context)

    async def on_command(self, args, update, context):
        pass


@pytest.fixture
def mock_update_message():
    update = MagicMock(spec=Update)
    update.message = MagicMock()
    update.message.from_user = MagicMock()
    update.message.from_user.id = 123
    update.message.text = "/start"
    update.message.id = 1
    update.callback_query = None
    update.effective_chat = MagicMock()
    update.effective_chat.id = 456
    return update


@pytest.fixture
def mock_update_callback():
    update = MagicMock(spec=Update)
    update.callback_query = MagicMock()
    update.callback_query.from_user = MagicMock()
    update.callback_query.from_user.id = 123
    update.callback_query.data = "test_data"
    update.message = None
    update.effective_chat = MagicMock()
    update.effective_chat.id = 456
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    return context


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
        update = MagicMock(spec=Update)
        update.message = None
        update.callback_query = None
        with pytest.raises(UserNotFoundError):
            get_user_id(update)


class TestMiddleware:
    @pytest.mark.asyncio
    async def test_middleware_registration(self, app):
        async def mw(update, context):
            return True

        app.middleware(mw)
        assert mw in app._middlewares

    @pytest.mark.asyncio
    async def test_middleware_execution(self, app, mock_update_message, mock_context):
        called = []

        async def mw(update, context):
            called.append("mw")
            return True

        app.middleware(mw)
        result = await app._run_middlewares(mock_update_message, mock_context)
        assert result is True
        assert called == ["mw"]

    @pytest.mark.asyncio
    async def test_middleware_abort_on_false(self, app, mock_update_message, mock_context):
        called = []

        async def mw1(update, context):
            called.append("mw1")
            return False

        async def mw2(update, context):
            called.append("mw2")
            return True

        app.middleware(mw1)
        app.middleware(mw2)
        result = await app._run_middlewares(mock_update_message, mock_context)
        assert result is False
        assert called == ["mw1"]

    @pytest.mark.asyncio
    async def test_command_handler_aborts_when_middleware_returns_false(self, app, mock_update_message, mock_context):
        app.middleware(AsyncMock(return_value=False))
        with patch.object(app, "remove_current_screen", new=AsyncMock()) as mock_remove:
            await app.command_handler(mock_update_message, mock_context)
            mock_remove.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dispatcher_aborts_when_middleware_returns_false(self, app, mock_update_callback, mock_context):
        app.middleware(AsyncMock(return_value=False))
        with patch.object(app, "get_or_create_screen", new=AsyncMock()) as mock_get:
            await app.dispatcher(mock_update_callback, mock_context)
            mock_get.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_message_dispatcher_aborts_when_middleware_returns_false(self, app, mock_update_message, mock_context):
        app.middleware(AsyncMock(return_value=False))
        with patch.object(app, "get_or_create_screen", new=AsyncMock()) as mock_get:
            await app.message_dispatcher(mock_update_message, mock_context)
            mock_get.assert_not_awaited()


class TestCommandHandler:
    @pytest.mark.asyncio
    async def test_full_flow(self, app, mock_update_message, mock_context):
        app._backend = AsyncMock()
        await app.command_handler(mock_update_message, mock_context)
        assert app._user_commands[123] == "start"
        assert ("start", 123) in app._user_screens

    @pytest.mark.asyncio
    async def test_on_start_override_called(self, mock_update_message, mock_context):
        app = Application("fake-token", {"start": OnStartScreen})
        app._backend = AsyncMock()
        await app.command_handler(mock_update_message, mock_context)
        screen = app._user_screens[("start", 123)]
        assert isinstance(screen, OnStartScreen)
        assert screen.on_start_called is True

    @pytest.mark.asyncio
    async def test_split_fix_multiple_args(self, app, mock_update_message, mock_context):
        mock_update_message.message.text = "/dummy arg1 arg2"
        app._backend = AsyncMock()
        await app.command_handler(mock_update_message, mock_context)
        assert app._user_commands[123] == "dummy"
        screen = app._user_screens[("dummy", 123)]
        assert isinstance(screen, DummyScreen)

    @pytest.mark.asyncio
    async def test_user_not_found_error(self, app, mock_context):
        update = MagicMock(spec=Update)
        update.message = None
        update.callback_query = None
        await app.command_handler(update, mock_context)

    @pytest.mark.asyncio
    async def test_key_error_unknown_command(self, app, mock_update_message, mock_context):
        mock_update_message.message.text = "/unknown"
        await app.command_handler(mock_update_message, mock_context)

    @pytest.mark.asyncio
    async def test_no_message_text(self, app, mock_update_message, mock_context):
        mock_update_message.message.text = None
        with patch.object(app, "remove_current_screen", new=AsyncMock()) as mock_remove:
            await app.command_handler(mock_update_message, mock_context)
            mock_remove.assert_awaited_once()


class TestDispatcher:
    @pytest.mark.asyncio
    async def test_callback_flow(self, app, mock_update_callback, mock_context):
        app._backend = AsyncMock()
        await app.dispatcher(mock_update_callback, mock_context)

    @pytest.mark.asyncio
    async def test_exception_handling(self, app, mock_update_callback, mock_context):
        screen = MagicMock()
        screen.dispatcher = AsyncMock(side_effect=RuntimeError("boom"))
        screen.display = AsyncMock()
        app._user_screens[("start", 123)] = screen
        app._user_commands[123] = "start"
        app._backend = AsyncMock()

        await app.dispatcher(mock_update_callback, mock_context)
        app._backend.send_plain_message.assert_awaited_once()


class TestMessageDispatcher:
    @pytest.mark.asyncio
    async def test_validation_flow(self, app, mock_update_message, mock_context):
        screen = MagicMock()
        screen.message_dispatcher = AsyncMock(return_value=True)
        screen.display = AsyncMock()
        app._user_screens[("start", 123)] = screen
        app._user_commands[123] = "start"
        app._backend = AsyncMock()

        await app.message_dispatcher(mock_update_message, mock_context)
        screen.display.assert_awaited_once()
        app._backend.delete_message.assert_awaited_once_with(mock_update_message, mock_context, 1)

    @pytest.mark.asyncio
    async def test_validation_error(self, app, mock_update_message, mock_context):
        screen = MagicMock()
        screen.message_dispatcher = AsyncMock(side_effect=ValidationError("bad input"))
        app._user_screens[("start", 123)] = screen
        app._user_commands[123] = "start"
        app._backend = AsyncMock()

        await app.message_dispatcher(mock_update_message, mock_context)
        app._backend.send_plain_message.assert_awaited_once_with(mock_update_message, mock_context, "bad input")

    @pytest.mark.asyncio
    async def test_generic_exception(self, app, mock_update_message, mock_context):
        screen = MagicMock()
        screen.message_dispatcher = AsyncMock(side_effect=RuntimeError("boom"))
        app._user_screens[("start", 123)] = screen
        app._user_commands[123] = "start"
        app._backend = AsyncMock()

        await app.message_dispatcher(mock_update_message, mock_context)
        app._backend.send_plain_message.assert_awaited_once_with(
            mock_update_message, mock_context, "An unexpected error occurred. Please try again later."
        )


class TestGetOrCreateScreen:
    @pytest.mark.asyncio
    async def test_factory_eager_evaluation(self, app, mock_update_message, mock_context):
        app._user_commands[123] = "start"
        screen1 = await app.get_or_create_screen(mock_update_message, mock_context)
        screen2 = await app.get_or_create_screen(mock_update_message, mock_context)
        assert screen1 is screen2

    @pytest.mark.asyncio
    async def test_backend_injection(self, app, mock_update_message, mock_context):
        app._user_commands[123] = "start"
        screen = await app.get_or_create_screen(mock_update_message, mock_context)
        assert screen.backend is app._backend

    @pytest.mark.asyncio
    async def test_not_initiated_fallback_to_start(self, app, mock_update_callback, mock_context):
        app._backend = AsyncMock()
        screen = await app.get_or_create_screen(mock_update_callback, mock_context)
        assert app._user_commands[123] == "start"
        assert isinstance(screen, StartScreen)

    @pytest.mark.asyncio
    async def test_unknown_command_keyerror(self, app, mock_update_message, mock_context):
        app._user_commands[123] = "unknown"
        with pytest.raises(KeyError, match="Unknown command"):
            await app.get_or_create_screen(mock_update_message, mock_context)

    @pytest.mark.asyncio
    async def test_passes_args_to_command_handler(self, app, mock_update_message, mock_context):
        app._user_commands[123] = "start"
        screen = await app.get_or_create_screen(mock_update_message, mock_context, args=["a", "b"])
        assert isinstance(screen, StartScreen)


class TestRemoveCurrentScreen:
    @pytest.mark.asyncio
    async def test_removes_screen_and_command(self, app_with_store, mock_update_message, mock_context):
        app = app_with_store
        app._backend = AsyncMock()
        await app.command_handler(mock_update_message, mock_context)
        assert ("start", 123) in app._user_screens
        assert 123 in app._user_commands

        await app.remove_current_screen(mock_update_message)
        assert ("start", 123) not in app._user_screens
        assert 123 not in app._user_commands

    @pytest.mark.asyncio
    async def test_user_not_found_error(self, app):
        update = MagicMock(spec=Update)
        update.message = None
        update.callback_query = None
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
    async def test_sends_generic_message_not_str_e(self, app, mock_update_message, mock_context):
        app._backend = AsyncMock()
        exc = RuntimeError("secret details")
        await app.handle_exception(exc, mock_update_message, mock_context)
        app._backend.send_plain_message.assert_awaited_once_with(
            mock_update_message, mock_context, "An unexpected error occurred. Please try again later."
        )


class TestRunAndRunWebhook:
    def test_run_setup(self, app):
        mock_app = MagicMock(spec=TgApplication)
        mock_builder = MagicMock()
        mock_builder.build.return_value = mock_app
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        app._app_builder = mock_builder

        with patch.dict("os.environ", {"PROXY": "http://proxy"}, clear=False):
            app.run()

        mock_builder.proxy.assert_called_once_with("http://proxy")
        mock_app.run_polling.assert_called_once_with(allowed_updates=Update.ALL_TYPES)

    def test_run_webhook_setup(self, app):
        mock_app = MagicMock(spec=TgApplication)
        mock_builder = MagicMock()
        mock_builder.build.return_value = mock_app
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        app._app_builder = mock_builder

        app.run_webhook("https://example.com/webhook", listen="127.0.0.1", port=5000)

        mock_app.run_webhook.assert_called_once_with(
            webhook_url="https://example.com/webhook",
            listen="127.0.0.1",
            port=5000,
            allowed_updates=Update.ALL_TYPES,
        )

    def test_post_shutdown_hook(self, app):
        mock_app = MagicMock(spec=TgApplication)
        mock_builder = MagicMock()
        mock_builder.build.return_value = mock_app
        mock_builder.post_init.return_value = mock_builder
        mock_builder.post_shutdown.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        app._app_builder = mock_builder

        async def shutdown_hook(application):
            pass

        app.post_shutdown(shutdown_hook)
        app.run()

        mock_builder.post_shutdown.assert_called_once()

    def test_post_init_hook(self, app):
        mock_app = MagicMock(spec=TgApplication)
        mock_builder = MagicMock()
        mock_builder.build.return_value = mock_app
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        app._app_builder = mock_builder

        async def init_hook(application):
            pass

        app.post_init(init_hook)
        app.run()

        mock_builder.post_init.assert_called_once()


class TestBuild:
    def test_build_adds_handlers(self, app):
        mock_app = MagicMock(spec=TgApplication)
        mock_builder = MagicMock()
        mock_builder.build.return_value = mock_app
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        app._app_builder = mock_builder

        app._build()

        assert app._app is mock_app
        mock_app.add_handler.assert_called()
        calls = [call.args for call in mock_app.add_handler.call_args_list]
        assert len(calls) == 3

    def test_build_is_idempotent(self, app):
        mock_app = MagicMock(spec=TgApplication)
        mock_builder = MagicMock()
        mock_builder.build.return_value = mock_app
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        app._app_builder = mock_builder

        app._build()
        first_app = app._app
        first_call_count = mock_app.add_handler.call_count

        app._build()

        assert app._app is first_app
        assert mock_app.add_handler.call_count == first_call_count

    def test_run_then_run_webhook_does_not_duplicate_handlers(self, app):
        mock_app = MagicMock(spec=TgApplication)
        mock_builder = MagicMock()
        mock_builder.build.return_value = mock_app
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        app._app_builder = mock_builder

        app.run()
        app.run_webhook("https://example.com/webhook")

        assert mock_app.add_handler.call_count == 3

    def test_built_flag_set_after_build(self, app):
        assert app._built is False
        mock_app = MagicMock(spec=TgApplication)
        mock_builder = MagicMock()
        mock_builder.build.return_value = mock_app
        mock_builder.post_init.return_value = mock_builder
        mock_builder.proxy.return_value = mock_builder
        app._app_builder = mock_builder

        app._build()
        assert app._built is True


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
    async def test_get_or_create_screen_uses_injected_backend(self, mock_update_message, mock_context):
        custom = MyBackend()
        app = Application("fake-token", {"start": StartScreen}, backend=custom)
        app._user_commands[123] = "start"
        screen = await app.get_or_create_screen(mock_update_message, mock_context)
        assert screen.backend is custom

    @pytest.mark.asyncio
    async def test_command_handler_injects_custom_backend(self, mock_update_message, mock_context):
        custom = MyBackend()
        app = Application("fake-token", {"start": StartScreen}, backend=custom)
        await app.command_handler(mock_update_message, mock_context)
        screen = app._user_screens[("start", 123)]
        assert screen.backend is custom
