import os
from typing import Sequence

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from src.application import Application
from src.components.button import Button
from src.components.screen import MainScreen


class ButtonScreen(MainScreen):
    def __init__(self):
        self.c = 0
        self.b = Button("my button", callback_data="button", on_change=self.update_message)
        super().__init__([self.b], message="no presses")

    def update_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        self.c += 1
        self.message = "pressed " + str(self.c)

    def get_layout(self, update, context) -> Sequence[Sequence[InlineKeyboardButton]]:
        return [[self.b.render(update, context)]]

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.display(update, context)


load_dotenv()
token = os.getenv("token")
main_screen = ButtonScreen()

app = Application(token, ButtonScreen)
app.run()
