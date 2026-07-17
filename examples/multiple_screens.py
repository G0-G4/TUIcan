import os
from typing import ClassVar, Sequence

from dotenv import load_dotenv

from tuican import Application
from tuican.components import Button, Component, Screen, ScreenGroup
from tuican.keyboard_button import KeyboardButton


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

    def get_layout(self) -> Sequence[Sequence[KeyboardButton | Component]]:
        buttons = []
        if self.left_screen:
            buttons.append(self.left_btn)
        if self.right_screen:
            buttons.append(self.right_btn)
        buttons.append(self.home_btn)
        buttons.append(self.back_btn)
        return [buttons]

    async def go_left(self):
        if self.left_screen:
            await self.group.go_to_screen(self.update, self.context, self.left_screen)

    async def go_right(self):
        if self.right_screen:
            await self.group.go_to_screen(self.update, self.context, self.right_screen)

    async def go_home(self):
        await self.group.go_home(self.update, self.context)

    async def go_back(self):
        await self.group.go_back(self.update, self.context)


class AppScreens(ScreenGroup):
    description: ClassVar[str] = 'main screen'
    def __init__(self):
        self.d = NavigationScreen(self, "D")
        self.c = NavigationScreen(self, "C", left_screen=self.d)
        self.b = NavigationScreen(self, "B")
        self.a = NavigationScreen(self, "A", left_screen=self.b, right_screen=self.c)

        super().__init__(self.a)


load_dotenv()
token = os.getenv("token")
app = Application(token, {'start': AppScreens})
app.run()
