import os
from typing import Sequence

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from src.application import Application
from src.components.button import Button
from src.components.screen import Screen, ScreenGroup


class NavigationScreen(Screen):
    def __init__(self, group: ScreenGroup, name: str, left_screen=None, right_screen=None):
        self.group = group
        self.name = name
        self.left_screen = left_screen
        self.right_screen = right_screen

        self.left_btn = Button("Left", callback_data="left", on_change=self.go_left)
        self.right_btn = Button("Right", callback_data="right", on_change=self.go_right)
        self.home_btn = Button("Home", callback_data="home", on_change=self.go_home)
        self.back_btn = Button("Back", callback_data="back", on_change=self.go_back)

        super().__init__([self.left_btn, self.right_btn, self.home_btn, self.back_btn],
                         message=f"Screen {name}")

    def get_layout(self, update, context) -> Sequence[Sequence[InlineKeyboardButton]]:
        buttons = []
        if self.left_screen:
            buttons.append(self.left_btn.render(update, context))
        if self.right_screen:
            buttons.append(self.right_btn.render(update, context))
        buttons.append(self.home_btn.render(update, context))
        buttons.append(self.back_btn.render(update, context))
        return [buttons]

    async def go_left(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        if self.left_screen:
            await self.group.go_to_screen(update, context, self.left_screen)

    async def go_right(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        if self.right_screen:
            await self.group.go_to_screen(update, context, self.right_screen)

    async def go_home(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        await self.group.go_home(update, context)

    async def go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        await self.group.go_back(update, context)


class AppScreens(ScreenGroup):
    def __init__(self):
        self.d = NavigationScreen(self, "D")
        self.c = NavigationScreen(self, "C", left_screen=self.d)
        self.b = NavigationScreen(self, "B")
        self.a = NavigationScreen(self, "A", left_screen=self.b, right_screen=self.c)

        super().__init__(self.a)


load_dotenv()
token = os.getenv("token")
app = Application(token, AppScreens)
app.run()
