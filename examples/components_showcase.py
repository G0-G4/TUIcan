import os
from typing import Sequence

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from src.application import Application
from src.components.button import Button
from src.components.checkbox import CheckBox, ExclusiveCheckBoxGroup
from src.components.input import Input
from src.components.screen import MainScreen
from src.validation import positive_int


class ComponentsScreen(MainScreen):
    def __init__(self):
        group = ExclusiveCheckBoxGroup()
        self.check_box_1 = CheckBox("1", callback_data="1", on_change=self.update_message, group=group)
        self.check_box_2 = CheckBox("2", callback_data="2", on_change=self.update_message, group=group)
        self.button = Button("3", callback_data="3", on_change=self.update_message)
        self.input = Input[int](text="возраст: ", value=123, on_change=self.update_message, callback_data="input",
                                validation_function=positive_int)
        super().__init__([self.check_box_1, self.check_box_2, self.button, self.input], message="show case")

    def update_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        self.message = "pressed " + callback_data
        print("pressed " + callback_data)

    def get_layout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Sequence[
        Sequence[InlineKeyboardButton]]:
        return [
            [self.check_box_1.render(update, context), self.check_box_2.render(update, context)],
            [self.button.render(update, context)],
            [self.input.render(update, context)]
        ]

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.display(update, context)


load_dotenv()
token = os.getenv("token")

app = Application(token, ComponentsScreen)
app.run()
