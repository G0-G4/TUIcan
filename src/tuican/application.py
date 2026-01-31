from typing import Any, Callable, Coroutine

from telegram import BotCommand, Update
from telegram.ext import Application as TgApplication, ApplicationBuilder, CallbackQueryHandler, \
    CommandHandler, ContextTypes, \
    MessageHandler, filters

from .components import Screen
from .components.screen import StartScreenProtocol
from .errors import ValidationError


def get_user_id(update: Update):
    if update.message is not None:
        return update.message.from_user.id
    elif update.callback_query is not None:
        return update.callback_query.from_user.id
    raise RuntimeError("no user id")


class Application:
    def __init__(self, token: str, screens: dict[str, StartScreenProtocol]):
        self._app_builder = ApplicationBuilder().token(token)
        self._app = None
        self._user_screens: dict[tuple[str, int], Screen] = dict()
        self._screen_factories = screens
        self._command = None
        self._post_init = None
        self._post_shutdown = None

    def _build(self):
        async def wrapper(application: TgApplication):
            await application.bot.set_my_commands(
                [BotCommand(c, s.description) for c, s in self._screen_factories.items()])
            if self._post_init:
                await self._post_init(application)

        if self._post_shutdown:
            self._app_builder.post_shutdown(self._post_shutdown)
        self._app_builder.post_init(wrapper)
        self._app = self._app_builder.build()
        self._app.add_handler(CommandHandler(self._screen_factories.keys(), self.command_handler))
        self._app.add_handler(CallbackQueryHandler(self.dispatcher, pattern=".*"))
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_dispatcher))

    def run(self):
        self._build()
        self._app.run_polling(allowed_updates=Update.ALL_TYPES)

    def post_shutdown(self, function: Callable[[TgApplication], Coroutine[Any, Any, None]]):
        self._post_shutdown = function
        return self

    def post_init(self, function: Callable[[TgApplication], Coroutine[Any, Any, None]]):
        self._post_init = function
        return self

    async def handle_exception(self, e: Exception, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        print(e)
        await context.bot.send_message(chat_id=chat_id, text=str(e))

    async def command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.remove_current_screen(update)
        command_args = update.message.text.replace('/', '').split(' ')
        self._command = command_args[0]
        screen = await self.get_or_create_screen(update, context, command_args)
        screen.clear_update()
        await screen.start_handler(update, context)


    async def dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        screen = await self.get_or_create_screen(update, context)
        try:
            if await screen.dispatcher(update, context):
                await screen.display(update, context)
        except Exception as e:
            await self.handle_exception(e, update, context)

    async def message_dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        screen = await self.get_or_create_screen(update, context)
        chat_id = update.effective_chat.id
        try:
            if await screen.message_dispatcher(update, context):
                message_id_to_delete = update.message.id
                await screen.display(update, context)
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id_to_delete)
        except ValidationError as e:
            await context.bot.send_message(chat_id=chat_id, text=str(e))
        except Exception as e:
            await self.handle_exception(e, update, context)

    async def get_or_create_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
        not_initiated = self._command is None
        if not_initiated:
            print("command is empty. possible press on button after restart. start will be shown")
            self._command = 'start'
        user_id = get_user_id(update)
        factory = self._screen_factories[self._command]
        key = (self._command, user_id)
        screen = self._user_screens.get(key, factory())
        if key not in self._user_screens:
            self._user_screens[key] = screen
            await screen.command_handler(args if args is not None else [], update, context)
        if not_initiated:
            await screen.display(update, context)
        return screen

    def remove_current_screen(self, update: Update):
        user_id = get_user_id(update)
        key = (self._command, user_id)
        if key in self._user_screens:
            del self._user_screens[key]
