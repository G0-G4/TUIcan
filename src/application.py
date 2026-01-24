from typing import Callable

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

from src.components.screen import MainScreen


class Application:
    def __init__(self, token: str, main_screen_factory: Callable[[], MainScreen]):
        self._main_screen_factory = main_screen_factory
        self._app = ApplicationBuilder().token(token).build()
        self._app.add_handler(CommandHandler('start', self.start_handler))
        self._app.add_handler(CallbackQueryHandler(self.dispatcher, pattern=".*"))
        self._user_screen = dict()

    def run(self):
        self._app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        screen = self.get_or_create_screen(update)
        await screen.start_handler(update, context)

    async def dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        screen = self.get_or_create_screen(update)
        await screen.dispatcher(update, context)

    def get_user_id(self, update: Update):
        if update.message is not None:
            return update.message.from_user.id
        elif update.callback_query is not None:
            return update.callback_query.from_user.id
        raise RuntimeError("no user id")

    def get_or_create_screen(self, update: Update):
        user_id = self.get_user_id(update)
        screen = self._user_screen.get(user_id, self._main_screen_factory())
        if user_id not in self._user_screen:
            self._user_screen[user_id] = screen
        return screen
