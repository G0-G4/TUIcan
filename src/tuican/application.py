from typing import Callable, Mapping

from telegram import BotCommand, Update
from telegram.ext import Application as TgApplication, ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, \
    MessageHandler, filters

from .components.screen import StartScreenProtocol
from .components import Screen
from .errors import ValidationError


def get_user_id(update: Update):
    if update.message is not None:
        return update.message.from_user.id
    elif update.callback_query is not None:
        return update.callback_query.from_user.id
    raise RuntimeError("no user id")



class Application:
    def __init__(self, token: str, screens: dict[str, StartScreenProtocol]):
        self._app = ApplicationBuilder().token(token).post_init(self.post_init).build()
        self._app.add_handler(CommandHandler(screens.keys(), self.command_handler))
        self._app.add_handler(CallbackQueryHandler(self.dispatcher, pattern=".*"))
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_dispatcher))
        self._user_screens: dict[tuple[str, int], Screen] = dict()
        self._screen_factories = screens
        self._command = None

    def run(self):
        self._app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def post_init(self, application: TgApplication):
        await application.bot.set_my_commands([BotCommand(c, s.description) for c, s in self._screen_factories.items()])

    async def command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._command = update.message.text.replace('/', '')
        screen = self.get_or_create_screen(update)
        screen.clear_update()
        await screen.start_handler(update, context)

    async def dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        screen = self.get_or_create_screen(update)
        if await screen.dispatcher(update, context):
            await screen.display(update, context)

    async def message_dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        screen = self.get_or_create_screen(update)
        chat_id = update.effective_chat.id
        try:
            if await screen.message_dispatcher(update, context):
                message_id_to_delete = update.message.id
                await screen.display(update, context)
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id_to_delete)
        except ValidationError as e:
            await context.bot.send_message(chat_id=chat_id, text=str(e))

    def get_or_create_screen(self, update: Update):
        user_id = get_user_id(update)
        factory = self._screen_factories[self._command]
        key = (self._command, user_id)
        screen = self._user_screens.get(key, factory())
        if key not in self._user_screens:
            self._user_screens[key] = screen
        return screen
