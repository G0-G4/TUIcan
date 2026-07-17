import os
from typing import ClassVar, Sequence

from dotenv import load_dotenv
from telegram import InlineKeyboardButton

from tuican.application import Application
from tuican.components import Button, Component, Screen, ScreenGroup


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

    def get_layout(self) -> Sequence[Sequence[InlineKeyboardButton | Component]]:
        self.add_dynamic_components()
        return [[b for b in self.buttons]] + [[self.left, self.right]]

    def left_handler(self):
        self.remove_dynamic_components()
        self.cursor = (self.cursor - 1) % len(test)

    def right_handler(self):
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

    async def open_button_screen(self, comp: Component):
        message = ""
        if isinstance(comp, Button):
            message = comp.text
        screen = ButtonScreen(self.group, message)
        await self.group.go_to_screen(self.update, self.context, screen)

class ButtonScreen(Screen):

    def __init__(self, group: ScreenGroup, message):
        self.back = Button(text="back", on_change=self.go_back)
        self.group = group
        super().__init__([self.back], message=message)

    def get_layout(self) -> Sequence[Sequence[InlineKeyboardButton | Component]]:
        return [[self.back]]

    async def go_back(self):
        await self.group.go_back(self.update, self.context)

class MainScreen(ScreenGroup):
    description: ClassVar[str] = 'main screen'
    def __init__(self):
        self.home = DailyScreen(self)
        super().__init__(self.home)


load_dotenv()
token = os.getenv("token")

app = Application(token, {'start': MainScreen})
app.run()
