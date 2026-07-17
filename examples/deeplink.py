import os
from typing import ClassVar

from dotenv import load_dotenv

from tuican.application import Application
from tuican.components import Button, Screen
from tuican.components import ScreenGroup

'''
open https://t.me/<bot name>?start=123
and see the message from bot on accept
'''


class MyScreen(Screen):
    description: ClassVar[str] = 'main screen'
    def __init__(self, group: ScreenGroup):
        self.group = group
        self.button = Button("Click me", on_change=self.handle_click)
        super().__init__([self.button], message="click the button")

    def handle_click(self):
        self.message = "Hello world!"

    async def command_handler(self, args: list[str], update, context):
        if len(args) > 1:
            screen = DeepLinkScreen(self.group, args[1])
            await self.group.go_to_screen(update, context, screen)

    def get_layout(self):
        return [[self.button]]

class DeepLinkScreen(Screen):
    description: ClassVar[str] = 'main screen'
    def __init__(self, group: ScreenGroup, arg):
        self.group = group
        self.arg = arg
        self.action = Button("✅ perform action", on_change=self.handle_action)
        self.cancel = Button("❌ cancel", on_change=self.handle_cancel)
        super().__init__([self.action, self.cancel], message="perform action?")

    async def handle_action(self):
        await self.send_message(self.update, self.context, f"action performed with argument {self.arg}")
        await self.group.go_home(self.update, self.context)

    async def handle_cancel(self):
        await self.group.go_home(self.update, self.context)

    def get_layout(self):
        return [[self.action, self.cancel]]

class Grp(ScreenGroup):
    description: ClassVar[str] = "deep link example"
    def __init__(self):
        main = MyScreen(self)
        super().__init__(main)

load_dotenv()
token = os.getenv("token")
app = Application(token, {'start': Grp})
app.run()
