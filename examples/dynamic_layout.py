import os
from typing import Sequence

from tuican.application import Application
from tuican.components import Button, Component, Screen, ScreenGroup
from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv

test = [
    ["b1", "b2"],
    ["b3", "b4", "b5"],
    ["b5", "b6"],
]

class DailyScreen(Screen):
    def __init__(self, group: ScreenGroup):
        self.left = Button(text="left", on_change=self.left_handler)
        self.right = Button(text="right", on_change=self.right_handler)
        self.cursor = 0
        self.buttons = []
        self.group = group
        super().__init__([self.left, self.right], message="dynamic")

    async def get_layout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Sequence[Sequence[InlineKeyboardButton]]:
        self.add_dynamic_components()
        return [[b.render(update, context) for b in self.buttons]] + [[self.left.render(update, context), self.right.render(update, context)]]

    def left_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str, comp: Component):
        self.remove_dynamic_components()
        self.cursor = (self.cursor - 1) % len(test)

    def right_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str, comp: Component):
        self.remove_dynamic_components()
        self.cursor = (self.cursor + 1) % len(test)

    def remove_dynamic_components(self):
        for b in self.buttons:
            self.delete_component(b)
        self.buttons = []

    def add_dynamic_components(self):
        if len(self.buttons) == 0:
            for label in test[self.cursor]:
                b = Button(text=label, on_change=self.open_button_screen)
                self.add_component(b)
                self.buttons.append(b)

    async def open_button_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str, comp: Component):
        message = ""
        if isinstance(comp, Button):
            message = comp.text
        screen = ButtonScreen(self.group, message)
        await self.group.go_to_screen(update, context, screen)

class ButtonScreen(Screen):

    def __init__(self, group: ScreenGroup, message):
        self.back = Button(text="back", on_change=self.go_back)
        self.group = group
        super().__init__([self.back], message=message)

    def get_layout(self, update, context) -> Sequence[Sequence[InlineKeyboardButton]]:
        return [[self.back.render(update, context)]]

    async def go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str, comp: Component):
        await self.group.go_back(update, context)

class MainScreen(ScreenGroup):
    def __init__(self):
        self.home = DailyScreen(self)
        super().__init__(self.home)


load_dotenv()
token = os.getenv("token")

app = Application(token, {'start': MainScreen})
app.run()
