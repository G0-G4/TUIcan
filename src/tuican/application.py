import logging
import os
from typing import Any, Callable, Coroutine

from telegram import BotCommand, Update
from telegram.ext import Application as TgApplication, ApplicationBuilder, CallbackQueryHandler, \
    CommandHandler, ContextTypes, \
    MessageHandler, filters

from .backend import PythonTelegramBotBackend
from .components import Screen
from .components.screen import StartScreenProtocol
from .errors import ValidationError
from .state_store import InMemoryStateStore, StateStore

Middleware = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, bool]]


def get_user_id(update: Update):
    if update.message is not None:
        return update.message.from_user.id
    elif update.callback_query is not None:
        return update.callback_query.from_user.id
    raise RuntimeError("no user id")


class Application:
    def __init__(self, token: str, screens: dict[str, StartScreenProtocol], state_store: StateStore | None = None):
        self._app_builder = ApplicationBuilder().token(token)
        self._app = None
        self._user_screens: dict[tuple[str, int], Screen] = dict()
        self._screen_factories = screens
        self._user_commands: dict[int, str] = {}
        self._backend = PythonTelegramBotBackend()
        self._state_store = state_store or InMemoryStateStore()
        self._middlewares: list[Middleware] = []
        self._post_init = None
        self._post_shutdown = None

    def _build(self):
        async def wrapper(application: TgApplication):
            loaded = await self._state_store.load_all()
            self._user_commands.update({int(k): v for k, v in loaded.items()})
            await application.bot.set_my_commands(
                [BotCommand(c, s.description) for c, s in self._screen_factories.items()])
            if self._post_init:
                await self._post_init(application)

        if self._post_shutdown:
            self._app_builder.post_shutdown(self._post_shutdown)

        if PROXY := os.getenv("PROXY"):
            self._app_builder.proxy(PROXY)

        self._app_builder.post_init(wrapper)
        self._app = self._app_builder.build()
        self._app.add_handler(CommandHandler(self._screen_factories.keys(), self.command_handler))
        self._app.add_handler(CallbackQueryHandler(self.dispatcher, pattern=".*"))
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_dispatcher))

    def run(self):
        self._build()
        self._app.run_polling(allowed_updates=Update.ALL_TYPES)

    def run_webhook(self, webhook_url: str, listen: str = "0.0.0.0", port: int = 8080, **kwargs):
        self._build()
        self._app.run_webhook(
            webhook_url=webhook_url,
            listen=listen,
            port=port,
            allowed_updates=Update.ALL_TYPES,
            **kwargs
        )

    def post_shutdown(self, function: Callable[[TgApplication], Coroutine[Any, Any, None]]):
        self._post_shutdown = function
        return self

    def post_init(self, function: Callable[[TgApplication], Coroutine[Any, Any, None]]):
        self._post_init = function
        return self

    def middleware(self, function: Middleware):
        self._middlewares.append(function)
        return function

    async def _run_middlewares(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        for mw in self._middlewares:
            result = await mw(update, context)
            if result is False:
                return False
        return True

    async def handle_exception(self, e: Exception, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.getLogger(__name__).exception("Unhandled exception in update handler")
        await self._backend.send_plain_message(update, context, str(e))

    async def command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._run_middlewares(update, context):
            return
        await self.remove_current_screen(update)
        command_args = update.message.text.replace('/', '').split(' ')
        await self._set_user_command(update, command_args[0])
        screen = await self.get_or_create_screen(update, context, command_args)
        screen.clear_update()
        await screen.start_handler(update, context)

    async def dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._run_middlewares(update, context):
            return
        screen = await self.get_or_create_screen(update, context)
        try:
            if await screen.dispatcher(update, context):
                await screen.display(update, context)
        except Exception as e:
            await self.handle_exception(e, update, context)

    async def message_dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._run_middlewares(update, context):
            return
        screen = await self.get_or_create_screen(update, context)
        try:
            if await screen.message_dispatcher(update, context):
                message_id_to_delete = update.message.id
                await screen.display(update, context)
                await self._backend.delete_message(update, context, message_id_to_delete)
        except ValidationError as e:
            await self._backend.send_plain_message(update, context, str(e))
        except Exception as e:
            await self.handle_exception(e, update, context)

    async def get_or_create_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
        command = self._get_user_command(update)
        not_initiated = command is None
        if not_initiated:
            logging.getLogger(__name__).info("command is empty. possible press on button after restart. start will be shown")
            command = 'start'
            await self._set_user_command(update, command)
        user_id = get_user_id(update)
        factory = self._screen_factories[command]
        key = (command, user_id)
        screen = self._user_screens.get(key, factory())
        screen.backend = self._backend
        if key not in self._user_screens:
            self._user_screens[key] = screen
            await screen.command_handler(args if args is not None else [], update, context)
        if not_initiated:
            await screen.display(update, context)
        return screen

    async def remove_current_screen(self, update: Update):
        user_id = get_user_id(update)
        command = self._get_user_command(update)
        if command is None:
            return
        key = (command, user_id)
        if key in self._user_screens:
            del self._user_screens[key]
        await self._remove_user_command(update)

    def _get_user_command(self, update: Update) -> str | None:
        user_id = get_user_id(update)
        return self._user_commands.get(user_id)

    async def _set_user_command(self, update: Update, command: str):
        user_id = get_user_id(update)
        self._user_commands[user_id] = command
        await self._state_store.save(user_id, command)

    async def _remove_user_command(self, update: Update):
        user_id = get_user_id(update)
        if user_id in self._user_commands:
            del self._user_commands[user_id]
        await self._state_store.delete(user_id)
