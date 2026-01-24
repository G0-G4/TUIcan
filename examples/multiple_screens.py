import os
from typing import Sequence

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from src.application import Application
from src.components.button import Button
from src.components.checkbox import CheckBox
from src.components.screen import Screen


class ScreenGroup(Screen):

    def __init__(self):
        super().__init__([])
        self.f1 = FirstScreen(self)
        self._screen_stack: list[Screen] = [self.f1]

    async def go_to_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, new_screen: Screen):
        self._screen_stack.append(new_screen)

    async def go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._screen_stack.pop()

    async def go_home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._screen_stack = self._screen_stack[:1]

    def get_layout(self, update, context) -> Sequence[Sequence[InlineKeyboardButton]]:
        return self._screen_stack[-1].get_layout(update, context)

    async def dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return await self._screen_stack[-1].dispatcher(update, context)

    async def message_dispatcher(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return await self._screen_stack[-1].message_dispatcher(update, context)

    async def display(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self._screen_stack[-1].display(update, context)

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self._screen_stack[-1].start_handler(update, context)

    @property
    def message(self) -> str:
        return self._screen_stack[-1].message

    @message.setter
    def message(self, message):
        self._screen_stack[-1].message = message


class FirstScreen(Screen):
    def __init__(self, screen_group: ScreenGroup):
        self.check_box = CheckBox("1", callback_data="1", on_change=self.update_message)
        self.button = Button("next" , callback_data="new_screen", on_change=self.new_screen_pressed)
        self.screen_group = screen_group
        self.second_screen = None
        super().__init__([self.check_box, self.button], message="first screen")

    def update_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        self.message = "pressed " + callback_data
        print("pressed " + callback_data)

    async def new_screen_pressed(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        await self.screen_group.go_to_screen(update, context, self.get_second_screen())

    def get_second_screen(self) -> Screen:
        if self.second_screen is None:
            self.second_screen = SecondScreen(self.screen_group)
        return self.second_screen

    def get_layout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Sequence[
        Sequence[InlineKeyboardButton]]:
        return [
            [self.check_box.render(update, context), self.button.render(update, context)],
        ]


class SecondScreen(Screen):
    def __init__(self, screen_group: ScreenGroup):
        self.screen_group = screen_group
        self.check_box = CheckBox("2", callback_data="2", on_change=self.update_message)
        self.button = Button("back", callback_data="back", on_change=self.back)
        self.next = Button("next", callback_data="new_screen", on_change=self.new_screen_pressed)
        self.third_screen = None
        super().__init__([self.check_box, self.button, self.next], message="second screen")

    def update_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        self.message = "pressed " + callback_data
        print("pressed " + callback_data)

    async def back(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        await self.screen_group.go_back(update, context)

    async def new_screen_pressed(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        await self.screen_group.go_to_screen(update, context, self.get_second_screen())

    def get_second_screen(self) -> Screen:
        if self.third_screen is None:
            self.third_screen = ThirdScreen(self.screen_group)
        return self.third_screen

    def get_layout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Sequence[
        Sequence[InlineKeyboardButton]]:
        return [
            [self.check_box.render(update, context), self.button.render(update, context), self.next.render(update, context)],
        ]

class ThirdScreen(Screen):
    def __init__(self, screen_group: ScreenGroup):
        self.screen_group = screen_group
        self.check_box = CheckBox("2", callback_data="2", on_change=self.update_message)
        self.button = Button("back", callback_data="back", on_change=self.back)
        self.home = Button("home", callback_data="home", on_change=self.home)
        super().__init__([self.check_box, self.button, self.home], message="third screen")

    def update_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        self.message = "pressed " + callback_data
        print("pressed " + callback_data)

    async def back(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        await self.screen_group.go_back(update, context)

    async def home(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        await self.screen_group.go_home(update, context)

    def get_layout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Sequence[
        Sequence[InlineKeyboardButton]]:
        return [
            [self.check_box.render(update, context), self.button.render(update, context), self.home.render(update, context)],
        ]


load_dotenv()
token = os.getenv("token")

app = Application(token, ScreenGroup)
app.run()
